# PHASE5 — 06_FINAL_FINDINGS

## Режим и стандарт доказательности

Итоги основаны только на статическом офлайн-анализе локального корпуса. Отсутствие доказанного exploit path не интерпретируется как доказательство невозможности. `NOT VERIFIED` не приравнивается к `CONTRADICTED`.

## IOS-SEC-004 — delta manifest / hardlink_copy_hierarchy / TOCTOU

### Финальный статус

**INSUFFICIENT EVIDENCE**

### Что подтверждено

1. Delta parser и связанные boundary/error checks не дали доказанного OOB, integer overflow, UAF, double-free или uninitialized-data defect.
2. `-[MIInstaller _patchUpdateInstallableForBundle:manifestPath:existingBundleContainer:patchType:error:]` проверяет installed/placeholder state и передаёт `existingBundleContainer` в создание patch installable.
3. `hardlink_copy_hierarchy` выполняет path-based `link`, `mkdir`, `rename`, `unlink`, `chmod`, `symlink`, `copyfile` и не использует destination dirfd anchor в исследованном callsite.
4. Перед file operations выполняются `realpath`/parent symlink/entity-type checks.
5. Следовательно, check/use separation является реальным structural property.

### Что не подтверждено

1. Конкретные UID/GID/mode/ACL `existingBundleContainer` и его parent directories.
2. Полная применимая sandbox/Seatbelt policy installd и helper-service.
3. Полный список процессов, которые могут эффективно менять relevant ancestor или directory entry.
4. Наличие либо отсутствие ACL/sandbox exception, позволяющего конкурентное изменение.
5. Фактическое сохранение object identity между check и use.
6. Security-relevant consequence при hypothetical mutation.

### Почему не RULED OUT

Phase 4 классифицировала condition C как `CONTRADICTED`, основываясь на intended trust model, entitlement и общем container-model. Phase 5 не считает это достаточным строгим опровержением. Локально доказано, что writer не найден; не доказано, что writer невозможен.

Корректный вывод:

> Структурное TOCTOU-условие присутствует; exploitability, доступный недоверенный writer и impact не установлены. IOS-SEC-004 нельзя назвать подтверждённой уязвимостью, но и `RULED OUT` не поддерживается текущим evidence.

## IOS-SEC-005 — общий path-check/path-use pattern

### Финальный статус

**INSUFFICIENT EVIDENCE** как security finding.

### Сохраняемая architectural observation

В исследованных функциях `installd` наблюдается архитектурный паттерн:

`realpath/lstat/entity checks -> path-based syscall`.

Это можно сохранить как **ARCHITECTURAL OBSERVATION**, если формулировка не утверждает, что безопасность паттерна доказана для всех callsites.

### Причины недостаточности

- IOS-SEC-005 шире одного delta callsite;
- provenance и trust boundary не восстановлены для всех path-based operations;
- exact permissions и complete sandbox policy отсутствуют;
- отсутствие найденного ordinary-app writer'а не исключает все системные/сервисные варианты;
- consequence не доказан и не опровергнут конструктивно.

### Что не следует утверждать

Не следует писать:

- «весь AppBundles domain доказан закрытым»;
- «только installd и helper могут писать»;
- «anti-symlink checks исключают TOCTOU»;
- «path-based операции безопасны, потому что destination privileged»;
- «race возможен только у уже privileged субъекта».

Допустимая формулировка:

> Для исследованных callsites подтверждены path-based checks и отсутствие FD anchoring. Intended privileged ownership согласуется с архитектурой MobileInstallation, однако effective DAC/ACL/sandbox и полный writer set локально не восстановлены. Security impact не установлен.

## Сводная таблица

| Кандидат | Phase 4 | Phase 5 | Основание изменения |
|---|---|---|---|
| IOS-SEC-004 | RULED OUT | **INSUFFICIENT EVIDENCE** | condition C была названа CONTRADICTED без полного access-control evidence |
| IOS-SEC-005 | ARCHITECTURAL OBSERVATION | **INSUFFICIENT EVIDENCE** для finding; observation сохранена | общий scope шире доказанного callsite, безопасность не доказана |

## Статусы, которые Phase 5 НЕ назначает

- `CONFIRMED SECURITY ISSUE`: нет конкретного субъекта, mutation и impact.
- `PLAUSIBLE / NEEDS VALIDATION`: в текущем корпусе есть structural class, но нет достаточно конкретного writer/impact сценария; conservative registry status остаётся `INSUFFICIENT EVIDENCE`.
- `RULED OUT`: не назначается, потому что ключевая невозможность writer'а не доказана.

## Остаточный evidence gap

Для будущего строго offline-аудита, без обращения к устройству и без race testing, понадобились бы:

- локальная копия реализации MobileInstallation framework;
- helper-service binary и его exported protocol authorization;
- извлечённые sandbox profiles соответствующих процессов;
- статические entitlement/code-signing материалы всех writer candidates;
- полная cross-reference inventory всех callsites, которые получают или передают destination URLs.

Даже наличие этих материалов потребовало бы отдельной проверки; их отсутствие сейчас не является доказательством уязвимости.
