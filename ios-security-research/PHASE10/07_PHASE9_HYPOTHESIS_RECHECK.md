# Phase 10 Report 07 — Phase 9 Hypothesis Recheck

Method: re-evaluate each Phase 9 hypothesis using the newly discovered Beta 2
frameworks and their declared dependencies. Statuses remain conservative —
framework existence does not prove call reachability.

---

## P9-H1 — `isValid=1` with `profile_valid=0` may bypass profile enforcement

Phase 9 blocker: `AMFIPathValidator_ios` internals were missing; no real MIG
client had been identified.

New Phase 10 evidence:
- `AppleMobileFileIntegrity` exists and contains the validator-side error
  vocabulary: "The best matching profile does not match the entitlements",
  "does not provision the certificates", "not valid for this device",
  "has expired", "not validly signed", "The signature on the file is
  invalid", "No matching profile found".
- `AMFIProfileScheduleTrust`, `AMFIProfileGetScheduledProfile`,
  `AMFIProfileCommitProfile`, `AMFIProfileSetTeamIDTrustWithOptions`,
  `AMFIProfileRemoveTeamIDTrust` are present as symbol names.
- B3 `amfid` disasm still shows `isValid`, `profileAuxSig`,
  `areEntitlementsValidated`, `computedCdHash`, `signerType` as separate
  result fields produced by `AMFIPathValidator_ios`.

What is still missing:
- A *concrete MIG caller* that consumes `isValid` and `profile_valid` as
  separate signals and makes a trust decision. `sub_100004030` populates them;
  nothing yet shows a caller branching on the combination.
- `__LINKEDIT` means we cannot trace which ObjC method names map to which
  function pointers inside `AMFIPathValidator_ios`.

**Status: PARTIALLY VERIFIED — validator surface is confirmed; the
discriminating caller is still unproven.**

---

## P9-H2 — entitlement↔signature binding is enforced at a single point

Phase 9 blocker: could not tell which component performs binding.

New Phase 10 evidence:
- `libmis → libCoreEntitlements` is a direct `LC_LOAD_DYLIB` — DER
  entitlement parsing lives in `libCoreEntitlements` and is consumed by MIS.
- `Security.framework` contains `CodeSigning::SecRequirement`,
  `SecStaticCode`, `SecCode`, `SuperBlobCore`, `MachOImage` — the entire
  requirement-language and blob-parsing machinery.
- `AppleMobileFileIntegrity` contains the two distinct error strings
  "The entitlements in this file are malformed" and "The best matching
  profile does not match the entitlements of this file" — i.e. there is a
  *syntax* check and a *policy* check at different layers.
- `libmis` strings include `CodeSignatureError`, `AuxiliarySignature`,
  `ProfileID`, `HasAuxiliarySignature` — the profile DB tracks signature
  objects alongside profile IDs.

What is still missing:
- The single call site where `SecStaticCode` requirements, the profile's
  entitlement set, and the file's actual entitlements are compared.
- Whether `AMFIPathValidator` invokes `SecStaticCodeCheckValidity` with a
  requirement built from the profile, or compares entitlement blobs itself.

**Status: PARTIALLY VERIFIED — binding is distributed across Security +
AMFI + libmis; the specific chokepoint is unresolved.**

---

## P9-H3 — `com.apple.MobileFileIntegrity` MIG endpoint reachable by
unprivileged callers

Phase 9 blocker: no launchd plist, sandbox profile, or XPC entitlement list.

New Phase 10 evidence:
- Nothing new. Dyld cache does not contain launchd plists or `.sb` profiles.
- B3 `amfid` disasm still shows `bootstrap_check_in("com.apple.MobileFileIntegrity")`
  at `sub_1000049c8` and the demux at `sub_100004a24` — confirms the endpoint
  exists, not who may reach it.
- `com.apple.amfi.nsxpc` remains a named service in the XPC surface but no
  entitlement enforcement data was recovered.

**Status: NOT VERIFIED — endpoint existence is confirmed; reachability
policy is still unknown.**

---

## P9-H4 — `boot-args allow process with invalid signature` enables a
signature bypass

Phase 9 blocker: the string was reported but not located.

New Phase 10 evidence:
- The literal `"boot-args allow process with invalid signature: %@"` is
  present in `AppleMobileFileIntegrity_B2.dylib` `__TEXT`.
- Its presence in `AppleMobileFileIntegrity` (the profile-matching engine)
  rather than in `amfid` itself suggests the diagnostic or policy branch is
  implemented at the framework layer.
- Nearby strings include other profile-scheduling and team-ID management
  operations — the boot-args check is likely inside a privileged profile
  trust path, not the hot validation loop.

What is still missing:
- Reachability. Without `__LINKEDIT`/symbols we cannot tell which function
  references this format string or what gate guards it.
- The boot-args parsing code — `boot-args` is a kernel-side argument;
  userspace can only *read* it via `kern.bootargs` sysctl or similar. The
  condition under which AppleMobileFileIntegrity honours it is unknown.
- Any evidence the flag is honoured on RELEASE builds vs internal/development.

**Status: PARTIALLY VERIFIED — the string exists; its guard, call site, and
build gating are unproven. This is NOT evidence of an exploitable bypass.**

---

## P9-H5 — auxiliary signatures are optional and can be absent

Phase 9 blocker: could not tell whether `profileAuxSig` is required or
optional.

New Phase 10 evidence:
- `libmis` exports strings: `AuxiliarySignature`, `HasAuxiliarySignature`,
  `ProfileID` — the profile DB stores an *optional* aux-signature field
  (the "Has" prefix is the tell).
- `AppleMobileFileIntegrity` exports:
  `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`,
  `_createAuxiliarySignature` — three distinct code paths suggest auxiliary
  signatures are *generated on demand* and *looked up*, not always present.
- `amfid` B3 disasm reads `profileAuxSig` via `vm_read` only *after*
  `isValid` and `areEntitlementsValidated` — consistent with optional
  post-validation enrichment, not mandatory gating.

What is still missing:
- The check that decides whether a profile requires aux sig. The presence of
  a "Has" column in `mis.db` strongly suggests optionality at the data
  layer, but the *policy* could still require it for some profile classes.
- `libDetachedCertificates` shows detached-chain validation, but whether
  that path is mandatory for aux signatures is unresolved.

**Status: PARTIALLY VERIFIED — aux signatures are treated as optional at
the storage layer; policy-level requirement is unproven.**

---

## Summary table

| Hypothesis | Phase 9 status | Phase 10 status | Direction |
|---|---|---|---|
| P9-H1 | UNVERIFIED | PARTIALLY VERIFIED | validator surface confirmed; caller unproven |
| P9-H2 | UNVERIFIED | PARTIALLY VERIFIED | components + roles confirmed; chokepoint unproven |
| P9-H3 | UNVERIFIED | NOT VERIFIED | unchanged — no policy data |
| P9-H4 | UNVERIFIED | PARTIALLY VERIFIED | string located; reachability/gating unproven |
| P9-H5 | UNVERIFIED | PARTIALLY VERIFIED | optional storage confirmed; policy requirement unproven |

None of the hypotheses advanced to VERIFIED. None are CONTRADICTED — every
recovered framework's contents are consistent with Phase 9's architectural
model.
