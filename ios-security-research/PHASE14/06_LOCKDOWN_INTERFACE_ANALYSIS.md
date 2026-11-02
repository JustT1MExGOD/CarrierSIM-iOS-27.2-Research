# Фаза 14 — анализ `CarrierBundleLockdownInterface`

## 1. Название и контекст

`CarrierBundleLockdownInterface` — строка в `.46` subcache. Название указывает на связь с lockdown/lockdownd — доверенным компьютером (paired device).

## 2. Что такое lockdown-контекст

Lockdownd — системный демон, обрабатывающий pairing между iPhone и доверенным компьютером (iTunes/Finder/pymobiledevice3). Lockdownd services доступны только после successful pairing — физического подтверждения доверия на устройстве.

## 3. Что найдено в CarrierSIM

Из `carrier.py`:
- `start_lockdown_service('com.apple.streaming_zip_conduit')` — для staging ZIP upload
- `start_lockdown_service('com.apple.atc')` — для AirTraffic asset transfer
- `installation_proxy` — для IPCC install

Это **lockdown services**, доступные через paired device. Но это не `CarrierBundleLockdownInterface` — это отдельные сервисы.

## 4. `CarrierBundleLockdownInterface` vs lockdown services

| Аспект | `installation_proxy` (lockdownd) | `streaming_zip_conduit` | `CarrierBundleLockdownInterface` |
|---|---|---|---|
| Тип | lockdownd service | lockdownd service | internal CommCenter interface |
| Доступ | paired device | paired device | вероятно internal |
| Формат | `.ipcc` | ZIP stream | неизвестно |
| Роль | IPCC install entry | ZIP upload staging | управление carrier settings |
| IMSI-алиас | нет | нет (Media-jail) | неизвестно |

## 5. Что может lockdown-интерфейс

Если `CarrierBundleLockdownInterface` существует как lockdownd service, он мог бы:

- принимать carrier settings от paired device;
- применять обновления к carrier profile;
- выполнять reset/restore carrier settings.

Но **название не доказывает** что он:
- создаёт IMSI-алиасы;
- изменяет сопоставление SIM→bundle;
- доступен обычному paired device.

## 6. Доверенный компьютер ≠ произвольная операция

Даже если `CarrierBundleLockdownInterface` доступен через lockdownd:
- он может принимать только валидные, подписанные данные;
- он может ограничивать операции до чтения/установки, не override;
- он может требовать entitlement на устройстве.

**Pairing доверия ≠ право изменять защищённые carrier settings.**

## 7. Вывод

`CarrierBundleLockdownInterface` — **строковое свидетельство внутренней поверхности**, возможно связанной с lockdownd. Его роль, методы и доступность не установлены. Доверенный компьютер может иметь доступ к `installation_proxy` и `streaming_zip_conduit`, но это не доказывает доступ к `CarrierBundleLockdownInterface` или возможность изменить carrier settings произвольно.

**Гипотеза H14-04** (LockdownInterface обеспечивает разрешённое управление carrier settings): **INSUFFICIENT EVIDENCE**.
