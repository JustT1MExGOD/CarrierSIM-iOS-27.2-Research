# PHASE9 — 05_FORMAT_VALIDATION_REVIEW

## Метод

Аудит валидации форматов доверия: Mach-O, SuperBlob, CodeDirectory, CMS,
entitlements, provisioning profiles. Для каждого формата фиксируется: где
в доступном коде происходит (или должна происходить) проверка, какие
проверки **видны**, а какие делегированы MISSING-компонентам.

Принцип: присутствие строки `"Cannot construct DER entitlements"` — это
доказательство наличия error-path, а не доказательство полноты валидации.
Полноту проверяем только там, где видны конкретные проверки.

---

## 1. Mach-O

**Видимые проверки в amfid/installd:** НЕТ.

`AMFIPathValidator` (`initWithURL:withFileOffset:withFlags:`) принимает
URL + file offset — это интерфейс для валидации **внутри Mach-O** (fat
binary может содержать несколько архитектур, file offset выбирает slice).
Но сама проверка Mach-O header, magic, load commands, `LC_CODE_SIGNATURE`
— внутри MISSING CoreTrust / dyld.

В amfid дизассемблере нет прямого парсинга `MH_MAGIC`, `mach_header`,
`load_command` — только вызов validator'а. В installd — `MICodeSigningInfo`
вызывается с audit token / bundle, без прямого Mach-O парсинга в показанных
фрагментах.

Статус: **PARSE LOGIC NOT VISIBLE — [DELEGATED]**. Параметр `withFileOffset`
подтверждает, что validator принимает slice-aware input (fat binary support),
но корректность парсинга не проверяема.

---

## 2. SuperBlob

**Видимые проверки:** НЕТ.

SuperBlob (`CS_SuperBlob`) — контейнер, в котором лежат CodeDirectory,
requirements, entitlements, CMS. Его индексы (`CSSLOT_CODEDIRECTORY`,
`CSSLOT_ENTITLEMENTS`, `CSSLOT_CMS`) и `magic`/`count` — внутри MISSING
code-signing framework.

В amfid есть `computedCdHash` — результат хэша **CodeDirectory**, т.е.
validator уже дошёл до CD. Но как он нашёл CD внутри SuperBlob — не видно.

В `sub_10000366c` (DER entitlement) XML entitlements приходят **уже
извлечёнными** — функция принимает готовый XML blob, а не SuperBlob.
Извлечение entitlement'ов из SuperBlob — где-то раньше, в недоступном коде.

Статус: **PARSE LOGIC NOT VISIBLE — [DELEGATED]**.

---

## 3. CodeDirectory

**Видимые проверки:** косвенные.

`computedCdHash:withLength:` (в `sub_100004030`) возвращает хэш CD —
подтверждает, что validator вычисляет/хранит хэш CodeDirectory. Сам CD
парсится в MISSING компоненте. Видимые поля CD (`hashType`, `hashSize`,
`nCodeSlots`, `nSpecialSlots`, `codeLimit`, `flags`, `scatterOffset`,
`teamOffset`, `execSegBase/Limit/Flags`, `runtime`, `linkage`) — не
проверяются в доступном коде.

Один видимый boundary check: в caller `sub_10000b194` входной msgh
проверяется на минимальный размер (`0x428`) и на alignment (`w21-0x40 ≥
rounded_len`). Это проверка **размера входного сообщения**, не CD.

Статус: **PARSE LOGIC NOT VISIBLE — [DELEGATED]**. Только результат
(`computedCdHash`) доступен.

---

## 4. CMS (Cryptographic Message Syntax)

**Видимые проверки:** НЕТ.

CMS-подпись (цепочка сертификатов, signerInfo, contentInfo, detached
signature) — в MISSING Security.framework / CoreTrust. В amfid есть строка
`"couldn't lookup detached certificates"` — подтверждает, что detached
certificate lookup где-то выполняется (в MIS/CoreTrust), но сама проверка
не видна.

Строки `trustTeamID:signature:error:`, `MISCopyProvisioningProfile`,
`signingIdentitiesWithTeamID:` — MIS/libmis calls, реализация недоступна.

Статус: **PARSE LOGIC NOT VISIBLE — [DELEGATED]**.

---

## 5. Entitlements (XML plist)

**Видимые проверки — в `sub_10000366c`** (`amfid_B3_disasm.txt:1860-2125`):

| Проверка | Где | Что проверяет |
|---|---|---|
| `xml_len >= 8` | `0x100003714` (`cmp w23,#0x8; b.hs`) | минимальный размер входного blob (8-байтовый header + XML) |
| null-termination | `0x100003750` (`strb wzr,[x23,x24]`) | завершение скопированного XML строки |
| `CFDataCreateWithBytesNoCopy` не NULL | `0x1000037a4` | успешное создание data wrapper |
| `CFPropertyListCreateWithData` не NULL | `0x1000037c4` | XML — валидный plist |
| `CFGetTypeID == CFDictionaryGetTypeID` | `0x1000037dc` | root — словарь, не другой plist type |
| `CESerializeCFDictionary == kCENoError` | `0x1000039e0` | сериализация в DER успешна |
| `vm_read` == 0 | `0x100003a64` | копия в клиентский buffer успешна |
| 0xAA-poison out buffer | `0x100003728` | до записи — canary-fill |

Это **подтверждённая цепочка**: вход → plist parse → type check → DER
serialize → copy out. Каждый этап имеет error-path. Отсутствие проверки
«не dictionary → ошибка» — покрыто (`typeID != CFDict → entitlement anomaly`).

**НЕ видимые проверки:**
- Содержимое словаря (какие ключи разрешены, какие значения допустимы) —
  не проверяется в `sub_10000366c`. Это уровень entitlement *semantics*,
  не *syntax*. Делегировано downstream-коду.
- Соответствие entitlement'ов подписи (что DER соответствует подписанному
  CD) — не видно. `construct_der_entitlements` просто сериализует
  предоставленный XML; связь с подписью — в вызывающей цепочке, недоступна.

Статус: **SYNTAX VALIDATION CONFIRMED; SEMANTIC VALIDATION [DELEGATED]**.

---

## 6. Provisioning profiles

**Видимые проверки:** только копирование.

`profileData` / `profileAuxSig` в `sub_100004030` — это уже **готовые**
объекты из validator'а (`[validator profileData]`). amfid их только
копирует через `vm_read` в ответ. Сама валидация профиля (expiry, team ID,
device list, entitlements match, signature) — внутри MISSING MIS/CoreTrust.

`MISCopyProvisioningProfile`, `trustTeamID:signature:error:`,
`signingIdentitiesWithTeamID:`, `MISProfileDBClient` — вызовы в amfid,
но реализация профиля-валидации недоступна.

В `sub_100004030` видимые проверки профиля:
- `profileData != NULL` → copy; `== NULL` → `profile_valid=0` (не ошибка).
- `vm_read` success/fail → `profile_valid` flag.

Это проверки **наличия и копируемости**, не **валидности** профиля.

Статус: **PROFILE VALIDATION [DELEGATED]**; копирование — корректно
защищено флагами.

---

## 7. Входные данные MIG (msgh)

Видимые проверки в caller `sub_10000b194` / `sub_10000b3d8`:

| Проверка | Где |
|---|---|
| msgh_id в диапазоне `0x3e8`-`0x3f4` или `0x441`+ | `sub_10000b15c` (subsystem range check) |
| msgh_size >= минимум для данного msg_id | `cmp w21,#0x428` / `#0x38` / `#0x43c` |
| OOL descriptor count/length соответствие | `cmp` на `0x400`, `0x1f` лимиты |
| NDR_record | `__got._NDR_record` |
| memchr for NUL в variable part | `0x10000b21c`, `0x10000b3e0` |
| msgh_bits complex flag | `tbnz w8,#0x1f` |

Это **строгая проверка входного сообщения** — размер, alignment, наличие
NUL-terminator, корректность OOL-дескриптора. Стандартная MIG stub
генерация + дополнительные ручные проверки.

Статус: **MIG INPUT VALIDATION CONFIRMED** (размеры, alignment, NUL,
OOL-дескрипторы).

---

## 8. Сводная матрица формат-валидации

| Формат | Где валидируется | Видно в коде? | Статус |
|---|---|---|---|
| Mach-O | CoreTrust / dyld | НЕТ | `[DELEGATED]` |
| SuperBlob | code-signing framework | НЕТ | `[DELEGATED]` |
| CodeDirectory | code-signing framework | только `computedCdHash` результат | `[DELEGATED]` |
| CMS | Security.framework / CoreTrust | НЕТ (только строки ошибок) | `[DELEGATED]` |
| Entitlement XML syntax | `sub_10000366c` | ДА — plist parse, type check, DER serialize | CONFIRMED (syntax) |
| Entitlement semantics | downstream | НЕТ | `[DELEGATED]` |
| Provisioning profile | MIS / CoreTrust | только copy flags | `[DELEGATED]` |
| MIG input message | stub callers | ДА — size, alignment, NUL, OOL | CONFIRMED |
| Entitlement→CD link | недоступно | НЕТ | `NOT VERIFIED` |

---

## Вывод

Из всех форматов доверия **полностью видимую валидацию** имеет только
entitlement XML (syntax-level: plist parse + type check + DER serialize)
и входное MIG-сообщение (size/alignment/NUL/OOL). Все остальные форматы —
Mach-O, SuperBlob, CodeDirectory, CMS, provisioning profile semantics —
делегированы MISSING-компонентам и их валидация не проверяема.

Ключевой пробел: **связь entitlement↔подпись** не видна. `construct_der_entitlements`
сериализует предоставленный XML без видимой проверки, что этот XML — именно
тот, что подписан в CodeDirectory. Если связь существует — она в вызывающей
цепочке MIG-клиента или в CoreTrust; локально `NOT VERIFIED`.
