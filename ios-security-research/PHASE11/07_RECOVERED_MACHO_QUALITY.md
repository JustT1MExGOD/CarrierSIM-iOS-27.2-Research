# Phase 11 Report 07 — Recovered Mach-O Quality (v2)

Per-file quality assessment for the 11 dylibs extracted by the corrected
Phase 11 extractor (`extract_flat.py`). Supersedes the first version of
this report — the Phase 10 files contained segment overlap corruption.

## 1. Structural integrity

| File | Size | Header | Load cmds | UUID | Segments present | `__LINKEDIT` | Verdict |
|---|---|---|---|---|---|---|---|
| `AppleMobileFileIntegrity_B2.dylib` | 90 KB | VALID | 25 | matches B2 image array | `__TEXT` `__DATA_CONST` `__AUTH_CONST` `__DATA` `__DATA_DIRTY` | absent | STRUCTURALLY VALID |
| `libmis_B2.dylib` | 463 KB | VALID | 35 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `Security_B2.dylib` | 2.28 MB | VALID | 41 | matches | 6 segments | absent | STRUCTURALLY VALID |
| `MobileInstallation_B2.dylib` | 254 KB | VALID | 25 | matches | 6 segments | absent | STRUCTURALLY VALID |
| `CodesignKit_B2.dylib` | 74 KB | VALID | 33 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `libDetachedCertificates_B2.dylib` | 57 KB | VALID | 19 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `MessageSecurity_B2.dylib` | 475 KB | VALID | 29 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `SecurityFoundation_B2.dylib` | 172 KB | VALID | 20 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `TrustKit_B2.dylib` | 639 KB | VALID | 51 | matches | 6 segments | absent | STRUCTURALLY VALID |
| `ProfileValidatedAppIdentity_B2.dylib` | 29 KB | VALID | 19 | matches | 5 segments | absent | STRUCTURALLY VALID |
| `LocalAuthentication_B2.dylib` | 356 KB | VALID | 34 | matches | 6 segments | absent | STRUCTURALLY VALID |

Per-image `LC_SYMTAB`, `LC_DYLD_INFO_ONLY`, `LC_FUNCTION_STARTS`,
`LC_DATA_IN_CODE`, `LC_ATOM_INFO`, `LC_DYLIB_CODE_SIGN_DRS` are all declared
in headers but their contents live in the absent `__LINKEDIT` region — file
offsets rewritten to 0 in the extracted files. `LC_CODE_SIGNATURE` is not
declared (dyld-cache images carry no per-image signatures).

## 2. Analytic usability

| Capability | Possible? | Notes |
|---|---|---|
| Disassemble `__TEXT` | YES | real arm64e bytes; verified with capstone (`pacibsp`, `stp`, `adrp`, `bl`) |
| Recover function boundaries | PARTIAL | no `LC_FUNCTION_STARTS`; derive from `BL` chains + prologue patterns (`pacibsp`/`stp`/`sub sp`) |
| Resolve imports | NO | bind opcodes in missing linkedit |
| Resolve exports | NO | export trie in missing linkedit |
| ObjC class names | YES | `__objc_classname`/`__AUTH_CONST` readable |
| ObjC selector names | YES | `__objc_methname` readable |
| ObjC method signatures | YES | method list entries inside class structures |
| ObjC sel→IMP | PARTIAL | class structures in `__AUTH_CONST` contain method IMP addresses; resolvable by VA arithmetic, no linkedit needed |
| Cross-dylib calls | PARTIAL | `BL` targets within same `__TEXT` resolve; calls through stubs need bind info to name targets |
| String xref | YES | ADRP+ADD pattern matching on `__TEXT` |
| Verify code signature | N/A | none present |

## 3. Quality classification

| File | Classification |
|---|---|
| `AppleMobileFileIntegrity_B2.dylib` | PARTIALLY USABLE — complete `__TEXT`+ObjC surface; no symbols/bind |
| `libmis_B2.dylib` | PARTIALLY USABLE — same |
| `Security_B2.dylib` | PARTIALLY USABLE — same; larger surface |
| `MobileInstallation_B2.dylib` | PARTIALLY USABLE — same |
| `CodesignKit_B2.dylib` | PARTIALLY USABLE — Swift metadata intact |
| `libDetachedCertificates_B2.dylib` | PARTIALLY USABLE — leaf component |
| `MessageSecurity_B2.dylib` | PARTIALLY USABLE — CMS strings confirmed |
| `SecurityFoundation_B2.dylib` | PARTIALLY USABLE |
| `TrustKit_B2.dylib` | PARTIALLY USABLE |
| `ProfileValidatedAppIdentity_B2.dylib` | PARTIALLY USABLE |
| `LocalAuthentication_B2.dylib` | PARTIALLY USABLE — out of scope for signature path |

**None reach `ANALYSIS READY`** — that grade requires resolvable imports
and exports.

## 4. Per-component capability

### `AppleMobileFileIntegrity`
- Strings confirmed: `MISProvisioningProfileInstalled/Removed`, developer-
  mode strings, `AMFIProfile*` API names, all `MIS Validation …` / `boot-args
  allow process …` / `auxiliary signature exists` strings.
- ObjC class names visible in `__AUTH_CONST`: `AMFIDeveloperModeSettingVisibilityManager`,
  `MISMatchedProfile`, block signature `B16@?0r^{MISMatchedProfile=…}`.
- Selector names for validator operations present.

### `libmis`
- Confirmed: `CodeSignatureError`, `CDHashInfo`, `LegacyUserTrustDB`,
  `MISOnlineAuthEntry`, `MISTrustedTeamIDEntry`, `MISTrustedProfileEntry`,
  `mis.LaunchWarningDB` SQL schema (`cdhash_type`, `cdhash`, `reason`,
  `flags`, `timestamp`, `kb_url`, `user_override`).

### `Security`
- Confirmed: `N8Security11CodeSigning{DetachedRep,FilterRep,DYLDCacheRep,
  SingleDiskRep,EmbeddedSignatureBlob,Maker,SecCode,BundleDiskRep,
  EditableDiskRep,DiskRep,FileDiskRep,BlobWriter,DetachedBlobWriter,
  ArchEditor,BlobEditor,MachOEditor,SecCodeSigner,SecStaticCode,
  ValidationContext,CollectingContext}` — C++ code-signing classes intact.

### `MobileInstallation`
- Confirmed: `MIStagingLocation`, `MIHelperServiceFrameworkClient`,
  `MIInstallOptions`, `developerInstall`, `systemAppInstall`,
  `lsInstallType`, `provisioningProfiles`, `SkipWatchAppInstall`,
  `provisioningProfileInstallFailureIsFatal`, `installationRequestorAuditToken`.

### `CodesignKit`
- Confirmed: Swift module `CodesignKit`, `CSKHostError`, `CSKHostSource`,
  `CSKSignatureAlgorithmWrapper`, `CSKMessageDigest`, `CSKSignerIdentity`,
  `SignerSourceXPCProtocol_v1`, `SignerSourceConfiguration`.

### `MessageSecurity`
- Confirmed: CMS/`MSCMSSignedData`/`MSCMSSignerInfo`, timestamp/TSA error
  strings, signer/countersigner verification errors.

### `libDetachedCertificates`
- Confirmed: detached chain validation — `"Compatibility version mismatch:
  self=%llu, other=%llu"` is the only extracted string.

### `TrustKit`
- Confirmed: `TrustKit` Swift module, `com.apple.security.webverifier`
  entitlement — clearly *not* on the amfid signature path.

### `SecurityFoundation`
- Confirmed: `ccspake_verifier_*` SPAKE crypto, `webVerifier` — unrelated to
  AMFI/profile signing.

### `LocalAuthentication`
- Confirmed: `LACredentialTypeExtractablePassword`, `MKBKeyBagKeyStashVerify`,
  FileVault verify paths — unrelated to code-signing trust.

### `ProfileValidatedAppIdentity`
- Confirmed: `DeviceCheck-1` project name — provisioning-profile–backed app
  identity assertions.

## 5. What is NOT recoverable

- `LC_SYMTAB` contents → symbol table entries.
- `LC_DYLD_INFO_ONLY` → bind/rebase/export tries.
- `LC_FUNCTION_STARTS` → function boundary index.
- `LC_DATA_IN_CODE` → code/data interleaving table.
- `LC_CODE_SIGNATURE` → not present anyway (per-image sig absent in dyld
  cache format).
- Cross-image `BL` target names → stub→bind resolution missing.

## 6. Verdict

All 11 files are **STRUCTURALLY VALID** Mach-O dylibs and **PARTIALLY
USABLE** for static analysis. The earlier Phase 10 files are superseded —
they contained a segment-overlap bug that made them unusable.
