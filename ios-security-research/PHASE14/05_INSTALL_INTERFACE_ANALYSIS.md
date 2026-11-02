# Фаза 14 — анализ `CarrierBundleInstallInterface`

## 1. Что известно о интерфейсе установки

`CarrierBundleInstallInterface` — строка в `.46` subcache B2 cache. Название указывает на интерфейс установки carrier bundle, но **не доказывает** что это публичный или клиентский API.

## 2. Что можно установить по CarrierSIM

Из `carrier.py:859-891` (`install_trigger`) видно, что установка IPCC происходит через:
- `pymobiledevice3.services.installation_proxy.InstallationProxyService`
- `install_from_local(path)` — где path = `.ipcc` файл

Внутренний процесс:
1. `_upload_ipcc` распаковывает ZIP через AFC staging
2. Файл записывается на устройство (staging путь)
3. `installation_proxy` lockdown-сервис обрабатывает файл
4. CommCenter получает сигнал о новом carrier bundle

**Это НЕ `CarrierBundleInstallInterface`** — это `installation_proxy` lockdownd interface. Разница критична:
- `installation_proxy` — lockdown service (paired device required)
- `CarrierBundleInstallInterface` — internal CommCenter API (entitlement-gated)

## 3. Что может установить штатный workflow

| Операция | Доступна | Доказательство |
|---|---|---|
| Установить новый IPCC с `SupportedSIMs` | ДА | `install_trigger` работает на B2/B3 |
| Обновить существующий bundle | ДА | тот же путь |
| Создать произвольный IMSI-алиас к чужому bundle | **НЕТ** | `SupportedSIMs` = MCCMNC-формат (`\d{5,6}`), не 15-значный IMSI |
| Назначить системный `Vodafone_hu.bundle` чужой SIM | **НЕТ** | IPCC устанавливает свой bundle, не алиас |
| Изменить сопоставление SIM→bundle без IPCC | **НЕТ** | нет API для этого |

## 4. Границы установки

| Аспект | Статус | Основание |
|---|---|---|
| Формат пакета | IPCC (ZIP с `Payload/*.bundle/`) | `check_trigger` (carrier.py:836) |
| Подпись пакета | Apple/CMS-signed | требуется `install_from_local` |
| Авторизация клиента | paired lockdownd + `InstallProhibited` check | `carrier.py:877` |
| Запись в carrier catalog | системный компонент (не клиент) | internal |
| Произвольное имя записи | **НЕТ** | `SupportedSIMs` зашито в bundle |
| Алиас к чужому bundle | **НЕТ** | IPCC = bundle installer, не alias creator |

## 5. `CarrierBundleInstallInterface` vs `installation_proxy`

| Аспект | `installation_proxy` | `CarrierBundleInstallInterface` |
|---|---|---|
| Тип | lockdownd service | внутренний CommCenter API |
| Доступ | paired computer (iTunes/pymobiledevice3) | internal only (entitlement-gated) |
| Формат входа | `.ipcc` файл | неизвестно (не извлечён) |
| Что делает | staging + делегирование системному компоненту | неизвестно |
| Может ли создать IMSI-алиас | нет | неизвестно |
| Доступен обычному клиенту | paired | вероятно нет |

## 6. Вывод

**Штатный IPCC workflow через `installation_proxy` работает на iOS 27.2** (подтверждено CarrierSIM), но **не решает задачу CarrierSIM**: он не создаёт произвольные IMSI-алиасы и не назначает чужой bundle другой SIM.

`CarrierBundleInstallInterface` — **внутренний интерфейс**, строка которого найдена, но реализация и полномочия не восстановлены. Нет доказательств, что он доступен обычному клиенту или может изменить сопоставление SIM→bundle без IPCC.

**Гипотеза H14-01** (существует штатный интерфейс изменения IMSI-привязки): **INSUFFICIENT EVIDENCE**.
