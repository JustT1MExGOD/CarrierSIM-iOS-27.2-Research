# PHASE2_IPC_VERIFICATION — независимая проверка IOS-SEC-001 и IOS-SEC-002

Метод: статический дизасм `installd_B3.bin` / `amfid_B3.bin` (ipsw разрешает
`bl`-цели в имена ObjC-методов), launchd plist `com.apple.mobile.installd`,
протокол `MobileInstallerProtocol` (извлечён из `__objc_protolist`).

**Ключевая рамка, которой не хватало в Phase 1:** на iOS/XPC авторизация —
двухслойная по замыслу: (1) **Mach bootstrap / named-service lookup**
ограничивает, кто вообще получает endpoint; (2) **per-method `valueForEntitlement`/
`verifyBoolEntitlement`** внутри обработчика. `listener:shouldAcceptNewConnection:`
в типовом Apple NSXPC-сервисе — это место для *настройки* соединения
(setExportedInterface/Object, resume), а не для проверки прав — проверка
осознанно отложена в методы. Поэтому «accept-all, return 1» — это
**архитектурная норма**, а не дефект, и его нельзя считать доказательством
дыры без доп. фактов.

---

## A. Механизм авторизации (установлено)

1. **Mach-service config** (`tmp_com.apple.mobile.installd.plist`):
   `MachServices={com.apple.mobile.installd: true}`, `UserName=_installd`,
   `GroupName=_installd`, `POSIXSpawnType=Adaptive`. В plist нет явных
   client-restriction-ключей. Точный entitlement/sandbox rule, который
   ограничивает bootstrap lookup именно этого Mach-service, в локальных
   материалах не установлен; это остаётся GAP, а не доказанный факт.
   Демон `_installd` — выделенный uid.
2. **Accept-фаза:** `-[MobileInstallationServiceDelegate
   listener:shouldAcceptNewConnection:]` (0x10001b280–0x10001b33c) —
   линейная, `setExportedInterface:`/`setExportedObject:`/`resume`/`return 1`.
   Без ветвлений, без `valueForEntitlement`, без `audit_token`.
   => **принятие соединения = безусловно.** Это факт; но сам по себе не дефект.
3. **Per-method gates:** helper `sub_10001c7c4`=`_ValidateMIAllowedSPIEntitlement`
   читает `xpcConnection → valueForEntitlement:"com.apple.private.mobileinstall.allowedSPI"`
   + `isKindOfClass`/NSArray; вторая группа валидаторов `0x10001e3xx`/`0x10001e40c`
   (persona/registration entitlements). Методы вызывают их в прологе.
4. **Протокол:** `MobileInstallerProtocol` экспортирует **75 методов**. Внутренние
   `_`-методы (`_installURL:`, `_doInstallationForURL:`, `_stageURL:`,
   `_uninstallIdentities:`, `_validateInstallRequestForURL:`, `_triggerRegistrationForContent:`)
   **в протокол НЕ входят** → по NSXPC недостижимы напрямую. Это закрывает
   половину подозрений Phase 1: внутренний метод без gate не опасен, если
   до него нельзя достучаться снаружи.

   Внутри этих 75 экспортируемых методов прямой вызов одного из найденных
   entitlement-helper'ов обнаружен у **63**, а у **12** его нет. Это не
   означает 12 уязвимых методов: `installURL`, `stageInstallURL`,
   `uninstall*` и `revertIdentity` делегируют в закрытые внутренние пути;
   trigger-методы защищены test-mode state; `checkCapabilities` и
   `getPidForTesting` read-only/trivial. Отдельно от этих 75 внутренних
   `MIClientConnection` методов в дизассемблере было 97 — именно оттуда
   произошла прежняя цифра 68/29; она не должна называться числом
   экспортируемых XPC-операций.

## B. Таблица методов (видимая проверка / внешние ограничения / вывод)

| Метод (protocol) | Видимая проверка | Внешние ограничения | Доказательства | Вывод |
|---|---|---|---|---|
| `installURL:…returningResultInfo:` | нет inline gate; → `_installURL:` → `_validateInstallRequestForURL:` (gated) | bootstrap+per-method ниже | `_installURL` 0x10001e50c `bl _validateInstallRequestForURL` | gated транзитивно |
| `uninstallIdentity/Identifiers:` | нет inline; → `_uninstallIdentities:` (gated) | bootstrap | `_uninstallIdentities` вызывает 0x10001c7c4 | gated транзитивно |
| `revertIdentity:` | нет inline; → `revertForIXWithIdentity:` (gated) | bootstrap | revertForIX вызывает gate | gated транзитивно |
| `installParallelPlaceholder…`, `finalizeStagedInstall…`, `registerContentsOnRoot/…OSModule/…DiskImage`, `register/unregisterContentsOnRoot` | прямой `bl 0x10001c7c4`/`0x10001e4xx` | bootstrap | пролог → SPI-валидатор | gated |
| persona-методы (`addPersona/removePersona/enrollPersona/setPersonas/dataSeparated/personasFor…`) | `bl 0x10001e4xx` | bootstrap | валидатор группы 2 | gated |
| reference-методы (`finalize/acquire/invalidateReference`, `referencesForBundle`) | referencesFor — нет gate; остальные gated | bootstrap; `appReferencesEnabled`-флаг | referencesFor вызывает `appReferencesEnabled`,`referencesForIdentifier:inDomain:error:` | см. вывод 3 |
| test-методы (`dieForTesting,setTestMode,…setTestFlags,clearTestFlags,setEligibilityTestOverrides`) | gated | bootstrap | пролог → валидатор | gated |
| `setLaunchProhibited`, `setAppReplacementStatus`, `prepareReplacement`, `pushReplacementInfo`, `endAppReplacement`, `removeAppReplacementState`, `setLaunchWarning`, `cloneSerializedPlaceholder` | gated | bootstrap | пролог → валидатор | gated |
| `checkCapabilities:withOptions:` | **нет gate**; → `defaultManager checkCapabilities:withOptions:error:` | bootstrap | 0x1000259d4 — только check, нет валидатора | no-gate, read-only |
| `getPidForTestingWithCompletion:` | **нет gate**; тело = `getpid()` + reply | bootstrap | 0x10002b504 `bl getpid` — ничего больше | no-gate, тривиально безопасен |
| `triggerRegistrationForContainerizedContentForOptions:` / `…DiskImageContent…` | **нет entitlement-gate**, но **test-mode gate** | bootstrap + `isRunningInTestMode`+`testFlagsAreSet` | см. ниже | test-gated |
| `_triggerRegistrationForContent:` (внутр.) | **нет entitlement-gate**; test-mode gate | не в протоколе (недостижим снаружи) | пролог → MITestManager | недостижим + test-gated |

## C. `triggerRegistrationFor*` — решающий разбор (IOS-SEC-002)

Публичные обёртки — тонкие: `b j__objc_msgSend _triggerRegistrationForContent:…writeLock:1`. Тело `_triggerRegistrationForContent:` (0x10002bcc0) в прологе:
```
MITestManager sharedInstance
→ isRunningInTestMode:outError:        (w26=0 ветка)
→ testFlagsAreSet:#0x2                 → "Triggering registration with test mode enabled"
→ testFlagsAreSet:#0x10                → MIDaemonConfiguration testFileSentinelForSyncURL
→ initWithOptions:forTargetUID:enumerator:
→ performGatherWithError:
→ removeItemAtURL:error:               (удаление — но под test-mode)
```
**Вывод:** привилегированное действие (registration + file ops) выполняется
**только когда включён test-mode**, а test-mode включается через gated
`setTestMode`/`setTestFlags`/`setEligibilityTestOverrides` (все gated). То есть
отсутствие entitlement-gate на самом trigger-калле компенсируется тем, что
состояние, при котором он что-то делает, защищено entitlement'ом на входе.
=> **IOS-SEC-002 по triggerRegistration — АРХИТЕКТУРНОЕ НАБЛЮДЕНИЕ, не дефект.**
Открытый остаток: реально ли `checkCapabilities`/no-gate методы что-то
привилегированное делают — `checkCapabilities` read-only → низкий риск.

## D. Итог по IOS-SEC-001/002

- **IOS-SEC-001** (accept-all + uneven gating): факт accept-all подтверждён,
  но это штатная NSXPC-архитектура; локальный протокол показывает 63/75
  методов с прямым helper-call, а остальные имеют транзитивные, test-mode,
  read-only или trivial объяснения. Точный bootstrap rule не извлечён.
  **→ ARCHITECTURAL OBSERVATION** (не дефект).
- **IOS-SEC-002** (`checkCapabilities`/`triggerRegistration`/no-gate методы):
  `checkCapabilities` — no-gate но read-only; `getPidForTesting` — trivial;
  `triggerRegistration` — gated через test-mode; внутренние `_` недостижимы.
  **→ ARCHITECTURAL OBSERVATION**, без признаков эксплуатируемой дыры.

**Чего не хватает для полного RULED_OUT:** точное bootstrap-ограничение —
какой entitlement реально требуется для lookup `com.apple.mobile.installd`
(из sandbox-профиля `_installd`, который не декомпилирован). Если lookup
доступен широкому кругу — no-gate read-методы становятся поверхностью
информационной утечки, не более. Отмечено как GAP, а не как дыра.
