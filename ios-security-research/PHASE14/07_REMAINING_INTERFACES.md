# Фаза 14 — оставшиеся интерфейсы CarrierBundle

## 1. `CarrierBundleManagerInterface`

**Статус:** строка в `.46` subcache. Реализация не восстановлена.

**Предполагаемая роль** (по названию): управление установленными carrier bundles — registry, enumeration, lifecycle.

**Нет доказательств:**
- какие методы он предоставляет;
- может ли создавать записи в `/var/mobile/Library/Carrier Bundles`;
- связан ли с `CarrierBundleUtilities.dylib`;
- доступен ли клиентам.

## 2. `CarrierBundleServerInterface`

**Статус:** строка в `.46` subcache. Реализация не восстановлена.

**Предполагаемая роль**: серверная сторона CommCenter — обработка запросов от клиентов (CoreTelephony.framework).

**Нет доказательств:**
- какие запросы обрабатывает;
- есть ли отдельные read/write endpoints;
- проверяет ли полномочия клиента;
- связан ли с `com.apple.commcenter.carrierspace.xpc`.

## 3. `CarrierBundleCacheInterface`

**Статус:** строка в `.46` subcache. Реализация не восстановлена.

**Предполагаемая роль**: кэширование carrier bundle values для быстрого чтения (`copyCarrierBundleValue`).

**Нет доказательств:**
- какие ключи кэширует;
- write-through или read-through;
- инвалидация при изменении bundle;
- доступность для записи.

## 4. `CarrierBundleDownloaderInterface`

**Статус:** строка в `.46` subcache. Реализация не восстановлена.

**Предполагаемая роль**: загрузка carrier bundles OTA или от Apple (не IPCC — это отдельный механизм).

**Нет доказательств:**
- URL/endpoint для загрузки;
- формат пакета;
- верификация подписи;
- триггеры (периодический, on-demand, event-driven);
- различие от `kCarrierBundleTriggerGetUpdatedCarrierBundle`.

## 5. `CarrierBundleFactoryInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: фабрика объектов carrier bundle — создание/парсинг объектов `CarrierBundle` из путей/plists.

## 6. `CarrierBundleXMLCacheInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: кэш XML-представлений carrier plist — оптимизация чтения carrier.plist.

## 7. `CarrierBundleBOMCopierInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: копирование BOM (Bill of Materials) файлов между системой и кэшем — вероятно для fast-path чтения.

## 8. `ActivationCarrierBundleInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: активация carrier bundle — вероятно связано с первоначальной настройкой устройства или eSIM activation.

## 9. `CarrierBundleUpdateInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: обновление carrier bundles — вероятно связано с OTA update (`kCarrierBundleTriggerGetUpdatedCarrierBundle`).

## 10. `SubscriberSimInterface`, `SubscriberSimCommandDriverDelegateInterface`

**Статус:** строки в `.46` subcache.

**Предполагаемая роль**: интерфейс к SIM-карте — чтение IMSI, ICCID, GID, MCC/MNC. Это **не** carrier bundle management — это SIM card access layer.

## 11. `CTXPCCarrierBundleNotificationInterface`

**Статус:** строка в `.46` subcache.

**Предполагаемая роль**: XPC notification — уведомление других процессов об изменении carrier bundle.

## 12. Итоговая таблица

| Interface | Предполагаемая роль | Установка | Matching | Выбор | Уведомление | Доступность |
|---|---|---|---|---|---|---|
| `InstallInterface` | установка IPCC | ✓ | | | | ? |
| `LockdownInterface` | lockdown access | ? | ? | ? | | ? |
| `MatchProxyInterface` | matching proxy | | ✓ | ? | | ? |
| `ManagerInterface` | управление bundles | ✓ | | | | ? |
| `ServerInterface` | CommCenter server | ✓ | ✓ | ✓ | ✓ | ? |
| `CacheInterface` | кэш carrier values | | | | | ? |
| `DownloaderInterface` | OTA download | ✓ | | | | ? |
| `FactoryInterface` | создание объектов | | | | | ? |
| `XMLCacheInterface` | XML кэш | | | | | ? |
| `BOMCopierInterface` | BOM копирование | | | | | ? |
| `ActivationInterface` | активация | ✓ | | | | ? |
| `UpdateInterface` | OTA update | ✓ | | | | ? |
| `SubscriberSimInterface` | SIM access | | | | | ? |
| `NotificationInterface` | уведомления | | | | ✓ | ? |

**Все роли — INFERRED по названию.** Нет доказательств методов, полномочий или реализации.

## 13. Вывод

Все оставшиеся интерфейсы — **строковые имена в cache**. Их реальная функциональность, методы и доступность не установлены. Ни один не может быть подтверждён как способ изменения IMSI-привязки или выбора чужого bundle.
