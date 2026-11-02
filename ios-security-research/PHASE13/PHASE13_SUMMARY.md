# Фаза 13 — итоговый отчёт: CarrierSIM Recovery, IPCC & CommCenter Bundle Selection

## 1. Точная реконструкция CarrierSIM

CarrierSIM — это **не установщик IPCC**, а механизм создания **IMSI-симлинка** в пользовательском каталоге операторов `/var/mobile/Library/Carrier Bundles/iPhone`, заставляющий CommCenter выбрать чужой системный bundle для данной SIM.

**Архитектура**:
```
carrier.py → читает IMSI через lockdownd (CarrierBundleInfoArray)
  → выбирает bundle из bundle.yaml (MCCMNC → Vodafone_hu/ro)
  → формирует желаемое дерево каталога с 15-значным IMSI-симлинком
  → staging через streaming_zip_conduit (ZIP → /var/mobile/Media)
  → три Book-asset через AirTraffic (atc):
      asset 0: staging-симлинк → /var/mobile/Library/Carrier Bundles
      asset 1: ЭКСПОРТ текущего каталога → airlift-saved-*  (ЗАБЛОКИРОВАН на B3/RC)
      asset 2: ЗАПИСЬ желаемого дерева → /var/mobile/Library/Carrier Bundles/iPhone
  → install_trigger: install_from_local(ipcc) → CommCenter rescan
  → CommCenter видит IMSI-алиас → выбирает чужой bundle → commcenter.log
```

**Ключевой механизм**: 15-значный IMSI-симлинк `<IMSI> -> /System/Library/Carrier Bundles/iPhone/<B>.bundle` имеет приоритет над MCCMNC-записями при выборе bundle в CommCenter.

## 2. Необходимые условия для восстановления

Для эквивалентного результата (назначить SIM оператора A bundle оператора B) необходимо:

1. **Создать IMSI-алиас** в `/var/mobile/Library/Carrier Bundles/iPhone` — запись в защищённый каталог.
2. **Заставить CommCenter пересканировать** каталог (IPCC install, rescan-триггер).
3. **CommCenter выбирает** IMSI-алиас приоритетно → применяет настройки чужого bundle.

**Единственное критическое условие**: возможность записать файловый симлинк в `/var/mobile/Library/Carrier Bundles/iPhone`.

## 3. Архитектура IPCC Installer

**Путь**: `installation_proxy` (lockdownd) → системный компонент (не извлечён; кандидаты: cbupdateservice/CommCenter-helper).

**Границы**:
- Требует **paired lockdownd** (доверенный компьютер).
- IPCC должен быть **Apple/carrier-signed** (CMS).
- Устанавливает **свой собственный bundle**, не алиас к системному.
- `SupportedSIMs` внутри bundle определяет matching — **только MCCMNC-диапазоны** (`\d{5,6}`), не произвольные IMSI.
- **Не создаёт** host-заданные 15-значные симлинки.

**Что может**: установить/обновить carrier bundle, триггерить rescan, применить `SupportedSIMs` matching.

**Что НЕ может**: назначить `/System/.../Vodafone_hu.bundle` чужой SIM, создать произвольный IMSI-алиас, выбрать уже установленный системный bundle другого оператора.

## 4. Архитектура выбора bundle в CommCenter

**CommCenter не извлечён** — анализ по строкам/ключам CoreTelephony и launchd plist.

**Идентификаторы** (по приоритету, inferred):
1. **IMSI** (15-значный) — `kSubscriberImsi`, `InternationalMobileSubscriberIdentity`, `IMSIOverride`
2. **MCCMNC** (5-6-значный) — `kSubscriberMcc`, `kSubscriberMnc`, `kSubscriberLastKnownMcc`
3. **GID1/GID2** — `GID1`, `GID2`, `SIM2GID1`, `SIM2GID2`
4. **ICCID** — `kSubscriberIccid`
5. **eSIM/fizicheskaya** — `kSubscriberIsEsim`, `kSubscriberSimTrayStatus`

**API-ключи**: `kCarrierBundlePathForBundle`, `kCarrierBundleTriggerInstallCarrierBundle`, `kCarrierBundleWatchBundleMatchCriteria`, `copyCarrierBundleValue`.

Дополнительные строки dyld-cache показывают внутреннюю поверхность `CarrierBundleInstallInterface`, `CarrierBundleLockdownInterface`, `CarrierBundleMatchProxyInterface`, `CarrierBundleDownloaderInterface`, `CarrierBundleManagerInterface` и `/usr/lib/CarrierBundleUtilities.dylib`. Это подтверждает существование внутренних компонентов установки/сопоставления, но не раскрывает их авторизацию или возможность прямого выбора чужого bundle.

**Предполагаемая логика**: IMSI-алиас > MCCMNC > GID > fallback. Пользовательский каталог (`/var`) имеет приоритет над системным (`/System`).

**Не доказано**: точный порядок, обработка GID, наличие internal API для прямого назначения.

## 5. Состояние IMSI-симлинков на iOS 27.2

**Логика разрешения** (CommCenter):
- **Скорее всего сохранилась** — API `kSubscriberImsi`, каталог существует, IPCC-rescan работает.
- **Прямое доказательство отсутствует** (нет CommCenter-бинаря).
- **Практическая применимость заблокирована**: запись симлинка в каталог невозможна на Beta 3/RC.

**Механизм записи** (AirTraffic):
- **Beta 2**: NSFileManager-move допускал `../`-traversal → IMSI-алиас создавался.
- **Beta 3/RC**: dirfd-confined move (`open+mkdirat+renameatx_np(RENAME_NOFOLLOW)`) → `/var/mobile/Library` недоступно, ENOTCAPABLE 107.

**Вывод**: Даже если CommCenter всё ещё резолвит IMSI-алиасы, их **нельзя создать** через доступные каналы.

## 6. Изменения Beta 2 → Beta 3 → RC

| Компонент | Beta 2 | Beta 3 | RC | Изменение |
|---|---|---|---|---|
| **AirTraffic** | NSFileManager-move | dirfd-confined (`open+mkdirat+renameatx_np`) | runtime-подтверждено | **КРИТИЧЕСКОЕ**: блокирует `../`-traversal |
| **atc** | 126 diff bytes | rebuild | НЕ извлечён | минимально |
| **amfid** | 2601 diff bytes | rebuild | НЕ извлечён | минимально |
| **installd** | 945168 B | 961888 B (+16KB) | НЕ извлечён | пересборка, нет carrier-изменений |
| **CommCenter** | НЕ извлечён | НЕ извлечён | НЕ извлечён | **НЕИЗВЕСТНО** |
| **CoreTelephony** | НЕ извлечён | НЕ извлечён | НЕ извлечён | **НЕИЗВЕСТНО** |
| **IPCC installer** | НЕ извлечён | НЕ извлечён | НЕ извлечён | **НЕИЗВЕСТНО** |

**Единственное подтверждённое изменение**: AirTraffic move-рутина переписана (B2→B3), dirfd-confinement. RC подтверждает идентичное поведение runtime.

## 7. Проверенные штатные механизмы

| Механизм | Может назначить чужой bundle | Требует доверенного пакета | IMSI-привязка | Статус |
|---|---|---|---|---|
| IPCC install | **НЕТ** | ДА | **НЕТ** | NOT SUPPORTED FOR GOAL |
| OTA update | **НЕТ** | ДА | **НЕТ** | NOT SUPPORTED FOR GOAL |
| eSIM activation | **НЕТ** | ДА | **НЕТ** | NOT SUPPORTED FOR GOAL |
| MDM | **НЕТ** | ДА | **НЕТ** | NOT SUPPORTED FOR GOAL |
| IMSI-симлинк (CarrierSIM) | ДА (исторически) | НЕТ | ДА | **RULED OUT** (Beta 3+) |
| CommCenter XPC | **НЕИЗВЕСТНО** | entitlement | **НЕИЗВЕСТНО** | NOT ESTABLISHED |

## 8. Зависимости VoWiFi

**Выбор Vodafone_hu для Tele2_ru SIM НЕ даст рабочий VoWiFi**:

- Bundle определяет **UI-флаги** (показать toggle).
- IMS-регистрация идёт на **оператор A** (Tele2), не на bundle-оператора (Vodafone).
- Учётные данные IMS из **SIM A** — Vodafone_ePDG их не примет.
- VoWiFi требует network-side активации оператором A.

**Bundle B может включить VoWiFi-флаг в UI**, но реальная активация требует совпадения оператора bundle и SIM + поддержки IMS оператором + корректных учётных данных.

## 9. Нерешённые вопросы

1. **CommCenter не извлечён**: точная логика выбора bundle, приоритет IMSI-алиасов, наличие internal API — неизвестны.
2. **IPCC installer не извлечён**: точная обработка `SupportedSIMs`, создание записей в каталоге — неизвестны.
3. **RC-бинари отсутствуют**: все RC-выводы по runtime, не по коду.
4. **CommCenter XPC**: могут ли internal endpoints дать доступ к carrier config без entitlement — неизвестно.
5. **Логика IMSI-алиасов на Beta 3/RC**: сохранилась ли приоритетность — не проверено (нет способа создать тестовый симлинк).
6. **Альтернативные пути записи в `/var/mobile/Library`**: другие демоны/API могут существовать, но не обнаружены в доступных компонентах.

## 10. Рекомендация для Phase 14

### Направления для закрытия (не продолжать без новых данных)

1. **AirTraffic/Airlift-путь** — **ЗАКРЫТ**. Dirfd-confined move делает `../`-traversal невозможным на Beta 3/RC. Повторные попытки воспроизведут ENOTCAPABLE 107.
2. **streaming_zip_conduit как файл-райтер** — **ЗАКРЫТ**. Media-jail, нет доступа к `/var/mobile/Library`.
3. **Штатный IPCC как механизм привязки** — **ЗАКРЫТ**. IPCC не создаёт произвольные IMSI-алиасы; устанавливает свой bundle с фиксированным `SupportedSIMs`.

### Направления, требующие новых данных (не продолжать без них)

4. **CommCenter-код** — критический пробел. Требуется:
   - извлечённый CommCenter-бинарь (из IPSW с доступным `.dyldlinkedit`/`.symbols`);
   - или система с включённым CommCenter-debug для трассировки (вне рамок static-only).
5. **CommCenter XPC** — теоретический канал к carrier config, но:
   - требует дизасма для подтверждения;
   - entitlement-gated (недоступен без системных прав);
   - даже если доступен, не подтверждено, что позволяет произвольную IMSI-привязку.
6. **Другие демоны с записью в `/var/mobile/Library`** — если существуют (не обнаружены в выборке):
   - `fileproviderd`, `backupd`, `profiled`, другие system daemons могут иметь доступ;
   - но требуют подтверждения записи в carrier catalog.

### Что можно проверить (низкоприоритетное)

7. **Точная логика `SupportedSIMs` в IPCC** — если CommCenter обрабатывает их шире, чем MCCMNC (например, поддерживает wildcard или IMSI-диапазоны), это могло бы открыть путь. Требует CommCenter-кода.
8. **GID1/GID2 как альтернативные ключи** — если CommCenter принимает их как самостоятельные критерии (не только суффикс к MCCMNC), это могло бы дать более гибкую привязку. Требует CommCenter-кода.

### Приоритет Phase 14

**Нет высокоприоритетных безопасных направлений** для продолжения без новых данных (извлечённый CommCenter, доступ к системным API, или другие демоны с записью в Library).

Рекомендуется:
- **Не продолжать** попытки восстановить IMSI-симлинк через AirTraffic (закрыто).
- **Не продолжать** искать workaround в streaming_zip_conduit (Media-jail).
- **Сфокусироваться** на получении CommCenter-кода (из других IPSW, cryptex, или систем с доступным dyld) — это единственный путь к пониманию, сохранилась ли логика IMSI-алиасов и есть ли internal API.

---

## CarrierSIM Recovery Verdict

### Сохранилась ли логика IMSI-симлинков?

**Скорее всего ДА** (на уровне CommCenter), но **прямое доказательство отсутствует** (нет CommCenter-бинаря для дизасма). Строки `kSubscriberImsi`, `InternationalMobileSubscriberIdentity`, `IMSIOverride` присутствуют; каталог `/var/mobile/Library/Carrier Bundles/iPhone` существует и используется; IPCC-rescan работает.

Однако **практическая применимость заблокирована**: даже если CommCenter всё ещё резолвит IMSI-алиасы, их **нельзя создать** через доступные файловые операции на iOS 27.2 Beta 3+.

### Есть ли подтверждённый разрешённый способ создать такую привязку?

**НЕТ.**

- **Штатный IPCC** — не создаёт произвольные IMSI-алиасы (только `SupportedSIMs` = MCCMNC-диапазоны).
- **OTA update** — управляется Apple, не клиентом.
- **eSIM activation** — управляет eSIM-профилями, не filesystem-симлинками.
- **MDM** — policy-level, не carrier catalog.
- **AirTraffic/Airlift** — **заблокирован** (dirfd-confined move, ENOTCAPABLE 107).
- **CommCenter XPC** — **не установлен** (имена внутренних интерфейсов найдены, но нет дизасма, selector-ов и entitlement-анализа; вероятно entitlement-gated).

### Может ли штатный IPCC Installer выполнить необходимую операцию?

**НЕТ.**

IPCC Installer:
- устанавливает **свой собственный** подписанный bundle;
- `SupportedSIMs` содержит только MCCMNC-формат (`\d{5,6}`), не произвольные 15-значные IMSI;
- **не создаёт** алиас к `/System/Library/Carrier Bundles/<other>` для чужой SIM;
- **не выбирает** уже установленный системный bundle другого оператора.

IPCC годится только как **rescan-триггер** после записи симлинка другим способом, не как носитель привязки.

### Существует ли альтернативный способ выбрать системный bundle другого оператора?

**НЕТ ДОКАЗАТЕЛЬСТВ.**

- **Файловый симлинк** — единственный известный механизм; заблокирован.
- **CommCenter internal API** — теоретически возможно, но:
  - не подтверждено (нет кода);
  - вероятно entitlement-gated;
  - не доказано, что позволяет произвольную IMSI-привязку.
- **Другие демоны** — не обнаружены с доступом к `/var/mobile/Library/Carrier Bundles`.

### Какие доказательства необходимы для практической проверки?

Для проверки, сохранилась ли логика IMSI-алиасов и есть ли альтернативный путь:

1. **Извлечённый CommCenter-бинарь** (arm64e Mach-O с `.dyldlinkedit`/`.symbols`) — для дизасма логики выбора bundle, приоритета IMSI-алиасов, обработки симлинков.
2. **Извлечённый IPCC installer и `/usr/lib/CarrierBundleUtilities.dylib`** — для понимания обработки `SupportedSIMs` и создания записей в каталоге.
3. **CommCenter XPC surface** — для проверки, есть ли internal endpoint для carrier config (и требует ли entitlement).
4. **Список системных демонов с записью в `/var/mobile/Library`** — для поиска альтернативного файлового пути (если существует).
5. **Runtime-тест на Beta 3/RC** (вне рамок static-only) — для проверки, принимает ли CommCenter IMSI-алиас, если его создать через другой канал (например, jailbreak — вне рамок проекта).

### Какие направления следует закрыть?

**Закрыть (не продолжать без новых данных)**:

1. **AirTraffic/Airlift-путь** — dirfd-confined move закрывает `../`-traversal на Beta 3/RC. Повторные попытки воспроизведут ENOTCAPABLE 107.
2. **streaming_zip_conduit как файл-райтер** — Media-jail only.
3. **Штатный IPCC как носитель привязки** — не создаёт произвольные IMSI-алиасы.
4. **Поиск обхода Airlock-фикса** — это intentional security boundary, не bug.

**Приостановить (требуют новых данных)**:

5. **CommCenter-анализ** — критичен, но требует извлечённого бинаря.
6. **CommCenter XPC** — теоретический канал, но требует дизасма и подтверждения доступности.
7. **Другие демоны с записью в Library** — не обнаружены в выборке; требуют расширенной инвентаризации.

---

**Финальный статус**: **НЕТ ПОДТВЕРЖДЁННОГО МЕХАНИЗМА** для назначения SIM уже установленного Apple carrier bundle другого оператора на iOS 27.2 Beta 3+.

Это не означает невозможность — это означает отсутствие доказанного пути в доступных материалах. Отсутствие доказательств ≠ доказательство невозможности, но и не даёт рабочего решения.

**Методология**: статический офлайн-анализ, без устройства, без IPC, без фаззинга, без эксплойтов. Все выводы маркированы уровнем уверенности (HIGH/MEDIUM/INFERRED/INDIRECT).
