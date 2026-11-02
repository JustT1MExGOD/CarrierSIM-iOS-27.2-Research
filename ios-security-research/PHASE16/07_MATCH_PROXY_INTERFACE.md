# Phase 16 · Отчёт 07 — CarrierBundleMatchProxyInterface

## 1. Назначение документа

Идентификация реализации `CarrierBundleMatchProxyInterface`, его методов,
транспорта и границ (lookup/match/selection/override).

## 2. Что доказано (уровень A)

- `CarrierBundleMatchProxyInterface` — **C++ класс в CommCenter**
  (`…MatchProxyInterfaceD2Ev`, `…MatchProxyInterfaceEEE3…` — деструктор +
  vtable-refs).
- Обработчики XPC: `xpc::dict`, `xpc::auto_reply`, `ctu::RestModule`,
  `dispatch::queue`, `Registry` — в mangled-сигнатурах
  `…ERKN…shared_ptrIK8RegistryEERKN3ctu10RestModuleERKN8dispatch5queueE
  RKN3xpc4dictENSI_10auto_replyE…` → **это XPC-сервис** внутри CommCenter.
- REST-поверхность `carrier_bundles`/`operator_bundles`/`default_bundle`
  property sinks — подписки на изменение match-результата.

## 3. Роль в потоке

`CarrierBundleMatchProxyInterface` — **прокси между XPC-клиентом и
`CarrierBundleHandler`**: принимает match-запрос (`xpc::dict` с
matching-info), вызывает `matchCarrierBundleForSim_sync`/`matchCarrierBundle_sync`,
возвращает результат в `auto_reply`. По имени и контексту это **lookup/
match/read**, не запись.

## 4. Lookup vs Match vs Selection vs Override

| Слой | Доказательство |
|---|---|
| **Lookup** | `copyCarrierBundleValue{,WithDefault,WithCountryBundleLookup,s}` — чтение значений из уже выбранного bundle |
| **Match** | `matchCarrierBundleForSim_sync`/`matchCarrierBundle_sync`, `isSimMatching:carrierDescriptors:completion:` — вычисление match по matching-info |
| **Selection** | `match{Operator,Country,Default,Bootstrap,DefaultBCAM}Bundle_sync` — выбор кандидата |
| **Override** | `IMSIOverride`, `override_carrier_list.json` (B2), `CarrierBundleOverlay` (`Added HomeBundleIdentifier from overlay file to matching info`) |

**Override — отдельный механизм** (`IMSIOverride`, overlay), не метод
`MatchProxyInterface`. Прямых доказательств, что `MatchProxyInterface`
изменяет сопоставление, нет — его роль **read/match**, не write.

## 5. Полномочия

`EntitlementChecker:forConnection:`, `EntitlementCache`,
`requiredEntitlementForRequest:`, `clientHandler:hasEntitlement:` —
gate'ы перед XPC-вызовами. `MatchProxyInterface` — XPC-сервис, значит его
вызовы проходят через entitlement-фильтр CommCenter (см. отчёт 09).
Конкретный ключ на этот интерфейс не разобран (`INSUFFICIENT EVIDENCE`).

## 6. Что не доказано

- Набор селекторов/методов `MatchProxyInterface` (тело vtable в
  недоступной части/абстрактный класс).
- Может ли он изменять сопоставление — **нет доказательств записи**;
  роль — match/lookup.
- Является ли он доступным обычному приложению — XPC-наличие ≠
  публичность; гейтится `EntitlementChecker`.
