# Phase 18 · Отчёт 04 — Проверка корректности извлечения

## 1. Mach-O header

| Проверка | Значение | Вердикт |
|---|---|---|
| magic | `0xcffaedfe` = MH_MAGIC_64 (little-endian `cffaedfe`) | OK |
| cputype | `0x100000c` (CPU_ARCH_ABI64 | arm64e) | OK |
| filetype | 20 (dyld sub-image) | OK |
| flags | `0x82110085` | OK |
| VA image | `0x2c5643000` (выравнивание 0x4000) | OK |

## 2. VM ↔ file mapping

Mapping subcache `.73`: `va 0x2c0400000 → fileoff 0`, size `0x7cc8000`.
Image VA `0x2c5643000` → fileoff `0x2c5643000-0x2c0400000 = 0x5243000`. Совпадает с реальным Mach-O magic на этом смещении → **корректно**.

`__text` VA `0x2c5643a90` → fileoff `0x5243a90`. Секция `__cstring` VA `0x2c5652a28` → fileoff `0x5252a28`; строки читаются по этим адресам → **согласовано**.

## 3. Section offsets / executable ranges

`__text` size `0xddac`; следующая секция `__gcc_except_tab` начинается сразу после `__text` в VA (`0x2c565183c`). Границы целы. `__objc_stubs`/`__auth_stubs`/`__objc_methname` имеют `size=0` — метаданные objc вынесены в общий кэш (норма для cache images).

## 4. Objective-C metadata

Секции `__objc_*` пусты (size 0) — **objc metadata не извлекается из этого сегмента**; классы/методы библиотеки живут в `__AUTH_CONST`/общем кэше. Это ограничение, а не ошибка extractor'а.

## 5. Branch targets

Дизассемблирование линейно; 234 PAC-функции имеют корректные `pacibsp`/`retab`/`blraa`. Branch targets не проверялись по таблице (нет LINKEDIT/function-starts для этого image) — **UNKNOWN для точных границ функций**; используется PAC-эвристика.

## 6. PAC

`pacda`, `pacibsp`, `retab`, `blraa` присутствуют — arm64e PAC-код подтверждён.

## 7. Независимая проверка адресов

- VA `0x2c5643000` ↔ `CarrierBundleUtilities` в `imagesText` таблице main-cache — совпало.
- `__cstring` VA ↔ строки — читаются корректно.
- ADRP+LDR target = адрес строки в сегменте — самосогласовано.

## 8. Ошибки extractor — исправление

- **cmpfs**: добавлена поддержка compression type `14` (LZFSE resource-fork) — патч в `cmpfs/src/lib.rs`.
- **Исправленный скрипт**: `p18_cbu_extract.py` — извлечение `__TEXT` по mapping subcache.
- Остаточное ограничение: B3 subcache dataless — не ошибка кода, а формат хранения, не покрытый reader'ом.

## 9. Исходные данные

Оригинальные DMG/dyld кэши не изменены; извлечение — read-only.
