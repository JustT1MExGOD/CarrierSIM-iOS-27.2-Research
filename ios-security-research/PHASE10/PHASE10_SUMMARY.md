# Phase 10 Summary — Trust Framework Recovery, Binary Extraction &
Evidence Expansion

## Headline result

The "missing" trust frameworks from Phase 9 were never missing — they are
embedded in the iOS 27.2 Beta 2 split dyld shared cache. By parsing the
image array directly (bypassing `ipsw.exe`, which fails on the empty
`.79.dyldlinkedit` subcache), Phase 10 recovered valid Mach-O headers, all
regular segments, UUIDs, and `LC_LOAD_DYLIB` dependency graphs for eleven
trust-relevant components.

The cache copy is itself incomplete: `.79.dyldlinkedit` and `.symbols` are
empty files. Every extracted dylib therefore has a structurally valid header
and real code/data pages but a zero-filled linkedit region. Symbol tables,
export/bind tries, and per-image code signatures are physically absent.

## Reports produced

| Report | File | Purpose |
|---|---|---|
| 01 | `01_PHASE9_EVIDENCE_GAPS.md` | What Phase 9 could not verify and what Phase 10 resolved |
| 02 | `02_LOCAL_SOURCE_INVENTORY.md` | Local artifact inventory and constraints |
| 03 | `03_COMPONENT_DISCOVERY.md` | Per-component UUIDs, roles, high-value strings |
| 04 | `04_DYLD_EXTRACTION_LOG.md` | Extraction methods, failures, results |
| 05 | `05_MACHO_VALIDATION.md` | Header/segment validation, missing-linkedit verdict |
| 06 | `06_TRUST_DEPENDENCY_MAP.md` | Dependency graph + reconstructed trust flow |
| 07 | `07_PHASE9_HYPOTHESIS_RECHECK.md` | P9-H1…H5 status under new evidence |
| 08 | `08_VERSION_COMPONENT_MATRIX.md` | Per-version availability matrix + B2 UUIDs |
| 09 | `09_EVIDENCE_QUALITY.md` | Per-claim quality with false-positive caveats |

## Component status recap

| Component | Phase 9 status | Phase 10 status |
|---|---|---|
| Security.framework | MISSING | PARTIALLY RECOVERED |
| MobileInstallation.framework | MISSING | PARTIALLY RECOVERED |
| libmis.dylib | MISSING | PARTIALLY RECOVERED |
| AppleMobileFileIntegrity.framework | MISSING | PARTIALLY RECOVERED |
| CodesignKit / libDetachedCertificates / TrustKit / ProfileValidatedAppIdentity / LocalAuthentication / SecurityFoundation / MessageSecurity | not classified | PARTIALLY RECOVERED |
| CoreTrust.framework | expected separate framework | CONTRADICTED — not a separate image on B2 |
| libsecurity_codesigning | expected separate library | CONTRADICTED — folded into `Security` |
| amfid, installd, trustd | binaries in filesystem | unchanged (amfid/installd via B3 disasm) |

## Architectural findings

1. **Dependency layering.** `AppleMobileFileIntegrity → libmis +
   Security` is the profile-validation spine. `libmis → libCoreEntitlements
   + sqlite` is the profile DB. `Security → AppleKeyStore + coretls` is the
   cryptographic core. `MobileInstallation → Security` is the install-side
   consumer.

2. **CoreTrust is no longer a separate framework on iOS 27.2.** Its
   functionality lives inside `Security` (C++ `CodeSigning::Sec*` classes)
   and `AppleMobileFileIntegrity` (profile policy). Phase 9's assumption of
   a separate CoreTrust image should be revised.

3. **TrustKit is not on the signature path.** Its dependency set (CoreML,
   CryptoKit, DeviceIdentity, Rules, RunningBoard, UnifiedAssetFramework)
   marks it as an ML/policy component, unrelated to the TSKTrust pinning
   library and unrelated to amfid's validator.

4. **Auxiliary signatures exist as an optional field.** libmis stores
   `HasAuxiliarySignature` alongside `ProfileID`; AMFI exposes
   `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`,
   `_createAuxiliarySignature`. Storage is optional; policy requirement is
   unproven.

5. **Boot-args string located.** `"boot-args allow process with invalid
   signature: %@"` is present in `AppleMobileFileIntegrity`'s `__TEXT`.
   Its call site and gating are unproven — *not* a demonstrated bypass.

## Hypothesis verdicts

| Hypothesis | Verdict |
|---|---|
| P9-H1 (`isValid=1` + `profile_valid=0`) | PARTIALLY VERIFIED — validator surface confirmed; discriminating caller unproven |
| P9-H2 (entitlement↔signature binding) | PARTIALLY VERIFIED — components confirmed; single chokepoint unproven |
| P9-H3 (MIG reachability) | NOT VERIFIED — no sandbox/launchd policy data |
| P9-H4 (boot-args bypass) | PARTIALLY VERIFIED — string located; reachability/gating unproven; no claim of exploitability |
| P9-H5 (aux signatures optional) | PARTIALLY VERIFIED — optional at storage layer; policy requirement unproven |

## Outstanding limitations

- `__LINKEDIT` and `.symbols` subcaches are empty on the local Beta 2 cache
  — symbol-level work needs a different cache copy or a different tool.
- No Beta 3 or RC trust-framework extraction has been performed; the version
  matrix is one column wide.
- amfid/installd function-level claims still rest solely on the B3
  disassemblies, not on B2 binaries.
- `com.apple.MobileFileIntegrity` MIG reachability and the boot-args guard
  require launchd/sandbox data that does not live in the dyld cache.

## Safety and constraints observed

- Offline analysis only.
- No device interaction, no IPC, no fuzzing.
- No modification of original IPSW/OTA/DMG/cache/binary files.
- No exploit chains, no AMFI/CoreTrust/sandbox bypass work, no modified
  executables for signature bypass.
- No Git push, no automatic publication.

All extracted artifacts live under
`C:\ipsw-tools\IOS_SECURITY_RESEARCH\PHASE10\extracted\dyld_B2\` and are
clearly labelled as partial reconstructions.
