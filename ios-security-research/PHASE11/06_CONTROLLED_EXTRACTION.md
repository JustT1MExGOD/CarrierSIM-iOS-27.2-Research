# Phase 11 Report 06 — Controlled Extraction (revised)

The Phase 10 extractor had a **layout bug** that produced unusable Mach-O
files. Phase 11 diagnoses the bug, fixes it, and re-extracts. This is the
"specific correctable cause" required by the Phase 11 plan.

## 1. Bug in Phase 10 `extract_dyld_segments.py`

```python
out[fileoff:fileoff + len(data)] = data
```

`fileoff` in `LC_SEGMENT_64` inside a dyld-cache image is a **cache-global
offset within the whole mapped VM space** — not a local offset in a standalone
dylib. Writing segments at their declared `fileoff` causes catastrophic
overlap:

- `__LINKEDIT` declared `fileoff=0x4000`, `filesize=0x294d8000` (663 MB)
- `__TEXT` declared `fileoff=0xc11000`, `filesize=0xfb34` (64 KB)

Writing `__LINKEDIT` at offset `0x4000` then `__TEXT` at `0xc11000` produces a
file where `__TEXT` is sandwiched inside the linkedit region — the "extracted"
files from Phase 10 were 100+ MB of overlaid garbage. They are unusable.

## 2. Correct extractor (`extract_flat.py`, Phase 11)

Fix:

1. Parse `LC_SEGMENT_64` commands as before.
2. Determine which segments have backing bytes (`.79.dyldlinkedit` is empty →
   `__LINKEDIT` absent).
3. Allocate a compact output: header+cmds at `0`, segments packed sequentially
   starting at the next page boundary.
4. **Rewrite** each segment's `fileoff` in the output header to point at the
   new location.
5. **Rewrite** each embedded `section_64.offset` field by the same delta.
6. Leave `__LINKEDIT` `fileoff=0`/`filesize=0` — declared but absent.

## 3. Per-image results (corrected)

| File | Size | `__TEXT` | `__DATA_CONST` | `__AUTH_CONST` | `__AUTH` | `__DATA` | `__DATA_DIRTY` | `__LINKEDIT` |
|---|---|---|---|---|---|---|---|---|
| `Security_B2.dylib` | 2.28 MB | ✓ 1.96 MB | ✓ | ✓ | ✓ | ✓ | ✓ | ABSENT |
| `MobileInstallation_B2.dylib` | 254 KB | ✓ 205 KB | ✓ | ✓ | ✓ | ✓ | ✓ | ABSENT |
| `libmis_B2.dylib` | 463 KB | ✓ 392 KB | ✓ | ✓ | — | ✓ | ✓ | ABSENT |
| `AppleMobileFileIntegrity_B2.dylib` | 90 KB | ✓ 64 KB | ✓ | ✓ | — | ✓ | ✓ | ABSENT |
| `CodesignKit_B2.dylib` | 74 KB | ✓ 44 KB | ✓ | ✓ | ✓ | ✓ | — | ABSENT |
| `libDetachedCertificates_B2.dylib` | 57 KB | ✓ 35 KB | ✓ | ✓ | ✓ | ✓ | — | ABSENT |
| `TrustKit_B2.dylib` | 639 KB | ✓ 515 KB | ✓ | ✓ | ✓ | ✓ | ✓ | ABSENT |
| `ProfileValidatedAppIdentity_B2.dylib` | 29 KB | ✓ 7.8 KB | ✓ | ✓ | ✓ | ✓ | — | ABSENT |
| `LocalAuthentication_B2.dylib` | 356 KB | ✓ 260 KB | ✓ | ✓ | ✓ | ✓ | ✓ | ABSENT |
| `SecurityFoundation_B2.dylib` | 172 KB | ✓ 100 KB | ✓ | ✓ | — | ✓ | ✓ | ABSENT |
| `MessageSecurity_B2.dylib` | 475 KB | ✓ 367 KB | ✓ | ✓ | — | ✓ | ✓ | ABSENT |

Every present segment was successfully copied from its owning subcache.
`__LINKEDIT` is `MISSING` on all — `.79.dyldlinkedit` is 0 bytes at source.

## 4. Sanity checks on corrected files

- `MH_MAGIC_64` `0xfeedfacf` at offset `0` — VALID.
- `ncmds`/`sizeofcmds` readable — VALID.
- First `__TEXT` instruction at `AppleMobileFileIntegrity_B2.dylib`:
  ```
  0x259011fd8: b #0x259011fdc
  0x259011fdc: pacibsp
  0x259011fe0: sub sp, sp, #0x20
  0x259011fe4: stp x29, x30, [sp, #0x10]
  0x259011fe8: add x29, sp, #0x10
  ...
  ```
  Real arm64e code — VALID.
- AMFI error strings correctly localised inside `__TEXT` (see report 03).
- ObjC metadata sections (`__objc_classname`, `__objc_methname`, `__objc_selrefs`)
  present in `__AUTH_CONST`/`__DATA_CONST` and resolvable.

## 5. What still fails

- `ipsw dyld info / image / extract` — still EOF because `.symbols` is empty.
- `LC_SYMTAB`/`LC_DYLD_INFO_ONLY`/`LC_FUNCTION_STARTS`/`LC_DATA_IN_CODE`/
  `LC_CODE_SIGNATURE` — declared in headers but content is in the absent
  `__LINKEDIT` region; cannot be recovered.
- Cross-image `BL` targets — call instructions go through stub islands whose
  target pointers live in `__AUTH_CONST`; the slot values exist but the
  symbols attached to them require bind info from linkedit.

## 6. Files produced

`C:\ipsw-tools\IOS_SECURITY_RESEARCH\PHASE11\extracted_v2\` — 11 correctly
laid-out Mach-O dylibs, all `STRUCTURALLY VALID` and `PARTIALLY USABLE` for
analysis. The earlier `PHASE10\extracted\dyld_B2\` files are superseded and
should not be used (they contain segment overlap corruption).
