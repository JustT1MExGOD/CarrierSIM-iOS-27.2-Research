# Phase 10 Report 02 — Local Source Inventory

Scope: every local artifact consulted or probed during Phase 10. All offline.

## 1. Primary binary sources

| Source | Path | Version | Status |
|---|---|---|---|
| Beta 2 dyld split cache | `C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\dyld_shared_cache_arm64e` (+ `.1`–`.79` subcaches) | iOS 27.2 B2 | PARTIALLY USABLE — `.79.dyldlinkedit` and `.symbols` subcaches are empty |
| Main cache SHA-256 | `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8` | — | recorded in Phase 8 |
| Beta 3 `amfid` disassembly | `amfid_B3_disasm.txt` | iOS 27.2 B3 | usable — primary function-level evidence |
| Beta 3 `installd` disassembly | `installd_B3_disasm.txt` | iOS 27.2 B3 | usable |
| Phase 8 binary artifacts | extracted `amfid`, `installd`, IPSW contents | B2/B3 | usable where present |

## 2. Phase 9 reports consumed

- `PHASE9\01_TRUST_COMPONENT_INVENTORY.md`
- `PHASE9\02_TRUST_ARCHITECTURE.md`
- `PHASE9\03_ERROR_HANDLING_REVIEW.md`
- `PHASE9\04_TRUST_DECISION_CONSISTENCY.md`
- `PHASE9\08_SECURITY_HYPOTHESES.md`
- `PHASE9\09_HYPOTHESIS_VERIFICATION.md`
- `PHASE9\10_FINDINGS_MATRIX.md`
- `PHASE9\PHASE9_SUMMARY.md`

## 3. Phase 10 tooling and artifacts produced

| Artifact | Path | Notes |
|---|---|---|
| Segment extractor | `PHASE10\extract_dyld_segments.py` | maps split-cache segments to backing files |
| Image validator | `PHASE10\validate_dyld_images.py` | parses headers/load commands |
| Validation JSON | `PHASE10\dyld_image_validation.json` | flags `VERIFIED` on declared load commands — must be read as PARTIAL because linkedit is empty |
| Extraction log | `PHASE10\dyld_extract_segments.log` | records `MISSING __LINKEDIT` for every target |
| Extracted dylibs | `PHASE10\extracted\dyld_B2\*.dylib` | 11 partial Mach-O files — valid headers + segments, zeroed linkedit |

## 4. Sources not available locally

- No standalone `CoreTrust.framework` image in the Beta 2 cache image array.
- No `libsecurity_codesigning.dylib` as a separate image — its functionality
  appears absorbed into `Security.framework` (`N8Security11CodeSigning*` C++
  classes).
- No Beta 3 / RC split dyld caches parsed for trust frameworks.
- No standalone `trustd` Mach-O.
- No kernelcache / XNU AMFI policy binary parsed this phase.
- No device-connected or live service data (per offline constraint).

## 5. Integrity constraints observed

- No original IPSW, OTA, DMG, kernelcache, dyld cache, or original binary was
  modified. All extraction wrote to `PHASE10\extracted\dyld_B2\`.
- No device interaction, no active IPC, no fuzzing, no Git push.
