# Фаза 14 — независимый аудит доказательств

## 1. Проверка имён интерфейсов ≠ реализация

**Проверено:** все `CarrierBundle*Interface` имена — только строки в `.46` subcache.

| Имя | Строка найдена | Mach-O найден | Методы найдены | Авторизация найдена |
|---|---|---|---|---|
| `CarrierBundleInstallInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleLockdownInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleMatchProxyInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleManagerInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleServerInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleCacheInterface` | ✓ (.46) | ✗ | ✗ | ✗ |
| `CarrierBundleDownloaderInterface` | ✓ (.46) | ✗ | ✗ | ✗ |

**Вывод:** Ни одно имя не имеет подтверждённой реализации. Все статусы — `string only`.

## 2. Внутренние интерфейсы ≠ публичные

**Проверено:** `CarrierBundle*Interface` — внутренние CommCenter API, не lockdownd services.

- `installation_proxy` — lockdownd service (paired device).
- `streaming_zip_conduit` — lockdownd service (paired device).
- `com.apple.atc` — lockdownd service (paired device).
- `CarrierBundle*Interface` — internal CommCenter (не lockdownd service).

**Вывод:** Внутренние интерфейсы не доступны обычному клиенту. Даже если бы они были, отсутствует доказательство методов.

## 3. Права системного процесса ≠ права клиента

**Проверено:** CommCenter работает как `_wireless` с `_LimitLoadToDeviceTree=baseband`. Клиентские процессы (pymobiledevice3, iTunes) имеют другие права.

- CommCenter может читать `/var/mobile/Library/Carrier Bundles` — системный доступ.
- Клиент не может — sandbox ограничивает `/var/mobile/Media`.

**Вывод:** Наличие CommCenter с правами ≠ доступность для клиента.

## 4. Версии iOS не перепутаны

**Проверено:**
- B2 (24B5089g): AirTraffic `__text` 0x18bf0, NSFileManager move.
- B3 (24B5099f): AirTraffic `__text` 0x18d68, dirfd-confined move.
- RC (24B119): runtime-лог с `error: [107: Capabilities insufficient]`.

**Вывод:** Версии корректно разделены. RC только по runtime.

## 5. Неполный dyld cache ≠ полное доказательство

**Проверено:** `.79.dyldlinkedit` и `.symbols` — 0 байт.

- Возможно: строки, keys, paths, interfaces.
- Невозможно: импорты, экспорты, symbol tables, full Mach-O extraction, call graphs.

**Вывод:** Строки использованы корректно — как indicators, не как implementation.

## 6. Выбор bundle ≠ VoWiFi автоматически

**Проверено:** `Vodafone_hu.bundle` для `Tele2_ru` SIM:
- UI может показать VoWiFi toggle (bundle-флаг).
- IMS-регистрация идёт на оператора A (Tele2), не Vodafone.
- Учётные данные IMS из SIM A, не bundle B.

**Вывод:** Выбор bundle ≠ рабочий VoWiFi. Разделение корректное.

## 7. Гипотезы не объявлены подтверждёнными без трассировки

**Проверено:** все гипотезы H14-* оценены как `INSUFFICIENT EVIDENCE` или `RULED OUT`, не `CONFIRMED`.

- H14-01: `INSUFFICIENT EVIDENCE` — нет реализации `InstallInterface`.
- H14-02: `INSUFFICIENT EVIDENCE` — нет методов `MatchProxy`.
- H14-03: `INSUFFICIENT EVIDENCE` — `Proxy` ≠ `Override`.
- H14-04: `INSUFFICIENT EVIDENCE` — нет доказательства lockdown-доступа.
- H14-05: `SUPPORTED BUT INCOMPLETE` — CommCenter не извлечён.
- H14-06: `RULED OUT` — IMS-учётка от SIM A.

**Вывод:** Нет подтверждённых гипотез без трассировки кода.

## 8. Итоговый аудит

| Проверка | Результат | Основание |
|---|---|---|
| Имена интерфейсов = строки | ✓ | `.46` subcache, нет Mach-O |
| Внутренние ≠ публичные | ✓ | lockdownd vs internal |
| Права системы ≠ клиента | ✓ | `_wireless` vs `mobile` |
| Версии разделены | ✓ | B2/B3 diff, RC runtime |
| Неполный cache ≠ полное | ✓ | `.79.dyldlinkedit` = 0 |
| VoWiFi ≠ автоматически | ✓ | IMS-зависимости учтены |
| Гипотезы не подтверждены | ✓ | все `INSUFFICIENT`/`RULED OUT` |

**Общий вывод:** Доказательная база Phase 14 корректно маркирует уровни уверенности. Все интерфейсы — строки. CommCenter — критическая граница. Гипотезы — не подтверждены.
