# PHASE5_SUMMARY — Final Evidence Audit

## Проведённый аудит

Phase 5 независимо перепроверила выводы Phase 4 по IOS-SEC-004 и IOS-SEC-005. Аудит выполнен только по статическим локальным материалам; с iPhone не было взаимодействия, фаззинг и тесты гонок не проводились, полезные нагрузки и цепочки обхода не создавались, системные бинарники не изменялись, публикация и Git push не выполнялись.

## Главный результат

Phase 4 была слишком уверена в переходе:

`writer не найден` → `writer невозможен` → `IOS-SEC-004 RULED OUT`.

Phase 5 заменяет это на:

`writer не найден` + `access-control evidence неполное` → `condition C NOT VERIFIED` → `IOS-SEC-004 INSUFFICIENT EVIDENCE`.

## Финальные статусы

| Кандидат | Финальный статус Phase 5 | Кратко |
|---|---|---|
| IOS-SEC-004 | **INSUFFICIENT EVIDENCE** | structural check/use separation подтверждён; writer и impact не установлены; `RULED OUT` не доказан |
| IOS-SEC-005 | **INSUFFICIENT EVIDENCE** как security finding; **ARCHITECTURAL OBSERVATION** может сохраняться как описание паттерна | path-based checks anti-symlink observed; полная безопасность pattern не доказана |

## Что подтверждено

- `existingBundleContainer` используется как destination для delta-patch callsite и выбирается через внутренние объекты MobileInstallation.
- `hardlink_copy_hierarchy` использует path-based file operations и не использует destination FD anchor в изученном callsite.
- `realpath_parent_no_symlink`, `lstat` и entity-type checks существуют и повышают защиту.
- Fresh-install staging делегируется через synchronous remote object proxy в helper service.
- Ownership-standardization API предусматривает UID/GID, ACL removal и symlink detection.
- Парсер delta manifest не дал доказанного memory-safety defect по изученному коду.

## Что остаётся UNKNOWN или NOT VERIFIED

- Точные UID/GID/mode/ACL всех relevant staging/destination objects.
- Полный effective writer set для AppBundles и staging parent components.
- Полная применимая sandbox policy installd и helper service.
- Результаты ACL removal для каждого path.
- Наличие или отсутствие untrusted writer'а.
- Значимое security consequence при hypothetical mutation.

## Ключевая коррекция

Нельзя объединять:

- process UID;
- entitlement;
- intended trust domain;
- inode owner;
- DAC mode;
- ACL;
- sandbox rule;
- kernel/VFS enforcement.

Каждый из этих уровней должен доказываться отдельно. В текущем корпусе доказана только часть архитектурной модели и отдельные API callsites.

## Итоговая формулировка

> IOS-SEC-004 не подтверждена как уязвимость и не доказана как невозможная. Структурная check→use separation существует, но ключевые условия exploitability не установлены доступными статическими материалами. Финальный статус — `INSUFFICIENT EVIDENCE`.

> IOS-SEC-005 фиксирует наблюдаемый паттерн path-based checks/use, но без полного access-control audit и demonstrated impact не может быть закрыт как безопасный. Финальный статус security finding — `INSUFFICIENT EVIDENCE`; как отдельное описание архитектурного паттерна допустим `ARCHITECTURAL OBSERVATION` без вывода об отсутствии риска.
