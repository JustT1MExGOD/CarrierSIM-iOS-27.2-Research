# Phase 15 · Отчёт 12 — Решение о следующей фазе

## 1. Назначение документа

На основании того, что Phase 15 восстановила (`CommCenter` B2+B3) и что
осталось недоступным (`CarrierBundleUtilities.dylib`, `CoreTelephony`,
расшифрованный `.dyldlinkedit`), определить рациональный следующий шаг.

## 2. Состояние после Phase 15

**Достигнуто (уровень A):**
- `CommCenter` B2 и B3 восстановлены полностью из main rootfs.
- Доказаны: владелец `CarrierBundle*Interface` = CommCenter; XPC-транспорт;
  entitlement-механизм (`EntitlementChecker`); IMSI-match логика
  (`copyMCCMNCFromIMSI`, `AllowedIMSIPrefixes`, `IMSIOverride`,
  `matchCarrierBundle_sync`, `matchDefaultBundle_sync`,
  `matchDefaultBCAMBundle_sync`, `handleSIMCarrierInfo_sync`);
  удаление `override_carrier_list.json` и добавление
  `Development Signed Carrier Bundles` в B3.

**Не достигнуто:**
- Тело `CarrierBundleUtilities.dylib` и `CoreTelephony` (dyld-образы).
- Точный приоритет IMSI-vs-MCCMNC-vs-GID-vs-default match.
- IPCC-путь как источник IMSI-alias (`INSUFFICIENT EVIDENCE`).
- Конкретные entitlement-ключи на каждый `CarrierBundle*Interface`.
- RC `24B119` бинарники (нет IPSW).

## 3. Варианты следующей фазы

### Вариант A — деcompиляция CommCenter (рекомендуется)
Дизассемблировать/декомпилировать `CommCenter_B3.bin` (и diff с B2):
- восстановить `CarrierBundleHandler::matchCarrierBundle_sync` —
  точный порядок match и где применяется IMSI-alias;
- разобрать `EntitlementChecker:forConnection:` — конкретные ключи
  (`com.apple.carrierspace.*`, `com.apple.commcenter.*`);
- найти обработчик `kCarrierBundleTriggerInstallCarrierBundle` —
  разрешённые входы и валидация.
- **Требуется**: только Ghidra/IDA/capstone + уже извлечённый файл. Всё
  локально доступно. **Наибольшая польза без новых источников.**

### Вариант B — восстановление CarrierBundleUtilities.dylib
Нужен расшифрованный `.79.dyldlinkedit` или rootfs-раздел cache.
Локально недостижимо (зашифрованные cryptex-экстенты, нет IPSW).
**Отложено** до появления источника.

### Вариант C — IPCC-инсталлер device-side
Извлечь `MobileInstallation`/`streaming_zip_conduit` из rootfs
(тот же метод `probe_catbin`) и проверить, может ли IPCC-путь писать
произвольные IMSI-alias. **Возможно** — rootfs доступен. Средняя польза:
закроет H14-05.

### Вариант D — RC `24B119` CommCenter
Нужен IPSW RC — запрещено скачиванием. **Отложено.**

## 4. Рекомендация

**Phase 16 = вариант A (+C по возможности).** Дизассемблирование
`CommCenter_B3.bin`/`CommCenter_B2.bin` — единственный путь, дающий новые
доказательства уровня A без новых источников: match-алгоритм,
entitlement-ключи и обработчик Install-триггера. Параллельно извлечь
`MobileInstallation`/`streaming_zip_conduit` из rootfs для H14-05.
