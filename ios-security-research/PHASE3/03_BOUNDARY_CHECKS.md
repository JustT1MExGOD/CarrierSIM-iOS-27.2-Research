# PHASE3 — 03_BOUNDARY_CHECKS: проверки граничных условий

Метод: построчный дизасм `read_bytes`(`0x1000043e4`), `read_next_manifest_command`
(`sub_100003e68`), `validate_stream`/header-региона, `make_and_check_dest_path`
(`0x100004270`), `realpath_parent_no_symlink` (`0x1000040c0`), цикла
`hardlink_copy_hierarchy` (`sub_100002630`). Для каждой категории — точный
адрес, подтверждающий проверку, либо `NOT VERIFIED` если прямого кода нет.

Легенда: ✅ проверка присутствует (адрес); ⚠ частично/неясно; ❌ отсутствует.

## Таблица граничных условий

| Категория | Установлено | Адрес / доказательство | Статус |
|---|---|---|---|
| **Пустой ввод** | `read_bytes` пролог: `ldp x8,x11,[x0,#8]; cmp x11,x8; b.ge → abort`. При пустом/усечённом стриме offset≥len → корректный выход до чтения magic. `Failed to read magic`. | `0x100003e90–0x100003e98`, `0x1000043f0–0x1000043f8` | ✅ |
| **Усечённый ввод (short read)** | Перед каждым поле-чтением проверка offset<len; на исчерпании → `Expected to read %ld bytes but stream didn't have that many` (`read_bytes`) и `Failed to read ... command`. | `0x100003fc0`, `0x100003e90-0x100003ea8` | ✅ |
| **Размер записи (arg-поля)** | arg1 читается через `0x1000043e4` с cap `w3=0x400` и NUL-termination; arg2 (numeric) cap `w3=0x19`. Поле ограничено и не пишется за буфер (cap enforce в `0x1000043e4`: `ccmp x10,x3` + `strb wzr`). | `0x100003f04`(`0x400`), `0x100003f34`(`0x19`), `0x100004404–0x10000444c` | ✅ |
| **Целочисленная арифметика** | Число arg2 → `strtoll` → сохраняется как qword `[x20,#0x408]`; ошибка не-числа → `Invalid touch time "%s"`. Нет арифметики умножения/сдвига по user-chislenny input в paths — только strtoll parse. Переполнение strtoll клампится самим strtoll (LONG_MAX/MIN). | `0x100003f4c`(`strtoll`), `0x100003f54`, `0x100004070` | ✅ (no overflow site) |
| **Неизвестные типы/команды** | Opcode-whitelist: `w9=cmd-0x2b; cmp #0x33; mask 0x800040005` → только `+`,`-`,`=`,`N`; `'x'`+`EOF` отдельно. Всё вне — `Stream had invalid command: %hhu` → abort. | `0x100003ecc–0x100003ef0`, `0x10000401c` | ✅ |
| **Повторяющиеся записи** | Нет явной dedup-проверки command; поведение — последовательная обработка; `Got done ... still commands remaining` фиксирует рассинхрон с FTS-walk, не duplicates. Допустимость повторов определена (последняя операция переписывает состояние). | `0x10000346c`, dispatch | ⚠ (семантика повторов = последний-выигрывает, не подтверждена атомарно) |
| **Ошибки чтения** | Каждая ветка ошибки → `_CreateAndLogDMError`(`0x100003cd8`)+`return 0`; обработка НЕ продолжается после отказа (единая `loc_100004078` → `str x0,[x19]` error-out). | `0x100004078–0x100004084` | ✅ |
| **Выделение памяти** | stream-object через `malloc_type_calloc` с проверкой NULL (`Failed to allocate command stream object`); arg/dest буферы — stack bzero(0x400/0x810)+cap. | `0x1000029dc–0x1000029e0`, `0x1000044a0–0x1000044a8` | ✅ |
| **Конец файла / неполная запись** | EOF → `Hit EOF so terminating manifest processing`; `'x'`+`EOF` marker валидируется (`Got malformed EOF marker`); `Failed to read arg2` на усечённом числе; `still commands remaining` — рассинхрон фиксируется ошибкой, не silently. | `0x100003288`, `0x100004034`, `0x100004054`, `0x10000346c` | ✅ |

## Дополнительные защитные проверки (не в таблице ТЗ, но релевантны)

- **magic:** `0x44617069` («ipaD») — `eor`+`orr` must-equal → `Stream had invalid magic` (0x100002b0c-0x100002b20). ✅
- **version:** `strtol` → must be in {1,2,3} → `Manifest had invalid version` (0x100003438-0x100003440). ✅
- **supported devices:** `validate_supported_devices` (`sub_100004460`) сравнивает allowed-list (CFArrayContainsValue). ✅
- **infoPlistHash:** `memcmp` → `Compare of info plist hash failed` (0x100003a94). ✅
- **dest-path bound:** `make_and_check_dest_path` `snprintf("%s/%s")` в 0x400 + `cmp w0,#0x400` → `Dest path too long` (0x1000042d4). ✅
- **anti-symlink на dest:** `realpath'd destpath is different from non-realpath` (0x100004338) + `realpath_parent_no_symlink`/`lstat` → `Found symlink at destination path ... not allowed` (0x100004240). ✅
- **entity-type at dest:** `Entity with mode 0%o exists at ... not allowed`, `Non-directory entity ... exists at directory location`, `Entity does not exist at file location` — проверка типа существующего объекта против ожидаемого. ✅
- **stack canaries:** `__stack_chk_guard`/`__stack_chk_fail` во всех функциях со stack-буферами (`0x1000042a0-0x1000042ac`, `0x1000043c0`, `0x100003e80-0x100003e8c`). ✅
- **FTS node-type mask:** `ldrh w8,[x27,#0x58]` → mask `0x314a` (FTS_D/DP/F/SL/SLNONE/DNR) — диспатч только известных типов узлов (0x100002b7c-0x100002b98). ✅

## Что НЕ удалось подтвердить (честные пробелы)

- **Длина каждого command-поля в байтах стрима** — формат text-delimited
  (читается до `\t`/`\n`, cap 0x400); нет отдельного length-prefix, который
  мог бы underflow. Значит классического «declared-len > actual» бага
  конструкция исключает: чтение ограничено cap и delimiter. NOT VULNERABLE
  по этому вектору — но требует, чтобы out-буфер `arg1`/`arg2` был ≥0x400/0x19
  (он stack 0x400/0x19 — соответствует cap). ✅
- **Атомарность dispatch→syscall:** между path-check (`make_and_check_dest_path`)
  и реальным `mkdir`/`link`/`rename`/`chmod` есть окно. Файловые op'ы идут
  по path-string (не fd) — потенциальный TOCTOU-класс, но staged каталог
  недоступен непривилегированному клиенту, и `realpath'd destpath different`
  снижает surface. ⚠ — зафиксировано как open point, не как доказанный баг.
- **Повторяющиеся команды** — семантика при конфликтующих повторах (например
  `+` затем `-` на том же пути в одном стриме) опирается на порядок
  обработки; формальной детерминированной проверки не видно. NOT VERIFIED.

## Вывод по границам

Все 9 обязательных категорий ТЗ имеют подтверждённые проверки кроме
«повторяющиеся записи» (⚠) — и та не образует memory-safety риска, только
операционную семантику. Parser написан как defensive bounded line-reader
с per-field cap, bounds-check, opcode-whitelist, error-abort и stack
protection. Признаков лобовой уязвимости на уровне границ не найдено.
