# PHASE6 — 06_CANDIDATE_VERIFICATION

## H1 — `installd` uneven authorization

### Проверка цепочки

`MobileInstallationServiceDelegate` принимает NSXPC connection и устанавливает `MIClientConnection`. Для install/uninstall/revert просмотренные wrappers ведут в internal validation/gated routines; отдельные test-destructive methods вызывают `_ValidateMIAllowedSPIEntitlement`. Это показывает, что отсутствие inline helper call в wrapper не равно отсутствию authorization.

У 12 из 75 exported protocol methods не найден direct helper call в рассмотренном callsite. Но для каждого из них одновременно не восстановлены: полный downstream call graph, exact client reachability и effective operation sensitivity. Поэтому необходимый мост от «no direct call» к «unprivileged client reaches privileged operation» отсутствует.

**Verdict:** INSUFFICIENT EVIDENCE; architectural observation only. Не `CONFIRMED SECURITY ISSUE`.

## H2 — `amfid` no-gate getters

### Проверка цепочки

`AMFIDelegate` создаёт `AMFIService`, связывает connection, exported interface `proto_AMFIProtocol`, exported object и вызывает `resume`, затем возвращает `1`. В listener нет visible entitlement/audit rejection branch.

В то же время:

- `verifyBoolEntitlement:` получает значение через `connection valueForEntitlement:` и fail-closed возвращает false для отсутствующего/не-NSNumber значения;
- все просмотренные state-changing methods (`setTrustForTeamID`, `removeTrustforTeamID`, `setManagedState`, `setDemoState`, `setSupervisedState`, `stageProfileForUuid`, `commitProfileForUuid`, `initiateDataMigration`, `initiateDeveloperModeDaemons`, `signTeamID`, `removeManagedState`) имеют method-specific entitlement gate;
- `getSEPState` и `getStagedProfile` выглядят read-only, но их exact protocol exposure, bootstrap policy и sensitivity не восстановлены;
- `getStagedProfile` читает fixed `/private/var/db/amfid/UPPStaging.plist`, что делает вопрос о sensitivity реальным, но не доказывает caller reachability.

**Verdict:** INSUFFICIENT EVIDENCE / low-priority review. Listener accept-all — ARCHITECTURAL OBSERVATION. Missing getter gate не доказан как vulnerability.

## H3 — `atc` confused deputy

### Проверка цепочки

Launchd material подтверждает несколько `com.apple.atc*` names, daemon user `mobile`, private AirTraffic entitlements и seatbelt profile. Доступный atc startup code показывает `ATDeviceService`, `MSVXPCTransaction` и `ATSession` setup, но не даёт полного списка incoming exported handlers либо accept-time caller policy.

Для B3 tested move path подтверждена directory-FD-relative/kernel-mediated confinement: destination outside AFC root получает capability failure. Это уменьшает класс произвольной записи за пределы root, но не отвечает на вопрос, кто может вызвать каждый session endpoint или какие операции разрешены внутри root.

**Verdict:** INSUFFICIENT EVIDENCE. No reachable unprivileged client and no specific privileged effect are proven.

## Независимая проверка B2/B3 для кандидатов

- `amfid`: доступные B2/B3 disassembly texts byte-for-byte identical; normalized authorization path has no observed delta.
- `atc`: normalized host disassembly is identical; observed confinement change belongs to AirTraffic framework, not atc host wrapper.
- `installd`: B2/B3 have point changes in install/replacement validation, but no evidence here that an un-gated exported IPC method became reachable or lost its downstream check.

## Итог

Три hypotheses remain open only at evidence level. Ни одна не достигает threshold `PLAUSIBLE / NEEDS VALIDATION` as a concrete security issue, потому что отсутствует доказанная reachability недостаточно привилегированного клиента к конкретному sensitive effect.
