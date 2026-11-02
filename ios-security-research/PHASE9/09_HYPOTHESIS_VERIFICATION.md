# PHASE9 — 09_HYPOTHESIS_VERIFICATION

## Метод

Независимая проверка каждой гипотезы из `08_SECURITY_HYPOTHESES.md`.
Для каждой: что подтверждено кодом, что требуется для подтверждения,
чего не хватает. Финальный статус — по шкале CONFIRMED /
ARCHITECTURAL OBSERVATION / INSUFFICIENT EVIDENCE / LIKELY NOT
EXPLOITABLE / LIKELY BY DESIGN / RULED OUT.

Верификация выполнена по первичным callsites, а не по выводам других
отчётов.

---

## P9-H1: Составной ответ `verify_code_directory` допускает isValid=1 + empty profile

### Проверка

Первичный код (`amfid_B3_disasm.txt:2547-2798`):

```text
0x100004068–0x10000409c:  zero все out-поля (init)
0x1000041c4:  validateWithError: → cbz → fail path
0x1000041e8:  computedCdHash → out
0x1000041f0:  signerType → out
0x1000041fc:  isValid → out
0x100004208:  areEntitlementsValidated → out
0x100004214:  profileData → cbz → skip copy
0x100004260:  vm_read(profileData bytes,len) → cbz → loc_100004328 (fail path)
0x1000042b8:  profileAuxSig → cbz → skip
0x100004300:  vm_read(aux bytes,len) → cbz → log, zero aux fields, continue
0x1000043d8:  ret
```

Fail path `loc_100004328` (`amfid_B3_disasm.txt:2700-2760`): release
objects → общий epilog → `ret`. Перед ret **нет** повторного обнуления
`isValid`/`signerType`/`cdHash`/`areEntitlementsValidated`.

### Подтверждено кодом

1. `isValid` записывается при `validateWithError:`=success, **до**
   `profileData`/`vm_read`. ✅
2. При `vm_read` fail на `profileData` — переход в fail path без
   обнуления уже записанных полей. ✅
3. Caller `sub_10000b194` (`amfid_B3_disasm.txt:10566-10604`) копирует
   все поля в reply без дополнительной проверки `profile_valid`. ✅
4. Reply **может** содержать `isValid=1` + `profile_valid=0`. ✅

### Чего не хватает для уязвимости

- Условие `vm_read` fail на валидном `profileData` — редкое (объект
  получен от validator'а, память уже доступна; vm_read fail возможен при
  racing unmap, что маловероятно внутри того же вызова).
- Клиентский артефакт, показывающий, что MIG-клиент игнорирует
  `profile_valid`. Отсутствует.
- Доказательство, что `isValid=1 + empty profile` приводит к неправильному
  решению. Не доказано.

### Финальный статус

**ARCHITECTURAL OBSERVATION.** Подтвержденная асимметрия полей в ответе —
`isValid` не сбрасывается при fail на profile copy. Для уязвимости нужен
клиент, доверяющий `isValid` без проверки `profile_valid`. Без него —
наблюдение, не дефект. Семантически корректный клиент, проверяющий
`profile_valid`, увидит «valid signature, no profile data».

---

## P9-H2: Отсутствие видимой связи XML↔подпись в `construct_der_entitlements`

### Проверка

`sub_10000366c` принимает `x0=xml_ptr`, `x1=xml_len` — уже извлечённый
XML blob. Никакого параметра «ссылка на файл/CD» в сигнатуре нет —
только token, xml, out-params. Проверка token ≠ 0 (`0x100003690-0x1000036a8`)
— единственная input-auth.

### Подтверждено кодом

1. Функция сериализует предоставленный XML без проверки его источника. ✅
2. Security token проверяется — клиент аутентифицирован. ✅
3. Нет параметра, связывающего XML с конкретным файлом. ✅

### Чего не хватает для уязвимости

- Кто вызывает `construct_der_entitlements` — недоступно. Если вызывает
  kernel AMFI hook после собственной проверки CD — связь установлена
  upstream. Если вызывает daemon — неизвестно.
- Security token — доверенный идентификатор; клиент с правильным token
  по определению privileged.
- Downstream проверка DER↔CD — может быть в MISSING CoreTrust/kernel.

### Финальный статус

**INSUFFICIENT EVIDENCE.** Отсутствие видимой связи — факт, но функция
— это сериализатор, не валидатор; связь может быть установлена upstream
в вызывающей цепочке (kernel hook сам знает, для какого файла запрашивает
DER). Без клиентского артефакта — не подтверждено.

---

## P9-H3: MIG endpoint может быть reachable непривилегированному клиенту

### Проверка

`bootstrap_check_in("com.apple.MobileFileIntegrity")` (`sub_1000049c8`)
— регистрация. `dispatch_mach_mig_demux` (`sub_100004a24`) — обработка.
Нет NSXPC entitlement; единственная проверка — security token в msg.

### Подтверждено кодом

1. Endpoint зарегистрирован у launchd. ✅
2. MIG stub'ы не проверяют client entitlement — только token. ✅
3. `mach-lookup`/`AppleMobileFileIntegrity` строки в sandbox kext —
   Phase 8. ✅

### Чего не хватает для уязвимости

- Декодированное sandbox/mach-lookup правило — НЕ декодировано.
- Демонстрация, что `security token` не является достаточной проверкой
  (token проверяется ≠0, но что такое token — не разобрано).
- Даже при reachability — результат read-only (trust record, DER blob).
  State change отсутствует.

### Дополнительное соображение

Security token в MIG msg — это audit token отправителя, проверяемый
ядром. Проверка «token ≠ 0» в `sub_100004030`/`sub_10000366c` — это
проверка «сообщение содержит валидный token», не «клиент имеет право».
Однако сам факт, что token встроен в MIG-протокол, указывает на то,
что endpoint **ожидает** доверенного клиента (kernel). Обычно MIG
endpoints с security token — это kernel↔daemon интерфейс, не общедоступный.

### Финальный статус

**INSUFFICIENT EVIDENCE.** Endpoint есть; правила reachability не
декодированы; предполагаемый клиент — kernel hook (не обычное приложение).
Даже при достижимости — read-only результат. Не поднимается до
подтверждённой поверхности атаки.

---

## P9-H4: `codeSigningEnforcementIsDisabled` — точка обхода

### Проверка

5 callsites в B3 (`91801, 92578, 96157, 96271, 98149`), 5 в B2. Все —
`objc_msgSend(MIDaemonConfiguration, "codeSigningEnforcementIsDisabled")`
— чтение bool. Видимых callers к setter'у нет. Строка `"Boot-args
disabled code signing enforcement..."` указывает на boot-arg источник.

### Подтверждено кодом

1. Флаг читается, не устанавливается через IPC в видимых callsites. ✅
2. При flag=1 — skip валидации (WatchKit stub, internal app identifier). ✅
3. Источник — daemon configuration, вероятно boot-args. ✅ (строка)

### Чего не хватает для уязвимости

- Метод установки флага через IPC — **не найден**. Если флаг только
  boot-arg — для эксплуатации нужен kernel-level доступ для установки
  boot-arg, что уже требует компрометации.
- Даже при flag=1 — это documented behavior для internal/development
  builds; production boot-args обычно не содержат этот флаг.

### Финальный статус

**LIKELY NOT EXPLOITABLE** через IPC. Это конфигурационный флаг с
boot-arg источником; IPC-settability не доказана и маловероятна. Для
эксплуатации нужен уже существующий kernel/boot доступ — не является
отдельной точкой входа. Точное происхождение флага (config source)
`NOT VERIFIED` — не разобран `MIDaemonConfiguration` internals.

---

## P9-H5: Асимметрия profileData vs profileAuxSig error paths

### Проверка

`sub_100004030`: `vm_read` fail на `profileData` → `loc_100004328`
(fail path → ret). `vm_read` fail на `profileAuxSig` →
`"unable to vm_read profileAuxSig"` log → zero aux fields → `loc_1000043c0`
(continue → ret).

### Подтверждено кодом

1. Разные error paths для двух `vm_read`. ✅
2. `profileAuxSig` — опциональное поле (auxiliary = дополнительная). ✅
3. Reply содержит `aux_valid=0` при fail — индикация отсутствия данных. ✅

### Чего не хватает для уязвимости

- Доказательство, что `profileAuxSig` обязателен для trust decision.
  По архитектуре aux signature — дополнительная, не основная.
- Клиент, обязующий aux signature, увидит `aux_valid=0` — корректная
  индикация.

### Финальный статус

**LIKELY BY DESIGN.** Асимметрия обоснована: profile body — обязательная
часть (fail), aux signature — опциональная (continue с индикацией).
Reply содержит корректный `aux_valid` flag. Не дефект.

---

## Итоговая матрица верификации

| ID | Гипотеза | Подтверждено кодом | Чего не хватает | Финальный статус |
|---|---|---|---|---|
| P9-H1 | isValid=1 + empty profile | асимметрия полей | клиент, игнорирующий profile_valid; vm_read fail условие | ARCHITECTURAL OBSERVATION |
| P9-H2 | нет связи XML↔подпись | DER без CD-link | upstream связь; клиент артефакт | INSUFFICIENT EVIDENCE |
| P9-H3 | MIG reachability | endpoint зарегистрирован | decoded sandbox rule; security token semantics | INSUFFICIENT EVIDENCE |
| P9-H4 | codeSigningEnforcementIsDisabled bypass | skip path exists | IPC-settability; флаг boot-arg | LIKELY NOT EXPLOITABLE |
| P9-H5 | profile/aux asymmetry | разные error paths | обязательность aux sig | LIKELY BY DESIGN |

**Итог:** 0 CONFIRMED, 1 ARCHITECTURAL OBSERVATION, 2 INSUFFICIENT
EVIDENCE, 1 LIKELY NOT EXPLOITABLE, 1 LIKELY BY DESIGN. Ни одна гипотеза
не доведена до уязвимости — все упираются в MISSING артефакты (клиент
MIG, CoreTrust internals, sandbox rule) или в маловероятность
эксплуатационного пути (boot-arg flag, aux-by-design).
