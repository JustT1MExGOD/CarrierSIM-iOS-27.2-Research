# Phase 17 · Отчёт 07 — Поток «Overlay → Выбор bundle»

## 1. Цепочка

```
┌─ Источник overlay ───────────────────────────────────────────┐
│  системный writer / mobile helper (точный компонент UNKNOWN) │
└──────────────────────┬───────────────────────────────────────┘
                       │ путь к overlay-файлу
                       ▼
┌─ Чтение/разбор ──────────────────────────────────────────────┐
│  `Using overlay file path` → `load overlay file as dict`     │
│  `Key not found` / `Successfully retrieved value`            │
│  Проверки: dict, ключ, SupportedSIM                          │
└──────────────────────┬───────────────────────────────────────┘
                       │ matching-info dict
                       ▼
┌─ Обогащение matching-info ───────────────────────────────────┐
│  `Added HomeBundleIdentifier from overlay file`              │
│  IMSI/entry match → SupportedSIM gate → add HBI              │
│  `Failed to find IMSI in overlay matching info` → no overlay │
└──────────────────────┬───────────────────────────────────────┘
                       │ matching-info (+ HomeBundleIdentifier)
                       ▼
┌─ Match ──────────────────────────────────────────────────────┐
│  `matchCarrierBundle_sync` / `matchCarrierBundleForSim_sync` │
│  `homeBundleIdentifierFromMatchInfo provided to search for   │
│   best match with SIM Info`                                  │
│  `Matches for the given HomeBundle Identifier`               │
└──────────────────────┬───────────────────────────────────────┘
                       │ candidate bundle
                       ▼
┌─ Применение ─────────────────────────────────────────────────┐
│  `sendBundleEvent_sync` (Phase 16)                           │
│  `Rematch carrier bundle to apply GSMA overlay` (при обновл.)│
└──────────────────────────────────────────────────────────────┘
```

## 2. Шаги с деталями

| Шаг | Функция/точка | Вход | Выход | Проверки | Уверенность |
|---|---|---|---|---|---|
| Источник | mobile helper / system writer (UNKNOWN) | — | путь overlay | права файловой системы | MEDIUM |
| Разбор | overlay reader | путь | CFDictionary | `load as dictionary`, `Key not found` | A |
| Извлечение | overlay-to-match-info mapper | dict | matching-info entry | `find IMSI`, `SupportedSIM allowed` | A |
| Обогащение | matching-info enricher | matching-info | matching-info + HBI | `Added HomeBundleIdentifier` | A |
| Поиск | `homeBundleIdentifierFromMatchInfo` → `matchCarrierBundle*` | matching-info + SIM | candidate bundle | `Matches for the given HBI` | A |
| Применение | `sendBundleEvent_sync` | candidate | активный bundle | `Bundle updated` → rematch | A |

## 3. Где входит HomeBundleIdentifier

`HomeBundleIdentifier` подмешивается **после** разбора overlay, **до**
передачи в `matchCarrierBundle{ForSim}_sync`. Он используется как критерий
поиска best-match, а не как прямой выбор.

## 4. Точки неопределённости

- **Источник**: кто вызывает `Using overlay file path`? — не установлен.
- **Состав**: полный список ключей overlay — не восстановлен.
- **Сила**: может ли `HomeBundleIdentifier` изменить результат, если
  нормальный match дал бы другой bundle? — **не доказано**.
- **Scoring**: `CarrierBundleUtilities.dylib` тело недоступно —
  точное влияние на приоритет не видно.

## 5. Возможный эффект

На основании строк overlay может:

- **ограничивать** набор кандидатов (SupportedSIM);
- **подсказывать** matcher'у приоритетный bundle (`Matches for the given
  HBI`);
- **пропускать** проверку SIM (`Overlay active, not validating the SIMs`)
  — *в контексте системного overlay*.

Но **не доказано**, что overlay способен **заменить** выбор bundle на
произвольный, обходя правила подписи/оператора.
