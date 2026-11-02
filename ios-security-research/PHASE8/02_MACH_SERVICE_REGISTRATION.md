# PHASE8 — 02_MACH_SERVICE_REGISTRATION

## Уровни доказательства

| Уровень | Результат | Статус |
|---|---|---|
| Строка имени | `com.apple.amfi.nsxpc` присутствует в B2/B3 code/data material | CONFIRMED, но слабое доказательство само по себе |
| Использование имени | `NSXPCListener initWithMachServiceName:` получает это имя | CONFIRMED |
| Объявление в launchd plist | amfid plist отсутствует | NOT VERIFIED |
| Регистрация listener | `NSXPCListener` назначает `AMFIDelegate`, вызывает `resume` | CONFIRMED для локальной регистрации listener |
| Глобальная доступность endpoint | bootstrap namespace/launchd domain не восстановлены | NOT VERIFIED |
| Доступность обычному приложению | client sandbox/lookup policy отсутствует | NOT VERIFIED |

## Подтверждённый код регистрации

В `amfid_B3_disasm.txt`:

```text
sub_10000a4f4:
  0x10000a528: ldr x0, __got._OBJC_CLASS_$_NSXPCListener
  0x10000a52c: objc_msgSend(x0, "alloc")
  0x10000a530: initWithMachServiceName:
  0x10000a534: @"com.apple.amfi.nsxpc"
  0x10000a550: setDelegate:
  0x10000a55c: resume
```

Вызов `initWithMachServiceName:` связывает listener с Mach-service именем на уровне NSXPC API. Это сильнее, чем отдельная строка, но не заменяет launchd-конфигурацию: NSXPC может зависеть от заранее объявленного launchd service/bootstrap context.

`AMFIDelegate listener:shouldAcceptNewConnection:` находится в `0x10000a400–0x10000a4f0`; после создания `AMFIService`, установки `AMFIProtocol`, `exportedObject` и `resume` возвращает `1`.

## Дополнительные имена

В отдельном Mach/MIG пути присутствует `com.apple.MobileFileIntegrity` для `bootstrap_check_in`. Это не доказательство второго имени NSXPC listener и не следует объединять его с `com.apple.amfi.nsxpc`.

Sandbox kext содержит строки `com.apple.amfi.xpc`, `com.apple.amfi.nsxpc`, `amfid` и `AppleMobileFileIntegrity`, но строки не являются decoded launchd declaration или allow rule. Точная xref/semantic role этих строк в текущем декомпилированном корпусе не установлена.

## Launchd и параметры запуска

Полный amfid launchd plist не найден среди B2/B3 extracted files, evidence package или RC materials. Поэтому неизвестны:

- точный `MachServices` dictionary;
- bootstrap/session domain;
- `LimitLoadToSessionType`;
- user/group и `POSIXSpawnType` для amfid;
- launchd-level client restrictions;
- дополнительные service aliases.

## Вывод

**CONFIRMED:** B2/B3 amfid программно создают NSXPC listener с именем `com.apple.amfi.nsxpc`, а listener экспортирует `AMFIProtocol`.

**NOT VERIFIED:** launchd объявление, bootstrap registration details и доступность endpoint для какой-либо категории клиента. Нельзя перейти от `initWithMachServiceName:` к выводу «обычное приложение может выполнить lookup».
