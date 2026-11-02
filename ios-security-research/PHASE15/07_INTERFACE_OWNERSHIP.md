# Phase 15 · Отчёт 07 — Принадлежность CarrierBundle*Interface

## 1. Назначение документа

Определение владельца `CarrierBundle*Interface` после восстановления
`CommCenter_B2.bin`. Чрезмерная формулировка Phase 14 («internal CommCenter
API», основанная только на строках) теперь **доказана** на уровне A.

## 2. Доказательство владельца (уровень A)

В `CommCenter_B2.bin` найдены **C++ mangled-символы** всех интерфейсов —
не голые строки, а имена с шаблонными сигнатурами и деструкторами:

| Интерфейс | Символы в CommCenter |
|---|---|
| `CarrierBundleInstallInterface` | `…InstallInterface`, `…InstallInterfaceD2Ev` |
| `CarrierBundleMatchProxyInterface` | `…MatchProxyInterface`, `…MatchProxyInterfaceD2Ev`, `…MatchProxyInterfaceEEE3…` |
| `CarrierBundleLockdownInterface` | `…LockdownInterface`, `…LockdownInterfaceD2Ev` |
| `CarrierBundleManagerInterface` | `…ManagerInterface`, `…ManagerInterfaceD2Ev` |
| `CarrierBundleServerInterface` | `…ServerInterface`, `…ServerInterfaceD2Ev` |
| `CarrierBundleCache/Downloader/Factory/XMLCache/BOMCopier/ActivationCarrierBundle/Update` + `CTXPCCarrierBundleNotification` | присутствуют (строки + символы) |

`D2Ev` — деструктор класса, `EEE…` — vtable/typeinfo-ссылки: это **реальные
C++ классы**, определённые в этом объектнике.

## 3. Транспорт и обработчики (уровень A)

`kCarrierBundleTriggerInstallCarrierBundle` имеет полный XPC-прототип в
mangled-имени:
```
…ERKN…shared_ptrIK8RegistryEERKN3ctu10RestModuleE
 RKN8dispatch5queueERKN3xpc4dictENSI_10auto_replyEEUlbE_FvbEEE
```
→ обработчик принимает `Registry`, `ctu::RestModule`, `dispatch::queue`,
`xpc::dict`, `xpc::auto_reply` — то есть интерфейсы обслуживаются через
XPC-сервер внутри CommCenter, а не являются локальными хелперами.

`LC_LOAD_DYLIB /usr/lib/CarrierBundleUtilities.dylib` → логика чтения
значений bundle делегирована библиотеке, CommCenter — её хост.

## 4. Entitlement-гейтинг (уровень A → SUPPORTED)

В `__TEXT`/строках CommCenter присутствуют:

- `EntitlementChecker:forConnection:` (ObjC-селектор),
- `EntitlementChecker`, `EntitlementCache`, `EntitlementController`,
- `EntitlementCheckForAttachMonitorMode`, `EntitlementAuthTokenType`,
- `com.apple.carrierspace.control.allow`, `com.apple.carrierspace.authinfo`,
  `com.apple.carrierspace.token`.

Это подтверждает, что **механизм проверки entitlement в CommCenter
реализован**. Точный список ключей, проверяемых для каждого
`CarrierBundle*Interface`, требует разбора `EntitlementChecker` по адресу
вызова — но сам факт гейтинга подтверждён существованием классов.

## 5. Вердикт по отношению к Phase 14

| Phase 14 вывод | Phase 15 статус |
|---|---|
| «internal CommCenter API» | **CONFIRMED** — C++-классы в CommCenter, XPC-обработчики. |
| «entitlement-gated» | **SUPPORTED BUT INCOMPLETE** — `EntitlementChecker` существует; конкретные ключи не разобраны. |
| «владелец неизвестен» | **опровергнуто** — владелец = `CommCenter` (`LC_LOAD_DYLIB` + символы). |
