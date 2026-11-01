# 03_IPC_SECURITY_REVIEW — аудит IPC/XPC-границ (installd, amfid, atc)

Метод: статический дизасм `installd_B3.bin` (ipsw + ручной разбор),
`__objc_methname`/`__objc_data` дают реальные имена методов и точки входа.
`ipsw macho disass` разрешает `bl`-цели в имена — поэтому проверка наличия
gate делается по факту вызова валидатора, а не по предположению.

Важная оговорка (повторяется во всех выводах): отсутствие видимого
entitlement-gate в одном методе ≠ уязвимость. Авторизация может
(а) выполняться централизованно при accept соединения, (б) вызываться
ниже по стеку в привилегированном действии, (в) быть ненужной для
read-only метода. Каждый случай помечен.

---

## A. installd — `com.apple.mobile.installd` (MobileInstallerProtocol, ~97 методов)

### A.1 Connection-accept НЕ проверяет entitlement [OBSERVED, HIGH]
`-[MobileInstallationServiceDelegate listener:shouldAcceptNewConnection:]`
(0x10001b280–0x10001b33c):
```
setExportedInterface: ; objc_opt_new MIClientConnection ;
setExportedObject: ; setRemoteObjectInterface: ; setXpcConnection: ;
setInterruptionHandler: ; setInvalidationHandler: ; resume ;
mov w0, #0x1 ; retab
```
Функция **линейная, без ветвлений, возвращает 1** — принимает любое
соединение. Никакого `valueForEntitlement`/`audit_token` в accept-фазе нет.
=> Авторизация полностью отложена на уровень методов. Это само по себе
не уязвимость (валидная схема «accept-all, gate-per-method»), но она
переносит всю нагрузку на корректность per-method gating — см. A.3.

### A.2 Централизованные валидаторы [OBSERVED, HIGH]
Есть helper `sub_10001c7c4` = `_ValidateMIAllowedSPIEntitlement`:
`xpcConnection → valueForEntitlement:@"com.apple.private.mobileinstall.allowedSPI"
 → isKindOfClass NSString → isEqualToString:  (или NSArray-ветка)`
и вторая группа валидаторов `0x10001e3xx`/`0x10001e40c` (другие entitlement —
persona/registration semantics). Методы вызывают их в прологе.

### A.3 Пер-метод покрытие gate — НЕРАВНОМЕРНО [OBSERVED, HIGH]
Просканированы все 97 методов `MIClientConnection` на вызов валидатора.
- **GATED (68):** installParallelPlaceholder, finalizeStagedInstall,
  revertForIXWithIdentity, _uninstallIdentities, registerContentsOnRoot/
  unregisterContentsOnRoot, persona-методы (add/remove/enroll/setPersonas,
  dataSeparated), reference-методы, test-хуки (dieForTesting, setTestFlags,
  setTestMode, raiseException, setEligibilityTestOverrides),
  setLaunchProhibited, setAppReplacementStatus и др.
- **NO-GATE (29):** прогресс/send-методы (безопасно), accessors, И:
  - `installURL:identity:targetingDomain:options:returningResultInfo:` —
    **НО** немедленно зовёт `_installURL:` → `_validateInstallRequestForURL:`
    (который gated). => транзитивно закрыт. [VERIFIED]
  - `uninstallIdentity:`/`uninstallIdentifiers:`/`revertIdentity:` →
    зовут `_uninstallIdentities:`/`revertForIXWithIdentity:` (gated). [VERIFIED]
  - `_stageURL:`/`stageInstallURL:`/`_doInstallationForURL:`/`_installURL:` —
    внутренние, достигаются через gated-путь либо через _validateInstallRequest.
  - **`checkCapabilities:withOptions:completion:` — НЕТ gate, и НЕТ вызова
    валидатора.** Делегирует `defaultManager checkCapabilities:withOptions:error:`.
    Read-only запрос возможностей — вероятно намеренно открыт (низкий риск),
    но это подтверждённый пример неоднородности: метод протокола без проверки.
    [NEEDS_REVIEW]
  - `getPidForTestingWithCompletion:`, `referencesForBundleWithIdentifier:`,
    `_triggerRegistrationForContent:`, `triggerRegistrationForContainerizedContent...`,
    `triggerRegistrationForDiskImageContent...` — no-gate; требуют
    проверки, что их привилегированное действие само gated ниже. [NEEDS_REVIEW]

### A.4 Вывод по installd
Схема «accept-all + gate-per-method» подтверждена. Защита корректна там,
где публичный метод делегирует в gated `_validate*`/`*_internal`. Риск —
**дрейф покрытия**: любой метод, добавленный без вызова валидатора, открыт.
`checkCapabilities:` — live-пример такого метода. Это класс
"uneven authorization on sibling operations" — отмечаем как NEEDS_REVIEW,
не как дыру: настоящий вред зависит от того, что делает метод, и от того,
кто может достичь Mach-service (bootstrap/Sandbox ограничивает клиентов
до entitled-процессов на iOS — см. A.5).

### A.5 Кто может вообще подключиться [OBSERVED/INFERRED]
`com.apple.mobile.installd` — named Mach-service. На iOS lookup ограничен
sandbox/entitlement (`com.apple.private.MobileInstallationHelperService.allowed`
и др.). Демон `_installd`. Произвольный app не имеет bootstrap-доступа;
привилегированные системные процессы — имеют. => Граница реальна, но
круг клиентов узок. [INFERRED]

## B. amfid — `AMFIService` (mutating trust-state методы)

- `[OBSERVED]` `-[AMFIDelegate listener:shouldAcceptNewConnection:]` есть;
  mutating-методы: `setTrustForTeamID:`, `setManagedState:`, `setDemoState:`,
  `commitProfileForUuid:`, `stageProfileForUuid:`, `signTeamID:`,
  `removeTrustforTeamID:`, `setSupervisedState:`.
- `[OBSERVED]` в бинаре есть `verifyBoolEntitlement:`, строки
  `bad security token`, `parseEntitlements`, `invalid XPC action`.
- `[NEEDS_REVIEW]` НЕ разобрано построчно (amfid — отдельная цель, меньше
  ObjC-методов): единообразно ли гейтятся все `set*/commit*/stage*/sign*`.
  Особый интерес — `setTrustForTeamID:` (добавление trusted signer) и
  `developer-mode-control`/`set-demo` пути. => Зафиксировано как цель
  следующего прохода, а не как вывод.

## C. atc / AirTraffic — host-input граница
(детально в предыдущих отчётах; здесь — кратко, т.к. уже доказано)
- `[OBSERVED]` accept-фаза и per-asset move; B3 dirfd-bound + kernel refuse.
  Граница усилена. Остаточные вопросы: тип root-fd, промежуточные symlink.

## D. Сквозной вывод для 06_FINDINGS
1. installd accept-all + частичный per-method gating → IOS-SEC-001
   (uneven authorization), `checkCapabilities:` и triggerRegistration* как
   конкретные no-gate методы — NEEDS_REVIEW.
2. amfid mutating-methods coverage → IOS-SEC-002 — NEEDS_REVIEW (нужен
   дизасм amfid_B3).
3. Отсутствие accept-time gate — зафиксировано как архитектурный факт,
   не дефект; повышает ценность любого no-gate метода.

След. шаги: разобрать amfid методы (та же техника), и подтвердить, что
`triggerRegistrationFor*`/`referencesForBundle`/`getPidForTesting` не
достигают привилегированного действия без gate.
