# PHASE7 — 02_EXPORTED_PROTOCOL

## Цепочка IPC endpoint → ответ

```text
launchd/mach bootstrap: com.apple.amfi.nsxpc   [NOT VERIFIED как глобально reachable]
        │
NSXPCListener.initWithMachServiceName: + setDelegate(AMFIDelegate) + resume
        │   sub_10000a4f4 @ 0x10000a4f4
        ▼
-[AMFIDelegate listener:shouldAcceptNewConnection:]  @ 0x10000a400
        │   AMFIService *svc = [AMFIService new]
        │   svc.connection = conn
        │   conn.exportedInterface = [NSXPCInterface interfaceWithProtocol:AMFIProtocol]
        │   conn.exportedObject    = svc
        │   [conn resume]; return 1
        ▼
Dispatch по селектору из AMFIProtocol
        │
   ┌────┴───────────────┐
   │ getSEPStateWithReply│ @ 0x100004c0c
   │ getStagedProfileWithReply│ @ 0x100006230
   └────────────────────┘
        │
        ▼
        reply block вызывается через blraa (PAC-signed block ptr из аргумента)
```

## Метод 1 — `getSEPStateWithReply:`

- Адрес: `0x100004c0c` (функция начинается с `pacibsp`, стек-фрейм 0xd0, canary `___stack_chk_guard`).
- Сигнатура протокола: `v24@0:8@?<v@?{?=III{?=C{?=I[32C]}}}@"NSError">16`
  - один блочный аргумент reply: `void(struct SEPState, NSError*)`.
- Тело:
  1. `LAStorage.alloc initWithDomain:0 authenticationContext:0`.
  2. `[storage dataForKey:0xf error:&err]` → `NSData`.
  3. При ошибке логирует `unable to get SEP state` и возвращает `AMFIError(code 0x…fe68)`.
  4. При успехе `getBytes:buf length:0x31` — копирует **49 байт** в локальную структуру на стеке.
  5. Логирует `returning SEP state | [exists: %u]`.
  6. Вызывает reply-блок `(bufStruct, nil)` через `blraa`.

- Вспомогательные вызовы: `LAStorage dataForKey:error:`, `NSData getBytes:length:`, `os_log`, `AMFIError initWithAMFIErrorCode:withURL:`. **Ни одного вызова `connection`, `valueForEntitlement`, `verifyBoolEntitlement`, audit-token API в теле нет.** [OBSERVED, HIGH]
- Проверки перед ответом: только обработка ошибки чтения `dataForKey:`; переполнение буфера исключено фиксированной длиной 0x31.

## Метод 2 — `getStagedProfileWithReply:`

- Адрес: `0x100006230` (pacibsp, фрейм 0x50, без canary-нужды — локальных массивов нет).
- Сигнатура протокола: `v24@0:8@?<v@?@"NSString"@"NSError">16`
  - один блочный аргумент reply: `void(NSString*, NSError*)`.
- Тело:
  1. Лог `acquiring staged UUID`.
  2. `[NSString stringWithContentsOfFile:@"/private/var/db/amfid/UPPStaging.plist" encoding:4(NSUTF8) error:&err]`.
  3. При ошибке логирует `unable to read staged file`, но **всё равно** вызывает reply с `(nil, err)` — `blraa` исполняется в любом случае (loc_1000062f0 общий выход).
  4. Reply получает сырое содержимое файла как `NSString` либо `nil` + `NSError`.

- Вспомогательные вызовы: `NSString stringWithContentsOfFile:encoding:error:`, `os_log`, `blraa` на блок. **Ни одного gate/entitlement/audit-token вызова в теле.** [OBSERVED, HIGH]

## Степень уверенности

| Элемент | Confidence | Основание |
|---|---|---|
| Принадлежность методов `AMFIService` | HIGH | ObjC method list класса + метаданные |
| Принадлежность методов экспортируемому `AMFIProtocol` | HIGH | `__objc_protolist` + `__objc_methlist` разобраны напрямую |
| Адреса функций B3 | HIGH | символьные метки дизасма + PAC-прологи |
| Отсутствие gate в телах обоих методов | HIGH | полный просмотр тел (0x100004c0c–0x100004e04; 0x100006230–0x100006370) |
| Поведение reply-блока (структура/строка) | HIGH | типы из `__objc_methtype` + трассировка `blraa` аргументов |

## Что метод точно НЕ делает

- `getSEPStateWithReply:` не читает файловую систему — читает LAStorage (LocalAuthentication key store, ключ `0xf`), то есть данные под управлением LA/SEP-подсистемы, не plist.
- `getStagedProfileWithReply:` не вызывает `verifyBoolEntitlement`, в отличие от соседнего `stageProfileForUuid:` (0x100005f9c вызывает gate с `com.apple.private.amfi.schedule-profile`).
- Ни один из методов не проверяет `self.connection` вообще — объект `connection` сохраняется при accept и используется только `verifyBoolEntitlement:`.
