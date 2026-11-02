# Phase 16 · Отчёт 09 — Границы entitlement

## 1. Назначение документа

Разбор `EntitlementChecker:forConnection:` и связанных проверок полномочий,
где они выполняются и что защищают.

## 2. Компоненты entitlement-контроля (уровень A)

| Компонент | Роль | Адрес/имя |
|---|---|---|
| `CTXPCFactory::createEntitlementChecker:forConnection:` | фабрика checker'а | IMP `0x100017b40` |
| `EntitlementChecker` | проверка entitlement по XPC-connection | класс |
| `EntitlementCache` | кэш результатов | класс |
| `EntitlementController` | контроллер | класс |
| `CTXPCServer::clientHandler:hasEntitlement:` | точечная проверка | IMP `0x10001fdec` |
| `CTXPCServer::_processAppEntitlement_sync:appInfo:` | обработка app-entitlement | IMP `0x10001969c` |
| `CTXPCServerEntitlementProvider::requiredEntitlementForRequest:` | карта request→required entitlement | IMP `0x10000d374` |
| `CTXPCServerEntitlementProvider::requiredEntitlementForNotification:` | для нотификаций | IMP `0x1000307f8` |
| `CTCarrierSpaceClientProxy::_isEntitledForControl` | контроль carrierspace | IMP `0x10095a0e4` |
| `CTCarrierSpaceClientProxy::entitlementValidator` | валидатор | IMP `0x10095d974` |
| `EntitlementCheckForAttachMonitorMode` | конкретная проверка | строка |

## 3. Архитектура

```
XPC connection ──► createEntitlementChecker:forConnection:
                          │
                          ▼
              EntitlementChecker (per-connection)
                          │
        requiredEntitlementForRequest:  (request → entitlement map)
        clientHandler:hasEntitlement:   (точечный запрос)
        _processAppEntitlement_sync:    (app-level)
                          │
                          ▼
              allow / deny обработчика
```

- **Где проверяются**: на границе XPC-connection (`forConnection:`), в
  точке dispatch каждого request (`requiredEntitlementForRequest:`),
  и на уровне отдельного handler (`hasEntitlement:`).
- **Кэширование**: `EntitlementCache` — результат проверки кэшируется
  на соединение.

## 4. Entitlement-ключи (строки, уровень B для конкретных значений)

Видимые ключи в строках:

- `com.apple.carrierspace.control.allow`,
  `com.apple.carrierspace.authinfo`, `com.apple.carrierspace.token`;
- `com.apple.commcenter.*` (множество `…commcenter.<sub>`);
- `com.apple.bridgecarriersettings`;
- `com.apple.abm.cellularcert(.allow)`;
- `com.apple.cellular-data.blocklist`.

## 5. Что защищается

- `CTCarrierSpaceClientProxy` (`_isEntitledForControl`, `entitlementValidator`)
  — carrierspace-интерфейс гейтится.
- `CTXPCServer` — каждый request проверяется через
  `requiredEntitlementForRequest:` → map.
- Carrier-bundle интерфейсы (`Install`/`MatchProxy`/`Lockdown`) — XPC,
  значит гейтятся той же схемой `requiredEntitlementForRequest:`.

## 6. Что доступно без специальных entitlement

- `copyCarrierBundleValue` / `copyCarrierBundleVersion` /
  `copyBundleLocation` / `getEnglishCarrierNameFor` — **read-only**
  операции, вероятно доступны обычным процессам (это публичный CT API
  `copyCarrierBundleValue`).
- Установка/override/match-запись — требуют entitlement (carrier-space/
  commcenter ключи).

## 7. Что нельзя вывести по статике

- Точный ключ entitlement на каждый конкретный `CarrierBundle*Interface`
  (`requiredEntitlementForRequest:` — map request→key; содержимое map не
  разобрано — `INSUFFICIENT EVIDENCE`).
- Политика для `MatchProxyInterface`/`InstallInterface` конкретно —
  нужна таблица request→key.
- Наличие XPC ≠ доступность приложению: все carrier-bundle XPC гейтятся.

## 8. B2 vs B3

`createEntitlementChecker`, `hasEntitlement`, `_isEntitledForControl`,
`requiredEntitlementForNotification` — **SAME** (normalized-hash).
`requiredEntitlementForRequest:` — **DIFF** по размеру (≥1000 insn) —
возможно расширение request→key map; содержимое изменения не разобрано
(`INSUFFICIENT EVIDENCE`).
