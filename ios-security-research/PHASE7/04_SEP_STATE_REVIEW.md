# PHASE7 — 04_SEP_STATE_REVIEW

## Путь обработки

```text
-[AMFIService getSEPStateWithReply:]   @ 0x100004c0c
 ├─ LAStorage.alloc
 ├─ [LAStorage initWithDomain:0 authenticationContext:0]
 ├─ [storage dataForKey:0xf error:&err]          → NSData (≤ 49 B used)
 ├─ on error → log + AMFIError(0x…fe68)
 ├─ on ok    → [data getBytes:&buf length:0x31]  → стековая структура 49 B
 ├─ log "returning SEP state | [exists: %u]"
 └─ reply(bufStruct, error)                      via blraa
```

## Данные, из которых формируется ответ

1. Источник: `LAStorage` (LocalAuthentication shared storage), домен `0`, без authentication context — значит **не** защищённый biometric-bound ACL (nil context = нет оценки политики на этом пути).
2. Ключ `0xf` (15) — внутренний индекс записи LAStorage; какая именно запись SEP хранится по нему — символьного имени нет. Семантика содержимого: **NOT VERIFIED по семантике полей**.
3. Размер копии фиксирован `0x31` = 49 байт — это layout ответа из methtype:

```text
{?=III{?=C{?=I[32C]}}}
   I        u32   — поле A
   I        u32   — поле B
   I        u32   — поле C
   C        u8    — байт-флаг (в дизасме отдельно сохранён из [sp,#0x80])
   I        u32   — вложенный счётчик/флаг
   C[32]    — 32-байтовый массив (digest/ID-sized blob)
   total    12+1+4+32 = 49 bytes
```

Поля по имени не размечены — по obj-c type encoding видна только структура. Лог `[exists: %u]` показывает, что одно из полей — булев признак наличия SEP-записи.

## Класс ответа

- Это **состояние подсистемы доверия (SEP-related state)**, а не секрет: API не возвращает ключи — возвращает фиксированную структуру атрибутов записи (флаги + 32-байтовое поле).
- Возможные поля: exists-флаг, версия/счётчик, метка/идентификатор записи, 32-байтовый blob (вероятный digest/UUID/хэш, размер совпадает с SHA-256). Точная семантика — **NOT VERIFIED**.
- По классу: системные метаданные / диагностика состояния; явных криптографических секретов (ключевой материал, пароли) в структуре по размеру и типу не видно.

## Различия ответов для разных клиентов

- В теле метода нет ни одной ветки по caller identity — ответ формируется одинаково для любого достигшего клиента. [OBSERVED]
- Различия по состоянию системы: если `dataForKey:` вернёт ошибку, ответ = `nil struct + NSError`; иначе struct + nil.

## Проверки внутри вызываемых функций

- `LAStorage dataForKey:error:` — библиотечный вызов; может содержать собственные ACL-проверки в LocalAuthentication.framework, но **вне** amfid и вне корпуса. При nil context вероятность внутренней caller-авторизации ниже, чем при context-bound ACL — но это **NOT VERIFIED**.
- `getBytes:length:` — простой memmove, никакой авторизации.

## Подтверждённые поля ответа

| Поле | Подтверждено | Основание |
|---|---|---|
| 3×u32 + u8 + вложенная {u32, C[32]} | CONFIRMED | `__objc_methtype` signature |
| копия ровно 49 байт | CONFIRMED | `getBytes length:0x31` |
| ошибка → AMFIError 0x…fe68 | CONFIRMED | disasm |
| семантика полей | NOT VERIFIED | имен полей нет |
| наличие секретного материала | NOT VERIFIED / unlikely по layout | поля похожи на метаданные записи |

## Риск-оценка этого метода отдельно

Getter без локального gate, возвращающий блоб состояния SEP-related хранилища. Чувствительность зависит от содержимого 32-байтового поля и флагов: если это digest/ID — утечка ограничена метаданными; если это wrapped credential — значительно хуже. Без семантики записи `dataForKey:0xf` уровень чувствительности: **LOW–MEDIUM, NOT VERIFIED**.
