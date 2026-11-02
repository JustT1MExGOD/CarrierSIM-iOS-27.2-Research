# Phase 17 · Отчёт 04 — Реализация CarrierBundleOverlay

## 1. Что найдено в исполняемом коде

`CarrierBundleOverlay` — C++ value-type, присутствующий в CommCenter B2/B3
в `shared_ptr`/`default_delete` mangled-метаданных. В отличие от Phase 16,
Phase 17 нашла не только имя типа, но и рабочие строки обработки overlay,
которые образуют фактический pipeline.

## 2. Подтверждённые этапы обработки

| Этап | Доказательство B2 | B3 | Уровень |
|---|---|---|---|
| Получить путь overlay | `Using overlay file path: %s` `0x102144d34` | `overlay file path provided` | A (строка в reachable коде; точный caller не восстановлен) |
| Открыть/разобрать dictionary | `Failed to load overlay file as dictionary: %s` `0x102144df0` | `overlay file as dictionary: %s` | A |
| Прочитать ключ | `Key not found in overlay file: %s` `0x102144e36` | сохраняется по смыслу | A |
| Получить значение | `Successfully retrieved value from overlay file` `0x102144e91` | сохраняется | A |
| Найти IMSI в matching info | `Failed to find IMSI in the overlay matching info` `0x102069f13` | `0x101fefc25` | A |
| Проверить SupportedSIM | `This SupportedSIM %s is not allowed for MVNO Overlay` `0x10206a045` | `0x101fefd57` | A |
| Добавить HomeBundleIdentifier | `Added HomeBundleIdentifier from overlay file to matching info` `0x102144d50` | формат изменён: `HomeBundleIdentifier = '%s'` | A |
| Передать в match | `homeBundleIdentifierFromMatchInfo provided to search for best match with SIM Info` `0x102147a7d` | сохраняется | A |
| Решить, применять ли overlay | `Device overlay decision`, `MVNO overlay decision`, `Multimode overlay decision`, `GSMA overlay decision` | все типы присутствуют | A по reachable strings + C++ контекст |

## 3. Типы overlay

Подтверждённые ключи/строки:

- `kDeviceMultimodeOverlay`
- `kMVNOMultimodeOverlay`
- `kDeviceMVNOMultimodeOverlay`
- `kMultimodeGSMAOverlay`
- `kDeviceMultimodeGSMAOverlay`
- `kDeviceMVNOGSMAOverlay`
- `kMVNOMultimodeGSMAOverlay`
- `kDeviceMVNOGSMAOverlay`
- `TechSettingsSecondaryOverlay`
- `IMSConfigSecondaryOverlay`
- `CarrierEntitlementsSecondaryOverlay`
- `PushSettingsSecondaryOverlay`
- `LocationSecondaryOverlay`
- `VoiceTextMediaOverlay`

## 4. Происхождение файла

Подтверждено только то, что pipeline получает **path** и читает dictionary.
Вызовы/строки:

- `Failed to create mobile helper to move the generated overlay files`
- `Error writing overlay file …`
- `Printing stats for overlay folder …`
- `Clearing Overlay files from: …`

Это показывает наличие системного writer/mobile-helper и overlay folder.
**Конкретный внешний источник, API создания или путь каталога Phase 17 не
утверждает**: строка `Using overlay file path` не раскрывает caller.

## 5. Когда вступает в силу

Доказаны события:

- `CarrierBundle has been updated, checking if there is a change in the GSMA settings state`;
- `Rematch carrier bundle to apply GSMA overlay based off the user preference`;
- `Overlay result is already cached, returning cached overlay path`;
- `No overlay matching key, marking override not required`;
- `No match for overlay`.

Следовательно, overlay участвует после загрузки/обновления carrier bundle и
может вызвать rematch; точный момент записи/инвалидации cache не восстановлен.

## 6. Вывод

Overlay — реальный системный механизм, а не только строковый artefact.
Однако наличие `HomeBundleIdentifier`/IMSI в overlay не доказывает, что
внешний клиент может создать overlay или использовать его для произвольного
назначения чужого bundle.
