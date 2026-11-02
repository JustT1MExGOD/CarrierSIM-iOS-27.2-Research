# PHASE9 — 02_TRUST_ARCHITECTURE

## Метод

Реконструкция архитектуры принятия решения о доверии строго по доступному коду.
Каждый компонент описан только в той мере, в которой он виден в дизассемблере.
Звенья, проходящие через MISSING-компоненты (см. `01_TRUST_COMPONENT_INVENTORY.md`),
помечены `[DELEGATED — implementation NOT AVAILABLE]`.

---

## 1. Два независимых пользовательских IPC-интерфейса amfid

amfid экспортирует **два разных интерфейса** для разных классов клиентов:

### A. NSXPC endpoint — `com.apple.amfi.nsxpc`

Регистрация (Phase 7): `NSXPCListener initWithMachServiceName:@"com.apple.amfi.nsxpc"`.
Протокол `AMFIProtocol` — 13 required methods (из `__objc_protolist`):

- `initiateDataMigrationWithReply:`
- `initiateDeveloperModeDaemonsWithReply:`
- `getSEPStateWithReply:`
- `signTeamID:withSignType:withLAContext:withReply:`
- `stageProfileForUuid:withReply:`
- `getStagedProfileWithReply:`
- `commitProfileForUuid:withReply:`
- `setTrustForTeamID:withSignature:withSignType:withReply:`
- `removeTrustforTeamID:withReply:`
- `setSupervisedState:withReply:`
- `setDemoState:withReply:`
- `setManagedState:withReply:`
- `removeManagedStateWithReply:`

Характер: **state-management API** — управление trust state, provisioning
profiles, developer mode, supervised/demo/managed state. Это НЕ per-file
validation API; это управление политикой и состоянием.

Авторизация: per-method `-[AMFIService verifyBoolEntitlement:]` →
`NSXPCConnection valueForEntitlement:` (`amfid_B3_disasm.txt:3275-3304`).
Mutating методы имеют отдельные entitlement-строки (Phase 7: `set-trust`,
`set-supervised`, `set-demo`, `set-managed`, `data-migration`,
`developer-mode-control`, `schedule-profile`, `commit-profile`, `remove-trust`).

### B. Mach MIG endpoint — `com.apple.MobileFileIntegrity`

Регистрация (Phase 9):

```text
sub_1000049c8:
  bootstrap_port
  bootstrap_check_in(bootstrap_port, "com.apple.MobileFileIntegrity")
  → если ошибка: syslog("unable to checkin with launchd: %s")

sub_100004a24:
  os_transaction_create("amfid mig server")
  dispatch_mach_mig_demux(msg, reply, ...subsystem...)
  → если demux вернул false: mach_msg_destroy(msg)
```

MIG demux — это сервер `com.apple.MobileFileIntegrity` (MIG subsystem, msg IDs
в районе `0x3e8+`). Это **per-file validation API** — клиент (обычно ядерный
AMFI hook или другой daemon) присылает Mach message с security token +
URL/path + флагами, amfid выполняет проверку и возвращает структурированный ответ.

Подтверждённые MIG stub'ы (Phase 9):

| Stub | Вызывается из | Функция | Семантика возврата |
|---|---|---|---|
| `sub_100004030` | `sub_10000b194` (msgh `0x441`+, размер тела ≥ `0x428`) | `verify_code_directory` — валидация path + file offset + flags | Out-struct: `computedCdHash`, `signerType`, `isValid`, `areEntitlementsValidated`, `profileData`, `profileAuxSig` + поля valid/len |
| `sub_10000366c` | `sub_10000b3d8` (msgh, размер `0x38`) | `construct_der_entitlements` — DER-encode entitlement XML | Return code: `0`=success, `0x5`=bad token, `0xe`=DER error; out: transmuted blob |
| `sub_100003ba4` | `sub_10000b5xx` (msgh, размер `0x43c`+, OOL payload) | вторая entitlement-функция (по OOL-data + signature match) | Return code, `mig_deallocate` входного OOL |

Ключевой факт для архитектуры: **оба интерфейса существуют одновременно** и
выполняют разные роли. NSXPC управляет состоянием; MIG выполняет per-file
validation по запросу. Это стандартное разделение AppleMobileFileIntegrity:
NSXPC — privileged configuration, MIG — validation service.

---

## 2. Цепочка per-file validation (MIG `verify_code_directory`)

Реконструировано по `sub_100004030` (`amfid_B3_disasm.txt:2547-2798`).

```text
[MIG msg in] → sub_10000b194 (demux, проверка msgh_id/size/OOL)
            → sub_100004030(x0=input_blob, x1=token_struct, x2..xN=out_ptrs)

sub_100004030:
  1. zero output status/result fields                     @0x100004068–0x10000409c
  2. проверка security-token structure:
       ldp x8,x9 / ldp x10,x11 → orr все 4 → cbz
       если НЕ все нули → syslog("%s: bad security token { 0x%x ... }")
                          → w21=0x5 → exit (error path)
  3. AMFIPathValidator_ios alloc
  4. initWithURL:(x2) withFileOffset:(x3) withFlags:(x4)   @0x1000041b4
  5. validateWithError:&err                                @0x1000041c4
       cbz result → FAILURE PATH (release, ret)
  6. SUCCESS PATH:
       computedCdHash:withLength:                          @0x1000041e8
       signerType                                          @0x1000041f0
       isValid                                             @0x1000041fc
       areEntitlementsValidated                            @0x100004208
       profileData                                         @0x100004214
         если profileData != NULL:
           [profileData bytes] / [profileData length]
           vm_read(mach_task_self, bytes, length, buf)      @0x100004260
           при vm_read-ошибке: zero out-valid/len, →fail
           иначе: mark profile-copy valid
       profileAuxSig                                       @0x1000042b8
         [profileAuxSig bytes] / [profileAuxSig length]
         vm_read(mach_task_self, bytes, length, buf)        @0x100004300
         при vm_read-ошибке: log("unable to vm_read profileAuxSig: %d")
                            zero out-ptr/len →continue to completion
         иначе: mark aux-copy valid
  7. release objects, ret
```

Что делает amfid **сам**: построение validator, вызов `validateWithError:`,
чтение результата (`isValid`, `signerType`, `computedCdHash`,
`areEntitlementsValidated`), выборочное копирование `profileData` и
`profileAuxSig` через `vm_read` в ответ клиенту.

Что amfid **делегирует**: саму валидацию подписи. `AMFIPathValidator_ios`
— это объект из недоступного фреймворка (CoreTrust / связанный signing
framework, см. `01_TRUST_COMPONENT_INVENTORY.md`). Внутренности —
парсинг Mach-O, SuperBlob, CodeDirectory, CMS, проверка цепочки —
`[DELEGATED — implementation NOT AVAILABLE]`.

Семантика ответа (из caller `sub_10000b194`):

```text
sub_10000b194:
  вызывает sub_100004030
  собирает out-поля в reply:
    reply+0x24: isValid byte
    reply+0x28: signerType (w20)
    reply+0x34: areEntitlementsValidated byte
    reply+0x38: (w21)
    reply+0x3c: NDR_record
    reply+0x58: pointer на OOL region
    reply+0x64..: profileData (var-len, strlen+1)
    далее: profileAuxSig (16+16 байт + byte)
    reply+0: msgh_bits | 0x80000000  (complex reply)
    reply+4: total size
    reply+0x18: msg_id 0x2  → это msg_id в reply
  ret
```

Т.е. MIG `verify_code_directory` возвращает **структурированный trust record**,
а не просто boolean. Клиент (вероятно, kernel или другой daemon) получает
`isValid` как главное решение, плюс cdHash, signerType, флаг проверки
entitlements, и (опционально) сами данные профиля.

---

## 3. Цепочка DER entitlement construction (MIG `construct_der_entitlements`)

Реконструировано по `sub_10000366c` (`amfid_B3_disasm.txt:1860-2125`) и caller
`sub_10000b3d8` (`amfid_B3_disasm.txt:10614-10703`).

```text
sub_10000366c(x0=entitlement_xml, x1=xml_len, x2=?, x3=out_code_ptr,
              x4=out_bufptr, x5=token_struct):
  1. проверка token:
       ldp 8 слов → orr все 4
       если ≠0 → syslog("%s: bad security token { 0x%x ... }")
                 → w21=0x5 → exit
  2. syslog("Being asked to construct DER entitlements")
  3. если xml_len < 8 → w24=1 → error path
  4. buffer[0x50] = 0xAA-fill; copy xml+8 → null-terminate
  5. sub_1000155f0(&buf, &err) — AMFIUnserializeXML-shaped
       если err или result NULL → "AMFIUnserializeXML failed" → w24=0
  6. CFDataCreateWithBytesNoCopy(xml+8, len-8)
     CFPropertyListCreateWithData
     если NULL → "Cannot construct DER entitlements, possibly corrupt XML"
                 → w21=0xe → exit
     если typeID ≠ CFDictionary → "entitlement anomaly" → w24=1 → w21=0xe
  7. CECRuntime / CESerializeCFDictionary → der_data
     если result ≠ kCENoError → CFRelease, w21=0xe → exit
  8. vm_read(mach_task_self, der_ptr, der_len, out)         @0x100003a60
     если ошибка → zero out[0], out[1] → exit (w21=0xe path)
     иначе → out[0]=1, syslog("Successfully transmuted entitlements.")
             w21=0 → success
```

Семантика caller `sub_10000b3d8`:

```text
  вызывает sub_10000366c → w21 = return code
  mig_deallocate(input OOL buffer)
  если w21 ≠ 0:
      reply+0x20 = w21       (error code в reply)
      reply+0x18 = NDR_record
      ret (reply — error reply)
  иначе:
      reply+0x24 = transmuted_valid byte
      reply+0x28 = transmuted_len
      reply+0x2c = NDR_record
      reply+0 = complex
      reply+4 = 0x38 size
      reply+0x18 = msg_id 0x1
```

Это **fail-closed по error-code**: любая ошибка (`0x5`, `0xe`, `0xfffffecb`,
`0xfffffed0`, `0xfffffed4`) записывается в reply как код и не создаёт
«valid»-структуру. Клиент по коду возврата может отличить причины.

Критическое архитектурное различие:

- `sub_100004030` (`verify_code_directory`): boolean `isValid` в reply,
  + данные.
- `sub_10000366c` (`construct_der_entitlements`): error code в reply
  (0=success, иначе причина) + transmuted blob.

Оба интерфейса используют **разные соглашения** «0 = OK» vs «isValid =
boolean». Это нормально для разных протоколов, но является источником
ошибок на стороне клиента, если он смешает семантику — Phase 9 фиксирует
это как архитектурное наблюдение, а не как уязвимость.

---

## 4. Кто вызывает валидацию

Прямых вызовов `AMFIPathValidator_ios` в amfid — только из MIG stub'ов
(`sub_100004030`, `sub_10000b194`). Других callers `initWithURL:...` внутри
amfid_B3_disasm нет в показанных диапазонах. Из этого следует:

- Per-file validation входит в amfid **только через MIG endpoint**
  `com.apple.MobileFileIntegrity`, а не через NSXPC.
- Кто является клиентом MIG endpoint — статически не установлено.
  По архитектуре iOS это обычно kernel AMFI hook (`AppleMobileFileIntegrity`
  в kernelcache) или другие доверенные daemon'ы. Локального артефакта,
  который бы посылал MIG msg `0x441`, в корпусе нет.
- `bootstrap_check_in` используется (Phase 9, `sub_1000049c8`), а не
  `bootstrap_look_up` — amfid регистрирует сервис у launchd.

Статус: клиент MIG endpoint — `NOT VERIFIED` (нет клиентского артефакта в
корпусе). Имя сервиса и MIG-структура подтверждены; reachability — нет.

---

## 5. Цепочка state-management (NSXPC)

```text
[NSXPC conn] → shouldAcceptNewConnection: (permissive — Phase 7)
            → AMFIService method dispatch
            → verifyBoolEntitlement:@"com.apple.private.amfi.<op>"
               → NSXPCConnection valueForEntitlement:
               → NSNumber isKindOfClass → boolValue
            → MISAgent / libmis calls:
                 MISCopyProvisioningProfile
                 trustTeamID:signature:error:
                 signingIdentitiesWithTeamID:
                 MISDataMigrate
                 MISValidateSignatureAndCopyInfo (NOT VERIFIED — string only)
            → LAStorage / SEP state (LocalAuthentication)
```

Изменение состояния доверия (set-trust, remove-trust, supervised, demo,
managed, profile stage/commit, sign) проходит через entitlement-gated
NSXPC методы, а не через MIG `verify_code_directory`. Это подтверждённое
разделение: **validation API (MIG) не изменяет состояние; management API
(NSXPC) изменяет состояние, но не выполняет per-file validation.**

`initiateDataMigrationWithReply:` (Phase 9, `amfid_B3_disasm.txt:4282+`)
требует `com.apple.private.amfi.data-migration` и вызывает `MISDataMigrate`
после внутренних проверок (SEP epoch, code-signing state, demo mode) —
это пример NSXPC-метода, который внутри себя вызывает MIS/libmis, но
всё ещё gated по entitlement.

---

## 6. installd-side trust flow

installd использует **вторую ветвь** — `MICodeSigningInfo` / `MICodeSigningVerifier`
(в MISSING `MobileInstallation.framework`). Реконструированные вызовы в B3:

```text
-[MIInstallableBundle _isValidWatchKitApp:...]:
  MIDaemonConfiguration codeSigningEnforcementIsDisabled      @0x1000535b0
    → если TRUE: skip validateWatchKitV2StubExecutableBundle
       (log "Boot-args disabled code signing enforcement ...")
    → если FALSE: MICodeSigningVerifier
       validateWatchKitV2StubExecutableBundle:error:          @0x100053664
       → при fail: error "invalid application executable"
  → _verifyPluginKitPlugins:...:checkAppexSignatures:checkFrameworkSignature:

-[MIInstallableBundle _validateApplicationIdentifierForNewBundleSigningInfo:error:]:
  codeSigningEnforcementIsDisabled                            @0x1000540d4
    → если TRUE: codeSignerType==1 (internal) → skip, log INTERNAL-ONLY
    → если FALSE: error path

+[MIInstallableBundle _shouldSkipEligibilityChecksForInstallRequestorWithAuditToken:...]:
  MICodeSigningInfo signingIdentifierForAuditToken:error:     @0x10005a4cc
  MITestManager isRunningInTestMode: + testFlagsAreSet:0x200
    → если test-runner + test mode + flag: skip eligibility
  audit_token_to_pid при ошибке
```

Количество callsites `codeSigningEnforcementIsDisabled`: **5 в B2, 5 в B3**
(без изменений между бетами — см. `07_VERSION_DIFFS.md`).

Архитектурный факт: installd **не вызывает** `AMFIPathValidator` напрямую.
Он делегирует проверку подписи устанавливаемого bundle'а в
`MICodeSigningVerifier`/`MICodeSigningInfo` (MobileInstallation.framework,
MISSING). Сам `codeSigningEnforcementIsDisabled` — **policy flag**, читаемый
из daemon configuration; он не является runtime-переключателем через IPC и
не подтверждён как изменяемый клиентом.

---

## 7. Доверенная цепочка (high-level)

```text
[installer client]
   │
   ▼ NSXPC (MobileInstallerProtocol, 75 methods)
[installd] ──► MICodeSigningInfo / MICodeSigningVerifier
   │              (MobileInstallation.framework — MISSING impl)
   │              ├─ signingIdentifierForAuditToken
   │              ├─ validateWatchKitV2StubExecutableBundle
   │              └─ getValue:forEntitlement:fromProcessWithAuditToken
   │
   └─► MIDaemonConfiguration.codeSigningEnforcementIsDisabled  (policy flag)

[kernel AMFI hook / other daemon]   [NSXPC client]
   │                                    │
   ▼ Mach MIG                          ▼ NSXPC (AMFIProtocol)
[com.apple.MobileFileIntegrity]    [com.apple.amfi.nsxpc]
   │                                    │
   ├─ verify_code_directory            ├─ verifyBoolEntitlement
   │   → AMFIPathValidator_ios         │      → valueForEntitlement
   │       (CoreTrust — MISSING impl)  ├─ MISAgent/libmis
   │                                   │      (MISCopyProvisioningProfile,
   ├─ construct_der_entitlements       │       trustTeamID, signingIdentities,
   │   → CFPropertyList/CE serialize   │       MISDataMigrate)
   │       (MISSING impl details)      └─ LAStorage / SEP
   │
   ▼
[XNU/AMFI kernel enforcement — kernelcache present, policy NOT decoded]
```

Граница ответственности (по доступному коду):

- **amfid**: orchestration — принимает MIG msg, вызывает validator, копирует
  результат в reply; принимает NSXPC calls, проверяет entitlement, вызывает MIS.
- **installd**: orchestration — принимает install request, вызывает
  `MICodeSigningVerifier`/`Info`, применяет policy flags.
- **CoreTrust / Security / libmis / MobileInstallation / XNU-AMFI**:
  `[DELEGATED — implementation NOT AVAILABLE]` — собственно криптография,
  CMS, формат-парсинг, запись решения, kernel enforcement.

---

## 8. Архитектурные наблюдения (не уязвимости)

1. **Два разных reply-протокола.** `verify_code_directory` возвращает
   `isValid` boolean + данные; `construct_der_entitlements` возвращает
   error code + blob. Это нормально, но создаёт поверхность для
   клиентских ошибок интерпретации.
2. **Validation и management разделены.** MIG — read-only validation;
   NSXPC — state-changing management. Ни один MIG stub не вызывает MIS.
3. **Policy flag `codeSigningEnforcementIsDisabled`** имеет 5 callsites в
   каждой сборке и используется как условие для skip валидации внутренних
   app'ов/WatchKit. Это конфигурационная ветвь, не runtime API.
4. **Test-mode bypass** в `_shouldSkipEligibilityChecks...` требует
   одновременно: signing id = `com.apple.mi-test-runner`, test mode ON,
   flag `0x200`. Это многофакторное условие, не single-entitlement.
5. **Отсутствие direct amfid→installd или installd→amfid callsites** в
   показанных фрагментах. Связь — через общие framework'и (MIS), не через
   прямой IPC между этими daemon'ами.
