# Phase 15 · Отчёт 03 — Восстановление CommCenter

## 1. Назначение документа

Целенаправленный поиск и **успешное восстановление** исполняемого
`/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter`.

## 2. Результат: CommCenter извлечён (уровень A)

| Параметр | Значение |
|---|---|
| Файл | `C:\ipsw-tools\CommCenter_B2.bin` |
| Источник | `beta2-fs-decrypted\141-56668-025.dmg` (main rootfs, экстенты type-8) |
| Путь в образе | `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` |
| Размер | **41 018 192 Б** |
| SHA-256 | `9e815d9e3a422ed2e65e857a6f1c5396c10d661fcd39bd5bc73234f6c48b2a60` |
| Тип | Mach-O 64-bit arm64e (PAC00) `MH_EXECUTE` |
| Флаги | `NOUNDEFS\|DYLDLINK\|TWOLEVEL\|BINDS_TO_WEAK\|PIE` |
| UUID | `83978CC2-2FEC-36B0-A77C-B9A90ED9C28C` |
| Load commands | 176 |

Извлечён `dpp probe_catbin` через `read_file` — полный файл со всеми
сегментами (включая данные, ObjC-метаданные и `__LINKEDIT` самого файла —
не путать с зашифрованным `.79.dyldlinkedit` кэша).

## 3. Подтверждение владельца интерфейсов (уровень A)

`LC_LOAD_DYLIB` в CommCenter включает:

- **`/usr/lib/CarrierBundleUtilities.dylib`** — CommCenter является
  **потребителем/владельцем** carrier-bundle логики;
- `/System/Library/Frameworks/CoreTelephony.framework/CoreTelephony`;
- `…/Support/libCommCenter{Base,M,K}CommandDrivers.dylib`,
  `libCommCenterAWDMetrics`, `libSystemDetermination`, `libCellularDecoders`,
  `CTParser`, `libTelephonyCapabilities`, `CTCarrierSpace`,
  `CellularPlanManager`, `TelephonyUtilities`, `TelephonyXPCClient`.

## 4. Доказанные символы/механизмы в `__TEXT`/строках CommCenter

- Все `CarrierBundle*Interface` (Install, MatchProxy, Lockdown, Manager,
  Server, Cache, Downloader, Factory, XMLCache, BOMCopier,
  ActivationCarrierBundle, Update, CTXPCCarrierBundleNotification) — C++
  mangled-символы (`…D2Ev`, `…EEE`) → **реальные классы, не просто строки**.
- `copyCarrierBundleValue`, `copyCarrierBundleValueWithDefault`,
  `copyCarrierBundleValueWithCountryBundleLookup`, `copyCarrierBundleValues`.
- `kCarrierBundlePathForBundle`,
  `kCarrierBundleTriggerInstallCarrierBundle` (полный XPC-прототип:
  `xpc::dict`, `auto_reply`, `ctu::RestModule`, `dispatch::queue`).
- `kSubscriberImsi`, `kSubscriberMcc`, `kSubscriberMnc`, `kSubscriberIccid`,
  `kSubscriberIsEsim`, `kSubscriberSimTrayStatus`.
- **IMSI-обработка**: `copyMCCMNCFromIMSI`, `createIMSIFromMccMnc`,
  `AllowedIMSIPrefixes`, `IMSIOverride`, `DigitMNCWithIMSI`,
  `EnableIMSISwitch`, `commCenterIMSISwitchEvent`, `UseIMSIDuringProvisioning`.
- **Entitlement-контроль**: `EntitlementChecker:forConnection:`,
  `EntitlementCache`, `EntitlementController`,
  `EntitlementCheckForAttachMonitorMode`, `EntitlementAuthTokenType`.
- **Carrier-settings файлы**: `com.apple.carrier.plist`,
  `com.apple.carrier_{0,1,2}.{plist,merged.plist}`, `bootstrap`,
  `com.apple.carrierspace.control.allow`, `com.apple.bridgecarriersettings`.

## 5. Что это доказывает / опровергает

- **CONFIRMED**: `CarrierBundle*Interface` принадлежат CommCenter —
  это внутренний C++ API CommCenter, обслуживаемый через XPC
  (`xpc::dict`/`auto_reply` в прототипах).
- **SUPPORTED**: entitlement-гейтинг — `EntitlementChecker:forConnection:`
  и `EntitlementCache` присутствуют как реальные классы; конкретные имена
  entitlement-ключей требуют разбора строк около проверок.
- CommCenter — `MH_EXECUTE` (daemon), не dyld-образ → в rootfs как
  standalone-файл, что и позволило его извлечь в отличие от
  `CarrierBundleUtilities.dylib`.
