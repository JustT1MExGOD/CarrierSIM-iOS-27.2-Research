# Phase 17 — Итоговый отчёт: CommCenter Authorization Diff, CarrierBundleOverlay & HomeBundleIdentifier

## 1. Объём работ

Проанализированы `CommCenter_B2.bin` (iOS 27.2 Beta 2, `24B5089g`, UUID `83978CC2-2FEC-36B0-A77C-B9A90ED9C28C`, SHA-256 `9e815d9e…b2a60`) и `CommCenter_B3.bin` (iOS 27.2 Beta 3, `24B5099f`, UUID `747592DD-284C-37BC-AE32-0FE36E8CB3DA`, SHA-256 `9a5eeaf3…57d2`). Извлечены и сравнены таблицы `requiredEntitlementForRequest:` (B2: 307 записей/302 paired; B3: 305/300), восстановлен overlay-pipeline, проведён семантический diff авторизации carrier-bundle операций.

## 2. Что изменилось в requiredEntitlementForRequest:

Различия: удалены `injectMTsms` и `invalidateKey`; добавлен `addParticipants:toGroupChat:…`. `bootstrapQuickSwitchEnrollmentFlowAsSecondary` имеет одинаковый код 25 в обеих версиях (ранее отмеченная разница снята как артефакт чтения смещения). Все carrier-bundle коды **идентичны**; общих записей с изменённым кодом нет.

## 3. Матрица авторизации

Carrier-bundle операции (чтение значений, локация, идентификатор, версия) требуют коды 1 и 3; `restoreToSystemBundles` — 19; `setTestBundleIdForSlice` — 14. Изменений между B2 и B3 нет. Полный список — в `03_AUTHORIZATION_MATRIX.md`.

## 4. Реализация CarrierBundleOverlay

C++ value-type; pipeline: путь → CFDictionary → ключи → `overlay matching info` → SupportedSIM gate → `HomeBundleIdentifier` → `matchCarrierBundle_sync`. Точный источник файла не установлен; writer — системный mobile helper. Подробности — `04_OVERLAY_IMPLEMENTATION.md`.

## 5. HomeBundleIdentifier

Строковый ключ matching-info, извлекаемый из overlay-dict и передаваемый matcher'у как критерий best-match. Это **metadata enrichment**, не bundle override. Доказательство произвольного назначения чужого bundle отсутствует. См. `05_HOME_BUNDLE_IDENTIFIER.md`.

## 6. Формат и доверие overlay

CFDictionary с IMSI-записями, `SupportedSIM`, `HomeBundleIdentifier`, классами k*Overlay. Внутри CommCenter проверка подписи overlay не найдена; генерация — системными helper'ами. См. `06_OVERLAY_FORMAT_AND_TRUST.md`.

## 7. Поток overlay → выбор

`Источник → разбор dict → matching-info +HBI → matchCarrierBundle* → sendBundleEvent_sync`. Overlay влияет на выбор как входной критерий через SupportedSIM/MVNO-гейты. См. `07_OVERLAY_TO_SELECTION_FLOW.md`.

## 8. B2/B3 diff по overlay

Механизм сохранён полностью; единственные отличия — удалён `override_carrier_list.json` (B2-only, назначение не восстановлено) и реформатирован лог HBI. Новых ограничений и новых API в B3 нет. См. `08_OVERLAY_VERSION_DIFF.md`.

## 9. Релевантность CarrierSIM

Overlay **не заменяет** CarrierSIM: другой механизм (matching-info vs symlink), нет внешнего API создания, SupportedSIM ограничивает применение, нет доказательства произвольного назначения bundle. См. `09_CARRIERSIM_RELEVANCE.md`.

## 10. Гипотезы

| Гипотеза | Статус |
|---|---|
| H17-01 (B3 изменил auth для carrier-bundle) | НЕ ПОДТВЕРЖДЕНА |
| H17-02 (HBI = произвольный override) | НЕ ПОДТВЕРЖДЕНА |
| H17-03 (внешний клиент создаёт overlay) | НЕ ПОДТВЕРЖДЕНА |
| H17-04 (overlay обходит подпись) | НЕ ПОДТВЕРЖДЕНА |
| H17-05 (новый путь в B3) | НЕ ПОДТВЕРЖДЕНА |
| H17-06 (overlay влияет на scoring) | ЧАСТИЧНО (как вход) |
| H17-07 (независимая подпись overlay) | НЕ ПОДТВЕРЖДЕНА |

## 11. Аудит

Проверены адреса, структура таблиц, reachable code для строк, разделение enrichment/selection/override. Главные ограничения: `CarrierBundleUtilities.dylib` тело недоступно; `matchCarrierBundle_sync` IMP не разрешён; источник overlay не установлен. См. `11_INDEPENDENT_AUDIT.md`.

## 12. Ответы на вопросы

**Q1. Что изменилось в `requiredEntitlementForRequest:`?**
Набор sel'екторов: удалены `injectMTsms`/`invalidateKey`, добавлен `addParticipants:toGroupChat:…` (B3). Изменённых кодов у общих записей нет — `bootstrapQuickSwitchEnrollmentFlowAsSecondary` имеет код 25 в обеих. Семантика записи таблицы не изменилась.

**Q2. Затрагивают ли изменения carrier-bundle операции?**
**Нет.** Все carrier-bundle entitlement-коды идентичны B2/B3.

**Q3. Откуда загружается CarrierBundleOverlay?**
Из файла по пути (`Using overlay file path`), разбираемого как CFDictionary. Генерируется системным mobile helper'ом; точный компонент и путь **не установлены**.

**Q4. Может ли HomeBundleIdentifier влиять на выбор bundle?**
Да — как критерий в matcher (`Matches for the given HomeBundle Identifier`), внутри ограничений SupportedSIM и fallback'ов (`No match for overlay`). Это влияние на приоритет, не прямое назначение.

**Q5. Существует ли поддерживаемый механизм обновления overlay?**
Системный writer существует (`Error writing overlay file`, mobile helper, `Clearing Overlay files`); пользовательский/внешний API обновления **не найден**.

**Q6. Появился ли новый путь восстановления CarrierSIM?**
**Нет.** Overlay — не symlink-механизм; регрессия B3 (`107 ENOTCAPABLE`) — в AirTraffic write path, вне overlay. Новых компенсирующих механизмов в B3 не обнаружено.

**Q7. Единственный наиболее полезный следующий шаг?**
Извлечь `CarrierBundleUtilities.dylib` из dyld-кэша cryptex (DMG `141-56439`) и восстановить scoring-функцию `matchCarrierBundle_sync` — единственный компонент, где виден реальный вес `HomeBundleIdentifier` при выборе bundle. Без него вопрос «подсказка vs override» окончательно не закрыть.
