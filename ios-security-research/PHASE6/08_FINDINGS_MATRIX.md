# PHASE6 — 08_FINDINGS_MATRIX

## Findings

| ID | Наблюдение | Service | Evidence | Classification | Why not stronger |
|---|---|---|---|---|---|
| P6-001 | NSXPC listener принимает connection без visible accept-time entitlement/audit branch | installd | `listener:shouldAcceptNewConnection:`; exported protocol; per-method validators | ARCHITECTURAL OBSERVATION | bootstrap reachability and downstream coverage are incomplete |
| P6-002 | 12 exported methods lack direct helper call in examined wrappers | installd | Phase 2 method inventory | INSUFFICIENT EVIDENCE | no proof that all 12 are sensitive or transitively ungated |
| P6-003 | `checkCapabilities` has no visible direct gate | installd | manager/type-check path | ARCHITECTURAL OBSERVATION | read-only effect; endpoint and sensitivity not fully established |
| P6-004 | destructive test hooks use entitlement/test-state controls | installd | `_ValidateMIAllowedSPIEntitlement`, test flags | ARCHITECTURAL OBSERVATION | complete setter/bootstrap state not reconstructed |
| P6-005 | AMFI listener accepts and exports service without visible accept-time gate | amfid | `AMFIDelegate` setup; `com.apple.amfi.nsxpc` | ARCHITECTURAL OBSERVATION | launchd/sandbox restrictions not available |
| P6-006 | examined AMFI mutating methods use specific `verifyBoolEntitlement:` gates | amfid | 11 method callsites; gate strings | ARCHITECTURAL OBSERVATION | delegated trust/signature semantics and full protocol declaration not reconstructed |
| P6-007 | `getSEPState` and `getStagedProfile` lack visible method gate | amfid | getter call paths | INSUFFICIENT EVIDENCE | caller reachability, exposure and sensitivity unresolved |
| P6-008 | atc exposes multiple endpoint names and host/session setup | atc | launchd plist, entitlements, startup disassembly | INSUFFICIENT EVIDENCE | no complete incoming handler/caller authorization map |
| P6-009 | B3 AirTraffic move is kernel/dirfd confined | atc/AirTraffic | B2/B3 framework evidence and errno 107 | ARCHITECTURAL OBSERVATION | filesystem confinement is not IPC caller authorization |
| P6-010 | no observed amfid or atc host B2→B3 IPC authorization delta | amfid/atc | normalized diff | RULED OUT for observed delta claim | only available binaries/material, not all dependencies/policies |

## Final security assessment

- `CONFIRMED SECURITY ISSUE`: none.
- `PLAUSIBLE / NEEDS VALIDATION`: none as a concrete vulnerability; open evidence gaps remain.
- `ARCHITECTURAL OBSERVATION`: accept-all listener setup followed by method-level checks; AirTraffic filesystem confinement; visible AMFI mutator gates.
- `INSUFFICIENT EVIDENCE`: installd no-direct-gate set, AMFI getter exposure, atc caller authorization.
- `RULED OUT`: a claim of an observed B2→B3 amfid/atc-host IPC authorization delta, within the analyzed material.

`RULED OUT` above applies only to the narrow version-delta hypothesis. It does not rule out missing policy in unavailable bootstrap, sandbox, dependency or framework material.
