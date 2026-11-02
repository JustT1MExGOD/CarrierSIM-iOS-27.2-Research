# Phase 17 · Отчёт 09 — Релевантность CarrierSIM

## 1. Формулировка вопроса

Может ли системный overlay-механизм CommCenter заменить CarrierSIM —
способ назначить SIM произвольного оператора чужой carrier bundle без
записи symlink'а в `Carrier Bundles/iPhone`?

## 2. Ответы на 6 вопросов

### Q1. Использует ли CarrierSIM overlay?

**Нет.** CarrierSIM работает через файловую систему — создаёт
15-значный IMSI-имя как symlink в `/var/mobile/Library/Carrier Bundles/iPhone`
на существующий подписанный bundle. Overlay — механизм CommCenter для
matching-info/выбора, не filesystem-связь. Механизмы не пересекаются.

### Q2. Использует ли CommCenter overlay при обработке SIM?

**Да**, но как внутренний фильтр/обогатитель. Строки `Overlay active, not
validating the SIMs`, `Failed to find IMSI in the overlay matching info`,
`This SupportedSIM %s is not allowed for MVNO Overlay` показывают, что
overlay участвует при обработке SIM **для системных сценариев** (MVNO,
multimode, GSMA). Это не путь пользовательского выбора оператора.

### Q3. Может ли overlay законно назначить другой bundle?

**Частично, в рамках системных ограничений.** `Added HomeBundleIdentifier
from overlay file to matching info` + `Matches for the given HomeBundle
Identifier` — overlay может подсказать matcher'у альтернативный bundle.
Но:

- `SupportedSIM` gate — только для SIM из белого списка;
- `No match for overlay` — если matcher не находит соответствия, ничего
  не меняется;
- `No overlay matching key, marking override not required` — есть флаг
  «override not required».

То есть overlay может **влиять** на выбор в пределах санкционированного
набора, не может **назначить произвольный** bundle.

### Q4. Подтверждён ли легальный источник overlay?

**Нет.** В Phase 17 подтверждено только: `Failed to create mobile helper
to move the generated overlay files` + `Error writing overlay file` —
системный writer. Точный API/компонент/путь для создания overlay извне
не найден. `com.apple.AppStoreOverlays.ViewService` — имя сервиса, не
доказательство общего доступа к carrier-bundle overlay.

### Q5. Требуются ли особые entitlements?

**Не доказано.** В `requiredEntitlementForRequest:` нет запросов,
относящихся к overlay (Phase 17 не нашла `overlay`-sel'екторов в
таблице). Возможно, overlay обслуживается внутренними вызовами, не
через XPC-запросы. Но это не значит, что любой процесс может
создавать overlay — доступ к системным helper'ам обычно ограничен.

### Q6. Достижимо ли без записи IMSI-symlink'а?

**Нет, не доказано.** Чтобы получить эффект CarrierSIM через overlay,
нужно:

1. Создать overlay-файл с `HomeBundleIdentifier` = bundle другого
   оператора и IMSI-префиксом, соответствующим целевой SIM.
2. Обойти `SupportedSIM` gate — внести IMSI в белый список.
3. Обеспечить `match` — matcher должен найти соответствие.

Phase 17 не нашла ни пользовательского API создания overlay, ни способа
включить IMSI в `SupportedSIM` без системных прав. Сам `HomeBundleIdentifier`
— подсказка, не команда.

## 3. Итог

Overlay — **не** механизм восстановления CarrierSIM. Это системный
способ уточнения match-выбора для легитимных сценариев (MVNO, GSMA,
multimode). Он не создаёт symlink'и, не даёт произвольного назначения
чужого bundle и не имеет доказанного пользовательского API.
