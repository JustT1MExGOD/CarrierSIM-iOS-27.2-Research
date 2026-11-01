# PHASE3_SUMMARY — installd Delta-Manifest Parser (IOS-SEC-004)

Режим: офлайн, без устройства, без фаззинга/эксплойтов, без payloads.
Объект: бинарный delta-patch command stream в `installd` (B3, идентичен B2).
Документы: 01_PARSER_IDENTIFICATION, 02_CONTROL_FLOW, 03_BOUNDARY_CHECKS,
04_MEMORY_AND_STATE, 05_VALIDATION, 06_VERSION_COMPARISON, 07_FINDING_ASSESSMENT.

## 1. Характеристика исследуемого парсера

`hardlink_copy_hierarchy` (`sub_100002630`) + C-helpers (`open_delta_manifest`,
`read_next_manifest_command`, `read_bytes`, `validate_stream`,
`make_and_check_dest_path`, `realpath_parent_no_symlink`,
`validate_supported_devices`, `patch_file`, `_CreateAndLogDMError`) —
`delta_update.c`-стиль парсер `com.apple.deltainstallcommands`.

Формат: `magic "ipaD"` + `version∈{1,2,3}` + text-delimited commands
`cmd arg1[=arg2]`, cmd ∈ {`+`,`-`,`=`,`N`}, terminator `xEOF`. Читается
из mmap-образа patch-файла, дошедшего по signed+gated install-path.
Имена функций — internal C names из embedded-строк, не external symbols.

## 2. Проверенные функции (все)

`hardlink_copy_hierarchy` (1311 ops), `read_next_manifest_command` (144),
`read_bytes` (30), `realpath_parent_no_symlink` (103),
`make_and_check_dest_path` (89), `validate_supported_devices` (211),
`_CreateAndLogDMError` (100), `sub_100003bc8`/`3bb4`/`47d0` helpers —
все разобраны построчно.

## 3. Карта потока

```
signed patch → install-path(entitlement gate) → mmap+madvise
  → validate_stream: magic(0x44617069) + version(1/2/3) + supported-devices + infoPlistHash
  → ⟲ read_next_manifest_command:
        bounds-check → 1B opcode → whitelist{+,-,=,N} → arg1(≤0x400,\t/\n) → [=arg2(≤0x19,strtoll)]
        → dispatch → make_and_check_dest_path(snprintf cap 0x400)
                      → realpath_parent_no_symlink(lstat, symlink-reject)
                      → file-op: link/mkdir/rename/unlink/chmod/symlink/copyfile (PATH-based)
  → xEOF | EOF → "Hit EOF so terminating" → cleanup(munmap/free/fts_close/close)
        error → _CreateAndLogDMError → return 0 (abort, no continue)
```

## 4. Таблица граничных условий (итог)

| Категория | Проверка | Статус |
|---|---|---|
| Пустой ввод | bounds-abort до magic | ✅ |
| Усечённый ввод | `Expected to read %ld but stream didn't have` | ✅ |
| Размеры записей | arg cap 0x400/0x19 + NUL-term | ✅ |
| Целочисленная | strtoll only; no size/index arith | ✅ |
| Неизвестные типы | opcode whitelist + `invalid command` | ✅ |
| Повторяющиеся | семантика last-wins, недетерминировано | ⚠ NOT VERIFIED |
| Ошибки чтения | единый error-abort | ✅ |
| Выделение памяти | calloc+NULL-check, stack bzero | ✅ |
| Конец файла | EOF/xEOF + malformed-EOF + still-remaining | ✅ |

## 5. Подтверждённые защитные проверки

magic `0x44617069`, version∈{1,2,3}, supported-devices CFArrayContains,
infoPlistHash memcmp, offset<len per-byte bounds, field caps, opcode
whitelist bitmask `0x800040005`, FTS node-type mask `0x314a`,
dest-path length cap, realpath-vs-rawpath compare, symlink-at-dest reject,
entity-type match, stack canaries, unified CFError error domain
`MIInstallerDeltaErrorDomain`.

## 6. Подозрительные участки

Один, и только один: **TOCTOU path-check→path-syscall**. `realpath`/
symlink/lstat проверки идут в момент T, а `link`/`mkdir`/`rename`/`chmod`/
`symlink`/`unlink`/`copyfile` — по той же path-string позже (ни одного
`*at`/fd-anchored вызова в `hardlink_copy_hierarchy`). Это реальный класс,
но не доказанный вектор.

## 7. Альтернативные объяснения

- Path-based ops — валидный выбор, потому что staged/destination-каталог
  принадлежит `_installd` и не даёт непривилегированному процессу
  write-доступа для race.
- `realpath'd destpath different` + symlink/entity-type rejects — это
  именно анти-TOCTOU защиты (проверяют resolved==requested).
- Ввод — из подписанного пакета, а не произвольный пользовательский
  поток; integrity внешний.
- Отсутствие in-parser rollback — operational atomicity на уровне
  install-journal/reverter выше, не memory-дефект.

## 8. Итоговый статус IOS-SEC-004

**INSUFFICIENT EVIDENCE** (no defect found; residual TOCTOU class open
but not demonstrated).

Обоснование: парсер — корректный defensive bounded line-reader. Ни один
memory/boundary/parser класс не подтверждён. Единственный открытый класс —
TOCTOU — не доведён до эксплуатируемого дефекта (привилегированный
staged-dir + anti-symlink checks + signed input). Парсер идентичен
B2↔B3 → это не «новая поверхность B3».

## 9. Рекомендации для следующего этапа

1. **Кто может писать в staged-каталог в окно TOCTOU** — найти
   callsite/ownership staged install dir; если непривилегированный процесс
   не имеет write → TOCTOU RULED_OUT окончательно.
2. **Атомарность install-пути** — есть ли журналирование/откат, которое
   закрывает «частично применённые изменения» при abort.
3. Если нужен дальнейший static pass — разобрать `patch_file` (читает
   ли он второй источник/применяет delta-патч к содержимому файлов) —
   это единственный не до конца разобранный helper, потенциально
   несущий второй parser (file-content delta).
