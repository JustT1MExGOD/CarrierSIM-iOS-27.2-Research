# PHASE2_AIRTRAFFIC_VERIFICATION — IOS-SEC-006 и errno 107

Источники: `AirTraffic_text_B3.bin` (SHA-256
`d263612f…c54ec1`), `AIRLOCK_DEEP_VERIFICATION/`,
`AIRLOCK_SYMBOL_VERIFICATION/`, RC runtime log. Работа статическая; обходы
AFC root не исследовались.

## 1. Что непосредственно видно в коде

В B3 move routine:

1. строка root: `/var/mobile/Media/`;
2. `mov w1,#0x4010,lsl#16` @ text offset `0x19280`, то есть
   `w1=0x40100000`;
3. двухаргументный call с `x0=path`, `w1=0x40100000`, результат fd в `x24`;
4. последующие вызовы используют `x24` как dirfd:
   `mkdirat`-образный (dirfd,path,mode),
   пятиаргументный `renameatx_np`-образный вызов с двумя одинаковыми dirfd,
   затем `unlinkat`-образный вызов;
5. rename получает `w4=0x20`;
6. строки: `Could not open AFC root`, `Could not create directory beneath AFC root`,
   `Airlock moved ... beneath AFC root`, `Failed to move ... beneath AFC root`.

### Уровень доказательства имён
- `renameatx_np`: **HIGH по форме** — уникальная 5-аргументная форма с двумя
  dirfd; literal import name в AirTraffic local image не резолвится.
- `mkdirat`/`unlinkat`: **HIGH по форме `*at` + dirfd**, literal names
  **MEDIUM**, так как dyld-linkedit отсутствует.
- `open`: **HIGH по форме** (2 args, path + flags, возвращает fd), имя
  import **MEDIUM/NOT DIRECTLY RESOLVED**.
- `RENAME_NOFOLLOW`: `0x20` соответствует этому Darwin flag и передаётся
  в rename call — **HIGH** по локальному callsite.

## 2. errno 107 и ENOTCAPABLE

Локальный runtime/kernel evidence устанавливает:

- строка ошибки устройства: `107: Capabilities insufficient`;
- kernel strerror table содержит текст `Capabilities insufficient` в
  соседней индексной позиции, что объясняет прежнюю off-by-one проблему
  индексации таблицы;
- ошибка возникает после failing rename-shaped call и проверяется в ветке
  error formatting `%{errno}d`.

**Что можно утверждать:** errno 107 — capability-domain denial, не обычный
`EPERM`/`EACCES`; его числовое значение и текст подтверждены локальным
материалом.

**Что нельзя утверждать как локально доказанный факт:** точное имя макроса
`ENOTCAPABLE`. Предыдущие отчёты называли 107 `ENOTCAPABLE` по соответствию
Darwin/XNU errno ordering, но в `C:\ipsw-tools` нет `errno.h`/Darwin SDK,
который бы это подтвердил для конкретного iOS build. Поэтому статус:

- `107 == "Capabilities insufficient"`: **CONFIRMED locally**;
- `107 == ENOTCAPABLE` literal macro in this SDK: **NOT VERIFIED**;
- domain = kernel capability refusal: **HIGH** по тексту/контексту, точная
  внутреняя ветка kernel policy (Seatbelt vs vnode/capability) — **NOT VERIFIED**.

## 3. Флаг 0x40000000

Подтверждено непосредственно:

```
0x40100000 = 0x00100000 + 0x40000000
0x00100000 = O_DIRECTORY  (подтверждается требованием directory fd)
0x40000000 = неизвестная старшая часть flags
```

В локальном наборе нет Darwin `fcntl.h`, который связывал бы
`0x40000000` с именем. Предыдущий отчёт называл `O_EXECONLY` «best fit»,
но это **рабочая интерпретация, не подтверждённое имя для iOS 27.2**.
Возможность private resolve/confinement flag также нельзя исключить.

- `O_NOFOLLOW (0x100)` — **не присутствует** в `0x40100000`;
- `O_NOFOLLOW_ANY (0x20000000)` — **не присутствует**;
- `RENAME_NOFOLLOW (0x20)` — присутствует на rename, final component;
- `0x40000000` name — **NOT VERIFIED**.

## 4. Какие ограничения подтверждаются непосредственно

Подтверждены:

- root path берётся как `/var/mobile/Media/`;
- path operations после открытия используют общий `x24` dirfd;
- final rename получает `RENAME_NOFOLLOW`;
- ошибка форматируется с errno и явно описывает boundary `beneath AFC root`;
- в RC log asset 0 внутри Media прошёл, asset 1 с destination за Media
  получил `[107: Capabilities insufficient]`.

Не подтверждены этим кодом:

- что один `dirfd` механически jail'ит все `..`;
- точный kernel mechanism (Seatbelt, vnode capability, private namei rule);
- поведение каждой возможной промежуточной symlink-цепочки;
- literal names всех stubs и точное имя `0x40000000`.

## 5. Согласование прежних отчётов

Исправления формулировок:

- «dirfd сам по себе изолирует путь» → неверно/слишком широко; корректно:
  dirfd-relative resolution + kernel policy дали наблюдаемый отказ.
- «errno 107 = ENOTCAPABLE как доказанный macro» → смягчено до numeric/text
  capability denial; macro name NOT VERIFIED.
- «O_NOFOLLOW используется» → опровергнуто для open; подтверждён только
  `RENAME_NOFOLLOW` на rename.
- «нет найденного обхода» → это не доказательство принципиальной
  невозможности обхода; этот Phase 2 его не искал.

## Итог IOS-SEC-006

**ARCHITECTURAL OBSERVATION.** B3 действительно использует более строгую
fd-relative/kernel-enforced схему, а Phase 1 hypothesis о новом security
дефекте через intermediate symlink не получила конкретного доказательства.
Точный flag name и symbolic errno name требуют Darwin/XNU headers или
полного символизированного kernel evidence.
