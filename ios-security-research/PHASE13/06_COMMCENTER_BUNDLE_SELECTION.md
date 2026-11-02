# Фаза 13 — выбор carrier bundle в CommCenter

## 1. Доступность кода

**CommCenter не извлечён** как исполняемый образ (нет `.dyldlinkedit`/`.symbols`). Анализ основан на:
- launchd plist (`com.apple.CommCenter.plist`) — XPC services;
- строках CoreTelephony.framework из dyld subcache `.05` и `.07`;
- runtime syslog (CommCenter pid 106);
- известной семантике CoreTelephony API (по ключам).

Это **INDIRECT/INFERRED** доказательства, не построчный дизасм.

## 2. Идентификаторы, участвующие в выборе

| Идентификатор | Используется в | Статус | Основание |
|---|---|---|---|
| **IMSI** | `kSubscriberImsi`, `InternationalMobileSubscriberIdentity`, `IMSIOverride` | КЛЮЧЕВОЙ | Строки `.07`: `kSubscriberImsi`, `IMSIOverride`, `SIM2GID1`, `InternationalMobileSubscriberIdentity2` |
| **MCC** | `kSubscriberMcc`, `kSubscriberLastKnownMcc` | ДА | `kSubscriberMcc`, `kSubscriberLastKnownMcc`, `kSubscriberHomeCountryList` |
| **MNC** | `kSubscriberMnc` | ДА | `kSubscriberMnc` |
| **ICCID** | `kSubscriberIccid` | ДА | `kSubscriberIccid` |
| **GID1/GID2** | `GID1 = %@`, `GID2 = %@`, `SIM2GID1`, `SIM2GID2` | ДА | Строки `.07`: `GID1`, `GID2`, `SIM2GID1`, `SIM2GID2` — вторичные критерии matching |
| **SPN** | (косвенно, через subscriber info) | НЕ ПРЯМО | Нет отдельного `kSPN` ключа; SPN входит в carrier.plist matching rules |
| **PLMN/MCCMNC** | `Provider name using carrier bundle`, `kCarrierBundleWatchBundleMatchCriteria` | ДА | `kCarrierBundleWatchBundleMatchCriteria` — matching критерии watch/carrier |
| **eSIM vs physical** | `kSubscriberIsEsim`, `kSubscriberSimTrayStatus` | ДА | `kSubscriberIsEsim`, `kSubscriberSimTrayStatus` |

## 3. Обнаруженная внутренняя поверхность carrier bundle

В строках dyld-cache дополнительно найдены имена интерфейсов:

```text
CarrierBundleInstallInterface
CarrierBundleLockdownInterface
CarrierBundleMatchProxyInterface
CarrierBundleDownloaderInterface
CarrierBundleManagerInterface
CarrierBundleServerInterface
CarrierBundleFactoryInterface
CarrierBundleCacheInterface
/usr/lib/CarrierBundleUtilities.dylib
```

Это более сильное свидетельство, чем одиночная строка `kCarrierBundle*`: в образе присутствует именованная внутренняя поверхность установки, lockdown и matching. Но без извлечённого CommCenter/CarrierBundleUtilities нельзя определить методы, авторизацию и возможность прямого назначения bundle. Наличие интерфейса не равно доступности для обычного клиента.

## 4. API-ключи carrier bundle (из `.07`)

```
kCarrierBundlePathForBundle              → путь к bundle по имени/ID
kCarrierBundleTriggerInstallCarrierBundle → триггер установки (IPCC)
kCarrierBundleTriggerGetUpdatedCarrierBundle → OTA-обновление
kCarrierBundleTriggerResetCarrierBundle  → сброс к дефолту
kCarrierBundleTriggerRemoteRestoreToDefault → remote restore
kCarrierBundleWatchBundleMatchCriteria   → matching для watch
kCarrierBundleGetRemoteBundleInfo        → remote bundle info
kCarrierBundleGetAttachAPNSettings       → APN settings
kCarrierBundleModifyAttachAPNSettings    → модификация APN
kCarrierBundleOTAServerOverrideUrl       → OTA override URL
copyCarrierBundleValue / WithDefault     → чтение ключей из bundle
```

Это **клиентский API** (CoreTelephony.framework). Серверная часть — CommCenter.

## 5. Как (предположительно) работает выбор

По семантике CoreTelephony и структуре каталога:

1. CommCenter читает subscriber info: IMSI → MCC+MNC (+GID1/GID2, ICCID, SPN).
2. Ищет в `/var/mobile/Library/Carrier Bundles/iPhone` запись, соответствующую идентификатору:
   - **15-значный IMSI-алиас** — наивысший приоритет (точное совпадение);
   - **5-6-значный MCCMNC** — следующий приоритет;
   - **GID1/GID2-суффикс** — дополнительная детализация;
   - fallback — `Unknown.bundle` или дефолт.
3. Резолвит запись → системный `.bundle` → читает carrier.plist → применяет настройки.

**Подтверждение приоритета IMSI-алиаса**: CarrierSIM работал именно через создание 15-значного IMSI-симлинка — и он побеждал MCCMNC-записи (иначе механизм не имел бы смысла). Это runtime-подтверждённое поведение на ≤Beta 2.

## 6. Carrier bundle override / versioning

- `IMSIOverride` — строка в `.07`, предположительно debug/test override.
- `kCarrierBundleTriggerResetCarrierBundle` — сброс к дефолту.
- `International assist forced; overriding carrier bundle check` — логика override для международного assist.
- `copyCarrierBundleValueWithDefault` — fallback к дефолту при отсутствии ключа.

## 7. Пользовательский vs системный каталог

- `/System/Library/Carrier Bundles/iPhone` — read-only, Apple-signed.
- `/var/mobile/Library/Carrier Bundles/iPhone` — writable, содержит MCCMNC-ссылки и IMSI-алиасы.
- **Приоритет**: пользовательский каталог имеет приоритет над системным (стандартная iOS-семантика override). Подтверждено тем, что IMSI-алиас в `/var` побеждает системный MCCMNC.

## 8. Что НЕ доказано

- Точный порядок сравнения: IMSI → MCCMNC → GID → SPN vs другой.
- Обрабатывает ли CommCenter GID1/GID2 как отдельные критерии или как суффикс к MCCMNC.
- Существует ли internal API для прямого назначения bundle по IMSI (без файлового симлинка).
- Версия кода на RC — предположительно идентична Beta 3, но бинарь не доступен для сравнения.

## 9. Вывод

CommCenter выбирает bundle по иерархии идентификаторов: **IMSI (15-значный) > MCCMNC (5-6-значный) > GID1/GID2 > fallback**. Пользовательский каталог имеет приоритет над системным. IMSI-алиас — легитимный механизм приоритета, который CarrierSIM эксплуатировал. Точная реализация выбора — внутри CommCenter, не доступна для построчного анализа.
