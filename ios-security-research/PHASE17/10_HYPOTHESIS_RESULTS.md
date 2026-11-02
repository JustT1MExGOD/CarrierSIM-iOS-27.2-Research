# Phase 17 · Отчёт 10 — Гипотезы H17-01…H17-07

## H17-01 — B3 изменил requiredEntitlementForRequest для carrier-bundle операций

**Статус: НЕ ПОДТВЕРЖДЕНА**

- За: diff таблицы `requiredEntitlementForRequest:` есть (B2: 307 записей/302 paired;
  B3: 305/300; адреса сместились).
- Против: carrier-bundle коды **идентичны** (copyCarrierBundleValue→1, bundle lookups→3,
  restoreToSystemBundles→19, setTestBundleIdForSlice→14). Изменения касаются
  `injectMTsms`/`invalidateKey` (удалены в B3) и `addParticipants:toGroupChat:…`
  (добавлен в B3) — не carrier-bundle. `bootstrapQuickSwitchEnrollmentFlowAsSecondary`
  имеет одинаковый код 25 в обеих версиях; ранее отмеченная разница «310→308»
  была артефактом чтения смещения записи и снята.
- Вывод: семантической смены политики для carrier-bundle нет; diff — компиляторный + чужие запросы.

## H17-02 — HomeBundleIdentifier даёт произвольный bundle override

**Статус: НЕ ПОДТВЕРЖДЕНА**

- За: `Added HomeBundleIdentifier from overlay file to matching info`, `Matches for the given HomeBundle Identifier` — подмешивает критерий выбора.
- Против: `No match for overlay`, `No overlay matching key, marking override not required`,
  `This SupportedSIM %s is not allowed for MVNO Overlay` — SupportedSIM gate + fallback.
- Вывод: HomeBundleIdentifier — **обогащение/подсказка**, не override.

## H17-03 — Overlay-файл может создавать внешний клиент

**Статус: НЕ ПОДТВЕРЖДЕНА**

- За: `Error writing overlay file`, `Failed to create mobile helper to move the generated overlay files` — есть системный writer.
- Против: ни одного XPC-запроса `overlay*` в `requiredEntitlementForRequest:`,
  ни API создания overlay для приложений.
- Вывод: overlay генерируется внутри системы; внешний API не найден.

## H17-04 — Overlay обходит проверку подписи bundle

**Статус: НЕ ПОДТВЕРЖДЕНА**

- За: `Overlay active, not validating the SIMs` — пропускает валидацию SIM **для системного overlay**.
- Против: overlay работает после выбора подписанного bundle; не создаёт unsigned bundle;
  `SupportedSIM` ограничивает применение.
- Вывод: overlay не обходит подпись; он влияет на выбор внутри подписанного набора.

## H17-05 — В B3 появился новый путь записи overlay для восстановления CarrierSIM

**Статус: НЕ ПОДТВЕРЖДЕНА**

- За: B3 содержит все overlay-строки.
- Против: B3 содержит те же механизмы без новых API; `override_carrier_list.json` удалён;
  regression `107: Capabilities insufficient` — в AirTraffic write path, не overlay.
- Вывод: нового пути нет.

## H17-06 — CarrierBundleUtilities.dylib содержит scoring, который может быть изменён overlay

**Статус: ЧАСТИЧНО ПОДТВЕРЖДЕНА (B-level)**

- За: `CarrierBundleUtilities.dylib` — библиотека, используемая `matchCarrierBundle_sync`;
  `Overlay active, not validating the SIMs` — влияет на процесс match.
- Против: тело библиотеки недоступно (dyld-cache image); не доказано, что overlay
  изменяет scoring, а не просто добавляет входной критерий.
- Вывод: overlay может влиять на scoring как **входной параметр**; изменение логики
  scoring не доказано.

## H17-07 — Overlay имеет независимую от bundle подпись/целостность

**Статус: НЕ ПОДТВЕРЖДЕНА (в CommCenter)**

- За: `Failed to load overlay file as dictionary` — есть проверка формата.
- Против: не найдено проверки подписи/хэша overlay в CommCenter; файл может
  подписываться на уровне системного writer'а (UNKNOWN).
- Вывод: внутри CommCenter проверка целостности overlay не доказана; она может
  быть на уровне файловой системы/прав writer'а.

## Сводная таблица

| Гипотеза | Статус | Уверенность |
|---|---|---|
| H17-01 | НЕ ПОДТВЕРЖДЕНА | ВЫСОКАЯ |
| H17-02 | НЕ ПОДТВЕРЖДЕНА | ВЫСОКАЯ |
| H17-03 | НЕ ПОДТВЕРЖДЕНА | ВЫСОКАЯ |
| H17-04 | НЕ ПОДТВЕРЖДЕНА | ВЫСОКАЯ |
| H17-05 | НЕ ПОДТВЕРЖДЕНА | ВЫСОКАЯ |
| H17-06 | ЧАСТИЧНО ПОДТВЕРЖДЕНА | СРЕДНЯЯ |
| H17-07 | НЕ ПОДТВЕРЖДЕНА | СРЕДНЯЯ |
