# Фаза 14 — восстановление CommCenter

## 1. Поиск CommCenter

`CommCenter` — ключевой компонент выбора carrier bundle. Проверены все доступные локальные образы.

### 1.1. Доступные источники

| Источник | Сборка | Содержимое | CommCenter |
|---|---|---|---|
| `beta2-dyld/` | B2 (24B5089g) | 82 dyld cache файла | **строки только** (path + interfaces) |
| `beta3-system/` | B3 (24B5099f) | cryptex system DMG | не извлечён |
| `beta3-filesystem/` | B3 | filesystem DMG | не извлечён |
| `beta3-fs-decrypted/` | B3 | decrypted DMG | не извлечён |
| `extracted_v2/` | B2 | 11 dylibs | **нет CommCenter** |
| RC | 24B119 | только runtime логи | **нет бинаря** |

### 1.2. Найдено в dyld cache

- Строка пути `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` — в `.01` subcache.
- Launchd plist `com.apple.CommCenter.plist` — подтверждает path, user `_wireless`, `_LimitLoadToDeviceTree=baseband`, MachServices.
- `kCarrierBundle*` ключи — в `.07` subcache.
- `CarrierBundle*Interface` имена — в `.46` subcache.

**Но standalone Mach-O CommCenter не найден.**

## 2. Что можно установить по strings/plist

| Аспект | Подтверждено | Основание |
|---|---|---|
| Path | `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` | plist + strings |
| User | `_wireless` | plist `UserName` |
| Device tree | `baseband` | plist `_LimitLoadToDeviceTree` |
| Mach services | 18 сервисов включая `commcenter.carrierspace.xpc`, `commcenter.coretelephony.xpc`, `commcenter.mobile-helper-cbupdateservice` | plist `MachServices` |
| CarrierBundle interfaces | 13+ имен в `.46` | strings |
| SIM identifiers | `kSubscriberImsi`, `kSubscriberMcc`, `kSubscriberMnc`, `kSubscriberIccid`, `GID1`, `GID2`, `SIM2GID1`, `SIM2GID2` | strings `.07` |
| Carrier bundle API | `kCarrierBundlePathForBundle`, `copyCarrierBundleValue` | strings `.07` |

## 3. Что НЕ установлено

- Mach-O header, UUID, size CommCenter
- Функции/методы CommCenter
- Логика выбора bundle
- Обработка IMSI-симлинков
- Обработка SIM identifiers в коде (не только строках)
- Carrier bundle matching implementation
- IPCC install implementation на устройстве
- XPC authorization checks
- Реализация `CarrierBundleUtilities.dylib`

## 4. Почему CommCenter критичен

CommCenter — единственный компонент, который мог бы:

- выбирать bundle по IMSI/PLMN/GID;
- резолвить IMSI-симлинки в `/var/mobile/Library/Carrier Bundles/iPhone`;
- принимать carrier settings от IPCC/OTA;
- обрабатывать `SupportedSIMs` matching.

**Без CommCenter невозможно подтвердить:**
- сохранилась ли логика IMSI-алиасов на Beta 3/RC;
- существует ли internal API для прямого назначения bundle;
- какие методы `CarrierBundleInstallInterface`/`MatchProxyInterface` реально делают.

## 5. Что нужно для восстановления CommCenter

1. **Полный dyld cache с `.dyldlinkedit`** — позволит извлечь CommCenter как Mach-O.
2. **Beta 3 dyld cache** — для проверки изменений B2→B3.
3. **RC dyld cache** — для проверки RC.
4. **Standalone CommCenter Mach-O** — из IPSW или cryptex с сохранённым `LINKEDIT`.

## 6. Проверка альтернативных путей

| Путь | Результат |
|---|---|
| `beta2-decrypted/141-56439-025.dmg` | системный DMG, не проверен на CommCenter standalone |
| `beta3-system/141-56439-039.dmg` | system DMG, не проверен |
| `beta3-fs-decrypted/141-56668-039.dmg` | filesystem DMG, не проверен |

**Проверка DMG не выполнена** — требуется mount/extract для поиска `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter` как standalone файла.

## 7. Вывод

CommCenter **не извлечён** и недоступен для построчного анализа. Все выводы о его поведении — **INFERRED** по строкам, plist и runtime-логам. Это критическая граница Phase 14.

**Для Phase 15:** проверить system DMG на наличие standalone CommCenter, или получить полный dyld cache с `.dyldlinkedit` для извлечения.
