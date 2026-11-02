# PHASE8 — 05_TRANSPORT_AUTHORIZATION

## Полная цепочка

```text
client process
  → launchd/bootstrap namespace lookup
  → Mach service resolution: com.apple.amfi.nsxpc
  → NSXPC connection handshake
  → amfid NSXPCListener
  → AMFIDelegate shouldAcceptNewConnection:
  → AMFIService + exported AMFIProtocol
  → selector dispatch
  → getter handler
  → reply block
```

## Уровень 1: Mach lookup и bootstrap

**Локально подтверждено:** серверный код вызывает `initWithMachServiceName:@"com.apple.amfi.nsxpc"`.

**Не подтверждено:**

- launchd объявляет ли имя в `MachServices` и каком domain;
- bootstrap namespace, видимый third-party app;
- client `mach-lookup` allow/deny;
- наличие entitlement-conditioned exception;
- ограничения `LimitLoadToSessionType` или service visibility.

Наличие `com.apple.security.exception.mach-lookup.global-name` в sandbox kext — это имя entitlement/policy mechanism, а не доказательство, что amfid endpoint разрешён или запрещён.

## Уровень 2: NSXPC connection

`AMFIDelegate`:

- принимает incoming connection;
- сохраняет его через `setConnection:`;
- создаёт `NSXPCInterface` из `AMFIProtocol`;
- устанавливает `exportedInterface` и `exportedObject`;
- вызывает `resume`;
- возвращает `1`.

В этом методе не видны:

- `auditToken` comparison;
- `SecTaskCopyValueForEntitlement`;
- `xpc_connection_get_audit_token/euid/pid`;
- code-signing identity check;
- UID/GID allowlist;
- client role check.

Это подтверждает accept-all behavior **после того, как connection уже достиг listener**. Оно не подтверждает возможность достижения listener.

## Уровень 3: method dispatch

`AMFIProtocol` recovered from ObjC metadata contains both getter selectors. No additional selector-specific allowlist is configured in the listener method. Therefore, for any connection accepted by this listener, protocol dispatch to both selectors is statically supported.

## Уровень 4: handler

`getSEPStateWithReply:` и `getStagedProfileWithReply:` не вызывают `self.connection`, `valueForEntitlement:` или known audit-token helpers. They do perform source-specific error handling:

- LAStorage read and fixed-size copy for SEP state;
- file read with UTF-8 conversion and NSError reply for staged profile.

## Уровень 5: вспомогательные функции

- `LAStorage dataForKey:error:` может иметь внутренние policy checks in LocalAuthentication.framework, но framework implementation и runtime result недоступны.
- `NSData getBytes:length:` — data copy, не authorization.
- `NSString stringWithContentsOfFile:encoding:error:` — file read; effective filesystem access depends on amfid's own sandbox/identity, не caller authorization.
- launchd/sandbox may enforce transport policy before handler; relevant artifacts absent/undecoded.

## Ответы на вопросы авторизации

| Механизм | Результат |
|---|---|
| Audit token in listener | не найден в просмотренном listener; transport-level use NOT VERIFIED |
| Code-signing identity | не найден в getter path; external policy NOT VERIFIED |
| Entitlement in listener | не найден; getter path no visible gate |
| UID/GID | не найден; launchd/client policy NOT VERIFIED |
| Client role/trusted origin | не найден; external policy NOT VERIFIED |
| Auxiliary authorization | possible in LAStorage/framework or sandbox, not recovered |

## Transport verdict

Наиболее точный вывод:

> Server-side authorization is absent in the two visible getter handlers and in the accept method, but client-side transport reachability is not established. The available corpus cannot distinguish “globally reachable but method ungated” from “endpoint restricted before NSXPC listener.”

Статус транспортной гипотезы: **NOT VERIFIED**, не `CONFIRMED` и не `RULED OUT`.
