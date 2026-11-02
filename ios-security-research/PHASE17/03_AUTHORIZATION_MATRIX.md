# Phase 17 · Отчёт 03 — Матрица авторизации

## 1. Уровни, которые нельзя смешивать

1. **Метод существует** — он присутствует в Mach-O/метод-таблице.
2. **IPC/XPC-сервис существует** — CommCenter регистрирует обработчик.
3. **Request имеет entitlement-код** — запись есть в
   `requiredEntitlementForRequest:` map.
4. **Соединение проходит проверку** — `EntitlementChecker`/`hasEntitlement`
   возвращает allow (статически без конкретного connection это не проверить).
5. **Операция выполнена** — нужен runtime; Phase 17 его не проводит.

## 2. Матрица request→код

| Категория | Request-примеры | Код B2/B3 | Что можно утверждать |
|---|---|---:|---|
| Carrier-bundle read | `copyCarrierBundleValue*`, `copyCarrierBundleValues*`, `copyCarrierBundleVersion`, `copyCarrierBookmarks` | 1 | request зарегистрирован; конкретное entitlement-имя для кода `1` не восстановлено |
| Carrier-bundle lookup | `getCountryBundleLocationForBundleIdentifier`, `copyBundleIdentifier`, `copyBundleLocation`, `getCountryBundleLocationForMatchingInfo`, `getCountryBundleIdentifierForCountryCode` | 3 | request зарегистрирован; lookup не равен override |
| Carrier-bundle update | `checkForUpdatedBundlesWithAutoInstall:` | 3 | update request существует и gated той же map |
| Carrier-bundle reset | `restoreToSystemBundles` | 19 | отдельный более высокий/системный класс кода |
| Carrier-bundle test | `setTestBundleIdForSlice:` | 14 | test/slice request, не IMSI mapping |
| SIM/read | `getSubscriptionInfo`, `getActiveContexts`, `getDualSimCapability` | map entries | IPC request существует; allow зависит от connection |
| SIM write/test | `setVirtualSimMode`, SIM Toolkit operations, `simulateDataStall` | map entries | наличие не означает доступ обычному приложению |
| Debug/test | B2 `injectMTsms`, `invalidateKey` | B2-only | удалены из request map B3 |

## 3. Проверочные компоненты

```text
XPC connection
  └─ CTXPCFactory::createEntitlementChecker:forConnection:  (B2 0x100017b40)
       └─ EntitlementChecker / EntitlementCache / EntitlementController
            ├─ CTXPCServer::clientHandler:hasEntitlement: (0x10001fdec)
            ├─ CTXPCServerEntitlementProvider::requiredEntitlementForRequest:
            │    (B2 0x10000d374, B3 0x10000cf20)
            └─ CTCarrierSpaceClientProxy::_isEntitledForControl (0x10095a0e4)
```

## 4. Интерпретация кодов

Коды `1`, `3`, `14`, `19` — внутренние значения map (вероятно enum/уровень
доступа), а **не сами entitlement-строки**. Сопоставление `code→key` требует
разбора `requiredEntitlementForRequest:` вызывающего кода/таблицы
`EntitlementProvider`; Phase 17 не подменяет это предположением.

## 5. CarrierSIM relevance

- `copyCarrierBundleValue*` (код 1) — read API; не пишет каталог и не меняет
  SIM-to-bundle mapping.
- `checkForUpdatedBundles`/lookup (код 3) — update/lookup; наличие request
  не доказывает право создавать IMSI-alias.
- `restoreToSystemBundles` (код 19) — reset к системным bundle, не alias.
- Ни одна извлечённая запись map не называется `setIMSIOverride`,
  `setBundleForIMSI` или аналогично.

## 6. Вывод

Carrier-bundle request map **сохранилась между B2 и B3**. Доступность XPC
обычному приложению не следует из наличия методов; реальные allow/deny требуют
конкретного entitlement connection и не проверялись активным IPC.
