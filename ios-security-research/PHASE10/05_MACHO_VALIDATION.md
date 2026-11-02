# Phase 10 Report 05 — Mach-O Validation

Method: `validate_dyld_images.py` parses each extracted dylib's
`mach_header_64`, every load command, every `LC_SEGMENT_64`, `LC_UUID`,
`LC_ID_DYLIB`, and all `LC_LOAD_DYLIB` dependencies. Results in
`dyld_image_validation.json`.

## 1. Header validation — all targets

| File | magic | cputype | filetype | ncmds | result |
|---|---|---|---|---|---|
| Security_B2.dylib | `0xfeedfacf` | arm64e | 6 (MH_DYLIB) | 41 | header VALID |
| MobileInstallation_B2.dylib | `0xfeedfacf` | arm64e | 6 | 25 | header VALID |
| libmis_B2.dylib | `0xfeedfacf` | arm64e | 6 | 35 | header VALID |
| AppleMobileFileIntegrity_B2.dylib | `0xfeedfacf` | arm64e | 6 | 25 | header VALID |
| CodesignKit_B2.dylib | `0xfeedfacf` | arm64e | 6 | 33 | header VALID |
| libDetachedCertificates_B2.dylib | `0xfeedfacf` | arm64e | 6 | 19 | header VALID |
| TrustKit_B2.dylib | `0xfeedfacf` | arm64e | 6 | 51 | header VALID |
| ProfileValidatedAppIdentity_B2.dylib | `0xfeedfacf` | arm64e | 6 | 19 | header VALID |
| LocalAuthentication_B2.dylib | `0xfeedfacf` | arm64e | 6 | 34 | header VALID |
| SecurityFoundation_B2.dylib | `0xfeedfacf` | arm64e | 6 | 20 | header VALID |
| MessageSecurity_B2.dylib | `0xfeedfacf` | arm64e | 6 | 29 | header VALID |

`dyld_image_validation.json` marks each `VERIFIED`. That flag means *the
declared load-command structure is well-formed*. It does **not** mean the file
is a complete dylib — see §4.

## 2. Segment coverage

Each file's regular segments are physically present and byte-for-byte copied
from the owning subcache:

```
Security_B2:      __TEXT __DATA_CONST __AUTH_CONST __AUTH __DATA __DATA_DIRTY __LINKEDIT*
libmis_B2:        __TEXT __DATA_CONST __AUTH_CONST __DATA __DATA_DIRTY __LINKEDIT*
AMFI_B2:          __TEXT __DATA_CONST __AUTH_CONST __DATA __DATA_DIRTY __LINKEDIT*
MobileInstallation_B2: __TEXT __DATA_CONST __AUTH_CONST __AUTH __DATA __DATA_DIRTY __LINKEDIT*
… (same pattern for the other 7)
```

`*` `__LINKEDIT` is declared with `vs=0x294d8000` but the bytes are all zero
because the backing `.79.dyldlinkedit` subcache is empty.

## 3. Load-command inventory (selected)

- `LC_UUID` — present, matches image-array UUID.
- `LC_ID_DYLIB` — present, matches install path (see report 03).
- `LC_LOAD_DYLIB`/`LC_LOAD_UPWARD_DYLIB`/`LC_LOAD_WEAK_DYLIB` — present;
  dependency lists in report 06.
- `LC_DYLD_INFO_ONLY`, `LC_FUNCTION_STARTS`, `LC_DATA_IN_CODE`,
  `LC_LINKER_OPTIMIZATION_HINT`, `LC_ATOM_INFO`, `LC_DYLIB_CODE_SIGN_DRS` —
  declared; contents in missing linkedit.
- `LC_SYMTAB` — declared on every image, e.g.:

| File | symoff | nsym |
|---|---|---|
| Security | `0x17894600` | 9,996 |
| MessageSecurity | `0x1cae8370` | 2,828 |
| LocalAuthentication | `0x1aab8590` | 1,874 |
| SecurityFoundation | `0x205d4150` | 1,457 |
| MobileInstallation | `0x1aeb2e20` | 1,104 |
| libmis | `0x1c7d37d0` | 1,028 |
| AppleMobileFileIntegrity | `0x1e37bd00` | 560 |
| TrustKit | `0x1d2170b0` | 350 |
| libDetachedCertificates | `0x219db130` | 141 |
| ProfileValidatedAppIdentity | `0x20233c70` | 77 |

All `symoff` values point into the zero-filled linkedit region — symbol tables
are **not readable**.

- `LC_CODE_SIGNATURE` — **not present** on any image. iOS dyld-cache images do
  not carry per-image code signatures; the cache is signed once as a whole.

## 4. Validation verdict

| Aspect | Status | Reason |
|---|---|---|
| Mach-O magic/CPU/type | VERIFIED | header parse succeeded |
| Segment structure | VERIFIED | all declared segments mapped and copied |
| `LC_UUID`/`LC_ID_DYLIB` | VERIFIED | consistent with image array |
| Declared dependencies | VERIFIED | `LC_LOAD_DYLIB` strings readable |
| `__LINKEDIT` contents | NOT VERIFIED | bytes are zeroed — backing file empty |
| Symbol table | NOT VERIFIED | `LC_SYMTAB` offsets unreadable |
| Export/bind tries | NOT VERIFIED | in missing linkedit |
| Code signature | NOT APPLICABLE | not a per-image load command in cache |
| Function-level disasm | PARTIALLY VERIFIED | `__TEXT` code bytes present, but relocations/binds unknown |

**Overall status per extracted image: PARTIALLY VERIFIED.**

The `VERIFIED` string in `dyld_image_validation.json` is a parser-side
declaration and has been downgraded for reporting purposes.

## 5. Implication for analysis

What can still be trusted from these files:
- ObjC class/selector names in `__AUTH_CONST`/`__DATA_CONST` sections.
- Format strings and identifier strings in `__TEXT`.
- Dependency edges from `LC_LOAD_DYLIB`.
- ARM64 code bytes for spot disassembly, treating all external references as
  unresolved.

What cannot be trusted:
- Any statement about "exported symbol X" — the export trie is absent.
- Any statement about "imported symbol Y from library Z" — bind table absent.
- Any statement about "this binary is/not signed" — no per-image signature
  exists in dyld-cache layout.
