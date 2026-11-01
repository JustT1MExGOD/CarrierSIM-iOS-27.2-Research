# RESEARCH_STATUS — сводная матрица результатов

Восемь кандидатов, поставленных в Phase 1 и перепроверенных в Phase 2–5.
Статусы отражают итог независимого аудита Phase 5, который имеет приоритет
над промежуточными интерпретациями.

## Матрица

| ID | Объект / гипотеза | Итоговый статус | Краткое обоснование |
|---|---|---|---|
| **IOS-SEC-001** | installd NSXPC authorization | **ARCHITECTURAL OBSERVATION** | `MobileInstallerProtocol` экспортирует 75 методов; 63 имеют прямой helper-gate (`_ValidateMIAllowedSPIEntitlement`), у 12 прямой вызов helper не найден статически. Не дефект: gate может быть в другом слое / реализован иначе. |
| **IOS-SEC-002** | installd test-mode registration | **ARCHITECTURAL OBSERVATION** | `triggerRegistrationFor*` проверяет `isRunningInTestMode`/`testFlagsAreSet` (#2, #0x10) и sentinel; test-mode — предположительно отладочная ветвь, вне штатной поверхности. Не дефект production-пути. |
| **IOS-SEC-003** | amfid `vm_read` double-fetch | **RULED OUT** | Два `vm_read` — из **разных** источников (`profileData` @0x100004260 и `profileAuxSig` @0x100004300), с локальным copy-out. Это не re-fetch одного объекта. Доказательство: `evidence/disasm-fragments/amfid_vm_read.txt`. |
| **IOS-SEC-004** | installd delta-manifest parser / filesystem ops | **INSUFFICIENT EVIDENCE** | Парсер корректен (bounded reader, opcode whitelist, EOF/error hygiene, canaries) — memory-defect не найден. Но structural TOCTOU (path-check→path-use без dirfd anchor) подтверждён структурно; доступный недоверенный writer и impact — `NOT VERIFIED`. `RULED OUT` не поддерживается evidence. См. ниже. |
| **IOS-SEC-005** | installd path validation / TOCTOU (общий паттерн) | **INSUFFICIENT EVIDENCE** | Path-based check/use паттерн наблюдается; provenance и access-control не восстановлены для всех callsites; безопасность паттерна в целом не доказана. Архитектурное наблюдение Phase 4 сохранено ниже. |
| **IOS-SEC-006** | AirTraffic directory-FD file ops | **ARCHITECTURAL OBSERVATION** | B3 переводит file-ops на общий dirfd + `mkdirat`/`renameatx_np`/`unlinkat` + `RENAME_NOFOLLOW`. Точные имена `0x40000000`-флага и `ENOTCAPABLE`-макроса — `NOT VERIFIED` (нет локальных заголовков); форма аргументов подтверждена. Конфайнмент корректен — это mitigation, не дефект. |
| **IOS-SEC-007** | installd/amfid entitlement parsing diff | **INSUFFICIENT EVIDENCE** | `parseEntitlements`, `AMFIUnserializeXML`, `verifyBoolEntitlement:` и DER-пути найдены; input pair с разными результатами между B2/B3 или между парсерами не найден. Differential не продемонстрирован. |
| **IOS-SEC-008** | installd unarchiver class restrictions | **RULED OUT** | Для journal/registration данных используется `decodeObjectOfClass:` + `unarchivedObjectOfClasses:fromData:error:`; `MIJournal journalEntryClasses` строит whitelist классов. Исходный claim «unarchive без ограничений» не подтверждён. |

## Ключевые уточнения

### IOS-SEC-001 — что значит «63/12»

Из 75 экспортируемых методов 63 вызывают `_ValidateMIAllowedSPIEntitlement`
(chit `com.apple.private.mobileinstall.allowedSPI`) прямо в прологе. У 12
методов прямого вызова не найдено **в исследованном фрагменте** — это не
доказывает отсутствие gate (он может быть в helper, в протокольном слое или
не требоваться для read-only операций вроде `checkCapabilities`/`getPidForTesting`).
Поэтому наблюдение, а не уязвимость.

### IOS-SEC-004 — почему статус изменился с RULED OUT на INSUFFICIENT EVIDENCE

Phase 4 присвоила `RULED OUT`, оценив условие «доступный недоверенный субъект»
как `CONTRADICTED` — на основании intended trust model: entitlement
`com.apple.private.security.storage.AppBundles`, принадлежность `_installd`,
общее знание о container-model.

Phase 5 показала, что это слабее, чем нужно для `CONTRADICTED`:

- Точные UID/GID/mode/ACL `existingBundleContainer` и его родителей — `UNKNOWN`
  (реализация MobileInstallation.framework не извлечена).
- Полный sandbox-профиль installd/helper — `NOT VERIFIED`.
- Результат `removeACLs` для каждого пути — `UNKNOWN`.
- Отсутствие **найденного** writer'а ≠ доказательство его **невозможности**.

Корректный вывод: writer не найден **и** access-control evidence неполное →
условие C `NOT VERIFIED` → `INSUFFICIENT EVIDENCE`. Уязвимость не подтверждена,
но и `RULED OUT` недоказан. См. `PHASE5/04_TOCTOU_EVIDENCE_MATRIX.md` и
`PHASE5/05_REPORT_CORRECTIONS.md`.

### IOS-SEC-005 — архитектурное наблюдение Phase 4 (сохранено)

В исследованных функциях installd наблюдается паттерн:
`realpath`/`lstat`/entity-check → path-based syscall (`link`/`mkdir`/`rename`/
`unlink`/`chmod`/`symlink`/`copyfile`), без привязки destination к dirfd.
Это законное архитектурное наблюдение; оно сохранено как описание паттерна.
Сам по себе паттерн не является ни доказанной уязвимостью, ни доказанной
безопасностью — итоговый security-статус `INSUFFICIENT EVIDENCE` отражает
неполноту access-control audit и отсутствие demonstrated impact, а не вывод
об отсутствии риска.

## Шкала статусов

- `CONFIRMED SECURITY ISSUE` — доказан дефект с impact. *Не присвоено никому.*
- `PLAUSIBLE / NEEDS VALIDATION` — есть конкретный подозреваемый дефект.
- `ARCHITECTURAL OBSERVATION` — корректное описание поведения/защиты.
- `INSUFFICIENT EVIDENCE` — ни уязвимость, ни невозможность не доказаны.
- `RULED OUT` — ключевая гипотеза опровергнута локальными доказательствами.
