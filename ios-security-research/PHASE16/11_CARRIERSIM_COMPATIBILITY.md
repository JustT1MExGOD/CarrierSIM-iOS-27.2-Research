# Phase 16 · Отчёт 11 — Совместимость исторического CarrierSIM

## 1. Назначение документа

Сопоставление шагов CarrierSIM с реальным кодом CommCenter B2/B3 и
доказательствами работоспособности механизма.

## 2. CarrierSIM механизм (по `carrier.py`, уровень A)

1. Читает SIM-идентификаторы (IMSI 15-зн.).
2. Строит `desired` каталог: `desired[imsi] = ('l', path_to_bundle)`.
3. Записывает каталог через **AirTraffic** asset-последовательность
   `[staging-link, export-catalog, write-catalog]` в
   `/var/mobile/Library/Carrier Bundles/iPhone`.
4. Создаёт IMSI-симлинк `…/iPhone/<IMSI>` → `…/iPhone/<bundle>.bundle`.
5. Инициирует IPCC-рескан (`_upload_ipcc` → AFC zip) для обновления match.

## 3. Сопоставление шагов с CommCenter

| Шаг CarrierSIM | Функция CommCenter | B2 | B3 | Доказательство |
|---|---|---|---|---|
| Получение идентификаторов SIM | `kSubscriber{Imsi,Mcc,Mnc,Iccid,IsEsim}` | ✓ | ✓ | символы+ключи |
| Поиск IMSI-привязки | `copyMCCMNCFromIMSI`, `AllowedIMSIPrefixes`, `IMSIOverride`, `createIMSIFromMccMnc` | ✓ | ✓ | символы |
| Разрешение симлинка `/var/mobile/…/iPhone/<IMSI>` | `Carrier Bundles/iPhone` path + match через `CarrierBundleUtilities` | SUPPORTED | SUPPORTED | path есть; `readlink`/`lstat` конкретно — в недоступной библиотеке |
| Выбор Vodafone bundle | `matchOperatorBundle_sync`/`matchCountryBundle_sync` | ✓ | ✓ | методы |
| Проверка bundle | `matchCarrierBundle_sync` + validation (`matching info is invalid`) | ✓ | ✓ | методы+строки |
| Применение настроек | `sendBundleEvent_sync` + `carrier_bundles` sinks | ✓ | ✓ | методы+символы |
| IPCC-рескан | `installCarrierBundle_sync`/`checkForUpdatedBundles` | ✓ | ✓ | методы |

## 4. Где CarrierSIM реально блокируется

Сопоставление показывает: **все match-шаги CarrierSIM сохранились** в B3 —
`matchCarrierBundle_sync`, IMSI-логика, IMSI-алиасы, entitlement-механизм
идентичны по normalized-hash.

Блок находится **не** на этапе match, а на этапе **записи** в
`/var/mobile/Library/Carrier Bundles/iPhone` — AirTraffic `move completed-
asset` теперь требует `open()` AFC-root + `mkdir beneath` + возвращает
`errno 107`/`ENOTCAPABLE`. Это файловый барьер **перед** match, не в нём.

## 5. Ключевой вывод

| Что | Статус |
|---|---|
| IMSI-алиасы как механизм | **работают** (`AllowedIMSIPrefixes`, `IMSIOverride`, `EnableIMSISwitch`) |
| Match-логика CommCenter | **идентична** B2↔B3 |
| Файловый канал записи каталога | **закрыт** в B3 (AirTraffic `beneath AFC root` + errno 107) |
| Альтернативный канал записи | **INSUFFICIENT EVIDENCE** — IPCC-путь не показан как способ создания IMSI-alias |

CarrierSIM перестал работать **не потому что CommCenter перестал
распознавать IMSI-симлинки, а потому что AirTraffic перестал их записывать**.
