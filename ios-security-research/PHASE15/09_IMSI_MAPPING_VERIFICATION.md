# Phase 15 · Отчёт 09 — Проверка исторического IMSI-маппинга

## 1. Назначение документа

Как CarrierSIM создаёт IMSI→bundle соответствие и что теперь доказано о
механизме на уровне кода — после восстановления `CommCenter_B2.bin`.

## 2. Механизм CarrierSIM (уровень A, по `carrier.py`)

- IMSI-alias = файловый симлинк `/var/mobile/Library/Carrier Bundles/iPhone/
  <IMSI>` → `/System/Library/Carrier Bundles/iPhone/<bundle>.bundle`
  (`bundle_link`, `make_plan`, `re.fullmatch(r'\d{15}')`).
- Запись — через AirTraffic asset-последовательность; IPCC — только
  триггер рескана (`_upload_ipcc` → AFC `makedirs`/`set_file_contents`).

## 3. Что CommCenter доказывает о резолюции IMSI→bundle (уровень A)

В `__TEXT`/строках CommCenter присутствуют реальные обработчики:

- `copyMCCMNCFromIMSI` — извлечение MCC/MNC из IMSI;
- `createIMSIFromMccMnc` — обратное построение;
- `DigitMNCWithIMSI` — учёт переменной длины MNC;
- `AllowedIMSIPrefixes` — whitelist префиксов IMSI;
- `IMSIOverride`, `EnableIMSISwitch`, `commCenterIMSISwitchEvent`,
  `UseIMSIDuringProvisioning`, `DontUseImpiForImsi`,
  `EnableUnprovisionnedIMSIRemediation`;
- `kSubscriberImsi/Mcc/Mnc/Iccid/IsEsim/SimTrayStatus`,
  `SIM2GID1`, `SIM2GID2` (GID1/GID2-ключи матчинга);
- `kCarrierBundleWatchBundleMatchCriteria` — подписка на критерии match.

Это подтверждает, что CommCenter **реализует** многоуровневый match:
точный IMSI → префикс/GID/SPN → MCC/MNC → default bundle. Существование
`IMSIOverride` и `AllowedIMSIPrefixes` показывает, что IMSI-алиасы —
**штатный, поддерживаемый механизм** матчинга, а не побочный эффект.

## 4. Что остаётся недоказанным

- Тело `copyCarrierBundleValue`/match-функции живёт в
  `CarrierBundleUtilities.dylib` (недоступна) → точный порядок
  приоритета IMSI-vs-MCCMNC-vs-GID и код записи в кэш не виден.
- IPCC как источник IMSI-alias: `INSUFFICIENT EVIDENCE` — ни «может», ни
  «не может» не доказано (нет IPCC-инсталлера device-side).
- Привязка match к зашифрованному `.dyldlinkedit` символам невозможна.

## 5. Статус

- Механизм IMSI-alias в CarrierSIM: **CONFIRMED** (симлинк, код).
- IMSI→bundle match реализован в CommCenter: **CONFIRMED**
  (`copyMCCMNCFromIMSI`, `AllowedIMSIPrefixes`, `kSubscriber*`,
  `kCarrierBundleWatchBundleMatchCriteria`).
- IMSI-алиасы — поддерживаемый механизм match: **SUPPORTED** (`IMSIOverride`,
  `AllowedIMSIPrefixes`, `EnableIMSISwitch`).
- Точный приоритет match и IPCC-путь: **INSUFFICIENT EVIDENCE**
  (нужна `CarrierBundleUtilities.dylib`).
