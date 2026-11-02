# Phase 17 · Отчёт 05 — HomeBundleIdentifier

## 1. Идентификация

`HomeBundleIdentifier` — **строковый ключ/значение matching-info**, который
системный код извлекает из overlay-dictionary и подмешивает в структуру,
используемую matcher'ом для выбора carrier bundle. Это не entitlement, не
правило подписи и не override-флаг.

Доказательства (B2 vm-адреса строк; B3 — по смыслу, см. отчёт 04):

- `Added HomeBundleIdentifier from overlay file to matching info` `0x102144d50`;
- `homeBundleIdentifierFromMatchInfo provided to search for best match with SIM Info` `0x102147a7d`;
- `Matches for the given HomeBundle Identifier` `0x102147c28`;
- `HomeBundleIdentifier = '%{public}s'` `0x1021468dd`;
- `Failed to find IMSI in the overlay matching info` `0x102069f13`;
- `This SupportedSIM %s is not allowed for MVNO Overlay` `0x10206a045`.

## 2. Тип, источник, хранение

| Параметр | Значение | Уровень |
|---|---|---|
| Тип | CFStringRef / CFString в matching-info dict | A (по контексту CF API и формату `%{public}s`) |
| Источник | overlay-dictionary (`overlay file as dictionary`) | A |
| Хранение | временное поле matching-info (per-match, per-slot); не записывается в файловую систему CommCenter-ом как symlink | A (нет строки записи; есть только чтение из overlay) |
| Создатель | **не установлен** — mobile-helper упомянут, API/компонент не идентифицирован | UNKNOWN |

## 3. Как он попадает в matching info

По строкам восстановлена цепочка:

```
overlay file path → CF read as dictionary → key lookup → IMSI/entry match →
SupportedSIM MVNO gate → append/set HomeBundleIdentifier into matching-info →
pass to matchCarrierBundle{ForSim}_sync
```

`Added HomeBundleIdentifier ... to matching info` — точка подмешивания.
`homeBundleIdentifierFromMatchInfo provided to search for best match with SIM Info`
— точка передачи в matcher. Прямого доступа внешнего XPC-клиента к этому
конвейеру Phase 17 не нашла.

## 4. Может ли он изменить приоритет кандидатов

**Условно да** — в пределах набора, допущенного matcher-ом:

- `Matches for the given HomeBundle Identifier` — это критерий фильтрации/
  ранжирования кандидатов, а не прямой выбор bundle по имени.
- `homeBundleIdentifierFromMatchInfo provided to search for best match with
  SIM Info` — он передаётся как подсказка для поиска best-match, не как
  принудительный результат.
- `No match for overlay` / `No overlay matching key, marking override not
  required` — если matcher не находит соответствия, overlay не применяется.

То есть `HomeBundleIdentifier` смещает **приоритет** внутри уже
санкционированного набора bundle; он не создаёт новых кандидатов и не
обходит подпись.

## 5. Ограничения

- **SupportedSIM MVNO gate** — строка `not allowed for MVNO Overlay` показывает,
  что применение ограничено белым списком SIM/операторов; не любой IMSI
  может быть маппирован на произвольный bundle.
- **Кэш и no-match** — `Overlay result is already cached`, `No match for
  overlay`, `override not required` — механизм может вернуть исходный
  результат без применения.
- **Нет записи symlink** — HomeBundleIdentifier не является и не заменяет
  механизм CarrierSIM (запись 15-значного IMSI-имени в `Carrier Bundles/iPhone`
  как symlink). Это два разных слоя.

## 6. Enrichment vs selection vs override — разграничение

- **Metadata enrichment**: `HomeBundleIdentifier` **добавляет** к matching-info
  атрибут (home operator hint), который matcher использует как один из критериев.
- **Bundle selection**: выбор конкретного bundle остаётся за
  `matchCarrierBundle_sync`/scoring-функцией в `CarrierBundleUtilities.dylib`
  (тело недоступно). `HomeBundleIdentifier` — вход, не результат.
- **Bundle override**: **не доказано**. Нет строки/кода, который бы
  напрямую назначал выбранный bundle по `HomeBundleIdentifier` без
  прохождения matcher/scoring. Тезис «overlay override выбирает чужой bundle»
  в Phase 17 **не подтверждён**.

## 7. Связь с домашним оператором

Ключ `HomeBundleIdentifier` семантически указывает на домашний/родной
bundle (обычно home carrier для MVNO/multimode), но Phase 17 не доказала,
что это соответствует «IMSI-другого оператора → bundle другого оператора»
как в CarrierSIM. Механизм работает через matching-info и matcher, а не
через symlink.
