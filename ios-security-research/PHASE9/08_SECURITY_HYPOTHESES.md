# PHASE9 — 08_SECURITY_HYPOTHESES

## Метод

Формулировка гипотез только при наличии конкретного кодового основания.
Каждая гипотеза — это **предположение, требующее проверки**, а не вывод.
Классификация каждой — в `09_HYPOTHESIS_VERIFICATION.md`.

Максимум 5 гипотез. Сформулировано ровно столько, сколько оправдано
кодом — не искусственно добито до лимита.

---

## P9-H1: Составной ответ `verify_code_directory` допускает частичный успех

**Основание:** `sub_100004030` (`amfid_B3_disasm.txt:2547-2798`).
При `vm_read`-ошибке `profileData` функция идёт в fail-path, но уже
записанные `isValid`, `signerType`, `computedCdHash`,
`areEntitlementsValidated` **не обнуляются** перед выходом. Caller
`sub_10000b194` упаковывает все поля как есть.

**Формулировка:** MIG reply может содержать `isValid=1` (успешная
валидация) вместе с `profile_valid=0` / `profile_len=0` (профиль не
скопирован). Клиент, игнорирующий `profile_valid`, увидит «valid +
пустой профиль».

**Что нужно для подтверждения:**
- Показать, что `vm_read` реально может вернуть ошибку на валидном
  profileData (условие маловероятно, но возможно — например, profileData
  в недоступной странице).
- Показать, что реальный клиент MIG интерпретирует `isValid=1` без
  проверки `profile_valid`.
- Клиентский артефакт отсутствует.

**Предварительный статус:** ARCHITECTURAL OBSERVATION — подтверждённая
асимметрия полей, но не подтверждено как уязвимость. Без клиента — не
поднимается выше наблюдения.

---

## P9-H2: Отсутствие видимой связи entitlement-XML ↔ подпись в `construct_der_entitlements`

**Основание:** `sub_10000366c` (`amfid_B3_disasm.txt:1860-2125`) принимает
XML blob и сериализует его в DER без видимой проверки, что этот XML —
тот, что подписан в CodeDirectory того же файла. Связь с подписью — в
вызывающей цепочке MIG-клиента или в CoreTrust, недоступной.

**Формулировка:** если MIG-клиент может подать произвольный entitlement
XML отдельно от файла, DER-результат может не соответствовать подписанным
entitlement'ам. Но: (а) функция проверяет security token — клиент
идентифицирован как доверенный; (б) связь может проверяться downstream
в MISSING коде.

**Что нужно для подтверждения:**
- Установить, кто является клиентом `construct_der_entitlements` и может
  ли он подать несоответствующий XML.
- Установить, проверяется ли соответствие DER↔CD downstream.
- Оба пункта требуют MISSING клиентского/фреймворк артефакта.

**Предварительный статус:** INSUFFICIENT EVIDENCE — поверхность есть,
но доверенный клиент + недоступная downstream-проверка не позволяют
подтвердить уязвимость.

---

## P9-H3: MIG endpoint `com.apple.MobileFileIntegrity` может быть доступен
непривилегированному клиенту

**Основание:** `bootstrap_check_in("com.apple.MobileFileIntegrity")`
(`sub_1000049c8`) регистрирует сервис у launchd. MIG не использует NSXPC
entitlement API — авторизация только через security token в сообщении.
Sandbox kext содержит `AppleMobileFileIntegrity` и `mach-lookup` строки,
но эффективное правило не декодировано (Phase 8).

**Формулировка:** если sandbox/mach-lookup policy разрешает обычному
приложению resolve `com.apple.MobileFileIntegrity`, то клиент может
вызвать `verify_code_directory` на произвольный файл и получить trust
record — информационная утечка (signerType, cdHash, profile data).
Запись в trust database — нет (MIG не изменяет состояние).

**Что нужно для подтверждения:**
- Декодировать sandbox/mach-lookup правило для `com.apple.MobileFileIntegrity`.
- Или найти клиентский артефакт, демонстрирующий непривилегированный вызов.
- Sandbox kext не декодирован; правило `NOT VERIFIED`.

**Предварительный статус:** INSUFFICIENT EVIDENCE — endpoint зарегистрирован,
но reachability не доказана. Даже если достижим — результат read-only
(trust record), не state-changing.

---

## P9-H4: `codeSigningEnforcementIsDisabled` — точка обхода валидации

**Основание:** 5 callsites в installd (B2: 89497, 90274, 93764, 93878,
95756; B3: 91801, 92578, 96157, 96271, 98149). В `_isValidWatchKitApp`
при flag=1 проверка `validateWatchKitV2StubExecutableBundle` пропускается
целиком. В `_validateApplicationIdentifier` при flag=1 internal app
получает missing-identifier bypass.

**Формулировка:** если `codeSigningEnforcementIsDisabled` может быть
установлен клиентом или через незащищённый путь — это обход валидации.

**Что нужно для подтверждения:**
- Показать, что флаг IPC-settable. Видимый код — это **чтение**
  (`codeSigningEnforcementIsDisabled`), не запись. Setter не найден
  в показанных callsites.
- Источник — `MIDaemonConfiguration` (daemon config, вероятно boot-args
  или config file). Строка `"Boot-args disabled code signing enforcement"`
  подтверждает: это boot-arg, не runtime API.
- Доказательства IPC-settability: **НЕТ**.

**Предварительный статус:** LIKELY NOT EXPLOITABLE через IPC — это
boot-arg/config flag, не client-controllable. Но точное происхождение
флага `NOT VERIFIED` (config source не разобран).

---

## P9-H5: Асимметрия обработки `profileData` vs `profileAuxSig` ошибок

**Основание:** `sub_100004030` — `vm_read` fail на `profileData` → fail
path; `vm_read` fail на `profileAuxSig` → log + продолжение с `aux_valid=0`.
Разное отношение к одинаковому типу ошибки.

**Формулировка:** это скорее design choice (profile обязателен, aux —
опционален), чем дефект. Но если `profileAuxSig` — обязательная часть
некоторых ответов, продолжение с `aux_valid=0` создаёт неполный ответ
без индикации ошибки на уровне reply header.

**Что нужно для подтверждения:**
- Установить, обязателен ли `profileAuxSig` для корректной trust decision.
- Требуется документация протокола или клиентский артефакт — недоступны.

**Предварительный статус:** LIKELY BY DESIGN — aux signature опциональна
по архитектуре (auxiliary = дополнительная). Обоснованное различие, не
дефект. Оставлено как наблюдение, не как уязвимость.

---

## Сводка гипотез

| ID | Гипотеза | Основание | Предварительный статус |
|---|---|---|---|
| P9-H1 | составной ответ допускает isValid=1 + empty profile | не-обнуление полей при vm_read fail | ARCHITECTURAL OBSERVATION |
| P9-H2 | нет видимой связи XML↔подпись | DER без видимой CD-link | INSUFFICIENT EVIDENCE |
| P9-H3 | MIG endpoint может быть reachable | bootstrap_check_in, no entitlement | INSUFFICIENT EVIDENCE |
| P9-H4 | codeSigningEnforcementIsDisabled — bypass | 5 callsites, skip path | LIKELY NOT EXPLOITABLE (boot-arg) |
| P9-H5 | асимметрия profile/aux error | разные error paths | LIKELY BY DESIGN |

Итого: **5 гипотез**, ни одна не доведена до CONFIRMED VULNERABILITY —
все упираются в MISSING клиентский/фреймворк артефакт или в недоступную
policy-decoded информацию.
