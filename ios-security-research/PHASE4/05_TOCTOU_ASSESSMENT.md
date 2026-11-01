# PHASE4 — 05_TOCTOU_ASSESSMENT: проверка гипотезы TOCTOU по 4 условиям

Оценка IOS-SEC-004 (delta-patch `hardlink_copy_hierarchy`) и смежного
IOS-SEC-005 (общий realpath→write). Каждое условие — CONFIRMED /
NOT VERIFIED / CONTRADICTED, с конкретным основанием.

## Условие 1 — Разделённые операции (check ≠ use)

**CONFIRMED.** `realpath`/`lstat`/entity-type/symlink-parent проверки
(`realpath_parent_no_symlink`, `make_and_check_dest_path`) идут в момент T,
а file-op (`link`/`mkdir`/`rename`/`chmod`/`symlink`/`unlink`/`copyfile`)
выполняется по той же path-string позже, без fd-anchored привязки.
Это и есть разделение check и use. Адреса/вызовы: см. 04.

## Условие 2 — Изменяемое состояние (может ли проверенный объект измениться)

**CONFIRMED (структурно).** Объект destination (`existingBundleContainer`)
существует как файловый путь, не как открытый fd — его компоненты могут быть
переименованы/подменены symlink'ом между `realpath`-проверкой и `rename`/
`link`/`chmod`, **при наличии** субъекта с правом записи в родительский
каталог. Отсутствие `RENAME_NOFOLLOW`/`*at`-ops оставляет техническое окно.

## Условие 3 — Доступный субъект (есть ли кто-то с подтверждёнными правами изменять)

**CONTRADICTED.** Для изменения `existingBundleContainer` нужен write в
домен `com.apple.private.security.storage.AppBundles`:
- Этот домен принадлежит `_installd`/`installd` + MobileInstallationHelperService.
- `mobile`-apps ограничены своим data-container'ом (container model + sandbox);
  у них нет write в чужой bundle-container.
- XPC-клиенты installd передают пакет/ID, не получают write-FD в AppBundles.
- Другие потенциальные writers (InstallCoordination) — trusted system daemons
  в той же trust-domain, не недоверенный субъект.
- `Daemon's home directory at %@ should be owned by uid %u` — installd
  верифицирует свою собственность домена.
=> **Нет непривилегированного субъекта с легитимным write в проверяемый путь.**
Это ключевое опровержение: окно есть только для того, кто уже в trust-domain
(тогда TOCTOU не повышает привилегии — он уже privileged).

## Условие 4 — Значимое последствие (может ли изменение повлиять на результат)

**NOT VERIFIED (условно).** Даже при гипотетической подмене: патч применяет
delta к уже установленному bundle — результат ограничен тем, что patch
может сделать (hardlink/copy/perm-change внутри app-bundle). Для значимого
эффекта (запись вне bundle, escalation) нужна подмена на sensitive-path
вне AppBundles — а anti-symlink `realpath'd destpath different` + lstat
блокируют выход за пределы. Значимость ограничена внутри trust-domain.

## Вердикт по 4 условиям

| Условие | Статус | Основание |
|---|---|---|
| Разделённые операции | CONFIRMED | path-check then path-use, no fd anchor |
| Изменяемое состояние | CONFIRMED (структурно) | path объект, не locked-fd |
| Доступный субъект | **CONTRADICTED** | нет непривилегированного writer в AppBundles |
| Значимое последствие | NOT VERIFIED | эффект ограничен доменом; выход за него — anti-symlink |

## Итог

Гипотеза TOCTOU **не подтверждается как реальная уязвимость**: хотя
разделение check/use структурно существует (условие 1) и состояние
теоретически изменяемо (условие 2), **необходимое условие 3 — наличие
непривилегированного субъекта с правом на изменение — опровергнуто**.
Домен AppBundles закрыт для всех, кроме installd и его trusted helpers;
то есть TOCTOU мог бы выполнить только тот, кто уже имеет privileged write,
что не создаёт повышения привилегий.

Последовательность `realpath→path-op` здесь — **безопасная часть штатной
архитектуры**: она работает внутри installd-владельца, где контролирующий
субъект и защищаемый объект в одной trust-domain. Это не race для
внешнего атакующего.
