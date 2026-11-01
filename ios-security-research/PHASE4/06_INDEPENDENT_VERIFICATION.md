# PHASE4 — 06_INDEPENDENT_VERIFICATION: проверка архитектурных предположений

Независимая перепроверка фактов, на которых держится вывод Phase 3/4.
Разделено: подтверждено локальным материалом / общее знание Darwin / пробел.

## 1. Принадлежат ли staging/destination-каталоги `_installd`?

- **Подтверждено:** `Daemon's home directory at %@ should be owned by uid %u`
  + `should have gid %u` + `was not a directory; found mode 0%ho` —
  installd верифицирует uid/gid/mode собственного daemon-container'а.
- **Подтверждено:** `_takeOwnershipOfInstallableContainingSymlink:` →
  `Failed to transfer ownership of path %@ to installd` — installd
  забирает владение staged-bundle.
- **Подтверждено (entitlement):** `com.apple.private.security.storage.AppBundles`
  — installd владеет доменом AppBundles (там — installed bundles).
- Для delta-patch (IOS-SEC-004) destination = `existingBundleContainer`
  — уже-установленный app bundle в том же домене. CONFIRMED по
  `patch submitted for application %@ that's not installed` —
  проверка существования установленного bundle.
- Уровень: HIGH (строки+disasm+entitlement), точный uid/mode —
  NOT VERIFIED (нет root FS listing прав на этих каталогах локально).

## 2. Могут ли другие системные процессы работать с этими каталогами?

- Подтверждено: `stageItemAtURL`/`moveItemInStagingLocation`/`wipeStagingRoot`
  — **XPC-делегация в MobileInstallationHelperService** (другой процесс,
  привилегированный). То есть не только `installd` пишет в staging —
  helper-service тоже, но он в той же trust-domain.
- InstallCoordination (`systemgroup.com.apple.installcoordinationd`) —
  coordinating daemon, в той же privileged group.
- Обычные apps/`mobile`-демоны — НЕ имеют write в AppBundles/
  InstallCoordination (см. 03). Это общее знание container-model +
  entitlement, не прямой дамп sandbox-профиля → INFERRED HIGH, не
  header-сonfirmed.

## 3. Дополнительные проверки в вызывающих функциях?

- `_patchUpdateInstallableForBundle:` — `isPlaceholder`/installed check
  перед построением `MIInstallableBundle` (`patch submitted for application
  that's not installed`/`just a placeholder. Failing.`). ✅
- `MIInstallableBundle performVerification` / `_validateBundle:` —
  code-sign/entitlement validation до apply. ✅ (имена методов видны)
- `validate_supported_devices` + infoPlistHash memcmp внутри
  `hardlink_copy_hierarchy`. ✅

## 4. Выполняются ли file-ops через безопасные fd-интерфейсы?

- **Нет.** Проверено перечислением всех file-op импортов `installd_B3`:
  `link, mkdir, rename, renamex_np, unlink, chmod, symlink, readlink,
  copyfile, fcopyfile, lstat, stat, realpath, mkstemp, mkdtemp, open,
  fopen, fts_*, fchmod, fstat, getattrlist` — **ни одного `*at`/dirfd-
  anchored вызова** в весь бинарь. Это прямо противоположно AirTraffic B3
  (open(dirfd)+mkdirat+renameatx_np+unlinkat). CONFIRMED HIGH.
- Следствие: installd работает path-based в своём домене; fd-anchored
  confinement нужен AirTraffic, потому что его root — shared/writable
  `/var/mobile/Media`, а installd-домен приватен. Архитектурное различие
  объясняет, почему AirTraffic нужен dirfd+jail, а installd — нет.

## 5. Не ошибочно ли интерпретированы символы/имена в прошлых отчётах?

- Имена ObjC-методов/классов — реальные selrefs (CONFIRMED).
- Имена C-функций (`hardlink_copy_hierarchy`, `read_next_manifest_command`,
  `read_bytes`, `make_and_check_dest_path`, `realpath_parent_no_symlink`,
  `open_delta_manifest`, `validate_stream`, `patch_file`,
  `_CreateAndLogDMError`) — из embedded error/log строк `__func__`,
  надёжны как internal names, НЕ external symbols. Помечено MEDIUM для
  `patch_file` (не разобран) и validate_stream (helper).
- `sub_*`/`func_*` адреса — точные.
- `renamex_np` — import-символ (в chained fixups), CONFIRMED имя.
- Символы dyld-cache — signature-matched (`.dyldlinkedit`=0B), НЕ resolved.

## 6. Проверка на подмену/несоответствие

- Никаких признаков, что `bl` в `hardlink_copy_hierarchy` указывает не на
  move-routine: цепочка вызовов + строки согласованы (`Making directory`,
  `Hardlinking`, `Setting final perms`, `link`, `mkdir`, `rename`, `chmod`).
- `existingBundleContainer`/`bundleURL`/`manifestURL` — ObjC-свойства,
  достающиеся из `MIInstallable`/`MIInstaller` — не client-controlled
  path-string, а внутренний резолв установленного bundle. CONFIRMED.

## Итог независимой проверки

Все ключевые архитектурные предположения Phase 3/4 выдерживают проверку;
единственные пробелы — точные uid/mode/ACL staging (в MobileInstallation.
framework) и sandbox-профиль (не декомпилирован). Это документируемые
NOT VERIFIED, не подменённые факты.
