# evidence — материалы для воспроизводимости

Этот каталог содержит **минимально необходимые** артефакты для проверки
выводов Phase 1–5. Полные дампы дизассемблирования, извлечённые бинарники и
прошивки **не публикуются** (проприетарный код Apple + объём).

## Содержимое

### `entitlements/` — entitlement-блоки подписи кода

XML-plist, извлечённые из `LC_CODE_SIGNATURE` соответствующих бинарников.
Пары `B2`/`B3` позволяют проверить сравнение версий (IOS-SEC-007 и границы
доверия). Имена файлов: `{daemon}_{B2|B3}.entitlements.plist`.

### `protocol_mobileinstaller.txt`

Текст Objective-C протокола `MobileInstallerProtocol` (75 методов), на
который опирается анализ авторизации installd (IOS-SEC-001).

### `disasm-fragments/` — минимальные фрагменты дизассемблирования

Каждый файл помечен источником (бинарь, версия, UUID, адрес). Это **не**
полный дизассемблированный код — только строки, непосредственно цитируемые
в отчётах:

- `amfid_vm_read.txt` — два `vm_read` из разных источников (IOS-SEC-003).
- `hardlink_ops.txt` — точки вызова file-ops в `hardlink_copy_hierarchy`
  (IOS-SEC-004/005): `realpath`, `link`, `mkdir`, `rename`, `unlink`, `chmod`,
  `symlink`, `copyfile`, `mkstemp` — path-based, без `*at` на destination.
- `patch_update_head.txt` — entry `_patchUpdateInstallableForBundle:` и
  проверка installed/placeholder перед передачей `existingBundleContainer`.
- `take_ownership.txt` — `_takeOwnershipOfInstallableContainingSymlink:` →
  `stagingLocationFor...` → `stageItemAtURL:` через helper.
- `standardize_ownership.txt` — callsite `standardizeOwnershipAtURL:toUID:
  GID:removeACLs:setProtectionClass:foundSymlink:error:`.
- `helper_proxy.txt` — `_synchronousRemoteObjectProxyWithErrorHandler:` →
  `stageItemAtURL:` / `moveItemInStagingLocation:` (делегирование в helper-service).

## Как проверять

Адреса (например `0x100002630`, `0x100004260`) — виртуальные адреса внутри
образа (image base `0x100000000`). Чтобы воспроизвести: загрузите тот же
бинарь в дизассемблер и перейдите по адресу. SHA-256 и LC_UUID исходных
образов приведены в `PHASE1/01_INVENTORY.md`, чтобы можно было подтвердить,
что речь идёт о тех же объектах.
