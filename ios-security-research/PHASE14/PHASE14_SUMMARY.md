# Фаза 14 — итоговый отчёт: CarrierBundle Framework, Interfaces & CommCenter

## 1. Executive Summary

Phase 14 выполнила систематический анализ CarrierBundle framework, интерфейсов и CommCenter на iOS 27.2 Beta 2, Beta 3 и RC.

**Главный результат:** все `CarrierBundle*Interface` имена — только строки в `.46` subcache Beta 2 dyld cache. Реализация, методы и авторизация **не восстановлены** из-за отсутствующего `.79.dyldlinkedit` и `.symbols`.

**CommCenter не извлечён** — это критическая граница. Все выводы о его поведении — **INFERRED** по строкам, plist и runtime-логам.

**Единственное подтверждённое изменение B2→B3:** AirTraffic move-рутина переписана с NSFileManager на dirfd-confined syscalls → блокирует `../`-traversal → CarrierSIM не может создать IMSI-симлинк.

## 2. Новые подтверждённые факты

### 2.1. CarrierBundle interface inventory (строковый слой)

В `.46` subcache B2 dyld cache найдены 13+ имен интерфейсов:

```
CarrierBundleInstallInterface      CarrierBundleLockdownInterface
CarrierBundleMatchProxyInterface   CarrierBundleManagerInterface
CarrierBundleServerInterface       CarrierBundleCacheInterface
CarrierBundleDownloaderInterface   CarrierBundleFactoryInterface
CarrierBundleXMLCacheInterface     CarrierBundleBOMCopierInterface
ActivationCarrierBundleInterface   CarrierBundleUpdateInterface
CTXPCCarrierBundleNotificationInterface
```

В `.07` subcache — ключи carrier bundle API:
```
kCarrierBundlePathForBundle          kCarrierBundleTriggerInstallCarrierBundle
kCarrierBundleTriggerGetUpdatedCarrierBundle
kCarrierBundleTriggerResetCarrierBundle
kCarrierBundleWatchBundleMatchCriteria
copyCarrierBundleValue / WithDefault
```

В `.07` — SIM identifiers:
```
kSubscriberImsi  kSubscriberMcc  kSubscriberMnc  kSubscriberIccid
GID1  GID2  SIM2GID1  SIM2GID2  InternationalMobileSubscriberIdentity2
```

### 2.2. `/usr/lib/CarrierBundleUtilities.dylib`

Строка пути найдена в main cache metadata и `.73` subcache. Это **path evidence** — подтверждает существование компонента, но не его реализацию.

### 2.3. CommCenter launchd plist

Подтверждены:
- path: `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter`
- user: `_wireless`
- `_LimitLoadToDeviceTree=baseband`
- 18 Mach services включая `commcenter.carrierspace.xpc`, `commcenter.coretelephony.xpc`, `commcenter.mobile-helper-cbupdateservice`

## 3. Реальные реализации CarrierBundle API

### 3.1. `installation_proxy` (lockdownd)

**Подтверждено работающим** на B2/B3 (CarrierSIM использует):
- `install_from_local(ipcc)` — staging + установка
- `SupportedSIMs` — MCCMNC-формат (`\d{5,6}`), не произвольный IMSI
- Требует paired device + `InstallProhibited` check

**Не может:** создать произвольный IMSI-алиас, назначить чужой bundle другой SIM.

### 3.2. `streaming_zip_conduit` (lockdownd)

**Подтверждено работающим:**
- `MediaSubdir` + ZIP stream → upload в `/var/mobile/Media`
- Media-jail only — не пишет в `/var/mobile/Library`

### 3.3. `copyCarrierBundleValue` (CoreTelephony)

**Подтверждено как клиентский API:**
- `copyCarrierBundleValue` / `WithDefault` — чтение ключей из выбранного bundle
- Не доказано связь с `CarrierBundleCacheInterface`

### 3.4. `CarrierBundle*Interface` — строки, не реализации

Ни один из 13+ интерфейсов не имеет:
- Mach-O реализации
- метода/селектора
- проверки полномочий
- клиентского вызова

## 4. Доступность интерфейсов

| Интерфейс | Тип | Доступ | Доказательство |
|---|---|---|---|
| `installation_proxy` | lockdownd | paired device | `carrier.py:859` — работает |
| `streaming_zip_conduit` | lockdownd | paired device | `carrier.py:662` — работает |
| `com.apple.atc` | lockdownd | paired device | `airtraffic_native.py:248` — работает |
| `CarrierBundle*Interface` | internal CommCenter | entitlement-gated | **нет доступа** |

## 5. Архитектура выбора bundle

```
SIM identity (IMSI, MCC, MNC, GID1, GID2, ICCID, SPN)
    → Subscriber info (CoreTelephony reads SIM)
        → Carrier matching (CommCenter: IMSI-алиас > MCCMNC > GID > fallback)
            → Bundle lookup (kCarrierBundlePathForBundle, резолв симлинка)
                → Trust checks (UNKNOWN — нет CommCenter-кода)
                    → Bundle selection (CommCenter выбирает активный bundle)
                        → Settings application (carrier.plist → baseband/UI)
```

**UNKNOWN-переход:** проверки подписи и entitlement в CommCenter — нет кода.

## 6. Результаты анализа CommCenter

### 6.1. Что подтверждено

- Path: `/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter`
- User: `_wireless`, `_LimitLoadToDeviceTree=baseband`
- 18 Mach services в plist
- CarrierBundle interfaces в `.46` subcache
- SIM identifiers в `.07` subcache

### 6.2. Что НЕ подтверждено

- Mach-O header, UUID, size
- Методы, функции, call graph
- Логика выбора bundle
- Обработка IMSI-симлинков
- XPC authorization checks
- Реализация `CarrierBundleUtilities.dylib`

### 6.3. Критическая граница

CommCenter — единственный компонент, который мог бы:
- резолвить IMSI-симлинки;
- выбирать bundle по SIM-идентификаторам;
- обрабатывать `SupportedSIMs` matching;
- управлять carrier settings.

**Без CommCenter невозможно подтвердить ни одну из этих функций.**

## 7. Различия версий iOS

| Компонент | B2→B3 | B3→RC | Критичность |
|---|---|---|---|
| AirTraffic | NSFileManager → dirfd-confined | идентично | **КРИТИЧЕСКОЕ** |
| atc | rebuild | — | минимально |
| amfid | rebuild | — | минимально |
| installd | rebuild | — | минимально |
| CommCenter | **НЕИЗВЕСТНО** | **НЕИЗВЕСТНО** | **НЕИЗВЕСТНО** |
| CoreTelephony | **НЕИЗВЕСТНО** | **НЕИЗВЕСТНО** | **НЕИЗВЕСТНО** |

## 8. Проверка шести гипотез

| Гипотеза | Статус | Ключевое ограничение |
|---|---|---|
| H14-01: штатный интерфейс IMSI-привязки | INSUFFICIENT EVIDENCE | нет реализации `InstallInterface` |
| H14-02: интерфейс выбора bundle | INSUFFICIENT EVIDENCE | нет методов `MatchProxy` |
| H14-03: `MatchProxy` изменяет сопоставление | INSUFFICIENT EVIDENCE | `Proxy` ≠ `Override` |
| H14-04: `LockdownInterface` для paired device | INSUFFICIENT EVIDENCE | нет lockdown-доступа |
| H14-05: IMSI-симлинк на RC | SUPPORTED BUT INCOMPLETE | CommCenter не извлечён |
| H14-06: VoWiFi без замены bundle | RULED OUT | IMS-учётка от SIM A |

## 9. Возможные поддерживаемые пути восстановления

### 9.1. Пути, которые НЕ работают

| Путь | Причина |
|---|---|
| AirTraffic/Airlift | dirfd-confined move, ENOTCAPABLE 107 |
| streaming_zip_conduit | Media-jail only |
| installation_proxy IPCC | только `SupportedSIMs` (MCCMNC), не произвольный IMSI |
| CommCenter XPC | entitlement-gated, не доступен обычному клиенту |

### 9.2. Пути, требующие новых данных

| Путь | Что нужно |
|---|---|
| CommCenter-код | извлечённый Mach-O с `.dyldlinkedit` |
| `CarrierBundleUtilities.dylib` | standalone Mach-O или full cache |
| IPCC installer | implementation на устройстве |
| CommCenter XPC | interface definitions + authorization |

## 10. Нерешённые вопросы

1. **CommCenter Mach-O** — критический пробел; без него логика выбора bundle, IMSI-алиасы и matching rules неизвестны.
2. **`CarrierBundleUtilities.dylib`** — только path string; реализация, экспорты и роль неизвестны.
3. **`CarrierBundle*Interface` методы** — только имена; неизвестно, что они делают и кто их вызывает.
4. **RC-бинарники** — отсутствуют; все RC-выводы по runtime.
5. **Логика IMSI-алиасов на B3/RC** — не проверяема без возможности создать симлинк.
6. **Альтернативные пути записи в `/var/mobile/Library`** — другие демоны могут существовать, но не обнаружены.

## 11. Рекомендация для Phase 15

### Направления для закрытия

1. **AirTraffic/Airlift** — закрыт (dirfd-confined move).
2. **streaming_zip_conduit** — закрыт (Media-jail).
3. **installation_proxy IPCC** — закрыт для цели (только MCCMNC, не IMSI-алиас).
4. **CommCenter XPC как клиентский API** — закрыт (entitlement-gated, не доступен).

### Направления, требующие новых данных

5. **CommCenter Mach-O** — приоритет 1. Требуется:
   - полный dyld cache с `.dyldlinkedit`;
   - или standalone Mach-O из IPSW/cryptex;
   - для проверки логики IMSI-алиасов, matching rules, XPC surface.

6. **`CarrierBundleUtilities.dylib`** — приоритет 2. Требуется:
   - standalone Mach-O;
   - для понимания `SupportedSIMs`, matching implementation.

7. **IPCC installer implementation** — приоритет 3. Требуется:
   - бинарь, обрабатывающий `.ipcc` на устройстве;
   - для понимания, что происходит после `install_from_local`.

8. **Другие демоны с записью в `/var/mobile/Library`** — приоритет 4. Требуется:
   - инвентаризация всех system daemons с доступом к Library;
   - `fileproviderd`, `backupd`, `profiled`, `mediaserverd` — проверка прав.

### Что можно проверить (низкоприоритетное)

9. **Beta 3 system DMG** — проверить, содержит ли он standalone CommCenter (не только dyld cache).
10. **RC dyld cache** — если доступен, сравнить с B2/B3.

---

## Ответы на пять ключевых вопросов

### Q1. Можно ли подтвердить, что iOS 27.2 RC продолжает распознавать IMSI-симлинки?

**НЕТ.** CommCenter не извлечён; нет способа создать симлинк для проверки; логика могла измениться. Статус: **SUPPORTED BUT INCOMPLETE**.

### Q2. Существует ли подтверждённый штатный интерфейс изменения сопоставления SIM и carrier bundle?

**НЕТ.** `CarrierBundle*Interface` — только строки. `installation_proxy` — только IPCC с `SupportedSIMs` (MCCMNC), не произвольный IMSI. Статус: **INSUFFICIENT EVIDENCE**.

### Q3. Доступен ли такой интерфейс непривилегированному клиенту или доверенному компьютеру?

**НЕТ.** Все `CarrierBundle*Interface` — internal CommCenter API, entitlement-gated. Paired device имеет доступ к `installation_proxy` и `streaming_zip_conduit`, но это не `CarrierBundle*Interface`. Статус: **INSUFFICIENT EVIDENCE**.

### Q4. Может ли он назначить SIM уже установленный Apple bundle другого оператора?

**НЕТ.** Нет доказательств, что любой интерфейс позволяет произвольную привязку IMSI→чужой bundle. `installation_proxy` устанавливает свой bundle с фиксированным `SupportedSIMs`. Статус: **NOT SUPPORTED BY AVAILABLE EVIDENCE**.

### Q5. Какие конкретные доказательства необходимы для перехода к практической проверке?

1. **CommCenter Mach-O** с `.dyldlinkedit` — для дизасма логики выбора bundle, IMSI-алиасов, matching rules.
2. **`CarrierBundleUtilities.dylib`** — для понимания `SupportedSIMs`, matching implementation.
3. **IPCC installer implementation** — для понимания, что происходит после `install_from_local`.
4. **CommCenter XPC interface definitions** — для понимания, какие методы доступны и требуют ли entitlement.
5. **Список system daemons с записью в `/var/mobile/Library`** — для поиска альтернативного файлового пути.
6. **Runtime-тест** (вне рамок static-only) — для проверки, принимает ли CommCenter IMSI-алиас на RC.

---

**Финальный статус:** **НЕТ ПОДТВЕРЖДЁННОГО МЕХАНИЗМА** для назначения SIM уже установленного Apple carrier bundle другого оператора на iOS 27.2 Beta 3+.

**Критическая граница:** CommCenter не извлечён. Все CarrierBundle interfaces — строки, не реализации. Гипотезы — `INSUFFICIENT EVIDENCE` или `RULED OUT`.

**Методология:** статический офлайн-анализ, без устройства, без IPC, без фаззинга, без эксплойтов. Все выводы маркированы уровнем уверенности.
