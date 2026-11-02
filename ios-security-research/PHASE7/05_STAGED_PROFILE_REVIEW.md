# PHASE7 — 05_STAGED_PROFILE_REVIEW

## Путь обработки

```text
-[AMFIService getStagedProfileWithReply:]   @ 0x100006230
 ├─ log "acquiring staged UUID"
 ├─ [NSString stringWithContentsOfFile:
 │      @"/private/var/db/amfid/UPPStaging.plist"
 │      encoding:NSUTF8(4) error:&err]
 ├─ on error → log "unable to read staged file" → reply(nil, err)
 ├─ on ok    → reply(fileContentsString, nil)
 └─ единый выход loc_1000062f0 → blraa
```

## Проверка предполагаемой связи с `/private/var/db/amfid/UPPStaging.plist`

1. **Путь подтверждён:** CFString-константа `"/private/var/db/amfid/UPPStaging.plist"` загружается в x2 и передаётся в `stringWithContentsOfFile:encoding:error:` @0x1000062b4–0x1000062c0. [CONFIRMED]
2. Тот же путь используется `stageProfileForUuid:withReply:` для **записи** (`writeToFile:atomically:encoding:error:` @0x100006010). Пара stage/commit/get образует единый staging-механизм UPP (User-Approved-Profile?) provisioning.

## Характер чтения

- `stringWithContentsOfFile:encoding:error:` читает **файл целиком** в строку — никакой выборки полей, фильтрации ключей или частичного разбора нет. [CONFIRMED по API]
- Никакого plist-parse (`propertyListWithData:`/`NSPropertyListSerialization`) в методе нет — возвращается **сырой текстовый контент**, а не разобранный словарь. Следовательно «метод возвращает весь plist-файл как текст» — подтверждено API-семантикой, а не названием.
- Преобразования содержимого нет: строка передаётся в reply как есть.

## Какие поля могут попасть в ответ

- Всё, что записано в `UPPStaging.plist`. Кто пишет: `stageProfileForUuid:` пишет `NSString` (аргумент `Uuid`) тем же `writeToFile:atomically:` — то есть файл по идее содержит **UUID строку**, не полный профиль. [INFERRED из write-side: параметр `stageProfileForUuid:` — NSString uuid; метод writeToFile пишет именно переданную строку]
- Из write-side следует: `getStagedProfile` возвращает с большой вероятностью **UUID, запланированный к provisioning**, — идентификатор, а не профильные данные. Лог-сообщение `acquiring staged UUID` это подтверждает текстом.
- Однако файл лежит в `/private/var/db/amfid/` — зона с ограниченным доступом; если другой компонент дописывает в файл больше данных, getter вернёт их целиком. Содержимое при пустом staging: отсутствует → NSError.

## Проверки перед чтением

- Никаких: метод не проверяет caller, не проверяет существование/права файла отдельно — ошибка чтения обрабатывается как NSError в ответе. [OBSERVED]

## Проверки перед отправкой ответа

- Никаких фильтрующих/логирующих-и-обрезающих шагов: `blraa` вызывается сразу после логов ошибки/успеха. [OBSERVED]

## Сравнение с write-side авторизацией

| Операция | Gate |
|---|---|
| `stageProfileForUuid:` (write) | `verifyBoolEntitlement:@"com.apple.private.amfi.schedule-profile"` @0x100005f9c |
| `getStagedProfileWithReply:` (read) | **нет** |
| `commitProfileForUuid:` (commit) | `verifyBoolEntitlement:@"com.apple.private.amfi.commit-profile"` |

Асимметрия: записать staged UUID требует entitlement, прочитать — нет. Это консистентно с моделью «чтение дешевле записи», но также означает, что значение, установленное только привилегированным клиентом, может быть прочитано любым достигшим endpoint субъектом — классический read-side information disclosure pattern, **если** reachability подтвердится.

## Классификация риска

- Что реально возвращается: staged UUID string (идентификатор профиля provisioning). 
- Чувствительность UUID как такового: низкая–средняя — это opaque-идентификатор, а не криптоматериал. Однако он может раскрывать состояние pending-provisioning и служить oracle/коррелятором для атак на profile pipeline.
- Фильтрация отсутствует → если файл когда-либо содержит больше, чем UUID, утечка расширяется. Семантически метод обещает «staged profile», а по write-side чаще всего UUID — расхождение имени и содержимого само по себе маленький architectural smell.
