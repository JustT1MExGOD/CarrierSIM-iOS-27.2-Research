# Phase 18 · Отчёт 02 — Анализ cryptex DMG 141-56439

## 1. Идентификация

| Параметр | B2 | B3 |
|---|---|---|
| Файл | `beta2-decrypted/141-56439-025.dmg` | `beta3-system/24B5099f__iPhone16,1/141-56439-039.dmg` |
| Размер | 6 188 695 552 Б | 6 192 889 856 Б (`.dmg`) + `.aea` |
| Тип | System Cryptex (dyld cache + системные фреймворки) | System Cryptex |
| Файловая система | APFS | APFS |
| Шифрование | decrypted (`.dmg`, не `.aea`) | decrypted `.dmg` доступен |

## 2. Читаемость на Windows

- **B2**: том открывается `apfs::ApfsVolume::open`, каталоги читаются, dyld cache **уже извлечён** (лежит в `beta2-dyld/`).
- **B3**: том открывается, `list_directory` работает (82 записи dyld-каталога). Однако `read_file` для каждого нумерованного subcache возвращает **0 байт**.

## 3. Содержимое (B3, `/System/Library/Caches/com.apple.dyld/`)

82 файла: `dyld_shared_cache_arm64e` (main), `.01`–`.78` subcaches, `.25.dylddata`, `.{26..78}.dyldreadonly`, `.79.dyldlinkedit`, `.symbols`, `.atlas`.

## 4. Наличие dyld shared cache

- **B2**: присутствует и доступен — извлечён полный набор.
- **B3**: присутствует в каталоге, но **данные недоступны** — см. ограничение.

## 5. Наличие CarrierBundleUtilities.dylib

- **B2**: `dyld cache → /usr/lib/CarrierBundleUtilities.dylib`, VA `0x2c5643000`, UUID `387c1f49-…` — извлечён.
- **B3**: `/usr/lib/CarrierBundleUtilities.dylib` — `FileNotFound` как standalone-файл; только в dyld cache. Cache unread → **не извлечён**.

## 6. Ограничение B3 (зафиксировано, не обходится)

`stat` для subcache: `kind=File`, `compression=Some(Header{compression_type:14, …})`, `com.apple.ResourceFork` xattr = **0 байт** (dataless), `com.apple.decmpfs` = 16-байтовый заголовок.

- Main-cache `dyld_shared_cache_arm64e`: `compression=None`, `size=802816`, но data-fork читается как 0 — extent-записи не резолвятся в данные текущей версией `dpp`/`apfs` reader (j_type 13 / deduped / dataless extents, не покрытые `read_file_data`).
- Добавлена поддержка cmpfs type 14 (LZFSE resource-fork) — не помогает, т.к. resource-fork пуст; реальный payload лежит в extents, которые reader не выдаёт.
- **Шифрование не обходилось.** Оригинальные DMG не изменены.

## 7. Вывод

B2 cryptex полностью доступен → CarrierBundleUtilities извлечён.
B3 cryptex читаем на уровне каталогов, но subcache-файлы dyld **dataless** в этом reader — CarrierBundleUtilities B3 остаётся недоступным (UNKNOWN), что ограничивает прямой binary-diff matcher'а.
