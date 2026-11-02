# Phase 16 · Отчёт 12 — Результаты гипотез H16-01…H16-07

## 1. Метод

Каждая гипотеза проверена по восстановленному `CommCenter_B2.bin`/
`CommCenter_B3.bin`: ObjC method-IMPs, C++ mangled-имена, normalized
mnemonic-hash diff, строковые ключи. Статусы: `CONFIRMED`,
`SUPPORTED BUT INCOMPLETE`, `INSUFFICIENT EVIDENCE`, `RULED OUT`.

## 2. Таблица

| Гипотеза | За | Против | Недостаёт | Статус | Уверенность |
|---|---|---|---|---|---|
| **H16-01**: B3 продолжает распознавать IMSI-симлинки | `copyMCCMNCFromIMSI`, `AllowedIMSIPrefixes`, `IMSIOverride`, `EnableIMSISwitch`, `Carrier Bundles/iPhone` path — все присутствуют в B3; match-методы идентичны | — | конкретный `readlink`/`lstat` внутри `CarrierBundleUtilities` | **SUPPORTED BUT INCOMPLETE** | высокая |
| **H16-02**: `matchCarrierBundle_sync` не претерпела существенных изменений | все match-методы (`isSimMatching`, `copyCarrierBundleValue*`, `getCountryBundleLocation`, `checkForUpdatedBundles`) — normalized-hash **SAME** | `requiredEntitlementForRequest:` DIFF — но это provider, не match | тело `matchCarrierBundle_sync` в `CarrierBundleUtilities` | **SUPPORTED BUT INCOMPLETE** (по видимому коду — идентична; внутренняя реализация недоступна) | средне-высокая |
| **H16-03**: отказ CarrierSIM обусловлен AirTraffic, не bundle-selection | match-код CommCenter идентичен; AirTraffic B3 `beneath AFC root`+errno 107 доказан; IMSI-логика не менялась | — | — | **CONFIRMED** | высокая |
| **H16-04**: существует штатный интерфейс управления SIM-to-bundle mapping | `IMSIOverride`, `AllowedIMSIPrefixes`, `CarrierBundleOverlay` (`Added HomeBundleIdentifier`), `ctu::rest` `carrier_bundles`/`operator_bundles`/`default_bundle` sinks | нет прямого «set mapping» метода | конкретный setter-интерфейс | **SUPPORTED BUT INCOMPLETE** — механизмы override существуют, штатный API не показан | средняя |
| **H16-05**: `CarrierBundleMatchProxyInterface` изменяет сопоставление | XPC-интерфейс существует | роль — match/lookup (прокси к handler), не write; нет setter-методов | vtable/методы | **INSUFFICIENT EVIDENCE** (скорее «нет» — прокси match, не запись) | средняя |
| **H16-06**: `CarrierBundleInstallInterface` поддерживает нужную операцию через разрешённый workflow | `installCarrierBundle_sync(URL, cb)`, `installiTunesUpdateBundles`, `checkForUpdatedBundles` | install ≠ match-mapping: ставит кандидата, не назначает SIM→bundle; entitlement-gated; `Development Signed: Not Allowed` B3 | доказательство, что install меняет SIM-маппинг | **INSUFFICIENT EVIDENCE** (install не является mapping-операцией) | средняя |
| **H16-07**: выбор чужого подписанного bundle остаётся возможным в B3 | IMSI-алиасы/`IMSIOverride`/`AllowedIMSIPrefixes` существуют; match не менялся; bundle-selection отделена от подписи пакета | файловый канал записи alias закрыт (AirTraffic); dev-signed install запрещён | путь записи IMSI-alias без AirTraffic | **SUPPORTED BUT INCOMPLETE** — технически match поддерживает, канал записи закрыт | средне-высокая |

## 3. Сводка

- **CONFIRMED**: H16-03 — регрессия в AirTraffic, не в bundle-selection.
- **SUPPORTED BUT INCOMPLETE**: H16-01, H16-02, H16-04, H16-07 — механизм
  IMSI-маппинга жив, match не изменился, но конкретная файловая резолюция
  и штатный setter не доказаны.
- **INSUFFICIENT EVIDENCE**: H16-05, H16-06 — proxy/install интерфейсы
  не показаны как write-каналы mapping.
- **RULED OUT**: нет — ни одна гипотеза не опровергнута окончательно;
  наиболее близко к опровержению H16-05/H16-06 (не write-каналы).

## 4. Главный технический вывод

CarrierSIM несовместим с B3+ **не из-за изменения IMSI/bundle-match в
CommCenter, а из-за закрытия файлового канала записи IMSI-алиаса через
AirTraffic**. Для восстановления нужен либо (а) альтернативный канал записи
в `/var/mobile/Library/Carrier Bundles/iPhone`, либо (б) штатный механизм
изменения match-criteria — оба пока `INSUFFICIENT EVIDENCE`.
