# 07_RESEARCH_PRIORITIES — приоритизация дальнейшего исследования

Оценка каждого направления по: (а) доступности доказательств офлайн,
(б) независимой верифицируемости, (в) трудоёмкости анализа,
(г) значимости класса дефекта, (д) силе альтернативных объяснений.
НЕ оценивается по «полезности для обхода CarrierSIM» — только по
security-значимости и доказуемости.

Ранги: P1 — высший приоритет (делать первым), P2 — средний, P3 — низкий.

---

## P1 — ядро / sandbox-kext: где именно возникает errno 107

**Почему первым.** Это единственное место, где можно *доказать* реальный
механизм confinement (а не предполагать). errno 107 «Capabilities
insufficient» — это отказ sandbox/capability-подсистемы ядра. Понять, что
именно проверяется (dirfd-jail? chroot? vnode-scope? отдельный
AFC-allowlist?), — значит понять, есть ли вокруг него обходной путь
(другой syscall, другой fd-тип, флаг, intermediate-symlink).

- Доказательства: `beta{2,3}/…/kernelcache.release.iPhone16,1`,
  `beta{2,3}/sandbox/com.apple.security.sandbox`.
- Трудоёмкость: ВЫСОКАЯ — kernelcache filetype=12 требует распаковки
  kext-секций/prelinked-info; sandbox-kext — бинарный профиль Seatbelt.
- Верифицируемость: дифф B2↔B3 sandbox-профиля покажет, добавили ли
  правило для AFC-root (если да — политика, а не код).
- Альтернативы: проверка может быть в VFS/namei, а не в sandbox —
  различить это и есть задача.
- **Следующий конкретный шаг:** извлечь из `com.apple.security.sandbox`
  профиль `AirTraffic` (на него ссылается entitlement `seatbelt-profiles`
  у atc) и сравнить B2↔B3. Если в B3 появилось правило на выход за
  `/var/mobile/Media` — механизм подтверждён как sandbox-политика.
- Риск застревания: средний (парсер Seatbelt-профилей нетривиален, но
  формат частично известен).

## P1 — IOS-SEC-003: amfid `vm_read`-from-client double-fetch

**Почему.** Самый конкретный memory-safety/TOCTOU кандидат с видимым кодом.
Разрешим полностью офлайн одним чтением функции `sub_100004030`.

- Доказательства: `amfid_B3_disasm.txt`, функция `sub_100004030`
  (все 4 `vm_read` + `profileAuxSig`).
- Трудоёмкость: НИЗКАЯ — одна функция, ~200 инструкций.
- Верифицируемость: если буфер читается дважды или используется после
  валидации указатель на чужую память — это класс-дефект; если одноразовый
  copy-out + валидация по копии — RULED_OUT. Чёткий бинарный вердикт.
- Альтернативы: сильные (copy-out — стандартная защита); поэтому статус
  NEEDS_REVIEW, а не подозрение на дыру.
- **Шаг:** разобрать `sub_100004030` целиком — куда девается `x20`/`x27`
  (out-params), валидируется ли содержимое до или после второго vm_read.

## P2 — IOS-SEC-001/002: installd неравномерный gating + no-gate методы

**Почему.** Структура подтверждена, но эксплуатируемость зависит от того,
кто может сделать bootstrap-lookup `com.apple.mobile.installd`, и что
делают no-gate методы (`triggerRegistrationFor*`).

- Доказательства: `installd_B3_disasm.txt`, launchd plist, entitlements.
- Трудоёмкость: СРЕДНЯЯ — нужно (а) разобрать тело
  `triggerRegistrationForContainerizedContentForOptions:` —
  запускает ли оно привилегированное действие без gate; (б) понять,
  какие клиенты имеют bootstrap-доступ (это решает, реальна ли граница).
- Верифицируемость: статическая — показать в коде, что no-gate метод
  вызывает privileged-op напрямую.
- Альтернативы: сильные — `com.apple.private.MobileInstallationHelperService.allowed`
  и bootstrap-ограничение делают сервис недоступным для обычных app.
- **Шаг:** дизассемблировать `triggerRegistrationFor*` и
  `referencesForBundleWithIdentifier:` полностью; зафиксировать, какое
  привилегированное действие они делают и есть ли gate ниже по стеку.

## P2 — IOS-SEC-006: тип root-fd + intermediate-symlink в AirTraffic

**Почему.** Дозакрывает модель confinement. RENAME_NOFOLLOW — только
final-component; поведение промежуточных symlink зависит от root-fd.

- Доказательства: `AirTraffic_text_B3.bin` (move-рутина), уже есть дизасм.
- Трудоёмкость: НИЗКАЯ-СРЕДНЯЯ — определить, как открывается root-fd
  (`open(path,0x40100000)` — что за path? dirfd от chdir/chroot?),
  и резолвит ли ядро intermediate-symlink через тот же vnode-scope.
- Верифицируемость: HIGH — разбор open-callsite.
- **Шаг:** найти callsite `open` → root-fd; определить `0x40000000` флаг
  (O_EXECONLY? O_NOFOLLOW_ANY? private flag). Частично пересекается с P1.

## P3 — IOS-SEC-004: manifest command-loop (installd)

**Почему третьим.** Реальная поверхность (недоверенный архив → цикл команд),
но архив доходит до installd по gated install-path — то есть нужен
способ подать malformed IPA, что само по себе требует примитива.

- Трудоёмкость: ВЫСОКАЯ (цикл команд + state machine).
- Верифицируемость: статическая, но нужно показать конкретный underflow/OOB.
- **Шаг:** разобрать loop `read next manifest command` → проверка длины
  перед каждым полем; есть ли trusted length из заголовка.

## P3 — IOS-SEC-005: realpath→write TOCTOU

**Почему.** Зависит от того, идёт ли запись по fd или по path — аналогично
IOS-SEC-006. Если по fd — RULED_OUT; если по path после realpath —
кандидат. Разбор install-path на предмет `open`→`f*` vs `rename(path)`.

- Трудоёмкость: СРЕДНЯЯ. Шаг: проверить, использует ли `_installURL`/
  `_doInstallation` fd-anchored операции или path-based `rename`/`copy`.

## P3 — IOS-SEC-007/008: entitlement-XML differential + unarchive

**Почему низко.** Нет конкретного расхождения/доказательства; оба — классы
«проверить на всякий случай». Дёшево проверить allowedClasses для 008.

---

## Матрица «эффект / доказуемость»

| Направление | Security-значимость | Доказуемость offline | Трудоёмкость | Приоритет |
|---|---|---|---|---|
| kernel/sandbox confinement (errno 107) | ВЫСОКАЯ | СРЕДНЯЯ | ВЫСОКАЯ | **P1** |
| amfid vm_read double-fetch | ВЫСОКАЯ | ВЫСОКАЯ | НИЗКАЯ | **P1** |
| installd gating coverage | ВЫСОКАЯ | ВЫСОКАЯ | СРЕДНЯЯ | **P2** |
| AirTraffic root-fd/inter-symlink | СРЕДНЯЯ | ВЫСОКАЯ | НИЗКАЯ | **P2** |
| installd manifest loop | ВЫСОКАЯ | СРЕДНЯЯ | ВЫСОКАЯ | **P3** |
| realpath→write TOCTOU | СРЕДНЯЯ | СРЕДНЯЯ | СРЕДНЯЯ | **P3** |
| XML/unarchive differential | СРЕДНЯЯ | СРЕДНЯЯ | НИЗКАЯ | **P3** |

Рекомендация: начать с **amfid vm_read (P1, дёшево и даёт бинарный
вердикт)** и **sandbox-профиль AirTraffic B2↔B3 (P1, доказывает
confinement-механизм)** — они либо подтвердят, либо чисто опровергнут
кандидатов, не требуя устройства.
