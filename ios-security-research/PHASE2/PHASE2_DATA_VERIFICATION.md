# PHASE2_DATA_VERIFICATION — IOS-SEC-004/005/007/008

Метод: независимый просмотр callsites и аннотированного дизассемблера
`installd_B3.bin` (SHA-256 `1dd5efbf…064b1d`). Строка сама по себе
не считается доказательством бага: для каждого кандидата проверены
конкретные API-вызовы и альтернативные объяснения.

---

## 1. IOS-SEC-004 — архивы и manifest command-loop

### Подтверждённые факты
В бинаре присутствуют реальные обработчики IPA/patch-архивов:

- `MIIPAPatcherManifest manifestFromPlistRepresentation:withError:`;
- `MIIPAPatcherFileManager plistRepresentationFromData:withError:`;
- `MIInstaller _manifestPathForBase:withIdentifier:patchType:error:`;
- `MIInstaller _extractPackageContainedSymlink:withError:`;
- `realpath_parent_no_symlink` и `hardlink_copy_hierarchy`.

Строки ошибок показывают проверки формата и состояния:
`Archive ... doesn't appear to be a zip archive`, `Invalid manifest file`,
`Invalid manifest, expected NSDictionary, got ...`, `Failed to read manifest
source version`, `Got manifest for version ... expected ...`, `Hit EOF so
terminating manifest processing`, `Got done processing bundle but there
were still commands remaining`, `Destination path was too long`.

Это подтверждает наличие ручного parser/state-machine и обработку ошибок,
но не подтверждает конкретный out-of-bounds или integer overflow.

### Проверки типов и архивов
- Для unarchive/manifest присутствуют type checks и error-return paths.
- Для path construction есть `__strlcpy_chk` и отдельная ошибка
  `Destination path was too long`.
- Полный цикл чтения каждой команды с восстановлением длины/границ по
  имеющемуся дизассемблеру не реконструирован до уровня доказанного
  underflow/OOB.

### Альтернативное объяснение
Это может быть корректный defensive parser: наличие сообщений `Hit EOF`,
`Invalid manifest`, `still commands remaining` скорее указывает на явную
обработку truncated/extra input, чем на её отсутствие. Install-path также
защищён системой авторизации installd и проверкой подписи устанавливаемого
артефакта.

### Итог IOS-SEC-004
**INSUFFICIENT EVIDENCE.** Поверхность парсинга подтверждена, дефект — нет.
Статус не повышается до PLAUSIBLE / NEEDS VALIDATION без конкретного
небезопасного перехода в command-loop.

---

## 2. IOS-SEC-005 — realpath и файловые операции

### Подтверждённые последовательности
1. `sub_100002630` (`hardlink_copy_hierarchy` по строкам):
   `fts_open_b` → `realpath$DARWIN_EXTSN` → `open` → `fstat`; при ошибках
   читается errno и возвращается ошибка. Также есть bounded `strlcpy_chk`.
2. `sub_1000040c0` (`realpath_parent_no_symlink` по строкам):
   вычисляет `realpath` родителя, строит путь через `strlcat/strlcpy`, затем
   делает `lstat`; при обнаружении запрещённого объекта используется ошибка
   `Found symlink at destination path "%s"; this is not allowed.`.
3. Явные методы/строки: `realpathForURL:withError:`,
   `_extractPackageContainedSymlink:withError:`,
   `Discovered invalid symlinks`, `Discovered unexpected symlinks`,
   `Entity with mode ... exists at symlink location`.

### Что доказано и чего нет
- Доказано: path canonicalization + lstat/symlink policy + отдельная
  обработка ошибок; в одном helper после realpath присутствуют файловые
  операции (`open/fstat`), но это не доказывает единый путь для каждой
  install-операции.
- Не доказано: что конкретный write/rename выполняется по path-string
  после проверки, а не по fd/atomic primitive; также не доказан интервал
  между проверкой и использованием.
- Следовательно, в доступном материале нет доказанной схемы
  `realpath(T1) → attacker mutation → write(path,T2)`.

### Альтернативное объяснение
`realpath_parent_no_symlink` может быть именно защитным preflight для
родителя, после которого операция использует fd или staged directory.
`open/fstat` в `hardlink_copy_hierarchy` совместим с объектно-ориентированной
проверкой, а не только с небезопасной строковой схемой.

### Итог IOS-SEC-005
**INSUFFICIENT EVIDENCE.** Подозрение основано на классе TOCTOU, но
конкретная check-vs-use цепочка не подтверждена.

---

## 3. IOS-SEC-007 — entitlement XML/DER differential

### Подтверждённые факты
В installd/amfid есть обработчики и строки `parseEntitlements`,
`AMFIUnserializeXML`, `Being asked to construct DER entitlements`,
`Cannot construct DER entitlements ... possibly corrupt XML`,
`verifyBoolEntitlement:`. В installd проверки подписи/entitlement связаны
с `MIInstallableBundle` и `MICodeSigningInfo`; amfid содержит AMFI trust
service и gated `verifyBoolEntitlement:`.

### Что не доказано
- Не найден конкретный XML-vs-DER input, который даёт разные entitlement
  sets.
- Не найдено расхождение между userspace parse result и подписанным
  canonical representation.
- Строка ошибки corrupt XML доказывает error path, а не parser differential.

### Альтернатива
DER/XML может быть двумя форматами одного канонического entitlement
представления с проверкой подписи до принятия решения. Ошибки могут быть
обычной диагностикой malformed input.

### Итог IOS-SEC-007
**INSUFFICIENT EVIDENCE.** Нет конкретного differential и нет основания
называть участок signing-bypass кандидатом выше общего класса риска.

---

## 4. IOS-SEC-008 — десериализация и allowed classes

### Подтверждённые факты
Проверены реальные callsites:

- `NSKeyedUnarchiver initForReadingFromData:error:` затем
  `decodeObjectOfClass:forKey:` (один ожидаемый root-класс);
- `unarchivedObjectOfClasses:fromData:error:` в нескольких местах;
- `MIJournal journalEntryClasses` строит `NSSet` из
  `MIInstallationJournalEntry`, после чего передаёт этот set как
  `allowedClasses` в `unarchivedObjectOfClasses:fromData:error:`;
- Swift callsite использует `Foundation.NSKeyedUnarchiver.unarchivedObject(of:from:)`
  с конкретным классом.

Таким образом, Phase 1 подозрение «unarchive без whitelist» опровергнуто
непосредственным кодом: whitelist/конкретный root-class действительно
используются.

### Альтернатива и остаток
Полнота whitelist для каждого вложенного класса и безопасность самих
декодируемых классов требуют отдельного анализа модели объектов. Но
отсутствие allowedClasses в одном callsite не подтверждено: основные
найденные callsites используют class restriction.

### Итог IOS-SEC-008
**RULED OUT** в исходной формулировке «unarchive без строгого ограничения
классов». Более глубокий object-model audit не нужен для текущего кандидата,
если не появится конкретный неподходящий класс или unsafe side effect.

---

## Сводка data-handling

| Кандидат | Проверенный факт | Итог |
|---|---|---|
| IOS-SEC-004 | parser/zip/manifest + многочисленные error/type/length paths | INSUFFICIENT EVIDENCE |
| IOS-SEC-005 | realpath/lstat/symlink policy; конкретный check-use gap не найден | INSUFFICIENT EVIDENCE |
| IOS-SEC-007 | XML/DER parsers есть; differential не показан | INSUFFICIENT EVIDENCE |
| IOS-SEC-008 | `decodeObjectOfClass` и `unarchivedObjectOfClasses` реально используются | RULED OUT |
