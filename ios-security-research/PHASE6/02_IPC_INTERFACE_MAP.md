# PHASE6 — 02_IPC_INTERFACE_MAP

## 1. `com.apple.mobile.installd`

### Endpoint and launch configuration

Локальный launchd plist `tmp_com.apple.mobile.installd.plist` показывает:

- label: `com.apple.mobile.installd`;
- Mach service: `com.apple.mobile.installd`;
- program: `/usr/libexec/installd`;
- user/group: `_installd`;
- `POSIXSpawnType=Adaptive`.

Это подтверждено plist; допустимость Mach lookup для конкретных классов клиентов в полном bootstrap/sandbox policy не восстановлена.

### IPC type

В `installd_B3_disasm.txt` [MobileInstallationServiceDelegate listener:shouldAcceptNewConnection:] (строки 28641–28689) видна NSXPC setup sequence:

1. `setExportedInterface:`;
2. создание `MIClientConnection`;
3. `setExportedObject:`;
4. `setRemoteObjectInterface:`;
5. `setXpcConnection:`;
6. interruption/invalidation handlers;
7. `resume`;
8. return `1`.

В accept function не наблюдается entitlement или audit-token branch.

### Exported interface

`MobileInstallerProtocol` содержит 75 экспортируемых protocol methods по `protocol_mobileinstaller.txt`. Среди них install/stage/uninstall, persona/container, references, capabilities и test-related methods. Внутренние `_` methods не являются protocol methods и не могут быть вызваны через этот exported interface напрямую.

### Authorization-relevant handlers

| Группа | Примеры | Наблюдаемая операция |
|---|---|---|
| Installation | `installURL:identity:targetingDomain:options:returningResultInfo:`; staging/finalization | создание/обновление install state и bundle |
| Removal/revert | `uninstallIdentity:`; `uninstallIdentifiers:`; `revertIdentity:` | удаление/revert через internal routines |
| Registration | `triggerRegistrationForContainerizedContent...`; disk-image variant | registration gatherer и file operations в test-mode path |
| Personas/references | `addPersona`, `removePersona`, reference methods | persona and app-reference state |
| Capabilities | `checkCapabilities:withOptions:completion:` | read-only capability result |
| Test | `getPidForTesting`, `dieForTesting`, test flags/mode | trivial or gated test operations |

## 2. `amfid` / `AMFIService`

### Endpoint

В `amfid_B3` присутствует `AMFIDelegate listener:shouldAcceptNewConnection:` и exported `AMFIService` methods. В текущем корпусе нет полного launchd plist с восстановленным Mach-service map для amfid; поэтому endpoint name и bootstrap restrictions для каждой клиентской категории: **NOT VERIFIED**.

### Sensitive methods

Строки/ObjC selectors указывают на методы, меняющие trust or policy state:

- `setTrustForTeamID:withSignature:withSignType:`;
- `setManagedState:`;
- `setDemoState:`;
- `setSupervisedState:`;
- `commitProfileForUuid:`;
- `stageProfileForUuid:`;
- `removeTrustforTeamID:`;
- `signTeamID:`;
- `initiateDeveloperModeDaemons`.

Также найдены `verifyBoolEntitlement:`, `bad security token`, `parseEntitlements`, `invalid XPC action` и `profileAuxSig` validation strings. Полное соответствие каждого selector каждому validator callsite не считается установленным без отдельного покрытия всех методов.

## 3. `com.apple.atc` / AirTraffic host

### Endpoint and launch configuration

Проверенный plist показывает:

- label: `com.apple.atc`;
- program: `/usr/libexec/atc`;
- user: `mobile`;
- Mach services: `com.apple.atc`, `com.apple.atc.xpc`, `.service`, `.sessions`, `.observer`, `.downloadprogress`, `.icappobserverdelegate`, `.runkeeplocaltask`, `com.apple.atc2`, `com.apple.private.alloy.airtraffic-idswake`.

Entitlements atc B3 включают `com.apple.private.alloy.airtraffic`, `com.apple.private.mobileinstall.allowedSPI`, `com.apple.private.InstallCoordination.allowed`, `mach-lookup.global-name` и seatbelt profile `AirTraffic`.

### Handlers and operation

В доступном atc disassembly виден startup/setup через `ATDeviceService`, `ATSession`, `MSVXPCTransaction`; AirTraffic move routine ранее восстановлена как asset/session path, принимающая host-controlled asset metadata and paths. B3 uses directory-FD-relative operations and kernel-mediated refusal for the tested out-of-root destination.

Полный список exported XPC methods и построчная проверка каждого handler's caller authorization в текущем корпусе не восстановлены.

## 4. Authorization API search

По доступному `installd` material подтверждены:

- `valueForEntitlement:` для `com.apple.private.mobileinstall.allowedSPI`;
- `clientName` built from XPC process identifier/effective UID/GID;
- internal audit-token-related methods in install request validation;
- per-method validators.

Не найдено как локально доказанный direct callsite в выбранных материалах:

- `xpc_connection_get_audit_token`;
- `xpc_connection_get_euid`;
- `xpc_connection_get_pid`;
- `SecTaskCopyValueForEntitlement`.

Это не означает отсутствия эквивалентной authorization logic: Objective-C `NSXPCConnection` methods, audit-token helper и downstream validation могут выполнять ту же роль.
