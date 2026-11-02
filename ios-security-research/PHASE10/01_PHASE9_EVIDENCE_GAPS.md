# Phase 10 Report 01 — Phase 9 Evidence Gaps

Scope: iOS 27.2 Beta 2 / Beta 3 / RC offline static analysis.
Source set: Phase 9 reports, Beta 2 split dyld shared cache, Beta 3 disassemblies (`amfid`, `installd`).

## 1. What Phase 9 could not verify

Phase 9 correctly identified the trust architecture conceptually but could not
inspect several core components because the binaries were not present as
standalone Mach-O files in the extracted filesystem views. The gaps were:

| Phase 9 gap | What was missing | Why it mattered |
|---|---|---|
| Security.framework code-signing internals | No binary | Could not confirm `SecCode`/`SecStaticCode`/SuperBlob use in amfid's path |
| libmis.dylib | No binary | Could not confirm MIS profile DB, team-ID trust, auxiliary signatures |
| AppleMobileFileIntegrity.framework | No binary | Could not confirm profile-matching errors or validator backing |
| MobileInstallation.framework | No binary | Could not confirm `MICodeSigningVerifier` internals |
| CoreTrust (standalone) | No binary | Could not determine if a separate `CoreTrust.framework` exists |
| trustd binary | No binary | Could not confirm certificate evaluation path |
| libsecurity_codesigning | No binary | Could not confirm if a distinct library still exists on iOS 27.2 |
| amfid → validator call graph | Incomplete | Could not prove a real MIG client consumes `isValid` + `profile_valid` |
| Beta 3 / RC trust frameworks | Not extracted | Could not diff across versions |

## 2. What Phase 10 has now resolved

By parsing the Beta 2 split dyld shared cache image array directly
(`dyld_shared_cache_arm64e` + `.1`-`.79` subcaches), Phase 10 has resolved the
*existence* question for most components:

- `Security.framework` — **present** in the cache (UUID `A413232A-E824-39DF-AAFA-2E7E6153AE24`).
- `MobileInstallation.framework` — **present** (UUID `60B509C3-9DED-3504-8840-9874714C0109`).
- `libmis.dylib` — **present** (UUID `CE1D3D2A-3EC2-3A6D-AFA8-2FEDA08BCB68`).
- `AppleMobileFileIntegrity.framework` — **present** (UUID `A235E3C2-68CE-338A-8ED8-FFE4462860C5`).
- `CodesignKit.framework` — **present** (UUID `0EC827C0-6BFE-392A-871F-CCAAE3917D0A`).
- `libDetachedCertificates.dylib` — **present** (UUID `D0B631B9-359C-360F-8359-880558F926C1`).
- `TrustKit.framework` — **present** (UUID `0791DC22-F4E8-3F90-8680-A7870D03EB67`).
- `ProfileValidatedAppIdentity.framework` — **present** (UUID `8631DD74-4F53-3328-BBE6-4AD26083027C`).
- `LocalAuthentication.framework` — **present** (UUID `2EB95A78-2506-3B6F-858B-DA37CD913010`).
- `SecurityFoundation.framework` — **present** (UUID `3245DBC2-ECE6-3BEA-B885-21917B0179DF`).
- `MessageSecurity.framework` — **present** (UUID `67504E44-A574-3334-BC94-8421CC1AB505`).

## 3. What remains unresolved

- **`__LINKEDIT` subcache (`dyld_shared_cache_arm64e.79.dyldlinkedit`) is empty** in the local
  Beta 2 cache. All images declare a shared `__LINKEDIT` mapped at
  `va=0x2de48c000`, `size=0x294d8000`, but the backing file contains zero bytes.
  Extracted dylibs therefore have a zero-filled linkedit region — headers and
  regular segments are valid, but symbol tables, export/bind tries, function
  starts and embedded code signatures are **not physically recoverable** from
  this cache copy.
- **`.symbols` subcache** is also empty, so `ipsw dyld info` / `dyld image`
  tooling fails with `EOF`.
- **CoreTrust** — no standalone `CoreTrust.framework` image is present in the
  Beta 2 image array. CoreTrust functionality is most likely compiled into
  `Security.framework` or `AppleMobileFileIntegrity.framework` (both contain
  CoreTrust-related strings and `CodeSigning::*` C++ class symbols).
- **trustd, amfid, installd binaries** are not inside the dyld shared cache
  (main executables never are). Beta 3 disassemblies of `amfid`/`installd`
  remain the only function-level evidence.
- **Beta 3 and RC** trust-framework binaries are still not extracted — no
  comparable split cache for those versions has been processed yet.
- **Mach lookup / launchd policy** for `com.apple.MobileFileIntegrity` — still
  only evidenced by amfid's `bootstrap_check_in` call site; sandbox profiles
  and `com.apple.amfi.nsxpc` entitlement gating are unverified.

## 4. Gap → evidence mapping for Phase 9 hypotheses

| Hypothesis | Phase 9 blocker | Phase 10 evidence now available |
|---|---|---|
| P9-H1 `isValid=1` + `profile_valid=0` | No validator internals, no real MIG client | AppleMobileFileIntegrity strings list every profile-mismatch failure category; validator API surface (`AMFIPathValidator`, `profileAuxSig`, `areEntitlementsValidated`) confirmed present |
| P9-H2 entitlement↔signature binding | Could not locate binding site | `libmis → libCoreEntitlements` dependency confirmed; `Security` contains `SecCode`/`SecStaticCode`/`SecRequirement`; AMFI contains `entitlements ... malformed` / `does not match the entitlements` errors |
| P9-H3 Mach/MIG reachability | No sandbox/launchd data | Still missing — no launchd plists or sandbox profiles recovered |
| P9-H4 boot-args policy | String not located | Located: `boot-args allow process with invalid signature: %@` inside AppleMobileFileIntegrity `__TEXT` |
| P9-H5 auxiliary signatures | Unclear if optional | `HasAuxiliarySignature`, `profileAuxSig`, `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`, `_createAuxiliarySignature` confirmed in libmis + AMFI |

## 5. Conclusion

Phase 10 closes the *component existence* gap but opens a *recovery
completeness* gap. The Beta 2 cache copy is structurally incomplete (empty
linkedit + empty symbols subcaches). All downstream statuses in reports
03–09 therefore use `PARTIALLY VERIFIED` rather than `VERIFIED` for cache-derived
evidence.
