# Phase 15 · Отчёт 08 — Анализ реально доступного исполняемого кода

## 1. Назначение документа

Перечень бинарников, для которых есть настоящий `__TEXT`, и что из них
следует для carrier-bundle логики. Phase 15 добавил **CommCenter** —
главный недостающий компонент.

## 2. Доступные Mach-O (уровень A)

| Бинарник | Размер | UUID | Источник |
|---|---|---|---|
| **`CommCenter_B2.bin`** | **41 018 192** | **`83978CC2-…`** | **rootfs `…/Support/CommCenter`** |
| `atc_B2.bin` / `atc_B3.bin` | 84 160 | `c5b4b497…`/`ca2f88e5…` | rootfs `/usr/libexec/atc` |
| `amfid_B2.bin` / `amfid_B3.bin` | 253 968 | `3e6d3282…`/`cfb0c004…` | rootfs `/usr/libexec/amfid` |
| `installd_B2.bin` / `installd_B3.bin` | 945 168 / 961 888 | `5d0437d3…`/`f54a48d1…` | rootfs `/usr/libexec/installd` |
| `AirTraffic_B2.bin` | 42 209 280 | `408fdad0…` | cryptex dyld `.48` |
| `AirTraffic_text_B2/B3.bin` | 131 072 | `408fdad0…`/`be4ea03b…` | cryptex dyld `.48` / B3 cryptex |

## 3. CommCenter — новый главный источник доказательств

В отличие от dyld-извлечений, `CommCenter_B2.bin` — **полный файл** со
всеми сегментами (код, ObjC/C++-метаданные, собственный `__LINKEDIT`).

Доказано в его `__TEXT`/строках:

- **CarrierBundle*Interface** — реальные C++ классы с XPC-обработчиками
  (`xpc::dict`, `auto_reply`, `ctu::RestModule`, `dispatch::queue`).
- **bundle-value API**: `copyCarrierBundleValue{,WithDefault,WithCountryBundleLookup,s}`,
  `kCarrierBundlePathForBundle`, `kCarrierBundleTrigger{Install,GetUpdated,Reset}CarrierBundle`,
  `kCarrierBundleWatchBundleMatchCriteria`, `kCarrierBundleTriggerRemoteRestoreToDefault`.
- **subscriber-поля**: `kSubscriber{Imsi,Mcc,Mnc,Iccid,IsEsim,SimTrayStatus,…}`.
- **IMSI-логика**: `copyMCCMNCFromIMSI`, `createIMSIFromMccMnc`,
  `AllowedIMSIPrefixes`, `IMSIOverride`, `DigitMNCWithIMSI`,
  `EnableIMSISwitch`, `commCenterIMSISwitchEvent`, `UseIMSIDuringProvisioning`,
  `DontUseImpiForImsi`, `EnableUnprovisionnedIMSIRemediation`.
- **Entitlement**: `EntitlementChecker:forConnection:`, `EntitlementCache`,
  `EntitlementController`, `com.apple.carrierspace.control.allow`.
- **Carrier plist**: `com.apple.carrier{,_1,_2}.{plist,merged.plist}`,
  `bootstrap`.

## 4. Что доказано из AirTraffic/atc/amfid/installd

- AirTraffic B3: Airlock переписан (`open()` AFC-root + `mkdir beneath` +
  errno) — механизм блокировки CarrierSIM подтверждён кодом.
- atc/amfid/installd: функционально идентичны B2↔B3 (diff = подпись/версия).

## 5. Оставшийся пробел

- `CarrierBundleUtilities.dylib` `__TEXT` не восстановлен (dyld-образ,
  `.dyldlinkedit` зашифрован) → конкретная реализация `copyCarrierBundleValue`
  и IMSI→bundle match-функции внутри библиотеки недоступна. Но её **API-
  поверхность** видна по импортам/символам в CommCenter.
- IPCC-инсталлер device-side (`MobileInstallation` IPCC-путь) `__TEXT`
  не анализировался — вопрос «может ли IPCC создать IMSI-alias» остаётся
  `INSUFFICIENT EVIDENCE`.

## 6. Вывод

Восстановление CommCenter подняло carrier-bundle анализ с уровня B
(строки) до уровня A (реальные классы/селекторы/прототипы). Логика match
находится частично в CommCenter (видна), частично в недоступной
`CarrierBundleUtilities.dylib` (API-граница видна, тело нет).
