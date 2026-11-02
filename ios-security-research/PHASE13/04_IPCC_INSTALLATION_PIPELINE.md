# Фаза 13 — цепочка установки IPCC

## 1. Что известно статически

IPCC (iPhone Carrier Configuration) — подписанный Apple пакет операторских настроек. CarrierSIM вызывает его через `InstallationProxyService.install_from_local(path)` — pymobiledevice3 client → lockdownd-сервис `installation_proxy`. Сам демон, обрабатывающий `.ipcc`, **не извлечён** из образов (нет отдельного бинаря в выборке; реализация внутри CommCenter/CoreTelephony-подсистемы или выделенного helper'а).

## 2. Статически восстановимая цепочка

```
[Host: carrier.py install_trigger]
   └─ pymobiledevice3 InstallationProxyService.install_from_local(ipcc)
        └─ lockdownd service 'installation_proxy'  (Mach/bootstrap gated)
             └─ _upload_ipcc: распаковка ZIP → AFC upload в staging-путь
                  └─ device-side daemon получает staged .ipcc
                       └─ верификация подписи Apple/carrier (CMS)
                            └─ CommCenter пересканирование carrier bundles
                                 └─ применение carrier.plist к SIM по правилам matching
```

Подтверждено: `_upload_ipcc` в carrier.py:862-869 распаковывает ZIP IPCC и через AFC создаёт `dst/<entry>` (makedirs + set_file_contents). Это **host-side upload staging**, не сама установка.

## 3. Что делает штатный установщик (по строкам/семантике)

### 3.1. Кто получает пакет
`installation_proxy` (lockdownd) → staging через AFC → установочный демон. Точный бинарь установщика не идентифицирован; кандидаты: CommCenter-helper (`commcenter.mobile-helper-cbupdateservice`) или `cbupdateservice`.

### 3.2. Определение формата
`.ipcc` = ZIP с `Payload/<name>.bundle/` содержащим `Info.plist`, `carrier.plist`, `signatures/*`. `check_trigger` (carrier.py:835) валидирует: ровно один `.bundle`, `SupportedSIMs` формат, симлинки с 5-6-значными MCCMNC-именами.

### 3.3. Проверки подлинности
IPCC подписан (CMS-обёртка). Устройство отвергает неподписанный/подделанный IPCC. Точная реализация верификации — внутри установочного демона (не извлечён). **CarrierSIM использует только Apple-signed IPCC** (`AVEA_tr.ipcc`, `Swisscom_ch.ipcc`, `O2_Germany.ipcc`) — самоподписанные не принимаются.

### 3.4. Что может устанавливаться
- carrier.plist (операторские параметры: APN, IMS, VoLTE, VoWiFi);
- carrier bundle в пользовательский каталог;
- записи `SupportedSIMs` → сопоставление PLMN/IMSI-диапазонов к bundle.

### 3.5. Куда устанавливается
Пользовательский каталог `/var/mobile/Library/Carrier Bundles/iPhone` (и/или приватное хранилище carrier settings). Точный путь записи — в установщике (не извлечён).

### 3.6. Разрешённые операции с ФС
Установщик может писать в carrier-catalog (это его назначение), **но только в рамках валидного подписанного IPCC** — он не является general-purpose file-writer. Нет доказательств, что IPCC может создать произвольный 15-значный IMSI-симлинк по команде клиента: записи каталога формируются из `SupportedSIMs` внутри подписанного bundle, а не из host-заданного имени.

### 3.7. Ошибки
`InstallProhibited` (наблюдается в carrier.py:877) — гейтинг по restrictions/MDM. Другие — внутри демона.

### 3.8. Действия после установки
CommCenter пересканирует каталог и применяет обновлённые настройки к затронутым SIM (rescan). Именно это CarrierSIM использует как «триггер» после записи своего IMSI-симлинка.

## 4. Может ли штатный IPCC выполнить нужную операцию?

| Операция | Возможно через IPCC? | Основание |
|---|---|---|
| Установить новый carrier bundle | ДА (если подписан Apple) | IPCC = bundle installer по назначению |
| Обновить существующий bundle | ДА | то же |
| Обновить таблицу сопоставления SIM (SupportedSIMs) | КОСВЕННО — только теми MCCMNC-диапазонами, что зашиты в подписанный bundle | `SupportedSIMs` внутри bundle определяет matching; host не задаёт имя записи |
| Создать произвольный 15-значный IMSI-симлинк | **НЕТ доказательств** | IPCC mapping идёт по `SupportedSIMs` (MCCMNC-формат `\d{5,6}`), не по произвольному 15-значному IMSI, заданному клиентом |
| Выбрать уже установленный СИСТЕМНЫЙ bundle другого оператора | **НЕТ** | IPCC устанавливает свой собственный bundle; он не создаёт алиас к `/System/Library/Carrier Bundles/<other>` для чужой SIM |

## 5. Техническая способность vs право клиента

- **Способность демона** писать в carrier-catalog: есть (это его роль).
- **Право клиента** инициировать запись **произвольной** записи: нет — клиент передаёт только готовый подписанный IPCC; содержимое (включая SupportedSIMs) фиксировано подписью Apple.

## 6. Вывод

Штатный IPCC — **не механизм для создания произвольного IMSI-алиаса к чужому системному bundle**. Он устанавливает свой собственный подписанный bundle и его `SupportedSIMs`-сопоставление. Он не может: (а) назначить `/System/.../Vodafone_hu.bundle` чужой SIM, (б) создать host-заданный 15-значный симлинк. Для цели CarrierSIM IPCC годится только как rescan-триггер, не как носитель привязки.
