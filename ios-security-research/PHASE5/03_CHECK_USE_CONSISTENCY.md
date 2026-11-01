# PHASE5 — 03_CHECK_USE_CONSISTENCY

## 1. Наблюдаемая операция

Восстановленная последовательность для `hardlink_copy_hierarchy`:

```text
manifest command
  -> make_and_check_dest_path
  -> realpath_parent_no_symlink / lstat / entity-type checks
  -> path-based file operation
```

В Phase 3–4 подтверждены path-based calls `link`, `mkdir`, `rename`, `unlink`, `chmod`, `symlink`, `copyfile`; destination не закрепляется через dirfd. Это непосредственно подтверждает разделение check/use.

## 2. Проверяется ли тот же объект

Нет доказательства object identity.

Проверки выполняются для состояния, найденного по path-string в момент T1. Последующий syscall повторно разрешает path в момент T2. Между T1 и T2:

- path component может быть переименован;
- directory entry может быть удалён и создан заново;
- компонент может быть заменён symlink'ом;
- metadata может измениться;
- другой процесс может изменить ancestor directory, если его effective rights это позволяют.

Важно: это не утверждение, что такой субъект существует. Это следствие того, что code path не использует FD anchor.

Статус object identity: **NOT VERIFIED**.

## 3. Что именно повторно проверяется

Локально наблюдаются проверки:

- `realpath`/parent resolution;
- `lstat`;
- отсутствие symlink в проверяемой parent chain;
- сравнение resolved и raw path;
- соответствие entity type ожидаемому типу.

Не наблюдается полного повторного enforcement перед каждым use для:

- owner/group;
- mode;
- ACL;
- sandbox identity;
- object identity через inode/file ID;
- directory FD confinement;
- `RENAME_NOFOLLOW`-подобной атомарной привязки для всей операции.

`rename` и `mkstemp` имеют собственную атомарную семантику отдельных file operations, но это не делает атомарным весь check→use sequence.

## 4. Наблюдается ли защитная граница

Да, но её пределы нужно описывать точно:

- `realpath_parent_no_symlink` снижает риск symlink в уже проверенной parent chain;
- `lstat` и entity-type checks отвергают часть неподходящих состояний;
- path construction bounded;
- parser input validated;
- destination выбирается через internal `existingBundleContainer`, а не напрямую как произвольный client path.

Однако ни один из этих фактов сам по себе не доказывает:

- отсутствие изменения после проверки;
- отсутствие другого writer'а;
- корректность всех helper-service paths;
- соответствие текущих DAC/ACL/sandbox permissions ожидаемой trust model;
- отсутствие значимого результата при hypothetical mutation.

## 5. Разница между “структурное окно” и “уязвимость”

Структурно подтверждено:

1. check и use разделены;
2. use не привязан к ранее проверенному FD;
3. некоторые операции используют path resolution заново.

Не подтверждено:

1. доступен ли атакующему writer;
2. может ли writer менять именно ancestor, необходимый для перенаправления;
3. может ли изменение пройти все kernel/VFS/sandbox проверки;
4. приводит ли это к выходу из intended trust domain;
5. возникает ли повышение привилегий или иной security-relevant impact.

Поэтому корректный результат check/use audit — **CONFIRMED structural TOCTOU precondition, but not a confirmed vulnerability**.

## 6. IOS-SEC-005

IOS-SEC-005 охватывает более широкий паттерн, чем конкретный delta callsite. Для него ещё осторожнее нельзя переносить provenance `existingBundleContainer` на все `installd` file operations. Наличие одинаковых helper names или path-based imports не доказывает одинаковые input provenance, ownership и threat model во всех callsites.

Статус:

- path-based check/use pattern: **CONFIRMED**;
- universal provenance across installd: **NOT VERIFIED**;
- universal absence of untrusted writer: **NOT VERIFIED**;
- demonstrated exploit consequence: **NOT VERIFIED**.
