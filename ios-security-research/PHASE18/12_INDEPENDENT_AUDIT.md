# Phase 18 · Отчёт 12 — Независимый аудит

## 1. Корректность Mach-O extraction

- Magic `0xcffaedfe`, cputype `0x100000c` (arm64e), filetype 20 — корректно.
- `__TEXT` VA `0x2c5643000` ↔ fileoff `0x5243000` через subcache `.73` mapping
  (`va 0x2c0400000 → off 0`) — **независимо проверено** по Mach-O magic на смещении.
- `__text` `0xddac` Б, SHA `68c66443…` — согласовано с секцией.

## 2. VM-to-file mapping

Mapping table subcache применён корректно (`fileoff = fo + (va - addr)`). Строки
`__cstring`/`__oslogstring` читаются по вычисленным fileoff — **согласовано**.

## 3. Границы функций

Использована PAC-эвристика (`pacibsp`/`paciasp`). Точные границы из
`LC_FUNCTION_STARTS` недоступны (LINKEDIT отдельный subcache) — **помечено как
ограничение**, не выдано за факт.

## 4. Cross-references / branch targets

- String xref через `adrp+add`/`adrp+ldr` — разрешены по ADRP-page+disp; 102 xref найдено.
- Branch targets не резолвились по таблице (нет fstarts) — **UNKNOWN**, не подменено.

## 5. Ошибки декомпилятора / extractor

- cmpfs не поддерживал type 14 → **исправлено** (LZFSE resource-fork).
- Остаточное: B3 subcache dataless — формат хранения, не баг.
- Найденная ошибка предыдущего вывода (код `bootstrapQuickSwitch` 310→308) — снята как артефакт чтения смещения; реальный код 25 в обеих.

## 6. Сопоставление версий

- B3 CommCenter проверен независимо: `_readlink`/`_lstat`/`_realpath`/`BundleLinks`/eIMSI — присутствуют.
- B3 CBU недоступен → diff помечен недоступным, не притянут по аналогии.

## 7. Подмена кода строками

- Роли функций CBU основаны на **строках внутри PAC-функций** (xref → функция) — A-level для роли.
- IMP `matchCarrierBundle_sync` **не разрешён** — помечено B-level; не выдано за CFG.
- Не утверждается «выбор bundle доказан кодом» — восстановлена обвязка + validator.

## 8. Разделение понятий

- **overlay metadata enrichment** ≠ **bundle override** — разделены (отчёт 08).
- **bundle selection** (CommCenter) ≠ **bundle signature validation** (CBU) —
  явно разделены в отчётах 05/06 — главная коррекция Phase 18.
- **bundle selection** ≠ **IMS registration** — не смешивались.
- **наличие IMSI-alias кода** ≠ **успешный CarrierSIM** — запись симлинка
  заблокирована отдельно; read path ≠ write path.

## 9. Необоснованные выводы

- «IMSI matching удалён» — **не утверждается** (он сохранён).
- «B3 CBU идентичен» — **не утверждается** (недоступен).
- «симлинк разрешается readlink» — подтверждено присутствием примитивов +
  `BundleLinks`, не прямым CFG xref — помечено A-/B+.

## 10. Итог

Главные корректировки Phase 18: (1) CBU — validator, не matcher; (2) IMSI-alias
сохранён в B3 — регрессия только в write path; (3) HBI — enrichment, не override.
Все выводы привязаны к машинному коду/импортам/строкам с указанием уровня.
