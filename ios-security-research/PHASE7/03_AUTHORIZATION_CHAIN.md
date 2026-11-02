# PHASE7 — 03_AUTHORIZATION_CHAIN

## Четыре раздельных свойства

Phase 6 предупреждала: «обнаружить имя», «установить соединение», «вызвать метод» и «получить содержательный ответ» — не эквивалентны. Раскладываю по уровням.

## Уровень 1 — обнаружение имени службы (lookup)

- Имя `com.apple.amfi.nsxpc` создаётся кодом `initWithMachServiceName:` — NSXPCListener регистрирует Mach service в своём bootstrap namespace. [OBSERVED]
- Регистрирующий bootstrap namespace для системного демона — обычно `bootstrap_system` или per-user launchd domain. Какой именно — из корпуса не видно. Launchd plist amfid отсутствует. **[NOT VERIFIED]**
- Sandbox-правило `mach-lookup` на клиенте может запретить resolve имени даже при его существовании. Клиентский sandbox профиль для «обычного приложения» не разобран. **[NOT VERIFIED]**
- Рядом существует отдельный endpoint `com.apple.MobileFileIntegrity` (MIG/mach, `bootstrap_check_in`). Он не имеет отношения к NSXPC-протоколу — смешивать их нельзя.

**Lookup-резюме:** имя существует [CONFIRMED]; кто может его разрешить — **NOT VERIFIED**.

## Уровень 2 — установление соединения (accept)

`-[AMFIDelegate listener:shouldAcceptNewConnection:]` @0x10000a400:

```text
alloc/init AMFIService
svc.connection = conn
iface = [NSXPCInterface interfaceWithProtocol:proto_AMFIProtocol]
conn.exportedInterface = iface
conn.exportedObject    = svc
[conn resume]
return 1
```

- В функции **нет** ветки `return 0`: ни проверки `auditToken`, ни `valueForEntitlement`, ни euid/pid сравнений — только `os_log` «received NSXPC Connection». [OBSERVED, HIGH]
- `interruptionHandler`/`invalidationHandler` в этом методе не устанавливаются (в отличие от installd) — отсутствие обработчиков не является security-фактом, отмечено для полноты.
- Никаких class-restriction/allowlist вызовов на `NSXPCInterface` (например `setClasses:forSelector:argumentIndex:ofReply:`) в accept-методе не выполняется — типы параметров берутся из протокола. Для двух getter'ов параметры только `NSError*`/`NSString*`/plain struct — class-whitelist риск здесь нерелевантен.

**Accept-резюме:** на уровне приложения решение «принять» принимается без проверки идентичности. [CONFIRMED для локального кода]

## Уровень 3 — вызов конкретного метода (dispatch)

- Диспетчеризация NSXPC идёт по селекторам `AMFIProtocol`; оба getter'а присутствуют в протоколе (см. 02). [CONFIRMED]
- `NSXPCInterface` whitelist-ограничений по селекторам не добавлено — все 13 методов одинаково доступны на уровне dispatch. [OBSERVED]

## Уровень 4 — авторизация внутри метода

| Метод | Видимые проверки в теле | Где проверяется |
|---|---|---|
| `getSEPStateWithReply:` | нет `connection`/`verifyBoolEntitlement`/audit | **никуда** — gate отсутствует в теле |
| `getStagedProfileWithReply:` | нет `connection`/`verifyBoolEntitlement`/audit | **никуда** — gate отсутствует в теле |
| (контраст) `stageProfileForUuid:` | `verifyBoolEntitlement:@"com.apple.private.amfi.schedule-profile"` | в самом методе |
| (контраст) `commitProfileForUuid:` | `verifyBoolEntitlement:@"com.apple.private.amfi.commit-profile"` | в самом методе |
| (контраст) `setTrustForTeamID:…` | `verifyBoolEntitlement:@"com.apple.private.amfi.set-trust"` | в самом методе |
| (контраст) `getSEPStateWithReply:` vs все 11 mutator'ов | единственные два метода протокола без `verifyBoolEntitlement:`: **`getSEPState`, `getStagedProfile`, `initiateDataMigration`?** — проверено по таблице вызовов: gate есть у всех, кроме двух getter'ов. `initiateDataMigration` имеет gate @0x1000059b8 (`data-migration`), `initiateDeveloperModeDaemons` @0x100005eac. | — |

`verifyBoolEntitlement:` @0x100004abc читает `self.connection → valueForEntitlement:name → NSNumber → boolValue`, fail-closed при nil/не-NSNumber. То есть механизм авторизации в бинарнике существует и реализован единообразно — у mutator'ов он вызван, у двух getter'ов нет. [OBSERVED]

## Уровень 5 — содержательный ответ

- `getSEPStateWithReply:` возвращает 49-байтовую структуру (LAStorage key 0xf) или NSError — даже при ошибке reply вызывается. Чувствительность структуры см. 04/06.
- `getStagedProfileWithReply:` возвращает текстовое содержимое `/private/var/db/amfid/UPPStaging.plist` целиком как NSString или NSError.
- «Получить ответ» ≠ «ответ содержит секреты» — классификация данных отдельно в 06.

## Где решение о допуске фактически принимается

```text
 [lookup]    sandbox/launchd bootstrap      NOT VERIFIED (материалы отсутствуют)
 [connect]   shouldAcceptNewConnection:     ACCEPT-ALL (return 1 без ветки отказа)
 [dispatch]  AMFIProtocol                   без per-selector ограничений
 [method]    getSEPState / getStagedProfile БЕЗ внутренних проверок
 [mutators]  verifyBoolEntitlement          есть у всех state-changing методов
```

Единственная место, где для getter'ов может быть реальная авторизация, — **уровень lookup/transport** (sandbox `mach-lookup`, bootstrap namespace, правило в launchd plist). Именно этот уровень в корпусе отсутствует.

## Что бы доказало уязвимость

Для `CONFIRMED` потребовалось бы показать клиент без `com.apple.private.amfi.*`, который (а) может resolve `com.apple.amfi.nsxpc`, (б) проходит sandbox, (в) вызывает getter и (г) получает чувствительный контент. Сейчас доказаны (в)+частично (г) — метод исполняется без gate; (а),(б) — NOT VERIFIED.
