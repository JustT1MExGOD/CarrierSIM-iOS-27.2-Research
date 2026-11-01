# PHASE5 — 01_PATH_PROVENANCE

## Цель и режим

Этот документ повторно устанавливает происхождение путей, участвующих в IOS-SEC-004 и IOS-SEC-005. Анализ выполнен только по локальным статическим материалам: дизассемблированию `installd_B3.bin`, строкам, импортам и документам Phase 1–4.

Ограничения Phase 5:

- Только статический офлайн-анализ.
- Не взаимодействовать с iPhone.
- Не запускать фаззинг системных служб.
- Не выполнять тесты гонок на реальных системных компонентах.
- Не создавать эксплуатационные полезные нагрузки.
- Не разрабатывать обходы sandbox, повышение привилегий или эксплуатационные цепочки.
- Не изменять системные бинарники.
- Не публиковать результаты автоматически.
- Не выполнять Git push.

Ключевое правило аудита: происхождение строки пути, право назвать путь и право изменять объект по этому пути — разные свойства и не должны объединяться в один вывод.

## 1. Delta-patch: что является источником destination

### Наблюдаемая цепочка

В дизассемблировании `installd_B3_disasm.txt` (строки 55933–56113) функция `-[MIInstaller _patchUpdateInstallableForBundle:manifestPath:existingBundleContainer:patchType:error:]` — фрагмент: [`evidence/disasm-fragments/patch_update_head.txt`](../evidence/disasm-fragments/patch_update_head.txt):

1. получает объект bundle/identity и параметры patch;
2. проверяет состояние bundle через `isPlaceholder`;
3. формирует ошибку, если application не установлено или является placeholder;
4. получает `stagingURL`, `stagingLocation`, `packageFormat`, `identity`, `installationDomain`, `options` и `installOperationType`;
5. передаёт существующий объект `existingBundleContainer` в `initWithBundle:...existingBundleContainer:...`.

Из этого непосредственно следует:

- destination для delta-пути связан с уже установленным bundle-контейнером;
- в исследованном callsite не видно, что клиент передаёт произвольную строку destination для прямой записи;
- путь для destination проходит через внутренние объекты MobileInstallation, а не через отдельный raw path-аргумент функции `hardlink_copy_hierarchy`.

### Что это не доказывает

Из этого callsite нельзя доказать всё нижеследующее:

- что ни один другой upstream-callsite никогда не формирует аналогичный объект иначе;
- что все свойства `existingBundleContainer` уже проверены на каждом компоненте пути непосредственно перед каждой операцией;
- что filesystem object в момент `realpath` совпадает с object в момент последующего syscall;
- что ни один другой процесс не может изменять родительский каталог;
- что destination имеет конкретные UID, GID, mode или ACL;
- что sandbox-политика полностью запрещает конкурентную запись.

Статус provenance для delta destination: **CONFIRMED на уровне внутреннего источника объекта; UNKNOWN на уровне фактических filesystem metadata и конкурентной записи**.

## 2. Delta manifest и относительные компоненты

`hardlink_copy_hierarchy` получает delta manifest и destination root, после чего строит дочерний путь из destination root и относительного имени. В Phase 3 подтверждены:

- ограниченное форматирование пути через `snprintf("%s/%s")` с буфером 0x400;
- проверки `realpath_parent_no_symlink`, `lstat`, entity type и resolved-vs-requested path;
- последующие операции `link`, `mkdir`, `rename`, `unlink`, `chmod`, `symlink`, `copyfile` по path-string.

Это подтверждает происхождение относительной части пути из проверяемого delta command stream и destination root, но не превращает path-string в неизменяемую ссылку на filesystem object.

Статус: **CONFIRMED для способа построения строки; NOT VERIFIED для идентичности объекта между проверкой и использованием**.

## 3. Fresh-install staging: отдельный механизм

Fresh-install staging нельзя автоматически подставлять в анализ delta-patch. В `installd_B3_disasm.txt` (строки 53195–53257) `_takeOwnershipOfInstallableContainingSymlink:error:` — фрагмент: [`evidence/disasm-fragments/take_ownership.txt`](../evidence/disasm-fragments/take_ownership.txt):

- получает `identity` и `location` installable;
- вызывает `stagingLocationForInstallLocation:withinStagingSubsystem:usingUniqueName:error:`;
- передаёт `installURL`, options и staging location в `stageItemAtURL:toStagingLocation:options:containedSymlink:error:`;
- затем сохраняет install URL и staging location в объекте installable.

В `installd_B3_disasm.txt` (строки 82816–82916) `MIHelperServiceClient` получает synchronous remote object proxy и вызывает helper-service method `stageItemAtURL:toStagingLocation:options:completion:`. Аналогично строки 83776–83865 вызывают `moveItemInStagingLocation:atRelativePath:toDestinationURL:onBehalfOf:completion:` через remote proxy — фрагмент: [`evidence/disasm-fragments/helper_proxy.txt`](../evidence/disasm-fragments/helper_proxy.txt).

Подтверждено:

- fresh-install staging использует отдельный helper-service путь;
- имя staging location запрашивается с `usingUniqueName`;
- операции stage/move происходят через IPC-клиент helper service.

Не подтверждено:

- какие именно UID/GID/mode/ACL установлены helper service;
- какие filesystem ACL и sandbox rules действуют в момент операции;
- может ли иной субъект с системными полномочиями конкурентно менять staging root;
- что `onBehalfOf` равнозначно отсутствию самостоятельной authority у helper service.

Статус provenance fresh staging: **CONFIRMED для call chain, UNKNOWN для полной модели writer'ов и прав объектов**.

## 4. Ownership standardization: что реально видно

В `installd_B3_disasm.txt` (строки 53970–53988) виден вызов — фрагмент: [`evidence/disasm-fragments/standardize_ownership.txt`](../evidence/disasm-fragments/standardize_ownership.txt):

`standardizeOwnershipAtURL:toUID:GID:removeACLs:setProtectionClass:foundSymlink:error:`

Callsite получает значения через методы `uid` и `gid`, передаёт `removeACLs=1` и `setProtectionClass=1`, а результат ошибки и `foundSymlink` обрабатывает отдельно.

Это подтверждает:

- в архитектуре существует отдельный шаг стандартизации ownership;
- API предусматривает UID/GID, удаление ACL и protection class;
- callsite проверяет результат этой операции.

Это не подтверждает:

- конкретные числовые UID/GID;
- итоговый mode каждого staging/destination каталога;
- содержимое ACL до и после вызова;
- успешное выполнение для каждого возможного пути;
- что именно этот callsite применяется к `existingBundleContainer` delta-patch в каждом сценарии.

Вывод: прежняя формулировка «права принадлежат `_installd`» была сильнее локального доказательства. Корректная формулировка — «код содержит путь стандартизации ownership с параметрами UID/GID и removeACLs; фактические значения и результаты для всех объектов не извлечены».

## 5. Итоговая provenance-таблица

| Компонент | Что подтверждено | Что остаётся UNKNOWN/NOT VERIFIED |
|---|---|---|
| Delta destination | `existingBundleContainer` уже установленного bundle | фактический абсолютный path, metadata, concurrent writers |
| Delta child path | строится из destination root и manifest-relative name | identity объекта после check до syscall |
| Fresh staging location | выбирается через `stagingLocation...usingUniqueName` | фактический owner/mode/ACL и полный writer set |
| Helper stage | вызов через synchronous remote proxy | policy helper service, независимая authority, DAC |
| Ownership API | `standardizeOwnership...toUID:GID:removeACLs...` присутствует и вызывается | числовые UID/GID, mode, ACL content, success for all paths |
| Daemon home check | runtime checks UID/GID/mode предусмотрены строками и кодом | значения, применимость к AppBundles и staging |
| Client input | bundle/ID/manifest участвуют в request | полный upstream call graph и все alternate callsites |

## Итог

Происхождение destination для основного delta callsite достаточно, чтобы отвергнуть тезис «клиент передаёт произвольный destination path». Но его недостаточно, чтобы доказать отсутствие любого writer'а или конкретные DAC/ACL свойства. Поэтому provenance поддерживает ограниченный вывод о внутреннем выборе destination, но не поддерживает `RULED OUT` для всей TOCTOU-гипотезы.
