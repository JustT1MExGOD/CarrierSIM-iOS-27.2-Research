# Phase 18 · Отчёт 10 — Проверка исторического CarrierSIM

## 1. Таблица соответствия

| Операция CarrierSIM | Компонент iOS | Beta 2 | Beta 3 | Доказательство |
|---|---|---|---|---|
| Получение IMSI | CommCenter `kSubscriberImsi`, `copyMCCMNCFromIMSI` | есть | есть | строки/импорты идентичны |
| Формирование имени ссылки | `BundleLinks` + IMSI-имя | есть | есть | `BundleLinks` присутствует; сборка имени — B-level |
| Поиск IMSI-привязки | `eIMSI config subfolder matching '%s'`, `BundleLinks` | есть | есть | строки идентичны |
| Разрешение целевого bundle | `_readlink`/`_realpath`/`_lstat` | есть | есть | импорты идентичны |
| **Запись симлинка** | AirTraffic/AFC write path | работает | **БЛОКИРОВАНО** | `107 ENOTCAPABLE` (Phase 16/17) |
| Проверка пакета | CarrierBundleUtilities signature verify | есть (извлечён) | есть (не извлечён) | B2 `__text` подтверждён |
| Применение конфигурации | `matchCarrierBundle_sync` → `sendBundleEvent_sync` | есть | есть | API-имена идентичны |

## 2. Анализ

- **Чтение/match IMSI-алиаса**: полностью сохранён в B3 — `_readlink`, `_lstat`,
  `_realpath`, `BundleLinks`, eIMSI-subfolder matching идентичны B2.
- **Запись симлинка**: единственный сломанный шаг — AirTraffic write path
  возвращает `107 ENOTCAPABLE` (`beneath AFC root` logic). Это **блокирует
  CarrierSIM на этапе записи**, не на match.
- **Signature validation**: CBU проверяет целевой bundle (подписан Apple),
  не сам симлинк — `Vodafone_hu.bundle` остаётся валидным.

## 3. Вывод

CarrierSIM **совместим с matcher B3** — IMSI-alias логика чтения целева. Точка
отказа исключительно в **невозможности записать симлинк** через исторический
AirTraffic workflow. Если симлинк существует (создан другим легальным путём),
matcher его разрешит — но Phase 18 не нашёл легального write-path для
пользователя и не исследует обход.

## 4. Чего не хватает для полного вывода

- IMP `matchCarrierBundle_sync` — не разрешён; порядок «симлинк vs eIMSI vs
  operator» восстановлен по именам.
- B3 CBU `__text` — недоступен; signature-verify в B3 предполагается
  идентичным, не доказан.
