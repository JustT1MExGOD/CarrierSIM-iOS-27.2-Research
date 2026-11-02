# Phase 15 · Отчёт 11 — Матрица доступности компонентов

## 1. Назначение документа

Сводная матрица всех компонентов, необходимых для carrier-bundle /
CommCenter исследования: где каждый находится, восстановлен ли исполняемый
код, и какой уровень доказательности достигнут.

## 2. Матрица

| Компонент | rootfs | cryptex | dyld-образ | Код восстановлен | Уровень |
|---|---|---|---|---|---|
| `CommCenter` (B2) | **есть** | — | — | **✅ 41 018 192 Б, UUID `83978CC2…`, SHA `9e815d9e…`** | **A** |
| `CommCenter` (B3) | **есть** | — | — | **✅ 40 370 720 Б, UUID `747592DD…`, SHA `9a5eeaf3…`** | **A** |
| `CarrierBundleUtilities.dylib` | нет | нет | есть | ❌ (в cache, `.dyldlinkedit` зашифрован) | B (install-name + `LC_LOAD_DYLIB`) |
| `CoreTelephony` | нет | нет | есть | ❌ (в cache) | B |
| `libCommCenter{Base,M,K}CommandDrivers` | нет | нет | есть | ❌ (в cache) | B |
| `AirTraffic` (B2/B3) | нет | есть (dyld `.48` / cryptex) | есть | ✅ `__TEXT` B2+B3 | A |
| `atc` | есть | — | — | ✅ B2+B3, идентичны | A |
| `amfid` | есть | — | — | ✅ B2+B3, идентичны | A |
| `installd` | есть | — | — | ✅ B2+B3 | A |
| `MobileInstallation` IPCC-путь | есть (framework) | — | — | ❌ (не анализирован для IPCC) | — |
| `EntitlementChecker` | — | — | — | класс в CommCenter | A (класс) / B (ключи) |

## 3. Барьеры и их природа

| Барьер | Причина | Обходим ли офлайн |
|---|---|---|
| `__LINKEDIT`/`.symbols` cache пусты | cryptex-экстенты зашифрованы (j_type 13, type-8 отсутствует, LZFSE) | **нет** без ключа тома / rootfs-раздела cache |
| `CarrierBundleUtilities`/`CoreTelephony` тело недоступно | это dyld-образы → границы/LINKEDIT в зашифрованной части | **нет** без расшифровки cache |
| RC `24B119` образ | нет локального IPSW | **нет** без скачивания (запрещено) |

## 4. Что изменилось благодаря Phase 15

- До Phase 15 все выводы о CommCenter/CarrierBundle были строковыми (B).
- Теперь **CommCenter B2 и B3 восстановлены полностью** из main rootfs —
  реальный Mach-O со всеми сегментами и ObjC/C++-метаданными.
- Владелец `CarrierBundle*Interface`, XPC-транспорт, entitlement-механизм
  и IMSI-match логика доказаны уровнем A.
- Единственный оставшийся невосстановленный carrier-bundle компонент —
  `CarrierBundleUtilities.dylib` (dyld-образ) и сам `CoreTelephony`.
