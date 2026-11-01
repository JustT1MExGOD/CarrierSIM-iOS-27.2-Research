# RESEARCH_SUMMARY — итог Phase 1: security-исследование iOS 27.2+

Дата/режим: полностью офлайн, без устройства, без фаззинга, без эксплойтов.
Все объекты — из `C:\ipsw-tools`. Документы: 01_INVENTORY, 02_TRUST_BOUNDARIES,
03_IPC_SECURITY_REVIEW, 04_DATA_HANDLING_REVIEW, 05_VERSION_DIFFS,
06_FINDINGS, 07_RESEARCH_PRIORITIES.

Метод, который всё это сделал возможным: `ipsw.exe macho disass` разрешает
`bl`-цели в имена ObjC-методов/символов → per-method аудит авторизации
выполняется по факту вызова валидатора, а не по догадке. Полные дизасмы:
`installd_B2/B3_disasm.txt`, `amfid_B2/B3_disasm.txt`, `atc_B2/B3_disasm.txt`.

---

## 1. Что изучено

- 9 исполняемых Mach-O (atc / amfid / installd × B2+B3, AirTraffic `__text`),
  оба kernelcache, оба sandbox-kext, dyld-кэш (82 файла), launchd-plists,
  entitlement-наборы.
- IPC/XPC-поверхность installd (`MIClientConnection`, ~97 методов) и amfid
  (`AMFIService`, ~17 методов) — построчно по авторизации.
- Обработка недоверенных данных: IPA/zip+manifest (installd), подписи
  профилей через vm_read (amfid), host-пути (atc/AirTraffic).
- Построечный дифф B2↔B3 на уровне отдельных функций.

## 2. Доступные компоненты (что реально есть под рукой)

- Сильное: atc, amfid, installd — полные ObjC-классы/методы, символы.
- Среднее: AirTraffic `__text`-срез (move-рутина разобрана, символы —
  signature-matched из-за пустого `.dyldlinkedit`).
- Не разобрано: kernelcache (filetype=12, нужна распаковка kext),
  sandbox-kext (Seatbelt-профиль), CommCenter/fileproviderd/dataaccessd/
  streaming_zip_conduit (бинари не извлечены — только plists/строки).
- Пробелы: нет XNU-заголовков, нет RC-бинарей, dyld-symbols = 0 байт.

## 3. Потенциальные проблемы (кандидаты, все NEEDS_REVIEW — без CVE-заявлений)

1. **installd accept-all XPC** — `shouldAcceptNewConnection:` возвращает 1
   безусловно, без проверки (HIGH факт). Авторизация per-method, покрытие
   неравномерное (68 gated / 29 нет; install/uninstall транзитивно закрыты).
   → IOS-SEC-001/002.
2. **amfid `vm_read profileAuxSig`** — читает подпись профиля из адресного
   пространства клиента. Виден одноразовый copy-out (вероятно защитный),
   но нужно подтвердить отсутствие double-fetch. → IOS-SEC-003.
3. **installd manifest command-loop** — ручной цикл над недоверенным
   архивом; поверхность для parser/state-bugs. → IOS-SEC-004.
4. **installd realpath→write TOCTOU** — есть realpath+symlink-валидация,
   но не доказано fd-anchored запись. → IOS-SEC-005.
5. **AirTraffic intermediate-symlink** — RENAME_NOFOLLOW только на
   final-component; семантика промежуточных symlink зависит от root-fd.
   → IOS-SEC-006.
6. Низкоприоритетные: entitlement-XML differential (IOS-SEC-007),
   NSKeyedUnarchiver allowedClasses (IOS-SEC-008).

## 4. Опровергнутые предположения (честный минус)

- **amfid uneven gating** — опровергнуто: ВСЕ mutating-методы зовут
  `verifyBoolEntitlement:`; покрытие консистентное.
- **atc несёт фикс Airlock** — опровергнуто: atc B2≡B3; фикс в AirTraffic.
- **amfid изменился в B3** — опровергнуто: инструкции идентичны.
- **installd ослабил авторизацию в B3** — опровергнуто: валидаторы не
  менялись; изменения = усиление (extension-validation, app-replacement).

## 5. Топ-3 обоснованных направления (доказуемость + значимость)

1. **amfid `vm_read` double-fetch (P1)** — самый дешёвый: одна функция
   `sub_100004030`, бинарный вердикт (двойное чтение → дефект; copy-out →
   RULED_OUT). Полностью офлайн.
2. **sandbox-профиль AirTraffic B2↔B3 (P1)** — извлечь Seatbelt-профиль из
   `com.apple.security.sandbox`, дифф B2/B3. Докажет, где живёт errno-107
   confinement: sandbox-политика vs VFS. Ключ к пониманию границы.
3. **installd no-gate методы (P2)** — разобрать `triggerRegistrationFor*` /
   `referencesForBundle`/`getPidForTesting`: делают ли привилегированное
   действие без gate, и кто имеет bootstrap-доступ к сервису.

## 6. Каких материалов не хватает (для повышения уверенности)

- **XNU/Darwin-заголовки** (errno-константы, open-флаги, sandbox API) —
  заменили бы предположения именами.
- **Распакованный kernelcache + декомпилированный Seatbelt-профиль** —
  для доказательства confinement-механизма (P1).
- **Бинари CommCenter / fileproviderd / dataaccessd /
  streaming_zip_conduit** — расширить IPC-аудит за пределы installd/amfid.
- **RC-сборки** (27.2 RC 24B119) — проверить, что B3-изменения дошли до RC.
- **dyld `.dyldlinkedit`/`.symbols` непустые** — снять signature-vs-symbol
  ограничение на имена stub-targets.

## Итоговая оценка

Ни один кандидат не поднят до уровня CONFIRMED-уязвимости — это корректно
для статического офлайн-прохода без XNU-заголовков и без устройства.
Получено: (а) твёрдо доказанная архитектура авторизации installd
(accept-all + частичный per-method gating), (б) чисто опровергнутые
гипотезы по amfid/atc, (в) точный построечный дифф, (г) 2 направления P1
с ясным офлайн-путём к бинарному вердикту. «Серьёзной уязвимости» по ТЗ
не обнаружено — если бы была, она осталась бы локальной с планом
ответственного раскрытия; таковой нет.
