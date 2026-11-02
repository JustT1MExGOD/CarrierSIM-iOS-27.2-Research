# Phase 10 Report 08 — Version Component Matrix

Scope: presence and recovery status of trust components across the three
analysed builds.

## 1. Per-component availability

| Component | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| Security.framework | PARTIALLY RECOVERED (dyld cache) | NOT EXTRACTED | NOT EXTRACTED |
| MobileInstallation.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| libmis.dylib | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| AppleMobileFileIntegrity.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| CodesignKit.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| libDetachedCertificates.dylib | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| TrustKit.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| ProfileValidatedAppIdentity.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| LocalAuthentication.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| SecurityFoundation.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| MessageSecurity.framework | PARTIALLY RECOVERED | NOT EXTRACTED | NOT EXTRACTED |
| CoreTrust.framework | ABSENT (as standalone image) | UNKNOWN | UNKNOWN |
| libsecurity_codesigning | ABSENT (folded into Security) | UNKNOWN | UNKNOWN |
| amfid (executable) | extracted | disassembled | not extracted |
| installd (executable) | extracted | disassembled | not extracted |
| trustd | not located | not located | not located |

Legend:
- **PARTIALLY RECOVERED** — Mach-O present, headers + segments valid, linkedit
  absent.
- **NOT EXTRACTED** — corresponding split dyld cache has not been processed.
- **ABSENT** — not in the image array; component does not exist as a
  separate image on iOS 27.2.
- **UNKNOWN** — no local data for that version.

## 2. Beta 2 component UUIDs (for future cross-version diff)

```
Security                     A413232A-E824-39DF-AAFA-2E7E6153AE24
MobileInstallation           60B509C3-9DED-3504-8840-9874714C0109
libmis                       CE1D3D2A-3EC2-3A6D-AFA8-2FEDA08BCB68
AppleMobileFileIntegrity     A235E3C2-68CE-338A-8ED8-FFE4462860C5
CodesignKit                  0EC827C0-6BFE-392A-871F-CCAAE3917D0A
libDetachedCertificates      D0B631B9-359C-360F-8359-880558F926C1
TrustKit                     0791DC22-F4E8-3F90-8680-A7870D03EB67
ProfileValidatedAppIdentity  8631DD74-4F53-3328-BBE6-4AD26083027C
LocalAuthentication          2EB95A78-2506-3B6F-858B-DA37CD913010
SecurityFoundation           3245DBC2-ECE6-3BEA-B885-21917B0179DF
MessageSecurity              67504E44-A574-3334-BC94-8421CC1AB505
```

When Beta 3 or RC caches become available, comparing these UUIDs is the
fastest way to confirm whether an image was rebuilt between versions.

## 3. Architectural deltas already observed

- `CoreTrust.framework` does **not** exist on iOS 27.2 Beta 2 — a change from
  earlier releases where CoreTrust was a separate private framework. Its
  functions appear absorbed into `Security` and `AppleMobileFileIntegrity`.
- `libsecurity_codesigning.dylib` likewise does not appear — the
  `N8Security11CodeSigning*` C++ class names are inside `Security` directly.
- `TrustKit.framework` is now an ML/rules-based component (deps on CoreML,
  CryptoKit, DeviceIdentity, Rules, RunningBoardServices,
  UnifiedAssetFramework). It is not part of the amfid signature path.

## 4. What a Beta 3 / RC comparison would tell us

- Whether `AMFIPathValidator_ios` selector set changed between versions —
  indicator of policy surface drift.
- Whether the boot-args check string is present in RC — presence in RC would
  weaken the "development-only" interpretation.
- Whether the profile-aux-signature schema (libmis's `mis.db` column list)
  has new required fields.
- Whether `CoreTrust` reappears as a separate image in RC.
