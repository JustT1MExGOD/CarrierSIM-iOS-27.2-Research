# PHASE4 — 04_OPERATION_SEQUENCE: последовательность проверка→использование

Метод: построчный дизасм `hardlink_copy_hierarchy` + `make_and_check_dest_path`
+ `realpath_parent_no_symlink` + file-ops. Отвечаем на 7 вопросов ТЗ.

## Восстановленная последовательность (per-entity)

```
manifest cmd (+,-,=,N) + arg1(relpath) + FTS-node(dest-entity)
  → make_and_check_dest_path: snprintf("%s/%s",destRoot,rel) → cap 0x400
  → realpath_parent_no_symlink: realpath(parent) + lstat →
       symlink-in-parent → reject; resolved-vs-raw mismatch → reject
  → entity-type match: lstat mode vs expected (file/dir/symlink) → reject
  → file-op по path-string:
       '+': link / mkdir / patch_file+mktemp+rename / symlink / copyfile
       '-': unlink / skip-dir (fts_set)
       '=': chmod (final perms)
       'N': special handling
  → следующая итерация read_next_manifest_command + fts_read
```

## Ответы на вопросы

**1. Используется ли после проверки тот же файловый объект?**
Не по fd. Проверяется path-string (realpath+lstat), затем syscall идёт по
той же path-string. Объект не «заперт» по дескриптору между check и use.
=> Технически check-vs-use по path, не по object. [OBSERVED]

**2. По строковому пути или относительно directory FD?**
По **строковому пути**. В `hardlink_copy_hierarchy` нет `*at`-вызовов
на destination (`link`,`mkdir`,`rename`,`unlink`,`chmod`,`symlink`,
`copyfile` — все path-based). `open`/`fstat`/`mmap`/`mkstemp`/`fchmod` —
на манифесте/tempfile, не на dest-объекте. [OBSERVED, HIGH]

**3. Какие свойства объекта повторно проверяются?**
- Тип объекта (`Entity with mode 0%o exists at ...`, `Non-directory entity
  ... at directory location`) — lstat перед op.
- Symlink в родительской цепочке (`realpath_parent_no_symlink`/`lstat`).
- Resolved-vs-requested path (`realpath'd destpath is different`).
- НЕ повторно: ownership/perms между check и use (fixup — в конце,
  `Setting final perms`/`standardizeOwnership`).

**4. Может ли путь измениться без изменения уже открытого дескриптора?**
Дестинационный объект не открыт как fd — он существует только как path.
=> Вопрос применим: path может быть перенаправлен symlink'ом/переименованием
компонента между check и use, потому что объекта-fd нет. НО для этого нужен
субъект с write в родитель (см. 05).

**5. Какие операции атомарны?**
- `rename` @0x10000320c — атомарная замена patched-файла (patched content
  пишется в `mktemp` + `rename` → атомарный свап содержимого). ✅
- `mkstemp` @0x100002d7c — атомарное создание temp-файла с уникальным именем.
- `mkdir`/`link`/`symlink`/`unlink`/`chmod` — НЕ атомарны по отношению к
  предшествующей path-проверке (операция на resolved-path в момент syscall).
- FTS-traversal `fts_read`/`fts_set` — последовательный, не транзакционный.

**6. Какие ограничения на символические ссылки?**
- `realpath_parent_no_symlink`: `realpath` родителя + `lstat` →
  `Found symlink at destination path ... not allowed`. Родительская
  цепочка не может содержать symlink. ✅
- `realpath'd destpath is different from non-realpath` — resolved path
  должен совпадать с запрошенным. ✅
- `Entity with mode 0%o exists at symlink location in dest path` —
  объект на позиции symlink проверяется по типу. ✅
- `Can't create/read symlink`, `Discovered invalid/unexpected symlinks` —
  контроль создания/обнаружения. ✅
- НО: `RENAME_NOFOLLOW`-эквивалента нет — `rename` без nofollow-флага;
  промежуточный symlink ниже проверенного родителя теоретически возможен
  (классический narrow TOCTOU).

**7. Независимые проверки на sandbox/VFS?**
- `seatbelt-profiles` entitlement у installd → Seatbelt-профиль (не
  декомпилирован — политика не известна, NOT VERIFIED).
- `com.apple.private.security.storage.AppBundles` — доступ к домену через
  entitlement; DAC uid `_installd` владелец.
- `realpath`/`lstat`/`entity-type` — VFS-level metadata reads.
- Повторной проверки на уровне kernel-per-op сверх DAC/path-resolution нет
  видимого — защита опирается на владельца домена + anti-symlink checks.

## Сводка последовательности

Проверка пути реальна и многослойна (realpath+lstat+type+symlink-parent),
но применяется к **path-string**, а file-op — к той же path-string позже.
Это подтверждает **структуру TOCTOU-класса** (check-vs-use по path, не по
fd), однако его эксплуатируемость определяется тем, кто может писать в
родительский каталог — см. 05.
