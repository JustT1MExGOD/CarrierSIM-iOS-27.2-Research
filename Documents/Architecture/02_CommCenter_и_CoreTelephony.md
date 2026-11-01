# CommCenter и CoreTelephony — владелец операторской конфигурации

`com.apple.CommCenter` — основной системный демон телефонии. Запускается `launchd` из
`/System/Library/Frameworks/CoreTelephony.framework/Support/CommCenter`, под учётной
записью `_wireless`, с ограничением `_LimitLoadToDeviceTree = baseband` (работает только на
устройствах с модемом). **Высокая** (launchd-определение прочитано из файловой системы).

## MachServices, объявленные у CommCenter

Из `com.apple.CommCenter.plist`:

```
com.apple.commcenter.xpc
com.apple.commcenter.coretelephony.xpc
com.apple.commcenter.carrierspace.xpc
com.apple.commcenter.atcs.xpc
com.apple.commcenter.ari.rt.xpc
com.apple.commcenter.cupolicy.xpc
com.apple.commcenter.tmk.xpc
com.apple.commcenter.oswatchdog
com.apple.commcenter.mobile-helper-cbupdateservice
com.apple.CellularPlanDaemon.xpc
com.apple.aps.CommCenter
com.apple.aps.CommCenter.webpush
com.apple.basebandd.xpc
com.apple.commcenter.fine-grained
com.apple.usernotifications.delegate.com.apple.SIMSetupUIService
com.apple.usernotifications.delegate.com.apple.SOSBuddy
com.apple.usernotifications.delegate.com.apple.telephony.BasebandServicesNotification
```

## Роль в carrier bundles

CommCenter — владелец операторского профиля и выбора применяемого бандла. Строки
`InstalledCarrierProfileVersion`, `CarrierName1`, `CarrierName2`, `KeyCommCenterStats*` и
путь `CoreTelephony` обнаружены в бинарнике AirTraffic. **Высокая.**

## Ограничения для стороннего использования

Эти XPC — **внутренние привилегированные** интерфейсы, а не публичные API. Их наличие
подтверждено, но:

- они обслуживают конкретные задачи (профиль, регистрация, политики);
- нет свидетельств существования у них общего вызова «записать файл по произвольному пути»;
- принадлежность к root-уровню сама по себе не делает интерфейс пригодным для записи в
  каталог — это ключевое ограничение, не факт доступности.

**Низкая/средняя** — интерфейсы существуют, но назначение вызовов и их пригодность для
изменения `/var/mobile/Library/Carrier Bundles/iPhone` не установлены и не проверялись.
