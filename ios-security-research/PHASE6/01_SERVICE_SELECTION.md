# PHASE6 — 01_SERVICE_SELECTION

## Режим

Phase 6 выполняется только статически и офлайн. Не выполняются активные IPC/XPC-запросы, не подключается iPhone, не запускаются fuzzing/race tests, не создаются payloads и не модифицируются системные бинарники.

## Критерии выбора

Выбраны только службы, для которых одновременно доступны хотя бы бинарь или существенный disassembly, launchd/Mach-service сведения и entitlement material либо предыдущий IPC-анализ. Служба не выбиралась только из-за слова `root`/`privileged`.

## Выбранные службы

| Служба | Бинарь | IPC evidence | Privileged operation | Почему выбрана |
|---|---|---|---|---|
| `com.apple.mobile.installd` | `installd_B2.bin`, `installd_B3.bin`; полный annotated disassembly | `MobileInstallerProtocol`, `NSXPCListener`, `MobileInstallationServiceDelegate` | install, uninstall, staging, registration, persona/container operations | наиболее полный код и уже установленный Phase 1–2 call graph |
| `amfid` / `AMFIService` | `amfid_B2.bin`, `amfid_B3.bin`; annotated disassembly | `AMFIDelegate listener:shouldAcceptNewConnection:`, AMFI service methods | trust/signing/profile/developer-mode state | sensitive trust-state operations и отдельный entitlement evidence |
| `com.apple.atc` / AirTraffic host | `atc_B2.bin`, `atc_B3.bin`; full-ish Mach-O/disassembly | multiple Mach services, private AirTraffic interface, asset/session handlers | file movement inside Media, host-controlled sync input | доступный полный-ish host-input boundary и B2→B3 IPC/filesystem comparison |

## Не выбранные службы

- `CommCenter`: launchd Mach-service plist доступен, но сам бинарь и реализация обработчиков в текущем корпусе отсутствуют.
- `dataaccessd`: plist доступен, но бинарь/реализация authorization handlers отсутствуют.
- `streaming_zip_conduit`: launchd plist доступен, но реализация обработчиков и полная entitlement-модель отсутствуют.
- `fileproviderd`: только adjacent observations/log evidence; нет достаточного локального endpoint implementation.

Их отсутствие в Phase 6 не означает отсутствия IPC-риска; это ограничение доступного evidence.

## Уровни уверенности

- `installd`: HIGH для наблюдаемых ObjC methods, protocol и per-method gate callsites; bootstrap restriction — NOT VERIFIED.
- `amfid`: MEDIUM/HIGH для методов, entitlement strings и обнаруженных validators; полное покрытие всех mutating methods требует отдельного disassembly review.
- `atc`: MEDIUM/HIGH для launchd services, entitlements и AirTraffic move path; complete accept-time/per-method client authorization — NOT VERIFIED.
