# PHASE3 — 06_VERSION_COMPARISON: Beta 2 vs Beta 3 по delta-парсеру

Метод: нормализованный mnemonic-diff (последовательность инструкций на
функцию, адреса/иммедиаты, зависящие от сдвига, отброшены). Объект —
C-функции delta-парсера (`sub_*`, не ObjC-методы) в
`installd_B2.bin` vs `installd_B3.bin`.

- B2 `installd_B2.bin`: SHA-256 `f0f1ce4b…8576f`, UUID 5D0437D3-…
- B3 `installd_B3.bin`: SHA-256 `1dd5efbf…064b1d`, UUID F54A48D1-…

## Результат: функции идентичны

| Функция | ops B2 | ops B3 | Идентична |
|---|---|---|---|
| `sub_100002630` `hardlink_copy_hierarchy` | 1311 | 1311 | ✅ да |
| `sub_100003bb4` | 4 | 4 | ✅ |
| `sub_100003bc8` | 67 | 67 | ✅ |
| `sub_100003cd8` `_CreateAndLogDMError` | 100 | 100 | ✅ |
| `sub_100003e68` `read_next_manifest_command` | 144 | 144 | ✅ |
| `sub_1000040c0` `realpath_parent_no_symlink` | 103 | 103 | ✅ |
| `sub_100004270` `make_and_check_dest_path` | 89 | 89 | ✅ |
| `sub_1000043e4` `read_bytes` | 30 | 30 | ✅ |
| `sub_100004460` `validate_supported_devices` | 211 | 211 | ✅ |
| `sub_1000047d0` | 143 | 143 | ✅ |

Все 10 функций delta-парсера — **побайтово идентичные mnemonic-последовательности**.
51 связанная embedded-строка также идентична (`open_delta_manifest`,
`read_next_manifest_command`, `hardlink_copy_hierarchy`, `read_bytes`,
`validate_stream`, `make_and_check_dest_path`, `realpath_parent_no_symlink`,
`patch_file`, `delta_update.c`, `com.apple.deltainstallcommands.`).

## Интерпретация

- **Парсер НЕ менялся B2→B3.** Apple в B3 правил AirTraffic/AFC-confinement
  и install-path validation, но не delta-manifest parser.
- Следствие: IOS-SEC-004 не является «появившейся в B3» поверхностью —
  parser стабилен между бетами; если в нём есть дефект, он присутствует
  в обеих.
- НИ одного добавленного boundary-check / error-handling / size-check
  B2→B3 в этом парсере нет — код не был предметом недавнего security-
  ужесточения (в отличие от AirTraffic).

## Оговорка про «идентичность»

«identical» здесь = одинаковая нормализованная последовательность
мнемоник, не гарантия побайтовой идентичности (различия в UUID/build-id
есть). Для вывода о security-поведении это достаточный уровень:
структура проверок и dispatch не изменилась.
