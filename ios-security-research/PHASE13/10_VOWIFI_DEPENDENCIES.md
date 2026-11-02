# Фаза 13 — зависимости VoWiFi

## 1. Разделённые уровни

**Отображение доступности Wi-Fi Calling** ≠ **возможность включить переключатель** ≠ **регистрация IMS** ≠ **успешный звонок через Wi-Fi**.

Каждый уровень имеет свои зависимости; выбор carrier bundle — только один из входов.

## 2. Что зависит от carrier bundle

| Параметр | Источник | Влияние |
|---|---|---|
| `carrier.plist` → `IMS`/`VoWiFi` flags | carrier bundle | Включает IMS/VoWiFi в логике CommCenter |
| `carrier.plist` → `AllowVoWiFi`, `WiFiCallingEnabled` | carrier bundle | Показывает переключатель в настройках |
| `carrier.plist` → `IMSDomain`, `PDN` | carrier bundle | IMS-регистрация parameters |
| `carrier.plist` → `Roaming`/`Emergency` rules | carrier bundle | Правила роуминга |
| `carrier.plist` → `SupportsEVS`, `SupportsVoLTE` | carrier bundle | Codec/features |

**Что делает bundle**: определяет, **какие возможности CommCenter сообщает системе и пользователю** для данного оператора.

## 3. Что НЕ зависит от carrier bundle

| Параметр | Источник | Влияние |
|---|---|---|
| IMS-регистрация на сети | **оператор A** (не B) | Оператор A решает, разрешать ли IMS |
| VoWiFi-разрешение на стороне сети | **оператор A** | Оператор A проверяет ePDG/IMS-учётку |
| SIM/eSIM-учётка | **оператор A** | Аутентификация идёт по SIM оператора A |
| Настройки устройства | пользователь | Wi-Fi Calling toggle, авиарежим |
| Сетевая регистрация | **оператор A** | PLMN-регистрация, roaming status |

## 4. Разложение сценария «SIM A + bundle B»

### Что произойдёт при выборе Vodafone_hu для SIM Tele2_ru

| Уровень | Результат | Почему |
|---|---|---|
| **Bundle selection** | CommCenter выберет `Vodafone_hu.bundle` | IMSI-алиас резолвится в системный bundle |
| **Settings display** | Покажет VoWiFi toggle (если Vodafone_hu включает его) | Bundle определяет UI |
| **IMS registration** | **НЕ произойдёт** | IMS-регистрация идёт на ePDG оператора A (Tele2_ru), который не выдаст Vodafone-учётку |
| **VoWiFi call** | **НЕ будет работать** | Нет IMS-регистрации → нет SIP-вызова |
| **VoLTE** | может работать (если bundle включает и оператор A поддерживает) | VoLTE — network-attach feature, не IMS-dependent |

## 5. Критические зависимости VoWiFi

```
[Выбор bundle B] 
  → [CommCenter: VoWiFi enabled flag = YES]
    → [UI: показать toggle]
      → [Пользователь: включить toggle]
        → [CommCenter: попытка IMS-регистрации]
          → [ePDG attach к оператору A]  ← ОПЕРАТОР A решает!
            → [IMS-учётка от оператора A]
              → [SIP-регистрация]
                → [VoWiFi работает]
```

**Bundle B может включить IMS/VoWiFi флаг, но не может изменить**:
- ePDG-адрес оператора A;
- учётные данные IMS оператора A;
- разрешение оператора A на IMS для этой SIM.

## 6. Что нужно для реальной работы VoWiFi

| Условие | Источник | Контролируется bundle? |
|---|---|---|
| Bundle включает VoWiFi | carrier bundle | ДА |
| Оператор A поддерживает IMS | network/operator | **НЕТ** |
| Оператор A разрешает VoWiFi | network/operator | **НЕТ** |
| ePDG доступен | operator A / internet | **НЕТ** |
| IMS credentials | SIM A / operator A | **НЕТ** |
| Device settings | user | **НЕТ** |
| Network registration | SIM A / operator A | **НЕТ** |

## 7. Вывод

**Выбор Vodafone_hu для Tele2_ru SIM НЕ даст рабочий VoWiFi**, потому что:

1. IMS-регистрация идёт на **оператор A** (Tele2), не на Vodafone.
2. Учётные данные IMS из **SIM A** (Tele2), а Vodafone_ePDG их не примет.
3. Оператор A решает, разрешать ли IMS/VoWiFi для данной SIM.

**Bundle может включить VoWiFi-флаг в UI**, но реальная активация требует:
- совпадения оператора bundle и SIM;
- поддержки IMS оператором;
- корректных учётных данных IMS.

CarrierSIM работал для **отображения настроек** (APN, иконки, некоторые флаги), но **не для IMS-функций**, требующих network-side активации оператором.
