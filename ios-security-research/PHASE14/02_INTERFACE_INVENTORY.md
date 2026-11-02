# Фаза 14 — каталог интерфейсов CarrierBundle

## 1. Источник строк

Основной источник имён интерфейсов:

`C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\dyld_shared_cache_arm64e.46`

Дополнительные carrier-related строки находятся в subcache `.07`, `.32`, `.73`, main cache metadata и `.atlas`. Отдельный Mach-O с реализацией не найден.

## 2. Таблица

| Interface | Binary | Type | Implementation | Methods | Access Checks | Confidence |
|---|---|---|---|---|---|---|
| `CarrierBundleInstallInterface` | B2 dyld cache `.46` | строка, похожая на имя IPC/XPC interface | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleLockdownInterface` | B2 dyld cache `.46` | строка, похожая на IPC/XPC interface | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleMatchProxyInterface` | B2 dyld cache `.46` | строка, похожая на IPC/XPC interface | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleManagerInterface` | B2 dyld cache `.46` | строка | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleServerInterface` | B2 dyld cache `.46` | строка | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleCacheInterface` | B2 dyld cache `.46` | строка | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `CarrierBundleDownloaderInterface` | B2 dyld cache `.46` | строка | не восстановлена | не восстановлены | не восстановлены | **LOW — string only** |
| `/usr/lib/CarrierBundleUtilities.dylib` | B2 cache metadata / строки | путь к image или dependency | Mach-O не найден | не восстановлены | не восстановлены | **LOW — path string** |

## 3. Почему это не реализация

В строковом слое отсутствуют подтверждённые:

- `LC_UUID` соответствующего образа;
- Mach-O header и load commands;
- ObjC class list, protocol list или method list, привязанные к этим именам;
- XPC listener/resume/`NSXPCInterface` call site;
- entitlement validation перед конкретным методом;
- возвратные значения и обработка ошибок.

Имена с суффиксом `Interface` могут происходить из Objective-C metadata, Swift metadata, сериализованного XPC surface или диагностических строк. По одному имени тип нельзя установить надёжно.

## 4. Подтверждённые связанные элементы

В том же локальном B2 cache найдены клиентские ключи:

- `kCarrierBundlePathForBundle`;
- `kCarrierBundleTriggerInstallCarrierBundle`;
- `kCarrierBundleTriggerGetUpdatedCarrierBundle`;
- `kCarrierBundleTriggerResetCarrierBundle`;
- `kCarrierBundleTriggerRemoteRestoreToDefault`;
- `kCarrierBundleWatchBundleMatchCriteria`;
- `copyCarrierBundleValue`;
- `copyCarrierBundleValueWithDefault`.

Они подтверждают наличие carrier-bundle vocabulary/API surface, но не связь с перечисленными интерфейсами и не возможность произвольного override.

## 5. Доступ и полномочия

Прямых проверок полномочий для этих интерфейсов в доступном коде нет. Из launchd plist CommCenter подтверждены Mach services:

- `com.apple.commcenter.carrierspace.xpc`;
- `com.apple.commcenter.coretelephony.xpc`;
- `com.apple.commcenter.mobile-helper-cbupdateservice`;
- `com.apple.commcenter.xpc`;
- `com.apple.CellularPlanDaemon.xpc`.

Наличие service name не показывает, кто может подключиться или какие методы разрешены.

## 6. Вывод

Интерфейсы существуют как строковые названия в B2 cache. Реализация, методы и authorization boundary не восстановлены. Ни один интерфейс не может быть классифицирован как штатный способ изменения IMSI-привязки.
