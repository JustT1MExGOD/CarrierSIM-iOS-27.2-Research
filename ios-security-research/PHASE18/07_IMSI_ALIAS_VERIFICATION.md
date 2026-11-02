# Phase 18 · Отчёт 07 — Проверка IMSI-симлинков (IMSI Alias)

## 1. Что искали

Исполняемую логику: `IMSI → имя файла/записи → каталог Carrier Bundles →
симлинк → целевой bundle → выбор конфигурации`. Целевой путь
`/var/mobile/Library/Carrier Bundles/iPhone` и операции `readlink`/`realpath`/`stat`/`lstat`/`opendir`.

## 2. Найденные доказательства (CommCenter)

| Элемент | B2 | B3 | Значение |
|---|---|---|---|
| `BundleLinks` строка | `0x1021e2820` | есть | имя каталога симлинков bundle |
| `_readlink` import | есть | есть | чтение симлинка |
| `_realpath$DARWIN_EXTSN` import | есть | есть | разрешение пути |
| `_lstat` import | есть | есть | stat без следования (симлинк!) |
| `eIMSI config subfolder matching '%s'` | есть | есть | перебор eIMSI-подкаталогов |
| `BCAM eIMSI config subfolder matching` | есть | есть | BCAM/eSIM вариант |
| `eIMSI` / `eIMSIConfig` | 17–18 hits | 17 hits | конфигурация eIMSI |
| `Carrier Bundles` | 4 hits | есть | базовый каталог |

## 3. Интерпретация

- **`_lstat`** — вызывается для проверки пути **без** следования симлинку — типичная проверка «является ли запись симлинком».
- **`_readlink`** — разрешает цель симлинка.
- **`_realpath`** — нормализует путь.
- **`BundleLinks`** — отдельный подкаталог для симлинков (а не `/var/mobile/Library/Carrier Bundles/iPhone` напрямую — Phase 18 не нашёл этого полного пути как строки; имя собирается из `Carrier Bundles` + `BundleLinks`).
- **`eIMSI config subfolder matching`** — подтверждённая функция перебора eIMSI-подкаталогов — семантический аналог «IMSI-имя → подкаталог».

## 4. Вывод по сохранности

**IMSI-alias обработка сохранена в B3.** Все примитивы (`_lstat`, `_readlink`,
`_realpath`, `BundleLinks`, eIMSI subfolder matching) присутствуют в CommCenter B3
в том же виде, что и B2. Phase 18 **не нашла** удаления IMSI-matching логики.

## 5. Что реально регрессировало

Регрессия Beta 3 (`107: Capabilities insufficient`, `ENOTCAPABLE`) — это **write path**
в AirTraffic/AFC (создание симлинка), а не matcher/read path. CarrierSIM ломается на
этапе *записи* `BundleLinks/…`-симлинка, а не на чтении.

## 6. Ограничение

- Точный IMP `matchCarrierBundle_sync`/функция перебора `BundleLinks` не разрешён
  (C++ метод, нет selref; call-graph по именам).
- `readlink`/`lstat` — это импорты; их xref к конкретным callsite восстановлен
  не полностью (chained-fixup stub → stub call). Связь `readlink`↔`BundleLinks`
  установлена по совместному присутствию в CommCenter + семантике, не по
  единому CFG — **уровень A-/B+**.

## 7. Ответ на задачу

Исполняемая логика `IMSI → symlink → bundle` **существует в B3**. Доказательство —
импорты `readlink`/`lstat`/`realpath` + `BundleLinks` + eIMSI-subfolder matching,
идентичные B2. Не доказано «удаление IMSI matching» — напротив, подтверждено
сохранение.
