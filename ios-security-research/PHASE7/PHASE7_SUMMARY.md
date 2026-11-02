# PHASE7 — PHASE7_SUMMARY

## 1. Идентификация службы и IPC endpoint

- Реализация: `amfid` (`/usr/libexec/amfid`, предполагаемый путь; launchd plist в корпусе отсутствует), класс `AMFIService`.
- Версии: iOS 27.2 B2 (SHA-256 `39d4d583…`), B3 (`d331a101…`); RC не представлен.
- NSXPC endpoint: **`com.apple.amfi.nsxpc`** — подтверждён реальным использованием в `initWithMachServiceName:` (sub_10000a4f4), не просто строкой.
- Отдельный MIG endpoint `com.apple.MobileFileIntegrity` (`bootstrap_check_in`) существует параллельно и к анализу не относится.

## 2. Экспортируемый протокол

`AMFIProtocol` — 13 required-методов, разобранных напрямую из `__objc_protolist`/`__objc_methlist`/`__objc_methtype`. Оба исследуемых getter'а (#2 `getSEPStateWithReply:`, #5 `getStagedProfileWithReply:`) входят в протокол. Уверенность идентификации: HIGH.

## 3. Схема авторизации

```text
lookup   com.apple.amfi.nsxpc     NOT VERIFIED (нет launchd plist, нет sandbox rules)
accept   shouldAcceptNewConnection  return 1 — accept-all, без ветки отказа
dispatch AMFIProtocol               без per-selector ограничений
method   verifyBoolEntitlement:     у 11/13 методов; НЕТ только у двух getter'ов
         getter bodies              никаких проверок — ни caller, ни caller-derived
```

Единственный слой, где getter'ы могут быть отфильтрованы, — транспорт (bootstrap namespace/sandbox mach-lookup). Именно он вне корпуса.

## 4. `getSEPStateWithReply:`

@0x100004c0c: `LAStorage.domain0 → dataForKey:0xf → getBytes 0x31 → reply(struct, err)`. Возвращает 49-байтовую структуру `{III{C{I[32C]}}}` — метаданные SEP-related записи (exists-флаг, счётчики, 32-байтовое поле вероятного digest/ID). Локальных проверок нет; caller-зависимых веток нет. Семантика полей — NOT VERIFIED; чувствительность LOW–MEDIUM.

## 5. `getStagedProfileWithReply:`

@0x100006230: `stringWithContentsOfFile:@"/private/var/db/amfid/UPPStaging.plist"` → reply(string, err). Читает файл целиком и отдаёт без фильтрации. По write-side (`stageProfileForUuid:`) файл содержит staged UUID. Локальных проверок нет ни до чтения, ни перед ответом.

**Асимметрия:** запись staged UUID требует `com.apple.private.amfi.schedule-profile`; чтение — ничего.

## 6. Классификация данных

Оба ответа — **системные метаданные / диагностика** (LOW–MEDIUM), не секреты: в getSEPState — атрибуты записи доверенного хранилища, в getStagedProfile — staged UUID. Явных защищённых данных (ключи, PII, credentials) в структурах ответа не идентифицировано; оговорка — семантика LAStorage key 0xf и возможное расширенное содержимое UPPStaging.plist не установлены.

## 7. Матрица доказательств

| | Exported | Reachable | Insufficient authz | Sensitive result |
|---|---|---|---|---|
| getSEPState | CONFIRMED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| getStagedProfile | CONFIRMED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |

## 8. Сравнение версий

B2 ≡ B3 для amfid: disasm файлы идентичны, authorization paths совпадают, entitlement-профили одинаковы. Никакого дельта. RC — вне корпуса.

## 9. Итоговые статусы

| Метод | Статус |
|---|---|
| `getSEPStateWithReply:` | **INSUFFICIENT EVIDENCE** |
| `getStagedProfileWithReply:` | **INSUFFICIENT EVIDENCE** |

Ни один не `CONFIRMED` (нет reachability+sensitivity), ни один не `RULED OUT` (нет опровержения). `PLAUSIBLE` не присвоен: позитивного элемента цепочки «непривилегированный клиент достигает endpoint» нет — есть только accept-all обработчик, что по правилам проекта ≠ reachability.

## 10. Рекомендация

**Не закрывать, перевести в deferred-узкий-вопрос.** Гипотеза сведена к одному измеримому пробелу:

> Действует ли `mach-lookup`/bootstrap-namespace ограничение на `com.apple.amfi.nsxpc`, и какие клиентские sandbox-профили его запрещают?

Способ закрытия без динамики:

1. Извлечь launchd plist `com.apple.MobileFileIntegrity.plist`/amfid из полного образа FS (сейчас отсутствует) — он покажет `MachServices`/bootstrap-ограничения.
2. Разобрать sandbox seatbelt-профили `Sandbox`/`container`/`amfid` в kernelcache/kext — mach-lookup whitelist.
3. Семантику LAStorage key `0xf` и содержимого `UPPStaging.plist` уточнить через LocalAuthentication.framework/MIS framework.

Если (1)–(2) покажут, что endpoint живёт в ограниченном namespace или mach-lookup закрыт для обычных приложений — оба метода переходят в `RULED OUT` (защита на transport-уровне). Если покажут глобальную доступность — поднимаются до `PLAUSIBLE / NEEDS VALIDATION`. Текущее состояние ни к тому, ни к другому не приводит.

## Limitations

- Нет launchd plist amfid, sandbox-профилей, dyld-метаданных клиентских ограничений.
- Нет RC-версии amfid.
- Семантика LAStorage key 0xf и формат UPPStaging.plist вне amfid не разобраны.
- Всё статическое; активных запросов к службе не выполнялось.
