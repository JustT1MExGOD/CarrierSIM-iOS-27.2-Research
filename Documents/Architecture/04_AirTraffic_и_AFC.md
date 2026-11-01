# AirTraffic, atc и граница /var/mobile/Media

## Что такое atc

`com.apple.atc` — демон медиа-синхронизации (`/usr/libexec/atc`) под учётной записью
`mobile`. Его launchd-определение объявляет MachServices `com.apple.atc`,
`com.apple.atc.xpc`, `com.apple.atc.xpc.service`, `com.apple.atc.xpc.sessions`,
`com.apple.atc.xpc.downloadprogress`, `com.apple.atc.xpc.observer`,
`com.apple.atc.xpc.runkeeplocaltask`, `com.apple.atc.xpc.icappobserverdelegate`,
`com.apple.atc2`, `com.apple.private.alloy.airtraffic-idswake`. **Высокая** (launchd-
определение и бинарные строки).

atc синхронизирует объекты `Book`, `Photo`, `Application` и др. между хостом и устройством.
Рабочая область — `/var/mobile/Media` (AFC root). **Высокая.**

## Почему Airlift проходил через atc

Хост отправляет готовые объекты `FileComplete` с `AssetID` вида `../../<staging>/…`.
Старший путь в Beta 2 проверял строку `Cannot move asset outside of AFC root` — текстовый
тест, который AssetID `../../`, проходящий через симлинк `p0/p1/p2/link`, обходил: строка
выглядела как внутри Media, а разрешалась в `/var/mobile/Library`. **Высокая** (строки и
журнал запуска).

## Что изменилось на уровне системы

В Beta 3 перемещение стало выполняться операциями относительно файлового дескриптора
каталога (общий `x24`), с отдельной обработкой ошибок на каждой стадии и форматом
`%{errno}d`. При этом первый объект внутри Media перемещается, а объект с целевым путём
`…/Library/Carrier Bundles/iPhone` отклоняется ошибкой `107`. **Высокая** для поведения;
**средняя** для точного набора имён вызовов (разрешены по форме аргументов).

## Граница ответственности atc

atc — не владелец carrier bundles. Его задача — синхронизация медиа внутри Media. Ошибка
107 — это отказ ядра на уровне системного вызова, а не отказ atc по бизнес-логике:
`fileproviderd` в той же операции получил `deny(1) file-read-data /private/var/mobile/Library`
— тот же контур sandbox. **Высокая** для факта отказа; **средняя** для полного объяснения
механизма (см. «Открытые вопросы»).

## Связь с прежним исследованием

Этот раздел дополняет [документ о статическом сравнении AirTraffic](../03_Сравнение_AirTraffic.md):
там показаны адреса вызовов и строки; здесь — то, как atc вписывается в общую архитектуру
служб и почему его роль в carrier bundles всегда была нестандартной.
