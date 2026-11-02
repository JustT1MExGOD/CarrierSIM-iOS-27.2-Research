# Фаза 14 — проверка гипотез восстановления

## H14-01: Существует штатный интерфейс установки, способный изменить IMSI-привязку

| Аспект | Оценка |
|---|---|
| Подтверждающие | `installation_proxy` устанавливает IPCC; `CarrierBundleInstallInterface` найден как строка; `kCarrierBundleTriggerInstallCarrierBundle` — ключ в `.07` |
| Противоречащие | `SupportedSIMs` = MCCMNC-формат, не произвольный IMSI; IPCC устанавливает свой bundle, не алиас; `CarrierBundleInstallInterface` — только строка, не реализация |
| Недостающие | реализация `CarrierBundleInstallInterface`; доказательство, что он может создать IMSI-алиас |
| **Статус** | **INSUFFICIENT EVIDENCE** |
| Следующий шаг | извлечь `CarrierBundleUtilities.dylib` или CommCenter Mach-O |

## H14-02: Существует поддерживаемый интерфейс выбора уже установленного bundle

| Аспект | Оценка |
|---|---|
| Подтверждающие | `kCarrierBundlePathForBundle`, `copyCarrierBundleValue`, `CarrierBundleCacheInterface` — строки API; `CarrierBundleMatchProxyInterface` — строка matching interface |
| Противоречащие | нет доказательств, что интерфейс позволяет «выбрать» bundle произвольно; matching — это lookup, не override |
| Недостающие | методы `MatchProxyInterface`; доказательство, что lookup может изменить результат |
| **Статус** | **INSUFFICIENT EVIDENCE** |
| Следующий шаг | проверить, есть ли методы `setBundleForIMSI` или `overrideMatch` в CommCenter |

## H14-03: `CarrierBundleMatchProxyInterface` предоставляет механизм изменения сопоставления

| Аспект | Оценка |
|---|---|
| Подтверждающие | имя `MatchProxy` в `.46`; `kCarrierBundleWatchBundleMatchCriteria` — matching criteria |
| Противоречащие | `Proxy` не означает `override`; нет методов; нет доказательств, что он изменяет, а не только читает |
| Недостающие | реализация; список методов; доказательство write-доступа |
| **Статус** | **INSUFFICIENT EVIDENCE** |
| Следующий шаг | извлечь CommCenter, найти методы `MatchProxy` |

## H14-04: `CarrierBundleLockdownInterface` обеспечивает разрешённое управление carrier settings

| Аспект | Оценка |
|---|---|
| Подтверждающие | имя `Lockdown` в `.46`; `installation_proxy` — lockdownd service; paired device имеет доступ к `streaming_zip_conduit`, `atc` |
| Противоречащие | `installation_proxy` ≠ `CarrierBundleLockdownInterface`; paired device не имеет прав на произвольные операции; `Lockdown` — только имя |
| Недостающие | реализация `LockdownInterface`; доказательство, что он доступен через lockdownd и позволяет carrier settings |
| **Статус** | **INSUFFICIENT EVIDENCE** |
| Следующий шаг | проверить, зарегистрирован ли `CarrierBundleLockdownInterface` как lockdownd service |

## H14-05: Исторический IMSI-симлинк продолжает распознаваться CommCenter на RC

| Аспект | Оценка |
|---|---|
| Подтверждающие | `kSubscriberImsi`, `InternationalMobileSubscriberIdentity` — строки `.07`; каталог `/var/mobile/Library/Carrier Bundles/iPhone` существует; IPCC-rescan работает |
| Противоречащие | нет способа создать симлинк на B3/RC для проверки; CommCenter не извлечён; логика могла измениться |
| Недостающие | CommCenter-код; runtime-тест с созданным симлинком |
| **Статус** | **SUPPORTED BUT INCOMPLETE** |
| Следующий шаг | получить CommCenter Mach-O для дизасма |

## H14-06: Существует документированный способ достичь нужной конфигурации VoWiFi без замены bundle

| Аспект | Оценка |
|---|---|
| Подтверждающие | carrier.plist может включать IMS/VoWiFi-флаги; MDM может устанавливать cellular APN; eSIM может нести свои настройки |
| Противоречащие | VoWiFi требует IMS-регистрации на операторе A; SIM A не имеет учётных данных для bundle B; MDM не пишет в carrier catalog |
| Недостающие | способ изменить IMS-учётные данные или ePDG-адрес для чужого bundle |
| **Статус** | **RULED OUT** (для цели CarrierSIM) |
| Следующий шаг | проверить, поддерживает ли MDM произвольную IMS-конфигурацию (нет доказательств) |

## Итоговая таблица

| Гипотеза | Статус | Ключевое ограничение |
|---|---|---|
| H14-01: штатный интерфейс установки IMSI-привязки | INSUFFICIENT EVIDENCE | нет реализации `CarrierBundleInstallInterface` |
| H14-02: интерфейс выбора установленного bundle | INSUFFICIENT EVIDENCE | нет методов `MatchProxyInterface` |
| H14-03: `MatchProxy` изменяет сопоставление | INSUFFICIENT EVIDENCE | `Proxy` ≠ `Override`; нет write-методов |
| H14-04: `LockdownInterface` разрешён для paired device | INSUFFICIENT EVIDENCE | нет доказательства lockdown-доступа |
| H14-05: IMSI-симлинк распознаётся на RC | SUPPORTED BUT INCOMPLETE | CommCenter не извлечён |
| H14-06: VoWiFi без замены bundle | RULED OUT | IMS-учётка от SIM A, не bundle B |

## Общий вывод

**Ни одна гипотеза не подтверждена.** Все интерфейсы — строковые имена без реализации. CommCenter — критический компонент, который не извлечён.

Для подтверждения любой гипотезы требуется:
1. CommCenter Mach-O с `.dyldlinkedit`;
2. `CarrierBundleUtilities.dylib`;
3. IPCC installer implementation;
4. CommCenter XPC interface definitions.

Без этих данных все гипотезы остаются `INSUFFICIENT EVIDENCE` или `RULED OUT`.
