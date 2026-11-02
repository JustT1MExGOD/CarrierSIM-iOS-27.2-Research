# Phase 18 · Отчёт 03 — Recovery CarrierBundleUtilities

## 1. Install name и mapping

- **Install name**: `/usr/lib/CarrierBundleUtilities.dylib`
- **Источник**: dyld shared cache `dyld_shared_cache_arm64e.73` (B2)
- **Load address (VA)**: `0x2c5643000`
- **UUID**: `387c1f49-584a-37ba-a526-0ab0f6041e02`
- **Subcache**: `.73`, mapping `va=0x2c0400000 size=0x7cc8000 fileoff=0` (prot 5/5); image fileoff `0x5243000`

## 2. Mach-O в кэше

| Поле | Значение |
|---|---|
| magic | `0xcffaedfe` (MH_MAGIC_64) |
| cputype | `0x100000c` (arm64e, PAC) |
| filetype | 20 (dyld-cache-optimized dylib) |
| flags | `0x82110085` |
| ncmds (видимых) | dyld-cache формат — заголовок содержит sub-image листинг |

## 3. Сегменты

| Сегмент | VA | vsize | fileoff |
|---|---|---|---|
| `__TEXT` | `0x2c5643000` | `0x11a6c` | `0x5243000` |
| `__DATA_CONST` | `0x2d1e587e0` | `0xb0` | `0x1df47e0` |
| `__AUTH_CONST` | `0x2d5d27ad0` | `0x7c0` | `0x5cc3ad0` |
| `__LINKEDIT` | `0x2de48c000` | (в linkedit subcache) | — |

## 4. Секции `__TEXT`

| Секция | VA | size | fileoff |
|---|---|---|---|
| `__text` | `0x2c5643a90` | `0xddac` | `0x5243a90` |
| `__gcc_except_tab` | `0x2c565183c` | `0x11ec` | `0x525183c` |
| `__cstring` | `0x2c5652a28` | `0x1b0` | `0x5252a28` |
| `__const` | `0x2c5652bd8` | `0x5ea` | `0x5252bd8` |
| `__oslogstring` | `0x2c56531c2` | `0x1081` | `0x52531c2` |
| `__unwind_info` | `0x2c5654244` | `0x828` | `0x5254244` |

## 5. Извлечённое представление

Полный Mach-O восстановить нельзя (LINKEDIT/sub-images в других subcache, chained fixups ссылаются на cache-адреса). Извлечён **сырой `__text`**:

- файл: `C:\ipsw-tools\CBU_B2_text.bin` (0x11a6c Б — весь `__TEXT` сегмент)
- `__text` code: `0xddac` Б, **SHA-256 `68c6644367148b2f3a1d71c3d7039b79856b0f23e65c8e93f3b4f461cfbf0c03`**
- дизассемблер: Capstone → **14 187 инструкций**, **234 PAC-пролога** (`pacibsp`/`paciasp`)

## 6. Проверка корректности

- PAC-прологи присутствуют → реальный исполняемый код.
- ADRP+LDR разрешают cstring/oslog строки → согласованный VA.
- Строки тематически верны: `eIMSIConfig_`, `CBSignature`, `overrides_mvno`, `CarrierBundleSignatures`, `CountryBundles`, PRI/`copyPRISignatureForDeviceName`.
- Дизассемблирование начинается с валидной PAC-записи (`pacda x16,x17`) — код целостен.

## 7. B3 — недоступно

`/usr/lib/CarrierBundleUtilities.dylib` отсутствует как файл; в dyld cache есть, но subcache dataless → `__text` B3 **не извлечён**. Direct binary-diff невозможен.
