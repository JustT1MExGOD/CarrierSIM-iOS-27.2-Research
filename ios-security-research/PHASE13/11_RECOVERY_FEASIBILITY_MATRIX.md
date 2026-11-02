# Фаза 13 — матрица вариантов восстановления

## Статусы

- `CONFIRMED SUPPORTED` — доказано, работает, достигает цели
- `POTENTIALLY SUPPORTED` — теоретически возможно, требует подтверждения
- `NOT ESTABLISHED` — недостаточно данных для оценки
- `NOT SUPPORTED BY AVAILABLE EVIDENCE` — механизм существует, но не решает задачу
- `RULED OUT` — доказано невозможным или заблокировано

## Матрица

| Вариант | Технически возможен | Разрешён без доп. полномочий | Подтверждён на RC | Ограничения | **СТАТУС** |
|---|---|---|---|---|---|
| **Штатный IPCC install** | ДА | paired lockdownd | ДА (B2, B3) | Только свой bundle; нет произвольной IMSI-привязки | **NOT SUPPORTED BY AVAILABLE EVIDENCE** |
| **Carrier settings update (OTA)** | ДА | нет (auto) | ДА | Управляется Apple; не даёт контроля над привязкой | **NOT SUPPORTED BY AVAILABLE EVIDENCE** |
| **Альтернативная IMSI-привязка (файловый симлинк)** | ДА (исторически) | НЕТ (требует записи в Library) | НЕТ (заблокирован) | Запись в `/var/mobile/Library` заблокирована Airlock | **RULED OUT** (Beta 3+) |
| **SIM/eSIM activation** | ДА | carrier-signed | ДА | Управляет eSIM-профилями, не filesystem-bundle | **NOT SUPPORTED BY AVAILABLE EVIDENCE** |
| **MDM cellular config** | ДА | MDM enrollment | НЕТ | Policy-level, не carrier catalog | **NOT SUPPORTED BY AVAILABLE EVIDENCE** |
| **CommCenter XPC direct** | НЕИЗВЕСТНО | entitlement-gated | НЕТ | Нет публичного API; internal only | **NOT ESTABLISHED** |
| **AirTraffic/Airlift (CarrierSIM)** | НЕТ (Beta 3+) | НЕТ | НЕТ | Dirfd-confined move, ENOTCAPABLE 107 | **RULED OUT** |
| **streaming_zip_conduit прямой доступ** | НЕТ | НЕТ | НЕТ | Media-jail only | **RULED OUT** |
| **Другой разрешённый workflow** | НЕИЗВЕСТНО | НЕИЗВЕСТНО | НЕТ | Нет кандидатов | **NOT ESTABLISHED** |

## Примечания по статусам

### `CONFIRMED SUPPORTED` — отсутствуют

**Нет подтверждённого механизма**, который бы:
1. назначал SIM уже установленный Apple carrier bundle другого оператора;
2. работал на iOS 27.2 Beta 3+;
3. не требовал недоступных полномочий.

### `POTENTIALLY SUPPORTED` — отсутствуют

Нет кандидатов, которые бы **теоретически** могли достичь цели при дополнительных проверках. Все доступные пути либо:
- устанавливают свой bundle (IPCC);
- требуют недоступных entitlement (CommCenter XPC);
- заблокированы (Airlift).

### `NOT SUPPORTED BY AVAILABLE EVIDENCE` — IPCC, OTA, eSIM, MDM

Эти механизмы **существуют и работают**, но **не решают задачу** CarrierSIM:
- они управляют carrier *settings* (APN, IMS-флаги);
- они **не создают** файловую IMSI-привязку к чужому системному bundle;
- они **не дают** контроля над тем, какой bundle CommCenter выберет для данной SIM.

### `RULED OUT` — IMSI-симлинк через AirTraffic, streaming_zip_conduit прямой доступ

**Доказано невозможным**:
- AirTraffic-move на Beta 3+ confine'ит к AFC root (`/var/mobile/Media`), `/var/mobile/Library` недоступно (ENOTCAPABLE 107).
- streaming_zip_conduit пишет только в `/var/mobile/Media`, не в Library.
- Прямой доступ к `/var/mobile/Library/Carrier Bundles` через AFC отсутствует (sandbox).

### `NOT ESTABLISHED` — CommCenter XPC, другие workflows

**Недостаточно данных**:
- CommCenter не извлечён; internal XPC мог бы (теоретически) дать доступ к carrier config, но:
  - нет дизасма для подтверждения;
  - entitlement-gated (требует системных прав);
  - нет доказательств, что internal API позволяет произвольную IMSI-привязку.

## Итоговый статус цели

**Цель**: назначить SIM оператора A уже существующий Apple carrier bundle оператора B.

**Статус**: **НЕТ ПОДТВЕРЖДЁННОГО МЕХАНИЗМА** на iOS 27.2 Beta 3+.

- Все доступные **штатные** пути (IPCC, OTA, eSIM, MDM) **не поддерживают** произвольную привязку IMSI к чужому bundle.
- Единственный **исторический** путь (IMSI-симлинк через AirTraffic) **заблокирован** на уровне файловой системы.
- Потенциальные **внутренние** пути (CommCenter XPC) **не установлены** и, скорее всего, entitlement-gated.

**Это не означает невозможность** — это означает отсутствие доказанного механизма в доступных материалах. Отсутствие доказательств ≠ доказательство невозможности, но и не даёт рабочего решения.
