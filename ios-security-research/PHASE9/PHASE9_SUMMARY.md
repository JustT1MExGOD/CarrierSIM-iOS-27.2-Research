# PHASE9 — SUMMARY

# iOS Security Research — Phase 9: Code Signing, Trust Validation & Error-Handling Audit

## Scope

Статический офлайн-аудит архитектуры принятия решения о доверии в iOS 27.2
Beta 2 и Beta 3: как система решает «доверен/не доверен», как результат
передаётся между компонентами, и корректна ли обработка ошибок на каждой
границе. RC-артефакты отсутствуют — RC-сравнение `NOT COMPARABLE`.

Все ограничения Phase 9 соблюдены: только статический анализ, без
взаимодействия с устройством, без активных IPC-запросов, без фаззинга,
без создания payloads/PoC, без разработки обходов, без модификации
бинарей, без публикации и без git push. Отчёты Phase 1–8 не изменены.

---

## Что было сделано

1. **Инвентаризация trust-компонентов** (`01_TRUST_COMPONENT_INVENTORY.md`):
   в корпусе — amfid B2/B3, installd B2/B3, kernelcache B2/B3, sandbox
   kext B2/B3, B2 dyld cache. **Отсутствуют**: trustd, CoreTrust.framework,
   libmis.dylib, libsecurity_codesigning, Security.framework,
   MobileInstallation.framework, RC-бинари. Отсутствие зафиксировано как
   `MISSING`, не заменено предположениями.

2. **Реконструкция архитектуры** (`02_TRUST_ARCHITECTURE.md`):
   amfid обслуживает **два разных IPC-интерфейса**:
   - NSXPC `com.apple.amfi.nsxpc` — state-management (13 методов
     `AMFIProtocol`, per-method entitlement gates).
   - Mach MIG `com.apple.MobileFileIntegrity` — per-file validation
     (`bootstrap_check_in` в `sub_1000049c8`, `dispatch_mach_mig_demux`
     в `sub_100004a24`, строка `"amfid mig server"`).

   MIG stub'ы — не NSXPC: `sub_100004030` (`verify_code_directory`,
   вызов из `sub_10000b194`, msg `0x441`+) и `sub_10000366c`
   (`construct_der_entitlements`, вызов из `sub_10000b3d8`). Собственная
   криптопроверка делегирована `AMFIPathValidator_ios` (CoreTrust —
   MISSING) и MIS/libmis (MISSING).

3. **Аудит обработки ошибок** (`03_ERROR_HANDLING_REVIEW.md`):
   - `sub_100004030`: out-поля обнуляются до валидации (fail-closed init).
     `validateWithError:`=fail → `isValid` никогда не записывается.
   - `sub_10000366c`: все error paths → `w21≠0` (`0x5` bad token,
     `0xe` DER error), единый exit; caller кладёт код в reply.
   - `verifyBoolEntitlement:` — nil/wrong-type → `false`.
   - `_shouldSkipEligibilityChecks` — multi-AND, fail default.
   **Не найдено пути, где ошибка создаёт «valid»-выглядящий ответ.**

4. **Аудит согласованности решений** (`04_TRUST_DECISION_CONSISTENCY.md`):
   `verify_code_directory` возвращает составной ответ из 6 полей
   (`isValid`, `signerType`, `areEntitlementsValidated`, `cdHash`,
   `profileData`, `profileAuxSig`). Обнаружена одна внутренняя
   асимметрия: при `vm_read`-fail на `profileData` уже записанные
   `isValid`/`signerType` не обнуляются перед exit.

5. **Аудит формат-валидации** (`05_FORMAT_VALIDATION_REVIEW.md`):
   полностью видимая валидация только у entitlement XML (plist parse +
   CFDictionary type check + `CESerializeCFDictionary` + `vm_read`) и у
   MIG-входа (size/alignment/NUL/OOL). Mach-O, SuperBlob, CodeDirectory,
   CMS, provisioning profile — `[DELEGATED]` в MISSING-компоненты.
   **Ключевой пробел:** связь entitlement-XML ↔ подпись (CD) не видна.

6. **Матрица trust boundary** (`06_TRUST_BOUNDARY_MATRIX.md`): 10 границ.
   amfid — посредник без перепроверки делегированного результата.
   installd и amfid используют разные движки валидации
   (MobileInstallation vs CoreTrust).

7. **Version diff** (`07_VERSION_DIFFS.md`): amfid B2≡B3 функционально
   (disasm идентичен). installd +16KB при parity ключевых callsites
   (`codeSigningEnforcementIsDisabled` 5→5). RC — `NOT COMPARABLE`.

8. **Гипотезы и верификация** (`08`, `09`): 5 гипотез, все проверены по
   первичным callsites.

---

## Research Outcome

| Категория | Количество |
|---|---|
| Подтверждённые факты (CONFIRMED facts) | **15** |
| Архитектурные наблюдения | **8** |
| Подтверждённые уязвимости (CONFIRMED vulnerabilities) | **0** |
| Гипотез — всего | **5** |
| — ARCHITECTURAL OBSERVATION | 1 (P9-H1: isValid=1 + empty profile) |
| — INSUFFICIENT EVIDENCE | 2 (P9-H2: XML↔CD link; P9-H3: MIG reachability) |
| — LIKELY NOT EXPLOITABLE | 1 (P9-H4: codeSigningEnforcementIsDisabled — boot-arg) |
| — LIKELY BY DESIGN | 1 (P9-H5: profile/aux asymmetry) |
| MISSING компонентов | **8** |
| NOT VERIFIED границ | **6** |

**Подтверждённых уязвимостей: 0.** Ни одна гипотеза не доведена до
уровня security finding — все упираются в отсутствующие артефакты
(MIG-клиент, CoreTrust internals, decoded sandbox rule) или в
маловероятность эксплуатационного пути.

---

## Главные архитектурные выводы

1. **Разделение ролей подтверждено:** MIG — read-only per-file
   validation; NSXPC — entitlement-gated state management. MIG stub'ы
   не вызывают MIS; NSXPC-методы не выполняют path validation.
2. **amfid — посредник, не верификатор.** Он оркеструет вызов
   `AMFIPathValidator` (CoreTrust) и MIS, честно передаёт результат, но
   не перепроверяет криптографию. Ошибка внутри MISSING CoreTrust
   попадёт в reply без фильтрации — это свойство архитектуры, не дефект
   самого amfid.
3. **Error handling — fail-closed** во всех разобранных точках:
   init-to-zero, единый error-exit, explicit error codes в reply,
   nil→false entitlement, multi-AND skip.
4. **Два движка валидации** (installd/MobileInstallation vs
   amfid/CoreTrust) с разными policy-сигналами; parity критериев
   `NOT VERIFIED`.
5. **Граница доверия смещена в MISSING-код.** Собственно решение
   «подпись валидна» принимается внутри CoreTrust/Security/libmis/XNU —
   недоступных для анализа. amfid/installd покрывают только orchestration.

## Ограничения

- Все выводы о CoreTrust, Security, libmis, MobileInstallation, XNU/AMFI —
  `NOT VERIFIED`, так как бинари не извлечены из dyld cache/kernelcache.
- Идентичность MIG-клиента не установлена — клиентский артефакт отсутствует.
- Reachability `com.apple.MobileFileIntegrity` для непривилегированного
  клиента не доказана — sandbox rule не декодировано.
- RC-сравнение невозможно — RC-бинари отсутствуют.

## Файлы Phase 9

- `01_TRUST_COMPONENT_INVENTORY.md` — инвентарь компонентов + MISSING list
- `02_TRUST_ARCHITECTURE.md` — реконструкция trust architecture
- `03_ERROR_HANDLING_REVIEW.md` — аудит error/status propagation
- `04_TRUST_DECISION_CONSISTENCY.md` — согласованность решений
- `05_FORMAT_VALIDATION_REVIEW.md` — аудит формат-валидации
- `06_TRUST_BOUNDARY_MATRIX.md` — матрица границ доверия
- `07_VERSION_DIFFS.md` — B2/B3/RC сравнение
- `08_SECURITY_HYPOTHESES.md` — 5 гипотез
- `09_HYPOTHESIS_VERIFICATION.md` — независимая верификация
- `10_FINDINGS_MATRIX.md` — итоговая матрица
- `PHASE9_SUMMARY.md` — этот файл
