# Phase 16 · Отчёт 05 — Алгоритм выбора bundle

## 1. Назначение документа

Восстановление последовательности `SIM → identifiers → matching → candidates →
validation → selected bundle` по коду CommCenter и его API-поверхности.

## 2. Поток данных

```
subscriber::SimSlot
   │  handleSIMCarrierInfo_sync(SimSlot, BundleTechnologyType,
   │     BundleChangeType, CFDictionary info)
   ▼
matchCarrierBundleForSim_sync  (per-slot entry)
   ▼
matchCarrierBundle_sync  (core dispatcher)
   │  собирает matching-info из SIM-идентификаторов:
   │    kSubscriber{Imsi,Mcc,Mnc,Iccid,IsEsim,SIM2GID1,SIM2GID2,SimTrayStatus}
   │    copyMCCMNCFromIMSI / createIMSIFromMccMnc / DigitMNCWithIMSI
   │    AllowedIMSIPrefixes / IMSIOverride
   ▼
   ├─ matchOperatorBundle_sync   (точный оператор/SPN/GID/IMSI)
   ├─ matchCountryBundle_sync    (по стране)
   ├─ matchBootstrapBundle_sync  (bootstrap)
   ├─ matchDefaultBundle_sync    (fallback default)
   └─ matchDefaultBCAMBundle_sync(BCAM default)
        │  scoring/выбор — в CarrierBundleUtilities.dylib (UNKNOWN)
        ▼
sendBundleEvent_sync(BundleType, BundleChangeType, SimSlot)
        │  применение + уведомление + кэш (`carrier_bundles`/`operator_bundles`/
        │  `default_bundle` REST property sinks)
        ▼
copyCarrierBundleValue{,WithDefault,WithCountryBundleLookup,s}
        (чтение значений из выбранного bundle)
```

## 3. Источники данных и кто их читает

| Данные | Ключ/функция чтения | Где используется |
|---|---|---|
| IMSI | `kSubscriberImsi`, `copyMCCMNCFromIMSI`, `createIMSIFromMccMnc` | `matchCarrierBundle_sync` → префикс-match (`AllowedIMSIPrefixes`, `IMSIOverride`) |
| MCC/MNC | `kSubscriberMcc`/`kSubscriberMnc`, `DigitMNCWithIMSI` | `matchOperatorBundle`/`matchCountryBundle` |
| ICCID | `kSubscriberIccid`, `matching info: ICCID` | matching-info dict |
| GID1/GID2 | `SIM2GID1`/`SIM2GID2` | match criteria |
| SPN | `homeBundleIdentifierFromMatchInfo` (overlay) | `matchOperatorBundle` |
| IsEsim/Tray | `kSubscriberIsEsim`/`kSubscriberSimTrayStatus` | фильтр кандидатов |
| WirelessTech | `WirelessTechnologyList` аргумент | `matchCarrierBundle_sync` |
| BundleType | `sendBundleEvent_sync`/`matchCountryBundle` | тип bundle (operator/country/…) |

## 4. Приоритет match (по иерархии имён)

1. **IMSI-префикс** (`AllowedIMSIPrefixes`, `IMSIOverride`) — самый точный.
2. **Operator** (`matchOperatorBundle_sync`) — SPN/GID/operator.
3. **Country** (`matchCountryBundle_sync`) — регион.
4. **Bootstrap** (`matchBootstrapBundle_sync`).
5. **Default** (`matchDefaultBundle_sync`) / **BCAM default**
   (`matchDefaultBCAMBundle_sync`) — fallback.

`HomeBundleIdentifier from overlay file` подмешивается в match-info и
участвует как критерий (`search for best match with SIM Info`).

## 5. Валидация и кэширование

- `bundle matching info is invalid`, `matching info is invalid` — валидация.
- `kCarrierBundleWatchBundleMatchCriteria` — подписка на критерии.
- `carrier_bundles`/`operator_bundles`/`default_bundle` property sinks —
  **кэш результата** (match result кэшируется; `BCAM bundle lookup results
  are already cached, returning cached results`).

## 6. Поведение при отсутствии соответствия

- fallback-цепочка operator→country→bootstrap→default;
- `Not sending bundle setup event because nothing has changed` — идемпотентность;
- `Request to initialize bundle, but the matching information and tech have
  not changed. Not processing further` — пропуск при неизменных входных.

## 7. Неизвестное (UNKNOWN)

- Точный scoring/priority внутри `CarrierBundleUtilities.dylib`
  (тело недоступно).
- Точный порядок IMSI-vs-SPN-vs-GID внутри `matchOperatorBundle_sync` —
  по именам восстановлена иерархия, по коду внутри — нет.
