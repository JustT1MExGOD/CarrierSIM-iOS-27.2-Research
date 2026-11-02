# Phase 11 Report 03 — Subcache Integrity

Method: parse `dyld_shared_cache_arm64e` main header → locate `subCacheArray`
table → extract expected UUID/name/vmOffset for each subcache → compare to
files on disk → verify each file's self-reported UUID and mapping ranges.

## 1. Main header

```
magic        = dyld_v1  arm64e
main uuid    = 4A8F3C2F-15CF-3AE3-B702-9B66E918CDEB
cacheType    = 2  (production)
mappings     = 1  (text @ 0x180000000, size 0xc0000, prot RX)
```

The main file is small (802,816 bytes) — it carries the header, image list,
and shared metadata only. All actual image segments live in subcaches.

## 2. subCacheArray

Located at file offset `0x5a4e8` by searching for the known `.01` UUID.

- **Entry stride: 56 bytes** `{uuid[16], cacheVMOffset u64, fileExtension[32]}`
- **Entry count: 79** (`.01` through `.79.dyldlinkedit`)
- The `.atlas` and `.symbols` files are **not** subcache entries — they are
  auxiliary files living outside the subcache array.

## 3. Expected vs. on-disk

79 subcache entries expected → **78 present on disk, 1 empty**.

| # | Name | Expected UUID | vmOffset | On disk | Self UUID match |
|---|---|---|---|---|---|
| 0–77 | `.01`–`.78.dyldreadonly` | (see report 02) | `0x400000`–`0x15e47c000` | YES | YES |
| 78 | `.79.dyldlinkedit` | `79D3F635-C960-3C22-A00A-264E5975D82D` | `0x15e488000` | **EMPTY (0 bytes)** | n/a |

Every non-empty subcache's self-reported UUID (at `0x58` in its own header)
matches the expected UUID in `subCacheArray`. **No UUID mismatches.**

`.symbols` and `.atlas` exist on disk but are not in `subCacheArray` — this is
expected: `.symbols` is a companion symbol file (here empty) and `.atlas`
uses its own `AA01` format (atlas is valid, 3,110,502 bytes).

## 4. Mapping-range coverage

Per-block address ranges deduced from each file's own `mappings[]` array:

| Block | Subcaches | VM range | Status |
|---|---|---|---|
| 1 | `.01`–`.27` | `0x180400000` – `0x1f9a30000` | COMPLETE — `.27` is a 1-page sentinel |
| 2 | `.28`–`.56` | `0x200400000` – `0x279948000` | COMPLETE — `.56` is a 1-page sentinel |
| 3 | `.57`–`.78` | `0x280400000` – `0x2de488000` | PARTIAL — `.79` missing |
| 3 expected | `.79.dyldlinkedit` | `0x2de48c000` – `0x31f740000` | **MISSING** |

Verification: `.78.dyldreadonly`'s highest mapping ends at `0x2de488000`.
The subcache table assigns `.79` `vmOff=0x15e488000`, i.e. the file's own
`vmaddr` for its first mapping is `0x2de488000+0x4000 = 0x2de48c000` — this
matches exactly the `__LINKEDIT` virtual address declared in every image
(`va=0x2de48c000`, `vs=0x294d8000`).

**Declared `__LINKEDIT` total: 663 MB across all images.** No backing bytes
exist locally.

## 5. Coverage gaps and overlaps

- **Gap:** `0x2de488000`–`0x2de48c000` — a single 4 KB page between `.78` end
  and `.79` start. Likely deliberate alignment padding; not a real data hole.
- **Overlap:** none detected — all 79 vmOffsets are monotonically increasing
  and each file's internal mappings are contiguous within its own range.
- **Trailing region:** `0x31f740000`–(end) — nothing expected past `.79`;
  cache VM space ends at the linkedit boundary.

## 6. Verdict

| Criterion | Result |
|---|---|
| Expected subcaches | 79 |
| Subcaches present & non-empty | 78 |
| UUID integrity (present files) | all match |
| Mapping coverage | contiguous except missing `.79` region |
| `__LINKEDIT` region | **missing — 663 MB absent** |
| Symbol file | `.symbols` empty |
| Overall | **PARTIALLY COMPLETE** |

The set is *structurally* complete (all 79 subcache slots have expected
records) but *content-incomplete* because the file that carries the shared
`__LINKEDIT` bytes is 0 bytes at the source. The empty `.symbols` is a
secondary loss that prevents `ipsw` from operating on the cache but does not
affect image data itself.
