# PHASE3 — 01_PARSER_IDENTIFICATION: какой именно «manifest» исследует IOS-SEC-004

## Главная проблема идентификации

В IOS-SEC-004 слово «manifest» покрывает **два разных формата** в `installd`.
Их нельзя смешивать — у них разные парсеры, разные входные данные и разный
риск. Настоящий объект IOS-SEC-004 — бинарный **delta-patch command stream**
(`delta_update.c`-стиль), а не plist-манифест.

| Аспект | Бинарный delta command stream (ОБЪЕКТ IOS-SEC-004) | Plist `MIIPAPatcherManifest` (НЕ объект) |
|---|---|---|
| Класс/функция | `hardlink_copy_hierarchy` (`sub_100002630`) + `open_delta_manifest`, `read_next_manifest_command`, `validate_stream`, `read_bytes` | `MIIPAPatcherManifest`, `manifestFromPlistRepresentation:`, `_manifestFromPlistRepresentationV1:` |
| Язык/уровень | C, ручной byte-level parser (mmap) | Objective-C, plist-API |
| Формат | magic + version + command-stream (`cmd arg1[=n]\n`) | plist (NSDictionary of arrays/strings/numbers) |
| Вход | mmap'ed patch file | plist file/data |
| Строки-маячки | `open_delta_manifest`, `Stream had invalid magic`, `read_next_manifest_command`, `Hit EOF so terminating` | `manifestFromPlistRepresentation`, `MIIPAPatcherManifestTarget` |

Оба связаны только тем, что plist-манифест указывает **на** delta-архив;
кодирование/парсинг у них раздельное. Все выводы Phase 3 относятся к
бинарному command-stream.

## Исследуемая реализация

- Бинарь: `installd_B3.bin` (`installd`, B3, arm64e; SHA-256
  `1dd5efbf…064b1d`, UUID F54A48D1-4E77-3425-BEAB-5EBBBB037C0F).
  Эквивалентная реализация в `installd_B2.bin` для diff (см. 06).
- Главная функция: **`hardlink_copy_hierarchy` = `sub_100002630`**
  (имя из embedded-строки `"hardlink_copy_hierarchy"` в error-макросах;
  имя CONFIRMED как внутреннее, не экспортируемый символ).
- Сопутствующие helpers (имена по embedded `"func_name"` в error/лог-вызовах):
  `open_delta_manifest`, `validate_stream`, `read_next_manifest_command`,
  `read_bytes`, `make_and_check_dest_path`, `realpath_parent_no_symlink`,
  `validate_supported_devices`, `_copy_symlink`, `_CreateAndLogDMError`,
  `patch_file`, `hardlink_copy_hierarchy`. Имена — из строк логов,
  надёжны как C-function names, не как external symbols.

## Входные данные и вызывающая цепочка

- **Вход:** mmap-образ patch/delta файла (`mmap` + `madvise` в
  `open_delta_manifest`), плюс root URL целевой иерархии (FTS-walk).
- **Вызывается из:** install/update path (`MIInstallableBundle` /
  `MIInstaller` patch-обработки) внутри installd — то есть данные идут
  из подписанного install-артефакта, дошедшего по gated install-path.
- **Проверки ДО парсера:** install-path entitlement gating (см. PHASE2),
  подпись/целостность пакета на уровне MIInstallableBundle
  (`performVerification`, code-sign), `validate_supported_devices`,
  сравнение `info plist hash` (`Compare of info plist hash failed`),
  `validate_stream` magic+version до первого command.

## Что НЕ проверяется перед command-stream (важно для границ)

- Подпись на каждый command-запись отдельно — стрим целиком доверяется
  после magic+version+infoPlistHash; integrity опирается на внешнюю
  подпись пакета, не на per-record MAC. Это нормально для формата, но
  значит parser обязан быть корректным к malformed input сам по себе.
