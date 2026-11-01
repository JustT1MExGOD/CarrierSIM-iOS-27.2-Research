# PHASE5 — 02_ACCESS_CONTROL_EVIDENCE

## Цель

Проверить, какие именно сведения о доступе к destination/staging объектам подтверждены локальными материалами, а какие были выведены слишком широко в Phase 4.

Правило: entitlement, UID процесса, наличие helper-service и имя API не являются взаимозаменяемыми доказательствами DAC, sandbox, ACL и фактического права записи.

## 1. Разделение уровней доступа

| Уровень | Что нужно доказать | Что есть локально | Статус |
|---|---|---|---|
| Процесс/identity | под каким runtime identity работает daemon | названия `_installd`, `mobile`, `_wireless` в материалах Phase 1–4 | CONFIRMED на уровне inventory |
| Entitlement | какие capability заявлены процессом | `com.apple.private.security.storage.AppBundles`, `seatbelt-profiles` и другие entitlement strings | CONFIRMED как наличие строки/entitlement материала |
| XPC authorization | кто может вызвать экспортированный метод | отдельные helper/IPC callsites и per-method checks изучены не для всех staging paths | PARTIAL / NOT VERIFIED globally |
| DAC owner/group | owner/group конкретного object | runtime strings и API parameters, но не filesystem listing и не numeric values | UNKNOWN для staging/AppBundles objects |
| Mode bits | exact mode конкретного object | `mkdtemp` + subsequent `chmod`, daemon-home check string | UNKNOWN для всех relevant objects |
| ACL | effective ACL конкретного object | API name содержит `removeACLs` | UNKNOWN: contents/result not extracted |
| Sandbox/Seatbelt | разрешённые операции и paths процесса | наличие `seatbelt-profiles`, профиль не декомпилирован | NOT VERIFIED |
| Kernel/VFS | фактический результат access checks | видны path-based syscalls, но нет runtime observation/kernel trace | NOT VERIFIED |

## 2. Entitlement не равен DAC

`com.apple.private.security.storage.AppBundles` является доказательством заявленной системной capability или архитектурной принадлежности, но сам по себе не показывает:

- owner inode конкретного bundle;
- group inode;
- mode bits родительских каталогов;
- ACL entries;
- effective sandbox rule для каждого path;
- наличие другого процесса с той же capability;
- результат kernel permission check в конкретный момент.

Поэтому фразы Phase 4 «entitlement доказывает, что installd владеет доменом» и «запись туда требует именно этого субъекта» должны быть заменены на более узкие:

> Entitlement согласуется с тем, что installd предназначен для работы с AppBundles; локальные материалы не содержат полного доказательства фактических inode ownership, DAC и sandbox policy для каждого relevant path.

## 3. UID процесса не равен owner каталога

В материалах присутствуют строки вида:

- `Daemon's home directory at %@ should be owned by uid %u, but found %u`;
- `Daemon's home directory at %@ should have gid %u, but found %u`;
- `Daemon's home directory at %@ was not a directory; found mode: 0%ho`.

Они подтверждают наличие проверки daemon home/container. Они не доказывают:

- числовое значение ожидаемого UID/GID;
- что тот же owner установлен на каждом staging path;
- что `existingBundleContainer` имеет те же metadata;
- что process UID `_installd` автоматически совпадает с inode owner;
- что group/ACL не дают записи иному субъекту.

Это принципиальная коррекция Phase 4: `_installd` как process identity и owner filesystem object должны рассматриваться раздельно.

## 4. Ownership standardization и ACL

Вызов `standardizeOwnershipAtURL:...` в `installd_B3_disasm.txt` (строки 53970–53988; фрагмент [`evidence/disasm-fragments/standardize_ownership.txt`](../evidence/disasm-fragments/standardize_ownership.txt)) передаёт:

- URL;
- UID, полученный из object/API;
- GID, полученный из object/API;
- `removeACLs=1`;
- `setProtectionClass=1`;
- out-parameter `foundSymlink`;
- error out-parameter.

Прямо подтверждено:

1. функция стандартизации предусмотрена;
2. callsite обрабатывает failure;
3. API имеет флаг удаления ACL;
4. symlink обнаруживается отдельным out-parameter.

Не подтверждено:

1. какие именно UID/GID переданы в конкретном запуске;
2. меняет ли функция mode, и если да — на какое значение;
3. какие ACL существовали до вызова;
4. были ли ACL удалены успешно во всех ветвях;
5. применяется ли этот callsite к каждому destination, который рассматривается IOS-SEC-005;
6. нет ли ACL или расширенных kernel restrictions после последующей операции.

Следовательно, «ACL исключён» — недоказанный вывод. Правильный статус: **API-level mitigation observed; effective ACL state UNKNOWN**.

## 5. Fresh staging и helper service

Подтверждено, что `stageItemAtURL` и `moveItemInStagingLocation` вызываются через `_synchronousRemoteObjectProxyWithErrorHandler:`. Это подтверждает IPC delegation, но не полную authorization policy.

Нельзя автоматически заключить:

- helper service имеет те же DAC права, что и installd;
- helper service не принимает path, который может контролироваться менее доверенным caller'ом;
- `onBehalfOf` ограничивает capability, а не только записывает attribution;
- helper service не имеет иных callsites с более широкими входными данными;
- все helper-side file operations используют безопасный object-anchored механизм.

Для этого нужны helper binary, его sandbox/entitlement material и полный protocol authorization analysis. В текущем корпусе они отсутствуют.

## 6. Sandbox и kernel/VFS

Наличие `seatbelt-profiles` entitlement показывает связь процесса с sandbox profile infrastructure, но не восстанавливает policy. В корпусе нет локально подтверждённого полного набора правил:

- allow/deny для AppBundles;
- разрешения на rename/unlink/chmod родительских компонентов;
- ограничения на symlink traversal;
- межпроцессные различия между installd и helper service;
- ограничения для процессов с тем же UID или capability.

Также нет динамического VFS trace, и его намеренно не следует получать в Phase 5: пользователь ограничил работу статическим офлайн-анализом.

Статус sandbox/VFS evidence: **NOT VERIFIED**, не `CONTRADICTED`.

## 7. Access-control verdict

Прежнее Phase 4 утверждение «нет непривилегированного writer'а» не является локально доказанным в строгом смысле. Доступные материалы показывают intended trust architecture и несколько защитных вызовов, но не полный effective access-control state.

Итог:

- intended privileged ownership: **ARCHITECTURAL INFERENCE**;
- exact DAC owner/group/mode: **UNKNOWN**;
- exact ACL state: **UNKNOWN**;
- complete sandbox policy: **NOT VERIFIED**;
- existence of an untrusted writer: **NOT VERIFIED**, а не `CONTRADICTED`;
- доказанный внешний writer: **не найден**;
- доказательство невозможности writer'а: **отсутствует**.
