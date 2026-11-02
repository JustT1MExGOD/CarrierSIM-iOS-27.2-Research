# Фаза 14 — анализ `CarrierBundleMatchProxyInterface`

## 1. Наблюдаемый факт

`CarrierBundleMatchProxyInterface` найден как строка в:

`C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\dyld_shared_cache_arm64e.46`

Отдельный класс, протокол или XPC definition не восстановлены.

## 2. Что можно установить

Название согласуется с компонентом, который может быть связан с передачей или проксированием carrier-bundle matching requests. Это только архитектурная гипотеза, **не доказанная роль**.

Нет доступных данных о:

- методах;
- параметрах;
- возвращаемых структурах;
- subscription context;
- MCC/MNC/IMSI/ICCID/GID handling;
- чтении или изменении результата matching;
- клиентских процессах.

## 3. Lookup, selection и override

| Возможность | Доказательство | Статус |
|---|---|---|
| Lookup подходящего bundle | имя `MatchProxyInterface` | только гипотеза |
| Selection активного bundle | нет call site и реализации | UNKNOWN |
| Override результата | слово `Proxy` не доказывает override | UNKNOWN |
| Чтение carrier values | `copyCarrierBundleValue` найден отдельно | косвенно подтверждено для CoreTelephony API |
| Изменение IMSI mapping | нет метода или записи в каталог | не установлено |

Особенно важно: `Proxy` может означать серверный proxy, transport wrapper, object proxy или IPC façade. Он не означает «override».

## 4. SIM identifiers

В cache отдельно присутствуют строки:

- `kSubscriberImsi`;
- `kSubscriberMcc`;
- `kSubscriberMnc`;
- `kSubscriberIccid`;
- `GID1`, `GID2`;
- `SIM2GID1`, `SIM2GID2`;
- `InternationalMobileSubscriberIdentity2`.

Однако нет связи между этими строками и `CarrierBundleMatchProxyInterface` на уровне вызова. Нельзя утверждать, что интерфейс принимает или возвращает любой из них.

## 5. Access boundary

Не найдены:

- `NSXPCInterface` creation, привязанное к этому имени;
- `listener:shouldAcceptNewConnection:` для этого интерфейса;
- entitlement string/check;
- bootstrap lookup policy;
- клиентский бинарник.

Launchd plist подтверждает CommCenter services, но не доступ к MatchProxy.

## 6. Вывод

`CarrierBundleMatchProxyInterface` — **строковое свидетельство внутренней поверхности**, не подтверждённый API выбора или override. H14-03 не подтверждается. Следующая проверка возможна только с полным CommCenter/CarrierBundleUtilities Mach-O или IPC metadata, содержащей реальные selectors и authorization checks.
