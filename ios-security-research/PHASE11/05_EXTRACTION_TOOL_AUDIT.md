# Phase 11 Report 05 — Extraction Tool Audit

Scope: tools installed locally that can process iOS 27.2 dyld shared caches.

## 1. `ipsw` — primary dyld tool

| Field | Value |
|---|---|
| Name | `ipsw.exe` |
| Version | 3.1.740 (commit `6361083e1fe6e800eb1e7a0cf436e3c8178f4347`) |
| Source | blacktop/ipsw (Go) — present at `C:\ipsw-tools\ipsw.exe` |
| Format support | `dyld_v1 arm64e`, split subcache layout including `.dylddata`/`.dyldreadonly`/`.dyldlinkedit` |
| Dyld commands | `info`, `image`, `extract`, `macho`, `disass`, `objc`, `symaddr`, `stubs`, `tbd`, `imports`, `search`, `xref`, `slide`, `patches`, `a2s`, `a2o`, `o2a`, `str`, `swift`, `webkit`, `ida`, `prewarm` |
| Mach-O extraction | YES (`dyld extract`) |
| `__LINKEDIT` recovery | NO — the tool itself cannot conjure data from an empty file; it aborts with `EOF` when `.symbols` or `.79.dyldlinkedit` are empty |
| Verdict | **USABLE for intact caches; BLOCKED on this one** because the required subcache is empty |

Observed behaviour:

```
ipsw dyld info    → EOF  (fails on .symbols)
ipsw dyld image   → EOF  (same)
ipsw dyld extract → untested in Phase 11 — expected to fail the same way
```

`--slide`, `--stubs`, `--objc` flags exist but are unreachable past the
EOF gate.

## 2. Python `capstone` 5.0.7

| Field | Value |
|---|---|
| Name | `capstone` |
| Version | 5.0.7 |
| Role | ARM64 disassembler — reads raw bytes, not a dyld tool |
| Mach-O extraction | NO — disassembles raw instruction streams only |
| `__LINKEDIT` recovery | NO |
| Verdict | **USABLE for `__TEXT` analysis of extracted dylibs** — can disassemble code bytes already recovered |

Use case in Phase 11: spot-disassembly of `__TEXT` regions for ObjC selector
xref analysis (boot-args string xref for P9-H4).

## 3. `macholib`

Not installed (`ImportError`). Would help parse Mach-O load commands but
cannot recover missing segments.

## 4. `LIEF`

Not installed. Could parse Mach-O and re-emit dylibs; cannot recover missing
`__LINKEDIT`.

## 5. `ipsw` manpages

`/c/ipsw-tools/manpages/ipsw-dyld-*.1.gz` — documentation for all subcommands,
no additional binaries.

## 6. `dpp-source` (Device Path Parser?)

Present at `C:\ipsw-tools\dpp-source` — Rust project for parsing Apple
provisioning/`.aea` archives, not a dyld tool.

## 7. Scripts written during this research

| Script | Purpose | Capability |
|---|---|---|
| `extract_dyld_segments.py` (Phase 10) | Segment-aware per-image extractor | works correctly; faithfully reproduces the missing `__LINKEDIT` as zeroes |
| `validate_dyld_images.py` (Phase 10) | Mach-O header/load-command validator | works; result must be read as PARTIAL |

## 8. Capability summary

| Tool | Can read this cache | Can recover `__LINKEDIT` | Can disassemble `__TEXT` |
|---|---|---|---|
| `ipsw` 3.1.740 | NO — aborts on `.symbols` EOF | NO | (unreachable) |
| `extract_dyld_segments.py` | YES (manual walk) | NO — data absent | N/A |
| `capstone` 5.0.7 | (reads extracted files) | N/A | YES |
| `macholib` / `LIEF` | not installed | NO | partial |

## 9. Tool gap

A tool that would help — one that walks `subCacheArray` + per-image
`LC_SEGMENT_64` + `LC_DYLD_INFO_ONLY` records directly from the *present*
subcache files and tolerates the missing `.79`/`symbols` — does not exist in
the local toolchain. `extract_dyld_segments.py` already does the first two;
the third is impossible without the data.

No additional tools were installed. No downloads were made.
