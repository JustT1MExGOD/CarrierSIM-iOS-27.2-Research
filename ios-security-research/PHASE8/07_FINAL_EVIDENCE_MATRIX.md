# PHASE8 — 07_FINAL_EVIDENCE_MATRIX

Статусы: `CONFIRMED`, `CONTRADICTED`, `NOT VERIFIED`. `CONTRADICTED` используется только там, где конкретное утверждение опровергается локальным evidence.

## `getSEPStateWithReply:`

| ID | Условие | Статус | Доказательство и источник | Версия | Ограничение | Уверенность |
|---|---|---|---|---|---|---|
| A | Метод экспортируется | CONFIRMED | `AMFIProtocol` method list #2; listener sets exported interface/object | B2/B3 | Protocol metadata recovered from binaries, no source header | HIGH |
| B | Unprivileged client can perform Mach lookup | NOT VERIFIED | no amfid launchd plist, effective sandbox profile or bootstrap policy | B2/B3 | Server-side listener creation cannot establish client lookup | HIGH that evidence is missing |
| C | Client can connect and invoke method | NOT VERIFIED | accept method returns 1 once connection arrives; no client-side reachability proof | B2/B3 | lookup and handshake remain unresolved | HIGH |
| D | Additional authorization absent/insufficient | NOT VERIFIED | no visible gate in listener/getter; possible launchd/sandbox/LAStorage policy not recovered | B2/B3 | absence in one function is not absence in system | HIGH |
| E | Response is protected from this client | NOT VERIFIED | 49-byte LAStorage state structure; key 0xf semantics unknown; no secret identified | B2/B3 | sensitivity and client category unresolved | MEDIUM/HIGH |

## `getStagedProfileWithReply:`

| ID | Условие | Статус | Доказательство и источник | Версия | Ограничение | Уверенность |
|---|---|---|---|---|---|---|
| A | Метод экспортируется | CONFIRMED | `AMFIProtocol` method list #5; exported NSXPC interface | B2/B3 | no source header, but ObjC metadata direct | HIGH |
| B | Unprivileged client can perform Mach lookup | NOT VERIFIED | same missing launchd/sandbox/bootstrap evidence | B2/B3 | service name/use is not client access proof | HIGH |
| C | Client can connect and invoke method | NOT VERIFIED | server accepts already-arrived connection; no client path | B2/B3 | no active IPC allowed and no static client policy | HIGH |
| D | Additional authorization absent/insufficient | NOT VERIFIED | no local method gate; transport policy and file/framework controls unresolved | B2/B3 | `stageProfile` write gate does not prove read reachability | HIGH |
| E | Response is protected from this client | NOT VERIFIED | full UTF-8 contents of fixed staging file are returned; normal writer suggests UUID, but exact content sensitivity unresolved | B2/B3 | no real file content extracted | MEDIUM/HIGH |

## Negative/contradictory controls

| Claim | Status | Reason |
|---|---|---|
| “Methods are not exported” | CONTRADICTED | direct `AMFIProtocol` metadata contains both selectors |
| “B2 and B3 differ in getter authorization” | CONTRADICTED | disassembly texts identical; normalized paths identical |
| “Accept-all proves ordinary App Store reachability” | CONTRADICTED as an inference | accept callback runs only after a connection reaches listener |
| “No visible method gate proves system-wide absence of authorization” | CONTRADICTED as an inference | launchd/sandbox/framework layers may still constrain access |
| “Returned values are confirmed secrets” | CONTRADICTED by available evidence | no key/credential/PII semantics established |
| “Endpoint is definitely inaccessible” | NOT VERIFIED, not CONTRADICTED | policy material is missing |

## Matrix conclusion

Neither method satisfies all five conditions. A and server-side portions are confirmed; B, C, D and E remain unresolved at the level required for a security finding.
