# PHASE6 — 03_AUTHORIZATION_FLOW

## Метод

Для каждой чувствительной группы отделены: endpoint reachability, exported protocol reachability, per-method authorization, downstream authorization и собственно privileged operation. Отсутствие gate в одном прологе не рассматривается как отсутствие авторизации во всей цепочке.

## A. installd flows

### A1. install

```text
client -> com.apple.mobile.installd -> NSXPC accept
       -> exported installURL:...
       -> _installURL:
       -> _validateInstallRequestForURL:identity:targetingDomain:options:withError:
       -> install/stage helpers
       -> filesystem/install operation
```

`installURL:...` не имеет inline direct gate в просмотренном прологе, но Phase 2 подтвердил транзитивный call в `_validateInstallRequestForURL:`. Прямой gate наблюдается у relevant internal validation path. Итог: **transitively gated in examined path**.

### A2. uninstall/revert

```text
client -> exported uninstallIdentity/uninstallIdentifiers/revertIdentity
       -> _uninstallIdentities: or revertForIXWithIdentity:
       -> entitlement validator / internal gate
       -> removal or revert operation
```

Прямой gate может отсутствовать у exported wrapper, но internal operation вызывает gated routine. Итог: **transitively gated in examined path**.

### A3. registration trigger

```text
client -> exported triggerRegistrationFor...
       -> _triggerRegistrationForContent:...
       -> MITestManager isRunningInTestMode:
       -> testFlagsAreSet:#2 / #0x10
       -> gatherer / removeItemAtURL / registration state
```

В [installd_B3_disasm.txt:47132-47228] видны test-mode checks; при flag `#0x10` удаляется test sentinel URL, а затем запускается registration gatherer. Публичный wrapper не показывает direct SPI entitlement gate в просмотренном callsite. Однако enabling test mode/flags methods сами gated, согласно Phase 2. Итог: **test-state mediated; no confirmed missing authorization**.

### A4. `checkCapabilities`

```text
client -> exported checkCapabilities:withOptions:completion:
       -> NSDictionary type check
       -> MICapabilitiesManager defaultManager
       -> checkCapabilities:withOptions:error:
       -> reply
```

В [installd_B3_disasm.txt:40217-40271] видны type check и manager call, но не entitlement validator. Операция read-only: capability result и `CapabilitiesMatch`/`MismatchedCapabilities` response. Итог: **observed no direct gate; sensitive privileged effect not demonstrated**.

### A5. `getPidForTesting`

```text
client -> exported getPidForTestingWithCompletion:
       -> getpid()
       -> completion(pid)
```

[installd_B3_disasm.txt:46584-46597]. Нет direct gate; операция возвращает PID daemon'а и не выполняет privileged mutation. Информационный эффект возможен, но security boundary violation не доказан.

### A6. Test destructive methods

`dieForTesting` и `raiseExceptionWithCompletion:` вызывают `_ValidateMIAllowedSPIEntitlement` с `UnitTestRunner` в просмотренном callsite ([installd_B3_disasm.txt:46610-46618] и 46634+). Это подтверждает, что опасные test hooks не являются необусловленно открытыми в этом участке.

## B. amfid flows

Из доступных strings/selectors восстановлено:

```text
client -> AMFI XPC listener -> AMFIService method
       -> verifyBoolEntitlement / security-token / signature-related checks
       -> trust/profile/developer-mode operation
```

Однако без полного line-by-line map всех exported AMFIService methods нельзя утверждать, что каждый mutating selector достигает validator. Статус конкретного missing-gate claim: **NOT VERIFIED**.

## C. atc flows

```text
host/client -> atc Mach/XPC endpoint -> session/asset handler
            -> path/asset validation and AirTraffic operation
            -> B3 dirfd-relative move + kernel/VFS restriction
```

Подтверждена сильная filesystem boundary для tested move path. Полный caller entitlement check до session creation в atc binary не восстановлен. Поэтому kernel/path confinement нельзя ошибочно назвать IPC caller authorization.

## Транзитивная авторизация

| Flow | Direct gate | Downstream gate/state | Final static assessment |
|---|---|---|---|
| installd install | не в wrapper | `_validateInstallRequest...` | gated in examined path |
| installd uninstall/revert | не всегда wrapper | gated internal methods | gated in examined path |
| installd trigger registration | no direct SPI in wrapper | test-mode + test flags | architectural protection; full endpoint reachability gap |
| installd checkCapabilities | no direct gate | read-only manager call | no-gate observation; no sensitive impact shown |
| installd getPidForTesting | no direct gate | none | trivial information response |
| amfid mutators | validators/strings present | full per-method map incomplete | NOT VERIFIED globally |
| atc asset move | caller gate incomplete | dirfd + kernel confinement | filesystem protection confirmed; IPC auth NOT VERIFIED |
