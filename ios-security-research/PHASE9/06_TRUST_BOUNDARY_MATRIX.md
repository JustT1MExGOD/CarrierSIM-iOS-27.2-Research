# PHASE9 — 06_TRUST_BOUNDARY_MATRIX

## Метод

Матрица trust boundary: кто кому доверяет, что передаётся через границу,
какая проверка выполняется на входе. Каждая граница описана по доступному
коду; для границ с MISSING-компонентами — статус `NOT VERIFIED` по
фактической реализации.

---

## Матрица границ

### Граница 1: MIG client → amfid `verify_code_directory`

| Аспект | Значение |
|---|---|
| Клиент | kernel AMFI hook / другой daemon (NOT VERIFIED — клиентский артефакт отсутствует) |
| Транспорт | Mach message → `com.apple.MobileFileIntegrity` |
| Что передаётся | security token + URL + file offset + flags |
| Проверка входа | msgh size, alignment, NUL, OOL-дескриптор, security token ≠ 0 |
| Что возвращается | `isValid`, `signerType`, `areEntitlementsValidated`, `cdHash`, `profileData`, `profileAuxSig` |
| Доверие amfid→клиент | amfid доверяет клиенту передать корректный token; не проверяет entitlement (MIG — нет NSXPC entitlement API) |
| Доверие клиент→amfid | клиент доверяет amfid вернуть честный `isValid` |
| Статус | input validation CONFIRMED; client identity NOT VERIFIED |

### Граница 2: MIG client → amfid `construct_der_entitlements`

| Аспект | Значение |
|---|---|
| Клиент | kernel AMFI hook / daemon (NOT VERIFIED) |
| Транспорт | Mach message → `com.apple.MobileFileIntegrity` |
| Что передаётся | security token + entitlement XML blob (OOL) |
| Проверка входа | token ≠ 0, `xml_len >= 8`, plist parse, type=dict |
| Что возвращается | error code (`0`/`0x5`/`0xe`) + DER blob |
| Доверие | клиент доверяет amfid корректно сериализовать |
| Статус | input validation CONFIRMED; semantic link к подписи NOT VERIFIED |

### Граница 3: NSXPC client → amfid `AMFIService`

| Аспект | Значение |
|---|---|
| Клиент | любой процесс, способный resolve `com.apple.amfi.nsxpc` (NOT VERIFIED — bootstrap policy) |
| Транспорт | NSXPC → `AMFIProtocol` (13 methods) |
| Проверка входа | `shouldAcceptNewConnection` — permissive; per-method `verifyBoolEntitlement:` |
| Что возвращается | per-method reply (trust state, profile, SEP state, signature) |
| Доверие | amfid проверяет client entitlement для mutating methods; для `getSEPState`/`getStagedProfile` — entitlement gate NOT VERIFIED (Phase 7) |
| Статус | listener permissive; per-method gating CONFIRMED для mutators, NOT VERIFIED для 2 getters |

### Граница 4: amfid → CoreTrust (`AMFIPathValidator`)

| Аспект | Значение |
|---|---|
| Направление | amfid → framework call |
| Что передаётся | URL + file offset + flags |
| Что возвращается | validator object; `isValid`, `signerType`, `cdHash`, `areEntitlementsValidated`, `profileData`, `profileAuxSig` |
| Доверие amfid→CoreTrust | amfid **полностью доверяет** результату validator'а — не перепроверяет |
| Реализация | MISSING — CoreTrust не в корпусе |
| Статус | `[DELEGATED]` — amfid не выполняет own revalidation |

### Граница 5: amfid → MIS/libmis

| Аспект | Значение |
|---|---|
| Направление | amfid → MISAgent / MISProfileDBClient / MISCopyProvisioningProfile / trustTeamID / MISDataMigrate / MISValidateSignatureAndCopyInfo |
| Что передаётся | team ID, signature, profile, migration request |
| Что возвращается | profile data, signing identities, trust result |
| Доверие | amfid доверяет MIS управлять trust database |
| Реализация | MISSING — libmis не в корпусе |
| Статус | `[DELEGATED]` |

### Граница 6: amfid → LAStorage / SEP

| Аспект | Значение |
|---|---|
| Направление | amfid → LocalAuthentication storage |
| Что передаётся | `initWithDomain:0 authenticationContext:0`, `dataForKey:` |
| Что возвращается | 49-byte SEP state structure |
| Доверие | amfid доверяет SEP/LocalAuthentication state |
| Статус | SEP state read CONFIRMED (Phase 7); write path NOT VERIFIED |

### Граница 7: NSXPC client → installd `MobileInstallerProtocol`

| Аспект | Значение |
|---|---|
| Клиент | любой с доступом к `com.apple.mobile.installd` (NOT VERIFIED — bootstrap) |
| Транспорт | NSXPC → 75 methods |
| Проверка входа | permissive listener; per-method `_ValidateMIAllowedSPIEntitlement` |
| Что возвращается | install/uninstall/query results |
| Статус | per-method gating CONFIRMED (63/75 direct, 12 indirect — Phase 6) |

### Граница 8: installd → MICodeSigningVerifier / MICodeSigningInfo

| Аспект | Значение |
|---|---|
| Направление | installd → MobileInstallation.framework call |
| Что передаётся | bundle, audit token, signing info |
| Что возвращается | validation result, signing identifier, entitlement values |
| Доверие | installd доверяет framework — но применяет собственный policy flag (`codeSigningEnforcementIsDisabled`) до вызова |
| Реализация | MISSING — MobileInstallation не в корпусе |
| Статус | `[DELEGATED]` с локальным policy override |

### Граница 9: installd → MITestManager

| Аспект | Значение |
|---|---|
| Направление | installd → test-mode state |
| Что передаётся | `isRunningInTestMode:`, `testFlagsAreSet:0x200` |
| Что возвращается | test mode bool, flag bool |
| Доверие | installd доверяет test manager state; используется для skip eligibility |
| Статус | CONFIRMED (multi-AND); enablement of test mode — gated отдельно (Phase 6) |

### Граница 10: amfid/installd → XNU/AMFI kernel enforcement

| Аспект | Значение |
|---|---|
| Направление | kernel → (через MIG) → amfid; amfid → (через MIS?) → kernel trust cache |
| Что передаётся | file для validation; trust record для cache |
| Реализация | kernelcache присутствует, AMFI policy path NOT decoded |
| Статус | `NOT VERIFIED` — механизм записи решения обратно в kernel не виден |

---

## Сводная таблица доверия

| # | Граница | Кто проверяет вход | Доверие к результату | Статус |
|---|---|---|---|---|
| 1 | MIG client→amfid verify | amfid (msgh+token) | клиент доверяет amfid | input OK; client ID NOT VERIFIED |
| 2 | MIG client→amfid DER | amfid (token+plist) | клиент доверяет amfid | input OK; semantic link NOT VERIFIED |
| 3 | NSXPC→amfid | amfid (entitlement) | клиент доверяет amfid | mutators OK; 2 getters NOT VERIFIED |
| 4 | amfid→CoreTrust | CoreTrust (внутри) | amfid доверяет | `[DELEGATED]` |
| 5 | amfid→libmis | libmis (внутри) | amfid доверяет | `[DELEGATED]` |
| 6 | amfid→LAStorage | LA/SEP | amfid доверяет | read OK |
| 7 | NSXPC→installd | installd (entitlement) | клиент доверяет | CONFIRMED |
| 8 | installd→MI framework | framework (внутри) | installd доверяет + policy flag | `[DELEGATED]` |
| 9 | installd→MITestManager | test manager | installd доверяет | CONFIRMED |
| 10 | amfid→XNU/AMFI | kernel | оба направления | `NOT VERIFIED` |

---

## Ключевые наблюдения

1. **amfid — доверенный посредник, не конечный верификатор.** Он принимает
   вход, передаёт в CoreTrust/MIS, возвращает результат. Сам он не
   перепроверяет результат делегированных компонентов — это нормально для
   архитектуры, но означает, что ошибка в CoreTrust напрямую попадёт в
   MIG reply.
2. **Два независимых движка валидации.** installd (MobileInstallation) и
   amfid (CoreTrust) — разные фреймворки. Согласованность их решений —
   `NOT VERIFIED`.
3. **Policy flags разнесены по daemon'ам.** `codeSigningEnforcementIsDisabled`
   — installd; security-boot-mode — amfid; test-mode — MITestManager.
   Нет единого policy source, видимого в коде.
4. **Граница «клиент↔amfid» на MIG — без entitlement.** MIG не имеет
   NSXPC-entitlement API; авторизация клиента MIG — только security token.
   Кто может послать MIG msg — определяется bootstrap/Mach policy, не
   amfid. Reachability `NOT VERIFIED`.
