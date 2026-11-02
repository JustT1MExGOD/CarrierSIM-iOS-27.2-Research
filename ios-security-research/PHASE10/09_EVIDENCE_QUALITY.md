# Phase 10 Report 09 — Evidence Quality

Classification scheme: `VERIFIED`, `PARTIALLY VERIFIED`, `NOT VERIFIED`,
`CONTRADICTED`. Applies to every claim Phase 10 makes.

## 1. Claims and their quality

### Binary existence and identity

| Claim | Evidence | Quality |
|---|---|---|
| Security.framework exists on iOS 27.2 B2 | image array entry + Mach-O header + UUID | VERIFIED |
| MobileInstallation.framework exists on B2 | image array entry + Mach-O header + UUID | VERIFIED |
| libmis.dylib exists on B2 | image array entry + Mach-O header + UUID | VERIFIED |
| AppleMobileFileIntegrity.framework exists on B2 | image array entry + Mach-O header + UUID | VERIFIED |
| CodesignKit, libDetachedCertificates, TrustKit, ProfileValidatedAppIdentity, LocalAuthentication, SecurityFoundation, MessageSecurity exist on B2 | image array + Mach-O headers | VERIFIED |
| CoreTrust.framework exists as a separate image on B2 | not in image array | CONTRADICTED |
| libsecurity_codesigning.dylib exists separately on B2 | not in image array; `N8Security11CodeSigning*` symbols inside `Security` | CONTRADICTED |

### Binary completeness

| Claim | Evidence | Quality |
|---|---|---|
| Extracted dylibs are complete standalone Mach-O | last 4 KB all zeros; `__LINKEDIT` backing file empty | CONTRADICTED |
| Extracted dylibs contain valid `__TEXT`/`__DATA`/`__AUTH*` | segment bytes copied from correct subcache files | VERIFIED |
| `LC_SYMTAB` contents are readable | symoff points into zeroed linkedit | CONTRADICTED |
| `LC_DYLD_INFO_ONLY` opcodes are readable | in missing linkedit | CONTRADICTED |
| Per-image `LC_CODE_SIGNATURE` exists | no such load command (dyld-cache layout) | NOT APPLICABLE |

### Trust architecture

| Claim | Evidence | Quality |
|---|---|---|
| AMFI links against libmis and Security | `LC_LOAD_DYLIB` records | VERIFIED |
| libmis links against libCoreEntitlements and sqlite | `LC_LOAD_DYLIB` | VERIFIED |
| Security contains `SecCode`/`SecStaticCode`/`SecRequirement` implementation | C++ mangled names in `__TEXT` | VERIFIED |
| libmis stores trust state in `mis.db` | `mis.db`, `sep_trusted_team_ids`, `user_trusted_profiles`, `banned_profile_uuids` strings + sqlite dep | VERIFIED |
| amfid uses `AMFIPathValidator_ios` | B3 disasm `sub_100004030` | VERIFIED (function-level) |
| `AMFIPathValidator_ios` is implemented in `AppleMobileFileIntegrity` | dependency + name match | PARTIALLY VERIFIED (string inference, not symbol proof) |
| Validator's `isValid`/`profile_valid` are consumed as independent signals by a MIG caller | no caller disasm recovered | NOT VERIFIED |
| `com.apple.MobileFileIntegrity` MIG endpoint is reachable to unprivileged callers | endpoint confirmed; policy missing | NOT VERIFIED |
| Boot-args check enables signature bypass on release builds | string exists; gating unproven | NOT VERIFIED — *not a claim of exploitability* |
| Auxiliary signatures are mandatory | `HasAuxiliarySignature` column + optional accessor names suggest optional | PARTIALLY VERIFIED (as "optional at storage layer") |

### Phase 9 hypothesis verdicts (carried forward)

| Hypothesis | Quality |
|---|---|
| P9-H1 | PARTIALLY VERIFIED |
| P9-H2 | PARTIALLY VERIFIED |
| P9-H3 | NOT VERIFIED |
| P9-H4 | PARTIALLY VERIFIED (string located only) |
| P9-H5 | PARTIALLY VERIFIED |

## 2. Known false-positive sources

- `dyld_image_validation.json` uses `VERIFIED` for "header parsed"; this must
  be read as PARTIAL because the same run also proves the linkedit is absent.
  Report 05 corrects the label.
- Strings in `__TEXT` are *existence* evidence only. A format string for an
  error does not prove that error is ever emitted.
- `LC_LOAD_DYLIB` edges show *link-time* dependency, not *runtime* call
  order.
- ObjC class names in `__AUTH_CONST` survive stripping because the runtime
  needs them; their presence is reliable. Selector→IMP mapping is *not*
  reliable without a working linkedit (selector-references section entries
  are bound pointers whose targets depend on bindings we cannot resolve).

## 3. Evidence that would upgrade statuses

| To upgrade | Needed evidence |
|---|---|
| P9-H1 → VERIFIED | disassembly of a MIG caller that branches on `isValid` AND `profile_valid` independently |
| P9-H2 → VERIFIED | identified call site performing `(file entitlements) ⊆ (profile entitlements)` check |
| P9-H3 → VERIFIED | launchd plist + sandbox profile allowing `lookup` on `com.apple.MobileFileIntegrity` for a non-entitled client |
| P9-H4 → VERIFIED or REFUTED | the function referencing the boot-args string and its guard |
| P9-H5 → VERIFIED | the policy code that reads `HasAuxiliarySignature` and decides whether absence is fatal |
| All framework claims → VERIFIED | a Beta 2 cache copy with intact `.79.dyldlinkedit` and `.symbols` |

## 4. Statement on safety

Phase 10 produced no exploit chain, no AMFI bypass, no sandbox bypass, no
modified binaries, and no device interaction. All recovered data is read-only
static evidence from a local, already-downloaded cache file. The boot-args
string is reported as a static artifact for completeness — it is not a
demonstrated bypass.
