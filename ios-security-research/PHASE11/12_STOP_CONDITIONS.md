# Phase 11 Report 12 — Stop Conditions

## 1. Stop conditions reached

Phase 11 stops further extraction attempts because all of the following are
now established:

1. **The Beta 2 subcache table is complete as a table:** 79 entries (`.01`
   through `.79.dyldlinkedit`).
2. **78 expected subcache files are present and UUID-correct.**
3. **The only missing content is the declared `.79.dyldlinkedit` body:**
   expected UUID `79D3F635-C960-3C22-A00A-264E5975D82D`, 0 bytes on disk.
4. **The `.symbols` companion file is also 0 bytes** (SHA-256 is the canonical
   empty-file hash).
5. **No alternate B2 cache exists locally.** `PHASE10\cache_work` is a
   derivative copy, not an independent source; its `.79`/`.symbols` are
   absent/empty as well.
6. **No other local file covers the missing VM range**
   `0x2de48c000–0x31f740000` (~663 MB).
7. **`ipsw` 3.1.740 cannot bypass the missing-file condition** — `info`/
   `image`/`extract` abort with EOF; a placeholder is not acceptable.
8. **The Phase 10 segment extractor had a layout bug**, but Phase 11 corrected
   it. The corrected extraction produces structurally valid, compact Mach-O
   files and no further extraction improvement is possible without `.79`.
9. **No symbols may be fabricated.** Synthesising `.symbols`, export tries,
   or bind data would create evidence not present in the source.

## 2. Exact missing artifacts needed to continue

### Required for full B2 Mach-O recovery

- `dyld_shared_cache_arm64e.79.dyldlinkedit`
  - Expected UUID: `79D3F635-C960-3C22-A00A-264E5975D82D`
  - Expected virtual start: `0x2de48c000`
  - Required VM/file coverage: at least `0x294d8000` bytes (663 MB)
- `dyld_shared_cache_arm64e.symbols`
  - Expected format: dyld local-symbol companion
  - Required for `ipsw dyld info`, `a2s`, `symaddr`, symbol-aware extraction

### Required to settle call graph / hypothesis questions

- Original complete Beta 2 IPSW or a re-extracted Beta 2 filesystem that
  preserves the two files above.
- `amfid` B3 disassembly around the full `sub_10000b194` body and the
  `AMFIPathValidator_ios validateWithError:` implementation.
- A client binary for `verify_code_directory` reply consumption (e.g.
  `misagent`/online-auth/XPC client).
- `launchd` plist + sandbox profile + entitlement metadata for
  `com.apple.MobileFileIntegrity` reachability.
- Complete Beta 3 / RC dyld caches for version comparison.

## 3. What will not help

- Re-running the Phase 10 extractor unchanged — same missing `.79`.
- Re-running the corrected extractor — produces the same correct partial
  files; no linkedit data can appear.
- Copying `.79` from Beta 3 into Beta 2 — wrong build/UUID and invalid data.
- Filling `.79` with zeros/placeholders — creates false evidence.
- Installing LIEF/macholib — parsers cannot reconstruct absent bytes.
- Active device requests or IPC — outside scope and unnecessary.

## 4. Final stop status

- **No infinite search/extraction loop.**
- **No further attempts against the current Beta 2 cache.**
- **Corrected partial extraction retained** under
  `PHASE11\extracted_v2\`.
- **Corrupt Phase 10 extraction explicitly superseded** by report 06.

Phase 11 is complete for the available local data. A Phase 12 should begin
only after the exact missing subcache files or a complete version-matched
source image is obtained.
