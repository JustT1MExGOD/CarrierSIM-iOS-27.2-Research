# Phase 17 · Отчёт 01 — Базовая проверка доказательств

## 1. Назначение документа

Сверка доказательств Phase 16 с текущими бинарниками и фиксация точных
адресов для Phase 17.

## 2. Бинарники (перепроверено)

| Файл | Размер | UUID | SHA-256 |
|---|---|---|---|
| `C:\ipsw-tools\CommCenter_B2.bin` | 41 018 192 | `83978CC2-2FEC-36B0-A77C-B9A90ED9C28C` ✅ | `9e815d9e…` |
| `C:\ipsw-tools\CommCenter_B3.bin` | 40 370 720 | `747592DD-284C-37BC-AE32-0FE36E8CB3DA` ✅ | `9a5eeaf3…` |

Оба Mach-O arm64e `MH_EXECUTE`, 176 LC, ObjC/C++-метаданные,
`LC_SYMTAB`/`LC_FUNCTION_STARTS`/`LC_DYLD_CHAINED_FIXUPS`.

## 3. Подтверждённые адреса (перерезолвлены в текущих бинарниках)

| Метод | B2 IMP | B3 IMP | Источник |
|---|---|---|---|
| `CTXPCServerEntitlementProvider::requiredEntitlementForRequest:` | `0x10000d374` | `0x10000cf20` | `__objc_classlist`→method_list |
| `CTXPCClientHandler::isSimMatching:carrierDescriptors:completion:` | `0x1018243f4` | `0x1017d6740` | то же |
| `CTXPCClientHandler::copyCarrierBundleValue:key:bundleType:completion:` | `0x1000ced88` | `0x1000cb128` | то же |
| `CTXPCFactory::createEntitlementChecker:forConnection:` | `0x100017b40` | `0x1000176a8` | то же |
| `CTXPCServer::clientHandler:hasEntitlement:` | `0x10001fdec` | `0x10001f520` | то же |
| `CTCarrierSpaceClientProxy::_isEntitledForControl` | `0x10095a0e4` | `0x1009401b8` | то же |

## 4. Новые доказательства Phase 17

| Доказательство | Место | Уровень |
|---|---|---|
| `requiredEntitlementForRequest:` — это **request→entitlement таблица на стеке** | `0x10000d374`/`0x10000cf20` | **A** — дизассемблирование |
| 309 (B2)/312 (B3) пар `ObjC-селектор → код entitlement` | таблица на стеке | **A** — извлечён `ldr`/`str`/`mov` поток |
| `CarrierBundleOverlay` — C++ value-type | `__TEXT __const` | A |
| `HomeBundleIdentifier` читается из overlay-файла и входит в match-info | `0x102144d50`/`0x1021468dd` | A |
| `Overlay active, not validating the SIMs` | `0x10210d7ed`/B3 `0x10208c02d` | A |
| `SupportedSIM %s is not allowed for MVNO Overlay` | `0x10206a045`/B3 `0x101fefd57` | A |
| `Failed to find IMSI in the overlay matching info` | `0x102069f13`/B3 `0x101fefc25` | A |

## 5. Методология Phase 16 — перепроверена

- ObjC method-IMP резолв: `class_ro_t.baseMethods` → relative method_list →
  `selname` через selref-slot (chained `0x100000000+low32`) + IMP `e+8+im`.
  Проверено на `setController:`/`.cxx_*` — корректно.
- `requiredEntitlementForRequest:` — дизассемблирован в обеих версиях;
  выявлено строительство request→entitlement map через `ldr selref` +
  `str [x8,#off]` + `mov w?,#code` + `str [x8,#off+8]` с шагом 0x10.

## 6. Ограничения

- `matchCarrierBundle_sync`/`match*` IMP — C++ методы (не ObjC), резолвятся
  через call-graph, а не selrefs; иерархия по именам (уровень B).
- Тело `match*` в `CarrierBundleUtilities.dylib` недоступно.
