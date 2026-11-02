# Фаза 14 — `CarrierBundleUtilities.dylib`

## 1. Поиск

Проверены доступные локальные деревья:

- `C:\ipsw-tools\beta2-dyld\System\Library\Caches\com.apple.dyld\`;
- `C:\ipsw-tools\IOS_SECURITY_RESEARCH\PHASE11\extracted_v2\`;
- `beta2-extracted`, `beta3-extracted`;
- локальные B2/B3 system DMG и извлечённые filesystem-каталоги;
- архивы evidence package.

Standalone-файл `/usr/lib/CarrierBundleUtilities.dylib` не найден.

## 2. Что найдено

Строка пути `/usr/lib/CarrierBundleUtilities.dylib` обнаружена в:

- main B2 cache metadata, около file offset `0xadc38`;
- cache subcache `.73`;
- `.atlas` metadata.

Это path/string evidence, а не извлечённый образ. В image set `PHASE11\extracted_v2` такого файла нет.

## 3. Почему исправленный extractor не решает проблему

`PHASE11\extract_flat.py` корректно упаковывает доступные сегменты образа и переписывает локальные `fileoff`. Но для полноценного извлечения нужны:

1. image record с VM-адресом и размером именно `CarrierBundleUtilities.dylib`;
2. байты всех доступных сегментов;
3. сохранённый `__LINKEDIT` для импорта/экспорта/fixups и UUID-связей.

Локальный `.79.dyldlinkedit` пуст. Поэтому даже найденная path string не даёт надёжного способа восстановить Mach-O image boundary, imports и exports.

## 4. Реализация и граф вызовов

- Mach-O header: **не найден**.
- UUID: **не найден**.
- Архитектура: ожидаемо arm64e по cache set, но для самого image не подтверждена отдельным header.
- SHA-256 standalone binary: **не вычисляется**.
- Exports/imports: **недоступны**.
- ObjC classes/protocols: **не привязаны к этому image**.
- Локальный call graph: **не строится**.
- Функции install/match/lookup/validation: **не восстановлены**.

## 5. Сильные и слабые утверждения

**ПРЯМО ПОДТВЕРЖДЕНО:** имя файла присутствует в локальной cache metadata/string data.

**КОСВЕННО ПОДДЕРЖИВАЕТСЯ:** в iOS build существует компонент с таким путём, связанный с carrier bundle functionality.

**НЕ ДОКАЗАНО:** что он предоставляет клиентский API; что он создаёт IMSI-симлинки; что он изменяет выбор bundle; что его методы доступны доверенному компьютеру или обычному процессу.

## 6. Что нужно для продолжения

Нужен полный version-matched dyld cache с непустым `.dyldlinkedit`, либо standalone Mach-O из соответствующего IPSW/cryptex. После получения можно проверить `LC_UUID`, load commands, ObjC metadata, imports/exports и call sites.

## 7. Статус

**Остановлено по критерию отсутствующего компонента.** Синтетические символы, экспорты или методы не создавались.
