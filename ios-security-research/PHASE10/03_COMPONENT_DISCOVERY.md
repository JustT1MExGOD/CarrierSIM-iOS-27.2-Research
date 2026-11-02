# Phase 10 Report 03 — Component Discovery

Method: parse `dyld_shared_cache_arm64e` image array for Beta 2, record each
image's install path, VM base, Mach-O UUID, and declared `LC_ID_DYLIB`.

## 1. Trust-relevant images found in Beta 2 cache

| Image | Install path | UUID | Segments | ncmds |
|---|---|---|---|---|
| Security | `/System/Library/Frameworks/Security.framework/Security` | `A413232A-E824-39DF-AAFA-2E7E6153AE24` | 7 | 41 |
| MobileInstallation | `/System/Library/PrivateFrameworks/MobileInstallation.framework/MobileInstallation` | `60B509C3-9DED-3504-8840-9874714C0109` | 7 | 25 |
| libmis | `/usr/lib/libmis.dylib` | `CE1D3D2A-3EC2-3A6D-AFA8-2FEDA08BCB68` | 6 | 35 |
| AppleMobileFileIntegrity | `/System/Library/PrivateFrameworks/AppleMobileFileIntegrity.framework/AppleMobileFileIntegrity` | `A235E3C2-68CE-338A-8ED8-FFE4462860C5` | 6 | 25 |
| CodesignKit | `/System/Library/PrivateFrameworks/CodesignKit.framework/CodesignKit` | `0EC827C0-6BFE-392A-871F-CCAAE3917D0A` | 6 | 33 |
| libDetachedCertificates | `/usr/lib/libDetachedCertificates.dylib` | `D0B631B9-359C-360F-8359-880558F926C1` | 6 | 19 |
| TrustKit | `/System/Library/PrivateFrameworks/TrustKit.framework/TrustKit` | `0791DC22-F4E8-3F90-8680-A7870D03EB67` | 7 | 51 |
| ProfileValidatedAppIdentity | `/System/Library/PrivateFrameworks/ProfileValidatedAppIdentity.framework/ProfileValidatedAppIdentity` | `8631DD74-4F53-3328-BBE6-4AD26083027C` | 6 | 19 |
| LocalAuthentication | `/System/Library/Frameworks/LocalAuthentication.framework/LocalAuthentication` | `2EB95A78-2506-3B6F-858B-DA37CD913010` | 7 | 34 |
| SecurityFoundation | `/System/Library/PrivateFrameworks/SecurityFoundation.framework/SecurityFoundation` | `3245DBC2-ECE6-3BEA-B885-21917B0179DF` | 6 | 20 |
| MessageSecurity | `/System/Library/PrivateFrameworks/MessageSecurity.framework/MessageSecurity` | `67504E44-A574-3334-BC94-8421CC1AB505` | 6 | 29 |

All: `MH_MAGIC_64`, `MH_DYLIB` (type 6), arm64e.

## 2. Trust-relevant images NOT found

| Component | Status |
|---|---|
| `CoreTrust.framework` | NOT PRESENT as a standalone image in B2 cache. Functionality appears absorbed into `Security` / `AppleMobileFileIntegrity`. |
| `libsecurity_codesigning.dylib` | NOT PRESENT as a standalone image. `N8Security11CodeSigning*` symbols live inside `Security`. |
| `trustd` | executables are not in the dyld cache — not discoverable this way. |
| `amfid`, `installd` | executables — only available from B3 disassemblies. |

## 3. High-value string evidence per component

### AppleMobileFileIntegrity (`__TEXT`)
- `Profile matching service is unavailable`
- `The best matching profile has expired`
- `The best matching profile is not valid for this device`
- `The best matching profile is not validly signed`
- `No matching profile found`
- `The best matching profile does not provision the certificates used to sign this file`
- `The best matching profile does not match the entitlements of this file`
- `The signature on the file is invalid`
- `The entitlements in this file are malformed`
- `The file is adhoc signed or signed by an unknown certificate chain`
- `The file is adhoc signed but contains restricted entitlements`
- `Unable to retrieve certificate chain`
- `AMFIProfileScheduleTrust`, `AMFIProfileGetScheduledProfile`, `AMFIProfileCommitProfile`
- `AMFIProfileSetTeamIDTrustWithOptions`, `AMFIProfileRemoveTeamIDTrust`
- `_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`, `_createAuxiliarySignature`
- `boot-args allow process with invalid signature: %@`

### libmis (`__TEXT`)
- `MISProfileDBClient`, `LegacyUserTrustDB`
- `mis.db`, `/Library/MobileDevice/ProvisioningProfiles`
- `sep_trusted_team_ids`, `user_trusted_profiles`, `banned_profile_uuids`
- `AuxiliarySignature`, `ProfileID`, `HasAuxiliarySignature`
- `CodeSignatureError`, `Trust`

### Security (`__TEXT`)
- C++ class names: `Security::CodeSigning::SecCode`, `SecStaticCode`,
  `SecRequirement`, `SuperBlobCore`, `EmbeddedSignatureBlob`, `MachOImage`,
  `DYLDCacheRep`, `DiskRep` variants, `DetachedRep`, `BlobWriter`,
  `EditableDiskRep`, `BundleDiskRep`, `SingleDiskRep`, `ArchEditor`.
- Anchor requirements: `anchor apple generic ...`
- Embedded test-root certificates:
  `Test Apple Platform Code Signing ML-DSA RSA Root CA - G1 HW0`,
  `Apple Code Signing Certification Authority`,
  `Apple Accessories Provisioning Authority`.

### MessageSecurity (`__TEXT`)
- `MSCMSSignedData`, `MSCMSSignerInfo`, `CMSIdentifier`
- `signature verification failed for signer`
- `unable to build chain according to mode`, `could not evaluate trust`
- `decode failed due to signature verification failure`

### MobileInstallation (`__TEXT`)
- Provisioning-profile and entitlement-management strings consistent with the
  `MICodeSigningVerifier` / `MIInstallableBundle` classes already seen in the
  installd B3 disassembly.

### libDetachedCertificates (`__TEXT`)
- Detached certificate sequence and AKID/SKID consistency validation strings.

## 4. Role assignment for the trust model

| Component | Phase 9 role | Phase 10 role | Status |
|---|---|---|---|
| amfid | MIG/NSXPC verifier | unchanged | VERIFIED via B3 disasm |
| AMFIPathValidator_ios | path validator ObjC class | backed by AppleMobileFileIntegrity + libmis + Security | VERIFIED (deps + class strings) |
| libmis | profile DB | same; also `sep_trusted_team_ids`, aux signatures | VERIFIED (structure-level) |
| Security | code-sign engine | `CodeSigning::SecCode/SecStaticCode/SecRequirement` + `libCoreEntitlements` dep | VERIFIED |
| MobileInstallation | installd verifier host | `MICodeSigningVerifier` etc. | VERIFIED (B3 disasm + B2 strings) |
| MessageSecurity | CMS layer | `MSCMSSignedData` etc. | VERIFIED |
| TrustKit | not previously placed | ML/rules-based trust (CoreML, CryptoKit, DeviceIdentity deps) — NOT TSKTrust pin validator | PARTIALLY VERIFIED |
| CoreTrust | standalone framework | no separate image — folded into Security/AMFI | CONTRADICTED (as separate framework) |

## 5. Discovery limitations

- String presence is *existence* evidence, not *reachability* evidence. A
  format string being present does not prove the error path is hit in the
  amfid validation flow.
- `LC_SYMTAB` commands are declared (e.g. Security `nsym=9996`) but the
  backing symbol/linkedit pages are absent from this cache copy, so exported
  symbol names can only be inferred from `__TEXT` strings and ObjC metadata,
  not enumerated from the table.
