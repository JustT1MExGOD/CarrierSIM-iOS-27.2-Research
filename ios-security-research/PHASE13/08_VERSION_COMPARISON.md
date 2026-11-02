# Фаза 13 — сравнение iOS 27.2 Beta 2, Beta 3 и RC

## 1. Матрица компонентов

| Компонент | Beta 2 (24B5089g) | Beta 3 (24B5099f) | RC (24B119) | Изменение | Уверенность |
|---|---|---|---|---|---|
| **AirTraffic.framework** | `__text` 0x18bf0, NSFileManager-move | `__text` 0x18d68 (+0x178), dirfd-confined move | НЕ извлечён | **РЕГРЕССИЯ**: NSFileManager → open+mkdirat+renameatx_np | HIGH (код) |
| **atc** | uuid `C5B4B497…`, 126 diff bytes | uuid `CA2F88E5…`, подпись/build-строки | НЕ извлечён | минимально (rebuild) | HIGH |
| **amfid** | uuid `3E6D3282…`, 2601 diff bytes | uuid `CFB0C004…`, подпись/CDHash | НЕ извлечён | минимально (rebuild) | HIGH |
| **installd** | uuid `5D0437D3…`, 945168 B | uuid `F54A48D1…`, 961888 B (+16KB) | НЕ извлечён | пересборка, нет carrier-bundle изменений | HIGH |
| **CommCenter** | НЕ извлечён | НЕ извлечён | НЕ извлечён | НЕИЗВЕСТНО | — |
| **CoreTelephony** | НЕ извлечён | НЕ извлечён | НЕ извлечён | НЕИЗВЕСТНО | — |
| **installation_proxy** | НЕ извлечён | НЕ извлечён | НЕ извлечён | НЕИЗВЕСТНО | — |
| **streaming_zip_conduit** | НЕ извлечён | НЕ извлечён | НЕ извлечён | НЕИЗВЕСТНО | — |

## 2. Ключевое изменение: AirTraffic move-рутина

### Beta 2 → Beta 3 (подтверждено)

| Аспект | Beta 2 | Beta 3 | Основание |
|---|---|---|---|
| Move-операция | `NSFileManager` BOOL call + `tbz` | `open(O_DIRECTORY\|0x40000000)` → `mkdirat` → `renameatx_np(RENAME_NOFOLLOW)` → `unlinkat` | AIRLOCK_FINAL_PATCH_ANALYSIS, syscalls по сигнатурам |
| Boundary test | строковая валидация `Cannot move asset outside of AFC root` | dirfd-relative resolution + kernel capability | код + errno 107 |
| `beneath AFC root` | absent | 3 occurrences в `__text` | grep B3-only strings |
| errno sites | 7 | 12 (+5 в одной области) | построечный diff |
| `__text` size | 0x18bf0 | 0x18d68 | binary diff |
| Ошибка | generic `tbz` | `Failed to move ... beneath AFC root, error: %{errno}d` | B3 __text string |
| `..` escape | allowed (symlink-id обходил string-check) | refused (dirfd+kernel) | runtime: asset 1 → ENOTCAPABLE 107 |

**Адреса (B3)**: `0x254c9e284` (open), `0x254c9e3e4` (mkdirat), `0x254c9e4e4` (renameatx_np), `0x254c9e524` (unlinkat), `0x254c9e558` (renameatx_np retry). Stub symbols не разрешены (пустой `.dyldlinkedit`), идентифицированы по сигнатуре.

### Beta 3 → RC (подтверждено runtime)

- **Идентичное поведение**: RC device.log содержит ту же строку `Failed to move completed file for asset ... beneath AFC root, error: [107: Capabilities insufficient]`.
- RC-бинарь AirTraffic **не извлечён** — подтверждение только runtime, не diff.

## 3. Изменения в IPCC Installer / CommCenter / CoreTelephony

**Не установлены.** Бинарники не извлечены; нет построечного diff.

Известно только:
- IPCC install работает на всех версиях (CarrierSIM использует `install_from_local` на Beta 2 и Beta 3).
- CommCenter plist идентичен (MachServices те же).
- CoreTelephony строки присутствуют в B2 cache; аналогичные ожидаются в B3 (не проверено).

## 4. Изменения файловых полномочий

- **atc**: user `mobile` на B2 и B3, jailed в `/var/mobile/Media`. Не изменилось.
- **AirTraffic**: sandbox-политика ужесточена — dirfd-confined move (ENOTCAPABLE 107 на RC).
- **streaming_zip_conduit**: user `mobile`, Media-jail. Не изменилось.

## 5. Изменения обработки carrier bundle

- **installd**: `Ignoring unsupported carrier bundle` присутствует на B2 и B3 в `_bundleInDirectory` — это про **embedded app bundles**, не carrier settings. Нет изменений в обработке carrier bundles.
- **CommCenter**: не доступен для сравнения.

## 6. Изменения в AirTraffic (обобщение)

| Изменение | Beta 2 | Beta 3 | Влияние на CarrierSIM |
|---|---|---|---|
| Move-операция | NSFileManager | dirfd-confined syscalls | **КРИТИЧЕСКОЕ**: блокирует `../`-traversal в `/var/mobile/Library` |
| Error handling | generic | errno-specific + retry | диагностика точнее |
| Boundary | string-check | kernel-capability | **КРИТИЧЕСКОЕ**: ENOTCAPABLE 107 для `/var/mobile/Library` |
| `__text` | 0x18bf0 | 0x18d68 | +0x178 новый код |

## 7. Что не установлено

- Изменился ли CommCenter между сборками (нет бинарей).
- Изменилась ли логика выбора bundle (нет CommCenter-кода).
- Изменился ли IPCC-installer (нет implementation).
- Добавлены ли новые проверки IMSI-алиасов (нет CommCenter-кода).

## 8. Вывод

Подтверждённое изменение **только одно**: AirTraffic move-рутина переписана с NSFileManager на dirfd-confined syscalls (open+mkdirat+renameatx_np). Это закрывает `../`-traversal из `/var/mobile/Media` в `/var/mobile/Library` — именно то, на чём строился CarrierSIM. RC подтверждает то же поведение runtime.

Все остальные компоненты (CommCenter, CoreTelephony, IPCC-installer) **не доступны для сравнения** — нет бинарей в выборке.
