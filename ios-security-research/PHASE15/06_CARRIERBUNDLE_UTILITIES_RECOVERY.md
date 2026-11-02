# Phase 15 · Отчёт 06 — Восстановление CarrierBundleUtilities.dylib

## 1. Назначение документа

Целенаправленный поиск `/usr/lib/CarrierBundleUtilities.dylib` во всех
локальных источниках и итоговый статус восстановления.

## 2. Результаты поиска

| Локация | Метод | Результат |
|---|---|---|
| cryptex `usr/lib` (каталог) | APFS btree resolve | **Отсутствует** — только `libLogRedirect`, `libMTLHud`, `libobjc-trampolines`, `libstdc++*`, `objc/libobjcMsgSend*`, `swift` |
| cryptex standalone Mach-O | `0xfeedfacf`+`LC_ID_DYLIB` | не найден (install-name в зашифрованном LINKEDIT) |
| dyld cache строки | grep | **Строка есть**: `/usr/lib/CarrierBundleUtilities.dylib` в main/`.73`/`.atlas` |
| dyld cache как образ | Mach-O в субкэшах | не резолвится без `.dyldlinkedit` |
| main rootfs `usr/lib` | `probe_catbin read_file` | **`FileNotFound("CarrierBundleUtilities.dylib")`** — в rootfs как standalone-файла нет |

## 3. Важное следствие из CommCenter

Извлечённый `CommCenter_B2.bin` содержит
`LC_LOAD_DYLIB /usr/lib/CarrierBundleUtilities.dylib` — библиотека реально
существует и загружается CommCenter. Значит она **есть** в системе, но живёт
**только как dyld-cache образ** (не standalone-файл и не в rootfs).

## 4. Почему не восстановлена

`CarrierBundleUtilities.dylib` — dyld-cache-образ. Его сегменты упакованы
в нумерованные субкэши подряд (без 4K-выравнивания), а `.79.dyldlinkedit`
и `.symbols` зашифрованы (j_type 13, type-8 отсутствует). Без LINKEDIT
нельзя определить границы образа и его export-trie.

## 5. Статус

`SUPPORTED BUT INCOMPLETE` — существование доказано строкой install-name
и `LC_LOAD_DYLIB` в CommCenter; исполняемый образ не восстановлен из-за
зашифрованных cryptex-экстентов. Для повышения до `CONFIRMED` нужен
расшифрованный `.dyldlinkedit` или rootfs-раздел с тем же cache.
