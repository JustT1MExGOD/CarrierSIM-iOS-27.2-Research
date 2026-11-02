# Phase 11 Report 02 — Dyld Cache Inventory

Scope: every dyld shared cache file present locally. Two copies exist —
`C:\ipsw-tools\beta2-dyld\` (primary) and
`C:\ipsw-tools\IOS_SECURITY_RESEARCH\PHASE10\cache_work\` (working copy made
in Phase 10; `.79.dyldlinkedit` and `.symbols` were not copied because they
were already 0 bytes at source).

## 1. Primary cache set — `beta2-dyld`

Location: `C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\`

Main file SHA-256: `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8` (Phase 8)
Main file UUID: `4A8F3C2F-15CF-3AE3-B702-9B66E918CDEB`
Magic: `dyld_v1  arm64e`
Expected arch: arm64e (Apple A17 Pro / iPhone 16,1)
Suspected build: iOS 27.2 Beta 2 (24B5089g)

### File list (82 entries)

| File | Size (hex) | Self UUID | State |
|---|---|---|---|
| `dyld_shared_cache_arm64e` | `0xc4000` | `4A8F3C2F-15CF-3AE3-B702-9B66E918CDEB` | VALID |
| `.01` | `0x7d74000` | `2931D1F8-5C46-3437-B2FE-9BBC8F06C1AC` | VALID |
| `.02` | `0x38000` | `D6CEB866-B80E-3E57-B0E8-944D8AAE4B12` | VALID |
| `.03` | `0x7cf4000` | `3F5CF910-8F69-3208-BD68-9FEE59E2B7B6` | VALID |
| `.04` | `0x44000` | `FC130C01-2EF4-34AC-8828-1B05675F8DAB` | VALID |
| `.05` | `0x7d64000` | `66F586C5-8510-35C4-ADED-263B81EFA2C6` | VALID |
| `.06` | `0x34000` | `11E47A9E-AF9B-3D6E-BE18-62384733DAAF` | VALID |
| `.07` | `0x7ce4000` | `D226942F-50DD-37C8-B1D2-0FF71E3E62C5` | VALID |
| `.08` | `0x40000` | `688A9490-5EB4-363D-9EFB-70EF244F81EF` | VALID |
| `.09` | `0x7d14000` | `662DAFC6-18B6-333E-918D-C89EA86E3A2A` | VALID |
| `.10` | `0x34000` | `59BB0E3E-CF93-3169-95BC-49160B2ECA7E` | VALID |
| `.11` | `0x7d5c000` | `88C0A593-F199-3FD9-9FAF-5FB810C1A8C7` | VALID |
| `.12` | `0x3c000` | `AAD091E6-8E8C-3863-AB7D-EFC3DF384442` | VALID |
| `.13` | `0x7d84000` | `8164EFD9-246B-3782-979B-F9688ECE6A5D` | VALID |
| `.14` | `0x44000` | `57B13C88-5063-3D8D-8D50-986B8735865A` | VALID |
| `.15` | `0x7d18000` | `12D1B675-8C85-3213-851C-01260D511546` | VALID |
| `.16` | `0x34000` | `11320482-2232-3EAA-A6E4-283C5A02B3C5` | VALID |
| `.17` | `0x7d84000` | `FF367A8B-37E1-312C-AED1-EDB764EB2A02` | VALID |
| `.18` | `0x4c000` | `9B13CCF9-DAF7-3839-B992-785DC00F61C1` | VALID |
| `.19` | `0x7d38000` | `7DA10EAE-B7FD-32DC-A1EF-A256C0D37999` | VALID |
| `.20` | `0x54000` | `D2567250-9846-326A-B223-F8A77CBCB1B0` | VALID |
| `.21` | `0x7d18000` | `3E4000A5-6B43-3C48-915F-7B02366F849C` | VALID |
| `.22` | `0x4c000` | `91B46D4D-929D-33E8-95A2-A621B242E147` | VALID |
| `.23` | `0x7ccc000` | `0CC26901-6F78-38C3-8B55-BD12C814644C` | VALID |
| `.24` | `0x4c000` | `3F4B2342-0861-3B80-A892-A14077DA278C` | VALID |
| `.25.dylddata` | `0xd9cc000` | `4B3B8310-0675-333A-9B2E-F029195F8DB6` | VALID |
| `.26.dyldreadonly` | `0xbb34000` | `12EAD6FD-0A6A-3A20-AD3D-FE4A998DC7AB` | VALID |
| `.27` | `0x8000` | `DA212564-9875-3BEC-8875-45F1A3B1A77B` | VALID |
| `.28` | `0x7ce4000` | `DAFB0494-D51F-3996-BA24-A95A208164E5` | VALID |
| `.29` | `0x50000` | `A16C7576-25F9-3255-880E-C74C04D1CDD3` | VALID |
| `.30` | `0x7cf8000` | `EA431865-5E75-3BBB-98CE-16D6F9BFF1E4` | VALID |
| `.31` | `0x5c000` | `12CA92B0-C9A0-3A38-A09C-8BCC55636B39` | VALID |
| `.32` | `0x7cc4000` | `B6E32014-2520-3165-A7E2-5CB8DA2756F1` | VALID |
| `.33` | `0x64000` | `C964F717-24FB-33B8-9AF2-41CCCB303A66` | VALID |
| `.34` | `0x7c84000` | `8268DED7-BE48-3B34-A62B-D7D96D99E18F` | VALID |
| `.35` | `0x28000` | `36265950-462D-34D5-A04F-DF36C5B5C443` | VALID |
| `.36` | `0x7d64000` | `25186808-7CF2-3C0F-AA97-93484AACD7A2` | VALID |
| `.37` | `0x68000` | `ADCC1FC9-871D-3BAF-91FD-A82C72A60F9A` | VALID |
| `.38` | `0x7cfc000` | `655446BF-410C-399A-B1D4-AEF529CE59EE` | VALID |
| `.39` | `0x70000` | `5CA3B0B4-E537-3AC3-9879-C1941B948866` | VALID |
| `.40` | `0x7d18000` | `4E0F36DB-DE3D-3F90-AF0A-611079CBF793` | VALID |
| `.41` | `0x60000` | `851AA976-E98C-30B0-8063-2345E3059A01` | VALID |
| `.42` | `0x7d18000` | `77B512D9-CC7F-335C-A325-52BB0638921D` | VALID |
| `.43` | `0x88000` | `11A2855D-E691-3478-A1E2-3316E741AE11` | VALID |
| `.44` | `0x7cfc000` | `025512B2-064A-303D-8D24-1A9114AAE1DB` | VALID |
| `.45` | `0x3c000` | `4D148908-7381-347B-B012-FD2AB58A336B` | VALID |
| `.46` | `0x7cc4000` | `372D24AC-B054-3E01-BCBA-1607DBF9AAEB` | VALID |
| `.47` | `0x48000` | `B5361E63-F1A3-3345-86C0-5B6D358701D0` | VALID |
| `.48` | `0x7cbc000` | `7BE12444-013F-3CE8-9E23-D66CA06FAEFE` | VALID |
| `.49` | `0x64000` | `3F89CD7E-942A-3311-A9E2-B1B002A653C5` | VALID |
| `.50` | `0x7d28000` | `DFF406C1-DD75-3680-8C03-7801560F682A` | VALID |
| `.51` | `0x50000` | `C4C1C1E4-13AF-3FAB-8913-BA246DE4B590` | VALID |
| `.52` | `0x7d10000` | `11FC491F-EC81-3F8E-A44D-5A10E7DD0BD8` | VALID |
| `.53` | `0x54000` | `C740F3C4-7CDF-3BE2-8F3A-1D01205528CF` | VALID |
| `.54.dylddata` | `0xd514000` | `F975B83E-2B1D-3B27-8EB1-B1067B8DC598` | VALID |
| `.55.dyldreadonly` | `0x384000` | `B23E7ED9-1E34-3A4E-AD5A-0F837E3CDC93` | VALID |
| `.56` | `0x8000` | `B2F3E634-CBAC-390D-A9E9-1A31588F0B70` | VALID |
| `.57` | `0x7c78000` | `FA638FF1-A8EF-35CC-B755-B9A273C1DD9B` | VALID |
| `.58` | `0x48000` | `3BB4458B-874D-34B4-8277-FB3C1527E477` | VALID |
| `.59` | `0x7d14000` | `F6855C0B-D6F3-3FED-83C0-C43C9402A3E3` | VALID |
| `.60` | `0x50000` | `16874E5E-8247-3BBF-B8D7-0FD04508F55F` | VALID |
| `.61` | `0x7ccc000` | `6CDACFB7-16E2-3447-9CFF-F273FDD9DDF1` | VALID |
| `.62` | `0x34000` | `BAA3F3A4-FA6C-3230-A470-97078AFD4C3A` | VALID |
| `.63` | `0x7d08000` | `408D3BF7-D423-3376-AB7D-CBB749F7D232` | VALID |
| `.64` | `0x48000` | `D8DFC7F4-CF57-33D0-8D7F-C7BF02DAD287` | VALID |
| `.65` | `0x7c9c000` | `EB306F26-379D-3BCD-96DA-2424CBE43513` | VALID |
| `.66` | `0x30000` | `0F755FB8-E3EC-3140-BB8C-2F976F15E5CA` | VALID |
| `.67` | `0x7cc0000` | `A0217346-CA0C-31E3-9ADA-17B2EA42DBF6` | VALID |
| `.68` | `0x4c000` | `3BA201B8-4475-32FA-AF4A-BB99C3BDA2C1` | VALID |
| `.69` | `0x7d08000` | `EEF3B970-CFC8-3BA1-8DDD-18D9881A2020` | VALID |
| `.70` | `0x50000` | `943A394A-4DD3-3C8D-A805-ACAB6AB2D621` | VALID |
| `.71` | `0x7cdc000` | `290CDAC4-5FF2-3F20-A9D3-E6D8D1FEBF02` | VALID |
| `.72` | `0x40000` | `B3357143-1194-3897-B9DC-1F0A282D4434` | VALID |
| `.73` | `0x7d08000` | `18D315B6-AEF7-328A-BD1C-82230F8CB161` | VALID |
| `.74` | `0x38000` | `A810EFA9-DB93-3879-AEB4-096F0B5312CF` | VALID |
| `.75` | `0x7c5c000` | `9E2A7160-F290-3D7F-BE5E-17D157F88F5A` | VALID |
| `.76` | `0x4c000` | `3C80648F-6731-33F6-BE5B-5B12DE1CD710` | VALID |
| `.77.dylddata` | `0xa46c000` | `EEF10167-9A3C-3DFD-9CCC-BA07EC9E3C9E` | VALID |
| `.78.dyldreadonly` | `0x10000` | `27C7501D-FE5D-3991-BB42-95ECE8C9B76A` | VALID |
| `.79.dyldlinkedit` | **`0x0`** | n/a — empty | **EMPTY** |
| `.atlas` | `0x2f7666` | not-dyld (AA01 magic) | VALID (atlas format) |
| `.symbols` | **`0x0`** | n/a — empty | **EMPTY** |

## 2. Subcache layout pattern

The set is organized as **three blocks** of ~26 files each:

| Block | Subcaches | Data | Readonly | Terminal |
|---|---|---|---|---|
| 1 | `.01`–`.24` | `.25.dylddata` | `.26.dyldreadonly` | `.27` (8 KB stub) |
| 2 | `.28`–`.53` | `.54.dylddata` | `.55.dyldreadonly` | `.56` (8 KB stub) |
| 3 | `.57`–`.76` | `.77.dylddata` | `.78.dyldreadonly` | `.79.dyldlinkedit` (EMPTY) |

Each text subcache (~130 MB `0x7c–0x7d` MB) holds `__TEXT`; the paired small
subcache (0x30–0x88 KB) holds data segments; `.dylddata` holds shared writable
data; `.dyldreadonly` holds shared read-only/ObjC metadata.

Block 3's `.dyldreadonly` is unusually small (0x10000) because most of its
content is meant to live in `.79.dyldlinkedit` — which is missing.

## 3. Cache-level status

| Aspect | Result |
|---|---|
| Total files | 82 |
| Valid dyld files | 80 |
| Empty files | 2 (`.79.dyldlinkedit`, `.symbols`) |
| Valid magic | 79 (`dyld_v1  arm64e`) + 1 atlas (`AA01`) |
| Main cache integrity | header parses, mappings consistent |
| Subcache UUID uniqueness | all 78 dyld subcaches have distinct uuids |
| Completeness | **INCOMPLETE** — missing `.79.dyldlinkedit` contents |

## 4. Second copy (`PHASE10/cache_work`)

- Working copy made in Phase 10 from the same source.
- `.79.dyldlinkedit` and `.symbols` are **absent** in `cache_work` — they were
  already 0 bytes in `beta2-dyld` and were not carried over.
- All non-empty subcache files match `beta2-dyld` byte-for-byte.
- Therefore `cache_work` is **not** an independent copy — it inherits the same
  missing-linkedit defect.

## 5. Other local sources

- **Beta 3 system DMG** `C:\ipsw-tools\beta3-system\24B5099f__iPhone16,1\141-56439-039.dmg`
  (6.2 GB) — contains a complete iOS filesystem including its own dyld cache,
  but has not been mounted/extracted in Phase 10. Potential source for B3
  trust binaries.
- **Beta 2 system DMG** `C:\ipsw-tools\beta2-dmg\24B5089g__iPhone16,1\141-55981-031.dmg`
  (16 MB — too small to be the full filesystem; likely the developer DMG or
  kernelcache partition).
- **No RC dyld cache** exists locally.

## 6. Verdict

The local Beta 2 dyld cache set is **PARTIALLY COMPLETE** — 80 of 82 files
are intact, but the two files that carry symbol/linkedit information are
empty. This is not an extraction error; the files themselves are 0 bytes at
the source and were propagated as such into `cache_work`.
