# PHASE9 — 10_FINDINGS_MATRIX

## Метод

Сводная матрица всех результатов Phase 9: подтверждённые факты,
архитектурные наблюдения, неподтверждённые гипотезы, отсутствующие
компоненты. Каждая строка — проверяемый пункт с указанием первичного
источника.

---

## Подтверждённые факты (CONFIRMED)

| # | Факт | Источник | Версии |
|---|---|---|---|
| C1 | amfid обслуживает два IPC: NSXPC `com.apple.amfi.nsxpc` и MIG `com.apple.MobileFileIntegrity` | `sub_1000049c8` (check_in), `sub_100004a24` (demux), Phase 7 (NSXPC) | B2, B3 |
| C2 | MIG `verify_code_directory` (`sub_100004030`) — per-file validation, возвращает 6-полевой trust record | `amfid_B3_disasm.txt:2547-2798`, caller `sub_10000b194` | B2, B3 |
| C3 | MIG `construct_der_entitlements` (`sub_10000366c`) — entitlement XML→DER, возвращает error code + blob | `amfid_B3_disasm.txt:1860-2125`, caller `sub_10000b3d8` | B2, B3 |
| C4 | Все error paths в `sub_10000366c` ведут к `w21≠0`, ни один не присваивает `w21=0` после ошибки | `amfid_B3_disasm.txt:2116-2125` (единый exit `loc_100003a08`) | B2, B3 |
| C5 | `verifyBoolEntitlement:` — nil/wrong-type → `false`, не ошибка и не `true` | `amfid_B3_disasm.txt:3290-3305` | B2, B3 |
| C6 | `_shouldSkipEligibilityChecks...` — multi-AND (signing-id + test-mode + flag + err-byte), fail default `w23=0` | `installd_B3_disasm.txt:99467-99595` | B2, B3 |
| C7 | `codeSigningEnforcementIsDisabled` — 5 callsites в каждой версии, все чтение, не запись | B2: 89497,90274,93764,93878,95756; B3: 91801,92578,96157,96271,98149 | B2, B3 |
| C8 | При enforcement ON `MICodeSigningVerifier.validateWatchKitV2StubExecutableBundle` определяет result; при OFF — skip | `installd_B3_disasm.txt:91795-91855` | B2, B3 |
| C9 | Out-поля `sub_100004030` обнуляются до валидации (fail-closed init) | `amfid_B3_disasm.txt:2568-2580` | B2, B3 |
| C10 | `vm_read` fail на `profileData` → fail path; на `profileAuxSig` → continue с `aux_valid=0` | `amfid_B3_disasm.txt:2700-2760, 2790-2800` | B2, B3 |
| C11 | amfid B2≡B3 функционально (disasm SHA-256 идентичен); отличается только UUID | hashes в `01_TRUST_COMPONENT_INVENTORY.md` | B2, B3 |
| C12 | installd B3 > B2 на ~16KB; `codeSigningEnforcementIsDisabled` callers 5→5 | `07_VERSION_DIFFS.md` | B2→B3 |
| C13 | `validateWithError:`=fail → `isValid` никогда не записывается (читается после success) | `amfid_B3_disasm.txt:2620-2640` | B2, B3 |
| C14 | `entitlements` plist B2≡B3 (SHA-256 идентичен) | `e080c72...937a0d` | B2, B3 |
| C15 | MIG input validation: msgh size, alignment, NUL-memchr, OOL-дескриптор, `0x3e8`+ range | `sub_10000b15c`, `sub_10000b194`, `sub_10000b3d8` | B2, B3 |

## Архитектурные наблюдения (ARCHITECTURAL OBSERVATION)

| # | Наблюдение | Источник |
|---|---|---|
| O1 | `verify_code_directory` возвращает составной ответ — `isValid` не сбрасывается при fail на profileData copy | `04_TRUST_DECISION_CONSISTENCY.md` §2 |
| O2 | Два разных reply-протокола: `isValid` boolean (MIG verify) vs error code (MIG DER) | `02_TRUST_ARCHITECTURE.md` §3 |
| O3 | Validation (MIG) и management (NSXPC) разделены — MIG не изменяет state, NSXPC не выполняет per-file validation | `02_TRUST_ARCHITECTURE.md` §5 |
| O4 | Три разных «entitlement» сущности (client / file validity / file DER) корректно разделены | `04_TRUST_DECISION_CONSISTENCY.md` §3 |
| O5 | installd имеет policy flag `codeSigningEnforcementIsDisabled`; у amfid в разобранном коде аналога нет | `04_TRUST_DECISION_CONSISTENCY.md` §4 |
| O6 | Ошибки DER схлопываются в reply в код `0xe` без указания этапа — information loss на границе | `03_ERROR_HANDLING_REVIEW.md` §2 |
| O7 | amfid — посредник, не конечный верификатор; результат CoreTrust передаётся без перепроверки | `06_TRUST_BOUNDARY_MATRIX.md` |
| O8 | installd и amfid используют разные движки валидации (MobileInstallation vs CoreTrust) | `06_TRUST_BOUNDARY_MATRIX.md` |

## Неподтверждённые гипотезы (INSUFFICIENT EVIDENCE и ниже)

| # | Гипотеза | Статус | Причина |
|---|---|---|---|
| P9-H1 | isValid=1 + empty profile при vm_read fail | ARCHITECTURAL OBSERVATION | нет клиентского артефакта; условие маловероятно |
| P9-H2 | нет связи entitlement-XML ↔ подпись | INSUFFICIENT EVIDENCE | связь может быть upstream; клиент недоступен |
| P9-H3 | MIG endpoint reachable непривилегированным | INSUFFICIENT EVIDENCE | sandbox rule не декодировано; token semantics не разобраны |
| P9-H4 | `codeSigningEnforcementIsDisabled` — обход | LIKELY NOT EXPLOITABLE | boot-arg источник; IPC-settability не найдена |
| P9-H5 | асимметрия profile/aux error | LIKELY BY DESIGN | aux опционален; корректный valid-flag |

## Отсутствующие компоненты (MISSING — не проверяемо)

| Компонент | Что не проверяемо |
|---|---|
| trustd | вся роль в trust chain |
| CoreTrust.framework | `AMFIPathValidator` internals: Mach-O, SuperBlob, CodeDirectory, CMS parse/verify |
| Security.framework | CMS, certificate chain |
| libmis.dylib | provisioning profile validation, MIS database, trustTeamID |
| libsecurity_codesigning | code-signing policy engine |
| MobileInstallation.framework | `MICodeSigningVerifier`, `MICodeSigningInfo` internals |
| XNU/AMFI kernel | enforcement, trust cache write, MIG client identity |
| RC binaries | вся RC-side валидация |

## Непроверяемые границы (NOT VERIFIED)

| Граница | Что не проверено |
|---|---|
| MIG client identity | кто посылает msg `0x441` |
| sandbox/mach-lookup rule | эффективное правило для `com.apple.MobileFileIntegrity` |
| entitlement↔CD link | соответствие DER подписанным entitlements |
| security token semantics | что именно проверяет `≠0` check |
| kernel write-back | как trust result попадает в kernel cache |
| installd/amfid criteria parity | одинаковы ли критерии двух движков |

## Итоговый счёт

- **Подтверждённых фактов:** 15
- **Архитектурных наблюдений:** 8
- **Гипотез:** 5 (0 CONFIRMED, 1 ARCH OBS, 2 INSUFFICIENT, 1 LIKELY NOT EXPLOITABLE, 1 LIKELY BY DESIGN)
- **Missing компонентов:** 8
- **Непроверяемых границ:** 6
- **Подтверждённых уязвимостей:** 0
