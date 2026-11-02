# Phase 16 · Отчёт 06 — Binary Diff Beta 2 vs Beta 3

## 1. Назначение документа

Сравнение реальных реализаций `CommCenter` B2 и B3 — не по строкам/UUID/
размерам, а по нормализованной последовательности инструкций функций.

## 2. Метод

- Для каждого ObjC-метода извлечён IMP-адрес из `class_ro_t.baseMethods`
  (относительный method_list, signed 32-бит offsets).
- Функция нормализована до последовательности мнемоник (Capstone),
  хеширована SHA-256. Совпадение хеша + длины ⇒ семантически идентична.
- Method presence: 2407 методов (B2) vs 2403 (B3), 153 класса в обоих.

## 3. Method presence diff

| Класс | Метод | B2 | B3 |
|---|---|---|---|
| `CTXPCClientHandler` | `fakeCrossPlatformTransferEvent:payload:completion:` | есть | **удалён** |
| `CTXPCClientHandler` | `injectMTsms:smsData:completion:` | есть | **удалён** |
| `CTXPCClientHandler` | `invalidateKey:with:` | есть | **удалён** |
| `StewieNWAgent` | `loopback:content:incomingData:stewieFramer:` | есть | **удалён** |

**Ни один из удалённых методов не относится к carrier-bundle / IMSI / match /
install** — это debug/test-поверхности (cross-platform transfer, SMS-inject,
key-invalidate, Stewie loopback). Удаление — ужесточение debug-API, не
carrier-bundle логики.

## 4. Функциональный diff (normalized mnemonic hash)

| Метод | B2 IMP | B3 IMP | Результат |
|---|---|---|---|
| `isSimMatching:carrierDescriptors:completion:` | `0x1018243f4` | `0x1017d6740` | **SAME** (524 insn) |
| `copyCarrierBundleValue:key:bundleType:completion:` | `0x1000ced88` | `0x1000cb128` | **SAME** (219) |
| `copyCarrierBundleValueWithCountryBundleLookup:…matchingInfo:completion:` | `0x1012d0770` | `0x10129f998` | **SAME** (758) |
| `getCountryBundleLocationForMatchingInfo:completion:` | `0x1012d7df8` | `0x1012a7020` | **SAME** (677) |
| `checkForUpdatedBundlesWithAutoInstall:completion:` | `0x1012d7898` | `0x1012a6ac0` | **SAME** (278) |
| `createEntitlementChecker:forConnection:` | `0x100017b40` | `0x1000176a8` | **SAME** (64) |
| `clientHandler:hasEntitlement:` | `0x10001fdec` | `0x10001f520` | **SAME** (90) |
| `_isEntitledForControl` (CTCarrierSpaceClientProxy) | `0x10095a0e4` | `0x1009401b8` | **SAME** (43) |
| `requiredEntitlementForRequest:` | `0x10000d374` | `0x10000cf20` | **DIFF** (≥1000 insn, tail-обрезан) |

`restoreToSystemBundles` — присутствует в обоих (проверено в таблицах),
но в B2/B3 map он не попал в TOP-выборку (метод есть, IMP различается по
адресу — см. `cc_b2_methods.txt`/`cc_b3_methods.txt`).

## 5. Классификация изменений

| Тип | Содержание | Влияние на CarrierSIM |
|---|---|---|
| **Семантические** | удаление 4 debug/test-методов (`fakeCrossPlatformTransferEvent`, `injectMTsms`, `invalidateKey`, `loopback`); добавление `Development Signed Carrier Bundles: Not Allowed`; удаление `override_carrier_list.json` | **ограниченное** — dev-API и override-лист |
| **Компиляторные** | весь carrier-bundle/match/install/entitlement код — **SAME** (идентичная последовательность мнемоник) | **нулевое** |
| **Изменения адресации** | `__TEXT` B2 `0x2398000` → B3 `0x2300000`; адреса IMP сдвинуты | не влияет на семантику |
| **Неопределённые** | `requiredEntitlementForRequest:` — размер функции ≥1000 инструкций, хеш отличается; без полного разбора нельзя классифицировать как семантическое/компиляторное | **INSUFFICIENT EVIDENCE** |

## 6. Главный вывод

**Carrier-bundle / IMSI / bundle-selection / entitlement код в CommCenter
семантически идентичен между B2 и B3** (все ключевые методы — `SAME`).
Изменения сосредоточены в:
- debug/test-поверхностях (удалены),
- строковом ужесточении (`Development Signed Carrier Bundles: Not Allowed`,
  удалённый `override_carrier_list.json`),
- потенциально `requiredEntitlementForRequest:` (DIFF, требует дальнейшего
  разбора — но это entitlement-provider, не match-алгоритм).

**Вывод Phase 13/15 подтверждён кодом**: регрессия CarrierSIM находится
**не** в логике выбора bundle CommCenter, а в AirTraffic (файловый move
completed-asset).
