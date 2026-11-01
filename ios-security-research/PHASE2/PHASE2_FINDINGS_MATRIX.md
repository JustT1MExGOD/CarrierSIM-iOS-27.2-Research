# PHASE2_FINDINGS_MATRIX — матрица независимой triage-проверки

Статусы применяются в строгом смысле:
- **CONFIRMED SECURITY ISSUE** — убедительно доказан дефект безопасности;
- **PLAUSIBLE / NEEDS VALIDATION** — конкретный подозрительный дефект, но
  недостаточно доказательств;
- **ARCHITECTURAL OBSERVATION** — поведение подтверждено, признаков дефекта
  нет;
- **RULED OUT** — исходная гипотеза опровергнута;
- **INSUFFICIENT EVIDENCE** — материала недостаточно даже для конкретного
  подозрения.

## Сводная таблица

| ID | Компонент / класс | Наблюдаемый факт | Первоначальная гипотеза | Независимая проверка и доказательство | Сильнейшая альтернатива | Статус |
|---|---|---|---|---|---|---|
| IOS-SEC-001 | installd / XPC auth | `shouldAcceptNewConnection:` @0x10001b280–0x10001b33c настраивает NSXPC и возвращает 1 без inline entitlement-check | accept-all может позволить любому клиенту вызвать privileged API | `MobileInstallerProtocol` = 75 экспортируемых методов; `_ValidateMIAllowedSPIEntitlement` (`sub_10001c7c4`) и группа `0x10001e3/4xx` вызываются per-method; install/uninstall транзитивно доходят до gated validators; `_`-методы не экспортируются | Mach bootstrap/lookup ограничивает endpoint; per-method gate — штатная NSXPC-модель | **ARCHITECTURAL OBSERVATION** |
| IOS-SEC-002 | installd / test registration | `triggerRegistrationFor*` публичные обёртки сами не вызывают entitlement helper | registration/file operations могут быть доступны без проверки | `_triggerRegistrationForContent:` @0x10002bcc0 проверяет `isRunningInTestMode:outError:` + `testFlagsAreSet:#2/#0x10` + test sentinel; test-mode setters gated. `checkCapabilities:` только read-only; `getPidForTesting` = `getpid()` + reply | test-mode — штатный gate состояния; read-only методы не дают privileged write | **ARCHITECTURAL OBSERVATION** |
| IOS-SEC-003 | amfid / memory | vm_read читает profile и profileAuxSig из клиентского address space | возможен double-fetch одного изменяемого буфера | В `sub_100004030`: profile body → один `vm_read` @0x100004260; profileAuxSig → один `vm_read` @0x100004300 после `bytes`/`length`; это разные источники, успешные данные уходят в локальные out-б buffers | одноразовый copy-out — защитная схема; ошибок `vm_read` код обрабатывает | **RULED OUT** |
| IOS-SEC-004 | installd / archive parser | IPA/zip/manifest parser, EOF/type/length error paths, command-loop строки | malformed/truncated manifest может вызвать parser/OOB/state bug | Найдены `manifestFromPlistRepresentation`, type checks, `__strlcpy_chk`, `Destination path was too long`, EOF/extra-command errors; конкретный unsafe branch не реконструирован | defensive parser с явной обработкой malformed input | **INSUFFICIENT EVIDENCE** |
| IOS-SEC-005 | installd / filesystem | `realpath`, `lstat`, symlink rejection; в `hardlink_copy_hierarchy` есть `realpath→open→fstat` | realpath check → path-based write создаёт TOCTOU | `sub_1000040c0` = `realpath_parent_no_symlink` + `lstat`; отдельный write-after-check path не доказан; fd-vs-path всей install chain не установлен | staged/fd-based operation либо atomic primitive закрывает TOCTOU | **INSUFFICIENT EVIDENCE** |
| IOS-SEC-006 | AirTraffic / AFC root | B3 открывает `/var/mobile/Media/` с `0x40100000`, передаёт `x24` в *at calls, rename flag `0x20`, отказ 107 | intermediate symlink / dirfd boundary может оставить bypass-class defect | Callsite подтверждает dirfd-relative sequence и `RENAME_NOFOLLOW`; `0x40000000` name, ENOTCAPABLE macro и exact kernel policy не подтверждены; конкретный unsafe path не найден | kernel capability/namei policy может покрывать resolved path; отсутствие bypass-search ≠ невозможность bypass | **ARCHITECTURAL OBSERVATION** |
| IOS-SEC-007 | installd/amfid / entitlement parsing | XML/DER entitlement parsers и verification methods существуют | parser differential может изменить effective entitlements | `parseEntitlements`, `AMFIUnserializeXML`, DER error paths, `verifyBoolEntitlement:` найдены; input pair с разными результатами не найден | canonical signed representation + malformed-input rejection | **INSUFFICIENT EVIDENCE** |
| IOS-SEC-008 | installd / deserialization | NSKeyedUnarchiver используется для journal/registration data | unarchive без allowed-class restriction | `decodeObjectOfClass:` для root; `unarchivedObjectOfClasses:fromData:error:`; `MIJournal journalEntryClasses` создаёт NSSet из `MIInstallationJournalEntry` и передаёт whitelist | object-model side effects требуют отдельного аудита, но исходный no-whitelist claim не подтверждён | **RULED OUT** |

## Итог по статусам

- `CONFIRMED SECURITY ISSUE`: **0**
- `PLAUSIBLE / NEEDS VALIDATION`: **0**
- `ARCHITECTURAL OBSERVATION`: **3** (001, 002, 006)
- `RULED OUT`: **2** (003, 008)
- `INSUFFICIENT EVIDENCE`: **3** (004, 005, 007)

## Исправления качества доказательств

1. `amfid` не следует описывать как «полностью исследованный» во всём
   смысле: выполнена полная проверка обнаруженного `AMFIService`-интерфейса
   и всех его mutating-методов по доступному дизассемблеру; это не полный
   аудит каждого внутреннего helper/kernel path.
2. `accept connection` и `permission to invoke method` разделены: accept-all
   — отдельная архитектурная фаза, entitlement-gating — per-method/test-state.
3. Совпадение нормализованных мнемоник B2/B3 означает «не обнаружено
   различий в проанализированных instruction sequences»; оно не является
   доказательством полной побайтной идентичности, одинакового поведения
   всех зависимостей или полной идентичности кода.
4. Отсутствие найденного обхода AFC root в этом исследовании не означает
   принципиальной невозможности обхода; Phase 2 обходы не искала.
5. Локально доказанные факты отделены от общих Darwin-ожиданий: bootstrap
   restriction описан как архитектурное объяснение и пробел, пока sandbox-
   профиль installd не декомпилирован.

## Сохранность истории

Phase 1-файлы `01_INVENTORY.md`—`07_RESEARCH_PRIORITIES.md` и
`RESEARCH_SUMMARY.md` не перезаписывались. Все корректировки и уточнения
сохранены в шести `PHASE2_*.md` файлах.
