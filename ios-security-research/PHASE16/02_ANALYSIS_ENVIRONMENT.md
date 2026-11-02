# Phase 16 · Отчёт 02 — Среда анализа

## 1. Назначение документа

Перечень инструментов, реально доступных локально, и выбранный набор для
статического анализа `CommCenter` arm64e.

## 2. Доступные инструменты

| Инструмент | Статус | Роль |
|---|---|---|
| **Capstone 5.0.7** | ✅ (Python binding) | основной ARM64/arm64e-дизассемблер: `pacibsp`, `retab`, `braa`, `blraa` распознаются корректно |
| **Python 3.14** | ✅ | парсинг Mach-O/APFS/chained-fixups, построение карт, diff |
| `dpp-source` (Rust `apfs`) | ✅ собран (`dpp-tool.exe`, `probe_*.exe`) | чтение rootfs APFS, `read_file` для извлечения Mach-O |
| `ipsw.exe` 3.1.740 | ✅ | `dyld`/`macho` команды (cache-анализ), не для standalone CommCenter |
| собственные скрипты | ✅ | `cc_b2_methods.txt`/`cc_b3_methods.txt` — карты ObjC-методов+IMP; `cc_b2_fstarts.txt` — 135 481 function starts |

## 3. Недоступно / не требовалось

- **Ghidra** — не найдена в системе; не скачивалась (запрет).
- **IDA** — не установлена.
- **LLVM objdump / otool** — отсутствуют в Windows-окружении.
- **radare2/rizin** — отсутствуют.
- **LIEF / macholib** — не установлены; Mach-O парсится вручную (`struct`).

## 4. Выбранный набор и методика

**Capstone + кастомный Mach-O/ObjC-парсер на Python.** Он достаточен, потому
что `CommCenter_B2/B3.bin` — полные Mach-O с `__objc_classlist`, `__objc_const`,
`__objc_selrefs`, `__objc_methname`, `__objc_methlist`, `LC_FUNCTION_STARTS`,
`LC_SYMTAB`, `LC_DYLD_CHAINED_FIXUPS`, что позволяет:

- **Резолвить ObjC-методы** по `class_ro_t.baseMethods` → относительный
  method_list (`{name_off,types_off,imp_off}` как signed 32-бит offsets) →
  имя селектора + IMP-адрес. Реализовано; результат `cc_b2_methods.txt` /
  `cc_b3_methods.txt` (2407/2403 методов, 153 класса).
- **Резолвить селекторы** через `__objc_selrefs` (chained ptr `low32+base`).
- **Дизассемблировать** любой IMP через `vm2off` + Capstone.
- **Нормализованный diff** по последовательности мнемоник (SHA-256).

## 5. Учёт особенностей ARM64e

- **PAC**: `pacibsp`/`retab`/`braa`/`blraa` обрабатываются как отдельные
  мнемоники; при diff они нормализуются по mnemonic, а не по операндам.
- **Indirect branches**: `br`/`blr` через `x16`/`x17` (ObjC `objc_msgSend`
  trampoline, `__objc_stubs`) — резолвятся через selrefs, а не трассировку.
- **Chained fixups**: декодируются `0x100000000 + (raw & 0xffffffff)`;
  verified на selrefs/classlist.
- **Оптимизации**: компилятор группирует одинаковые `bl` в shared stubs
  (`j__*`), tail-call `b` вместо `bl+ret` — при diff учитывается.
- **Разница адресов загрузки**: vm-адреса B2≠B3 (text grew 0x98000);
  сравнение ведётся по нормализованной последовательности мнемоник,
  не по адресам.

## 6. Ограничения

- Нет декомпилятора C→pseudocode — анализ на уровне инструкций и
  call-graph; C++ mangled-имена дают сигнатуры.
- `CarrierBundleUtilities.dylib`/`CoreTelephony` тела недоступны (dyld-образы,
  `.dyldlinkedit` зашифрован) → часть match-логики внутри них `UNKNOWN`.
- Автоматический результат Capstone проверяется вручную по сырой
  инструкции при ключевых выводах (PAC, `bl`-таргеты).
