# Phase 15 — Сводный отчёт: восстановление бинарников и коррекция доказательств

## Решающий результат

**Phase 15 восстановила настоящий исполняемый `CommCenter` для Beta 2 и
Beta 3** — цель, считавшаяся недостижимой в Phase 14. Оба образа извлечены
из main rootfs (`141-56668`) через `dpp probe_catbin`, где экстенты файлов
не зашифрованы (j_type 8), в отличие от cryptex.

| Образ | Размер | UUID | SHA-256 |
|---|---|---|---|
| `CommCenter_B2.bin` | 41 018 192 | `83978CC2-2FEC-36B0-A77C-B9A90ED9C28C` | `9e815d9e…` |
| `CommCenter_B3.bin` | 40 370 720 | `747592DD-284C-37BC-AE32-0FE36E8CB3DA` | `9a5eeaf3…` |

Оба — Mach-O arm64e `MH_EXECUTE` (PAC), 176 load commands, полные сегменты.
Это подняло carrier-bundle анализ с уровня B (строки) до уровня A
(реальные C++ классы, XPC-прототипы, ObjC-селекторы).

## Что доказано уровнем A (новое)

1. **`CarrierBundle*Interface` принадлежат CommCenter** — C++ mangled-
   классы `*InterfaceD2Ev`/`EEE` в обоих образах; обработчики через XPC
   (`xpc::dict`, `auto_reply`, `ctu::RestModule`, `dispatch::queue`).
   Раньше было «INSUFFICIENT» → теперь **CONFIRMED**.
2. **CommCenter потребляет `CarrierBundleUtilities.dylib`** —
   `LC_LOAD_DYLIB /usr/lib/CarrierBundleUtilities.dylib` в load commands.
3. **IMSI→bundle match реализован в CommCenter** — `copyMCCMNCFromIMSI`,
   `createIMSIFromMccMnc`, `AllowedIMSIPrefixes`, `IMSIOverride`,
   `DigitMNCWithIMSI`, `CarrierBundleHandler::match{CarrierBundle,Default,
   DefaultBCAM,Bootstrap}Bundle_sync`, `BasebandSettings::handleSIMCarrierInfo_sync`,
   `kCarrierBundleWatchBundleMatchCriteria`, `kSubscriber{Imsi,Mcc,Mnc,Iccid,IsEsim,SIM2GID1,SIM2GID2}`.
4. **Entitlement-механизм существует** — `EntitlementChecker:forConnection:`,
   `EntitlementCache`, `EntitlementController`, `com.apple.carrierspace.control.allow`.
5. **B2→B3 изменения в CommCenter**: `override_carrier_list.json`
   присутствует только в B2 (удалён); `Development Signed Carrier Bundles:
   Not Allowed` — только в B3 (добавлен контроль dev-signed).
   Все carrier-bundle/IMSI символы присутствуют с идентичными счётчиками —
   **match-логика не менялась между бетами** (регрессия CarrierSIM была в
   AirTraffic, не в CommCenter).

## Ответы на вопросы Q1–Q6

**Q1 — удалось ли восстановить настоящий исполняемый `CommCenter`?**
Да. `CommCenter_B2.bin` (41 018 192 Б) и `CommCenter_B3.bin` (40 370 720 Б)
извлечены из main rootfs с UUID и SHA-256. Полные Mach-O со всеми сегментами.
Это главный результат Phase 15.

**Q2 — восстановлена ли `CarrierBundleUtilities.dylib`?**
Частично: **доказано существование** (install-name в cache + `LC_LOAD_DYLIB`
в CommCenter), но исполняемый образ не восстановлен — это dyld-образ, чьи
`.dyldlinkedit`/границы зашифрованы в cryptex. Standalone-файла ни в rootfs,
ни в cryptex нет. Статус `SUPPORTED BUT INCOMPLETE`.

**Q3 — кто владеет `CarrierBundle*Interface`?**
**CommCenter** (CONFIRMED). C++ классы найдены в CommCenter; обработчики —
XPC (`xpc::dict`/`auto_reply`). Чрезмерная строковая гипотеза Phase 14
теперь доказана кодом.

**Q4 — защищены ли интерфейсы entitlement?**
`SUPPORTED BUT INCOMPLETE`. `EntitlementChecker:forConnection:`,
`EntitlementCache`, `EntitlementController`, `com.apple.carrierspace.*`
существуют как классы/строки; конкретный ключ на каждый интерфейс не разобран
(требуется декомпиляция — Phase 16).

**Q5 — может ли штатный механизм назначить SIM A чужой bundle B?**
`INSUFFICIENT EVIDENCE`. IMSI-алиасы — **поддерживаемый** механизм CommCenter
(`IMSIOverride`, `AllowedIMSIPrefixes`, `EnableIMSISwitch`), но device-side
код официального назначения чужого bundle не показан; операторская
конфигурация и IPCC-путь не исключены.

**Q6 — корректен ли Phase 11 extractor?**
Да. `extract_flat.py` устранил дефект Phase 10 (компактная упаковка,
переписанные `fileoff`, сохранённые `vmaddr`); извлечённые `amfid`/`installd`/
`atc` дали воспроизводимый дизассемблер; пустота `.dyldlinkedit` — ограничение
источника, не дефект extractor.

## Скорректированные гипотезы

| Гипотеза | Было | Стало |
|---|---|---|
| H14-01 internal CommCenter API | строки | **CONFIRMED** |
| H14-02 entitlement-gated | предположение | **SUPPORTED BUT INCOMPLETE** |
| H14-03 IMSI-alias только через Catalog | сильная формулировка | **SUPPORTED BUT INCOMPLETE** |
| H14-04 CommCenter резолвит IMSI | предположение | **CONFIRMED** |
| H14-05 штатное назначение чужого bundle | «нет» | **INSUFFICIENT EVIDENCE** |
| H14-06 AirTraffic B3/RC блокирует запись | выдвинута | **CONFIRMED** |

## Оставшийся барьер

`CarrierBundleUtilities.dylib` и `CoreTelephony` — dyld-образы; их тела и
точный match-приоритет недоступны без расшифрованного `.79.dyldlinkedit`/
`.symbols` (cryptex-экстенты зашифрованы j_type 13, type-8 отсутствует,
LZFSE). RC `24B119` IPSW отсутствует.

## Рекомендация (Phase 16)

Дизассемблировать `CommCenter_B3.bin`/diff с B2 — match-алгоритм
`CarrierBundleHandler::matchCarrierBundle_sync`, entitlement-ключи
`EntitlementChecker`, обработчик `kCarrierBundleTriggerInstallCarrierBundle`.
Всё необходимое уже локально. Параллельно извлечь `MobileInstallation`/
`streaming_zip_conduit` из rootfs для H14-05.

## Файлы фазы

12 отчётов + `evidence_commcenter_match_strings.txt` + `CommCenter_B2.bin`,
`CommCenter_B3.bin` (у `C:\ipsw-tools\`).
