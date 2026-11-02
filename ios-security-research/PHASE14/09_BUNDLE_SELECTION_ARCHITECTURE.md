# Фаза 14 — архитектура выбора bundle

## 1. Обобщённая цепочка

```
[SIM identity] 
    → [Subscriber info: IMSI, MCC, MNC, GID1, GID2, ICCID, SPN]
        → [Carrier bundle matching: поиск записи в каталоге]
            → [Bundle lookup: резолв IMSI-алиас / MCCMNC / GID → системный .bundle]
                → [Trust checks: проверка подписи bundle, entitlement]
                    → [Bundle selection: выбор активного bundle для SIM]
                        → [Settings application: применение carrier.plist]
```

Каждый переход маркирован уровнем доказанности.

## 2. Детальный разбор

### 2.1. SIM identity → Subscriber info

| Аспект | Статус | Основание |
|---|---|---|
| Источник | SIM card / baseband | `kSubscriberImsi`, `kSubscriberMcc`, `kSubscriberMnc`, `kSubscriberIccid`, `GID1`, `GID2` |
| Чтение | `CoreTelephony.framework` | клиентский API |
| Хранение | CommCenter | владелец carrier state |

**Доказанность:** ПРЯМАЯ (строки + семантика CoreTelephony).

### 2.2. Subscriber info → Carrier bundle matching

| Аспект | Статус | Основание |
|---|---|---|
| Критерии | IMSI(15), MCCMNC(5-6), GID1/GID2 | `kSubscriberImsi`, `kSubscriberMcc`, `kSubscriberMnc`, `GID1`, `GID2`, `SIM2GID1`, `SIM2GID2` |
| Каталог | `/var/mobile/Library/Carrier Bundles/iPhone` + `/System/Library/Carrier Bundles/iPhone` | CarrierSIM + strings |
| Приоритет | IMSI-алиас > MCCMNC > GID > fallback | CarrierSIM runtime (≤B2) |
| Механизм | симлинк resolution | `p0/p1/p2/link → ../../../var/mobile/Library/Carrier Bundles` |

**Доказанность:** ЧАСТИЧНАЯ. Приоритет IMSI-алиаса — runtime-подтверждён на ≤B2; на B3/RC — INFERRED (нет записи симлинка для проверки).

### 2.3. Carrier bundle matching → Bundle lookup

| Аспект | Статус | Основание |
|---|---|---|
| Lookup | `kCarrierBundlePathForBundle`, `lookupOrCreateBundleForLibraryURL` | strings `.07` |
| Результат | путь к `.bundle` | `kCarrierBundlePathForBundle` |
| Кэш | `PSUICoreTelephonyCarrierBundleCache`, `copyCarrierBundleValue` | strings |
| Резолв | симлинк → системный bundle | CarrierSIM |

**Доказанность:** ЧАСТИЧНАЯ. Lookup-функции существуют как ключи, но реализация не извлечена.

### 2.4. Bundle lookup → Trust checks

| Аспект | Статус | Основание |
|---|---|---|
| Подпись bundle | Apple-signed системный bundle | семантика `/System/Library` |
| Проверка | предположительно при чтении carrier.plist | не подтверждено кодом |
| Entitlement | неизвестно | нет дизасма CommCenter |

**Доказанность:** НИЗКАЯ. Системные bundle Apple-signed, но механизм проверки в CommCenter не восстановлен.

### 2.5. Trust checks → Bundle selection

| Аспект | Статус | Основание |
|---|---|---|
| Выбор | CommCenter | владелец carrier config |
| Активный bundle | `CFBundleIdentifier` в `CarrierBundleInfoArray` | `carrier.py:765` |
| Уведомление | `carrierBundleChange:` | `PSUICoreTelephonyCarrierBundleCache` |

**Доказанность:** ЧАСТИЧНАЯ. CommCenter — владелец выбора, но код выбора не извлечён.

### 2.6. Bundle selection → Settings application

| Аспект | Статус | Основание |
|---|---|---|
| carrier.plist | параметры оператора | IPCC structure |
| Применение | CommCenter → baseband/UI | `Resetting baseband after pushing files` (`.32`) |
| Уведомление | `carrierBundleChange:` | strings |

**Доказанность:** ЧАСТИЧНАЯ. Применение подтверждено `commcenter.log` в CarrierSIM, но код не извлечён.

## 3. Состояние IMSI-симлинков

### 3.1. На Beta 2

| Аспект | Статус | Основание |
|---|---|---|
| Создание | AirTraffic NSFileManager move | допускает `../`-traversal |
| Резолв | CommCenter резолвит симлинк | runtime-подтверждено (CarrierSIM работал) |
| Приоритет | IMSI-алиас > MCCMNC | runtime-подтверждено |
| Применение | bundle применяется к SIM | commcenter.log подтверждает выбор |

### 3.2. На Beta 3 / RC

| Аспект | Статус | Основание |
|---|---|---|
| Создание | **ЗАБЛОКИРОВАНО** | dirfd-confined move → ENOTCAPABLE 107 |
| Резолв | **НЕ ПРОВЕРЕНО** | нет симлинка для проверки |
| Приоритет | **НЕ ПРОВЕРЕНО** | нет runtime-теста |
| Применение | **НЕ ПРОВЕРЕНО** | нет симлинка |

**Вывод:** IMSI-симлинк — корректный механизм на ≤B2, но на B3/RC его нельзя создать для проверки. Логика CommCenter может быть идентична, но без симлинка её не проверить.

## 4. Архитектура с метками UNKNOWN

```
[SIM identity] 
    → [Subscriber info]                    ПРЯМАЯ (строки + API)
        → [Carrier matching]              ЧАСТИЧНАЯ (каталог + runtime ≤B2)
            → [Bundle lookup]             ЧАСТИЧНАЯ (ключи + семантика)
                → [Trust checks]          UNKNOWN (нет кода CommCenter)
                    → [Bundle selection]  ЧАСТИЧНАЯ (plist + runtime)
                        → [Settings]      ЧАСТИЧНАЯ (commcenter.log)
```

**UNKNOWN-переход**: проверки подписи и entitlement в CommCenter — нет кода, нет дизасма, нет подтверждения.

## 5. Вывод

Архитектура выбора bundle — **частично восстановлена**. SIM identity → subscriber info → matching → lookup → selection → application подтверждены на уровне семантики и runtime-наблюдений. Точная реализация matching rules, приоритетов и trust checks — внутри CommCenter, не доступна.

Исторический IMSI-симлинк — **подтверждён на ≤B2**, **не проверяем на B3/RC** из-за блокировки записи.
