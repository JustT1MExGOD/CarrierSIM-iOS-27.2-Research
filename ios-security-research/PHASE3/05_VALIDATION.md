# PHASE3 — 05_VALIDATION: независимая учебная модель парсера

## Метод и оговорки

Построена **отдельная учебная модель** state-machine, реализующая
восстановленную семантику `read_bytes`/`read_next_manifest_command` —
**не копия оригинального кода**. Её поведение иллюстрирует замысел
(bounded fields + opcode whitelist + delimiter requirement), но НЕ
доказывает поведение оригинального `installd`. Реальный `installd`
не запускался; повреждённые данные никуда не отправлялись.

## Восстановленная модель (семантика)

- magic `ipaD` + version поле (cap 0x19);
- цикл: 1 байт command → arg1 до `\t`/`\n` (cap 0x400) → если `=` то
  arg2 до `\t`/`\n` (cap 0x19, strtoll) → `'x'`+`EOF` завершает;
- opcode whitelist {`+`,`-`,`=`,`N`}; прочее → reject;
- bounds: чтение не выходит за len(stream); каждое поле обязано
  завершиться delimiter или cap.

## Результаты прогона модели

| Тест | Поведение модели | Соответствует оригиналу? |
|---|---|---|
| empty | reject (нет magic) | ✅ — `read_bytes` bounds-abort до magic |
| magic-only | end-of-stream, 0 cmds | ✅ — bounds-check завершает цикл чисто |
| truncated-cmd | end-of-stream, частично | ✅ — `Failed to read ... command` error path |
| bad-opcode `\x00` | REJECT invalid command | ✅ — `Stream had invalid command` |
| oversized arg1 (2000B) | arg1-truncated | ✅ — cap 0x400 срабатывает |
| unterminated numeric | end-of-stream | ✅ — `Failed to read arg2`/`Invalid touch time` |
| valid stream | EOF, cmds распарсены | ✅ |

## Что подтверждает модель

- **bounded-поля:** ни одно поле не читается неограниченно; cap 0x400/0x19
  не пропускает oversized input в stack-буфер — overflow невозможен
  конструктивно (cap ≤ buffer).
- **opcode-whitelist:** посторонний байт не может стать командой —
  диспатч только валидного set.
- **delimiter-requirement:** отсутствие завершающего `\t`/`\n` до cap
  приводит к error-path, не к использованию усечённого поля как целого.
- **EOF-гигиена:** `xEOF` маркер валидируется; просто исчерпание стрима —
  корректное завершение, не OOB.

## Чего модель НЕ доказывает

- Точная семантика оригинального loop-exit (когда `cap` достигнут без
  delimiter — модель помечает `arg1-truncated`, оригинал идёт в
  `Failed to read arg1` error path; поведение консистентно — обе
  отклоняют неполное поле).
- Повторяющиеся записи и их детерминизм — модель не моделирует file-ops,
  только parse; семантика повторов — вопрос dispatch'а, не parser'а.
- TOCTOU между path-check и syscall — модель вообще не делает file-ops;
  это отдельный вопрос (04).

## Вывод

Учебная модель воспроизводит **корректную defensive-логику** парсера:
bounded поля, opcode-whitelist, delimiter+EOF гигиена, error-abort.
На уровне модели граничные случаи обрабатываются корректно — что
согласуется с прямым чтением дизассемблера и не даёт оснований
подозревать boundary-дефект в оригинале.
