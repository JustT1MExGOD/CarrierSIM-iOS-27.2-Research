# PHASE3 — 07_FINDING_ASSESSMENT: итог по IOS-SEC-004

## Ответы на обязательные вопросы

**1. Установлен ли точный формат манифеста?**
Да. Объект IOS-SEC-004 — **бинарный delta-patch command stream**
(`com.apple.deltainstallcommands`, исходный файл `delta_update.c`),
а не plist `MIIPAPatcherManifest`. Формат восстановлен:
`magic "ipaD"` + `version∈{1,2,3}` + последовательность команд вида
`cmd arg1[=arg2]` где cmd ∈ {`+`,`-`,`=`,`N`} и маркер `xEOF`.
Имена функций — internal C names из embedded-строк (не external symbols).

**2. Восстановлен ли полный путь обработки?**
Да — `mmap → validate_stream(magic/version/devices/infoPlistHash) →
command-loop(read_next_manifest_command + FTS-walk) → dispatch(+,-,=,N)
→ path-check → file-op → EOF → cleanup`. Каждый этап отображён в
02_CONTROL_FLOW с адресами.

**3. Найдены ли конкретные ошибки проверки границ?**
Нет. Все 9 категорий ТЗ проверены: bounded reader (offset<len на каждый
байт), per-field caps (0x400/0x19), opcode whitelist + invalid-command
reject, delimiter-required, EOF hygiene (`xEOF` valid/, malformed EOF
error), error-abort (единый `_CreateAndLogDMError` → return 0, без
продолжения), stack canaries, anti-symlink/realpath/entity-type checks.
См. 03_BOUNDARY_CHECKS.

**4. Найдены ли признаки повреждения памяти?**
Нет. OOB/overflow/UAF/double-free/uninit — NOT FOUND (см. 04). Единственный
стоящий класс — **TOCTOU** (path-check по realpath/symlink, затем
path-based syscall `link`/`mkdir`/`rename`/`chmod`/`symlink`/`unlink` —
ни одного fd-anchored `*at`), но он не доведён до доказанного дефекта:
staged-каталог привилегирован `_installd`, ввод — из подписанного пакета,
и `realpath'd destpath is different from non-realpath` + symlink-reject
снижают поверхность.

**5. Какие подозрения удалось опровергнуть?**
- «unbounded parse» — опровергнуто: bounded reader + caps.
- «любой байт → команда» — опровергнуто: opcode whitelist.
- «declared-length OOB» — опровергнуто конструктивно: text-delimited
  формат, нет length-prefix.
- «обработка продолжается после ошибки» — опровергнуто: единый error-abort.
- «непроверяемый magic/version» — опровергнуто: оба валидируются.

**6. Какие данные ещё необходимы?**
- Точный callsite/контекст `hardlink_copy_hierarchy` (кто открывает
  staged-каталог и с какими правами) — чтобы оценить, есть ли у
  непривилегированного процесса write-доступ в окно TOCTOU.
- Реальный `com.apple.deltainstallcommands` sample-манифест для
  подтверждения семантики повторов/extended-команд.
- Kernel/sandbox context — какие ещё проверки накладывает VFS/sandbox
  на file-ops installd.

## Итоговый статус

**INSUFFICIENT EVIDENCE → скорее RULED OUT по memory/boundary-вектору,
с открытым остатком TOCTOU.**

Обоснование: ни один из обязательных классов дефекта не подтверждён —
парсер является корректным defensive bounded line-reader с opcode
whitelist, per-field bounds, EOF/error hygiene и stack protection.
Единственный нерешённый вопрос — TOCTOU между path-check и path-syscall,
и он не доказан как реальный вектор (привилегированный staged-dir +
anti-symlink checks + signed input). Для CONFIRMED или PLAUSIBLE нет
конкретного дефекта; чистый RULED_OUT не ставлю только потому, что
TOCTOU-окно структурно существует, хотя и не эксплуатируемо из
доказанной позиции.

→ Рекомендуемый статус: **INSUFFICIENT EVIDENCE** (точнее —
«no defect found; residual TOCTOU class open but not demonstrated»).
