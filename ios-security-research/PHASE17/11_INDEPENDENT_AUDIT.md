# Phase 17 · Отчёт 11 — Независимый аудит доказательств

## 1. Цель

Проверить, не выводятся ли выводы Phase 17 из артефактов анализа (строки
без кода, неверные адреса, ошибки дизассемблера, смешение понятий).

## 2. Проверка адресов и ссылок

| Элемент | Проверка | Результат |
|---|---|---|
| `requiredEntitlementForRequest:` B2 `0x10000d374` | Таблица 309 записей, пары `str x?,[x8,#N]` + `str w?,[x8,#N+8]` | ПОДТВЕРЖДЕНО |
| `requiredEntitlementForRequest:` B3 `0x10000cf20` | Таблица 312 записей, та же структура | ПОДТВЕРЖДЕНО |
| Overlay-строки B2 | Адреса в `__TEXT.__cstring`, reachable через ADRP+LDR | ПОДТВЕРЖДЕНО |
| Overlay-строки B3 | Те же строки с новыми адресами | ПОДТВЕРЖДЕНО |
| `HomeBundleIdentifier` | `Added … to matching info` + `homeBundleIdentifierFromMatchInfo` | ПОДТВЕРЖДЕНО |

## 3. Проверка семантических утверждений

| Утверждение | Аудит | Вердикт |
|---|---|---|
| Carrier-bundle entitlement-коды не изменились | Проверены все carrier-bundle sel'екторы в `p17_*_entmap.txt`; значения 1/3/14/19 идентичны | ПОДТВЕРЖДЕНО |
| `requiredEntitlementForRequest:` diff — не carrier-bundle | Различия: `injectMTsms`, `invalidateKey`, `bootstrapQuickSwitchEnrollmentFlowAsSecondary`, `addParticipants:toGroupChat` — вне carrier-bundle | ПОДТВЕРЖДЕНО |
| `HomeBundleIdentifier` — не override | Нет строки/кода прямого назначения bundle; есть `No match for overlay` и `SupportedSIM` gate | ПОДТВЕРЖДЕНО |
| `Overlay active, not validating the SIMs` | Найдена в reachable коде; контекст — системный overlay, не пользовательский выбор | ПОДТВЕРЖДЕНО |
| `matchCarrierBundle_sync` IMP | Не разрешён через ObjC method_list (C++ метод); восстановлен по именам/строкам | B-level, не ошибка |

## 4. Возможные ошибки анализа

| Риск | Мера | Остаток |
|---|---|---|
| Строка без reachable кода | Использовались только строки с ADRP+XREF | `override_carrier_list.json` — строка есть, кода нет; помечено B2-only |
| Ошибка chained-fixup decode | `target = 0x100000000 + (raw & 0xffffffff)`; проверено на известных selref'ах | Низкий |
| Перепутаны class_ro_t/relative method_list | Разрешение через `baseMethods` + signed 32-bit offsets | Низкий |
| `__objc_methlist` как method_t | Не использовался; найдено, что это stub-table | Низкий |
| `matchCarrierBundle_sync` нет IMP | Отражено в отчётах как ограничение | Открыто |

## 5. Разделение понятий

- **Metadata enrichment** vs **Bundle selection** vs **Bundle override** —
  разделены в отчёте 05: `HomeBundleIdentifier` — enrichment, не override.
- **Bundle selection** vs **VoWiFi** — не смешивались; overlay относится к
  выбору bundle, не к VoWiFi-конфигурации напрямую.
- **Строки** vs **код** — для каждого вывода указано, доказано ли строкой
  (B-level) или строкой + контекстом (A-level).
- **Внутренний механизм** vs **пользовательский API** — overlay — внутренний;
  наличие строки не означает доступ из приложения.

## 6. Неразрешённые ограничения

- `CarrierBundleUtilities.dylib` тело недоступно — scoring не виден.
- `matchCarrierBundle_sync` IMP не разрешён — call-graph по именам.
- Точный путь/компонент создания overlay — не установлен.
- `override_carrier_list.json` — назначение не восстановлено.

## 7. Итог аудита

Все выводы Phase 17 основаны на строках с reachable code или на
количественном сравнении таблиц. Главная ошибка предыдущих фаз
(«есть строка → есть механизм для пользователя») исключена разделением
enrichment/selection/override и явным указанием UNKNOWN для источника
overlay.
