# Фаза 13 — инвентаризация компонентов

Устройство/платформа: iPhone16,1 (iPhone 15 Pro), arm64e. Сборки: Beta 2 (24B5089g), Beta 3 (24B5099f), RC (24B119). Уверенность символов: FULL / PARTIAL / SLICE / NONE (см. Phase 1 `01_INVENTORY.md`).

## 1. Таблица компонентов

| Компонент | Путь | Сборка | UUID Mach-O | SHA-256 | Арх | Дизасм | Участие в carrier config | Статус |
|---|---|---|---|---|---|---|---|---|
| `CommCenter` | `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` | B3 (24B5099f) | не извлечён | не извлечён | arm64e | НЕТ (только launchd plist + строки dyld-cache) | OWNS carrier config/profile, выбор bundle | **НЕ ИЗВЛЕЧЁН — ключевой пробел** |
| `CoreTelephony.framework` | `/System/Library/Frameworks/CoreTelephony.framework/CoreTelephony` | B2 | — | — | arm64e | только строки/ключи из dyld subcache (.05,.07) | клиентский API `copyCarrierBundleValue`, `kCarrierBundle*` | PARTIAL (строки) |
| `installd` | `/usr/libexec/installd` | B3 | `F54A48D1-4E77-3425-BEAB-5EBBBB037C0F` | `1dd5efbf…064b1d` | arm64e | `installd_B3_disasm.txt` (FULL-ish) | app-install + provisioning profiles; **не IPCC-writer для carrier catalog** | PARTIAL |
| `atc` | `/usr/libexec/atc` | B3 | `CA2F88E5-5348-330C-89FA-98BA1ADEA086` | `2ed9c6fe…5a4afc` | arm64e | `atc_B3_disasm.txt` | media-SYNC (AirTraffic), user `mobile`, jailed в Media | FULL-ish |
| `AirTraffic.framework` | `/System/Library/PrivateFrameworks/AirTraffic.framework/AirTraffic` | B3 | `be4ea03b…85db` | `d263612f…54ec1` | arm64e | `AirTraffic_text_B3.bin` (SLICE 128KB `__text`) | move-рутина «beneath AFC root» — место регрессии | SLICE |
| `MobileInstallation.framework` | извлечён в `PHASE11/extracted_v2` | B2 | `60B509C3-9DED-3504-8840-9874714C0109` | `c6903554…d84620` | arm64e | PARTIAL | app-install API `MobileInstallationInstallApp`; provisioning profiles | PARTIAL |
| `streaming_zip_conduit` | `/usr/libexec/streaming_zip_conduit` | B3 | не извлечён | не извлечён | — | только launchd plist (user `mobile`, `com.apple.streaming_zip_conduit`) | upload ZIP-триггера IPCC | НЕ ИЗВЛЕЧЁН |
| `fileproviderd` | системный демон | — | — | — | — | только syslog deny | НЕ mover; disk-usage scan (infer) | НЕ ИЗВЛЕЧЁН |
| `installation_proxy` | lockdown-сервис → демон | — | — | — | — | pymobiledevice3 client | IPCC install entry point (`install_from_local`) | ИНТЕРФЕЙС есть, реализация НЕ извлечена |

## 2. Что подтверждено участием в carrier config

- **CommCenter** — владелец carrier profile и логики выбора bundle. Подтверждено: launchd plist (`MachServices` включая `commcenter.carrierspace.xpc`, `commcenter.mobile-helper-cbupdateservice`, `com.apple.commcenter.coretelephony.xpc`), строки `kCarrierBundlePathForBundle`, `kCarrierBundleTriggerInstallCarrierBundle`, `kCarrierBundleWatchBundleMatchCriteria`, `kSubscriberImsi`, `kSubscriberIccid`, `copyCarrierBundleValue`. В строковом слое dyld-cache также обнаружены интерфейсы `CarrierBundleInstallInterface`, `CarrierBundleLockdownInterface`, `CarrierBundleMatchProxyInterface`, `CarrierBundleDownloaderInterface`, `CarrierBundleManagerInterface` и путь `/usr/lib/CarrierBundleUtilities.dylib`. Это подтверждает наличие соответствующей внутренней поверхности, но не её доступность и не конкретную семантику методов.
- **atc/AirTraffic** — демон синхронизации; abused как файловый транспорт для записи каталога. НЕ владелец bundle.
- **installation_proxy/streaming_zip_conduit** — канал загрузки IPCC-файла на устройство; реальную установку carrier settings делает CommCenter/соответствующая подсистема после получения IPCC.

## 3. Что НЕ доказано участием

- `installd` — обрабатывает app install и provisioning profiles; строка `Ignoring unsupported carrier bundle` относится к `_bundleInDirectory` (embedded app bundles), НЕ к установке carrier settings. Нет доказательств, что installd пишет в `/var/mobile/Library/Carrier Bundles`.
- `MobileInstallation.framework` — app-ориентирован; `MIInstallProfileWithData`/`MIInstallProfileAtURL` — provisioning profiles, не carrier bundles.

## 4. Ключевые ограничения анализа

1. **CommCenter и CoreTelephony НЕ извлечены как исполняемые образы** — `.79.dyldlinkedit` и `.symbols` в dyld cache = 0 байт (Phase 11). Доступны только: launchd plist, XPC service names, клиентские строки/ключи API, syslog-поведение.
2. Нет RC-бинарей вообще — RC выводится только по логам runtime, не по дизасму.
3. `installation_proxy` реализация (демон, обрабатывающий `.ipcc`) не извлечён — виден только клиентский интерфейс pymobiledevice3 и lockdown service name.

## 5. Следствие

Точная логика выбора bundle в CommCenter (приоритет IMSI-алиаса vs MCCMNC vs GID1/SPN) и обработчик IPCC на стороне устройства остаются **частично недоступными** для построчного анализа. Выводы по ним основаны на строках, ключах API, launchd конфигурации и runtime-логах — что корректно маркируется как INDIRECT/INFERRED, а не DIRECT.
