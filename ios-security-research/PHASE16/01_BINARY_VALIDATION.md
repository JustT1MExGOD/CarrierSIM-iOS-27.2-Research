# Phase 16 · Отчёт 01 — Валидация бинарников

## 1. Назначение документа

Проверка бинарников `CommCenter`, извлечённых в Phase 15, перед
дизассемблированием и бинарным diff.

## 2. Файлы и идентификация

| Параметр | `CommCenter_B2.bin` | `CommCenter_B3.bin` |
|---|---|---|
| Путь | `C:\ipsw-tools\CommCenter_B2.bin` | `C:\ipsw-tools\CommCenter_B3.bin` |
| Размер | 41 018 192 | 40 370 720 |
| SHA-256 | `9e815d9e3a422ed2e65e857a6f1c5396c10d661fcd39bd5bc73234f6c48b2a60` | `9a5eeaf3f8145da4b700e7b7e2f52be1013f82eb24f8f41f8e1a1e66320257d2` |
| Magic | `feedfacf` (Mach-O 64) | `feedfacf` |
| cputype / subtype | `0x100000c / 0x80000002` (arm64e, PAC00) | то же |
| filetype | 2 (`MH_EXECUTE`) | 2 |
| ncmds / flags | 176 / `0x00210085` (`NOUNDEFS\|DYLDLINK\|TWOLEVEL\|BINDS_TO_WEAK\|PIE`) | 176 / то же |
| **UUID** | **`83978CC2-2FEC-36B0-A77C-B9A90ED9C28C`** ✅ | **`747592DD-284C-37BC-AE32-0FE36E8CB3DA`** ✅ |
| LC_DYLD_CHAINED_FIXUPS | есть | есть |
| LC_DYLD_EXPORTS_TRIE | есть (0x20, internal-образ) | есть |
| LC_FUNCTION_STARTS | есть | есть |

**UUID совпадают с Phase 15 → сравнительный анализ разрешён.**

## 3. Сегменты

| Сегмент | B2 `__TEXT` | B2 `__LINKEDIT` | B3 `__TEXT` | B3 `__LINKEDIT` |
|---|---|---|---|---|
| vm | `0x100000000` | `0x102590000` | `0x100000000` | `0x1024f4000` |
| vsize | `0x2398000` | `0x1a4000` | `0x2300000` | `0x1a4000` |
| filesize | `0x2398000` | `0x1a2350` | `0x2300000` | `0x1a0220` |

Отличие `__TEXT` B2 `0x2398000` vs B3 `0x2300000` — размер кода вырос на
`0x98000` (~606 КБ), при этом `__LINKEDIT` почти одинаков — изменения в коде
ограничены, а не глобальны.

## 4. Символы и метаданные

- **LC_SYMTAB присутствует** в обоих: B2 `nsyms=9284`, B3 `nsyms=9261`
  (symoff/stroff корректно распарсены; первые записи — ObjC/Swift импорты и
  `radr://5614542` debug-символ). Это — внешние импорты + debug-имена, а не
  экспортируемые API.
- **LC_FUNCTION_STARTS декодируется**: B2 даёт **135 481** функцию.
- Полная ObjC-метадата: `__objc_classlist` (225 классов), `__objc_const`,
  `__objc_selrefs`, `__objc_methname`, `__objc_methlist`, `__objc_protolist`,
  `__objc_stubs`, `__objc_data`, `__objc_ivar`.
- C++ метаданные: mangled-имена `CarrierBundleHandler::*` в `__TEXT __const`.

## 5. Пригодность для дизассемблирования

- Оба файла — **полные standalone Mach-O со всеми сегментами** (не
  cache-срез), с собственным `__LINKEDIT` → ObjC/C++-имена, selrefs и
  method IMP разрешаются напрямую.
- arm64e + `pacibsp`/`retab` — Capstone 5.0.7 дизассемблирует корректно
  (PAC-инструкции распознаются как `pacibsp`, `retab`, `braa` и т.п.).
- Chained fixups декодируются формулой `target = 0x100000000 + (raw & 0xffffffff)`
  — подтверждено резолвом `__objc_selrefs`/`__objc_classlist`.

## 6. Вывод

Оба бинарника валидны и пригодны для полного статического анализа;
UUID-верификация пройдена; Phase 16 может опираться на них как на
доказательство уровня A.
