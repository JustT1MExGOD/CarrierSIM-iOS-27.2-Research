# Phase 16 · Отчёт 13 — Независимый аудит доказательств

## 1. Назначение документа

Критическая проверка методологии Phase 16: границы функций, идентификация
методов, ошибки декомпиляции, сопоставление B2/B3, интерпретация PAC,
неподтверждённые связи.

## 2. Границы функций

- `LC_FUNCTION_STARTS` декодирован ULEB128 → **135 481** функция B2 —
  корректно для `__TEXT` `0x2398000` (~7.3 инструкций/функцию в среднем,
  реалистично с учётом stubs/thunks).
- Граница функции = следующий function_start. Tail-call `b` вместо `bl+ret`
  корректно считается концом (последняя инструкция до следующего start).
- `restoreToSystemBundles` — метод есть в таблице, IMP резолвится; не попал
  в TOP-выборку diff из-за фильтра, а не из-за ошибки резолва.

## 3. Идентификация методов

- **ObjC-методы**: `class_ro_t.baseMethods` → relative method_list →
  selname через selref-slot (chained ptr `0x100000000+low32`) + IMP через
  `e+8+im`. Проверено на `setController:`/`remoteAlertHandle:`/`.cxx_*` —
  резолв корректный.
- **C++ методы**: mangled-имена `ZN20CarrierBundleHandler23match…` —
  `__func__`/lambda-имена для `std::function` и typeinfo, **не** адреса
  функций. `matchCarrierBundle_sync` IMP не резолвлен через selrefs
  (C++ вызов напрямую, не ObjC) — зафиксировано как ограничение.
- Ошибки: `__objc_methlist` сначала разобран неверно (это ObjC-stub
  dispatch-table, не method_t); исправлено.

## 4. Ошибки автоматической декомпиляции/диффа

- Normalized-hash по мнемонике+operand-types — **не** доказывает байтовую
  идентичность: одинаковая последовательность `bl`-мнемоник при разных
  таргетах даёт SAME-хеш, но разные вызовы. Поэтому diff считает методы
  семантически идентичными по **структуре**, а не по конкретным таргетам.
- `requiredEntitlementForRequest:` — DIFF по размеру (≥1000 insn обрезано
  по function-end boundary) — может быть как семантическим, так и
  компиляторным изменением; заявлено `INSUFFICIENT EVIDENCE`, не `DIFF`.

## 5. PAC-интерпретация

- `pacibsp`/`retab`/`braa`/`blraa` корректно распознаются Capstone.
- IMP-адреса в method_list — сырой offset от field, не PAC-tagged
  (verified: `imp_addr` резолвится в `__TEXT` и дизассемблируется в
  `pacibsp` prologue — валидный code).
- Indirect `br x16`/`blraa` через `__objc_stubs` резолвятся через selrefs,
  не трассировку — соответствует реальному ObjC dispatch.

## 6. Неподтверждённые связи

- `matchCarrierBundleForSim_sync` → `matchCarrierBundle_sync` call-graph —
  иерархия восстановлена по **имени и контексту** (`_sync`/`ForSim` naming,
  иерархия match-методов), не по прямому `bl`-резолву. Помечено уровнем B.
- `matchCarrierBundle_sync` → `match{Operator,Country,…}Bundle_sync` —
  логическая иерархия по именам, не по call-graph.
- `isSimMatching:` → `matchCarrierBundleForSim_sync` — предположение по
  семантике, не прямой `bl`.

## 7. Строки vs код

- IMSI-логика доказана **символами** (`copyMCCMNCFromIMSI`,
  `AllowedIMSIPrefixes`, `IMSIOverride`, `EnableIMSISwitch`) — это реальные
  имена функций/ключей в `__TEXT __const`/ObjC-метаданных, не просто
  совпадающие байты.
- `Development Signed Carrier Bundles: Not Allowed`, `override_carrier_list.json` —
  строки `__cstring`, а не инструкции — помечены уровнем B (присутствие/
  отсутствие в B3 доказано, семантика предполагается).
- `readlink`/`lstat`/`realpath` конкретно **не найдены** — заявлено
  `INSUFFICIENT EVIDENCE`, не «симлинки разрешаются».

## 8. Системные vs пользовательские полномочия

- `CTCarrierSpaceClientProxy::_isEntitledForControl` — carrierspace;
  `CTXPCServerEntitlementProvider::requiredEntitlementForRequest:` — map.
  Разделены корректно: read API `copyCarrierBundleValue` — публичный,
  install/match-write — gated.
- Не смешивается: `copyCarrierBundleValue` (публичный читатель) ≠
  `installCarrierBundle` (gated write).

## 9. Выбор bundle vs VoWiFi

- Bundle-selection ≠ сетевое разрешение IMS — отдельно зафиксировано;
  VoWiFi не объявлен ни возможным, ни невозможным (`INSUFFICIENT EVIDENCE`
  для операторской активации).

## 10. Вывод аудита

Доказательства уровня A (восстановленные Mach-O, ObjC method-IMPs, C++
mangled-имена, normalized-hash SAME) — корректны и воспроизводимы.
Связи уровня B (call-graph по имени, строки) явно помечены. Две главные
неизвестные — тело `matchCarrierBundle_sync` в `CarrierBundleUtilities.dylib`
и `requiredEntitlementForRequest:` diff — заявлены честно.
