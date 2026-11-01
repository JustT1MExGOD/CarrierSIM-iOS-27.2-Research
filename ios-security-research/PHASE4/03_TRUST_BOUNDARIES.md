# PHASE4 — 03_TRUST_BOUNDARIES: кто может влиять на каталоги/пути installd

Метод: дизасм + entitlements + launchd + provenance путей. Разделяем
**передачу пути** (могу назвать/знать) и **право изменять** (могу писать/
переименовывать) — это разные вещи.

## Провенiens destination-пути для IOS-SEC-004 (delta-patch)

`MIClientConnection installURL:` → `MIInstallable` → `MIInstaller
_patchUpdateInstallableForBundle:manifestPath:existingBundleContainer:`:
- **валидирует** `isPlaceholder`/installed: `patch submitted for application
  %@ that's not installed. Failing.` / `that's just a placeholder. Failing.`
- `existingBundleContainer` резолвится самим installd из установленного app —
  **это не client-supplied path**, а внутренний объект установленного bundle.
- destination = `existingBundleContainer` = контейнер уже установленного
  приложения в домене `com.apple.private.security.storage.AppBundles`.

=> Клиент подаёт **пакет/идентификатор**, installd сам определяет
destination container. Клиент не передаёт сырой путь записи.

## Субъекты и их возможности

| Субъект | передать путь/ID | читать каталог | изменить содержимое | переименовать компонент | изменить родителя |
|---|---|---|---|---|---|
| **installd** (`_installd`) | да (внутренне) | да | да — это его домен | да | да |
| **MobileInstallationHelperService** | via XPC | да (выделенная привилегия) | да (выполняет stage/move) | да | в staging-подсистеме |
| **LaunchServices / InstallCoordination** (`systemgroup.com.apple.installcoordinationd`) | да (process-ограничено) | limited | координирует, не пишет напрямую в AppBundles | — | — |
| **Обычное приложение (mobile)** | может знать свой bundleID/контейнер | только свой data-container | только свой data-container | только внутри своего | нет |
| **Процесс пользователя `mobile`** (atc, dataaccessd и др.) | ограничено | sandbox-зависит | sandbox-зависит, НЕ AppBundles | нет | нет |
| **XPC-клиент installd** (приложение/демон) | передаёт URL/ID запроса | нет (только через installd API) | нет — только просит операцию | нет | нет |

## Ключевой вывод по владению

Destination IOS-SEC-004 (`existingBundleContainer`) находится в домене
`com.apple.private.security.storage.AppBundles`. Запись туда требует либо
быть `installd`/`MobileInstallationHelperService` (владелец домена), либо
обладать entitlement `AppBundles`/`InstallCoordination`. Обычное приложение
и `mobile`-процесс **не имеют write-доступа** к чужому bundle-контейнеру
(каждое app ограничено своим data-container'ом через sandbox + container
model; `com.apple.private.security.system-application`/`container-required`
разграничивают это).

## Два независимых уровня защиты для delta-patch

1. **Entitlement/XPC-уровень:** право инициировать patch-update ограничено
   (InstallCoordination/privileged клиенты; `_patchUpdateInstallable` —
   внутренний).
2. **Filesystem/DAC-уровень:** запись в AppBundles-домен — только installd/
   helper. Проверка installed/placeholder гарантирует, что destination —
   легитимный контейнер.

## Что НЕ подтверждено (честно)

- Точный sandbox-профиль installd (seatbelt) — есть `seatbelt-profiles`
  entitlement, но сам .sb-профиль не декомпилирован → граница описана по
  entitlement/DAC-модели, не по тексту профиля.
- Может ли **другой процесс с `AppBundles`-entitlement** или
  `InstallCoordination` писать в тот же контейнер конкурентно — теоретически
  да (coordinating daemons), но все они — trusted system daemons, не
  непривилегированный субъект. Для TOCTOU нужен **недоверенный** субъект
  с write — такого в домене AppBundles нет.
- `mobile`-демоны с широкими entitlements (atc и др.) — НЕ имеют
  `AppBundles`/InstallCoordination write → не являются TOCTOU-субъектами.

## Вывод

Для IOS-SEC-004 **нет непривилегированного субъекта**, способного легитимно
изменять `existingBundleContainer` или его родителя между проверкой и
операцией. Граница доверия закрыта на уровне entitlement + DAC + container
model: единственные writers — installd и его привилегированные
helper-service, входящие в ту же trust-domain.
