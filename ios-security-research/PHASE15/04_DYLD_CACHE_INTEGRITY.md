# Phase 15 · Отчёт 04 — Целостность dyld shared cache

## 1. Назначение документа

Оценка структурной целостности и пригодности локального B2 dyld shared
cache для извлечения `CommCenter` и `CarrierBundleUtilities.dylib`, и
точное документирование того, **почему** полное восстановление этих
образов невозможно из имеющихся данных.

## 2. Состав cache-каталога

`C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\`

- `dyld_shared_cache_arm64e` — 802 816 Б (заголовок, mapping info,
  image array, инициализаторы/кэш-метаданные; код сосредоточен в субкэшах).
- Нумерованные субкэши `.01`…`.79`.
- Именованные пары `.25.dylddata`/`.26.dyldreadonly`,
  `.54.dylddata`/`.55.dyldreadonly`, `.77.dylddata`/`.78.dyldreadonly`.
- `dyld_shared_cache_arm64e.atlas` — служебные метаданные.
- `dyld_shared_cache_arm64e.79.dyldlinkedit` — **0 Б**.
- `dyld_shared_cache_arm64e.symbols` — **0 Б**.

## 3. Причина пустоты `.dyldlinkedit` и `.symbols`

Это ключевой вывод Phase 15, подтверждённый двумя независимыми путями:

1. **Метаданные есть, данных нет.** В cryptex-каталоге inode этих файлов
   существуют и несут корректные `decmpfs`-размеры:
   - `.79.dyldlinkedit` → uncompressed **694 321 152 Б**;
   - `.symbols` → uncompressed **1 245 495 296 Б**.
   Значит, в исходном образе файлы **не пустые** — пустой является локальная
   копия.

2. **Физический маппинг зашифрован.** Полный census cryptex-каталога показал
   набор типов записей `{3,4,5,6,9,12,13}` — `j_file_extent` (j_type 8)
   **отсутствует полностью**. Данные файлов лежат в resource-fork data
   stream через crypto-state записи `j_type 13`; их `phys_block` не читается
   в открытом виде без ключа тома. Плюс `compression_type=14` (LZFSE),
   который `cmpfs` не декодирует.

**Вывод**: пустота `.dyldlinkedit`/`.symbols` — ограничение **источника**
(зашифрованные cryptex-экстенты), а не дефект парсера и не реальное
отсутствие данных в прошивке. Это нельзя исправить установкой другого
инструмента: `ipsw dyld image` падает `⨯ …79.dyldlinkedit: EOF`.

## 4. Что проверено структурно

- Главный кэш парсится как `dyld_v1 arm64e` (magic проверен на субкэше
  `.01` по блоку 134750 — начинается с `dyld_v1  arm64e`).
- Mach-O заголовки внутри субкэшей **не** выровнены на 4K — образы идут
  подряд, поэтому простой поиск `0xfeedfacf` на границе страницы не находит
  `CommCenter`/`CoreTelephony` как самостоятельные Mach-O в `.01`/`.46`/`.73`.
- Строки install-name/paths присутствуют (см. отчёт 07):
  `/usr/lib/CarrierBundleUtilities.dylib` — в main, `.73`, `.atlas`;
  `CoreTelephony.framework/CoreTelephony` — в main, `.01`, `.atlas`;
  `CoreTelephony.framework/Support/CommCenter` — в `.01`.

## 5. Следствие для Phase 15

- Строковое присутствие целей в cache **доказано** (уровень B).
- Восстановление исполняемого Mach-O `CommCenter`/`CarrierBundleUtilities`
  из этого cache **невозможно** без `.dyldlinkedit` (таблицы binds/exports/
  rebase + chained fixups) и без `.symbols`, потому что:
  - нельзя разрешить импорты/селекторы/ObjC-метаданные,
  - нельзя отреконструировать `LC_ID_DYLIB`-границы образа в подряд-упакованном
    субкэше.
- Любые выводы «образ есть, но мы его не достали» корректно формулировать
  как `SUPPORTED BUT INCOMPLETE`, а не «функциональность отсутствует».

## 6. Что потребовалось бы для полного восстановления

- Ключ тома cryptex (для чтения `phys_block` из j_type 13) **или**
- Расшифрованный `.79.dyldlinkedit`/`.symbols` из IPSW-раздела rootfs
  (там экстенты — type 8, не зашифрованы) **или**
- Полный IPSW Beta 2/Beta 3 с rootfs-разделом, содержащим тот же
  dyld-кэш в расшифрованном виде.

Ни одно из условий локально не выполнено, скачивание запрещено ограничениями
Phase 15.
