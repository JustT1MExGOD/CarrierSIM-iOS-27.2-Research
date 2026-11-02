# Phase 18 · Отчёт 01 — Исходная база исследования

## 1. Доступные компоненты и доказательства

| Компонент | Источник | Статус | UUID / SHA |
|---|---|---|---|
| CommCenter B2 | `C:\ipsw-tools\CommCenter_B2.bin` (из main rootfs DMG `141-56668-025`) | извлечён, валиден | UUID `83978CC2-2FEC-36B0-A77C-B9A90ED9C28C`; SHA-256 `9e815d9e…b2a60` |
| CommCenter B3 | `C:\ipsw-tools\CommCenter_B3.bin` (DMG `141-56668-039`) | извлечён, валиден | UUID `747592DD-284C-37BC-AE32-0FE36E8CB3DA`; SHA-256 `9a5eeaf3…57d2` |
| **CarrierBundleUtilities.dylib B2** | dyld cache `beta2-dyld/…/.73`, fileoff `0x5243a90` | **извлечён `__text`** | UUID `387c1f49-584a-37ba-a526-0ab0f6041e02`; `__text` SHA `68c66443…` |
| CarrierBundleUtilities B3 | dyld cache в cryptex `141-56439-039` | **не извлечён** (dataless extents) | UNKNOWN |
| CoreTelephony.framework B2 | dyld cache `.73` | в cache, не извлечён | UUID `013d69da-…` |
| CommCenter Match/Overlay | внутри CommCenter.bin | код доступен | — |

## 2. Состояние dyld shared cache

- **B2**: полный набор в `beta2-dyld/System/Library/Caches/com.apple.dyld/` — 82 файла включая `.symbols`, `.dylddata`, `.dyldreadonly`, `.dyldlinkedit`. Main-cache = `dyld_shared_cache_arm64e` (802816 Б). Извлечение выполнено ранее рабочим инструментом.
- **B3**: присутствует в cryptex `141-56439-039.dmg` (82 записи каталога `/System/Library/Caches/com.apple.dyld/`), но **все файлы возвращают 0 байт** через `ApfsVolume::read_file` — dataless/deduped extents + compression type 14 (см. отчёт 02).

## 3. Ошибки/ограничения предыдущего extractor

- `probe_catbin.exe` возвращает 0 байт для всех нумерованных subcache B3 (dataless extents, j_type 13).
- `cmpfs` не поддерживал compression type 14 — добавлена поддержка (LZFSE resource-fork), но resource-fork самих файлов пуст (dataless), поэтому payload остаётся недоступным.
- Main-cache файл B3 не сжат (`compression=None`), но его data-fork тоже читается как 0 — extents не резолвятся этой версией reader'а.

## 4. Неисследованные cryptex DMG

| DMG | Путь | Статус |
|---|---|---|
| `141-56439-025.dmg` (B2 cryptex) | `beta2-decrypted/` | decrypted, dyld cache извлечён ранее |
| `141-56439-039.dmg` (B3 cryptex) | `beta3-system/…/` | decrypted, readable, но subcaches dataless |
| `141-55981-031.dmg` (B2) | `beta2-dmg/` | 16 MB, назначение UNKNOWN |
| `141-56668-039.dmg` (B3 rootfs) | `beta3-fs-decrypted/` | decrypted, CommCenter получен отсюда |

## 5. Предыдущие ограничения анализа CarrierBundleUtilities

- Phase 15–17: библиотека недоступна (dyld-only image), `matchCarrierBundle_sync` IMP не разрешён.
- **Phase 18 прорыв**: B2 `__text` извлечён и дизассемблирован — 14 187 инструкций, 234 PAC-функции, полный набор строк signature/verification/eIMSI.
