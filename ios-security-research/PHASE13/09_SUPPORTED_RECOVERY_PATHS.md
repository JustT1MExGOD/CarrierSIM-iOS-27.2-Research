# Фаза 13 — штатные механизмы восстановления

## 1. Проверенные workflow

### 1.1. Carrier settings update (IPCC install)

**Механизм**: `InstallationProxyService.install_from_local(ipcc)` → lockdownd `installation_proxy` → системный установщик.

**Может ли влиять на выбор bundle**: **КОСВЕННО** — только через `SupportedSIMs` внутри подписанного bundle. Триггерит rescan.

**Требует доверенного пакета**: **ДА** — IPCC должен быть Apple/carrier-signed (CMS).

**Поддерживает произвольную IMSI-привязку**: **НЕТ** — `SupportedSIMs` содержит только MCCMNC-диапазоны (`\d{5,6}`), не произвольные 15-значные IMSI, заданные клиентом.

**Специальные полномочия**: paired lockdownd (доверенный компьютер), может быть заблокирован restrictions/MDM (`InstallProhibited`).

**Совместимость iOS 27.2+**: **РАБОТАЕТ** — CarrierSIM использует на Beta 2 и Beta 3 как rescan-триггер.

**Может ли назначить чужой bundle SIM**: **НЕТ** — IPCC устанавливает свой собственный bundle; не создаёт алиас к `/System/.../Vodafone_hu.bundle` для чужой SIM.

### 1.2. OTA carrier settings update

**Механизм**: CommCenter получает обновления от Apple OTA (`kCarrierBundleTriggerGetUpdatedCarrierBundle`).

**Может ли влиять на выбор bundle**: **ДА** — обновляет carrier.plist, может изменить matching rules.

**Требует доверенного пакета**: **ДА** — Apple OTA, подписанный.

**Поддерживает произвольную IMSI-привязку**: **НЕТ** — управляется Apple, не клиентом.

**Специальные полномочия**: нет (автоматически).

**Совместимость iOS 27.2+**: **РАБОТАЕТ** — штатный механизм.

**Может ли назначить чужой bundle SIM**: **НЕТ** — OTA обновляет существующие bundle, не создаёт кастомные привязки.

### 1.3. SIM/eSIM activation (CellularPlan)

**Механизм**: `CellularPlanDaemon.xpc` — провижининг eSIM-планов.

**Может ли влиять на выбор bundle**: **КОСВЕННО** — eSIM-план может нести свои carrier settings, но не файловые bundle.

**Требует доверенного пакета**: **ДА** — eSIM activation code / QR / carrier push.

**Поддерживает произвольную IMSI-привязку**: **НЕТ** — управляет eSIM-профилями, не filesystem-симлинками.

**Специальные полномочия**: eSIM entitlement (carrier-signed activation).

**Совместимость iOS 27.2+**: **РАБОТАЕТ**.

**Может ли назначить чужой bundle SIM**: **НЕТ** — eSIM-план определяет свои настройки, не алиас к чужому системному bundle.

### 1.4. Device management (MDM)

**Механизм**: `.mobileconfig` профили через MDM-сервер.

**Может ли влиять на выбор bundle**: **ОГРАНИЧЕННО** — может установить APN/cellular policy, но не произвольный bundle.

**Требует доверенного пакета**: **ДА** — enrolled device + signed profile.

**Поддерживает произвольную IMSI-привязку**: **НЕТ** — MDM не пишет в `/var/mobile/Library/Carrier Bundles`.

**Специальные полномочия**: MDM enrollment + admin rights.

**Совместимость iOS 27.2+**: **РАБОТАЕТ** для policy, не для filesystem-write.

**Может ли назначить чужой bundle SIM**: **НЕТ** — MDM управляет policy, не carrier catalog.

### 1.5. Обновление через Apple Devices / Finder

**Механизм**: iTunes/Finder carrier settings update (та же installation_proxy).

**Может ли влиять на выбор bundle**: **ДА** — то же, что IPCC install.

**Требует доверенного пакета**: **ДА** — Apple-signed IPCC.

**Поддерживает произвольную IMSI-привязку**: **НЕТ**.

**Специальные полномочия**: paired device.

**Совместимость iOS 27.2+**: **РАБОТАЕТ**.

**Может ли назначить чужой bundle SIM**: **НЕТ**.

### 1.6. Регистрация уже установленного carrier bundle

**Механизм**: **не существует публичного API**. `kCarrierBundleTriggerInstallCarrierBundle` устанавливает IPCC, не регистрирует существующий системный bundle.

**Может ли влиять на выбор bundle**: **НЕТ** — нет API для «выбрать Vodafone_hu для этой SIM».

**Требует доверенного пакета**: н/д.

**Поддерживает произвольную IMSI-привязку**: **НЕТ**.

**Специальные полномочия**: internal CommCenter (не доступен).

**Совместимость iOS 27.2+**: н/д.

**Может ли назначить чужой bundle SIM**: **НЕТ**.

## 2. Альтернативные внутренние механизмы (не публичные)

### 2.1. IMSI-симлинк через файловую запись

**Исторический CarrierSIM**: запись 15-значного симлинка в `/var/mobile/Library/Carrier Bundles/iPhone` через AirTraffic-move.

**Статус на iOS 27.2 Beta 3/RC**: **ЗАБЛОКИРОВАНО** — dirfd-confined move (ENOTCAPABLE 107).

**Это не «штатный» механизм**, а злоупотребление dataclass-синхронизацией — закрыто Apple.

### 2.2. Direct CommCenter XPC (`commcenter.carrierspace.xpc`, `commcenter.coretelephony.xpc`)

**Механизм**: internal XPC для carrier config.

**Доступность**: **entitlement-gated**, не доступен сторонним процессам без специальных прав.

**Может ли влиять на выбор bundle**: **ПРЕДПОЛОЖИТЕЛЬНО ДА** (это CommCenter API).

**Поддерживает произвольную IMSI-привязку**: **НЕИЗВЕСТНО** (нет дизасма).

**Совместимость**: entitlement-gated.

**Может ли назначить чужой bundle SIM**: **НЕИЗВЕСТНО** — если да, то требует entitlement, не доступного host-клиенту.

## 3. Итоговая таблица

| Workflow | Может назначить чужой bundle SIM | Требует доверенного пакета | Поддерживает IMSI-привязку | Совместимость 27.2+ | Статус |
|---|---|---|---|---|---|
| IPCC install | НЕТ | ДА | НЕТ | РАБОТАЕТ | NOT SUPPORTED FOR GOAL |
| OTA update | НЕТ | ДА | НЕТ | РАБОТАЕТ | NOT SUPPORTED FOR GOAL |
| eSIM activation | НЕТ | ДА | НЕТ | РАБОТАЕТ | NOT SUPPORTED FOR GOAL |
| MDM | НЕТ | ДА | НЕТ | РАБОТАЕТ | NOT SUPPORTED FOR GOAL |
| IMSI-симлинк (CarrierSIM) | ДА (исторически) | НЕТ | ДА | **ЗАБЛОКИРОВАН** | RULED OUT (Beta 3+) |
| CommCenter XPC | НЕИЗВЕСТНО | entitlement | НЕИЗВЕСТНО | entitlement-gated | NOT ESTABLISHED |

## 4. Вывод

**Нет подтверждённого штатного механизма** для назначения SIM уже установленного Apple carrier bundle другого оператора на iOS 27.2 Beta 3+.

Все доступные штатные пути (IPCC, OTA, eSIM, MDM) либо устанавливают свой собственный bundle (с фиксированным `SupportedSIMs`), либо управляют политикой на уровне выше, но **не создают произвольную привязку IMSI→чужой системный bundle**.

Единственный исторический механизм (IMSI-симлинк через AirTraffic-write) — **заблокирован** на уровне файловой системы.
