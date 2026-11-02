# Phase 18 · Отчёт 06 — Восстановление алгоритма выбора bundle

## 1. Архитектурное уточнение

Phase 18 установил ключевой факт: **выбор bundle и верификация bundle — разные компоненты**.

- **Matcher (выбор)**: `CarrierBundleHandler` в CommCenter — `matchCarrierBundle_sync`.
- **Validator (доверие)**: `CarrierBundleUtilities.dylib` — signature/version.xml/PRI verification.

IMSI-symlink разрешается **в CommCenter**, до/во время match; CBU проверяет уже выбранный файл.

## 2. Подтверждённая цепочка

```
SIM identity (IMSI/MCC/MNC/ICCID/GID)
   │  CommCenter: kSubscriber{Imsi,Mcc,Mnc,...}, copyMCCMNCFromIMSI,
   │  createIMSIFromMccMnc, DigitMNCWithIMSI
   ▼
matching information dict
   │  + HomeBundleIdentifier (overlay, Phase 17)
   │  + eIMSI config subfolder match (CommCenter:
   │    "BCAM eIMSI config subfolder matching '%s'")
   ▼
matchCarrierBundle_sync  (CommCenter, IMP не разрешён — B-level)
   │  ├─ IMSI-alias: BundleLinks dir + _readlink/_realpath/_lstat  ← CarrierSIM
   │  ├─ matchOperatorBundle / matchCountryBundle / matchBootstrap
   │  └─ matchDefaultBundle / matchDefaultBCAMBundle
   ▼
candidate bundle → sendBundleEvent_sync
   │  CommCenter: carrier_bundles/operator_bundles/default_bundle sinks
   ▼
validation — CarrierBundleUtilities.dylib (только B2 доступен)
   │  readBundle (0x2c5646540) → eIMSIConfig classify (0x2c564725c)
   │  → signature verify (0x2c564d69c/…ee90) → version.xml check
   ▼
selected bundle применён
```

## 3. Параметры и приоритет (по иерархии имён CommCenter)

1. **IMSI-alias / BundleLinks** — чужой подписанный bundle через симлинк (CarrierSIM).
2. **eIMSI config subfolder match** — BCAM/eSIM профиль.
3. **Operator** — SPN/GID/exact operator.
4. **Country** — регион.
5. **Bootstrap** — первичная настройка.
6. **Default / BCAM default** — fallback.

## 4. Роль каталогов

| Каталог | Роль |
|---|---|
| `…/Carrier Bundles/iPhone` (системный) | подписанные Apple bundle |
| `BundleLinks` | **точка IMSI-симлинка** — разрешается `_readlink`/`_lstat` |
| пользовательский/overlay | matching-info (HomeBundleIdentifier) — enrichment |

## 5. Кэш

`carrier_bundles`/`operator_bundles`/`default_bundle` property sinks — кэш результата match (`already cached, returning cached`).

## 6. Отсутствующее соответствие / несколько кандидатов

- fallback-цепочка operator→country→bootstrap→default;
- `No match for overlay`, `override not required` — для overlay;
- `eIMSI config subfolder matching '%s' not found` — для eIMSI.

## 7. UNKNOWN

- Точный scoring внутри `matchCarrierBundle_sync` (IMP не разрешён, B3 CBU недоступен).
- Порядок IMSI-alias vs eIMSI vs operator внутри dispatch — по именам восстановлен, по коду нет.
