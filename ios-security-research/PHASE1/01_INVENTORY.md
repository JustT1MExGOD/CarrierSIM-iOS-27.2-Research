# 01_INVENTORY — доступные артефакты iOS 27.2 (Beta 2 / Beta 3) для security-исследования

Дата сборки инвентаря: работа выполняется офлайн, без устройства.
Диапазон: только `C:\ipsw-tools` и явно названные источники. Никакие
произвольные пользовательские каталоги не сканировались.

Обозначения уверенности по символам:
- **FULL** — есть таблица символов / chained-fixups, имена резолвятся.
- **PARTIAL** — резолвятся строки/CString/ObjC-имена, но не все call-targets.
- **SLICE** — вырезанный сегмент (`__text`) без загрузочного контекста,
  `macho info` на нём падает; адреса есть, символы — только по сигнатурам.
- **NONE** — нет таблицы символов, только байты/строки.

Устройство/платформа: iPhone16,1 (iPhone 15 Pro), arm64e, MinOS/SDK iOS 27.2.

---

## 1. Извлечённые исполняемые Mach-O (основной аналитический материал)

| Файл | Компонент | Сборка | SHA-256 | LC_UUID | Тип / арх | Символы |
|---|---|---|---|---|---|---|
| `atc_B2.bin` | atc (AirTraffic host) | B2 (ld 27100.1.100) | `adf839d4…1e23bcd` | C5B4B497-C77A-3F40-AFE6-AFDC172E2C5E | EXECUTE, arm64e USR00, PIE | FULL-ish (33 syms, 31 undef, chained fixups) |
| `atc_B3.bin` | atc | B3 (ld 27106) | `2ed9c6fe…5a4afc` | CA2F88E5-5348-330C-89FA-98BA1ADEA086 | EXECUTE, arm64e USR00, PIE | FULL-ish (33 syms, chained fixups, 82 ent keys) |
| `amfid_B2.bin` | amfid (code-sign eval) | B2 | `39d4d583…001ccd9` | 3E6D3282-527E-3BC1-8A9F-1C2BABF3A894 | EXECUTE, arm64e USR00 | PARTIAL (chained fixups) |
| `amfid_B3.bin` | amfid | B3 | `d331a101…0db8f` | CFB0C004-41E6-3E06-9D94-0F71E7B3DA2B | EXECUTE, arm64e USR00 | PARTIAL |
| `installd_B2.bin` | installd | B2 | `f0f1ce4b…8576f` | 5D0437D3-8824-39D1-8BEB-E8F48DA6F93B | EXECUTE, arm64e USR00 | PARTIAL |
| `installd_B3.bin` | installd | B3 | `1dd5efbf…064b1d` | F54A48D1-4E77-3425-BEAB-5EBBBB037C0F | EXECUTE, arm64e USR00 | FULL-ish (536 chained-fixup imports разобраны) |
| `AirTraffic_B2.bin` | AirTraffic.framework | B2 | `d6926732…80ca2` | (см. ниже) | композитный dyld-cache slice, 42 MB | PARTIAL — `macho info` падает (EOF @ stroff 0x2214b6b0) |
| `AirTraffic_text_B2.bin` | AirTraffic `__text` | B2 | `9c67b759…1db5ba` | 408fdad03c913c3eaf68413d594f13e6 | SLICE, 128 KB `__text` | SLICE |
| `AirTraffic_text_B3.bin` | AirTraffic `__text` | B3 | `d263612f…c54ec1` | be4ea03b081a3edfbd165396096485db | SLICE, 128 KB `__text` | SLICE |

Примечания:
- `AirTraffic_B2.bin` (42 MB) — дамп образа из кэша со множеством
  зависимых библиотек в строках (CloudDocs, StoreServices, MediaServices,
  Airship…). Полный заголовок не парсится; для анализа используются
  выделенные `__text`-срезы (`*_text_B2/B3.bin`).
- atc_* — это хост-демон, который выполняет файловые перемещения
  (move) для синхронизируемых «asset». Именно здесь живёт проверенный
  dirfd-bound move (см. AIRLOCK_* отчёты).
- Парные B2/B3 версии позволяют делать построечный diff — ключевой
  источник для `05_VERSION_DIFFS.md`.

## 2. Ядро (XNU) и sandbox-kext — НОВЫЙ материал

| Файл | Сборка | SHA-256 | Тип | Символы |
|---|---|---|---|---|
| `beta2/…/kernelcache.release.iPhone16,1` | B2 | `35e3266f…fbfb85` | Mach-O arm64e (PAK00) filetype=12 (kernelcache), 73 990 144 B | PARTIAL (ядро+kexts; символьная инфа ограничена) |
| `beta3/…/kernelcache.release.iPhone16,1` | B3 | `c31c0819…65a09` | то же, 73 465 856 B | PARTIAL |
| `beta2/sandbox/com.apple.security.sandbox` | B2 | `c884a1af…2b7438` | kext bundle arm64e (PAK00), 2 379 048 B | PARTIAL (содержит sandbox-профили/правила) |
| `beta3/sandbox/com.apple.security.sandbox` | B3 | `e41c7ea7…6c0329` | то же | PARTIAL |

Это самый весомый актив для этапов 2–3: kernelcache содержит реализацию
*at-системных вызовов, sandbox-крюков, проверок entitlement/capability —
то есть место, где возникает errno 107. sandbox-kext содержит профили
Seatbelt (в т.ч. профиль `AirTraffic`, на который ссылается entitlement
`seatbelt-profiles` у atc). Построечный diff kernelcache/sandbox позволяет
увидеть, что поменялось в политике между B2 и B3.

## 3. dyld shared cache (Beta 2)

`beta2-dyld/System/Library/Caches/com.apple.dyld/` — 82 файла,
`dyld_shared_cache_arm64e` + пронумерованные под-кэши (.01–.79),
`.25.dylddata`, `.26.dyldreadonly`.

- Суммарный полезный объём — порядка гигабайт; содержит системные
  фреймворки/библиотеки (CoreTelephony, AirTraffic, Foundation и т.д.).
- **Критическое ограничение (подтверждено повторно):**
  `dyld_shared_cache_arm64e.79.dyldlinkedit` и `.symbols` имеют размер
  **0 байт**. `ipsw dyld info` падает с
  `dyldlinkedit: EOF`. Следовательно резолюция имён символов/stub-targets
  из кэша НЕВОЗМОЖНА — адреса видны, имена — нет. Это фундаментальное
  ограничение для всех последующих этапов: call-targets помечаются
  как signature-matched, а не symbol-resolved.

## 4. Launchd plists (прочитаны из root FS B3, сняты ранее)

`CARRIERSIM_ARCHITECTURE_RESEARCH/evidence/tmp_com.apple.*.plist`
(+ дубликаты в корне `ipsw-tools`). Формат: часть bplist00, часть XML.

| Сервис (Label) | Бинарь | Пользователь | MachServices |
|---|---|---|---|
| com.apple.atc | /usr/libexec/atc | **mobile** | com.apple.atc.xpc(.service/.sessions/.observer/.downloadprogress/.icappobserverdelegate/.runkeeplocaltask), com.apple.atc2, com.apple.private.alloy.airtraffic-idswake |
| com.apple.CommCenter | CoreTelephony.framework/Support/CommCenter | **_wireless** | ~16: commcenter.xpc/.coretelephony/.carrierspace/.atcs/.ari.rt/.cupolicy/.tmk/.oswatchdog/.mobile-helper-cbupdateservice, CellularPlanDaemon.xpc, aps.CommCenter(.webpush), basebandd.xpc, usernotifications.* |
| com.apple.mobile.installd | /usr/libexec/installd | **_installd** | com.apple.mobile.installd |
| com.apple.streaming_zip_conduit | /usr/libexec/streaming_zip_conduit | **mobile** | com.apple.streaming_zip_conduit |
| com.apple.dataaccess.dataaccessd | DataAccess.framework/Support/dataaccessd | **mobile** | com.apple.dataaccess.dataaccessd(.aps/.aps.demo/.aps.dev) |

Пользователь демона — ключевая колонка границы доверия: atc и
dataaccessd/streaming_zip_conduit работают от `mobile` (низкие права,
sandbox), CommCenter/installd — от выделенных uid с широкими
возможностями. Это определяет, какие сервисы являются privileged-депьюти.

## 5. Entitlements (извлечены из LC_CODE_SIGNATURE → `IOS_SECURITY_RESEARCH/ents/`)

| Компонент | B2↔B3 | #keys | Характерные ключи |
|---|---|---|---|
| atc | **идентичны** (diff пуст) | 82 | seatbelt-profiles=[AirTraffic], application-groups, mach-lookup.global-name, home-relative-path.rw=[/Media/Music, /Library/NanoMusicSync…], tcc.allow, mobileinstall.allowedSPI, InstallCoordination.allowed, private.* (~40) |
| amfid | **идентичны** | 20 | keystore.keybag.load, iokit.nvram-read/write-access, private.amfi.*, mis.trust.set, LocalAuthentication.Storage.*, MobileGestalt.AllowedProtectedKeys |
| installd | **идентичны** | 31 | private.sandbox.profile:embedded, MobileContainerManager.allowed, MobileInstallationHelperService.*, amfi.can-check-trust-cache, mis.online_auth_agent, uninstall.deletion, usermanagerd.persona.*, daemon-container |

Важно для этапа 5: **эталонные entitlement-наборы не изменились между
B2 и B3** — патч Airlock был сделан в коде/логике, а не расширением
прав. Это сужает поиск регрессии к поведению, а не к новым entitlement.

## 6. Образы файловых систем / прошивки (исходники, read-only)

| Артефакт | Содержимое | Размер |
|---|---|---|
| `beta2-fs-decrypted/141-56668-025.dmg` | B2 root FS (raw NXSB/APFS) | 10.45 GB |
| `beta3-fs-decrypted/141-56668-039.dmg` | B3 root FS | 10.52 GB |
| `beta3-system/24B5099f__iPhone16,1/141-56439-039.dmg` | B3 cryptex (system) | 6.19 GB |
| `beta2-decrypted/141-56439-025.dmg` | B2 cryptex | 6.19 GB |
| `beta{2,3}-filesystem/*.aea`, `beta{2,3}-system/*.aea` | зашифрованные исходники AEA | 9.1 / 2.4 GB |
| `beta3-system/…/fcs-keys.json` | приватный ключ FileCoordinatedStorage | — |
| `beta2-dmg/…/141-55981-031.dmg` | вспомогательный DMG | 16 MB |

Чтение root FS идёт через пропатченный `dpp-source` (APFS NOHEADER fix)
+ примеры `apfs/examples/probe_*.rs` — read-only, для извлечения
plist'ов/бинарей по имени. Полный обход каталога медленный; целевые
`read_file`/`stat` быстрые. Содержимое cryptex-файлов частично
заблокировано crypto-state/decmpfs-экстентами (тип 13/14).

## 7. Предыдущие отчёты (источник фактов и гипотез, не независимое доказательство)

- `AIRLOCK_SYMBOL_VERIFICATION/` — 6 файлов, разрешение символов,
  флаги Darwin, AFC-root confinement, B2/B3 diff, fileproviderd, verdict.
- `AIRLOCK_DEEP_VERIFICATION/` — 6 файлов, углублённая проверка флага
  0x40000000, механизм confinement, resolved imports, errno 107,
  вердикт по заявлениям исследователя, индекс доказательств.
- `AIRLOCK_FINAL_PATCH_ANALYSIS.md` — сводный анализ патча.
- `CARRIERSIM_ARCHITECTURE_RESEARCH/` — 5 файлов + evidence plists.
- `rc-test-24B119/` — on-device RC-прогон: FINAL_RC_TEST,
  ROOT_CAUSE_ANALYSIS, STATIC_ANALYSIS, логи syslog (raw + atc).
- `research-evidence-package/` — MANIFEST, analysis, binaries, logs,
  reports, source.
- `final-analysis/` — DARWIN_CONSTANTS.md, b2_move_path.asm,
  b3_move_routine.asm, log_evidence.txt.

## 8. Известные пробелы (фиксируем честно)

- **Нет XNU/Darwin-заголовков локально** — константы errno, флаги open(),
  коды mach/error проверяются по бинарям/таблице strerror, не по исходникам.
- **Нет RC-бинарей** — есть только RC on-device лог; RC-код не диффился.
- **`CommCenter`, `fileproviderd`, `dataaccessd`, `streaming_zip_conduit`
  бинари НЕ извлечены** — их анализ ограничен plist/строками.
- **Stub-имена не резолвятся** — `.dyldlinkedit`/`.symbols` = 0 байт;
  вызовы идентифицируются по сигнатуре, не по имени символа.
- **sandbox-профили не декомпилированы** в .sb-правила (kext бинарный);
  структура Seatbelt-профилей требует отдельного разбора.
- **kernelcache не дизассемблирован** на момент инвентаря (filetype=12,
  требует распаковки/анализа kext-секций).

## 9. Вывод по готовности

Достаточно материала для этапов 2–5 (trust boundaries, IPC-review по
entitlement/plist/строкам, data-handling по дизасму, B2↔B3 diff).
Главный структурный лимит — отсутствие символьных таблиц кэша: выводы о
конкретных вызовах будут с уровнем уверенности MEDIUM/HIGH по сигнатуре,
не FULL по имени. Это будет отражено в каждом finding как ограничение
доказательства.
