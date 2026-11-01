# PHASE3 — 04_MEMORY_AND_STATE: анализ памяти, состояния и TOCTOU

Метод: построчный дизасм `hardlink_copy_hierarchy` (`sub_100002630`),
`read_next_manifest_command`, `read_bytes`, `make_and_check_dest_path`,
`realpath_parent_no_symlink`, `patch_file`. Цель — найти основания для
OOB/overflow/UAF/double-free/uninit/state-desync; **без заявлений о
memory corruption без доказательств**.

---

## 1. Out-of-bounds read/write — НЕ найдено доказанного сайта

- `read_bytes` (`0x1000043e4`) — bounded reader: bounds `cmp offset,len`
  перед каждым байтом, cap `0x400`/`0x19` на поле, NUL-termination
  (`strb wzr`). Чтение строго внутри `base..base+len` mmap-стрима. ✅
- arg-буферы — stack `bzero(0x400)`/`bzero(0x810)`, размеры согласованы с
  cap → соответствие buffer≥cap. ✅
- `snprintf("%s/%s")` в 0x400-dest с `cmp ret,#0x400` → `Dest path too long`.
  Нет unbounded strcpy/strcat в path-construction (используется
  `__strlcpy_chk`, `snprintf`, `strlcat` с cap). ✅
- Нет прямого memcpy/read по user-controlled length-prefix — формат
  text-delimited, не length-prefixed. Классического «declared>actual»
  OOB вектора нет. ✅
- Stack canaries `__stack_chk_guard`/`__stack_chk_fail` во всех функциях
  со stack-буферами. ✅

## 2. Integer overflow / truncation — НЕ найдено

- Единственное user-numeric поле — arg2 → `strtoll` (64-bit, клампится
  libc к LONG_MAX/MIN, ошибка не-числа → `Invalid touch time`). Результат
  идёт в `[x20,#0x408]` (mtime) — не в size/index арифметику.
- Нет user-controlled size, подаваемого в malloc/memcpy/off arithmetic.
  `malloc_type_calloc` вызывается с константным размером stream-object.
- Сравнения длин — `cmp x11,x8`/`cmp w0,#0x400` — над корректными типами.

## 3. Use-after-free / double-free — НЕ найдено

- Cleanup-пути (`munmap`,`free`,`fts_close`,`close`,`CFRelease`)
  выполняются один раз на выходе; error-пути возвращают CFError через
  out-param, не продолжают использовать освобождённое.
- CF-объекты (`CFString`, `CFDictionary`, `CFError`, `CFArray`) —
  release/cbз-паттерн согласован; `expected_infoplisthash is NULL`
  проверяется. Нет явного double-CFRelease в разобранных ветках.

## 4. Неинициализированные данные — НЕ найдено

- Все stack-буферы предварительно `bzero` (0x1000042b0 `bzero 0x400`,
  `0x100003c30` `bzero 0x400`, `0x100003c3c` `bzero 0x400`).
- Стрим-структура через `calloc` (zero-init).
- Возвраты инициализируются до использования (`str wzr`, `str xzr`).

## 5. Несогласованность состояния после ошибки — ЧАСТИЧНО

- `Got done processing bundle but there were still commands remaining`
  — фиксируется как ошибка, не молчаливый успех. ✅
- Но: обработка применяет file-ops инкрементально (`mkdir`,`link`,`rename`,
  `chmod`, `symlink`, `unlink`, `copyfile`). При сбое в середине стрима
  часть изменений уже применена — **нет транзакционного отката** видимого
  в `hardlink_copy_hierarchy`. Откат, если есть, на уровне install-journal/
  reverter выше, не в этом парсере. ⚠ — operational atomicity, не memory bug.

## 6. TOCTOU — ЕДИНСТВЕННЫЙ СТОЯЩИЙ КЛАСС-РИСК (не доказан как дефект)

**Факт [OBSERVED, HIGH]:** все file-ops в `hardlink_copy_hierarchy` —
**path-based**, ни одного `*at`/fd-anchored вызова:
```
0x100002fcc link      0x100003170 mkdir   0x10000320c rename
0x10000321c unlink    0x1000030a8 chmod   0x1000030f8 symlink
0x100003040 copyfile  0x100002fcc link    0x1000032f8 chmod
```
**Гипотеза (не доказанная):** `make_and_check_dest_path` +
`realpath_parent_no_symlink`/`lstat` проверяют путь в момент T; syscall
(`link`/`mkdir`/`rename`/`chmod`/`symlink`) выполняется по той же
path-string позже в T+Δ. Если между ними компонент пути подменяется
symlink'ом, проверенный путь ≠ использованному объекту.

**Что это закрывает/смягчает:**
- `realpath'd destpath is different from non-realpath` — проверка, что
  resolved-путь совпадает с запрошенным (детект подмены).
- `Found symlink at destination path ... not allowed` — отказ на symlink.
- `Entity with mode ... exists at ... not allowed` — проверка типа.
- Стадия/destination — staged install dir под installd (`_installd`),
  недоступная непривилегированному клиенту → race требует уже иметь
  write в этот каталог (локальный/installd-привилегия), что сужает
  практическую эксплуатируемость.
- Данные — из подписанного patch-пакета (external integrity), а не
  произвольный пользовательский ввод напрямую.

**Вердикт по TOCTOU:** класс существует структурно (path-check затем
path-use), но окно узкое и целевой каталог привилегирован — это
**PLAUSIBLE-класс без доказанного вектора**, не CONFIRMED defect.
Для подтверждения потребовалось бы показать: (а) реальное окно между
`make_and_check_dest_path` и syscall, (б) что атакующий может писать в
целевую иерархию между ними, (в) что результат даёт запись за пределы
staged-area. Ничего из этого не доказано офлайн.

## Сводка

| Класс | Статус |
|---|---|
| OOB read/write | NOT FOUND (bounded reader, caps, canaries) |
| Integer overflow | NOT FOUND (strtoll только) |
| UAF / double-free | NOT FOUND |
| Uninitialized data | NOT FOUND (bzero/calloc) |
| State-desync после ошибки | PARTIAL — нет in-parser rollback (operational) |
| TOCTOU path-check→path-use | PLAUSIBLE-CLASS, недоказанный вектор |

**Заявлений о memory corruption нет** — это корректно по материалу.
Единственный стоящий вопрос — TOCTOU, и он не доведён до доказанного
дефекта из-за привилегированности staged-каталога и anti-symlink checks.
