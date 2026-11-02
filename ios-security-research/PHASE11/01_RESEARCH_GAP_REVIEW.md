# Phase 11 Report 01 — Research Gap Review

Method: re-read every Phase 10 report plus Phase 9 `03`, `04`, `08`, `09`.
The unresolved questions below are ordered by impact on the trust model.

## 1. `AMFIPathValidator_ios` implementation site

| Item | Value |
|---|---|
| Known | `amfid` B3 disasm calls `AMFIPathValidator_ios alloc/init`, `initWithURL:withFileOffset:withFlags:`, `validateWithError:`, `computedCdHash`, `signerType`, `isValid`, `areEntitlementsValidated`, `profileData`, `profileAuxSig`. AppleMobileFileIntegrity exists as a B2 dyld image (UUID `A235E3C2-…`). |
| Missing artifact | The `AMFIPathValidator_ios` Objective-C method implementations — specifically the function body that fills `isValid` and `profile_valid`. |
| How it would help | Confirms whether the two result fields are written independently or atomically; whether `profile_valid=0` can accompany `isValid=1`. |
| Local availability | YES — the class selector names and ObjC metadata are in `AppleMobileFileIntegrity_B2.dylib`'s `__AUTH_CONST`/`__DATA_CONST`; method addresses require working selector→IMP binding. |
| Futility test | If `LC_SYMTAB`/`LC_DYLD_INFO_ONLY` were recoverable, IMP pointers could be resolved from `__objc_methname`/`__objc_selrefs`. Without linkedit, selector names exist but cannot be bound to code addresses. FUTILE unless a non-empty linkedit is found. |

## 2. Real MIG caller for `isValid`/`profile_valid` (P9-H1)

| Item | Value |
|---|---|
| Known | `sub_100004030` populates the result fields; `sub_10000b194` is the MIG caller for `verify_code_directory`; MIG demux at `sub_100004a24`. |
| Missing artifact | The MIG reply structure layout and the server-side function that translates validator results into the reply fields. |
| How it would help | Determines whether `isValid=1 && profile_valid=0` is a reachable combination seen by callers. |
| Local availability | PARTIAL — amfid B3 disasm has the callers, but the reply-packing code is inside `amfid` itself (already present). What is missing is the *client* that consumes it. |
| Futility test | If we cannot find a MIG client binary in local images, the hypothesis stays PARTIALLY VERIFIED indefinitely. FUTILE once all local clients are enumerated. |

## 3. Entitlement↔signature binding site (P9-H2)

| Item | Value |
|---|---|
| Known | `libmis → libCoreEntitlements` is a direct dependency; `Security` contains `SecCode`/`SecStaticCode`/`SecRequirement`/`SuperBlobCore` classes; AMFI has two distinct entitlement error strings. |
| Missing artifact | The single function that performs `profile.entitlements ⊇ file.entitlements`. |
| How it would help | Confirms whether AMFI delegates this check to `Security`'s `SecStaticCodeCheckValidity` (with a requirement built from the profile), or implements it directly inside `AppleMobileFileIntegrity`. |
| Local availability | Partially — `__TEXT` contains both class names and error strings; selector→code mapping needs linkedit. |
| Futility test | Without export/bind tables we cannot see which AMFI function calls into `Security`. FUTILE for call-graph resolution; still VERIFIED at dependency level. |

## 4. `com.apple.MobileFileIntegrity` reachability (P9-H3)

| Item | Value |
|---|---|
| Known | amfid calls `bootstrap_check_in("com.apple.MobileFileIntegrity")`; MIG demux is active. |
| Missing artifact | launchd plist, sandbox `.sb` profile, or `com.apple.amfi.nsxpc` entitlement list that gates who may `lookup` the port. |
| How it would help | Determines whether unprivileged clients can reach the MIG endpoint. |
| Local availability | NO — launchd plists and sandbox profiles live outside the dyld cache; the local B3 filesystem extracts do not include `LaunchDaemons/com.apple.MobileFileIntegrity.plist` or a `.sb` for amfid. |
| Futility test | Once all local launchd/sandbox sources are checked and the plist is absent, further analysis is FUTILE without a different filesystem image. |

## 5. Boot-args gating (P9-H4)

| Item | Value |
|---|---|
| Known | String `boot-args allow process with invalid signature: %@` exists in `AppleMobileFileIntegrity` `__TEXT`. |
| Missing artifact | The function that references the string and the condition guarding its use. |
| How it would help | Distinguishes a development-only diagnostic from a runtime policy path. |
| Local availability | The string is present; its xref requires the function-starts table (in missing linkedit) or a pattern scan of `__TEXT` for the ADRP/ADD pair that materialises the string address. |
| Futility test | A manual ARM64 pattern scan can locate the xref; once located, the surrounding function determines the guard. NOT futile — a targeted disasm pass can recover the guard without symbols. |

## 6. Auxiliary signature policy (P9-H5)

| Item | Value |
|---|---|
| Known | `mis.db` column `HasAuxiliarySignature` exists (storage is optional); `AMFIProfileGetScheduledProfile`, `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`, `_createAuxiliarySignature` symbol names exist; `amfid` reads `profileAuxSig` AFTER `isValid`/`areEntitlementsValidated`. |
| Missing artifact | The code that consumes `HasAuxiliarySignature` and decides whether absence fails validation. |
| How it would help | Determines whether aux signatures are hard-required for some profile classes. |
| Local availability | The policy function lives inside `libmis`/`AMFI`; selector names exist. Needs linkedit for function resolution. |
| Futility test | If linkedit is recovered, selector→IMP binding gives the function entry; otherwise the check is hidden behind ObjC dispatch. PARTIALLY FUTILE. |

## 7. Beta 3 / RC trust binaries

| Item | Value |
|---|---|
| Known | `amfid`/`installd` B3 disassemblies exist. Beta 3 system DMG `141-56439-039.dmg` (6.2 GB) exists locally; RC directory has no dyld cache. |
| Missing artifact | B3 and RC versions of the 11 recovered frameworks; B3/RC kernelcache and sandbox profiles. |
| How it would help | UUID comparison, code drift detection, version matrix completion. |
| Local availability | The B3 DMG contains the same dyld cache layout — extracting it is a file-read operation, but mounting/extracting requires `ipsw` or `dmg` tooling. |
| Futility test | If the B3 DMG's `dyld_shared_cache` is present and non-empty, the version matrix can be filled. FUTILE only if the DMG's cache is also stripped. |

## 8. `__LINKEDIT` subcache contents

| Item | Value |
|---|---|
| Known | `.79.dyldlinkedit` is 0 bytes in the local copy; `.78.dyldreadonly` ends at `0x2de488000`; declared `__LINKEDIT` vm range `0x2de48c000`–`0x31f740000` (~663 MB) has no backing file; `.symbols` is also 0 bytes. |
| Missing artifact | A non-empty `.79.dyldlinkedit` (and `.symbols`) matching the Beta 2 build. |
| How it would help | Restores symbol tables, export/bind tries, code-signature blob, function-starts index — everything needed for full Mach-O reconstruction. |
| Local availability | NO — both local copies (`beta2-dyld`, `PHASE10/cache_work`) have 0-byte files with identical SHA-256 (`e3b0c44…b855`, the empty-file hash). |
| Futility test | Once the IPSW/DMG extraction pipeline is re-run and the file still arrives empty, the upstream source itself shipped a truncated cache. FUTILE for this copy; would need a re-download. |

## 9. Mach-O completeness of extracted dylibs

| Item | Value |
|---|---|
| Known | 11 extracted dylibs have valid `MH_MAGIC_64`, correct `MH_DYLIB` type, correct UUIDs, all declared segments physically present except `__LINKEDIT`. `LC_SYMTAB`/`LC_DYLD_INFO_ONLY`/`LC_FUNCTION_STARTS`/`LC_CODE_SIGNATURE` are declared but point into the absent region. |
| Missing artifact | See #8. |
| Status | STRUCTURALLY VALID but PARTIALLY USABLE for analysis. |

## Summary

| # | Question | Locally resolvable? | Blocked by |
|---|---|---|---|
| 1 | Validator internals | YES (selector names) | linkedit for IMP |
| 2 | Real MIG caller for H1 | PARTIAL | client binary absent |
| 3 | Entitlement↔signature site | NO (call graph) | linkedit |
| 4 | MIG reachability | NO | launchd/sandbox data absent |
| 5 | Boot-args gating | YES | xref scan is possible |
| 6 | Aux-sig policy | PARTIAL | linkedit |
| 7 | B3/RC versions | YES | need to extract B3 DMG cache |
| 8 | `__LINKEDIT` contents | NO | source copy is empty |
| 9 | Mach-O completeness | depends on #8 | linkedit |
