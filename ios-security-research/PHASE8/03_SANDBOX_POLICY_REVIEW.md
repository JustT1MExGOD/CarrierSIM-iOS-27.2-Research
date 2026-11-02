# PHASE8 — 03_SANDBOX_POLICY_REVIEW

## Доступные policy artifacts

B2 и B3 содержат Mach-O arm64e sandbox kext:

- B2: `C:\ipsw-tools\beta2\sandbox\com.apple.security.sandbox`, UUID `757D791B-2F6E-38AF-88F4-56996F99B8BC`;
- B3: `C:\ipsw-tools\beta3\sandbox\com.apple.security.sandbox`, UUID `1490B613-0415-3F49-8612-7B8D08328873`.

Оба файла содержат sandbox engine, policy evaluation routines и строки, относящиеся к Mach/bootstrap, но в корпусе нет декодированных seatbelt profile blobs или per-client effective policy.

## Результаты поиска строк

В обоих kext найдены:

- `mach-lookup`;
- `common-mach-lookups`;
- `com.apple.security.exception.mach-lookup.global-name`;
- `com.apple.security.exception.mach-lookup.local-name`;
- `bootstrap`, `mach-bootstrap`;
- `amfid`;
- `com.apple.amfi.xpc`;
- `com.apple.amfi.nsxpc`;
- `/private/var/db/amfid`;
- `com.apple.private.security.storage.amfid`;
- `com.apple.rootless.storage.amfid`;
- `AppleMobileFileIntegrity`.

Точная строка `com.apple.amfi.nsxpc` встречается один раз в каждом kext (B2 offset `0x1af2fb`; B3 offset `0x1b0183`). Эти offsets различаются из-за layout/version changes. Рядом находятся служебные и policy-related данные, однако без разбора xref/serialized profile нельзя доказать, является ли строка rule name, logging text, lookup table entry или unrelated constant.

## Что доказано

1. Sandbox framework знает о Mach lookup как о контролируемом классе операции.
2. Sandbox framework содержит механизмы global/local mach-lookup exceptions.
3. В compiled kext присутствуют AMFI-related names, включая `com.apple.amfi.nsxpc`.
4. B2/B3 policy artifacts различаются значительно по байтам, поэтому простое совпадение/несовпадение файла не отвечает на вопрос об effective rule.

## Что не доказано

Не найдено декодированное правило вида:

```text
(allow mach-lookup (global-name "com.apple.amfi.nsxpc"))
```

или:

```text
(deny mach-lookup (global-name "com.apple.amfi.nsxpc"))
```

Также не восстановлены:

- default policy для обычного App Store процесса;
- наследование profile parameters;
- profile, применяемый к amfid client/server;
- entitlement-conditioned exceptions;
- launchd bootstrap namespace;
- различия lookup policy между system app и third-party app.

Отсутствие явного текстового allow/deny **не является** ни разрешением, ни запретом.

## Вывод

Статический sandbox kext audit подтверждает наличие policy machinery и наличие AMFI-related constants, но не даёт effective authorization result для `com.apple.amfi.nsxpc`. Для этого нужны декодированные seatbelt profiles/compiled policy tables, client profile assignments и launchd bootstrap metadata.

Статус для конкретного lookup: **NOT VERIFIED**.
