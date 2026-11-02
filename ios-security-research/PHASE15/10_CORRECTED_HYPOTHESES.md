# Phase 15 · Отчёт 10 — Скорректированные гипотезы H14-01…H14-06

## 1. Назначение документа

Переклассификация гипотез H14 **после** восстановления `CommCenter_B2.bin`.
Допустимые статусы: `CONFIRMED`, `SUPPORTED BUT INCOMPLETE`,
`INSUFFICIENT EVIDENCE`, `RULED OUT`.

## 2. Таблица переклассификации

| Гипотеза | Статус (Phase 15) | Обоснование |
|---|---|---|
| H14-01: `CarrierBundle*Interface` — внутренний API CommCenter | **`CONFIRMED`** | C++ mangled-классы `*InterfaceD2Ev/EEE` в `CommCenter_B2.bin` + XPC-прототипы (`xpc::dict`, `auto_reply`, `RestModule`) + `LC_LOAD_DYLIB CarrierBundleUtilities`. |
| H14-02: интерфейсы защищены entitlement | **`SUPPORTED BUT INCOMPLETE`** | `EntitlementChecker:forConnection:`, `EntitlementCache`, `EntitlementController`, `com.apple.carrierspace.control.allow` существуют как классы/строки; точный ключ на каждый интерфейс не разобран. |
| H14-03: IMSI-маппинг создаётся только Catalog-replace (CarrierSIM), а не IPCC | **`SUPPORTED BUT INCOMPLETE`** | Доказано: CarrierSIM делает alias файловым симлинком (A); IPCC-путь не показан как источник alias, но и не опровергнут. |
| H14-04: CommCenter резолвит IMSI→bundle при match | **`CONFIRMED`** | `copyMCCMNCFromIMSI`, `createIMSIFromMccMnc`, `AllowedIMSIPrefixes`, `IMSIOverride`, `DigitMNCWithIMSI`, `kCarrierBundleWatchBundleMatchCriteria`, `kSubscriber{Imsi,Mcc,Mnc,Iccid,IsEsim}`. |
| H14-05: штатный механизм (IPCC/OTA/eSIM/MDM) может назначить SIM A существующий bundle оператора B | **`INSUFFICIENT EVIDENCE`** | IMSI-алиасы — поддерживаемый механизм (`IMSIOverride`, `AllowedIMSIPrefixes`), но device-side код официального назначения чужого bundle не показан; операторская конфигурация не исключена. |
| H14-06: AirTraffic B3/RC закрывает запись carrier-catalog | **`CONFIRMED`** | `__TEXT` B3 AirTraffic: `open()` AFC-root + `mkdir beneath` + `errno`; runtime `errno 107`/`ENOTCAPABLE`. |

## 3. Дополнительные уточнения

- IMSI-алиасы — **штатный, поддерживаемый** механизм матчинга CommCenter
  (`IMSIOverride`, `AllowedIMSIPrefixes`, `EnableIMSISwitch`,
  `commCenterIMSISwitchEvent`), а не эксплуатационный побочный эффект.
- VoWiFi: **не исключён** для оператора — bundle-selection не определяет
  сетевое разрешение IMS; operator-side активация не исключена.
- `CarrierBundleUtilities.dylib`: существует и загружается CommCenter
  (`LC_LOAD_DYLIB`), но тело не восстановлено — `SUPPORTED BUT INCOMPLETE`.

## 4. Вывод

Из шести гипотез: **три CONFIRMED** (H14-01, H14-04, H14-06), **две
SUPPORTED BUT INCOMPLETE** (H14-02, H14-03), **одна INSUFFICIENT EVIDENCE**
(H14-05). Главный скачок доказательности — восстановление CommCenter дало
реальные C++ классы и XPC-прототипы вместо строковых предположений Phase 14.
