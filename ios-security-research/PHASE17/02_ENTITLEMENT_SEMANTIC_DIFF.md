# Phase 17 · Отчёт 02 — Семантический diff requiredEntitlementForRequest:

## 1. Функция и границы

| Версия | Адрес | Пролог | Эпилог | Видимая длина |
|---|---:|---|---|---:|
| B2 | `0x10000d374` | `pacibsp; stp x28,x27; …; sub sp,#0x390` | `add sp,#0x390; ldp; retab` | 1352 инструкций до `retab` |
| B3 | `0x10000cf20` | `pacibsp; stp x28,x27; …; sub sp,#0x370` | аналогичный | 1344 инструкций |

Сегменты/UUID: `CommCenter_B2.bin` SHA `9e815d9e…`, UUID
`83978CC2-…`; `CommCenter_B3.bin` SHA `9a5eeaf3…`, UUID
`747592DD-…`.

## 2. Что делает функция

Первые ветви — lazy-init внутренней таблицы/кэша:

```asm
B2 0x10000d3b4: adrp x8, #0x102576000
B2 0x10000d3c0: tbz  w8, #0, 0x10000d448
B2 0x10000d3c4: adrp x8, #0x102576000
B2 0x10000d3d0: ldr  x9, [x8,#0x20]
B2 0x10000d3d4: cmp  x2, x9
...
B2 0x10000d40c: ldr  w0, [x8,#0x28]
B2 0x10000d414: mov  w0, #2
```

B3 имеет ту же CFG и условия, с адресными заменами:

```asm
B3 0x10000cf60: adrp x8, #0x1024da000
B3 0x10000cf6c: tbz  w8, #0, 0x10000cff4
B3 0x10000cf70: adrp x8, #0x1024da000
B3 0x10000cf7c: ldr  x9, [x8,#0x20]
...
B3 0x10000cfb8: ldr  w0, [x8,#0x28]
B3 0x10000cfc0: mov  w0, #2
```

Таблица строится как записи по 16 байт:

```asm
adrp x13, __objc_selrefs_page
ldr  x13, [x13,#offset]       ; selector pointer
str  x13, [x8,#N]              ; request key
str  w13, [x8,#N+8]            ; entitlement class/code
```

## 3. Полная матрица carrier-bundle запросов

Извлечённые коды одинаковы в B2 и B3:

| Request | Код |
|---|---:|
| `copyCarrierBundleValue:key:bundleType:completion:` | 1 |
| `copyCarrierBundleValue:keyHierarchy:bundleType:completion:` | 1 |
| `copyCarrierBundleValueWithDefault:key:bundleType:completion:` | 1 |
| `copyCarrierBundleValueWithDefault:keyHierarchy:bundleType:completion:` | 1 |
| `copyCarrierBundleValues:keys:defaultValues:bundleType:withFallbackBundleCheck:completion:` | 1 |
| `copyCarrierBundleValues:keyHierarchies:defaultValues:bundleType:withFallbackBundleCheck:completion:` | 1 |
| `copyCarrierBundleValueWithCountryBundleLookup:keyHierarchy:matchingInfo:completion:` | 3 |
| `getCountryBundleLocationForBundleIdentifier:completion:` | 3 |
| `copyBundleIdentifier:bundleType:completion:` | 3 |
| `copyBundleLocation:bundleType:completion:` | 3 |
| `checkForUpdatedBundlesWithAutoInstall:completion:` | 3 |
| `getCountryBundleLocationForMatchingInfo:completion:` | 3 |
| `getEnglishCarrierNameFor:completion:` | 3 |
| `restoreToSystemBundles` | 19 |
| `copyBundleVersion:bundleType:completion:` | 3 |
| `copyCarrierBundleVersion:completion:` | 3 |
| `copyCarrierBundleLocation:completion:` | 3 |
| `copyCarrierBookmarks:completion:` | 1 |
| `getCountryBundleIdentifierForCountryCode:completion:` | 3 |

## 4. Реальный semantic diff

- **Carrier-bundle request set:** не изменился.
- **Коды для carrier-bundle requests:** не изменились.
- **CFG таблицы:** не изменился по условиям/ветвям; изменились размеры
  stack-frame (`0x390`→`0x370`) и адреса глобальных таблиц.
- **Общий map diff (подтверждён повторной экстракцией, 302/300 paired
  записей, 307/305 всего):**
  - B2-only: `injectMTsms:smsData:completion:`,
    `invalidateKey:with:`;
  - B3-only: `addParticipants:toGroupChat:withParticipantsToAdd:
    withOperationID:withSecurity:completion:` (не carrier-bundle).
- `bootstrapQuickSwitchEnrollmentFlowAsSecondary:completion:` — код **25
  в обеих версиях**; ранее отмеченная разница «310→308» была артефактом
  чтения смещения записи как кода и **снята**. Общих записей с изменённым
  кодом нет — единственный вид diff'а это добавление/удаление sel'екторов.

## 5. Вывод

**H17-01 для carrier-bundle операций не подтверждается.** Изменение
`requiredEntitlementForRequest:` — адресная/компиляторная перестройка таблицы
и удаление/добавление несвязанных запросов; carrier-bundle requests и их
коды неизменны. `requiredEntitlementForRequest:` в целом нельзя объявлять
байт-в-байт идентичной: размер и общий набор не-carrier requests изменились.
