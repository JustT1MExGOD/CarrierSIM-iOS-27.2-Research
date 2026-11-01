# PHASE4 — 02_DIRECTORY_PERMISSIONS: права доступа к каталогам/объектам

Метод: строки + дизасм `installd_B3.bin`. Различать: подтверждённый вызов +
контекст vs предполагаемое право. Не выводить права только из `_installd`.

## 1. Подтверждённые файловые операции и их семантика

### В `hardlink_copy_hierarchy` (`sub_100002630`, IOS-SEC-004)
Все ops — **path-based** (ни одного `*at`/fd-anchored):
- `link` @0x100002fcc — создание hardlink (дельта-копия существующего файла).
- `mkdir` @0x100003170 — создание каталога.
- `rename` @0x10000320c — атомарная замена patched-файла.
- `unlink` @0x10000321c.
- `chmod` @0x1000030a8, @0x1000032f8 — установка прав (`Setting final perms`,
  `Failed to make destination directory "%s" writable`).
- `symlink` @0x1000030f8, `readlink` @0x1000030d8, `copyfile` @0x100003040.
- `mkstemp` @0x100002d7c, `fchmod` @0x1000031f0, `close`, `fts_*`.

**Защита путей перед этими ops:** `make_and_check_dest_path`
(`snprintf("%s/%s")` ≤0x400), `realpath_parent_no_symlink` (`realpath`
родителя + `lstat` + `Found symlink at destination path ... not allowed`),
`realpath'd destpath is different from non-realpath`, entity-type check
(`Entity with mode 0%o exists at ... not allowed`, `Non-directory entity
with mode 0%o exists at directory location`).

### В `createTempDirectoryWithPrefix:` (MIIPAPatcherFileManager, 0x10000679c)
`mkdtemp("%@.XXXXXX")` → `chmod` на новый каталог → `Could not chmod newly
created temp directory`. Временный каталог с генерируемым именем, права
выставляются немедленно chmod'ом — то есть не полагаются на umask.

### В staging/ownership path (MIInstaller / helper-service)
- `standardizeOwnershipAtURL:toUID:GID:removeACLs:setProtectionClass:
  foundSymlink:error:` — **явно принимает `foundSymlink` out-параметр** —
  обнаруживает symlink при стандартизации владения. (В MobileInstallation.
  framework — точные uid/gid/mode не восстановлены.)
- `_takeOwnershipOfInstallableContainingSymlink:error:` — передача владения
  staged-bundle **в installd** (`Failed to transfer ownership of path %@
  to installd`).
- `Daemon's home directory at %@ should be owned by uid %u, but found %u`
  / `should have gid %u, but found %u` / `was not a directory; found mode:
  0%ho` — installd **верифицирует uid/gid/mode своего home/container**.

## 2. Начальные права, umask, владелец

- Для temp-dir — mkdtemp + явный `chmod` (не зависит от umask). ✅
- Для staged-bundle — `standardizeOwnershipAtURL:toUID:GID:removeACLs:
  setProtectionClass:` — явная установка uid/gid/mode/ACL/protection-class.
  ✅ (точные значения — в framework, NOT VERIFIED).
- Владелец: `_installd` для daemon-container; `com.apple.private.security.
  storage.AppBundles` entitlement — **installd владеет доменом AppBundles**
  (там лежат installed app bundles, включая `existingBundleContainer`).

## 3. ACL / дополнительные ограничения

- `standardizeOwnershipAtURL:...removeACLs:` — ACL явно удаляются при
  стандартизации → исключается унаследованный ACL, дающий сторонний write.
- `setProtectionClass:` + `data-protection-class` — Data Protection class
  выставляется на контент.
- `com.apple.private.security.system-application`, `daemon-container`,
  `no-container` — entitlement-модель container'ов.

## 4. Проверки доступа к родительским каталогам

- `realpath_parent_no_symlink` — realpath **родителя** dest-пути +
  `lstat` + `Found symlink ... not allowed`. То есть symlink в родителе
  цепочки явно отклоняется. ✅
- `Failed to make destination directory "%s" writable` — есть шаг
  установки writable на dest-родителя перед записью. ✅
- `realpath'd destpath is different from non-realpath` — resolved-path
  должен совпадать с запрошенным (anti-redirect).

## 5. Использование уже открытых FD

- В `hardlink_copy_hierarchy` — только path-ops, fd используется для
  `fstat`/`fchmod`/`close`/`mmap` манифеста и для `mkstemp`-tempfile.
  **Нет fd-anchored операций на destination** — это подтверждает, что
  проверка→использование идёт по path-string, а не по dirfd. (См. 04 —
  это и есть TOCTOU-класс, но его эксплуатируемость определяется владельцем.)

## 6. Символические ссылки

- `Found symlink at destination path "%s"; this is not allowed.`
- `Entity with mode 0%o exists at symlink location in dest path %s`
- `standardizeOwnershipAtURL:...foundSymlink:` — foundSymlink out-param.
- `realpath_parent_no_symlink` — родительская цепочка проверяется.
- `Can't create symlink`, `Can't read symlink`, `Discovered invalid symlinks`,
  `Discovered unexpected symlinks` — контроль создания/чтения symlink.

## Вывод по правам

Права на destination (existingBundleContainer в домене AppBundles) принадлежат
`_installd`/`installd`-домену; standardizeOwnership + removeACLs + явный chmod
на temp-dir исключают унаследованный доступ. Проверки пути реальны, но
path-based ops создают теоретическое TOCTOU-окно — его закрытость зависит
от того, кто ещё может писать в этот домен (см. 03).
