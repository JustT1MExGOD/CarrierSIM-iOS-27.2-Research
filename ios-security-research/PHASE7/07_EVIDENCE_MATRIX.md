# PHASE7 — 07_EVIDENCE_MATRIX

Статусы: `CONFIRMED` / `CONTRADICTED` / `NOT VERIFIED`. Отсутствие найденной проверки ≠ доказанное отсутствие проверки.

## getSEPStateWithReply:

| Условие | Статус | Основание |
|---|---|---|
| A. Exported через IPC | **CONFIRMED** | Селектор #2 в `__objc_methlist` протокола `AMFIProtocol`; протокол привязан к exportedInterface в `shouldAcceptNewConnection:` |
| B. Reachable для непривилегированного клиента | **NOT VERIFIED** | Accept = return 1 без gate, но launchd plist amfid отсутствует в корпусе; sandbox `mach-lookup` и bootstrap namespace не разобраны. Accept-all обработчик не доказывает достижимость имени из untrusted bootstrap namespace |
| C. Insufficient authorization | **NOT VERIFIED** | В теле метода gate отсутствует [CONFIRMED]; единственный возможный уровень авторизации — lookup/transport, который недоступен для анализа. Нельзя ни подтвердить, ни исключить наличие системного ограничения до входа в метод |
| D. Sensitive result | **NOT VERIFIED** | Возвращается 49-байтная структура LAStorage key 0xf (метаданные записи). Чувствительность: системные метаданные, LOW–MEDIUM; защищённого секрета по layout не видно, но семантика полей не восстановлена |

## getStagedProfileWithReply:

| Условие | Статус | Основание |
|---|---|---|
| A. Exported через IPC | **CONFIRMED** | Селектор #5 в `__objc_methlist` `AMFIProtocol` |
| B. Reachable для непривилегированного клиента | **NOT VERIFIED** | то же, что выше — lookup/sandbox не разобраны |
| C. Insufficient authorization | **NOT VERIFIED** | Нет gate в теле [CONFIRMED]. Контраст: write-side (`stageProfileForUuid:`) gated — асимметрия подтверждена; но полнота авторизации с учётом transport-уровня недоказуема |
| D. Sensitive result | **NOT VERIFIED** | Возвращает содержимое `UPPStaging.plist` — по write-side staged UUID. Чувствительность: системные метаданные/oracle, LOW–MEDIUM |

## Дополнительно зафиксированные факты

| Факт | Статус |
|---|---|
| `com.apple.amfi.nsxpc` реально используется кодом (`initWithMachServiceName:`) | CONFIRMED |
| `shouldAcceptNewConnection:` не имеет ветки отказа | CONFIRMED |
| `verifyBoolEntitlement:` присутствует у всех 11 mutator'ов и отсутствует только у 2 getter'ов | CONFIRMED |
| Прямое использование audit-token / SecTask / xpc_connection_get_* где-либо в amfid | **NOT VERIFIED** (не найдено в корпусе; не приравнивать к CONTRADICTED) |
| Ограничения launchd/sandbox на `com.apple.amfi.nsxpc` | **NOT VERIFIED — материалы недоступны для анализа** |
| B2↔B3 различия в обоих методах | CONTRADICTED как различие — disasm-файлы идентичны |

## Почему C не может быть CONFIRMED

Для `CONFIRMED` на «insufficient authorization» надо показать, что ни один уровень цепочки не выполняет эквивалентной проверки. Уровень 0 (bootstrap/sandbox lookup) находится вне доступных материалов → утверждать недостаточность нельзя. Одновременно CONTRADICTED тоже нельзя — внутренних проверок действительно нет, и вероятность того, что системный демон NSXPC-интерфейс ограничен только mach-lookup, отлична от нуля.
