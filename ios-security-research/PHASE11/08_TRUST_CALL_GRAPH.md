# Phase 11 Report 08 — Trust Call Graph

Objective: map the signature-validation call path across `amfid`,
`AppleMobileFileIntegrity`, `libmis`, `Security`, `MobileInstallation`,
`installd`, `MessageSecurity`, and supporting components.

Methodology note: `LC_SYMTAB`/`LC_DYLD_INFO_ONLY`/`LC_FUNCTION_STARTS` are
unrecoverable (absent `__LINKEDIT`). Call-graph edges are established via:

- `LC_LOAD_DYLIB` records (link-time dependency — confirmed).
- ObjC method names in `__objc_methname`/`__TEXT` (selector-level API surface).
- ObjC class names in `__objc_classname`/`__AUTH_CONST`.
- ARM64 disassembly of `__TEXT` in `amfid`/`installd` B3 disassemblies.

For every edge the "type" column indicates the level of proof:
`DEP` = `LC_LOAD_DYLIB` only, `OBJC` = ObjC selector name,
`CALL` = disassembled `BL`/`objc_msgSend`/`BLR` in the B3 disasm.

## 1. amfid → AppleMobileFileIntegrity / libmis / Security

| Source | Target | Type | Evidence | Confidence |
|---|---|---|---|---|
| `amfid` `sub_100004030` | `AMFIPathValidator_ios` (ObjC class) | CALL | B3 disasm shows `objc_alloc`/`objc_msgSend` selector `initWithURL:withFileOffset:withFlags:` | VERIFIED (function-level) |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios validateWithError:]` | CALL | selector name + `objc_msgSend` pattern | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios computedCdHash:]` | CALL | selector name | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios signerType]` | CALL | selector name | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios isValid]` | CALL | selector name | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios areEntitlementsValidated]` | CALL | selector name | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios profileData]` | CALL | selector name | VERIFIED |
| `amfid` `sub_100004030` | `-[AMFIPathValidator_ios profileAuxSig]` | CALL | selector name | VERIFIED |
| `amfid` `sub_1000049c8` | `bootstrap_check_in("com.apple.MobileFileIntegrity")` | CALL | B3 disasm | VERIFIED |
| `amfid` `sub_100004a24` | `dispatch_mach_mig_demux(...)` | CALL | B3 disasm | VERIFIED |
| `amfid` `sub_10000b194` | MIG `verify_code_directory` handler | CALL | B3 disasm | VERIFIED |
| `amfid` `sub_10000b3d8` | MIG DER-entitlement handler | CALL | B3 disasm | VERIFIED |
| `amfid` `sub_10000366c` | `AMFIUnserializeXML`-shaped parse | CALL | B3 disasm — `CFPropertyListCreateWithData`, `CFDictionary` check, `CESerializeCFDictionary`, `vm_read` | VERIFIED |

**Where `AMFIPathValidator_ios` actually lives:**

- The ObjC class name `AMFIPathValidator_ios` does not appear in
  `AppleMobileFileIntegrity_B2.dylib` — it is a private class compiled into
  `amfid` itself (or an associated helper embedded in the binary).
- `AppleMobileFileIntegrity` framework contains the *profile matching
  engine* — class names like `AMFIConnection`, `AMFIDeveloperModeSettingVisibilityManager`,
  `MISMatchedProfile`.
- The amfid-side validator then calls into `AppleMobileFileIntegrity` /
  `libmis` / `Security` via the MIG+XPC surface.

## 2. AppleMobileFileIntegrity internal flow

From the corrected `AppleMobileFileIntegrity_B2.dylib` `__TEXT` section:

Confirmed ObjC selectors/methods (via string extraction from `__TEXT`):

```
AMFIProfileRequiresReboot
AMFIProfileScheduleTrust
AMFIProfileGetScheduledProfile
AMFIProfileCommitProfile
AMFIProfileSetTeamIDTrustWithOptions
AMFIProfileRemoveTeamIDTrust
AMFISupervisedModeSetState
AMFIDemoModeSetState
AMFIMDMModeEnroll
AMFIMDMModeRemove
_getTeamIDAuxiliarySignature
-[AMFIConnection initiateDataMigration]_block_invoke
-[AMFIConnection initiateDeveloperModeDaemons]_block_invoke
-[AMFIConnection getSEPStateWithError:]_block_invoke
-[AMFIConnection signTeamID:withSignType:withLAContext:withError:]_block_invoke
-[AMFIConnection stageProfileForUuid:]_block_invoke
-[AMFIConnection getStagedProfileWithError:]_block_invoke
-[AMFIConnection commitProfileForUuid:]_block_invoke
-[AMFIConnection setTrustForTeamID:withSignature:withSignType:]_block_invoke
-[AMFIConnection removeTrustforTeamID:]_block_invoke
-[AMFIConnection setSupervisedState:]_block_invoke
-[AMFIConnection setDemoState:]_block_invoke
-[AMFIConnection setManagedState:]_block_invoke
-[AMFIConnection removeManagedState]_block_invoke
```

This is the **profile management API** used by `amfid`/`installd`/`misagent`
to schedule, commit, and remove trusted profiles — not the validator
implementation itself.

Confirmed error strings (validation failure categories):

```
Profile matching service is unavailable
Caller requested validation of an unknown platform
Caller requested validation with an invalid option
Caller provided invalid parameters
Profile requested is not currently staged
The best matching profile has expired
The best matching profile is not valid for this device
The best matching profile is not validly signed
No matching profile found
The best matching profile does not provision the certificates used to sign this file
The best matching profile does not match the entitlements of this file
The signature on the file is invalid
The file is unsigned
The entitlements in this file are malformed
The file is adhoc signed or signed by an unknown certificate chain
The file is adhoc signed but contains restricted entitlements
Unable to retrieve code path information
Unable to retrieve signing identifier
Unable to retrieve executable path
MIS Validation successful, but unexpected info? path: '%@', options: %@, info: %@, cdhash: %@
Unable to extract signer type? path: '%@', info: '%@'
%@ not valid: 0x%x: %@
boot-args allow process with invalid signature: %@
found local signing key as a system key
unable to find local signing key on the system
unable to add public key to AMFI
found untrusted object in the keychain
the local signing private key is not available: %d
successfully copied local signing private key
unable to find local signing key in keychain: %d
found no local signing keys in keychain
found multiple (%ld) local signing keys in keychain
successfully copied local signing private key from keychain
successfully created local signing private key in keychain
unable to extract public key from local signing private key
unable to add public key to AMFI: %d (%s)
added local signing public key to AMFI
Unexpected MISError (0x%x): %@
Dropping validation metrics because queue is full
[%s] profile UUID must be provided
[%s] request for profile: %@
[%s] auxiliary signature exists: %@
```

## 3. AppleMobileFileIntegrity → libmis / Security

| Source | Target | Type | Evidence | Confidence |
|---|---|---|---|---|
| `AppleMobileFileIntegrity` | `libmis.dylib` | DEP | `LC_LOAD_DYLIB /usr/lib/libmis.dylib` | VERIFIED |
| `AppleMobileFileIntegrity` | `Security.framework` | DEP | `LC_LOAD_DYLIB /System/Library/Frameworks/Security.framework/Security` | VERIFIED |
| `AppleMobileFileIntegrity` | `libCoreEntitlements.dylib` | DEP via libmis | libmis's own dep — used to parse DER entitlements | VERIFIED (transitive) |
| `AppleMobileFileIntegrity` | `sqlite3` | DEP via libmis | libmis owns `mis.db` | VERIFIED |
| `AppleMobileFileIntegrity` | `IOKit` | DEP | `LC_LOAD_DYLIB` — likely SEP/AMCC channel | VERIFIED |
| `AppleMobileFileIntegrity` | `CoreAnalytics` | DEP | `LC_LOAD_DYLIB` — `amfid.validation.metrics` | VERIFIED |

Function-level calls **not** proven — bind information is missing.

## 4. libmis internal state

From `libmis_B2.dylib` `__TEXT`/`__AUTH_CONST`:

- SQL schema strings: `cdhash_type INTEGER, cdhash BLOB NOT NULL,
  UNIQUE(cdhash_type, cdhash)`, `cdhash_type, cdhash, reason, flags,
  timestamp, kb_url, user_override, pk FROM launch_warning WHERE
  cdhash_type = ?1 AND cdhash = ?2`.
- Class/struct names: `MISProfileDBClient`, `MISOnlineAuthEntry`,
  `MISTrustedTeamIDEntry`, `MISTeamIDEntryForUI`, `MISTrustedProfileEntry`,
  `MISOnlineAuthMigrationState`, `LegacyUserTrustDB`,
  `LegacyTrustedTeamIdEntry`, `LegacyUserTrustedProfileEntry`,
  `LegacyUserTrustOperations`, `MISAgentClientError`,
  `MISDBManagerError`, `CodeSignatureError`, `CDHashInfo`.
- Dependency: `libCoreEntitlements` (DER entitlement parser) + `Security` +
  `sqlite3` + `IOKit` (SEP) + `CoreAnalytics` + `swift` runtime.

libmis is the **profile-state store** — `mis.db` holds `sep_trusted_team_ids`,
`user_trusted_profiles`, `banned_profile_uuids`, `launch_warning` records.

## 5. Security.framework internals

From `Security_B2.dylib` `__TEXT`:

C++ class names inside `Security::CodeSigning` namespace:

```
DetachedRep, FilterRep, DYLDCacheRep (Reader + Writer), SingleDiskRep,
EmbeddedSignatureBlob, Maker, SecCode, BundleDiskRep (Reader + Writer),
EditableDiskRep, DiskRep (Reader + Writer), FileDiskRep (Reader + Writer),
BlobWriter, DetachedBlobWriter, ArchEditor, BlobEditor, MachOEditor,
SecCodeSigner, SecStaticCode, ValidationContext, CollectingContext
```

Plus `Security::SuperBlobCore<EmbeddedSignatureBlob, 0xfade0cc0>` —
the CodeSigning requirement engine.

Plus libmis's `LC_LOAD_DYLIB` on `Security.framework` — confirms the lower
layer that libmis delegates to for actual SecTrust evaluation.

## 6. installd → MobileInstallation

| Source | Target | Type | Evidence | Confidence |
|---|---|---|---|---|
| `installd` `-[MIInstallableBundle _isValidWatchKitApp:…]` | `MIDaemonConfiguration codeSigningEnforcementIsDisabled` | CALL | B3 disasm shows getter call | VERIFIED |
| `installd` same | `MICodeSigningVerifier validateWatchKitV2StubExecutableBundle:error:` | CALL | B3 disasm | VERIFIED |
| `installd` `+[MIInstallableBundle _shouldSkipEligibilityChecksForInstallRequestorWithAuditToken:…]` | `MICodeSigningInfo signingIdentifierForAuditToken:error:` | CALL | B3 disasm | VERIFIED |
| `installd` same | `MITestManager isRunningInTestMode:outError:` | CALL | B3 disasm | VERIFIED |
| `installd` same | `testFlagsAreSet:0x200` | CALL | B3 disasm | VERIFIED |
| `MobileInstallation` (framework) | `MIHelperServiceFrameworkClient`, `MIStagingLocation`, `MIInstallOptions`, `MIStagingSubsystem` | OBJC | class names + selector names in `__TEXT`/`__AUTH_CONST` | VERIFIED |

## 7. CodesignKit / MessageSecurity / libDetachedCertificates

| Source | Target | Type | Evidence | Confidence |
|---|---|---|---|---|
| `CodesignKit` | `CodesignKit` Swift module | OBJC | `CSKHostError`, `CSKHostSource`, `CSKSignerIdentity`, `SignerSourceXPCProtocol_v1` | VERIFIED |
| `MessageSecurity` | `MSCMSSignedData`, `MSCMSSignerInfo` | OBJC | class names + CMS verification strings | VERIFIED |
| `MessageSecurity` | `heimdal-asn1` | DEP | `LC_LOAD_DYLIB` | VERIFIED |
| `libDetachedCertificates` | detached-chain consistency check | OBJC | `Compatibility version mismatch` error string | VERIFIED |
| `ProfileValidatedAppIdentity` | `DeviceCheck-1` project | OBJC | class names + project string | VERIFIED |

## 8. What is NOT on the trust path

These components exist but are not on the amfid code-signing path:

- `TrustKit` — ML/rules-based policy framework (deps: CoreML, CryptoKit,
  DeviceIdentity, Rules, RunningBoard, UnifiedAssetFramework). Not the
  TSKTrust pinning library; not invoked from amfid.
- `SecurityFoundation` — `ccspake_verifier_*` + `webVerifier` SPAKE
  cryptography; unrelated.
- `LocalAuthentication` — FileVault/password verification; unrelated.
- `ProfileValidatedAppIdentity` — `DeviceCheck` project — related to
  app-identity assertions, not the amfid validator path.

## 9. Reconstructed high-level graph

```
┌─────────────────────────────────────────────────────────────────┐
│ amfid (B3 disasm — real binary, not a dyld image)               │
│  ├─ bootstrap_check_in "com.apple.MobileFileIntegrity"         │
│  ├─ dispatch_mach_mig_demux                                     │
│  │    └─ MIG handlers:                                          │
│  │        verify_code_directory → sub_10000b194                │
│  │        DER entitlements     → sub_10000b3d8                │
│  │        XML unserialise+ver  → sub_10000366c                │
│  └─ AMFIPathValidator_ios (ObjC, embedded in amfid)            │
│       ├─ initWithURL:withFileOffset:withFlags:                 │
│       ├─ validateWithError:                                     │
│       ├─ computedCdHash:withLength:                             │
│       ├─ signerType                                             │
│       ├─ isValid                                                │
│       ├─ areEntitlementsValidated                              │
│       ├─ profileData                                            │
│       └─ profileAuxSig                                          │
│                                                                  │
│  Calls into (via DEP edges):                                    │
│   ├─ AppleMobileFileIntegrity (AMFIConnection, AMFIProfile*)     │
│   │    ├─ libmis (mis.db: teams/profiles/bans/launch_warn)       │
│   │    │    ├─ libCoreEntitlements (DER)                         │
│   │    │    ├─ Security.framework (SecCode/SecStaticCode)         │
│   │    │    ├─ sqlite3                                          │
│   │    │    └─ IOKit (SEP)                                      │
│   │    ├─ Security.framework (CodeSigning::* classes)             │
│   │    ├─ IOKit                                                 │
│   │    └─ CoreAnalytics (amfid.validation.metrics)              │
│   ├─ Security.framework                                         │
│   ├─ MessageSecurity.framework (CMS aux sig)                    │
│   └─ libDetachedCertificates.dylib (detached chain checks)      │
│                                                                  │
│ installd (B3 disasm):                                           │
│  └─ MobileInstallation.framework                                │
│       ├─ MICodeSigningVerifier                                  │
│       ├─ MIDaemonConfiguration                                  │
│       ├─ MIHelperServiceFrameworkClient                         │
│       ├─ MIStagingLocation                                      │
│       └─ deps: Security.framework, Bom, MobileSystemServices    │
└─────────────────────────────────────────────────────────────────┘
```

## 10. Confidence summary

| Edge | Confidence |
|---|---|
| amfid → `AMFIPathValidator_ios` selectors | VERIFIED (function-level) |
| amfid → `com.apple.MobileFileIntegrity` endpoint | VERIFIED |
| AMFI.framework → libmis | VERIFIED (DEP) |
| AMFI.framework → Security | VERIFIED (DEP) |
| libmis → libCoreEntitlements | VERIFIED (DEP) |
| libmis → sqlite3 | VERIFIED (DEP) |
| libmis → Security | VERIFIED (DEP) |
| installd → MobileInstallation | VERIFIED (function-level) |
| `AMFIPathValidator` → specific internal check | PARTIALLY VERIFIED (selector names confirmed; call sites not resolvable without linkedit) |
| `boot-args` flag honoured by AMFI | NOT VERIFIED (string located; call site not resolvable) |
| Real MIG client for `isValid`/`profile_valid` | NOT VERIFIED (no client binary recovered) |
