# 02_TRUST_BOUNDARIES — карта границ доверия iOS 27.2 (на доступных данных)

Метод: статический анализ. Для каждой границы разделяем три класса:
- **[OBSERVED]** — наблюдаемый факт из бинаря/plist/entitlement (строка, метод,
  load-command, лог). Приводится конкретное доказательство.
- **[INFERRED]** — предположение о замысле/роли, выведенное из факта.
- **[DEFECT-CLASS]** — класс уязвимости, к которому граница относится
  (не утверждение, что уязвимость есть — только что здесь она возможна по типу).

Все имена методов — реальные Objective-C selrefs/CString, извлечённые из
`__objc_methname`/cstring-секций соответствующего бинаря. Имена syscall-стабов
— signature-matched (см. ограничение по `.dyldlinkedit` в 01_INVENTORY).

---

## Граница T1 — Хост (USB/pairing) → atc / AirTraffic (media sync)

- **[OBSERVED]** atc слушает `com.apple.atc.xpc`, `com.apple.atc2`,
  `com.apple.private.alloy.airtraffic-idswake` (launchd plist), работает от
  `mobile`, seatbelt-profile `AirTraffic`, jail в `/var/mobile/Media`.
- **[OBSERVED]** atc принимает сериализованные «assets» с host-контролируемым
  `AssetID`/путём — входные данные недоверенные (host может слать `../../`).
- **[OBSERVED]** до B3 применялась *строковая* проверка «outside of AFC root»,
  обойдённая `../../`+symlink; B3 заменил на dirfd-bound `open`+`mkdirat`+
  `renameatx_np`+`unlinkat` + отказ ядра errno 107.
- **[INFERRED]** доверие: host считается полу-доверенным (paired), но его
  пути НЕ доверены — Apple явно признал это, переведя проверку из userspace-
  строки в kernel-anchored resolution.
- **[DEFECT-CLASS]** path traversal / symlink race / TOCTOU на move;
  confused deputy (atc записывает от имени host). Класс **активно
  смягчён в B3** — но остаточные риски: (а) промежуточные symlink'и внутри
  Media, (б) тип корневого fd (dirfd vs chroot) не подтверждён, (в) rename
  с RENAME_NOFOLLOW покрывает только последний компонент.

## Граница T2 — Любой клиент → installd (`com.apple.mobile.installd`)

- **[OBSERVED]** installd (`_installd`, группа `_installd`) — privileged
  system daemon; Mach-service `com.apple.mobile.installd`.
- **[OBSERVED]** ObjC-слой `MIClientConnection` экспонирует ~60+ вызовов:
  `_doInstallationForURL:`, `_installURL:`, `_uninstallIdentities:`,
  `_stageURL:`, `installParallelPlaceholderForStagedIdentifier:`,
  `checkCapabilities:withOptions:`, `cloneSerializedPlaceholderForInstalledAppWithBundeID:personaUniqueString:atResultURL:`,
  `enrollPersona:forApps:`, `addDataSeparatedAppsWithBundleIDs:toPersona:`,
  `fetchInfoForContainerizedAppWithIdentity:`, `dieForTesting` и др.
- **[OBSERVED]** клиентская аутентификация присутствует:
  `_audit_token_to_pid`, `installationRequestorAuditToken`, `auditToken`,
  `getValue:forEntitlement:fromProcessWithAuditToken:error:`,
  `_validateInstallRequestForURL:identity:targetingDomain:options:withError:`,
  `_validateArgsForMethodWithName:bundleIdentifier:`,
  `_shouldSkipEligibilityChecksForInstallRequestorWithAuditToken:`.
- **[OBSERVED]** entitlement `com.apple.private.sandbox.profile:embedded`
  (embedded profile), `MobileContainerManager.allowed`,
  `MobileInstallationHelperService.allowed`, `uninstall.deletion`.
- **[INFERRED]** доверие: installd — классический confused deputy.
  Разные вызовы требуют разных entitlement (install vs uninstall vs
  persona vs fetch); проверка — по audit_token вызывающего.
- **[DEFECT-CLASS]** (а) неоднородная авторизация — какой-то метод из
  60+ может пропускать entitlement-check, который есть у соседних;
  (б) TOCTOU между `_validate*` и исполнением; (в) `dieForTesting`,
  `clearTestFlags:`, `setTestFlags` — test-hooks, достижимые ли они без
  entitlement?; (г) URL-based install (`_installURL:`, `_stageURL:`) —
  обработчик недоверенного URL/пути → path/parse bugs. **Требует
  построчного аудита каждого метода на наличие вызова
  `getValue:forEntitlement:…`/audit-проверки — не факт, что все покрыты.**

## Граница T3 — Любой клиент → amfid (`com.apple.amfi.usernotifications` + private)

- **[OBSERVED]** amfid — code-signing/trust evaluator. `- [AMFIDelegate
  listener:shouldAcceptNewConnection:]` — точка приёма XPC.
- **[OBSERVED]** `AMFIService` методы МУТИРУЮТ состояние доверия:
  `setTrustForTeamID:withSignature:withSignType:`, `setManagedState:`,
  `setDemoState:`, `setSupervisedState:`, `commitProfileForUuid:`,
  `stageProfileForUuid:`, `removeTrustforTeamID:`, `signTeamID:`,
  `removeManagedStateWithReply:`, `initiateDeveloperModeDaemons`.
- **[OBSERVED]** проверки: `verifyBoolEntitlement:`, строки
  `bad security token {…}`, `parseEntitlements`, `Being asked to construct
  DER entitlements`, `invalid XPC action`, `unable to vm_read profileAuxSig`.
- **[OBSERVED]** entitlements: `private.amfi.developer-mode-control`,
  `private.amfi.set-demo`, `private.mis.trust.set`,
  `managedconfiguration.feature-setting.trustedCodeSigningIdentities`.
- **[INFERRED]** доверие: каждый mutating-метод должен требовать своего
  entitlement; `setTrustForTeamID:` — высочайший риск (добавление доверенного
  подписчика = обход проверки подписи для приложений).
- **[DEFECT-CLASS]** confused deputy (клиент без `mis.trust.set` вызывает
  `setTrustForTeamID:`?); несоответствие entitlement-gating между
  read-методами и write-методами; `bad security token` → путь, где токен
  читается не из audit_token а из клиентских данных. **Ключевой вопрос:
  единообразно ли гейтятся все `set*`/`commit*`/`stage*`/`sign*` методы.**

## Граница T4 — Ядро (XNU) → все userspace (syscall/sandbox)

- **[OBSERVED]** `kernelcache.release.iPhone16,1` (filetype=12) для B2 и B3;
  `com.apple.security.sandbox` kext для B2 и B3.
- **[OBSERVED]** errno 107 «Capabilities insufficient» возвращается ядром
  при dirfd-relative move, когда resolved-destination выходит за AFC root —
  то есть capability/sandbox-проверка в VFS/namei-пути ядра, а не в atc.
- **[INFERRED]** финальный арбитр границы — ядро: даже если atc обманут
  строкой, ядро отказывает. Это defense-in-depth.
- **[DEFECT-CLASS]** sandbox-обход; несоответствие между тем, что проверяет
  userspace, и тем, что форсит ядро; capability-граница, которую можно
  подать иначе (другой syscall, флаг, fd-тип). **Анализ kernelcache —
  самый трудоёмкий, но и самый доказательный путь.**

## Граница T5 — mobile-даemons с широкими entitlements (atc, dataaccessd, streaming_zip_conduit)

- **[OBSERVED]** atc (`mobile`) имеет 82 entitlement-ключа — tcc.allow,
  mobileinstall.allowedSPI, InstallCoordination.allowed, private.* —
  т.е. **низкопривилегированный uid с широкими capabilities**.
- **[OBSERVED]** dataaccessd (`mobile`), streaming_zip_conduit (`mobile`).
- **[INFERRED]** uid `mobile` ≠ низкий риск: entitlement-модель даёт этим
  демонам точечные, но мощные права. Компрометация любого — доступ к
  соответствующим private-SPI.
- **[DEFECT-CLASS]** lateral movement: уязвимость в одном mobile-демоне →
  доступ к его entitlement-набору; confused deputy через XPC-делегацию.

## Сводная таблица приоритета границ

| Граница | Вход | Привилегия цели | Класс дефекта | Доказуемость offline |
|---|---|---|---|---|
| T2 installd | XPC от любого app | `_installd`, install/uninstall | uneven auth, TOCTOU, URL-parse | ВЫСОКАЯ (методы+строки видны) |
| T3 amfid | XPC | root-trust, codesign | confused deputy, uneven gating | ВЫСОКАЯ |
| T1 atc/AirTraffic | host USB/paired | `mobile`+Media | traversal, symlink race | ВЫСОКАЯ (уже частично доказано) |
| T5 mobile-daemons | XPC | `mobile`+ents | lateral movement | СРЕДНЯЯ |
| T4 kernel/sandbox | syscall | ring-0 | sandbox bypass | НИЗКАЯ (нужен разбор kext) |

Следующий шаг (03): для T2/T3 построчно проверить, какие методы вызывают
audit/entitlement-проверку, а какие — нет; для T1 — завершить модель
confinement (тип root-fd, промежуточные symlink).
