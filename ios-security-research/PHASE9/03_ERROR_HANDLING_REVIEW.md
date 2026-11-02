# PHASE9 — 03_ERROR_HANDLING_REVIEW

## Метод

Аудит того, как результат валидации и ошибки передаются между этапами:
внутри одной функции (out-params, return codes), между MIG stub и caller,
между amfid и делегируемыми фреймворками. Для каждого перехода фиксируется:
что записывается в out-поля при успехе, что при ошибке, и может ли
ошибочный путь создать «valid»-выглядящий результат.

Принцип Phase 9: наличие необычной ветки ошибки само по себе — не
уязвимость. Уязвимость требует доказанного пути, где ошибочный/пустой
результат принимается за валидный.

---

## 1. MIG `verify_code_directory` (`sub_100004030`) — выходная структура

### Инициализация (до любой валидации)

`amfid_B3_disasm.txt:2547-2580` — все out-поля обнуляются до начала работы:

```text
0x100004068–0x10000409c: str wzr/xzr по out-полям
                         (isValid=0, signerType=0, areEntitlementsValidated=0,
                          cdHash_len=0, profile_valid=0, aux_valid=0)
```

Это подтверждённое **fail-closed по умолчанию**: до вызова validator'а
ответ уже «invalid». Любой early-exit до записи valid-полей оставляет нули.

### Точки отказа и поведение

| Точка | Условие | Что записано в out | Поведение |
|---|---|---|---|
| bad security token | `or(all token words) != 0` | все нули (init) | `syslog("bad security token")` → ret. `isValid` остаётся 0. |
| `initWithURL` fail | validator == NULL | все нули | release, ret. |
| `validateWithError:` возврат 0 | `cbz` | все нули | branch to failure, ret. |
| `validateWithError:` возврат ≠0 | success | далее — чтение метаданных | переход к metadata. |
| `profileData` == NULL | `cbz` | profile_valid=0, profile_len=0 | продолжает к aux_sig (не error). |
| `profileData` != NULL, `vm_read` fail | kern_return ≠ 0 | profile_valid=0, profile_len=0, out-ptr=0 | `→` fail path (не продолжает). |
| `profileData` != NULL, `vm_read` ok | = 0 | profile_valid=1, profile_len=len, out-ptr=buf | продолжает. |
| `profileAuxSig` == NULL | `cbz` | aux_valid=0, aux_len=0 | нормальный выход (не error). |
| `profileAuxSig` != NULL, `vm_read` fail | ≠ 0 | aux_valid=0, aux_len=0, aux_ptr=0 | `log("unable to vm_read profileAuxSig: %d")`, продолжает к выходу. |
| `profileAuxSig` != NULL, `vm_read` ok | = 0 | aux_valid=1, aux_len=len | нормальный выход. |

### Наблюдения о consistency

- **Асимметрия ошибок vm_read**: ошибка чтения `profileData` → fail-ветка;
  ошибка чтения `profileAuxSig` → log + продолжение с `aux_valid=0`.
  Обоснование: profile body — обязательная часть ответа; aux signature —
  опциональная. Это разумное различие, но зафиксировано как несимметричное
  поведение: при `vm_read`-ошибке aux signature ответ **успешен**, но
  без aux данных.
- **Нет пути, где `validateWithError:` вернул ошибку, а `isValid` был бы
  записан**: чтение `isValid` происходит только после успешного
  `validateWithError:`. Подтверждено по `amfid_B3_disasm.txt:2620-2640`.
- **Нет пути, где vm_read-ошибка записала бы `valid=1`**: оба `vm_read`
  при ошибке пишут `wzr` в valid/len поля. Подтверждено по
  `amfid_B3_disasm.txt:2700-2710` и `:2790-2800`.

### Статус распространения ошибки в reply (caller `sub_10000b194`)

`amfid_B3_disasm.txt:10566-10604`:

```text
bl 0x100004030                       → заполнены out-поля в stack
ldp w8, w20, [sp,#0x64]              → читаются isValid/signerType
strb w8, [x19,#0x24]                 → в reply
str  w20,[x19,#0x28]
ldp w8, w21, [sp,#0x5c]              → читаются areEntitlementsValidated/len
strb/str → reply
ldr x22 = NDR_record → reply+0x3c
strlen + copy profileData → reply
copy profileAuxSig → reply
orr w8, w8, #0x80000000 → msgh_bits complex
mov w8,#2 → reply+0x18 (msg_id)
```

**Факт:** caller **не проверяет** отдельный «status» от `sub_100004030` —
функция не возвращает error code; она возвращает заполненную структуру.
При любой ошибке внутри `sub_100004030` поля просто остаются нулями, и
caller упаковывает эти нули в reply как `isValid=0, signerType=0, ...`.

Следствие для trust decision: **reply всегда well-formed**, но его
семантика «isValid=0 + нулевой signerType + нулевой cdHash» — единственный
индикатор ошибки. Клиент, который смотрит только на `isValid`, корректно
получит «невалидно». Клиент, который игнорирует `isValid` и читает
`profileData`/`cdHash` напрямую, получит пустые данные — но это уже
ошибка клиента, не amfid.

Статус: **NO DEFECT DEMONSTRATED** внутри этой цепочки. Отдельная
архитектурная особенность — смешение «error reply» и «valid reply с
isValid=0» оформляется как наблюдение в `08_SECURITY_HYPOTHESES.md`
(не подтверждено как уязвимость).

---

## 2. MIG `construct_der_entitlements` (`sub_10000366c`) — коды возврата

### Коды возврата (подтверждено по `amfid_B3_disasm.txt:1860-2125`)

| Код | Причина | Где установлен |
|---|---|---|
| `0` | успех — DER blob скопирован через vm_read | `loc_100003a80` (`mov w8,#1; str w8,[x19]` — valid flag; w21=0 по пути) |
| `0x5` | bad security token | `loc_1000036e4` (`mov w21,#0x5`) |
| `0xe` | entitlement anomaly / corrupt XML / CE-serialize fail / vm_read fail | `loc_100003a04` (`mov w21,#0xe`) |

### Caller (`sub_10000b3d8`) — распространение кода

`amfid_B3_disasm.txt:10678-10703`:

```text
bl 0x10000366c → w21 = code
mig_deallocate(input OOL)
cbz w21 → loc_10000b4e0 (success)
else:
    str w21, [x19,#0x20]        → reply+0x20 = error code
    → reply+0x18 = NDR_record
    → ret  (error reply)
success path:
    reply+0x24 = transmuted byte
    reply+0x28 = transmuted_len
    reply+0x2c = NDR_record
    reply+0    = msgh complex
    reply+4    = 0x38
    reply+0x18 = msg_id 0x1
```

**Факт:** caller `sub_10000b3d8` корректно различает success (`w21==0`)
и error (`w21!=0`) и создаёт **разные формы reply**. При ошибке reply
содержит только error code, без «valid»-структуры. При успехе — структуру
с `transmuted` blob. Это **fail-closed по протоколу**.

### Внутренние проверки `sub_10000366c`

- `xml_len < 8` → `w24=1` → error path (защита от усечённого заголовка).
- `0xAA`-fill выходного буфера до записи — canary/poison.
- `CFPropertyListCreateWithData` NULL → `w24=1` → «possibly corrupt XML».
- `CFGetTypeID != CFDictionaryGetTypeID` → `w24=1` → «entitlement anomaly».
- `CESerializeCFDictionary != kCENoError` → CFRelease, `w24=1`.
- `vm_read` fail → `str wzr` в out-поля → `w21=0xe`.

Все error-пути ведут к `w21 ≠ 0`, ни один не присваивает `w21=0` после
ошибки. Подтверждён **единый error-exit** `loc_100003a08` (`mov x0,x21; retab`).

### Наблюдение о диагностике

Error-пути различают причины по syslog-строкам:
- `"bad security token"` — input auth fail.
- `"AMFIUnserializeXML failed"` — первый XML parse.
- `"Cannot construct DER entitlements due to an entitlement anomaly"` — type mismatch.
- `"Cannot construct DER entitlements, possibly corrupt XML"` — plist parse fail.
- `"Successfully transmuted entitlements."` — success.

Но в reply эти причины схлопываются в два кода (`0x5` и `0xe`). Это —
information loss на границе reply, не дефект: клиент знает «ошибка DER»,
но не знает, на каком этапе. Зафиксировано как архитектурное наблюдение.

Статус: **NO DEFECT DEMONSTRATED**.

---

## 3. NSXPC `verifyBoolEntitlement` (`-[AMFIService verifyBoolEntitlement:]`)

`amfid_B3_disasm.txt:3275-3305`:

```text
connection → valueForEntitlement:x19
cbz result → loc_100004b34 (os_log error path, w21=0)
else:
    NSNumber opt_class → isKindOfClass → tbz → loc_100004b84 (false)
    boolValue → w21
```

Факт: **nil entitlement → w21=0 (false)**, а не ошибка. Тип не NSNumber →
false. Это строгая проверка «есть bool-entitlement и он true». Нет пути,
где отсутствующий entitlement возвращал бы «разрешено».

Статус: **NO DEFECT DEMONSTRATED**.

---

## 4. installd `_shouldSkipEligibilityChecks...` — skip-логика

`installd_B3_disasm.txt:99467-99595`:

```text
MICodeSigningInfo signingIdentifierForAuditToken:error: → x20, x21(err)
cbz x20 → loc_10005a5b0:
    audit_token_to_pid → log "Failed to get signing identifier ... pid %d"
    w23 = 0  → NO SKIP (default)
else:
    isEqualToString:@"com.apple.mi-test-runner" → cbz → loc_10005a580 (no skip)
    MITestManager isRunningInTestMode:outError: → cbz → no skip
    ldrb w8 [out_err byte] → tbz → no skip
    testFlagsAreSet:0x200 → cbz → no skip
    w23 = 1  → SKIP, log "Test mode: forcing skip ..."
```

Каждый отказ на любом этапе → `w23=0` (не skip). Skip требует одновременно:
signing-id match, test-mode, err-byte flag, test-flag `0x200`. Подтверждён
**многофакторный AND** без single-point bypass.

Статус: **NO DEFECT DEMONSTRATED**.

---

## 5. installd `_isValidWatchKitApp` — policy-disabled path

`installd_B3_disasm.txt:91795-91855`:

```text
MIDaemonConfiguration codeSigningEnforcementIsDisabled → w28
cbz w28 → loc_100053650 (enforcement ON → validate)
else:
    log "Boot-args disabled code signing enforcement so not validating ..."
    → loc_100053684 (skip validate, continue)

loc_100053650 (enforcement ON):
    MICodeSigningVerifier validateWatchKitV2StubExecutableBundle:error: → w27
    tbz w27 → loc_1000536e0 (fail → error "invalid application executable")
    else → loc_100053684 (continue)
```

**Разделение**: при enforcement ON результат `MICodeSigningVerifier`
напрямую определяет дальнейший путь (fail → error). При enforcement OFF
проверка пропускается целиком. Это подтверждённая **policy-controlled
ветвь**: решение принимается флагом конфигурации, а не клиентским вводом.

Статус: **policy bypass — documented behavior, NOT A DEFECT**. Нет
доказательства, что клиент может установить `codeSigningEnforcementIsDisabled`;
это чтение daemon config, не IPC-settable.

---

## 6. Общая матрица «ошибка → решение»

| Компонент | Ошибка | Что попадает в ответ | Может ли выглядеть «valid»? |
|---|---|---|---|
| `sub_100004030` bad token | token ≠ 0 | `isValid=0`, всё нули | НЕТ — нулевая структура |
| `sub_100004030` validate fail | `validateWithError:`=0 | `isValid=0`, всё нули | НЕТ |
| `sub_100004030` vm_read profile fail | kr≠0 | `isValid` из успеха validator'а, `profile_valid=0` | isValid может быть 1, но профиль пуст — по design |
| `sub_100004030` vm_read aux fail | kr≠0 | `aux_valid=0` | успех без aux — по design |
| `sub_10000366c` bad token | — | reply code `0x5` | НЕТ |
| `sub_10000366c` any DER fail | — | reply code `0xe` | НЕТ |
| `verifyBoolEntitlement` nil/wrong type | — | return 0 (false) | НЕТ — nil ≠ true |
| `_shouldSkipEligibility` any check fail | — | `w23=0` | НЕТ — multi-AND |
| `codeSigningEnforcementIsDisabled`=1 | policy | skip validate | документированный policy path |

**Общий вывод:** во всех разобранных точках обработки ошибки результат
либо отражает ошибку (error code, `isValid=0`, `w23=0`), либо явно
помечает отсутствие данных (`profile_valid=0`, `aux_valid=0`, `w24=1`→`0xe`).
Не найдено пути, где внутренняя ошибка приводила бы к «valid»-выглядящему
ответу без сопутствующего индикатора.

Статус секции: **NO CONFIRMED DEFECT**; несколько архитектурных наблюдений
вынесены в `08_SECURITY_HYPOTHESES.md` для отдельной оценки.
