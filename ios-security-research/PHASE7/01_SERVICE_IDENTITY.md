# PHASE7 — 01_SERVICE_IDENTITY

## 1. Реализующий бинарник

Оба исследуемых метода — `getSEPStateWithReply:` и `getStagedProfileWithReply:` — являются методами класса `AMFIService` в бинарнике `amfid` (Apple Mobile File Integrity daemon).

| Поле | B2 | B3 |
|---|---|---|
| Файл | `amfid_B2.bin` | `amfid_B3.bin` |
| Путь на устройстве | `/usr/libexec/amfid` (по конвенции; в корпусе нет launchd plist amfid — см. §4) | то же |
| Mach-O | EXECUTE, arm64e (USR00) | EXECUTE, arm64e (USR00) |
| UUID | `3E6D3282-527E-3BC1-8A9F-1C2BABF3A894` (по 01_INVENTORY) | `CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B` |
| SHA-256 | `39d4d583…001ccd9` | `d331a101…0db8f` |
| Размер | 253 968 B | 253 968 B |

Замечание по UUID: непосредственный разбор LC_UUID даёт идентичное поле `c0850300-505a-…` в обоих файлах — вероятно, оба дампа построены из dyld-cache slice, где UUID был перезаписан/не восстановлен; уверенные build-различия лежат в SHA-256 и строках версии. Точные UUID по инвентарю приведены выше; приведённое LC_UUID-значение помечено как артефакт извлечения. **[NOT VERIFIED как абсолютный UUID]**

## 2. Версия iOS

- B2: iOS 27.2 Beta 2 (build-train по `01_INVENTORY`, ld 27100.x).
- B3: iOS 27.2 Beta 3 (ld 27106), build `24B5099f__iPhone16,1`.

RC-бинарник amfid в корпусе отсутствует → сравнение с RC: **NOT AVAILABLE**.

## 3. Регистрация IPC endpoint

В `amfid_B3_disasm.txt` (функция `sub_10000a4f4`, строки 9553–9606):

```text
0x10000a530: "com.apple.amfi.nsxpc"
bl j__objc_msgSend(x0, "initWithMachServiceName:")
… setDelegate: (AMFIDelegate)
… resume
"%s: NSXPC interface setup successfully"
```

**[OBSERVED]** Бинарник создаёт `NSXPCListener` через `initWithMachServiceName:@"com.apple.amfi.nsxpc"` и назначает `AMFIDelegate` делегатом. Это имя фактически используется кодом — не просто лежащая строка.

Дополнительно в Phase 6 зафиксирован отдельный MIG/Mach путь `bootstrap_check_in("com.apple.MobileFileIntegrity")` — это второй, отдельный endpoint (mach-urcil/MIG), не относящийся к исследуемым NSXPC-методам. **[OBSERVED из Phase 6]**

## 4. Launchd-конфигурация

В корпусе **нет** plist `com.apple.amfid.plist` / `com.apple.MobileFileIntegrity.plist` для B2/B3/RC — извлечённые файловые системы не содержат LaunchDaemons. Доступны только entitlement-профили `ents/amfid_B2/B3.entitlements.plist`.

Следствие: **кто именно объявляет MachService `com.apple.amfi.nsxpc`, в каком bootstrap-namespace он живёт и какие `LimitLoadToSessionType`/`MachServices` правила применяются — NOT VERIFIED.**

## 5. Экспортируемый IPC-протокол

`AMFIDelegate listener:shouldAcceptNewConnection:` (0x10000a400–0x10000a4f0) выполняет:

```objc
AMFIService *svc = [AMFIService alloc] init];
svc.connection = newConnection;           // setConnection:
NSXPCInterface *iface = [NSXPCInterface interfaceWithProtocol:@protocol(AMFIProtocol)];
newConnection.exportedInterface = iface;
newConnection.exportedObject    = svc;
[newConnection resume];
return 1;
```

Протокол **`AMFIProtocol`** подтверждён из `__objc_protolist` бинарника (3 протокола: `AMFIProtocol`, `NSObject`, `NSXPCListenerDelegate`).

## 6. Полный список методов AMFIProtocol

Восстановлен из `__objc_methlist` (13 методов, все required, class/opt lists пусты):

| # | Селектор | Параметры → reply |
|---|---|---|
| 0 | `initiateDataMigrationWithReply:` | → `void(NSError*)` |
| 1 | `initiateDeveloperModeDaemonsWithReply:` | → `void(NSError*)` |
| 2 | **`getSEPStateWithReply:`** | → `void(struct{I,I,I,{C,{I,C[32]}}}, NSError*)` |
| 3 | `signTeamID:withSignType:withLAContext:withReply:` | (NSString, int, LAContext) → `void(NSData*, NSError*)` |
| 4 | `stageProfileForUuid:withReply:` | (NSString) → `void(NSError*)` |
| 5 | **`getStagedProfileWithReply:`** | → `void(NSString*, NSError*)` |
| 6 | `commitProfileForUuid:withReply:` | (NSString) → `void(NSError*)` |
| 7 | `setTrustForTeamID:withSignature:withSignType:withReply:` | (NSString, NSData, int) → `void(NSError*)` |
| 8 | `removeTrustforTeamID:withReply:` | (NSString) → `void(NSError*)` |
| 9 | `setSupervisedState:withReply:` | (int) → `void(NSError*)` |
| 10 | `setDemoState:withReply:` | (int) → `void(NSError*)` |
| 11 | `setManagedState:withReply:` | (LAContext) → `void(NSError*)` |
| 12 | `removeManagedStateWithReply:` | → `void(NSError*)` |

Типы восстановлены из `__objc_methtype` extended-method-types таблицы (file offsets 0x20f58–0x21088). **Степень уверенности: HIGH** — имена и подписи прочитаны напрямую из объектных метаданных, а не из строк.

`getStagedProfileWithReply:` действительно входит в экспортируемый набор; `getSEPStateWithReply:` — тоже.

## 7. Ограничения на уровне подключения

- `listener:shouldAcceptNewConnection:` возвращает `1` без какой-либо ветки отказа — **OBSERVED accept-all NSXPC** на уровне этого метода.
- Никакого `auditToken`, `SecTask…`, `xpc_connection_get_*`, `valueForEntitlement` в accept-фазе нет.
- Ограничения могут существовать выше (launchd bootstrap namespace, sandbox `mach-lookup` правила, `com.apple.amfi.nsxpc` не объявлен в глобальном namespace) — **в корпусе не восстановлены; NOT VERIFIED.**

## Итог

| Факт | Статус |
|---|---|
| Бинарник/класс методов | CONFIRMED (amfid/AMFIService) |
| Имя NSXPC endpoint `com.apple.amfi.nsxpc` | CONFIRMED (используется в `initWithMachServiceName:`) |
| Протокол `AMFIProtocol` и оба getter'а в нём | CONFIRMED (из __objc_protolist) |
| Launchd bootstrap policy для endpoint | NOT VERIFIED |
| RC-версия бинарника | NOT AVAILABLE |
