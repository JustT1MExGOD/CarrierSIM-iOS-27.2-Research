# PHASE9 — 07_VERSION_DIFFS

## Метод

Сравнение Beta 2 → Beta 3 → RC только там, где есть парные артефакты.
Для компонентов без RC-артефакта — `NOT COMPARABLE`.

---

## 1. amfid B2 vs B3

### Бинарный уровень

| Параметр | B2 | B3 |
|---|---|---|
| SHA-256 | `39d4d58...01ccd9` | `d331a10...0db8f` |
| UUID | `3E6D3282-527E-3BC1-8A9F-1C2BABF3A894` | `CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B` |
| Размер | 253968 | 253968 |
| Disasm SHA-256 | `dbf55bc...deb3aa` | `dbf55bc...deb3aa` (идентичен) |

**Вывод:** размеры совпадают, disasm SHA-256 идентичен. Различие только в
UUID (build-embedded) и итоговом SHA-256 бинаря (UUID + возможные
timestamp/ordering differences). **Функциональных различий в amfid B2→B3
не обнаружено.**

### Проверенные функции (B3 disasm, применимо к B2)

- `sub_100004030` (`verify_code_directory` stub) — B3, идентично B2.
- `sub_10000366c` (`construct_der_entitlements` stub) — B3, идентично B2.
- `sub_1000049c8` (`bootstrap_check_in`) — B3, идентично B2.
- `sub_100004a24` (`dispatch_mach_mig_demux`) — B3, идентично B2.
- `AMFIProtocol` (13 methods), `verifyBoolEntitlement:` — Phase 7, B2≡B3.
- `initiateDataMigrationWithReply:` — B3; B2 присутствует (строки совпадают).

Статус: **NO FUNCTIONAL DIFF B2→B3** для amfid.

## 2. amfid RC

RC amfid binary **отсутствует**. RC диагностические логи присутствуют, но
не содержат amfid disasm/entitlements. Сравнение B3→RC для amfid:
**NOT COMPARABLE**.

## 3. installd B2 vs B3

### Бинарный уровень

| Параметр | B2 | B3 |
|---|---|---|
| SHA-256 | `f0f1ce4...08576f` | `1dd5efb...064b1d` |
| UUID | `5D0437D3-8824-39D1-8BEB-E8F48DA6F93B` | `F54A48D1-4E77-3425-BEAB-5EBBBB037C0F` |
| Размер | 945168 | 961888 (+16720 байт) |

Размер **отличается** — installd B3 больше на ~16KB. Это реальное различие,
в отличие от amfid.

### Функциональные точки сравнения

| Функция/сигнал | B2 | B3 | Различие |
|---|---|---|---|
| `codeSigningEnforcementIsDisabled` callsites | 5 (89497, 90274, 93764, 93878, 95756) | 5 (91801, 92578, 96157, 96271, 98149) | count паритет; адреса сдвинуты (ожидаемо при росте кода) |
| `MICodeSigningInfo` callsites | присутствует | присутствует | NOT QUANTIFIED diff |
| `MICodeSigningVerifier` callsites | присутствует | присутствует | NOT QUANTIFIED |
| `MIDaemonConfiguration` refs | присутствует | 76 total occurrences | NOT QUANTIFIED diff |
| `_shouldSkipEligibilityChecks...` | присутствует | присутствует (`sub_10005a468`) | NOT QUANTIFIED |
| `_ValidateMIAllowedSPIEntitlement` | присутствует | присутствует | Phase 6 — per-method gating |
| `MobileInstallerProtocol` methods | 75 | 75 | Phase 6 — parity |
| Test-mode helpers | присутствует | присутствует | NOT QUANTIFIED |

**Вывод:** installd B3 имеет +16KB кода при сохранении всех ключевых
trust-validation callsites. Количество `codeSigningEnforcementIsDisabled`
callers не изменилось (5→5). Без построчного diff нельзя утверждать, что
добавленные ~16KB — это новая trust-логика; возможны refactoring, новые
features, debug code. Статус: **CODE GROWTH OBSERVED; TRUST-RELEVANT
DIFF NOT QUANTIFIED**.

## 4. installd RC

RC installd binary **отсутствует**. Сравнение B3→RC: **NOT COMPARABLE**.

## 5. kernelcache B2 vs B3

| Параметр | B2 | B3 |
|---|---|---|
| SHA-256 | `35e3266...bfb85` | `c31c081...65a09` |

Разные хэши — kernelcache пересобран. AMFI policy path **не декодирован**
ни в одном. Сравнение AMFI-логики: **NOT COMPARABLE** (нет декодированного
policy).

## 6. sandbox kext B2 vs B3

| Параметр | B2 | B3 |
|---|---|---|
| SHA-256 | `c884a1a...7438` | `e41c7ea...0329` |
| `com.apple.amfi.nsxpc` offset | `0x1af2fb` | `0x1b0183` |

Строка `com.apple.amfi.nsxpc` присутствует в обоих; сдвиг offset
соответствует пересборке. Эффективные правила **не декодированы** в обоих.
Статус: **STRING PRESERVED; RULE DIFF NOT DECODED**.

## 7. dyld shared cache

Только B2 present (`11a4b07...ebb8`). B3 dyld — отсутствует. Trust-
relevant frameworks (CoreTrust, Security, MobileInstallation, libmis) —
не извлечены ни из одного. Статус: **NOT COMPARABLE** (B3 missing, B2
not extracted).

## 8. Entitlement plists

B2 и B3 amfid/installd entitlements: **SHA-256 идентичны**
(`e080c72...937a0d`). Никаких изменений entitlement'ов между бетами.
Статус: **IDENTICAL**.

## 9. Сводная таблица

| Компонент | B2→B3 | B3→RC | Вывод |
|---|---|---|---|
| amfid | disasm identical; UUID/build diff only | NOT COMPARABLE | no functional diff |
| installd | +16KB; callsite parity; count parity | NOT COMPARABLE | growth, trust-diff not quantified |
| kernelcache AMFI | rehash, not decoded | NOT COMPARABLE | not comparable |
| sandbox kext | string preserved, offset shift | NOT COMPARABLE | rules not decoded |
| dyld cache | B2 only, not extracted | — | not comparable |
| entitlements | identical | NOT COMPARABLE | no change |
| `codeSigningEnforcementIsDisabled` | 5→5 callsites | NOT COMPARABLE | parity |

---

## Вывод

- **amfid: функционально идентичен B2→B3.** Единственное различие —
  build UUID.
- **installd: рост ~16KB, trust callsites сохранены.** Есть изменения, но
  их trust-релевантность не установлена без полного diff.
- **RC: сравнение невозможно** — нет RC amfid/installd binaries.
- Все kernel/framework side diffs — `NOT COMPARABLE` из-за MISSING
  компонентов.

Ни одно подтверждённое различие B2→B3 не затрагивает trust decision path.
