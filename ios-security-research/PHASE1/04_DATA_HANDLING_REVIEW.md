# 04_DATA_HANDLING_REVIEW — обработка недоверенных данных и файловых путей

Метод: статический дизасм + строки. Разделены [OBSERVED] факт /
[CLASS] класс риска / [STATUS]. Никакие payload'ы против компонентов не
запускались. Изолированные примеры — только по собственному коду.

---

## 1. atc / AirTraffic — host-controlled paths (уже доказано, сведено)

- [OBSERVED] host присылает сериализованные assets с контролируемым
  AssetID/путём. До B3 — строковая проверка «outside of AFC root»,
  обходилась `../../`+symlink. B3 — dirfd-bound `open(0x40100000)` +
  `mkdirat` + `renameatx_np(RENAME_NOFOLLOW)` + `unlinkat`, ядро
  возвращает errno 107 при выходе за AFC root.
- [OBSERVED] `0x40000000`-флаг имя — NOT VERIFIED; O_DIRECTORY=0x100000
  CERTAIN; O_NOFOLLOW=0x100 отсутствует; RENAME_NOFOLLOW=0x20 подтверждён.
- [CLASS] path traversal / symlink-в-middle / TOCTOU move. Статус:
  АКТИВНО СМЯГЧЁН в B3 (kernel-anchored). Остаточный риск: RENAME_NOFOLLOW
  покрывает только последний компонент; промежуточные symlink'и внутри
  dirfd-дерева разрешаются ядром — их семантика зависит от того, чем является
  root-fd (chroot vs dirfd+jail) — NOT VERIFIED.
- [STATUS] частично CONFIRMED как зафикшенная граница; остаточное —
  NEEDS_REVIEW (тип root-fd).

## 2. installd — обработчик недоверенных артефактов

installd — самый богатый источник data-handling поверхности:

### 2.1 IPA/zip extraction + manifest command-loop [OBSERVED→CLASS]
- Строки: `Archive at %s doesn't appear to be a zip archive`,
  `Failed to extract archive at %@ to %@`, `Failed to standardize
  permissions on extracted archive`, `Got done processing bundle but
  there were still commands remaining`, `Failed to read next manifest
  command`, `Failed to read manifest source version`, `Hit EOF so
  terminating manifest processing`, `Invalid manifest file at %s`,
  `Got manifest for version "%@", but expected version "%@"`.
- `MIIPAPatcherManifest manifestFromPlistRepresentation:withError:`,
  `plistRepresentationFromData:withError:`, `_manifestErrorForKey:`.
- [CLASS] парсинг недоверенного архива/manifest'а → size/type/EOF-bugs,
  command-loop state-machine bugs, integer issues. Требует разбора
  цикла «read next manifest command» — классический сайт off-by-one /
  underflow при truncated archive. [NEEDS_REVIEW]

### 2.2 Symlink handling при install/patch [OBSERVED→CLASS]
- Строки: `Discovered invalid symlinks in %@`, `Discovered unexpected
  symlinks in %@`, `Found symlink at destination path "%s"; this is not
  allowed.`, `Entity with mode 0%o exists at symlink location in dest
  path %s`, `Can't create symlink`, `Can't read symlink`,
  `Error from helper service creating symlink`, `_extractPackageContainedSymlink:withError:`,
  `realpathForURL:withError:`, `Failed to realpath parent of %s`.
- [OBSERVED] наличие realpath + явной проверки/отказа symlink в dest —
  значит авторы знают о symlink-риске и валидируют.
- [CLASS] TOCTOU между realpath-проверкой и фактической записью:
  realpath разрешает путь в момент T, а rename/write происходит позже —
  если между ними атакующий подменяет компонент пути symlink'ом,
  проверенный путь ≠ записанный. Подтверждение требует показать, что
  между `realpathForURL:` и последующей записью нет повторной проверки /
  что запись идёт по path-string, а не по fd. [NEEDS_REVIEW]
- Связь с 03: запись идёт под gated-путём, но fd-vs-path — открытый вопрос.

### 2.3 NSKeyedUnarchiver / deserialize [OBSERVED→CLASS]
- `Failed to unarchive journal entry data`, `Failed to deserialize
  built-in persona associations`, `Failed to deserialize temporary
  references`, `MIPersonaLifecycleEventJournalEntry`.
- [CLASS] unarchive недоверенных plist'ов. На iOS NSKeyedUnarchiver с
  строгим allowed-class whitelist обычно безопасен; риск — если
  используется без allowedClasses или с широким набором. [NEEDS_REVIEW —
  требует найти `setAllowedClasses`/`requiresSecureCoding` в дизасме]

### 2.4 code-sign / entitlements parse [OBSERVED]
- `verifyBoolEntitlement:`, `parseEntitlements`, `Being asked to
  construct DER entitlements`, `Cannot construct DER entitlements due to
  an entitlement anomaly`, `possibly corrupt XML`,
  `MICopyProcessNameForPid`, `MICodeSigningInfo`.
- [CLASS] расхождение между тем, что парсит пользовательский XML-
  entitlements, и тем, что видит ядро/AMFI при проверке подписи —
  canonical parser-differential. [NEEDS_REVIEW]

## 3. amfid — trust-state data handling

- [OBSERVED] `parseEntitlements`, `AMFIUnserializeXML`,
  `profileAuxSig` → `unable to vm_read profileAuxSig` (проверка
  подписи профиля через vm_read чужой памяти!), `/private/var/db/amfid/
  {UPPCommitting,UPPStaging}.plist`, `metrics.db`.
- [CLASS→ИНТЕРЕСНО] `unable to vm_read profileAuxSig: %d` — amfid
  читает подпись профиля из адресного пространства клиента через
  vm_read. Это классический TOCTOU/double-fetch: содержимое, которое
  amfid проверяет (подпись), живёт в изменяемой клиентом памяти. Если
  профиль валидируется, а потом используется то же буферное содержимое,
  клиент может подменить его между check и use. [NEEDS_REVIEW — сильный
  кандидат; нужно подтвердить, что profileAuxSig копируется до проверки,
  а не читается повторно после неё]

## 4. Сквозные паттерны для 06_FINDINGS
| Класс | Где | Статус |
|---|---|---|
| symlink-in-dest validation без повторной проверки при write | installd realpath→write | NEEDS_REVIEW |
| manifest command-loop truncated/EOF | installd patcher | NEEDS_REVIEW |
| double-fetch через vm_read (profileAuxSig) | amfid | NEEDS_REVIEW (сильный) |
| NSKeyedUnarchiver allowedClasses | installd | NEEDS_REVIEW |
| промежуточные symlink в dirfd-дереве | atc/AirTraffic | NEEDS_REVIEW |
| entitlement XML parser differential | installd/amfid | NEEDS_REVIEW |

След. шаг: 05_VERSION_DIFFS — дифф B2↔B3 по atc/installd/amfid (что
изменилось в проверках, error-handling, file-access), чтобы отделить
«всегда было» от «появилось в B3».
