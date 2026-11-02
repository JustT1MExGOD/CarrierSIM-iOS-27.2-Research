# Phase 17 · Отчёт 08 — B2/B3 diff по overlay

## 1. Метод

Сравнение по `p17_*_entmap.txt`, `cc_b2/b3_methods.txt`, строковому
инвентарю и фрагментам кода `requiredEntitlementForRequest:`. B2 —
`CommCenter_B2.bin` (iOS 27.2 Beta 2, `24B5089g`, UUID `83978CC2-…`),
B3 — `CommCenter_B3.bin` (iOS 27.2 Beta 3, `24B5099f`, UUID `747592DD-…`).

## 2. Присутствие overlay-механизма

| Элемент | B2 | B3 | Статус |
|---|---|---|---|
| `CarrierBundleOverlay` C++ type | есть | есть | без изменений |
| `HomeBundleIdentifier` | есть | есть | без изменений |
| `overlay file path` | есть | есть | без изменений |
| `overlay file as dictionary` | есть | есть | без изменений |
| `overlay matching info` | есть | есть | без изменений |
| `Failed to find IMSI in the overlay matching info` | `0x102069f13` | `0x101fefc25` | без изменений (адресная смена) |
| `Overlay active, not validating the SIMs` | `0x10210d7ed` | есть | без изменений |
| `This SupportedSIM %s is not allowed for MVNO Overlay` | `0x10206a045` | `0x101fefd57` | без изменений |
| `Added HomeBundleIdentifier from overlay file to matching info` | `0x102144d50` | формат `HomeBundleIdentifier = '%{public}s'` | реформатировано |
| `kMVNOMultimodeOverlay`, `kDeviceMultimodeOverlay`, `kDeviceMVNOMultimodeOverlay`, `kMultimodeGSMAOverlay`, `kDeviceMultimodeGSMAOverlay`, `kDeviceMVNOGSMAOverlay`, `kMVNOMultimodeGSMAOverlay`, `kDeviceMVNOGSMAOverlay` | есть | есть | без изменений |
| `TechSettingsSecondaryOverlay`, `IMSConfigSecondaryOverlay`, `CarrierEntitlementsSecondaryOverlay`, `PushSettingsSecondaryOverlay`, `LocationSecondaryOverlay`, `VoiceTextMediaOverlay` | есть | есть | без изменений |
| `override_carrier_list.json` | есть | **нет** | **удалено** |
| `com.apple.AppStoreOverlays.ViewService` | есть | есть | без изменений |

## 3. Entitlement-коды carrier-bundle операций

Отчёт 02 показал: для операций чтения/поиска carrier-bundle (`copyCarrierBundleValue`,
`copyCarrierBookmarks`, `copyBundleIdentifier`, `copyBundleLocation`,
`getCountryBundleLocation`, `restoreToSystemBundles`, `setTestBundleIdForSlice`)
требуемые коды **идентичны** B2/B3. Overlay не изменяет entitlement-границу.

## 4. Что изменилось в B3

- **Удалена строка `override_carrier_list.json`** — B2-специфичная
  конфигурация/файл; в B3 не присутствует. Назначение не восстановлено
  (B-level).
- **Форматирование лога** — `Added HomeBundleIdentifier …` заменено на
  `HomeBundleIdentifier = '%{public}s'` — семантика та же.
- **Адресное смещение** — все overlay-строки и коды сохранились, только
  vm-адреса сместились (размер `__TEXT` изменился).

## 5. Что не изменилось

- Чтение overlay как dictionary.
- IMSI-matching в `overlay matching info`.
- SupportedSIM/MVNO gate.
- Подмешивание `HomeBundleIdentifier` в matching-info.
- `Overlay active, not validating the SIMs` — skip-флаг сохранён.
- `Rematch carrier bundle to apply GSMA overlay` — перенастройка при
  обновлении bundle.
- `kLookupGSMAConfiguration` — точка запроса GSMA overlay.

## 6. Новые ограничения в B3

**Не найдено**. Phase 17 не обнаружила в B3 новых строк/проверок,
ограничивающих overlay по сравнению с B2. Изменения —
компиляторно-адресные, форматирование и удаление `override_carrier_list.json`.

## 7. Вывод

Overlay-механизм **полностью сохранён** в B3. Основная регрессия
Beta 3 (`107: Capabilities insufficient` при записи symlink'а) находится
**вне** overlay-подсистемы — это AirTraffic/AFC-write path. В B3 не
появилось нового механизма overlay-записи, который мог бы компенсировать
потерю CarrierSIM.
