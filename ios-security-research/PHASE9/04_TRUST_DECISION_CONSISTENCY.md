# PHASE9 — 04_TRUST_DECISION_CONSISTENCY

## Метод

Проверка того, согласованы ли решения о доверии между компонентами и внутри
компонента: применяется ли одинаковый критерий «доверен/не доверен» на
разных этапах, нет ли расхождения между тем, что проверяет validator, и тем,
что реально используется при принятии решения.

Только факты из доступного кода. Решения, делегированные MISSING-компонентам,
помечены `[DELEGATED]`.

---

## 1. Что означает «isValid» в `verify_code_directory`

`sub_100004030` (`amfid_B3_disasm.txt:2547-2798`) собирает **несколько
разных полей** результата `AMFIPathValidator`:

| Поле ответа | Источник | Значение |
|---|---|---|
| `isValid` (byte) | `[validator isValid]` | главный boolean — общая валидность подписи |
| `signerType` (w32) | `[validator signerType]` | класс подписи (Apple / adhoc / dev / и т.п.) |
| `areEntitlementsValidated` (byte) | `[validator areEntitlementsValidated]` | флаг, что entitlements проверены |
| `computedCdHash` (bytes + len) | `[validator computedCdHash:&len]` | хэш CodeDirectory |
| `profileData` | `[validator profileData]` → `vm_read` | provisioning profile blob |
| `profileAuxSig` | `[validator profileAuxSig]` → `vm_read` | auxiliary signature |

Это **не одно решение**, а набор из шести результатов. Семантика «доверен»
зависит от того, какой набор полей проверяет клиент.

**Возможное несоответствие**: клиент, смотрящий только на `isValid`, может
получить `isValid=1` при `areEntitlementsValidated=0` — например, подпись
криптографически верна, но entitlements не прошли проверку. Клиент,
смотрящий только на `areEntitlementsValidated`, пропустит общую невалидность.

Статус этого наблюдения: **CONSISTENCY DEPENDS ON CLIENT**. Внутри amfid
оба поля передаются честно; обязанность проверять оба лежит на клиенте.
amfid не объединяет их в одно «итоговое» решение — он возвращает все поля
и предоставляет клиенту право решить. Подтверждено по
`amfid_B3_disasm.txt:2620-2660` (порядок чтения) и caller
`sub_10000b194:10566-10604` (все поля пакуются без дополнительной логики).

Поскольку MIG-клиент в корпусе отсутствует, реальное использование —
`NOT VERIFIED`.

---

## 2. Согласованность между `isValid` и данными профиля

В `sub_100004030`:

- `profileData` читается **только** после `validateWithError:` = success.
  При validate fail функция завершается до чтения профиля — `profile_valid`
  остаётся 0.
- `vm_read` ошибка `profileData` → переход в fail-ветку. Но `isValid` уже
  мог быть прочитан (строка `isValid` @ `0x1000041fc` идёт **после**
  `validateWithError:` но **до** `profileData`/`vm_read`).

**Точная последовательность** (`amfid_B3_disasm.txt:2620-2680`):

```text
validateWithError:   → cbz → fail
computedCdHash       → сохранён в out
signerType           → в out
isValid              → в out
areEntitlementsValidated → в out
profileData          → cbz → skip
    bytes/length → vm_read → cbz → fail path (aux_valid=0, profile_valid=0)
profileAuxSig        → cbz → skip
    bytes/length → vm_read → cbz → log, aux_valid=0 (continue, NOT fail)
```

**Несоответствие**: при `vm_read` fail на `profileData` функция идёт в
**fail path** (`loc_100004328` — общий exit). Но к этому моменту `isValid`,
`signerType`, `cdHash`, `areEntitlementsValidated` уже записаны в out-поля
и остаются ненулевыми. Вопрос — обнуляет ли fail-path эти уже записанные
поля, или они попадают в reply «как есть».

По `amfid_B3_disasm.txt:2700-2760` fail path (`loc_100004328`) идёт к
общему epilogу: release objects, `ret`. Он **не перезаписывает** уже
записанные `isValid`/`signerType`/`cdHash`. Следствие:

> При `vm_read`-ошибке `profileData` reply может содержать `isValid=1`
> (из успешного validator'а) вместе с `profile_valid=0` и `profile_len=0`.

Это **внутренняя несоответствие полей** одного ответа: главный boolean
говорит «valid», а блок профиля говорит «нет данных». Для клиента,
проверяющего только `isValid`, это выглядит как успех. Для клиента,
проверяющего `profile_valid`, — как частичный успех.

Статус: **ARCHITECTURAL INCONSISTENCY, NOT CONFIRMED DEFECT**. Это
реальная асимметрия в структуре ответа, но без клиентского артефакта нельзя
установить, приводит ли она к неправильному решению. Вынесено в гипотезы
(`08_SECURITY_HYPOTHESES.md`).

Для сравнения: `vm_read` fail на `profileAuxSig` — **не** fail path, а
нормальное завершение с `aux_valid=0`. Асимметрия между двумя `vm_read`
подтверждена (profile → fail; aux → continue).

---

## 3. Согласованность entitlement-валидации между интерфейсами

`AMFIProtocol` (NSXPC) имеет метод `verifyBoolEntitlement:` — он проверяет
**entitlement клиента** (NSXPCConnection), а не entitlement файла.
MIG `construct_der_entitlements` — сериализует **entitlement файла** в DER
для передачи дальше. MIG `verify_code_directory` читает
`areEntitlementsValidated` — флаг, что entitlement файла проверены
validator'ом.

Три разных «entitlement» сущности:

| Сущность | Где проверяется | Что означает |
|---|---|---|
| client entitlement | `-[AMFIService verifyBoolEntitlement:]` | имеет ли NSXPC-клиент право вызвать метод |
| file entitlement validity | `areEntitlementsValidated` (в `verify_code_directory`) | корректны ли entitlements подписываемого файла |
| file entitlement DER | `construct_der_entitlements` | сериализация entitlement dict для передачи |

Это **три независимых решения** на разных границах. Нет кода, который бы
смешивал их — например, нет пути, где успешный `verifyBoolEntitlement`
клиента подменял бы проверку `areEntitlementsValidated` файла.

Статус: **CONSISTENT SEPARATION** — разные проверки на разных границах,
не перепутаны. Подтверждено отсутствием cross-call в показанных фрагментах.

---

## 4. Согласованность между installd и amfid решениями

installd использует `MICodeSigningVerifier`/`MICodeSigningInfo` для
проверки устанавливаемого bundle; amfid использует `AMFIPathValidator` для
per-file validation по MIG-запросу. Это **два разных движка** валидации:

| | installd | amfid |
|---|---|---|
| Что проверяется | bundle при установке | файл по MIG-запросу (kernel hook) |
| Движок | `MICodeSigningVerifier` / `MICodeSigningInfo` (MobileInstallation) | `AMFIPathValidator_ios` (CoreTrust) |
| Тип решения | install eligibility (install/remove/launch-time) | per-execution validation |
| Policy flag | `codeSigningEnforcementIsDisabled` | нет прямого аналога в разобранном коде |

Оба используют MISSING-компоненты — нельзя проверить, одинаковы ли их
внутренние критерии (одинаковый ли набор acceptance rules у
`MICodeSigningVerifier` и `AMFIPathValidator`). Это `[DELEGATED]`.

**Известное различие policy**: installd имеет явную ветку
`codeSigningEnforcementIsDisabled` для skip валидации внутренних компонентов.
У amfid в разобранном `verify_code_directory` нет аналогичного flag-check —
`isValid` приходит напрямую из validator'а без локального policy override.
Это **не доказывает** отсутствие такого флага в amfid (может быть внутри
MISSING CoreTrust), но в разобранном amfid-коде локального skip-path нет.

Статус: **PARTIAL CONSISTENCY, DELEGATED DECISION**. Разные движки,
неизвестно — единые ли критерии. `NOT VERIFIED`.

---

## 5. Согласованность test-mode / internal-build ветвей

installd:
- `_shouldSkipEligibilityChecks...` — multi-AND (signing-id + test-mode +
  flag + err-byte). Fail по умолчанию.
- `codeSigningEnforcementIsDisabled` — single flag, skip internal
  validation. Читается из `MIDaemonConfiguration`.

amfid:
- `initiateDataMigrationWithReply:` — проверяет `[migration] using internal
  build`, SEP epoch, code-signing state, demo mode перед `MISDataMigrate`.
- Строка `"resolved security-boot-mode"`, `"unexpected security boot mode"`,
  `"failed to arm security boot mode"` — есть проверка security boot mode,
  но разобранный path не показан.

Нет доказательства, что `codeSigningEnforcementIsDisabled` (installd) и
security-boot-mode (amfid) — это одно и то же состояние. Это **разные
policy сигналы** в разных daemon'ах. Статус: **NOT VERIFIED** — нет
доказательства ни эквивалентности, ни расхождения.

---

## 6. Матрица согласованности решений

| Решение | Кто принимает | Критерий | Отказ → | Согласовано с другими? |
|---|---|---|---|---|
| `isValid` файла | `AMFIPathValidator` `[DELEGATED]` | подпись + CD | `isValid=0` | с `areEntitlementsValidated` — отдельное поле |
| `areEntitlementsValidated` | `AMFIPathValidator` `[DELEGATED]` | entitlement file | `=0` | с `isValid` — отдельное поле |
| entitlement клиента | `verifyBoolEntitlement` | `valueForEntitlement` bool | return 0 | с file entitlement — разные сущности |
| skip eligibility | `_shouldSkipEligibility` | multi-AND test | `w23=0` | с install signing — предварительная проверка |
| skip internal validation | `codeSigningEnforcementIsDisabled` | daemon config flag | validate | с amfid — разные daemon'ы, NOT VERIFIED |
| DER construction | `sub_10000366c` | plist/CE serialize | code `0xe` | с verify_code_directory — разные протоколы |

---

## Вывод

Внутри amfid и installd разобранные решения **передаются честно** (нет
кода, подменяющего результат), но:

1. `verify_code_directory` возвращает составной ответ из 6 полей —
   «решение» распределено, и его интерпретация зависит от клиента.
   Обнаружена одна внутренняя асимметрия: `vm_read` fail на `profileData`
   идёт в fail-path, но уже записанные `isValid`/`signerType` не обнуляются.
2. installd и amfid используют **разные движки** валидации с разными
   policy сигналами — согласованность их критериев `NOT VERIFIED`
   (оба `[DELEGATED]`).
3. Три разных «entitlement» проверки (client / file validity / file DER)
   корректно разделены, не смешиваются.

Ни одно наблюдение не достигает уровня CONFIRMED DEFECT — для этого нужен
клиентский артефакт, демонстрирующий неправильное решение. Все вынесены
в `08_SECURITY_HYPOTHESES.md`.
