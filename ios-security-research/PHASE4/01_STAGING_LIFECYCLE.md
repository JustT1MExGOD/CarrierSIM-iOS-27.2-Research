# PHASE4 — 01_STAGING_LIFECYCLE: жизненный цикл staging-каталогов installd

Метод: статический дизасм `installd_B3.bin` (UUID F54A48D1-4E77-3425-BEAB-5EBBBB037C0F,
SHA-256 `1dd5efbf…064b1d`). Имена методов — реальные ObjC selrefs.
Важно: в `installd` есть ДВА разных staging-механизма — их нельзя смешивать.

## Два staging-пути (различить!)

| | Свежий install/stage | Delta-patch update (IOS-SEC-004) |
|---|---|---|
| Метод | `stageItemAtURL:toStagingLocation:` | `hardlink_copy_hierarchy` ← `-[MIInstallable _applyDeltaPatchWithError:]` |
| Кто выполняет | **`MIHelperServiceClient` → `_synchronousRemoteObjectProxyWithErrorHandler:` → helper-service XPC** | **installd сам, in-process** (`bl 0x100002630`) |
| Назначение | Стадировать новый bundle до установки | Применить delta к **уже установленному** bundle |
| Объект path | уникальный staging-каталог (`MIStagingLocation`) | `existingBundleContainer`/`bundleURL` установленного приложения |

=> IOS-SEC-004 НЕ использует `MIStagingLocation`-жизненный цикл. Он работает
напрямую внутри bundle-контейнера уже установленного приложения.

## Жизненный цикл staging-каталога (общий, для stage-пути)

1. **Создание:** `MIStagingLocation stagingLocationFor{InstallLocation|URL|SystemContent|UserContent}:withinStagingSubsystem:usingUniqueName:` —
   выбирает уникальное имя и расположение; реальный mkdir делегирован
   helper-service через `stageItemAtURL:`/`moveItemInStagingLocation:`.
2. **Инициатор:** `MIInstaller` / `MIInstallable` install/stage-path.
3. **Формирование пути:** `MIStagingLocation` объект — расположение
   выбирает subsystem (`withinStagingSubsystem`), имя через `usingUniqueName`
   (server-generated, не из входных данных клиента).
4. **Кто выбирает имя:** helper-service (subsystem) — `stagingLocationForURL:…
   usingUniqueName:` — имя генерируется сервисом, не клиентом.
5. **Под каким пользователем:** `_installd` (daemon) для installd-части;
   helper-service — отдельный привилегированный контекст.
6. **Права/владелец:** `_takeOwnershipOfInstallableContainingSymlink:error:` →
   `Failed to transfer ownership of path %@ to installd` — **installd
   забирает владение** staged-bundle; `standardizeOwnershipAtURL:toUID:GID:
   removeACLs:setProtectionClass:` (в MobileInstallation.framework) выставляет
   uid/gid/mode/ACL.
7. **Временные каталоги:** `MIIPAPatcherFileManager createTempDirectoryWithPrefix:
   relativeToURL:mode:` — `mkdtemp("%@.XXXXXX")` + `chmod` + `Could not chmod
   newly created temp directory` — временный dir с генерируемым именем.
8. **Передача между процессами:** `moveItemInStagingLocation:atRelativePath:
   toDestinationURL:onBehalfOf:` — helper-service перемещает элементы внутри
   staging «on behalf of» installd; `transferOwnershipOfSandboxExtensionToCaller`
   — sandbox-extension может переходить caller'у (точечная передача прав).
9. **Удаление:** `wipeStagingRootAndSetUpPerUserDataDirWithError:`,
   `Failed to remove temporary staging directory`, `_DestroyContainerIfTemporary`
   — staging root вытирается после завершения/при пер-юзер setup.

## Для IOS-SEC-004 — destination это НЕ staging-каталог

`_applyDeltaPatchWithError:` → `hardlink_copy_hierarchy(existingBundleContainer,
manifestURL, versions, execURL)`. Destination = `existingBundleContainer` —
существующий установленный app-bundle (не временный staging). Это меняет
весь вопрос TOCTOU: мутация должна происходить в **постоянном
bundle-контейнере приложения**, а не в свежем temp-dir.

## Уровни уверенности

- Два staging-пути различены, делегирование через XPC — CONFIRMED (disasm).
- `hardlink_copy_hierarchy` работает на `existingBundleContainer` — CONFIRMED.
- Точные uid/gid/mode/ACL staging-каталогов — NOT VERIFIED (MobileInstallation.
  framework не извлечён; `_takeOwnership` подтверждает передачу владения
  installd, но не конкретный uid/mode).
