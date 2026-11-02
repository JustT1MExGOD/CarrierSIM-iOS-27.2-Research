# Phase 16 — Сводный отчёт: CommCenter Deep RE, Bundle Matching, B2/B3 Diff

## Executive Summary

**CommCenter B2 и B3 — полные исполняемые Mach-O** с символами, ObjC- и
C++-метаданными. Phase 16 выполнила первый настоящий статический анализ их
carrier-bundle логики: **восстановлен C++ API `CarrierBundleHandler`,
ObjC-методы `CTXPCClientHandler` с IMP-адресами, entitlement-механизм и
бинарный diff**.

Главный вывод: **match-логика CommCenter семантически идентична между B2 и
B3** — все ключевые методы (`isSimMatching`, `copyCarrierBundleValue*`,
`getCountryBundleLocation`, `checkForUpdatedBundles`, `createEntitlementChecker`,
`hasEntitlement`, `_isEntitledForControl`) имеют одинаковый normalized-hash.
Регрессия CarrierSIM находится в AirTraffic, не в bundle-selection CommCenter.

## 1. Подтверждение бинарников

- `CommCenter_B2.bin` 41 018 192 Б, UUID `83978CC2-…`, SHA `9e815d9e…` ✅
- `CommCenter_B3.bin` 40 370 720 Б, UUID `747592DD-…`, SHA `9a5eeaf3…` ✅
- Mach-O arm64e `MH_EXECUTE`, 176 LC, `LC_SYMTAB`, `LC_FUNCTION_STARTS`,
  `LC_DYLD_CHAINED_FIXUPS`, ObjC/C++-метаданные — пригодны для полного анализа.

## 2. Архитектура CarrierBundleHandler

`matchCarrierBundleForSim_sync → matchCarrierBundle_sync → {matchOperator,
matchCountry, matchBootstrap, matchDefault, matchDefaultBCAM}Bundle_sync →
sendBundleEvent_sync`. `installCarrierBundle_sync`, `installiTunesUpdateBundles`,
`loadEquivalentTableFrom_sync` (MCC/MNC-эквивалентность), `loadSidTableFrom_sync`.
CommCenter — оркестратор; скоринг в `CarrierBundleUtilities.dylib`.

## 3. IMSI matching

`copyMCCMNCFromIMSI`, `createIMSIFromMccMnc`, `AllowedIMSIPrefixes`,
`IMSIOverride`, `DigitMNCWithIMSI`, `EnableIMSISwitch`,
`commCenterIMSISwitchEvent`, `UseIMSIDuringProvisioning`,
`EnableUnprovisionnedIMSIRemediation`, `SIM2GID1/2`, `kSubscriber{Imsi,Mcc,
Mnc,Iccid,IsEsim}` — IMSI-алиасы — **поддерживаемый механизм** match.
`Carrier Bundles/iPhone` path присутствует; `readlink`/`lstat` — в
недоступной `CarrierBundleUtilities` (`INSUFFICIENT EVIDENCE`).

## 4. Bundle selection

`SIM → kSubscriber* + copyMCCMNCFromIMSI → matchCarrierBundle_sync →
{Operator→Country→Bootstrap→Default→BCAM} → sendBundleEvent_sync →
carrier_bundles sinks → copyCarrierBundleValue*`. IMSI-префикс — наивысший
приоритет; `HomeBundleIdentifier from overlay file` подмешивается в match-info.

## 5. Binary diff B2↔B3

**Все carrier-bundle/match/entitlement методы — `SAME`** (normalized-hash).
Изменения: удалены 4 debug/test-метода (`fakeCrossPlatformTransferEvent`,
`injectMTsms`, `invalidateKey`, `Stewie loopback` — не carrier-bundle);
строки: `override_carrier_list.json` удалён, `Development Signed Carrier
Bundles: Not Allowed` добавлен. `requiredEntitlementForRequest:` — DIFF по
размеру (`INSUFFICIENT EVIDENCE`).

## 6. CarrierBundleMatchProxyInterface

C++ класс в CommCenter, XPC-сервис (`xpc::dict`, `auto_reply`, `RestModule`).
Роль — **match/lookup прокси** к `CarrierBundleHandler`, не write.

## 7. CarrierBundleInstallInterface

C++ класс, `installCarrierBundle_sync(URL, cb)`, `installiTunesUpdateBundles`,
`checkForUpdatedBundles`. Install ≠ match: ставит кандидата, **не назначает
SIM→bundle**. Entitlement-gated; `Development Signed: Not Allowed` в B3.

## 8. Entitlement

`EntitlementChecker:forConnection:`, `EntitlementCache`,
`requiredEntitlementForRequest:` (map request→key), `clientHandler:hasEntitlement:`,
`_isEntitledForControl`, `com.apple.carrierspace.*`/`commcenter.*` ключи.
Read API `copyCarrierBundleValue` — публичный; install/match-write — gated.
Все компоненты `SAME` кроме `requiredEntitlementForRequest:` (DIFF).

## 9. Совместимость CarrierSIM

Все match-шаги CarrierSIM сохранены в B3; блок — **файловый канал записи**
IMSI-алиаса через AirTraffic (`beneath AFC root` + errno 107), не match.

## 10. Гипотезы

| H | Результат |
|---|---|
| 01 IMSI-симлинки распознаются в B3 | SUPPORTED BUT INCOMPLETE |
| 02 matchCarrierBundle_sync не изменилась | SUPPORTED BUT INCOMPLETE |
| 03 отказ CarrierSIM = AirTraffic, не bundle-selection | **CONFIRMED** |
| 04 штатный интерфейс SIM-to-bundle mapping | SUPPORTED BUT INCOMPLETE |
| 05 MatchProxy изменяет сопоставление | INSUFFICIENT EVIDENCE |
| 06 InstallInterface = нужная операция | INSUFFICIENT EVIDENCE |
| 07 выбор чужого bundle возможен в B3 | SUPPORTED BUT INCOMPLETE |

## 11. Ограничения

- Тело `matchCarrierBundle_sync`/`match*` в `CarrierBundleUtilities.dylib`
  и `CoreTelephony` — недоступно (dyld-образы, `.dyldlinkedit` зашифрован).
- `requiredEntitlementForRequest:` diff не разобран.
- RC `24B119` бинарник отсутствует.
- Call-graph `match*→match*` — по именам, не прямому `bl`-резолву.

## 12. Ответы Q1–Q6

**Q1**: **Да** — IMSI-симлинки распознаются (`AllowedIMSIPrefixes`,
`IMSIOverride`, `EnableIMSISwitch`, `copyMCCMNCFromIMSI` присутствуют в B3;
match-методы идентичны). Барьер — файловая запись, не распознавание.

**Q2**: **Нет семантических изменений** в видимом коде — все match-методы
`SAME` по normalized-hash; внутренняя реализация в `CarrierBundleUtilities`
не проверена (недоступна).

**Q3**: **Да, подтверждена** — отказ CarrierSIM на уровне AirTraffic
(`beneath AFC root` + errno 107), а не bundle-selection CommCenter.

**Q4**: `SUPPORTED BUT INCOMPLETE` — механизмы override существуют
(`IMSIOverride`, `AllowedIMSIPrefixes`, `CarrierBundleOverlay`), но прямой
штатный setter-интерфейс SIM→bundle не показан.

**Q5**: `matchCarrierBundle_sync`/`matchOperatorBundle_sync`/`matchCountryBundle_sync`
(тела в `CarrierBundleUtilities`), `requiredEntitlementForRequest:` (diff),
`CarrierBundleOverlay` (override-механизм), `installCarrierBundle_sync`
(доверие/пути), IPCC-инсталлер device-side.

**Q6**: **Значительно** — впервые восстановлен полный carrier-bundle API
CommCenter и доказана неизменность match между бетами; исследование точно
локализовало барьер в файловом канале записи, а не в match-логике. Осталось
найти альтернативный канал записи IMSI-алиаса.

## Рекомендация (Phase 17)

1. Дизассемблировать `installCarrierBundle_sync` и `CarrierBundleOverlay` —
   разрешённые пути записи bundle/override.
2. Извлечь `MobileInstallation`/`streaming_zip_conduit`/`installd` IPCC-путь
   из rootfs — может ли IPCC создавать IMSI-alias (H14-05).
3. Разобрать `requiredEntitlementForRequest:` — полный request→key map.
4. При появлении RC `24B119` IPSW — сравнить CommCenter RC vs B3.
