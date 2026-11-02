# PHASE9 — 01_TRUST_COMPONENT_INVENTORY

## Метод

Статический офлайн-инвентарь локального корпуса материалов. Для каждого компонента,
перечисленного в задании Phase 9, зафиксировано: присутствует ли он как локальный
артефакт, и что именно из него доступно для анализа. Для отсутствующих компонентов
записано `MISSING` — отсутствие артефакта не интерпретируется как доказательство ни
наличия, ни отсутствия валидации.

Источник перечня компонентов — задание Phase 9:
`amfid`, `trustd`, `installd`, `MobileInstallation.framework`, `Security.framework`,
`CoreTrust.framework`, `libmis`, `libsecurity_codesigning`, `XNU/AMFI`.

---

## Компоненты, присутствующие в корпусе

### amfid — PRESENT (B2 + B3)

| Артефакт | SHA-256 | UUID | Размер |
|---|---|---|---|
| `amfid_B2.bin` | `39d4d583262c82cdbf4dee2ed694ffc20e99d4589e51a34b127924daa001ccd9` | `3E6D3282-527E-3BC1-8A9F-1C2BABF3A894` | 253968 |
| `amfid_B3.bin` | `d331a10135df45100a431aa77e1d65b3d5b012f494f747346dcab4a551b0db8f` | `CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B` | 253968 |
| `amfid_B3_disasm.txt` | `dbf55bcf7a53b0bef60b0abf277c829285b9367f8f679b45c0eee966aadeb3aa` (B2 disasm идентичен) | — | — |

Покрытие анализа:
- NSXPC endpoint `com.apple.amfi.nsxpc` + `AMFIProtocol` (13 методов) — Phase 7.
- Mach MIG endpoint `com.apple.MobileFileIntegrity` + `dispatch_mach_mig_demux` —
  Phase 9, `sub_100004a24`, `bootstrap_check_in` @ `sub_1000049c8`.
- MIG-серверные stub'ы `sub_100004030` (verify_code_directory) и `sub_10000366c`
  (construct_der_entitlements) — Phase 9.
- `AMFIPathValidator_ios` callsites — Phase 9.
- MISAgent/provisioning-profile вызовы (`MISCopyProvisioningProfile`,
  `trustTeamID:signature:error:`, `signingIdentitiesWithTeamID:`) — Phase 9.
- Entitlement plist — `e080c72eaf386c6467a1da58b7c6ae36f3d8ee059342d930dfb42cb1a3937a0d`
  (B2 == B3).

### installd — PRESENT (B2 + B3)

| Артефакт | SHA-256 | UUID | Размер |
|---|---|---|---|
| `installd_B2.bin` | `f0f1ce4b9c7db3dc560792329a397d09437770d44b4cb9590a8ed0160608576f` | `5D0437D3-8824-39D1-8BEB-E8F48DA6F93B` | 945168 |
| `installd_B3.bin` | `1dd5efbfdd635e7617217eefba07f58fc24d1eb7cb60677a1a878999a0664b1d` | `F54A48D1-4E77-3425-BEAB-5EBBBB037C0F` | 961888 |
| `installd_B2_disasm.txt` / `installd_B3_disasm.txt` | — | — | — |

Покрытие анализа:
- `MobileInstallerProtocol` (75 методов) + `_ValidateMIAllowedSPIEntitlement` — Phase 6.
- `MIInstallableBundle` signing-validation helpers (`_isValidWatchKitApp:...`,
  `_validateApplicationIdentifierForNewBundleSigningInfo:error:`,
  `_validateAppManagementDomainForSigningInfo:error:`,
  `_validateLinkedParentForSigningInfo:...`,
  `_checkEligibilityForAppWithSigningInfo:...`,
  `_shouldSkipEligibilityChecksForInstallRequestorWithAuditToken:persona:authorizingBundleID:`) — Phase 9.
- `MICodeSigningInfo` callsites — Phase 9.
- `MICodeSigningVerifier` callsite — Phase 9 (только вызов, реализация отсутствует).
- `MIDaemonConfiguration.codeSigningEnforcementIsDisabled` — Phase 9 (5 callers в B2, 5 в B3).
- `updateMCMWithCodeSigningInfoAsAdvanceCopy:withError:` — Phase 9 (callsite).
- `MITestManager` / test-mode helpers — Phase 9.
- Entitlement plist — `e080c72eaf386c6467a1da58b7c6ae36f3d8ee059342d930dfb42cb1a3937a0d`
  (B2 == B3).

### XNU / AMFI kernel side — PARTIAL

| Артефакт | SHA-256 |
|---|---|
| `beta2/24B5089g__iPhone16,1/kernelcache.release.iPhone16,1` | `35e3266f96981d2fed31f917914fe212c36219431ca190c416cfbeb84f1bfb85` |
| `beta3/24B5099f__iPhone16,1/kernelcache.release.iPhone16,1` | `c31c08194763cb3a6adf51dc945676ac555ed028ac625adda57e8dc45d665a09` |
| `beta2/sandbox/com.apple.security.sandbox` | `c884a1afe97b8d5f8c21c86eb4e57466edeec9a04b261e45bc9385e5652b7438` |
| `beta3/sandbox/com.apple.security.sandbox` | `e41c7ea73ea53164f9f4ec839431dfb8538b0fe831aeb29210ff7f79b46c0329` |

Статус:
- Kernelcache присутствует, но **AMFI code-signing policy path внутри kernelcache
  НЕ декодирован**. Выполнена только проверка наличия AMFI-related строк в
  sandbox kext (Phase 8): `amfid`, `com.apple.amfi.xpc`, `com.apple.amfi.nsxpc`,
  `AppleMobileFileIntegrity`, `/private/var/db/amfid`, `mach-lookup`,
  `mach-bootstrap`, `common-mach-lookups`, `bootstrap` — строки присутствуют.
- Sandbox kext подтверждает наличие policy machinery и AMFI constants;
  эффективное allow/deny правило для конкретного клиента НЕ декодировано.
- XNU source не присутствует; AppleMobileFileIntegrity.kext не выделен как
  отдельный артефакт.

### dyld shared cache — PARTIAL (только B2)

| Артефакт | SHA-256 |
|---|---|
| `beta2-dyld/.../dyld_shared_cache_arm64e` (+ split set) | `11a4b07ef56f3674a21937980cc1a377e8085e93e72334dc428b02ca26b2ebb8` |

Статус: присутствует как контейнер, но целевые фреймворки (MobileInstallation,
Security, CoreTrust, libmis, libsecurity_codesigning) из него **НЕ извлечены
и не дизассемблированы**. Использовать для анализа format validation нельзя.
B3 dyld shared cache не присутствует.

---

## Компоненты, отсутствующие в корпусе — MISSING

| Компонент | Назначение (по заданию) | Локальный статус |
|---|---|---|
| `trustd` | trust evaluation daemon | MISSING. Бинарь не найден ни в B2, ни в B3 corpus. Все выводы о его роли — по имени/строкам, не по коду. |
| `CoreTrust.framework` | низкоуровневая валидация подписи, обычно реализует `AMFIPathValidator` internals | MISSING. Не извлечён из dyld cache, нет disasm. Реализация `initWithURL:...`/`validateWithError:`/`computedCdHash:`/`signerType`/`isValid`/`areEntitlementsValidated` — внутренности НЕ доступны. |
| `libmis.dylib` | provisioning profile / MIS database | MISSING. Вызывается из amfid через `MISCopyProvisioningProfile`, `MISProfileDBClient`, `MISAgent`, `MISDataMigrate`, `MISValidateSignatureAndCopyInfo` — но реализация НЕ доступна. |
| `libsecurity_codesigning` | code-signing policy engine | MISSING. Не найден как отдельный бинарь. |
| `Security.framework` | CMS/certificate evaluation | MISSING. Не извлечён из dyld cache. CMS-валидация, проверка цепочки сертификатов — внутренности НЕ доступны. |
| `MobileInstallation.framework` | install-side signing info | MISSING. `MICodeSigningInfo`/`MICodeSigningVerifier` вызываются из installd, но их реализация живёт в этом фреймворке — недоступна. |

---

## Вспомогательные артефакты

- RC diagnostic logs/reports — присутствуют, но **RC amfid binary, RC installd
  binary и RC entitlement/policy артефакты НЕ присутствуют**.
- B2/B3 amfid/installd entitlement plists — идентичны (SHA-256 совпадает).
- Извлечённые Info.plist — пустые (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Apple SDK/Xcode headers relevant to this service — не присутствуют.
- amfid launchd plist — не присутствует; endpoint registration виден только через
  `bootstrap_check_in("com.apple.MobileFileIntegrity")` в коде.
- Предшествующие отчёты Phase 1–8 — используются как контекст, не изменяются.

---

## Вывод по покрытию

Прямой код анализа доступен только для **amfid** (обе версии) и **installd**
(обе версии). Все компоненты, выполняющие собственно криптографическую проверку
подписи, CMS, проверку цепочки сертификатов и запись решения в MIS database,
находятся в MISSING-фреймворках/библиотеках:

- `AMFIPathValidator` (CoreTrust) — вызывается, но реализация не видна.
- `MICodeSigningInfo` / `MICodeSigningVerifier` (MobileInstallation) — вызываются, реализация не видна.
- `MISCopyProvisioningProfile` / `MISAgent` / `MISValidateSignatureAndCopyInfo` (libmis) — вызываются, реализация не видна.
- XNU/AMFI enforcement — kernelcache присутствует, но policy path не декодирован.

Следствие: Phase 9 может реконструировать **вызовную архитектуру**, порядок
проверок и семантику передачи ошибок на границе amfid/installd. Любые утверждения
о том, *что именно* происходит внутри CoreTrust, Security, libmis или XNU,
оформляются только как `NOT VERIFIED` / `UNKNOWN`, поскольку код этих компонентов
не извлечён.
