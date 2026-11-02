# Phase 10 Report 06 — Trust Dependency Map

Edges are `LC_LOAD_DYLIB` / `LC_LOAD_WEAK_DYLIB` / `LC_LOAD_UPWARD_DYLIB`
records read from each extracted Mach-O. These are *declared link-time*
dependencies — function-level reachability is not proven.

## 1. Dependency edges of trust components

### AppleMobileFileIntegrity.framework
```
/usr/lib/libmis.dylib                              ← MIS profile DB
/System/Library/Frameworks/Security.framework/Security  ← SecCode/SecTrust
/System/Library/Frameworks/Foundation.framework/Foundation
/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation
/usr/lib/libobjc.A.dylib
/usr/lib/libc++.1.dylib
/usr/lib/libSystem.B.dylib
/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit
/System/Library/PrivateFrameworks/CoreAnalytics.framework/CoreAnalytics
```

### libmis.dylib
```
/usr/lib/libCoreEntitlements.dylib                 ← DER entitlement parsing
/System/Library/Frameworks/Security.framework/Security
/System/Library/PrivateFrameworks/CoreAnalytics.framework/CoreAnalytics
/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit  ← SEP/keystore channel
/System/Library/Frameworks/Foundation.framework/Foundation
/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation
/usr/lib/libMobileGestalt.dylib
/usr/lib/libsqlite3.dylib                          ← mis.db backing store
/usr/lib/libobjc.A.dylib, libSystem.B.dylib, libc++.1.dylib
/usr/lib/swift/libswiftCore.dylib, libswiftDispatch.dylib, libswiftXPC.dylib,
    libswift_DarwinFoundation1.dylib, libswiftos.dylib
```

### Security.framework
```
/System/Library/PrivateFrameworks/AppleKeyStore.framework/AppleKeyStore ← SEP keys
/usr/lib/libcoretls.dylib, libcoretls_cfhelpers.dylib                     ← TLS
/usr/lib/libMobileGestalt.dylib
/usr/lib/libbsm.0.dylib                                                  ← audit
/usr/lib/libsqlite3.dylib
/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit
/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation
/System/Library/PrivateFrameworks/SoftLinking.framework/SoftLinking
/usr/lib/libobjc.A.dylib, libSystem.B.dylib, libc++.1.dylib
```

### MobileInstallation.framework
```
/System/Library/Frameworks/Security.framework/Security
/System/Library/PrivateFrameworks/Bom.framework/Bom
/System/Library/PrivateFrameworks/MobileSystemServices.framework/MobileSystemServices
/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation
/System/Library/Frameworks/Foundation.framework/Foundation
/usr/lib/libobjc.A.dylib, /usr/lib/libSystem.B.dylib
```

### MessageSecurity.framework
```
/System/Library/Frameworks/Security.framework/Security
/usr/lib/libheimdal-asn1.dylib                      ← ASN.1 decoder for CMS
/System/Library/PrivateFrameworks/CoreAnalytics.framework/CoreAnalytics
+ Foundation/CoreFoundation/objc/swift runtime
```

### CodesignKit.framework
```
/System/Library/Frameworks/ExtensionFoundation.framework/ExtensionFoundation
+ Foundation/CoreFoundation/objc/swift runtime
```

### libDetachedCertificates.dylib
```
+ Foundation/CoreFoundation/objc/libSystem only — leaf component
```

### TrustKit.framework
```
/System/Library/Frameworks/CoreML.framework/CoreML
/System/Library/Frameworks/CryptoKit.framework/CryptoKit
/System/Library/Frameworks/Security.framework/Security
/System/Library/PrivateFrameworks/DeviceIdentity.framework/DeviceIdentity
/System/Library/PrivateFrameworks/Rules.framework/Rules
/System/Library/PrivateFrameworks/RunningBoardServices.framework/RunningBoardServices
/System/Library/PrivateFrameworks/UnifiedAssetFramework.framework/UnifiedAssetFramework
/System/Library/PrivateFrameworks/CoreAnalytics.framework/CoreAnalytics
/usr/lib/libMobileGestalt.dylib
```
TrustKit is an ML/policy framework, **not** the certificate-pinning
TSKTrust library — it does not sit on the amfid signature path.

### ProfileValidatedAppIdentity.framework
```
+ Foundation/CoreFoundation/objc/libSystem only — thin wrapper
```

### SecurityFoundation.framework
```
/System/Library/Frameworks/Security.framework/Security
+ Foundation/CoreFoundation/objc/libSystem
```

### LocalAuthentication.framework
```
/System/Library/Frameworks/Security.framework/Security
/System/Library/PrivateFrameworks/LocalAuthenticationCore.framework/LocalAuthenticationCore
/System/Library/PrivateFrameworks/LocalAuthenticationCredentialServices.framework/...
/System/Library/Frameworks/LocalAuthentication.framework/Support/SharedUtils.framework/SharedUtils
/System/Library/PrivateFrameworks/SoftLinking.framework/SoftLinking
/System/Library/Frameworks/Combine.framework/Combine
+ swift runtime
```

## 2. Reconstructed trust validation graph

```
amfid (B3 disasm evidence)
  └─ bootstrap_check_in "com.apple.MobileFileIntegrity"
  └─ dispatch_mach_mig_demux
        │
        ▼ MIG: verify_code_directory, unserialize_and_verify, DER entitlements
  AMFIPathValidator_ios (in amfid address space)
        │
        ├─▶ AppleMobileFileIntegrity.framework
        │       ├─▶ libmis.dylib
        │       │      ├─▶ libCoreEntitlements.dylib
        │       │      ├─▶ libsqlite3  (mis.db:
        │       │      │              sep_trusted_team_ids,
        │       │      │              user_trusted_profiles,
        │       │      │              banned_profile_uuids)
        │       │      ├─▶ IOKit      (SEP trust state)
        │       │      └─▶ Security
        │       ├─▶ Security
        │       │      ├─▶ CodeSigning::SecCode / SecStaticCode /
        │       │      │    SecRequirement / SuperBlobCore / MachOImage
        │       │      ├─▶ AppleKeyStore (SEP)
        │       │      └─▶ coretls (policy evaluation)
        │       └─▶ IOKit, CoreAnalytics
        │
        └─▶ MessageSecurity (CMS aux signatures)
               └─▶ heimdal-asn1, Security

installd (B3 disasm evidence)
  └─▶ MobileInstallation.framework
         ├─▶ Security       (MICodeSigningVerifier internals)
         ├─▶ Bom
         └─▶ MobileSystemServices

Supporting trust components
  CodesignKit               — codesigning policy abstraction (Swift)
  libDetachedCertificates   — detached CMS chain structure checks
  ProfileValidatedAppIdentity — thin helper over provisioning profiles
  SecurityFoundation        — ObjC façade over Security
  TrustKit                  — ML-based trust, NOT on the signature path
```

## 3. Edge semantics confirmed by strings

| Producer → Consumer | Evidence |
|---|---|
| AMFI → libmis | `LC_LOAD_DYLIB /usr/lib/libmis.dylib`; AMFI contains profile-scheduling and team-ID strings that match libmis's `sep_trusted_team_ids`, `user_trusted_profiles` tables |
| AMFI → Security | `LC_LOAD_DYLIB /System/Library/Frameworks/Security.framework/Security`; AMFI error text "entitlements in this file are malformed", "signature on the file is invalid" mirror `SecCode`/`SecStaticCode` operations |
| libmis → libCoreEntitlements | direct dependency — DER-encoded entitlement blobs live in `libCoreEntitlements` |
| libmis → sqlite | `LC_LOAD_DYLIB libsqlite3.dylib`; `mis.db`, `sep_trusted_team_ids` |
| MessageSecurity → Security | `LC_LOAD_DYLIB Security`; `MSCMSSignedData`/`MSCMSSignerInfo` call into `SecTrust` |
| installd → MobileInstallation | B3 disasm `-[MIInstallableBundle _isValidWatchKitApp:]` calling `MICodeSigningVerifier` |

## 4. Edges NOT proven

- No `LC_LOAD_DYLIB` from any recovered image points to `CoreTrust.framework`
  (it does not exist as a separate image).
- No `LC_LOAD_DYLIB` to `libsecurity_codesigning` — functionality folded into
  `Security`.
- No `LC_LOAD_DYLIB` to `amfid`/`installd`/`trustd` — executables are not
  linkable dependencies.
- `LC_LOAD_WEAK_DYLIB` names are empty strings on every image — dyld-cache
  weak-link records collapse to an empty name and cannot be used for mapping.
