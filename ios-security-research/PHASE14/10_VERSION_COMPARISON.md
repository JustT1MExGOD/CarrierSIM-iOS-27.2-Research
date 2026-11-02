# Фаза 14 — сравнение версий iOS 27.2

## 1. Методология сравнения

Сравнение B2↔B3 по бинарным diff, B3→RC по runtime-логам. RC-бинарники отсутствуют.

## 2. AirTraffic — КРИТИЧЕСКОЕ изменение

| Аспект | Beta 2 | Beta 3 | RC | Влияние |
|---|---|---|---|---|
| Move-рутина | NSFileManager BOOL | dirfd-confined syscalls | runtime-идентично B3 | **Блокирует `../`-traversal** |
| `__text` size | 0x18bf0 | 0x18d68 (+0x178) | — | новый код |
| errno sites | 7 | 12 (+5) | — | errno-specific handling |
| Boundary | string-check | kernel-capability | — | **КРИТИЧЕСКОЕ** |
| `beneath AFC root` | absent | 3 occurrences | — | новая логика |
| Ошибка | generic | ENOTCAPABLE 107 | — | диагностика точнее |

**Адреса B3**: `0x254c9e284` (open), `0x254c9e3e4` (mkdirat), `0x254c9e4e4` (renameatx_np), `0x254c9e524` (unlinkat), `0x254c9e558` (renameatx_np retry).

**Влияние на CarrierSIM:** КРИТИЧЕСКОЕ — закрывает `../`-traversal из `/var/mobile/Media` в `/var/mobile/Library`. CarrierSIM не может создать IMSI-симлинк.

## 3. atc — минимальное изменение

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| UUID | `C5B4B497…` | `CA2F88E5…` | — |
| Diff bytes | 126 | rebuild | — |
| User | `mobile` | `mobile` | — |
| Jail | `/var/mobile/Media` | `/var/mobile/Media` | — |

**Влияние:** минимально (rebuild, подпись/build-строки).

## 4. amfid — минимальное изменение

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| UUID | `3E6D3282…` | `CFB0C004…` | — |
| Diff bytes | 2601 | rebuild | — |

**Влияние:** минимально (подпись/CDHash).

## 5. installd — пересборка

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| UUID | `5D0437D3…` | `F54A48D1…` | — |
| Size | 945168 | 961888 (+16KB) | — |
| Carrier bundle | `Ignoring unsupported carrier bundle` | идентично | — |

**Влияние:** пересборка, нет carrier-изменений. Строка `Ignoring unsupported carrier bundle` относится к embedded app bundles, не carrier settings.

## 6. CommCenter — НЕИЗВЕСТНО

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| Mach-O | НЕ извлечён | НЕ извлечён | НЕ извлечён |
| plist | `com.apple.CommCenter` | идентичен? | — |
| MachServices | 18 сервисов | идентично? | — |

**Влияние:** НЕИЗВЕСТНО — нет бинарей для сравнения.

## 7. CoreTelephony — НЕИЗВЕСТНО

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| Mach-O | НЕ извлечён | НЕ извлечён | НЕ извлечён |
| Строки | `kCarrierBundle*` | идентично? | — |

**Влияние:** НЕИЗВЕСТНО — нет бинарей для сравнения.

## 8. IPCC installer — НЕИЗВЕСТНО

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| Mach-O | НЕ извлечён | НЕ извлечён | НЕ извлечён |
| installation_proxy | работает | работает | — |

**Влияние:** работает на всех версиях (подтверждено CarrierSIM), но реализация не извлечена.

## 9. Carrier bundle matching — НЕИЗВЕСТНО

| Аспект | Beta 2 | Beta 3 | RC |
|---|---|---|---|
| IMSI-алиас | работал | заблокирован | заблокирован |
| Логика CommCenter | работала | ? | ? |

**Влияние:** запись заблокирована; логика CommCenter не проверяема.

## 10. Итоговая таблица

| Компонент | B2→B3 изменение | B3→RC | Критичность для CarrierSIM |
|---|---|---|---|
| AirTraffic | NSFileManager → dirfd-confined | идентично | **КРИТИЧЕСКОЕ** |
| atc | rebuild | — | минимально |
| amfid | rebuild | — | минимально |
| installd | rebuild | — | минимально |
| CommCenter | НЕИЗВЕСТНО | НЕИЗВЕСТНО | **НЕИЗВЕСТНО** |
| CoreTelephony | НЕИЗВЕСТНО | НЕИЗВЕСТНО | **НЕИЗВЕСТНО** |
| IPCC installer | НЕИЗВЕСТНО | НЕИЗВЕСТНО | **НЕИЗВЕСТНО** |

## 11. Вывод

Единственное подтверждённое изменение — **AirTraffic move-рутина** переписана с NSFileManager на dirfd-confined syscalls (B2→B3). Это закрывает CarrierSIM-путь записи IMSI-симлинка.

Все остальные компоненты — CommCenter, CoreTelephony, IPCC installer — **не доступны для сравнения** из-за отсутствия бинарей.
