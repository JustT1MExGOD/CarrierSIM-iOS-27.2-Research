# Phase 18 · Отчёт 09 — Сравнение Beta 2 и Beta 3 (matcher)

## 1. Метод и ограничение

Прямой binary-diff `matchCarrierBundle_sync`/CBU **невозможен**: B3
`CarrierBundleUtilities` недоступен (dataless subcache), `matchCarrierBundle_sync`
IMP не разрешён. Diff проведён по **импортам, строкам, entitlement-кодам и
функциональной инвентаризации** — семантический уровень, не побайтовый.

## 2. IMSI lookup / alias resolution

| Элемент | B2 | B3 | Классификация | Влияние на CarrierSIM |
|---|---|---|---|---|
| `_readlink` import | есть | есть | без изменений | matcher читает симлинк |
| `_realpath` import | есть | есть | без изменений | — |
| `_lstat` import | есть | есть | без изменений | проверка типа записи |
| `BundleLinks` | `0x1021e2820` | есть | без изменений | каталог симлинков |
| `eIMSI config subfolder matching` | есть | есть | без изменений | eIMSI/IMSI-подкаталог |
| `BCAM eIMSI config subfolder` | есть | есть | без изменений | BCAM вариант |

**Вывод**: IMSI-alias resolution присутствует в обеих версиях без изменений.

## 3. Candidate matching / selection

- `matchCarrierBundle_sync`, `match{Operator,Country,Bootstrap,Default,DefaultBCAM}Bundle_sync` — набор имён идентичен; IMP не разрешён → семантический diff недоступен.
- Carrier-bundle entitlement-коды в `requiredEntitlementForRequest:` — идентичны (Phase 17).

## 4. Overlay integration

| Элемент | B2 | B3 | Статус |
|---|---|---|---|
| `HomeBundleIdentifier` | `0x102144d50` | `HomeBundleIdentifier = '%s'` | реформат |
| overlay machinery | все строки | все строки | сохранён |
| `override_carrier_list.json` | есть | **нет** | удалено (B2-only) |

## 5. Bundle validation (CBU)

- B2 CBU `__text`: signature/version.xml/PRI — полный движок.
- B3 CBU: недоступен → diff невозможен. По аналогии с CommCenter (там всё сохранено) семантических изменений не ожидается, но **не доказано**.

## 6. Cache handling

`already cached, returning cached` — в обеих версиях.

## 7. Что реально изменилось (для CarrierSIM)

| Изменение | Локация | Эффект |
|---|---|---|
| `107 ENOTCAPABLE` на записи | AirTraffic/AFC write path | **блокирует создание симлинка** — точка отказа |
| `injectMTsms`, `invalidateKey` | CommCenter req-map | удалены (не carrier-bundle) |
| `override_carrier_list.json` | CommCenter strings | удалён |
| IMSI matching / read path | CommCenter | **не изменён** |

## 8. Вывод

Между B2 и B3 **нет семантических изменений matcher**, влияющих на CarrierSIM.
Единственная регрессия — **запись симлинка** (AirTraffic), не чтение/match.
CarrierSIM теоретически совместим, если симлинк создать другим путём —
но Phase 18 не исследует обход записи.
