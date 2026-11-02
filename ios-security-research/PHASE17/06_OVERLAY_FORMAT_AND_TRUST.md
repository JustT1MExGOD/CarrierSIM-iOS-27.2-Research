# Phase 17 · Отчёт 06 — Формат и доверие к overlay

## 1. Формат

Доказано по коду:

- `Failed to load overlay file as dictionary` → **CFDictionary** (plist /
  property list — читается через CF-парсер, а не произвольный текст).
- `Using overlay file path: %s` — файл приходит как путь.
- `Key not found in overlay file: %s` — доступ по ключу.
- `overlay matching info` — подмножество ключей используется для match.
- `This SupportedSIM %s is not allowed for MVNO Overlay` — содержит
  список SupportedSIM / IMSI-префиксов.
- `HomeBundleIdentifier` — один из значений, подмешиваемых в match-info.

## 2. Обязательные поля и ключи

Подтверждено по строкам (не по schema):

| Поле/ключ | Роль |
|---|---|
| IMSI-префикс / запись в `overlay matching info` | Идентификация SIM, для которой применяется overlay |
| `SupportedSIM` (или эквивалент) | Белый список MVNO-совместимых SIM |
| `HomeBundleIdentifier` | Подсказка для matcher'а |
| `kMVNOMultimodeOverlay`, `kDeviceMultimodeOverlay`, `kDeviceMVNOMultimodeOverlay`, `kMultimodeGSMAOverlay`, `kDeviceMultimodeGSMAOverlay`, `kDeviceMVNOGSMAOverlay`, `kMVNOMultimodeGSMAOverlay`, `kDeviceMVNOGSMAOverlay` | Классы overlay по типу SIM/Device |

**Схема не восстановлена**: Phase 17 не нашла schema-файла, не извлекла
все ключи и не доказала обязательность каждого поля.

## 3. Проверки типов и значений

Доказаны проверки:

- **Словарь**: `Failed to load overlay file as dictionary` — если не dict,
  отказ.
- **Наличие ключа**: `Key not found in overlay file` — ключ может отсутствовать.
- **Соответствие IMSI**: `Failed to find IMSI in the overlay matching info` —
  запись должна быть для текущей SIM.
- **SupportedSIM**: `This SupportedSIM %s is not allowed for MVNO Overlay` —
  проверка доступа к MVNO overlay.
- **Кэш**: `Overlay result is already cached` — результат кэшируется после
  первого чтения.
- **Match**: `No match for overlay`, `No overlay matching key, marking
  override not required` — если не найдено соответствие, overlay не
  применяется.

**Не доказано**: явные проверки типов значений (CFString vs CFNumber vs CFArray)
для каждого ключа, диапазоны, обязательность и т.п.

## 4. Доверие/происхождение

- **Подпись**: в CommCenter строки/кода проверки подписи overlay-файла
  **не найдено** (в отличие от carrier bundle, которые подписаны Apple).
- **Происхождение**: есть строка `Failed to create mobile helper to move
  the generated overlay files` → overlay генерируется/копируется системным
  helper'ом, не создаётся приложением пользователя.
- **AppStoreOverlays.ViewService** — отдельный системный сервис; связь с
  carrier-bundle overlay доказана только как использование имени overlay-
  концепции, не как общий механизм.
- **Путь**: `Using overlay file path` — получение пути из системного
  контекста; сам путь не раскрыт.

## 5. Обновление

- `Error writing overlay file` — есть системный писатель.
- `Clearing Overlay files from: %s` — есть механизм очистки.
- `CarrierBundle has been updated, checking if there is a change in the
  GSMA settings state` + `Rematch carrier bundle to apply GSMA overlay` —
  после обновления bundle запускается rematch с учётом overlay.

Точный lifecycle обновления overlay-файла (кто, когда, с какими правами)
**не установлен**.

## 6. Вывод по доверию

Overlay — внутренний системный формат, генерируемый и обновляемый
системными компонентами. Формально подписанного канала (как для carrier
bundle) для overlay Phase 17 **не обнаружила**. Это означает, что
overlay не является механизмом внешнего пользователя, но и не
продемонстрирован как канал для CarrierSIM.
