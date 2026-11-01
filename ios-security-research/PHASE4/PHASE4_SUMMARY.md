# PHASE4_SUMMARY — installd Filesystem Trust Boundaries (TOCTOU)

Режим: статический офлайн-анализ. Объект: `installd_B3.bin` (B3, arm64e;
UUID F54A48D1-4E77-3425-BEAB-5EBBBB037C0F, SHA-256 `1dd5efbf…064b1d`).
Документы: 01_STAGING_LIFECYCLE, 02_DIRECTORY_PERMISSIONS, 03_TRUST_BOUNDARIES,
04_OPERATION_SEQUENCE, 05_TOCTOU_ASSESSMENT, 06_INDEPENDENT_VERIFICATION,
07_FINDINGS_ASSESSMENT.

Главный вопрос Phase 4: есть ли **реальная граница доверия**, на которой
возможна TOCTOU-ошибка в `realpath→path-op`, или это безопасная штатная
архитектура. Ответ: **границы для непривилегированного субъекта нет —
последовательность безопасна**.

## 1. Карта жизненного цикла staging

ДВА механизма (не смешивать):
- **Stage-путь** (свежий install): `MIStagingLocation` + XPC-делегирование в
  `MobileInstallationHelperService` (`stageItemAtURL`/`moveItemInStagingLocation`/
  `wipeStagingRoot`) → `standardizeOwnershipAtURL:toUID:GID:removeACLs:
  setProtectionClass:foundSymlink:` → `_takeOwnership…to installd` →
  `wipeStagingRoot`. Имя — server-generated (`usingUniqueName`).
- **Delta-patch (IOS-SEC-004):** `hardlink_copy_hierarchy` работает in-process
  installd на `existingBundleContainer` — уже-установленный bundle, не temp-dir.
  `mkdtemp` только для temp-dir в patcher, с явным `chmod`.

## 2. Владельцы/группы/права

| Объект | Владелец | Источник |
|---|---|---|
| daemon home/container | `_installd` (верифицируется uid/gid/mode) | `should be owned by uid %u` |
| AppBundles домен | installd (`com.apple.private.security.storage.AppBundles`) | entitlement |
| staged-bundle | передаётся **в installd** | `_takeOwnership`/`transfer ownership to installd` |
| temp-dir | mkdtemp+chmod (не umask) | `Could not chmod newly created temp dir` |
| ACL | удаляются при стандартизации | `standardizeOwnership…removeACLs` |

## 3. Последовательность проверка→использование

`realpath(parent)+lstat → realpath'd-vs-rawpath compare → symlink-parent
reject → entity-type match → path-op`. Все file-ops **path-based**
(`link`/`mkdir`/`rename`/`unlink`/`chmod`/`symlink`/`copyfile`); ни одного
`*at`/fd-anchored вызова во всём `installd` (проверено импортами).
`rename`/`mkstemp` — атомарны для содержимого; path-check→op — нет.

## 4. Модель границ доверия

- Пишет в AppBundles только installd + MobileInstallationHelperService
  (та же trust-domain) + InstallCoordination.
- `mobile`-apps: только свой data-container; `mobile`-демоны (atc и др.):
  нет AppBundles/InstallCoordination write.
- XPC-клиенты: передают пакет/ID; destination резолвится installd'ом
  (`existingBundleContainer`), не client-path.
- Валидация: `patch submitted for application that's not installed`/
  `just a placeholder` — destination подтверждается легитимным.

## 5. TOCTOU — 4 условия

| Условие | Статус |
|---|---|
| Разделённые операции | CONFIRMED |
| Изменяемое состояние | CONFIRMED (структурно) |
| Доступный субъект | **CONTRADICTED** — нет недоверенного writer |
| Значимое последствие | NOT VERIFIED |

=> Гипотеза не реализуется: необходимое условие опровергнуто.

## 6. Итоговые статусы

- **IOS-SEC-004 → RULED OUT** (TOCTOU не реализуется: нет недоверенного
  субъекта с write в AppBundles; окно только для уже-privileged).
- **IOS-SEC-005 → ARCHITECTURAL OBSERVATION** (anti-symlink проверки в
  своём домене — штатная защита, не дефект).

## 7. Противоречия с Phase 3

- Phase 3 пометила TOCTOU как «стоящий класс-риск». Phase 4 уточняет:
  класс структурно есть, но **нет субъекта** → это безопасная архитектура,
  не дефект. Это уточнение, не противоречие фактов — статус понижен по
  результату проверки субъекта.
- Phase 3 `INSUFFICIENT EVIDENCE` для IOS-SEC-004 → Phase 4 даёт более
  сильный `RULED OUT` по подтверждённому отсутствию субъекта.

## 8. Недостающие доказательства (честные пробелы)

- Точные uid/gid/mode/ACL staging-каталогов (в MobileInstallation.framework,
  не извлечён) — предполагается installd-daemon, подтверждено takeOwnership.
- Декомпилированный Seatbelt-профиль installd (есть entitlement `seatbelt-profiles`,
  сам профиль не разобран) — граница описана по entitlement/DAC, не по .sb.
- Возможность race от **другого privileged** процесса (не недоверенного) —
  не является повышением привилегий и не входит в TOCTOU-threat.

## 9. Рекомендация

**Закрыть гипотезу** по IOS-SEC-004/005. TOCTOU-класс здесь не даёт
повышения привилегий, потому что контролирующий и защищаемый объект в
одной trust-domain (installd/AppBundles). Дальнейший поиск на этой
поверхности не имеет обоснованного threat-model без нового субъекта,
способного писать в installd-домен — а такого в модели нет.

Единственное разумное дальнейшее направление (вне IOS-SEC-004): если нужен
полный аудит — разобрать `patch_file` (единственный недоисследованный
helper в `hardlink_copy_hierarchy`) и `MIIPAPatcherFileManager` file-ops —
но и там домен остаётся installd'ом, что сохраняет тот же вердикт.
