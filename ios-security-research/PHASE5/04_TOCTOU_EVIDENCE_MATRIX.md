# PHASE5 — 04_TOCTOU_EVIDENCE_MATRIX

## Метод

Матрица применяет четыре необходимые проверки к IOS-SEC-004 и IOS-SEC-005. `NOT VERIFIED` не преобразуется в `CONTRADICTED`. `RULED OUT` допускается только при опровержении ключевой гипотезы, а не при отсутствии найденного exploit path.

## Матрица доказательств

| Условие | IOS-SEC-004: delta patch | IOS-SEC-005: общий installd pattern | Оценка доказательства |
|---|---|---|---|
| A. Check и use разделены | CONFIRMED: `realpath`/`lstat`/type checks перед path-based ops; destination не закреплён FD | CONFIRMED для исследованных callsites; универсальность по всему бинарю не доказана | прямое disassembly/import evidence |
| B. Проверенное состояние может измениться | CONFIRMED структурно: path re-resolution, отсутствие dirfd anchor | CONFIRMED структурно для тех же path-based sequences | зависит от возможного writer'а |
| C. Есть недоверенный субъект с effective write/rename | NOT VERIFIED. Intended trust model указывает на privileged installd/helper, но exact DAC/ACL/sandbox/полный writer set не извлечены | NOT VERIFIED; общий claim ещё слабее, чем для конкретного delta callsite | Phase 4 ошибочно поставила CONTRADICTED |
| D. Есть значимое security consequence | NOT VERIFIED | NOT VERIFIED | нет runtime impact evidence; absence не доказывает impossibility |

## Уточнение условия C

Для `CONTRADICTED` требовалось бы доказать невозможность relevant writer'а в рассматриваемой модели, например через согласованный набор:

- exact owner/group/mode/ACL relevant parent directories;
- complete applicable sandbox rules;
- authorization path for all processes able to reach the object;
- отсутствие альтернативного privileged-but-untrusted или compromised writer;
- отсутствие helper-side input path, меняющего threat model.

В корпусе этого набора нет. Есть только:

- process identities и entitlement strings;
- intended AppBundles architecture;
- ownership-standardization API;
- helper-service call chain;
- отсутствие найденного обычного app writer'а.

Это достаточная основа для «внешний writer не найден», но не для «writer невозможен».

## Уточнение условия D

Изменение объекта могло бы быть security-relevant только при доказанном impact. Локально не доказаны:

- выход за AppBundles;
- запись в sensitive path;
- изменение кода с bypass signing;
- privilege escalation;
- cross-container effect;
- persistence или arbitrary file write вне intended domain.

Но отсутствие таких доказательств не превращается в доказательство невозможности. Поэтому D остаётся `NOT VERIFIED`.

## Классификационное правило

### IOS-SEC-004

- `CONFIRMED` для A и B;
- `NOT VERIFIED` для C и D;
- parser memory/boundary defect не найден;
- vulnerability не подтверждена;
- `RULED OUT` не поддерживается, поскольку C не опровергнут, а только не доказан.

Финальный статус Phase 5: **INSUFFICIENT EVIDENCE**.

### IOS-SEC-005

- path-based anti-symlink/check-use architecture подтверждена;
- общая provenance и полный access-control model не подтверждены;
- exploitability и impact не подтверждены.

Финальный статус Phase 5: **INSUFFICIENT EVIDENCE** для security finding. Отдельно можно сохранить **ARCHITECTURAL OBSERVATION** как описание паттерна, но это не должно звучать как доказательство его безопасности.

## Что матрица не утверждает

- Она не утверждает наличие уязвимости.
- Она не утверждает наличие недоверенного writer'а.
- Она не утверждает, что realpath/lstat бесполезны.
- Она не утверждает, что entitlement не имеет значения.
- Она не утверждает, что AppBundles доступны обычному приложению.

Она утверждает только, что доступные материалы не позволяют честно перевести ключевые unknowns в `CONTRADICTED`.
