# Phase 18 · Отчёт 11 — Проверка гипотез H18-01…H18-07

## H18-01 — Реализация CarrierBundleUtilities.dylib доступна

- **За**: B2 `__text` извлечён из dyld cache `.73` — 0xddac кода, 234 PAC-функции,
  signature/version.xml/PRI движок.
- **Против**: B3 subcache dataless → B3 CBU не извлечён; LINKEDIT/objc metadata не собраны.
- **Статус**: `SUPPORTED BUT INCOMPLETE` (полный для B2 `__text`, недоступен для B3).
- **Уверенность**: высокая (B2), нет (B3).

## H18-02 — Восстановлен существенный фрагмент matcher

- **За**: CBU полностью дизассемблирован и размечен по ролям; CommCenter match-иерархия
  (operator/country/bootstrap/default) + IMSI-alias примитивы подтверждены.
- **Против**: `matchCarrierBundle_sync` IMP не разрешён — ядро scoring не видно;
  CBU оказался validator'ом, не matcher'ом.
- **Статус**: `SUPPORTED BUT INCOMPLETE`.
- **Уверенность**: средняя — восстановлен validator и обвязка matcher'а, не сам scoring.

## H18-03 — Beta 3 продолжает обрабатывать IMSI-симлинки

- **За**: `_readlink`, `_realpath`, `_lstat`, `BundleLinks`, `eIMSI config subfolder
  matching '%s'`, `BCAM eIMSI config` — идентичны B2.
- **Против**: IMP функции перебора не разрешён; нет runtime-подтверждения.
- **Статус**: `SUPPORTED BUT INCOMPLETE` — read path сохранён, запись заблокирована отдельно.
- **Уверенность**: высокая по присутствию кода; средняя по фактическому выбору.

## H18-04 — Нет семантических изменений, влияющих на CarrierSIM

- **За**: carrier-bundle entitlement-коды идентичны; readlink/lstat/BundleLinks/eIMSI
  без изменений; удаления касаются `injectMTsms`/`invalidateKey`/`override_carrier_list.json`.
- **Против**: единственное семантическое изменение — `107 ENOTCAPABLE` write-path —
  **влияет на CarrierSIM**, но находится вне matcher.
- **Статус**: `SUPPORTED BUT INCOMPLETE` — в matcher изменений нет; в write-path есть.
- **Уверенность**: высокая.

## H18-05 — CarrierBundleOverlay влияет на выбор активного bundle

- **За**: `Added HomeBundleIdentifier to matching info`, `Matches for the given
  HomeBundle Identifier`, `Rematch carrier bundle to apply GSMA overlay`.
- **Против**: `No match for overlay`, `override not required`, SupportedSIM gate —
  влияние ограничено whitelist/fallback.
- **Статус**: `SUPPORTED BUT INCOMPLETE` — влияет как входной критерий.
- **Уверенность**: высокая.

## H18-06 — HomeBundleIdentifier способен изменить результат matching

- **За**: передаётся в `matchCarrierBundle*` как best-match hint.
- **Против**: не прямое назначение; зависит от scoring (не виден); ограничен SupportedSIM.
- **Статус**: `INSUFFICIENT EVIDENCE` — может изменить приоритет внутри санкционированного
  набора; произвольное изменение не доказано.
- **Уверенность**: средняя.

## H18-07 — Подтверждённый поддерживаемый способ выбрать bundle другого оператора

- **За**: IMSI-alias read path сохранён; overlay/HBI могут влиять.
- **Против**: запись симлинка заблокирована (`107 ENOTCAPABLE`); нет внешнего API
  overlay; нет SupportedSIM обхода; HBI — не override.
- **Статус**: `RULED OUT` — легальный пользовательский путь не подтверждён.
- **Уверенность**: высокая.

## Сводная таблица

| Гипотеза | Статус | Уверенность |
|---|---|---|
| H18-01 | SUPPORTED BUT INCOMPLETE | высокая (B2) / — (B3) |
| H18-02 | SUPPORTED BUT INCOMPLETE | средняя |
| H18-03 | SUPPORTED BUT INCOMPLETE | высокая (код) |
| H18-04 | SUPPORTED BUT INCOMPLETE | высокая |
| H18-05 | SUPPORTED BUT INCOMPLETE | высокая |
| H18-06 | INSUFFICIENT EVIDENCE | средняя |
| H18-07 | RULED OUT | высокая |
