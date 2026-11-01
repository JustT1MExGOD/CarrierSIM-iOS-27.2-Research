# 06_FINDINGS — реестр кандидатов в уязвимости iOS 27.2+

Формат каждой записи — как требует ТЗ: ID, компонент, сборка, класс дефекта,
наблюдаемый факт, гипотеза, доказательство (файл/адрес/код/SHA-256),
альтернативные объяснения, уверенность (LOW/MED/HIGH), статус
(NEEDS_REVIEW / NOT_REPRODUCED / RULED_OUT / CONFIRMED).

Все объекты — офлайн, из `C:\ipsw-tools`. Имена методов — реальные ObjC
selrefs; `bl`-цели разрешены ipsw по имени. Символы dyld-cache — signature-
matched (см. ограничение `.dyldlinkedit` в 01_INVENTORY).
SHA-256: amfid_B3 `d331a10…0db8f`, installd_B3 `1dd5efb…064b1d`,
atc_B3 `2ed9c6f…5a4afc`, AirTraffic_text_B3 `d263612…c54ec1`.

---

## IOS-SEC-001 — installd: безусловный accept + неравномерный per-method gating
- Компонент: `/usr/libexec/installd` (`com.apple.mobile.installd`), B3 (и B2).
- Класс: uneven authorization / архитектурный риск confused-deputy.
- **Факт [OBSERVED, HIGH]:** `-[MobileInstallationServiceDelegate
  listener:shouldAcceptNewConnection:]` (0x10001b280–0x10001b33c) — линейная
  функция, создаёт `MIClientConnection`, `resume`, `mov w0,#1; retab`.
  Нет ветвлений и нет `valueForEntitlement`/`audit_token` — **любое
  XPC-соединение принимается**. Авторизация отложена на методы.
- **Факт [OBSERVED, HIGH]:** централизованные валидаторы есть
  (`sub_10001c7c4`=_ValidateMIAllowedSPIEntitlement, читает
  `com.apple.private.mobileinstall.allowedSPI`; + группа `0x10001e3/4xx`).
  68 методов gated, 29 — нет. install/uninstall-цепочки транзитивно
  закрыты (публичные методы → gated `_validate*`/`_*` internals).
- **Гипотеза:** метод, добавленный/обновлённый без вызова валидатора, открыт
  любому процессу, способному сделать bootstrap-lookup сервиса.
- **Альтернативы:** bootstrap/Sandbox уже ограничивает lookup до entitled-
  клиентов (тогда accept-all безопасен); no-gate методы могут быть read-only
  или делегировать в gated-внутренние.
- Уверенность: HIGH в факте accept-all + uneven coverage; LOW в том, что это
  эксплуатируемо без доп. примитива (lookup-ограничение не проверено).
- Статус: **NEEDS_REVIEW** (структура подтверждена; эксплуатируемость — нет).

## IOS-SEC-002 — installd: `checkCapabilities:` без entitlement-gate
- Компонент: installd B3.
- **Факт [OBSERVED, MED]:** `-[MIClientConnection checkCapabilities:withOptions:completion:]`
  (0x100025940…) не вызывает ни одного валидатора; делегирует
  `defaultManager checkCapabilities:withOptions:error:`. Так же no-gate:
  `getPidForTestingWithCompletion:`, `referencesForBundleWithIdentifier:`,
  `triggerRegistrationForContainerizedContentForOptions:`,
  `triggerRegistrationForDiskImageContentForOptions:`,
  `_triggerRegistrationForContent:…`.
- **Гипотеза:** часть методов протокола досягаема без entitlement;
  `triggerRegistrationFor*` потенциально запускает регистрацию контента.
- **Альтернативы:** `checkCapabilities` — read-only (низкий риск);
  `triggerRegistrationFor*` могут гейтить ниже в defaultManager или
  требовать bootstrap-доступ, которого у обычного app нет.
- Доказательство: `installd_B3_disasm.txt` 0x1000259d4 `checkCapabilities:
  withOptions:error:` без предшествующего `bl 0x10001c7c4`.
- Уверенность: MED.
- Статус: **NEEDS_REVIEW** — нужно показать, что no-gate метод делает
  привилегированное действие, и что клиент может достичь сервиса.

## IOS-SEC-003 — amfid: `vm_read profileAuxSig` из памяти клиента
- Компонент: `amfid` (`AMFIService`), B3 (B2 идентичен).
- Класс: double-fetch / TOCTOU на недоверенной памяти.
- **Факт [OBSERVED, HIGH]:** `sub_100004030` читает `profileAuxSig` (NSData
  от клиента), берёт `bytes`+`length`, затем `vm_read` копирует из
  адресного пространства вызывающего в свой буфер (0x1000042bc→0x100004300;
  4 вызова `vm_read` на 0x100003a60/3ed8/4260/4300).
- **Гипотеза:** содержимое подписи профиля живёт в изменяемой клиентом
  памяти; если amfid читает указатель, а затем повторно обращается к тем же
  данным при валидации/применении — возможна подмена между fetch'ами.
- **Альтернативы (СИЛЬНЫЕ):** vm_read делает **одноразовую копию**
  буфера → это защитный copy-out, а не double-fetch; уязвимость только если
  буфер читается дважды или указатель переиспользуется после проверки.
  На данный момент виден единственный `vm_read` для profileAuxSig.
- Доказательство: `amfid_B3_disasm.txt` строки ~2700–2740.
- Уверенность: MED в факте vm_read-from-client; LOW в double-fetch.
- Статус: **NEEDS_REVIEW** — требует разбора, читается ли буфер повторно
  или результат валидации привязан к копии.

## IOS-SEC-004 — installd: manifest command-loop (truncated/EOF)
- Компонент: installd B3.
- Класс: parser / integer / state-machine на недоверенном архиве.
- **Факт [OBSERVED, MED]:** строки `Failed to read next manifest command`,
  `Failed to read manifest source version`, `Hit EOF so terminating`,
  `Got done processing bundle but there were still commands remaining`,
  `Invalid manifest file`, `Got manifest for version "%@" but expected "%@"`,
  `Failed to standardize permissions on extracted archive` — указывают на
  ручной command-loop над IPA/patch-manifest.
- **Гипотеза:** truncated/malformed archive → underflow/OOB/state-confusion
  в цикле команд; отсутствие строгой length-validation перед чтением полей.
- **Альтернативы:** цикл может корректно валидировать каждую команду
  (наличие error-строк свидетельствует о проверках); архив доходит до
  installd уже подписанным (install-path gated).
- Уверенность: MED в наличии поверхности; LOW в конкретном баге.
- Статус: **NEEDS_REVIEW** — разобрать цикл read-command.

## IOS-SEC-005 — installd: realpath→write TOCTOU на symlink
- Компонент: installd B3.
- Класс: TOCTOU path-vs-object.
- **Факт [OBSERVED, MED]:** `realpathForURL:withError:`, `Failed to realpath
  parent of %s`, `_extractPackageContainedSymlink:withError:`, `Found symlink
  at destination path "%s"; this is not allowed`, `Entity with mode 0%o
  exists at symlink location in dest path` — есть валидация symlink'ов и
  realpath-нормализация.
- **Гипотеза:** realpath проверяет путь в момент T, а rename/write идёт
  позже по path-string → между ними компонент пути можно подменить
  symlink'ом; проверенный путь ≠ записанному объекту.
- **Альтернативы:** запись может идти по fd (тогда TOCTOU закрыт);
  install-path gated + staged в недоступном атакующему каталоге.
- Уверенность: MED. Статус: **NEEDS_REVIEW** — проверить fd-vs-path при записи.

## IOS-SEC-006 — atc/AirTraffic: промежуточные symlink внутри dirfd-дерева
- Компонент: AirTraffic.framework B3 (move-логика).
- **Факт [OBSERVED, HIGH]:** B3 move dirfd-bound + RENAME_NOFOLLOW на
  последнем компоненте + errno 107 при выходе за AFC root.
- **Гипотеза:** RENAME_NOFOLLOW защищает только final-component; промежуточные
  symlink'и внутри `/var/mobile/Media` разрешаются ядром — если один из них
  указывает за пределы, ядро должно отказать (capability), но поведение для
  intra-Media symlink→symlink цепочек не подтверждено до конца.
- **Альтернативы:** kernel confinement по resolved-vnode покрывает все
  промежуточные symlink — тогда зазора нет (основное объяснение).
- Уверенность: MED. Статус: **NEEDS_REVIEW** — нужен тип root-fd и семантика
  intermediate-symlink в dirfd-resolution.

## IOS-SEC-007 — installd/amfid: entitlement XML parser differential
- Компонент: installd + amfid B3.
- **Факт [OBSERVED, MED]:** `parseEntitlements`, `AMFIUnserializeXML`,
  `Cannot construct DER entitlements … possibly corrupt XML`,
  `Being asked to construct DER entitlements` — entitlement'ы парсятся из XML.
- **Гипотеза:** расхождение между тем, как userspace-парсер читает
  entitlements, и тем, что видит ядро/AMFI → signing-bypass / неправильная
  атрибуция entitlement.
- **Альтернативы:** единый канонический парсер; DER-формат проверяется
  подписью до парсинга.
- Уверенность: LOW. Статус: **NEEDS_REVIEW** (низкоприоритетно — нет
  конкретного расхождения).

## IOS-SEC-008 — installd: NSKeyedUnarchiver allowedClasses
- Компонент: installd B3.
- **Факт [OBSERVED, MED]:** `Failed to unarchive journal entry data`,
  `Failed to deserialize built-in persona associations`, `MIPersonaLifecycle-
  EventJournalEntry` — deserialize недоверенных plist'ов.
- **Гипотеза:** unarchive без строгого allowed-class whitelist → object-
  substitution / class-confusion.
- **Альтернативы:** NSKeyedUnarchiver с requiresSecureCoding+whitelist
  (стандарт на iOS) — безопасен; journal-файлы в защищённом каталоге.
- Уверенность: LOW. Статус: **NEEDS_REVIEW** — найти `setAllowedClasses`.

## RULED_OUT (опровергнутые гипотезы — фиксируем честно)
- **amfid uneven gating** — ОПРОВЕРГНУТО: все mutating-методы AMFIService
  вызывают `verifyBoolEntitlement:`; неравномерности нет. (был подозреваемым)
- **atc содержит фикс Airlock** — ОПРОВЕРГНУТО: atc B2==B3; фикс в AirTraffic.
- **amfid изменился в B3** — ОПРОВЕРГНУТО: инструкции идентичны.
- **installd ослабил авторизацию в B3** — ОПРОВЕРГНУТО: валидаторы не
  изменились, новые методы gated; изменения = усиление (extension-validation).
