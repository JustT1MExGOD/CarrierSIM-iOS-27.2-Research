# Phase 11 Report 10 — Hypothesis Reassessment

Each Phase 9 hypothesis is re-evaluated against Phase 11 evidence.

## P9-H1 — `isValid=1` with `profile_valid=0` may bypass profile enforcement

| Field | Content |
|---|---|
| Previous status | PARTIALLY VERIFIED (Phase 10) |
| New evidence | AMFI framework `__TEXT` contains TWO distinct failure vocabularies (signature axis vs profile-matching axis); `sub_100004030` writes `isValid` and `profile_valid` via separate selector calls; `AMFIPathValidator_ios` is confirmed as an ObjC class embedded in `amfid` itself (not in `AppleMobileFileIntegrity.framework`); AppleMobileFileIntegrity is confirmed to hold the profile-management API (`AMFIConnection`, `AMFIProfile*`). |
| New contradiction | None — every recovered framework's contents are consistent with independent result fields. |
| Final status | **PARTIALLY VERIFIED** — unchanged |
| Reason | The two fields are provably independent at the producer side; the profile-matching failure categories are confirmed. What remains unproven: (a) whether `validateWithError:` actually returns success when only profile matching fails, (b) the MIG caller `sub_10000b194`'s reply packing, (c) a real consumer that acts on the combination. Items (a) and (b) are reachable through further `amfid` disasm (no linkedit needed); item (c) requires a client binary not present locally. |

## P9-H2 — entitlement↔signature binding is enforced at a single point

| Field | Content |
|---|---|
| Previous status | PARTIALLY VERIFIED (Phase 10) |
| New evidence | `libmis → libCoreEntitlements` confirmed by `LC_LOAD_DYLIB`; `Security` confirmed to contain `SecCode`, `SecStaticCode`, `SecRequirement`, `SuperBlobCore`, `EmbeddedSignatureBlob`, `DYLDCacheRep`, `MachOEditor`, `SecCodeSigner`, `ValidationContext`, `CollectingContext`; `AppleMobileFileIntegrity` contains two distinct entitlement error strings ("malformed" vs "does not match the entitlements") — consistent with layered checks. |
| New contradiction | None. |
| Final status | **PARTIALLY VERIFIED** — unchanged |
| Reason | The binding is distributed across `Security` (requirement evaluation), `libmis`/`libCoreEntitlements` (DER parsing), and `AppleMobileFileIntegrity` (profile matching). The single chokepoint remains unproven because the call site performing `profile.entitlements ⊇ file.entitlements` has not been located. |

## P9-H3 — `com.apple.MobileFileIntegrity` MIG endpoint reachable by unprivileged callers

| Field | Content |
|---|---|
| Previous status | NOT VERIFIED (Phase 10) |
| New evidence | None — the dyld cache does not contain launchd plists or `.sb` sandbox profiles. `bootstrap_check_in` + `dispatch_mach_mig_demux` confirmed in `amfid` B3 disasm (unchanged). |
| New contradiction | None. |
| Final status | **NOT VERIFIED** — unchanged |
| Reason | No new data source covering launchd policy or sandbox profiles was introduced in Phase 11. Would require mounting a filesystem image that includes `LaunchDaemons/` and `.sb` files. |

## P9-H4 — `boot-args allow process with invalid signature` enables a signature bypass

| Field | Content |
|---|---|
| Previous status | PARTIALLY VERIFIED (Phase 10) |
| New evidence | String `boot-args allow process with invalid signature: %@` confirmed present in `AppleMobileFileIntegrity_B2.dylib` `__TEXT` at file offset `0xf2a6` region (verified via corrected section mapping). Near-by strings: `found local signing key as a system key`, `unable to find local signing key on the system`, `unable to add public key to AMFI`, `found untrusted object in the keychain`, `the local signing private key is not available`, `successfully copied local signing private key` — consistent with a *local-signing developer-mode* code path, not the hot validation loop. |
| New contradiction | None — context suggests development-mode handling, not a bypass. |
| Final status | **PARTIALLY VERIFIED** — unchanged |
| Reason | The string is located in a region of `__TEXT` that also contains local-signing key management, consistent with developer/local-signing flows. The guard (boot-args read + condition) has not been located — a capstone disasm pass at the string's xref would resolve it. No claim of exploitability. |

## P9-H5 — auxiliary signatures are optional and can be absent

| Field | Content |
|---|---|
| Previous status | PARTIALLY VERIFIED (Phase 10) |
| New evidence | `HasAuxiliarySignature` column confirmed in `mis.db` schema (optional storage); `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`, `_createAuxiliarySignature` confirmed in AMFI `__TEXT`; `amfid` reads `profileAuxSig` only AFTER `isValid`/`areEntitlementsValidated` — consistent with optional post-validation enrichment; `libDetachedCertificates` contains `Compatibility version mismatch` — a detached-chain consistency check. |
| New contradiction | None. |
| Final status | **PARTIALLY VERIFIED** — unchanged |
| Reason | Storage is provably optional (`HasAuxiliarySignature` flag); the three accessor names suggest on-demand generation; the `amfid` call order confirms it's post-validation. What is NOT proven: whether policy *requires* aux sig for specific profile classes (e.g. development vs App Store). |

## Summary table

| Hypothesis | Phase 9 | Phase 10 | Phase 11 | Delta |
|---|---|---|---|---|
| P9-H1 | UNVERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | validator independence confirmed at framework level |
| P9-H2 | UNVERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | layered components confirmed; chokepoint unproven |
| P9-H3 | UNVERIFIED | NOT VERIFIED | NOT VERIFIED | no new data |
| P9-H4 | UNVERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | string + context confirmed; gating unproven |
| P9-H5 | UNVERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | storage optionality confirmed; policy requirement unproven |

No hypothesis was upgraded to VERIFIED. None were refuted. Phase 11
confirmed the architectural components; function-level answers remain
blocked on `__LINKEDIT` or additional `amfid` disasm.
