# Phase 10 Report 04 — Dyld Extraction Log

Objective: extract only the trust-relevant dylibs from the Beta 2 split dyld
shared cache without modifying the cache files.

## 1. Extraction path

Tooling used:

1. `ipsw.exe dyld info` and `ipsw.exe dyld image` — both fail with `EOF`
   because `dyld_shared_cache_arm64e.79.dyldlinkedit` and `.symbols` are
   empty. The tool refuses to proceed.
2. Placeholder-file workaround — a dummy linkedit file with a patched UUID was
   tried in a copied cache. `ipsw` accepted the UUID patch but then aborted
   on the still-empty `.symbols` file. Abandoned.
3. Naive contiguous range copy — produced an incomplete `libmis_B2.dylib`.
   Rejected: split-cache file offsets are not globally contiguous, so a raw
   range read stitches unrelated bytes.
4. `extract_dyld_segments.py` (final) — for each target image, walks
   `LC_SEGMENT_64`, looks up which subcache owns each `vmaddr` range via the
   cache mapping table, seeks to `fileoff` in that subcache, and writes each
   segment into a reconstructed file at the correct offset.

Only method 4 produced structurally valid Mach-O files.

## 2. Per-image extraction results

All files written to `PHASE10\extracted\dyld_B2\`.

| File | Size (bytes) | Segments | __LINKEDIT bytes recovered |
|---|---|---|---|
| `AppleMobileFileIntegrity_B2.dylib` | 118,583,296 | 6 | 0 (zero-filled padding) |
| `CodesignKit_B2.dylib` | 58,671,104 | 6 | 0 |
| `LocalAuthentication_B2.dylib` | 64,331,776 | 7 | 0 |
| `MessageSecurity_B2.dylib` | 99,471,360 | 6 | 0 |
| `MobileInstallation_B2.dylib` | 88,391,680 | 7 | 0 |
| `ProfileValidatedAppIdentity_B2.dylib` | 1,658,880 | 6 | 0 |
| `SecurityFoundation_B2.dylib` | 110,411,776 | 6 | 0 |
| `Security_B2.dylib` | 113,192,960 | 7 | 0 |
| `TrustKit_B2.dylib` | 2,969,600 | 7 | 0 |
| `libDetachedCertificates_B2.dylib` | 26,787,840 | 6 | 0 |
| `libmis_B2.dylib` | 30,752,768 | 6 | 0 |

Every image declares `__LINKEDIT va=0x2de48c000 vs=0x294d8000 fo=0x4000
fs=0x294d8000`. The backing subcache is empty, so the written files pad that
region with zeros. Verified: last 4 KB of every extracted file is all `0x00`.

## 3. What is actually inside each file

Recovered and readable:
- Full `mach_header_64` (magic `0xfeedfacf`, `MH_DYLIB`, arm64e).
- All `LC_SEGMENT_64` commands with original `vmaddr`/`fileoff`.
- `LC_UUID`, `LC_ID_DYLIB`, `LC_LOAD_DYLIB`/`LC_LOAD_WEAK_DYLIB`,
  `LC_BUILD_VERSION`, `LC_DYLD_INFO_ONLY`, `LC_SYMTAB`, `LC_DYSYMTAB`,
  `LC_FUNCTION_STARTS`, `LC_DATA_IN_CODE` — declared, contents not present.
- `__TEXT` (code, ObjC method names, format strings).
- `__DATA_CONST`, `__AUTH_CONST`, `__AUTH`, `__DATA`, `__DATA_DIRTY`
  (cfstrings, ObjC class/selector tables, got).

Not recoverable from this cache copy:
- Symbol table entries (`LC_SYMTAB` offsets point into the missing linkedit).
- Export trie / bind / rebase opcodes (in linkedit).
- `LC_CODE_SIGNATURE` blob — not declared as a load command in these
  dyld-cache images (cache images are signed once at the cache level, not per
  image).
- Function-starts index and data-in-code table contents.

## 4. Failure log

```
ipsw.exe dyld info dyld_shared_cache_arm64e
    -> EOF  (empty .79.dyldlinkedit)

ipsw.exe dyld image dyld_shared_cache_arm64e <idx>
    -> EOF  (empty .symbols)

extract_dyld_segments.py <image>
    -> all regular segments OK
    -> MISSING __LINKEDIT vm=0x2de48c000 size=0x294d8000  (every target)
```

## 5. Conclusion

The extraction is **segment-complete but linkedit-absent**. The files are
genuine Mach-O dylibs with real headers and real code/data pages, suitable for
static `__TEXT` and ObjC-metadata analysis. They are **not** complete dylibs —
no symbol, export, bind, or embedded-code-signature analysis can be performed
on them, and they must not be treated as loadable.
