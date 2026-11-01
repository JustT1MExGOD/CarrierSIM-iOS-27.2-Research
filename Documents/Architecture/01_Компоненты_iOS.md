# Компоненты iOS и зоны ответственности за carrier bundles

Carrier bundles — каталоги `.bundle` с операторскими настройками (APN, IMS/VoLTE/VoWiFi/VoNR,
переопределения, профили). Существуют две копии:

- системная, только для чтения: `/System/Library/Carrier Bundles/iPhone/*.bundle`;
- рабочая, изменяемая: `/var/mobile/Library/Carrier Bundles/iPhone/*` — именно её перемещал
  прежний механизм Airlift. **Высокая** (целевой путь зафиксирован в журнале запуска).

## Кто отвечает за каждую функцию

Подтверждено чтением `launchd`-определений из файловой системы Beta 3 (`24B5099f`), бинарными
строками `atc`/`installd`/`amfid` и журналом RC `24B119`.

| Компонент | Бинарник | Учётная запись | Роль по отношению к carrier bundles | Уверенность |
|---|---|---|---|---|
| `com.apple.CommCenter` | `CoreTelephony.framework/Support/CommCenter` | `_wireless` | Владелец операторской конфигурации: профиль, регистрация, выбор бандла. MachServices включают `carrierspace`, `coretelephony`, `mobile-helper-cbupdateservice`, `CellularPlanDaemon`, `basebandd`. | Высокая |
| `com.apple.mobile.installd` | `/usr/libexec/installd` | `_installd` | Официальный установщик приложений и IPCC/carrier bundles. MachService `com.apple.mobile.installd`. | Высокая |
| `com.apple.streaming_zip_conduit` | (launchd) | `mobile` | Канал потоковой загрузки ZIP; тот же путь, что CarrierSIM уже использует для триггера IPCC. | Высокая |
| `com.apple.atc` | `/usr/libexec/atc` | `mobile` | Демон **медиа-синхронизации** (Book/Photo и др.) для iTunes/Finder. Работает внутри `/var/mobile/Media`. Путь, злоупотребленный Airlift — не владелец carrier bundles. | Высокая |
| `com.apple.dataaccess.dataaccessd` | `DataAccess.framework/Support/dataaccessd` | `mobile` | Синхронизация аккаунтов (почта/контакты/календарь). К carrier bundles отношения не имеет. | Высокая |
| `com.apple.symptomsd` | `symptomsd` | — | Сетевая телеметрия; источник параллельного сканирования дискового пространства (fileproviderd). | Средняя |
| `com.apple.fileproviderd` | `fileproviderd` | — | Служба FileProvider; именно её `file-read-data` на `/private/var/mobile/Library` была отклонена — смежный, не исполнитель перемещения. | Высокая |

## Три операции, которые нельзя смешивать

1. **Штатное обновление операторских настроек** — установка подписанного `.ipcc` через
   `installd` (путь iTunes/Finder) или OTA через `CommCenter`. Документировано.
2. **Управление eSIM** — `CellularPlanDaemon`/настройки; это управление тарифными планами,
   а не файловый каталог.
3. **Произвольная запись в `/var/mobile/Library/Carrier Bundles/iPhone`** — то, что делал
   Airlift: запись симлинков и структур в живой каталог. **Документированного API для этого
   нет** — это и есть та операция, которую Apple закрыла. **Высокая.**

## Вывод раздела

`CommCenter` владеет операторской конфигурацией, `installd` — официальная установка пакетов,
`atc` — только медиа-синхронизация внутри `/var/mobile/Media`. Путь Airlift был
нестандартным использованием канала синхронизации, и именно его ядро теперь отклоняет.
