# PHASE5 — 05_REPORT_CORRECTIONS

## Назначение

Зафиксировать, какие формулировки Phase 4 были сильнее, чем позволяет локальное evidence, и чем их заменить. Phase 1–4 не изменяются; этот документ является отдельным audit trail Phase 5.

## 1. Corrections matrix

| Предыдущая формулировка | Проблема | Исправленная формулировка |
|---|---|---|
| «Домен AppBundles закрыт для всех, кроме installd и trusted helper-service» | не представлен полный DAC/ACL/sandbox/writer audit | «В материалах видна intended privileged architecture; полный effective writer set не доказан» |
| «Доступный субъект: CONTRADICTED» | absence of found writer не равна доказанной невозможности writer'а | `NOT VERIFIED`: внешний writer не найден, невозможность не доказана |
| «entitlement AppBundles доказывает владельца домена» | capability/entitlement не равен inode owner или DAC rights | entitlement подтверждает заявленную capability/architectural role; owner/mode/ACL остаются UNKNOWN |
| «_installd владеет destination» | UID процесса не доказывает owner каждого объекта | process identity и filesystem owner разделены; конкретный owner destination UNKNOWN |
| «ACL явно удаляются, значит сторонний write исключён» | API call name и flag не показывают effective result для всех paths | вызов стандартизации с `removeACLs` подтверждён; итоговый ACL state UNKNOWN |
| «точные uid/gid/mode не важны для вывода» | именно они нужны для строгого опровержения writer hypothesis | точные значения отсутствуют и являются существенным evidence gap |
| «sandbox/VFS boundary описана entitlement/DAC» | sandbox profile не извлечён, DAC listing отсутствует | sandbox policy NOT VERIFIED; DAC metadata UNKNOWN |
| «realpath→path-op — безопасная штатная архитектура» | structural mitigation не доказывает race impossibility | realpath/lstat дают mitigation; check/use remains structurally unanchored |
| «IOS-SEC-004 RULED OUT» | ключевое условие C не CONTRADICTED | `INSUFFICIENT EVIDENCE`: vulnerability not demonstrated, but not ruled out |
| «IOS-SEC-005 ARCHITECTURAL OBSERVATION» как итог безопасности | observation смешивалась с security conclusion | сохранить observation, но security classification — `INSUFFICIENT EVIDENCE` |

## 2. Что остаётся подтверждённым из Phase 4

Phase 5 не отменяет следующие наблюдения:

- `existingBundleContainer` передаётся в installable construction после installed/placeholder checks;
- `hardlink_copy_hierarchy` использует path-based operations;
- `realpath_parent_no_symlink`, `lstat` и entity-type checks существуют;
- no destination `*at`/dirfd sequence найден в исследованном installd binary;
- fresh staging использует helper-service proxy;
- ownership-standardization API предусматривает UID/GID, ACL removal и symlink out-parameter;
- parser bounds/error checks не дали доказанного memory-safety defect.

Исправляется не фактология этих observations, а сила security inference.

## 3. Почему `NOT VERIFIED`, а не `CONTRADICTED`

`CONTRADICTED` означало бы, что доступные данные прямо несовместимы с гипотезой. В данном случае данные совместимы с двумя моделями:

1. AppBundles и staging действительно недоступны любому недоверенному writer'у;
2. существует неисследованный путь, helper, ACL, sandbox exception или иной субъект, который может менять relevant path.

Поскольку локальные материалы не различают эти модели, корректен `NOT VERIFIED`.

## 4. Нельзя повышать статус до CONFIRMED

Phase 5 также не нашла:

- конкретного недоверенного субъекта;
- доказанной race mutation;
- подтверждённого redirect outside intended domain;
- значимого consequence;
- runtime observation.

Поэтому `CONFIRMED SECURITY ISSUE` не назначается.

## 5. Корректный итог коррекции

Phase 4 была чрезмерно уверенной только в переходе:

`writer не найден` → `writer невозможен` → `TOCTOU RULED OUT`.

Phase 5 заменяет эту цепочку на:

`writer не найден` + `access-control evidence неполное` → `condition C NOT VERIFIED` → `finding INSUFFICIENT EVIDENCE`.
