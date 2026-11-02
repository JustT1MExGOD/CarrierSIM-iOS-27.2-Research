# Phase 11 Summary — dyld Shared Cache Integrity, LINKEDIT Recovery & Trust Call-Graph Reconstruction

## Executive result

Phase 11 found and fixed a real Phase 10 extraction defect, then proved the
remaining missing-data boundary.

Two independent facts were initially conflated:

1. The local Beta 2 dyld cache has an empty `.79.dyldlinkedit` and empty
   `.symbols` file. This is a source-data defect, not a normal extractor
   limitation.
2. The Phase 10 extractor also had a layout bug: it wrote cache image segment
   data at cache-global `fileoff` values, producing overlapping, unusable
   files. Phase 11 corrected the layout and re-extracted 11 components.

The corrected files are genuine compact Mach-O reconstructions containing all
available `__TEXT` and regular data segments. They are structurally valid and
partially usable. Full linkedit/symbol/import/export recovery remains
impossible because the only version-matched linkedit subcache is empty.

## 1. Cache inventory

| Metric | Result |
|---|---|
| Main dyld cache sets checked | 2 local copies — primary `beta2-dyld`; derivative `PHASE10/cache_work` |
| Independent build/version sets | 1 (Beta 2; `cache_work` is not independent) |
| Main cache files checked | 2 |
| Subcache entries expected | 79 (`subCacheArray`, stride `0x38`, table at `0x5a4e8`) |
| Expected subcache files present/non-empty | 78 |
| Expected subcache file empty | 1 — `.79.dyldlinkedit` |
| Auxiliary files | `.symbols` empty; `.atlas` valid AA01 file (3,110,502 bytes) |
| Total directory entries beginning `dyld_shared_cache_arm64e` | 82 |
| Build | iOS 27.2 Beta 2, `24B5089g`, arm64e / iPhone16,1 |
| Main cache UUID | `4A8F3C2F-15CF-3AE3-B702-9B66E918CDEB` |

All 78 non-empty subcaches have valid `dyld_v1 arm64e` magic and self UUIDs
matching the 79-entry main-cache `subCacheArray` (the 79th is empty and
cannot self-report its UUID).

## 2. Subcache completeness

**Overall classification: INCOMPLETE.**

- Structurally expected set: complete — `.01` … `.79` are listed in the
  header.
- Physical content: incomplete — `.79.dyldlinkedit` is zero bytes.
- `.78.dyldreadonly` ends at `0x2de488000`.
- `.79` is expected to begin at `0x2de48c000`, exactly the declared
  `__LINKEDIT` base in every target image.
- Declared linkedit range: `0x2de48c000–0x31f740000`, approximately 663 MB.
- No overlap or alternate backing mapping was found in `.77`, `.78`, `.atlas`,
  or `.symbols`.

The primary cache main file has SHA-256:
`11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8`.

Both empty files have SHA-256:
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## 3. Why LINKEDIT is missing

The header and subcache table prove `.79.dyldlinkedit` is an expected
version-matched subcache:

- expected UUID `79D3F635-C960-3C22-A00A-264E5975D82D`;
- expected VM/file role at the terminal of the subcache set;
- every target's `__LINKEDIT` points into its range.

The file is empty in the source directory, and the derivative `cache_work`
does not provide a second copy. The most likely explanations are an upstream
truncated extraction or an extraction-tool/packaging defect. It is **not**
valid to infer that Apple deliberately shipped a functioning cache with a
zero-byte linkedit: dyld needs linkedit data to resolve image metadata and
bindings.

No arbitrary bytes were written into the empty file. No synthetic symbols,
exports, binds, or code signatures were created.

## 4. Tool audit

| Tool | Version | Can parse intact cache? | Can recover missing LINKEDIT? | Result |
|---|---|---|---|---|
| `ipsw.exe` | 3.1.740, commit `6361083e…` | YES in principle | NO | `info`/`image` fail with `EOF` on this set |
| `extract_dyld_segments.py` | Phase 10 local script | segment reads YES | NO | had cache-global/local fileoff bug; superseded |
| `extract_flat.py` | Phase 11 local script | YES for available segments | NO | corrected compact extractor; used for final files |
| `capstone` | 5.0.7 | raw arm64e disasm YES | NO | verified real code in corrected AMFI file |
| `macholib` | not installed | — | NO | not installed; unnecessary |
| `LIEF` | not installed | — | NO | not installed; cannot invent absent data |

No external program or source code was downloaded or installed.

## 5. Corrected extraction results

The corrected extractor wrote 11 files under:
`C:\ipsw-tools\IOS_SECURITY_RESEARCH\PHASE11\extracted_v2\`

| Component | Corrected file | Source cache | UUID | LINKEDIT | Call graph | Final |
|---|---|---|---|---|---|---|
| AppleMobileFileIntegrity | B2 split cache | `A235E3C2-68CE-338A-8ED8-FFE4462860C5` | missing | DEP edges + ObjC surface | STRUCTURALLY VALID / PARTIALLY USABLE |
| libmis | B2 split cache | `CE1D3D2A-3EC2-3A6D-AFA8-2FEDA08BCB68` | missing | DEP edges + trust DB strings | STRUCTURALLY VALID / PARTIALLY USABLE |
| Security | B2 split cache | `A413232A-E824-39DF-AAFA-2E7E6153AE24` | missing | CodeSigning class surface; no imports | STRUCTURALLY VALID / PARTIALLY USABLE |
| MobileInstallation | B2 split cache | `60B509C3-9DED-3504-8840-9874714C0109` | missing | ObjC install/verifier surface | STRUCTURALLY VALID / PARTIALLY USABLE |
| CodesignKit | B2 split cache | `0EC827C0-6BFE-392A-871F-CCAAE3917D0A` | missing | Swift metadata surface | STRUCTURALLY VALID / PARTIALLY USABLE |

Correction to the first Phase 10 extraction: the old files under
`PHASE10\extracted\dyld_B2\` are superseded and must not be used. Their
segments overlapped because cache-global `fileoff` values were treated as
local output offsets.

## 6. New confirmed call-graph links

### Function-level (`CALL`, B3 disasm)

- `amfid` `sub_100004030` → `AMFIPathValidator_ios`
  `initWithURL:withFileOffset:withFlags:`.
- `amfid` `sub_100004030` → `validateWithError:`, `computedCdHash:withLength:`,
  `signerType`, `isValid`, `areEntitlementsValidated`, `profileData`,
  `profileAuxSig`.
- `amfid` `sub_1000049c8` → `bootstrap_check_in("com.apple.MobileFileIntegrity")`.
- `amfid` `sub_100004a24` → `dispatch_mach_mig_demux`.
- `amfid` `sub_10000b194` → MIG `verify_code_directory` handling.
- `amfid` `sub_10000b3d8` → DER entitlement construction/handling.
- `amfid` `sub_10000366c` → XML/property-list entitlement parse and
  `CESerializeCFDictionary` path.
- `installd` `MIInstallableBundle` → `MICodeSigningVerifier
  validateWatchKitV2StubExecutableBundle:error:`.
- `installd` eligibility path → `MICodeSigningInfo
  signingIdentifierForAuditToken:error:` and test-mode checks.

### Dependency-level (`DEP`, not concrete calls)

- `AppleMobileFileIntegrity` → `libmis` + `Security` + `IOKit`.
- `libmis` → `libCoreEntitlements` + `Security` + `sqlite3` + `IOKit`.
- `MobileInstallation` → `Security` + `Bom` + `MobileSystemServices`.
- `MessageSecurity` → `Security` + `heimdal-asn1`.
- `Security` → `AppleKeyStore` + `coretls`.

The distinction is explicit: `LC_LOAD_DYLIB` does not prove a call to a
specific function.

## 7. P9-H1 result propagation

`sub_100004030` produces several result fields independently after
`validateWithError:`:

- `computedCdHash`
- `signerType`
- `isValid`
- `areEntitlementsValidated`
- `profileData`
- `profileAuxSig`

AppleMobileFileIntegrity contains distinct signature-failure and
profile-matching failure categories, making an independent-axis model
plausible. But Phase 11 still cannot establish all required conditions:

1. whether the validator returns success while profile matching fails;
2. exact MIG reply packing in `sub_10000b194`;
3. a real client that consumes `isValid=1, profile_valid=0`;
4. a security consequence;
5. absence of independent checks (`installd` has its own verifier path).

**P9-H1 remains PARTIALLY VERIFIED, not a demonstrated vulnerability.**

## 8. Other hypotheses

| Hypothesis | Phase 10 | Phase 11 | Change |
|---|---|---|---|
| P9-H1 partial response | PARTIALLY VERIFIED | PARTIALLY VERIFIED | no status change |
| P9-H2 entitlement binding | PARTIALLY VERIFIED | PARTIALLY VERIFIED | layered components confirmed; chokepoint absent |
| P9-H3 MIG reachability | NOT VERIFIED | NOT VERIFIED | no launchd/sandbox policy artifact |
| P9-H4 enforcement flag | PARTIALLY VERIFIED | PARTIALLY VERIFIED | string/context confirmed; guard absent |
| P9-H5 auxiliary profiles | PARTIALLY VERIFIED | PARTIALLY VERIFIED | optional storage confirmed; policy requirement absent |

No hypothesis reached VERIFIED. None was contradicted.

## 9. Missing artifacts

Minimum artifacts for a productive Phase 12:

1. Version-matched, non-empty B2
   `dyld_shared_cache_arm64e.79.dyldlinkedit` (expected UUID
   `79D3F635-C960-3C22-A00A-264E5975D82D`).
2. Matching B2 `dyld_shared_cache_arm64e.symbols`.
3. Complete B3/RC dyld caches for version comparison.
4. B3 `amfid` disassembly covering the full `sub_10000b194` and
   `AMFIPathValidator_ios validateWithError:` paths.
5. A real MIG/XPC client binary for `verify_code_directory` reply semantics.
6. launchd plist, sandbox profile, and entitlement metadata governing
   `com.apple.MobileFileIntegrity`.

## 10. Recommendation for Phase 12

Do not continue searching or extracting from the current Beta 2 cache. The
corrected partial Mach-O files are sufficient for string, ObjC-surface,
load-command, and selected `__TEXT` disassembly work, but not for full symbol
or cross-image call-graph recovery.

Phase 12 should begin only after obtaining either:

- a complete version-matched B2 cache set, or
- a specific B3/RC cache set with intact linkedit, or
- a complete `amfid`/client/sandbox artifact bundle sufficient to settle
  result propagation and reachability without dyld linkedit.

## 11. Safety and scope

- Offline static analysis only.
- No iPhone connected.
- No active IPC, fuzzing, exploit chain, bypass development, or modified
  system binary.
- Original cache files and source images were not modified.
- No Git push or automatic publication.

**Final conclusion:** Phase 11's principal result is a reliable data-quality
boundary. The Beta 2 cache is structurally indexed and mostly present, but
its required linkedit subcache is empty. The Phase 10 extraction was also
corrected. The trust architecture is confirmed at component/dependency
level and partially at function level; a complete cross-component call graph
and P9-H1 verdict are not supportable from the remaining local artifacts.
