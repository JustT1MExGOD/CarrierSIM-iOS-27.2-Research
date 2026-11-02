# PHASE8 — 06_INFORMATION_SENSITIVITY

## `getSEPStateWithReply:`

### Подтверждённая структура

Из ObjC type encoding `v24@0:8@?<v@?{?=III{?=C{?=I[32C]}}}@"NSError">16` и `getBytes:length:0x31` подтверждено 49 байт:

```text
{ u32, u32, u32, { u8, { u32, u8[32] } } }
```

Дизассемблер не даёт names для полей. Лог `returning SEP state | [exists: %u]` подтверждает существование отдельного presence-related значения, но не его точное смещение.

### Происхождение

- `LAStorage alloc/initWithDomain:0 authenticationContext:0`;
- `dataForKey:0xf error:&error`;
- fixed-size copy from returned `NSData`.

### Назначение key 0xf

В доступном корпусе нет `LocalAuthentication.framework` implementation, public/private header или symbolic mapping, который связывает numeric key `0xf` с конкретным именем. Назначение: **NOT VERIFIED**.

### Чувствительность

По layout нет доказательства raw key material, credential, token или PII. 32-byte field может быть digest/identifier/state blob, но это inference по размеру. Наиболее обоснованный класс: **internal system/diagnostic metadata, LOW–MEDIUM sensitivity**.

Нет локального доказательства, что Apple запрещает раскрывать эту структуру обычному приложению; нет и доказательства обратного. Вопрос зависит от transport reachability и semantic mapping key 0xf.

## `getStagedProfileWithReply:`

### Подтверждённый источник и формат

- fixed path: `/private/var/db/amfid/UPPStaging.plist`;
- API: `NSString stringWithContentsOfFile:encoding:4:error:`;
- ответ: full decoded UTF-8 string or nil + NSError;
- plist parser/filter/field removal: not present in handler.

### Связь с staging writer

`stageProfileForUuid:` writes its NSString input to the same fixed path and requires `com.apple.private.amfi.schedule-profile`. Its log says `attempting to stage: %@`; getter log says `acquiring staged UUID`. These facts support the inference that normal content is a staged UUID/string, not a complete provisioning profile.

Это не исключает другого writer'а или другого file content: getter returns whatever UTF-8 text is in the file. Exact file contents, size and ACL are intentionally not extracted from a device.

### Чувствительность

- UUID/opaque staging identifier: LOW direct sensitivity;
- pending provisioning state: LOW–MEDIUM metadata sensitivity;
- arbitrary additional file content: **UNKNOWN**, because no runtime file sample or complete writer inventory exists.

Нет доказательства, что response is a secret. Но отсутствие filtering означает, что sensitivity cannot be bounded by the method name alone.

## Общий verdict

Информационная чувствительность обоих ответов не подтверждает protected-secret disclosure. Это не отменяет architectural asymmetry: two getter methods return internal state without visible method gate. `E` condition for a security issue remains **NOT VERIFIED**, not CONFIRMED.
