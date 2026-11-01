# PHASE3 — 02_CONTROL_FLOW: статическая модель обработки delta manifest

Модель: `источник → mmap → validate header → command-loop ⟲ (read cmd →
read args → dispatch → file op) → EOF/done → cleanup`. Адреса — VADDR
`installd_B3.bin` (image base 0x100000000). Имена функций из embedded
error/log строк — надёжны как internal C names, не external symbols.

## Уровень 0 — вход и проверки перед command-stream

| Адрес / функция | Назначение | Условия переходов | Вход | Возможные ошибки |
|---|---|---|---|---|
| `sub_100002630` `hardlink_copy_hierarchy` | точка входа patch-apply | — | src/root URL, patch file path | `fts_open failed`, `realpath failed`, `not a directory` |
| open+FSTaT @0x10000271c | открыть manifest, fstat | open<0 / fstat<0 → err | path | `Could not stat`, `Could not open` |
| mmap+madvise @0x100002960-9d4 | отобразить stream | mmap fail → `Failed to map file`; `madvise failed` | fd,size | map error |
| `malloc_type_calloc` @0x1000029dc | выделить stream-object | NULL → `Failed to allocate command stream object` | size | alloc fail |
| `0x1000043e4` `read_bytes` пролог | прочитать magic (6 байт) | EOF → `Failed to read magic` | stream,buf,len=6 | short read |
| magic cmp @0x100002b0c-0x100002b20 | `w9=0x44617069` («ipaD»); `eor`+`orr`==0 → ok | mismatch → `Stream had invalid magic: %s` | 4-6 байт | bad magic → abort |
| `0x1000043e4`/`strtol` | прочитать version из header | `strtol` version ∉{1,2,3} → `Manifest had invalid version` | stream | bad version → abort |
| `validate_supported_devices` (`sub_100004460`) | сверка устройства/платформы | mismatch → `Failed to validate supported devices` | devices-list | reject |
| infoPlistHash `memcmp` @0x100003a94 | сверка Info.plist hash | mismatch → `Compare of info plist hash failed` | expected hash | reject |

## Уровень 1 — цикл commands ⟲

Цикл `hardlink_copy_hierarchy` (0x100002b44–0x100003b48) итерирует одновременно:
- `read_next_manifest_command` (`sub_100003e68`) — следующий command из stream;
- `fts_read` — следующий узел destination-иерархии (для sync-traversal).

### `read_next_manifest_command` (`sub_100003e68`, ~0x100003e68–0x100004088)

Шаги:
1. `read_bytes`/`0x1000043e4` пролог (0x100003e90-0x100003ea8): bounds-check
   `cmp x8,x9` (offset vs len); `b.ge` → EOF/error путь (`Expected to read
   %ld bytes but stream didn't have that many` @0x100003fc0).
2. Читает 1 байт команды → `ldrb` @0x100003eb8, инкремент offset.
3. **Dispatch-валидация (0x100003ecc-0x100003ef0):** `w9=cmd-0x2b`;
   `cmp w9,#0x33`; `x10=0x800040005`; `(1<<w9)&x10` → валидные опкоды.
   Декодированный set = `{'+'(0x2b), '-'(0x2d), '='(0x3d), 'N'(0x4e)}`.
   Вне set → `Stream had invalid command: %hhu` (0x10000401c) → abort.
   `'x'(0x78)` обрабатывается отдельной веткой (см. ниже).
4. Читает arg1: `0x1000043e4` с cap `w3=0x400` — читает до `\t`(0x09)/
   `\n`(0x0a) либо cap, NUL-терминирует (`strb wzr`). Не достигнут
   delimiter/cap → `Failed to read arg1 of command %hhu` (0x100003ff8).
5. Опциональный `'='`-суффикс (0x100003f14-0x100003f58): если arg1[0]=='='
   → читает число `0x1000043e4` cap `w3=0x19` → `strtoll` → `[x20,#0x408]`.
   Пустое/невалидное число → error path.
6. `'x'` extended (0x100003f60-0x100003f88): если arg1[0]=='x' и
   arg1[1..3]=='EOF' → трактуется как маркер конца (ветка `loc_100004028`),
   иначе невалидная команда.

### `0x1000043e4` `read_bytes` (read-until-delimiter, ~0x1000043e4–0x10000445c)

- Пролог: `ldp x8,x11,[x0,#8]`; `cmp x11,x8` (offset vs total) → `b.ge`
  → return/abort (защита от чтения за конец).
- Цикл: `ldrb [base+off]`, инкремент `[x0,#0x10]`; сравнивает байт с
  `\t`/\n`/`\r` (0x9/0xa) → stop; иначе `strb` в out-buf, инкремент x9;
  `ccmp x10,x3` — cap по переданной длине.
- Выход: записывает `wzr` terminator, возвращает 1; bounds exhausted → 0.
- **Ключевой факт:** читает строго внутри `[x0]` (base) + bounds из `[x0,#8]`
  — нет чтения за пределы stream; cap `0x400`/`0x19` ограничивает длину
  поля. Это **bounded line-reader**, не unbounded.

## Уровень 2 — dispatch на file-op (внутри `hardlink_copy_hierarchy`)

После `read_next_manifest_command` команда `cmd` + FTS-node `x27`
(`ldrh w8,[x27,#0x58]` = fts_info) диспатчатся по маске `0x314a`
(bits {1,3,6,8,12,13} = FTS_D, FTS_DP, FTS_F, FTS_SL, FTS_SLNONE, FTS_DNR)
и по значению `cmd`:

| cmd (декод.) | Действие (по строкам) | Проверки пути |
|---|---|---|
| `+` | create: `Making directory` (`mkdir`), `Hardlinking` (`link`), `patch_file`+`mktemp`+`rename` for files | `make_and_check_dest_path` (0x100004270) + `realpath_parent_no_symlink` (0x1000040c0) |
| `-` | remove/skip dir: `Skipping directory`, `Skipping link creation` | path check |
| `=` | set perms: `Setting final perms` (`chmod`), `Command '%c' with path %s matched relpath` | path check |
| `N` | special/new-entity handling | path check |
| `x`/`EOF` | `Hit EOF so terminating manifest processing` | — |

`make_and_check_dest_path` (`sub_100004270`, ~0x100004270–0x1000043e0):
`snprintf("%s/%s")` в 0x400-буфер → `cmp w0,#0x400` → `Dest path too long`;
`realpath` через `0x1000040c0` → `realpath'd destpath is different from
non-realpath` (anti-symlink check); error → `_CreateAndLogDMError`.

`realpath_parent_no_symlink` (`sub_1000040c0`): realpath родителя + `lstat`;
`Found symlink at destination path ... not allowed`.

## Уровень 3 — завершение

- EOF: `Hit EOF so terminating manifest processing` → выход из цикла.
- Остаток: `Got done processing bundle but there were still commands
  remaining` → состояние проверяется.
- Cleanup: `munmap`, `free`, `fts_close`, `close`, `CFRelease` — все пути
  ошибок ведут через `_CreateAndLogDMError` (`sub_100003cd8`, создаёт
  CFError и логирует, не abort-процессом).

## Возможные ошибки на каждом этапе (полный список)

magic, version, supported devices, infoPlistHash, short-read, invalid
command byte, missing arg1, bad numeric suffix, dest-path too long,
dest-path realpath mismatch, symlink-at-dest, entity-type mismatch at
dest, fts error, link/mkdir/chmod/rename/copyfile/unlink/patch_file
syscall failures, alloc/mmap failures. Каждый → `_CreateAndLogDMError`
(CFError) → возврат ошибки вызывающему, обработка прекращается.

## Вызывающие функции (context)

`hardlink_copy_hierarchy` вызывается из patch-apply пути (installd).
Прямой callsite не в `MIClientConnection` — это внутренняя helper для
patch/delta install. Все ошибки агрегируются в CFError домена
`MIInstallerDeltaErrorDomain` и передаются наверх, не приводят к abort.
