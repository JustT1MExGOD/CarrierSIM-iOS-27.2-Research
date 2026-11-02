# Phase 16 · Отчёт 03 — CarrierBundleHandler

## 1. Назначение документа

Восстановление структуры `CarrierBundleHandler` и его match-методов по
C++ mangled-именам, присутствующим в `CommCenter_B2.bin` (и идентичным в B3).

## 2. Идентификация класса

`CarrierBundleHandler` — **C++ класс**, не ObjC (отсутствует в
`__objc_classlist`). Его методы вызываются напрямую через `bl` (не через
`objc_msgSend`), а `__func__`/mangled-имена хранятся в `__TEXT __const`
как lambda-имена для `std::function` и os_log-дескрипторов.

## 3. Восстановленный C++ API (уровень A, mangled-имена)

| Метод | Сигнатура |
|---|---|
| `matchCarrierBundle_sync` | `(CFSharedRef<CFDictionary const>&, CFSharedRef<CFDictionary const>&, WirelessTechnologyList, subscriber::SimSlot, bool)` |
| `matchCarrierBundleForSim_sync` | `(subscriber::SimSlot, CFSharedRef<CFDictionary const>&, ...)` |
| `matchDefaultBundle_sync` | `()` |
| `matchDefaultBCAMBundle_sync` | `()` |
| `matchBootstrapBundle_sync` | `(CFSharedRef<CFDictionary const>&, CFSharedRef<CFDictionary const>&, bool)` |
| `matchOperatorBundle_sync` | `(CFSharedRef<CFDictionary const>&, subscriber::SimSlot, bool)` |
| `matchCountryBundle_sync` | `(BundleType, CFSharedRef<CFDictionary const>&, subscriber::SimSlot, bool)` |
| `sendBundleEvent_sync` | `(BundleType, BundleChangeType, subscriber::SimSlot)` |
| `installCarrierBundle_sync` | `(CFSharedRef<__CFURL const>&, function<void(bool)>)` |
| `installiTunesUpdateBundles_sync` | `(CFSharedRef<__CFArray const>&, bool, function<void(bool)>)` |
| `getRemoteCardSettingsServerURL_sync` | `(CFSharedRef<CFDictionary const>&, function<void(CFSharedRef<CFString const>)>)` |
| `handleCellularPlanTransferCarrierBundleUpdateRequest_sync` | `(rest::TransferCarrierBundleUpdateRequest&&, rest::command_responder_t<TransferCarrierBundleUpdateError>&&)` |
| `loadEquivalentTableFrom_sync` | `(basic_string const&, map<MCCAndMNC, optional<vector<...>>>&)` |
| `loadSidTableFrom_sync` | `(basic_string const&, map<Cdma1xCell, optional<vector<...>>>&)` |

## 4. Сигнатура главного метода

`matchCarrierBundle_sync` принимает:

- `CFSharedRef<CFDictionary const>` — **matching info** (SIM-идентификаторы);
- второй `CFSharedRef<CFDictionary const>` — вероятно контекст/опции;
- `WirelessTechnologyList` — список технологий;
- `subscriber::SimSlot` — слот SIM;
- `bool` — флаг (вероятно `force`/`notify`).

**Две реализации** (`…EES8_…` и `…EES5_…` — два разных типа второго dict,
вероятно shared_ptr vs raw/другой dictionary-тип) — перегруженные варианты
или две точки входа (internal и ForSim-обёртка).

## 5. Иерархия match

Из имён методов восстанавливается **иерархия**:

```
matchCarrierBundleForSim_sync (entry, per-SIM-slot)
        │
        ▼
matchCarrierBundle_sync (core match: info dict + tech + slot + flag)
        │
        ├── matchOperatorBundle_sync   (по оператору)
        ├── matchCountryBundle_sync    (по стране/региону)
        ├── matchDefaultBundle_sync    (fallback)
        ├── matchDefaultBCAMBundle_sync(BCAM/boot-campaign default)
        └── matchBootstrapBundle_sync  (bootstrap-пакет)
```

- `matchCarrierBundleForSim_sync` — точка входа per-SIM-slot (вызывается из
  `handleSIMCarrierInfo_sync`/`isSimMatching:`-пути).
- `matchCarrierBundle_sync` — центральный диспетчер, выбирающий между
  operator/country/default/bootstrap/bcam ветками.
- `sendBundleEvent_sync` — применение результата + уведомление.

## 6. Ключевые доказательства логики (строки __TEXT)

- `Sent request %s to match bundle, received result: %s` — match через
  запрос к engine.
- `match carrier bundle to apply GSMA overlay based off the user pref` /
  `match carrier bundle for GSMA settings` — GSMA-overlay поверх match.
- `homeBundleIdentifierFromMatchInfo provided to search for best match
  with SIM Info. Returning bundle match` — match-info → bundle id.
- `bundle matching info is invalid` / `matching info is invalid` — валидация.
- `match result: %s` / `match result for %s` — результат.
- `CarrierBundleUpdateMatchData`, `kCarrierBundleWatchBundleMatchCriteria`.

## 7. Что вне CommCenter

`matchCarrierBundle_sync` делегирует фактическое скоринг-совпадение
`CarrierBundleUtilities.dylib` (`LC_LOAD_DYLIB` подтверждён) и `CoreTelephony`
— эти тела недоступны → точный scoring IMSI-vs-MCCMNC-vs-GID `UNKNOWN`.
CommCenter — оркестратор: собирает matching-info, вызывает engine, применяет
результат через `sendBundleEvent_sync`.

## 8. Call-graph (2 уровня, уверенность по типу вызова)

```
CTXPCClientHandler::isSimMatching:…completion:  [ObjC IMP 0x1018243f4, A]
   └─bl→ internal match path → CarrierBundleHandler::matchCarrierBundleForSim_sync [B: имя+иерархия]
         └─bl→ matchCarrierBundle_sync            [B: sibling, вызывается из ForSim]
               ├─bl→ matchOperatorBundle_sync      [B]
               ├─bl→ matchCountryBundle_sync       [B]
               ├─bl→ matchDefaultBundle_sync       [B]
               ├─bl→ matchDefaultBCAMBundle_sync   [B]
               ├─bl→ matchBootstrapBundle_sync     [B]
               └─bl→ sendBundleEvent_sync          [B]
                     └─bl→ CarrierBundleUtilities copyCarrierBundleValue* [A: LC_LOAD_DYLIB]
```
