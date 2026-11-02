# PHASE6 — PHASE6_SUMMARY

## Scope and method

Phase 6 — это статический офлайн-аудит IPC/XPC authorization для трёх выбранных служб:

1. `com.apple.mobile.installd`;
2. `amfid` / `AMFIService`;
3. `com.apple.atc` / AirTraffic host.

Не выполнялись подключения к iPhone, активные IPC/XPC-запросы, fuzzing, race tests, payload development, sandbox bypass или modification of system binaries. Предыдущие Phase 1–5 отчёты не изменялись.

## Что установлено

### `installd`

`MobileInstallationServiceDelegate listener:shouldAcceptNewConnection:` выполняет NSXPC setup: exported interface/object, remote interface, connection storage, handlers, `resume`, затем возвращает `1`. В этом accept callsite не наблюдается direct audit-token или entitlement rejection branch.

Это только архитектурное наблюдение. Phase 2/6 также подтверждает per-method и downstream authorization: install/uninstall/revert paths ведут в internal validation; destructive test methods вызывают `_ValidateMIAllowedSPIEntitlement`; registration trigger проверяет test mode/flags. 12 из 75 exported protocol methods не показывают direct helper call в просмотренном wrapper set, но для них не восстановлены одновременно complete downstream graph, endpoint reachability и sensitivity. Статус: **INSUFFICIENT EVIDENCE**, не confirmed issue.

`checkCapabilities:` выглядит read-only и в доступном callsite не имеет direct helper gate; security-sensitive effect не доказан. `getPidForTesting` возвращает PID daemon'а без видимой мутации.

### `amfid`

NSXPC listener создаётся с Mach service `com.apple.amfi.nsxpc`; `AMFIDelegate` сохраняет connection в `AMFIService`, устанавливает `proto_AMFIProtocol`, exported object, вызывает `resume` и возвращает `1`. В listener нет visible rejection branch.

При этом `verifyBoolEntitlement:` получает entitlement через `NSXPCConnection valueForEntitlement:` и fail-closed обрабатывает missing/invalid values. Все просмотренные state-changing методы имеют method-specific checks:

- `com.apple.private.amfi.set-trust`;
- `set-supervised`;
- `set-demo`;
- `set-managed`;
- `data-migration`;
- `developer-mode-control`;
- `schedule-profile`;
- `commit-profile`;
- `remove-trust`.

`getSEPStateWithReply:` и `getStagedProfileWithReply:` не показывают такого gate и рассматриваются как read-oriented. Однако protocol exposure, bootstrap policy, caller reachability и sensitivity ответа не доказаны полностью. Это **INSUFFICIENT EVIDENCE**, а не vulnerability.

По amfid B2/B3 disassembly texts byte-for-byte identical; normalized authorization paths совпадают. Entitlement plists также line-for-line совпадают. Нет наблюдаемого IPC authorization regression/fix между B2 и B3.

Найденные security-token strings не доказывают связь с NSXPC caller audit token. Прямое использование `audit_token_t`, `SecTaskCopyValueForEntitlement`, `xpc_connection_get_audit_token/euid/pid` в доступном material не установлено. Это **NOT VERIFIED**, не `CONTRADICTED`.

### `atc`

Launchd plist подтверждает несколько AirTraffic service names, daemon user `mobile`, private AirTraffic entitlements и seatbelt profile. Startup code показывает `ATDeviceService`, `MSVXPCTransaction` и `ATSession`, но полный incoming handler map и per-session caller authorization не восстановлены.

B3 AirTraffic move path использует directory-FD-relative/kernel-mediated confinement; tested destination за AFC root получает capability failure. Это подтверждает filesystem boundary для рассмотренного пути, но не заменяет IPC caller authorization. Confused-deputy hypothesis остаётся **INSUFFICIENT EVIDENCE**, поскольку недостаточно привилегированный клиент, его endpoint reachability и конкретный privileged effect не доказаны.

Доступный `atc` host normalized diff не показывает B2/B3 IPC authorization delta. Существенное изменение относится к AirTraffic framework filesystem confinement.

## Кандидатные гипотезы

Проверены не более трёх гипотез:

1. uneven/transitive authorization на 12 no-direct-gate `installd` methods;
2. no-gate AMFI getters;
3. confused deputy через atc session/asset endpoints.

Ни одна не достигла статуса `PLAUSIBLE / NEEDS VALIDATION` как конкретная security vulnerability: во всех случаях отсутствует доказанная цепочка от insufficiently privileged client до sensitive operation.

## Findings registry

| Classification | Result |
|---|---|
| `CONFIRMED SECURITY ISSUE` | none |
| `PLAUSIBLE / NEEDS VALIDATION` | none as a concrete vulnerability |
| `ARCHITECTURAL OBSERVATION` | accept/setup before method gates; visible AMFI mutator gates; AirTraffic filesystem confinement |
| `INSUFFICIENT EVIDENCE` | installd no-direct-gate set; AMFI getter reachability; atc caller authorization; audit-token linkage |
| `RULED OUT` | only narrow claim of an observed B2→B3 amfid/atc-host IPC authorization delta in analyzed material |

## Main limitations

- Full launchd bootstrap and Mach lookup policy for each client category is unavailable.
- Full sandbox/seatbelt rules are not reconstructed.
- atc incoming protocol and all session handlers are not fully available.
- amfid protocol declaration is represented by recovered pointer, not independent source header.
- Delegated MIS/framework cryptographic semantics are outside the available disassembly.
- Static absence of an API call is not proof of absence of equivalent authorization in another layer.

## Final conclusion

Phase 6 не выявила подтверждённой IPC/XPC authorization vulnerability. Она установила более узкую картину: accept-time setup у `installd` и `amfid` выглядит permissive в видимом listener code, но sensitive mutating operations имеют downstream/per-method checks; atc имеет сильную filesystem confinement boundary, однако caller authorization не восстановлена полностью. Не следует превращать эти gaps в security claim без endpoint reachability, client identity и sensitive-effect evidence.
