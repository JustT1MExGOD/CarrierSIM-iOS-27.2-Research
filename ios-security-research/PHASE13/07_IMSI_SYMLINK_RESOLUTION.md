# Фаза 13 — логика IMSI-симлинков

## 1. Доступность кода разрешения

**Код CommCenter, резолвящий IMSI-симлинки, не извлечён.** Анализ основан на:
- структуре каталога `/var/mobile/Library/Carrier Bundles/iPhone` (подтверждено device-логами и CarrierSIM);
- runtime-поведении (IMSI-алиасы работали на ≤Beta 2);
- строках CoreTelephony (`kSubscriberImsi`, `InternationalMobileSubscriberIdentity`, `IMSIOverride`).

## 2. Что известно о механизме

### 2.1. Каталоги просмотра

- **Пользовательский**: `/var/mobile/Library/Carrier Bundles/iPhone` — writable, содержит:
  - 15-значные IMSI-симлинки → `/System/Library/Carrier Bundles/iPhone/<X>.bundle`;
  - 5-6-значные MCCMNC-симлинки → аналогично;
  - вложенные каталоги `MCCMNC/` для дополнительных записей.
- **Системный**: `/System/Library/Carrier Bundles/iPhone` — read-only, Apple-signed `.bundle` файлы.

### 2.2. Имя записи

- 15-значное число = полный IMSI подписчика (`kSubscriberImsi` → `InternationalMobileSubscriberIdentity`).
- 5-6-значное = MCCMNC (PLMN-код).
- Формат подтверждён: `imsi_links` в CarrierSIM ищет `\d{15}`, `SupportedSIMs` в IPCC — `\d{5,6}`.

### 2.3. Обработка симлинков

CommCenter резолвит симлинк → читает `Info.plist`/`carrier.plist` из целевого `.bundle` → применяет настройки. Разрешение идёт через стандартный VFS (readlink). Точные проверки (например, `lstat` vs `stat`, `realpath`, проверка валидности целевого пути) — внутри CommCenter (не доступны).

### 2.4. Разрешение целевого пути

Симлинк вида `../../../../../../System/Library/Carrier Bundles/iPhone/Vodafone_hu.bundle` резолвится из `/var/mobile/Library/Carrier Bundles/iPhone/<IMSI>` в `/System/Library/Carrier Bundles/iPhone/Vodafone_hu.bundle`. Шесть `..` выводят из `/var/mobile/Library/Carrier Bundles/iPhone` в `/`, затем `System/Library/...` — read-only системный путь.

### 2.5. Проверки

Известные (по CarrierSIM):
- Целевое имя валидируется: `re.fullmatch(r'[A-Za-z0-9_]+\.bundle', name)` — только `[A-Za-z0-9_]` в имени bundle.
- IMSI-формат: `\d{15}`.
- Подпись целевого bundle: предположительно проверяется CommCenter (системный bundle Apple-signed), но код проверки не доступен.

### 2.6. Приоритет пользовательского каталога

**Подтверждено**: IMSI-алиас в `/var` имеет приоритет над системными MCCMNC-записями (иначе CarrierSIM не работал бы). Точный порядок: IMSI(15) > MCCMNC(5-6) > GID-суффикс > fallback.

### 2.7. Отсутствие записи

Fallback: `Unknown.bundle` или дефолтный carrier bundle для устройства (из `MobileEquipmentInfo` или hardcoded). Точный fallback — внутри CommCenter.

### 2.8. Несовместимый bundle

Если симлинк указывает на несуществующий `.bundle`: CommCenter падает обратно на fallback (предположительно). Подтверждения нет — CarrierSIM откатывал при `missing` в rescan-логе (carrier.py:2367).

## 3. Сохранилась ли логика на iOS 27.2 Beta 3 / RC?

### Что подтверждено

- Каталог `/var/mobile/Library/Carrier Bundles/iPhone` существует и используется (device.log, journal `target=/var/mobile/Library/Carrier Bundles/iPhone`).
- CommCenter обрабатывает IMSI-алиасы (API `kSubscriberImsi`, `InternationalMobileSubscriberIdentity` присутствуют в `.07`).
- IPCC-установка триггерит rescan (CarrierSIM использует `install_from_local` для этого).

### Что НЕ подтверждено

- Что 15-значный IMSI-алиас **всё ещё** имеет приоритет на Beta 3/RC (нет runtime-теста с успешной записью).
- Что CommCenter не добавил дополнительную валидацию (например, проверку подписи IMSI-симлинка или белый список допустимых bundle).

### Ключевое ограничение

**Даже если логика разрешения IMSI-симлинков сохранилась**, её нельзя использовать без **записи симлинка** в `/var/mobile/Library/Carrier Bundles/iPhone`. Запись туда — защищённая операция, которая на Beta 3/RC закрыта Airlock-фиксом (dirfd-confined move). Это делает вопрос о сохранении логики академическим для CarrierSIM: механизм записи закрыт, независимо от того, сохранилась ли логика чтения.

## 4. Вывод

Логика IMSI-симлинков **скорее всего сохранилась** (CommCenter обрабатывает IMSI-идентификаторы, каталог существует, IPCC-rescan работает). Однако:

- **Прямое доказательство отсутствует** (нет CommCenter-бинаря для дизасма).
- **Практическая применимость заблокирована**: запись симлинка в каталог на Beta 3/RC невозможна через известные каналы.

IMSI-симлинк остаётся корректным механизмом разрешения, но не достижимым через доступные файловые операции.
