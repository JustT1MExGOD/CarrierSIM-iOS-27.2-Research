# PHASE6 — 04_TRUST_BOUNDARY_MATRIX

## Правила чтения

Матрица разделяет четыре разные границы: lookup/bootstrap, принятие соединения, method-level authorization и защиту самой операции. `Mach service` в plist или `return 1` из `shouldAcceptNewConnection:` не доказывают, что любой непривилегированный процесс может достичь метода. `NOT VERIFIED` означает отсутствие локального доказательства, а не опровержение.

## Матрица

| Служба/граница | Локально подтверждено | Не подтверждено | Оценка |
|---|---|---|---|
| `installd` launchd/bootstrap | label, Mach service `com.apple.mobile.installd`, daemon identity `_installd` | bootstrap namespace, sandbox `mach-lookup`, client classes | NOT VERIFIED для reachability |
| `installd` NSXPC accept | `setExportedInterface`, `setExportedObject`, `setRemoteObjectInterface`, `resume`, `return 1` | accept-time audit/entitlement rejection | ARCHITECTURAL OBSERVATION |
| `installd` install/uninstall | exported wrappers lead to internal request/identity validation and gated paths in examined call graph | complete coverage of every wrapper and every helper-side path | gated in examined paths; globally PARTIAL |
| `installd` 12 methods without direct helper call | direct gate absent in examined wrapper set | downstream authorization for every method; client reachability; effect classification for each | INSUFFICIENT EVIDENCE |
| `installd` `checkCapabilities` | type validation, manager call, capability response | whether all callers are trusted; exact information sensitivity | read-only observation |
| `installd` test hooks | destructive hooks visibly call `_ValidateMIAllowedSPIEntitlement`; registration path checks test mode/flags | complete state-setting path and bootstrap restrictions | no confirmed missing gate |
| `amfid` Mach bootstrap | `bootstrap_check_in` for `com.apple.MobileFileIntegrity` in separate path | complete MIG policy and caller classes | NOT VERIFIED |
| `amfid` NSXPC endpoint | `com.apple.amfi.nsxpc`; listener setup; accept method returns `1` | launchd/sandbox lookup restrictions | ARCHITECTURAL OBSERVATION |
| `amfid` mutating selectors | method-specific `verifyBoolEntitlement:` gates for examined state-changing methods | full protocol declaration and delegated MIS cryptographic semantics | gated in examined methods |
| `amfid` getters | `getSEPState` and `getStagedProfile` have no visible entitlement gate | exposure, protocol reachability, sensitivity, caller policy | INSUFFICIENT EVIDENCE |
| `amfid` caller identity | `NSXPCConnection valueForEntitlement:` is used by verifier | direct `audit_token_t`, `SecTask`, euid/pid linkage | NOT VERIFIED |
| `atc` launchd/bootstrap | plist lists multiple AirTraffic services; daemon runs as `mobile`; private entitlements/profile present | which client categories can lookup each name | NOT VERIFIED |
| `atc` session/asset handler | host/session setup and tested B3 dirfd-relative operation | complete handler map and per-client entitlement checks | IPC authorization NOT VERIFIED |
| `atc` filesystem operation | B3 kernel/VFS confinement rejects tested destination outside AFC root | whether every handler uses same anchored mechanism | protection confirmed only for tested path |

## Boundary-specific conclusion

Наиболее сильное доказательство в корпусе относится к method-level gating у mutating методов `installd` и `amfid`, а также к filesystem confinement AirTraffic. Наименее восстановлены bootstrap restrictions, full sandbox rules и complete atc session authorization. Поэтому ни одна строка `accept-all` не переводится автоматически в `CONFIRMED SECURITY ISSUE`.
