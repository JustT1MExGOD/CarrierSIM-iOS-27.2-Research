# PHASE2_RESEARCH_SUMMARY — Verification & Triage

## 1. Есть ли хотя бы одна находка с конкретными признаками уязвимости?

**Нет.** В Phase 2 не подтверждено ни одной `CONFIRMED SECURITY ISSUE`
и не осталось кандидата со статусом `PLAUSIBLE / NEEDS VALIDATION`.

Установлены архитектурные наблюдения:

- installd и amfid принимают NSXPC-соединение через accept-all
  `shouldAcceptNewConnection:`; это не равно разрешению любого метода.
  Реальная граница — Mach bootstrap/lookup плюс per-method entitlement
  validation. Для installd экспортируемые install/uninstall-методы
  транзитивно доходят до gated validators.
- `triggerRegistrationFor*` защищён test-mode state (`isRunningInTestMode`
  + `testFlagsAreSet` + sentinel), а включение test-mode — gated.
- AirTraffic B3 действительно использует dirfd-relative move и kernel-side
  capability denial, но точные имена `ENOTCAPABLE`/`0x40000000` не
  подтверждены локальным Darwin SDK.

## 2. Какие первоначальные гипотезы опровергнуты?

- **IOS-SEC-001:** accept-all не доказал IPC bypass; это архитектура
  accept-all + method-level authorization. Внутренние `_`-методы не входят
  в NSXPC-протокол и не вызываются удалённым клиентом напрямую.
- **IOS-SEC-002:** отсутствие gate на тонких trigger-обёртках компенсируется
  защищённым test-mode состоянием; `checkCapabilities` read-only, а
  `getPidForTesting` только возвращает `getpid()`.
- **IOS-SEC-003:** double-fetch опровергнут: один vm_read для profile body,
  один для отдельного profileAuxSig; повторного чтения одного источника
  после проверки нет.
- **IOS-SEC-008:** no-whitelist claim опровергнут реальными вызовами
  `decodeObjectOfClass:` и `unarchivedObjectOfClasses:fromData:error:`.
- Не доказаны как уязвимости: manifest parser, realpath TOCTOU,
  XML/DER differential, intermediate-symlink issue.

## 3. Какие кандидаты требуют дополнительных материалов?

Три направления имеют `INSUFFICIENT EVIDENCE`, но не конкретный доказанный
дефект:

1. **IOS-SEC-004:** нужен полный control-flow manifest command-loop с
   проверками длины каждого поля; безопасно — только статический разбор,
   без создания malformed архивов для системных служб.
2. **IOS-SEC-005:** нужен полный install write-chain, чтобы установить,
   используется ли fd/atomic operation после `realpath_parent_no_symlink`
   или path-string.
3. **IOS-SEC-007:** нужны канонические XML и DER-пары либо реализация
   parser boundary, чтобы показать реальный differential.

Для архитектурной полноты также полезны:

- sandbox-профиль installd и bootstrap entitlement policy;
- Darwin/XNU `errno.h` и `fcntl.h` соответствующего SDK;
- распакованный kernelcache/sandbox для точного объяснения errno 107.

## 4. Какие направления наиболее обоснованны для дальнейшего безопасного исследования?

1. **Статический разбор sandbox/kerncache** — определить механизм
   capability denial и проверить, какие границы являются политикой ядра,
   не исследуя обход.
2. **Полный статический CFG manifest parser** — только для проверки
   bounds/EOF/integer handling, без payloads и запуска на iOS.
3. **Полная цепочка realpath → fd/rename/write** — определить, закрывается
   ли TOCTOU архитектурно; не проводить race-тесты против устройства.
4. **Документальная проверка Mach bootstrap restrictions** — отделить
   локально наблюдаемый plist от общих Darwin-архитектурных ожиданий.

## Финальный triage

| Статус | Количество |
|---|---:|
| CONFIRMED SECURITY ISSUE | 0 |
| PLAUSIBLE / NEEDS VALIDATION | 0 |
| ARCHITECTURAL OBSERVATION | 3 |
| RULED OUT | 2 |
| INSUFFICIENT EVIDENCE | 3 |

Phase 2 сохранила все Phase 1 документы и вынесла корректировки в отдельные
файлы. Отсутствие подтверждённой уязвимости означает именно результат
текущей проверки, а не доказательство принципиальной невозможности дефекта
в iOS или отсутствия иных проблем вне изученных материалов.
