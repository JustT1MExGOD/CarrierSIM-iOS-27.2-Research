# Phase 15 · Отчёт 02 — Инвентаризация локальных образов

## 1. Назначение документа

Полная инвентаризация локальных IPSW/OTA/DMG/cryptex/dyld-cache источников,
доступных для статического анализа CarrierSIM под iOS 27.2 (Beta 2 `24B5089g`,
Beta 3 `24B5099f`, RC `24B119`). Каждый источник классифицирован по роли
(main rootfs vs System Cryptex vs dyld cache) и по пригодности для извлечения
`CommCenter` и `CarrierBundleUtilities.dylib`.

## 2. Расшифрованные DMG (локальные, готовые к анализу)

### Main rootfs (файловая система устройства) — `141-56668`

| Путь | Размер | SHA-256 | Том |
|---|---|---|---|
| `C:\ipsw-tools\beta2-fs-decrypted\141-56668-025.dmg` | 10 454 302 720 | `0c78044a3f69a270cd23a6712f5aae05e32d4646277b9e2c5f056e5481cffbc0` | B2 rootfs |
| `C:\ipsw-tools\beta3-fs-decrypted\141-56668-039.dmg` | 10 517 217 280 | `8d7d2e8e29d6f7dab9d963603b27522a82c6b3344cf2e8cdd2cb67a4b61a6cc7` | B3 rootfs |

- Формат: голый APFS-контейнер (`NXSB` magic на блоке 0), **не** UDIF (`koly`
  trailer отсутствует → `dpp-tool`/`fs` отклоняет; требуется прямой
  `apfs::ApfsVolume::open`).
- Экстенты файлов хранятся как `j_file_extent` (j_type 8) в открытом виде —
  физический маппинг **доступен**. Именно отсюда были извлечены `atc`,
  `amfid`, `installd` (Phase 10/REPORT.md).
- Содержит: `usr`, `bin`, `sbin`, `private`, `var`, `System`, `Library`,
  `etc`, `dev`, `tmp`, `Applications`, `Developer`, `cores` (15 корневых
  записей — подтверждено `list_directory("/")`).

### System Cryptex — `141-56439`

| Путь | Размер | SHA-256 | Том |
|---|---|---|---|
| `C:\ipsw-tools\beta2-decrypted\141-56439-025.dmg` | 6 188 695 552 | `971bc2234869f88cc661dbc2c758063691cbd8c754b1564369e2481235a9d2ec` | B2 cryptex |
| `C:\ipsw-tools\beta3-system\24B5099f__iPhone16,1\141-56439-039.dmg` | 6 192 889 856 | `fbe834971d5d737d751f236f5ecb09545ffd397eb555652d157b4a4a79cb288b` | B3 cryptex |

- Формат: голый APFS-контейнер.
- Содержит WebKit/Safari-стек (`WebKit.framework`, `MobileSafari.framework`,
  `WebCore.framework` и т.п.) и `System/Library/Caches/com.apple.dyld` —
  полный dyld shared cache платформы.
- **Критическое ограничение**: физические экстенты файлов в cryptex
  зашифрованы — `j_file_extent` (j_type 8) отсутствует полностью; census
  показывает только типы `{3,4,5,6,9,12,13}`. Данные хранятся в resource-fork
  data stream через crypto-state записи `j_type 13`; `phys_block` не читается
  без ключа тома. `compression_type=14` (LZFSE). Подтверждено полным census
  каталога (REPORT.md §B).
- Следствие: файловое содержимое субкэшей `.79.dyldlinkedit` и `.symbols`
  в образе **присутствует** (их inode и decmpfs-размеры известны:
  694 321 152 и 1 245 495 296 байт), но **физически недостижимо** — логический
  →физический маппинг зашифрован. Извлечённые на диск `.79.dyldlinkedit` и
  `.symbols` имеют размер 0 именно по этой причине, а не потому что файлы
  пусты в образе.

### Зашифрованные `.aea` исходники (не анализируются напрямую)

- `beta2-filesystem\24B5089g__iPhone16,1\141-56668-025.dmg.aea` — 9 126 805 504
- `beta2-system\24B5089g__iPhone16,1\141-56439-025.dmg.aea` — 2 415 919 104
- `beta3-filesystem\24B5099f__iPhone16,1\141-56668-039.dmg.aea` — 9 126 805 504
- `beta3-system\24B5099f__iPhone16,1\141-56439-039.dmg.aea` — 2 415 919 104
- `beta2-dmg\24B5089g__iPhone16,1\141-55981-031.dmg` — 16 777 216 (маленький,
  вероятно restore/ramdisk-компонент)

## 3. dyld shared cache (B2, извлечён из cryptex)

Каталог: `C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\`

- Главный `dyld_shared_cache_arm64e` — 802 816 байт (только заголовок/
  mapping info / image array; код в субкэшах), SHA-256
  `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8`.
- Субкэши `.01`…`.79` присутствуют, включая `.25.dylddata`,
  `.54.dylddata`, `.26.dyldreadonly`, `.55.dyldreadonly`, `.77.dylddata`,
  `.78.dyldreadonly`, `.atlas`.
- `.79.dyldlinkedit` — **0 байт** (SHA-256 `e3b0c442…` пустого файла).
- `.symbols` — **0 байт** (SHA-256 `e3b0c442…` пустого файла).

Оба пустых файла — следствие зашифрованных cryptex-экстентов (см. §2),
а не реального отсутствия данных в образе. Отсутствие `__LINKEDIT`, экспорт-
три, binds и символов — **ограничение источника**, не исправимое установкой
другого парсера: `ipsw dyld image` падает `⨯ …79.dyldlinkedit: EOF`.

## 4. Что где лежит — матрица поиска CommCenter / CarrierBundleUtilities

| Компонент | rootfs `141-56668` | cryptex `141-56439` | dyld cache |
|---|---|---|---|
| `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` | **есть — извлечён** (B2 41 018 192 Б, B3 40 370 720 Б) | отсутствует (нет CoreTelephony в cryptex-каталоге) | строка пути есть в `.01` |
| `/usr/lib/CarrierBundleUtilities.dylib` | нет (FileNotFound) | отсутствует (`usr/lib` cryptex = только libobjc/libstdc++/objc-msgSend) | строка пути есть в main/.73/.atlas + `LC_LOAD_DYLIB` в CommCenter |
| `CoreTelephony.framework` | нет | нет | есть как образ в cache |
| `CarrierBundle*Interface` (строки) | — | — | `.46` + C++ символы в CommCenter |

**Вывод по размещению**: `CommCenter` — standalone-файл в main rootfs
(`MH_EXECUTE`), извлечён `probe_catbin`. `CarrierBundleUtilities.dylib` и
`CoreTelephony` — только dyld-образы (install-name в cache + загружаются
CommCenter); их тела недоступны из-за зашифрованного `.dyldlinkedit`.

## 5. Прочие источники

- `beta2\24B5089g__iPhone16,1\kernelcache.release.iPhone16,1` — ядро B2.
- `b3_dyld_probe.bin`, `rsrc_symbols.bin` — промежуточные дампы.
- `tmp_com.apple.CommCenter.plist` — launchd-манифест CommCenter
  (`ProgramArguments=/System/Library/Frameworks/CoreTelephony.framework/
  Support/CommCenter`, `UserName=_wireless`, MachServices `…commcenter.xpc`,
  `_LimitLoadToDeviceTree=baseband`). Подтверждает только launch-конфигурацию,
  не содержит кода.
- Извлечённые бинарники: `atc_B2/B3.bin`, `amfid_B2/B3.bin`,
  `installd_B2/B3.bin`, `AirTraffic_B2.bin`, `AirTraffic_text_B2/B3.bin` —
  с UUID и SHA-256 (см. `11_COMPONENT_AVAILABILITY_MATRIX.md`).

## 6. Ограничения инвентаризации

- Полный IPSW (`iPhone16,1_27.2_24B5099f_Restore.ipsw`, ~12.4 ГБ) локально
  **отсутствует** — был получен только cryptex через HTTP Range
  (`bytes=386409981-2802329085`). Остальные разделы IPSW (OTA update payload,
  ramdisk, SEP/baseband firmware) недоступны.
- RC `24B119` образы на диске нет — анализ RC опирается на логи устройства
  (`rc-test-24B119`, `research-evidence-package/logs`), а не на IPSW.
- Скачивание дополнительных материалов не выполнялось (ограничение Phase 15).
