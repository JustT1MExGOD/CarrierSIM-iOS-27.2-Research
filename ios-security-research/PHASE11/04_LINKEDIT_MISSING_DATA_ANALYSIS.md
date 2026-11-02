# Phase 11 Report 04 — Linkedit Missing Data Analysis

Subject: `.79.dyldlinkedit` and `.symbols`, both 0 bytes in the local Beta 2
dyld cache.

## 1. Are these files supposed to contain data?

### `.79.dyldlinkedit`

YES — expected to be the largest single subcache file.

Evidence from the cache itself:
- `subCacheArray` entry 78 declares `.79.dyldlinkedit` with
  `cacheVMOffset = 0x15e488000` and UUID `79D3F635-C960-3C22-A00A-264E5975D82D`.
- Every dyld image declares `__LINKEDIT va=0x2de48c000, vs=0x294d8000` —
  shared linkedit region spanning **663 MB**.
- `.78.dyldreadonly`'s last mapping ends at `0x2de488000`, exactly one page
  before the linkedit base — confirming `.79` is meant to start there.
- In every Apple dyld-cache release since iOS 15, the `.dyldlinkedit`
  subcache contains the merged `__LINKEDIT` of all images (symbol tables,
  string pools, export tries, bind/rebase opcodes, function-starts tables,
  data-in-code tables, ObjC metadata tails).

A 0-byte `.dyldlinkedit` is **physically impossible** for a functioning dyld
cache — the OS cannot resolve a single bind or export without it.

### `.symbols`

YES — expected to contain a compressed `dyld_cache_local_symbols_info` blob
(mapping image UUIDs → nlist symbol tables).

- `ipsw dyld info` aborts with `EOF` because `.symbols` is empty — this is a
  secondary failure caused by the tool needing the symbol file before
  walking images.
- Without it, `a2s`/`symaddr`/`extract --objc` cannot work either.

## 2. Where did these files come from?

Provenance chain:
1. Downloaded IPSW `24B5089g__iPhone16,1` (iOS 27.2 Beta 2, iPhone 16,1).
2. `ipsw extract` / `ipsw mount` produced the decrypted DMG
   `beta2-dyld` directory tree.
3. Phase 10 created `cache_work` copy — `.79.dyldlinkedit` and `.symbols`
   were already 0 bytes and were **not** carried over (or were carried as
   empty files and deleted — same outcome).

The empty files are **already empty in `beta2-dyld`** — this is not a Phase
10 corruption. SHA-256 of both files is `e3b0c44…b855` (the canonical
empty-file hash).

## 3. Why are they empty?

Possible causes, ranked by likelihood:

| Cause | Likelihood | Evidence |
|---|---|---|
| Upstream IPSW shipped them empty (Apple-side) | HIGH | iOS cryptex/restore bundles sometimes ship `.dyldlinkedit` separately or omit it entirely when the cache is meant to be recompressed |
| Extraction tool failed silently | MEDIUM | `ipsw extract` version 3.1.740 may have a bug with the new `.dylddata`/`.dyldreadonly`/`.dyldlinkedit` triple-subcache scheme in iOS 27.2 |
| File was present but zeroed during transfer | LOW | all other 80 files are intact — selective zeroing is implausible |
| Different layout: linkedit embedded in `.dylddata` or `.dyldreadonly` | LOW | `.78.dyldreadonly` ends at `0x2de488000` and `.77.dylddata` ends at `0x2de474000` — neither reaches `0x2de48c000` |

The most consistent explanation: **the extraction pipeline produced a
partially-truncated cache**. The `.79.dyldlinkedit` slot exists in
`subCacheArray` (proving the format expects it) but the file body was never
written.

## 4. Could `__LINKEDIT` data live elsewhere?

Checked every candidate:

| File | Ends at | Could cover `0x2de48c000`? |
|---|---|---|
| `.77.dylddata` | `0x2de474000` | no — 24 KB short |
| `.78.dyldreadonly` | `0x2de488000` | no — one page short |
| `.atlas` | proprietary AA01 format, not VM-mapped | no |
| `.symbols` | empty | no (and wrong format anyway) |

No local file covers the `0x2de48c000`–`0x31f740000` range.

## 5. Was a prior extraction error possible?

Yes — but not from the Phase 10 pipeline:

- Phase 10 `extract_dyld_segments.py` did not fail; it correctly identified
  that `.79` was empty and reported `MISSING __LINKEDIT` for every target.
- The truncation happened **upstream**, when `ipsw` (or whatever tool
  generated `beta2-dyld`) wrote the files. Re-running that upstream step on
  the original IPSW/DMG could produce a complete `.79.dyldlinkedit` — but
  the original IPSW file is **not** present locally (only the extracted
  `beta2-dyld` tree and the encrypted/decrypted DMG).

## 6. Alternative copies / metadata layout

- **`beta2-dyld` ↔ `cache_work`**: identical empties; not independent.
- **Beta 3 system DMG** `141-56439-039.dmg` (6.2 GB): contains a complete
  iOS filesystem. If its dyld cache is intact, it would have its own
  `.dyldlinkedit` — but for B3, not B2.
- **No B2 IPSW file** is present locally — cannot re-extract.

## 7. Are any `__LINKEDIT` bytes recoverable?

Partially — from inside the extracted dylibs themselves:

- ObjC metadata (`__objc_*` sections) is in `__AUTH_CONST`/`__DATA_CONST`,
  not `__LINKEDIT` — already recovered.
- Selector names (`__objc_methname`) are in `__TEXT` or `__AUTH_CONST` —
  already recovered.
- **Lost**: symbol table entries, export trie, bind/rebase opcodes,
  function-starts index, data-in-code table, code-signature blob.

A heuristic *reconstruction* (re-parsing ObjC metadata to re-derive
selector→IMP bindings) is **technically possible** but produces inferred
symbols, not original ones — and would violate the "do not fabricate
symbols" constraint.

## 8. Conclusion

`.79.dyldlinkedit` and `.symbols` are empty **at the source copy**. The
declared `__LINKEDIT` region (663 MB) exists in the cache's VM map and in
`subCacheArray` but has no backing bytes locally. No other local file covers
that range. Recovery requires either:

1. Re-extracting the original B2 IPSW (not present locally), or
2. Using a different tool/copy that preserved `.dyldlinkedit`, or
3. Accepting the loss and relying on `__TEXT`/`__AUTH_CONST` analysis only.

Status: **UNRECOVERABLE from local data alone.**
