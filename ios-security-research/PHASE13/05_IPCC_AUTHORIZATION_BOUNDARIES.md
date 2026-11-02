# Фаза 13 — границы полномочий IPCC Installer

## 1. Модель «Клиент → сервис → авторизация → пакет → операция»

### installation_proxy (lockdownd)
```
host tool (pymobiledevice3/iTunes) 
  → lockdownd service 'installation_proxy' 
  → авторизация: lockdownd pairing (доверенный компьютер) + entitlement
  → пакет: .ipcc (Apple-signed, CMS)
  → операция: staging upload + делегирование установки системному компоненту
```
Граница: требуется **paired/dоверенный компьютер** (lockdownd trust). Не general API.

### streaming_zip_conduit (`/usr/libexec/streaming_zip_conduit`, user `mobile`)
```
host → lockdownd service 'com.apple.streaming_zip_conduit'
  → авторизация: lockdownd pairing
  → данные: MediaSubdir + сырой ZIP-поток
  → операция: распаковка в /var/mobile/Media/<subdir>  (Media-jail only!)
```
Граница: пишет **только в `/var/mobile/Media`** (AFC root). Не может писать в `/var/mobile/Library`. Это подтверждено тем, что CarrierSIM использует его именно для staging-симлинка в Media, а не для прямой записи в carrier catalog.

### Реальный установщик carrier settings (CommCenter-helper, не извлечён)
```
installation_proxy → системный компонент (cbupdateservice/CommCenter-helper)
  → авторизация: internal system call, entitlement-gated
  → пакет: подписанный IPCC
  → операция: распаковка bundle → запись в carrier catalog → rescan
```
Граница: работает от имени системы (`_wireless`/root-adjacent), доступен **только через** installation_proxy с валидным пакетом. Не принимает произвольные файловые операции от клиента.

## 2. Проверки вызывающего процесса

- `install_from_local` требует **paired device** — физическое подтверждение доверия на устройстве. Это не entitlement-check, а pairing trust.
- Дополнительно `InstallProhibited` (carrier.py:877): restrictions (Screen Time → «Установка приложений») или MDM-профиль могут запретить установку. Подтверждено в коде и логах.
- Внутренний установщик: entitlement-gated (не доступен сторонним процессам).

## 3. Проверки происхождения пакета

- IPCC должен быть **Apple/carrier-signed** (CMS). Неподписанный ZIP отвергается.
- `check_trigger` (carrier.py:845) отвергает `com.apple.Viva_kw` и триггеры, пересекающиеся с установленными SIM — это host-side валидация, не системная.
- Системная верификация подписи — внутри установщика (не извлечён).

## 4. Ограничения допустимых операций

| Операция | Доступна через installation_proxy? | Основание |
|---|---|---|
| Загрузить .ipcc на устройство | ДА | `_upload_ipcc` (carrier.py:862) — staging через AFC |
| Записать в `/var/mobile/Media` | ДА (через streaming_zip_conduit) | Media-jail |
| Записать в `/var/mobile/Library/Carrier Bundles` | **НЕТ напрямую** | только через подписанный IPCC + rescan; streaming_zip_conduit ограничен Media |
| Создать произвольный симлинк | **НЕТ** | IPCC-симлинки формируются из `SupportedSIMs` (MCCMNC-формат), не из host-имени |
| Выбрать системный bundle другого оператора | **НЕТ** | IPCC устанавливает свой bundle, не алиас к системному |

## 5. Обработка символических ссылок

- `staging_archive` создаёт симлинк `p0/p1/p2/link → ../../../var/mobile/Library/Carrier Bundles` — но это **внутри Media** (staging). Он не записывается в carrier catalog напрямую.
- IPCC-internal symlinks: `check_trigger` (850-854) валидирует, что все ссылки в IPCC имеют 5-6-значные имена (`\d{5,6}` = MCCMNC). 15-значные IMSI-алиасы в подписанных IPCC **не встречаются** — это подтверждённый факт из `bundle.yaml`/IPCC-структуры.

## 6. Вывод

Граница IPCC-установки строгая: **paired lockdownd → signed IPCC → системный установщик → запись только того, что зашито в bundle**. Нет канала для клиента задать произвольное имя записи или создать алиас к чужому системному bundle. Это делает IPCC непригодным для воспроизведения CarrierSIM-эффекта (привязка IMSI к чужому bundle).
