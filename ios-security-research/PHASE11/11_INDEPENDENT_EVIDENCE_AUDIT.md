# Phase 11 Report 11 — Independent Evidence Audit

Self-audit of Phase 11 claims, checking for the specific failure modes
listed in the task.

## 1. Version confusion check

| Claim | Check | Result |
|---|---|---|
| Cache is iOS 27.2 Beta 2 | `beta2-dyld` directory name; matches `24B5089g__iPhone16,1` build | CONFIRMED — no version mixup |
| B3 disasm is for Beta 3 | filenames `amfid_B3_disasm.txt`, `installd_B3_disasm.txt` | CONFIRMED — B3 only, distinct from B2 cache |
| No RC material present | `rc-test-24B119` has only logs, no cache | CONFIRMED |

## 2. UUID mixing check

| Claim | Check | Result |
|---|---|---|
| Extracted dylib UUIDs match image array | all 11 files re-verified via `LC_UUID` — see `05_MACHO_VALIDATION.md` (Phase 10) and section-table check this phase | CONFIRMED |
| Subcache UUIDs match `subCacheArray` | all 78 non-empty subcaches verified against expected table | CONFIRMED |
| Image array UUID ≠ subcache UUID | these are different ID spaces; no cross-reference attempted | CONFIRMED — no conflation |

## 3. Strings-as-behavior check

Claims that could be mistaken:

| String | What it proves | What it does NOT prove |
|---|---|---|
| `AMFIProfileScheduleTrust` etc. | the symbol names exist | that `amfid` calls them — needs call-site proof |
| `The best matching profile …` | the error vocabulary exists | that the error is ever emitted — needs caller reachability |
| `boot-args allow process with invalid signature: %@` | the string exists in `__TEXT` | that the flag is honoured — needs xref + guard |
| `HasAuxiliarySignature` | the column exists in `mis.db` schema | that absence is always tolerated — needs policy code |
| `isValid`, `profileAuxSig`, `areEntitlementsValidated` | the selectors exist on `AMFIPathValidator_ios` | that they're consumed the way Phase 9 assumed — needs caller |

All downstream reports flag these as `PARTIALLY VERIFIED` or `NOT
VERIFIED`, not as confirmed behaviour. **OK.**

## 4. Imports-as-calls check

- `LC_LOAD_DYLIB` edges are used only as `DEP` (link-time dependency)
  markers in report 08, never as `CALL` evidence.
- Function-level edges (`CALL`) are only claimed where the B3 `amfid` /
  `installd` disasm explicitly shows `objc_msgSend`, `BL`, or `BLR` to a
  named selector/function.
- No claims of "libmis calls SecTrust" — only `libmis → Security` DEP edge.

## 5. Recovered-symbol-as-original check

- No symbols were fabricated. `LC_SYMTAB` contents are unreadable (pointed
  into absent linkedit); `dyld_image_validation.json` correctly notes them
  as declared-but-absent.
- All symbol-level claims (e.g. `MISProfileDBClient`, `AMFIConnection`)
  come from ObjC metadata in `__AUTH_CONST`/`__objc_methname` — these are
  *real* bytes, not reconstructed names.
- `N8Security11CodeSigning*` mangled names in `Security` are unmangled
  typeinfo strings — real, not inferred.

## 6. Incomplete-Mach-O-as-full check

- Report 05 (Phase 10) already declared the files `PARTIALLY VERIFIED` —
  not `VERIFIED`.
- Report 07 (Phase 11) uses `STRUCTURALLY VALID` and `PARTIALLY USABLE` —
  no claim of completeness.
- Report 04 explains that `__LINKEDIT` is absent (663 MB unrecoverable).
- The Phase 10 extracted files contained a segment-overlap bug — Phase 11
  report 06 documents it and provides corrected files.

## 7. Assumptions-as-facts check

Questionable statements found and corrected:

| Statement | Status | Correction |
|---|---|---|
| "AMFIPathValidator_ios is in AppleMobileFileIntegrity.framework" | CONTRADICTED — class name is in `amfid` itself; framework holds the profile engine | Updated in report 08 |
| "CoreTrust is a separate framework on iOS 27.2" | CONTRADICTED — not in B2 image array; folded into Security/AMFI | Already corrected in Phase 10; maintained |
| "libsecurity_codesigning exists separately" | CONTRADICTED — symbols inside `Security` | Maintained |
| "TrustKit is on the signature path" | CONTRADICTED — ML/policy framework, no amfid calls | Corrected in Phase 11 report 08 |
| "Phase 10 extracted dylibs are usable" | CONTRADICTED — segment-overlap bug | New report 06 with corrected files |

## 8. Error-as-vulnerability check

- No report claims an exploit, AMFI bypass, sandbox bypass, or signature
  validation vulnerability.
- P9-H4 is reported as "string located" with no claim of reachability or
  consequence — explicitly notes the surrounding strings suggest
  developer-mode handling.
- No exploit chains, no bypass techniques, no modified binaries.

## 9. Cross-check: reports vs. evidence

| Report claim | Verified by |
|---|---|
| `subCacheArray` has 79 entries | direct read at offset `0x5a4e8`, stride `0x38` |
| `.79.dyldlinkedit` empty | `ls` size=0, SHA-256=empty-file hash |
| `.symbols` empty | same |
| `LC_LOAD_DYLIB` AMFI→libmis | parsed load commands |
| `LC_LOAD_DYLIB` libmis→libCoreEntitlements | parsed load commands |
| `AMFIProfile*` API names | string extraction from `__TEXT` |
| `CodeSigning::Sec*` classes | mangled C++ names in `Security` `__TEXT` |
| `mis.db` schema | SQL strings in `libmis` `__TEXT` |
| `boot-args` string | offset `0xf2a6` in corrected AMFI `__TEXT` |
| `auxiliary signature exists: %@` | `__TEXT` string |

## 10. Verdict

Phase 11's conclusions are internally consistent and conservative:

- No claims exceed the available evidence.
- All `VERIFIED` claims are directly evidenced by parsed structures or
  disassembled code.
- All `PARTIALLY VERIFIED` claims have a specific missing artifact named.
- All `NOT VERIFIED` claims state what data would be needed.
- One CONTRADICTED finding (Phase 10 extractor bug) was found and fixed —
  the corrected files are produced and the corrupt ones marked unusable.
