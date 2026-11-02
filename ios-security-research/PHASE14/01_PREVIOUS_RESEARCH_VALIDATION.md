# Фаза 14 — проверка предыдущих исследований

## 1. Результат проверки

Phase 14 не начиналась с повторного извлечения. Были сопоставлены отчёты Phase 11–13, локальные бинарники, dyld-cache и исходники CarrierSIM.

Главный результат проверки: в Phase 13 имена carrier-bundle интерфейсов были найдены только как строки. Они не являются доказательством доступного API, реализации или возможности изменить сопоставление SIM.

## 2. Доступные исполняемые материалы

| Компонент | Путь | Сборка | UUID | Состояние |
|---|---|---|---|---|
| `amfid` | `C:\ipsw-tools\amfid_B3.bin` | B3 `24B5099f` | `CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B` | корректный Mach-O, дизасм доступен |
| `installd` | `C:\ipsw-tools\installd_B3.bin` | B3 `24B5099f` | `F54A48D1-4E77-3425-BEAB-5EBBBB037C0F` | корректный Mach-O, дизасм доступен |
| `atc` | `C:\ipsw-tools\atc_B3.bin` | B3 `24B5099f` | `CA2F88E5-5348-330C-89FA-98BA1ADEA086` | корректный Mach-O, дизасм доступен |
| `AirTraffic` `__text` | `C:\ipsw-tools\AirTraffic_text_B3.bin` | B3 | `BE4EA03B-081A-3EDF-BD16-5396096485DB` | только срез `__text` |
| `MobileInstallation` | `PHASE11\extracted_v2\MobileInstallation_B2.dylib` | B2 | `60B509C3-9DED-3504-8840-9874714C0109` | компактная частичная реконструкция |
| `Security` | `PHASE11\extracted_v2\Security_B2.dylib` | B2 | `A413232A-E824-39DF-AAFA-2E7E6153AE24` | компактная частичная реконструкция |

Полные SHA-256 и размеры перечислены в Phase 11/12. Повреждённые извлечения `PHASE10\extracted\dyld_B2` не используются.

## 3. Dyld-cache и отсутствующие данные

Основной локальный B2 cache:

`C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\dyld_shared_cache_arm64e`

- UUID cache: `4A8F3C2F-15CF-3AE3-B702-9B66E918CDEB`.
- SHA-256: `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8`.
- `.79.dyldlinkedit`: 0 байт, UUID `79D3F635-C960-3C22-A00A-264E5975D82D`.
- `.symbols`: 0 байт.
- Ожидаемый диапазон `__LINKEDIT`: приблизительно `0x2de48c000–0x31f740000`, около 663 МБ.

Это исключает восстановление оригинальных export/bind/symbol tables и полноценное standalone-извлечение CommCenter/CarrierBundleUtilities из локального B2 cache.

B3 system DMG присутствует, но отдельный B3 dyld shared cache с пригодным `LINKEDIT` локально не найден. RC-бинарники CommCenter/CoreTelephony также отсутствуют.

## 4. Что подтверждено дизассемблированием

- `AirTraffic` B2→B3: move-рутина заменена на dirfd-confined последовательность; это подтверждено срезами `__text` и runtime-логом RC.
- `atc`: обработка AirTraffic assets подтверждена дизассемблированием.
- `installd`: app installation, provisioning profile и отдельные проверки подтверждены дизассемблированием; carrier-bundle installer в нём не найден.
- `amfid`: trust-validation path подтверждён, но к carrier bundle не относится.

## 5. Что основано только на строках/конфигурации

В B2 cache найдены:

- путь `/usr/lib/CarrierBundleUtilities.dylib` — в main cache metadata и связанных cache-файлах;
- путь `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` — строковая запись в `.01`;
- имена `CarrierBundleInstallInterface`, `CarrierBundleLockdownInterface`, `CarrierBundleMatchProxyInterface`, `CarrierBundleManagerInterface`, `CarrierBundleServerInterface`, `CarrierBundleCacheInterface`, `CarrierBundleDownloaderInterface` — в `.46`;
- ключи `kCarrierBundle*`, `kSubscriberImsi`, `kSubscriberMcc`, `kSubscriberMnc`, `kSubscriberIccid`, `GID1`, `GID2` — в cache strings.

Это доказывает наличие строк в cache, но не реализацию, вызов, полномочия или доступность.

## 6. Компоненты, остающиеся недоступными

- `CommCenter` как Mach-O;
- `CarrierBundleUtilities.dylib` как Mach-O;
- device-side `installation_proxy`/IPCC helper;
- RC dyld cache и RC CommCenter;
- точные CommCenter XPC protocols и entitlement checks.

## 7. Итог

Phase 11–13 корректно установили data-quality boundary и AirTraffic regression. Phase 14 может каталогизировать строковую внутреннюю поверхность, но не может честно восстановить реализацию интерфейсов без отсутствующего `LINKEDIT` или другого полного образа.
