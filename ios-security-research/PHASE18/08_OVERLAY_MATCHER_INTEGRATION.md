# Phase 18 · Отчёт 08 — Интеграция CarrierBundleOverlay с matcher

## 1. Граф

```
Overlay source (system writer / mobile helper — компонент UNKNOWN)
   │  путь к overlay-файлу
   ▼
Overlay parser (CommCenter): "load overlay file as dictionary"
   │  CFDictionary; проверки: dict, key present
   ▼
overlay matching info (IMSI-запись, SupportedSIM, HomeBundleIdentifier)
   │  SupportedSIM MVNO gate → "Added HomeBundleIdentifier to matching info"
   ▼
matching information dict  (CommCenter)
   │  + IMSI/MCC/MNC/ICCID/GID + eIMSI subfolder match + HBI
   ▼
matchCarrierBundle_sync   (CommCenter, C++ method, B-level)
   │  "homeBundleIdentifierFromMatchInfo ... best match with SIM Info"
   │  "Matches for the given HomeBundle Identifier"
   ▼
selected bundle → sendBundleEvent_sync →
   │  validation: CarrierBundleUtilities.dylib (signature verify)
   ▼
активный bundle
```

## 2. Откуда поступает overlay

`Using overlay file path` — путь из системного контекста; writer — mobile helper
(`Failed to create mobile helper to move the generated overlay files`).
Внешний API создания **не найден**.

## 3. Как разбирается и какие поля используются

- Читается как **CFDictionary** (`Failed to load overlay file as dictionary`).
- Поля: IMSI-запись (`overlay matching info`), `SupportedSIM`, `HomeBundleIdentifier`,
  классы `kDeviceMVNO/Multimode/GSMAOverlay`.
- `Failed to find IMSI in the overlay matching info` — ключ привязки к SIM.

## 4. Формирование matching information

`Added HomeBundleIdentifier from overlay file to matching info` — overlay
обогащает dict подсказкой домашнего bundle, передаваемой в matcher.

## 5. Применение HomeBundleIdentifier

`homeBundleIdentifierFromMatchInfo provided to search for best match with SIM Info`
+ `Matches for the given HomeBundle Identifier` — критерий приоритета внутри
matcher, не прямое назначение.

## 6. Влияние на выбор кандидатов

- **может** сузить кандидатов (SupportedSIM) и сдвинуть приоритет (HBI);
- **не может** назначить произвольный bundle: `No match for overlay`,
  `override not required`, `No overlay matching key`.

## 7. Проверки доверия

- формат dict + наличие ключа;
- SupportedSIM whitelist;
- fallback при отсутствии match;
- **подпись overlay в CommCenter не найдена** — доверие через системный writer/FS-права.

## 8. Ограничение

Overlay — **входное обогащение**, а не override. `matchCarrierBundle_sync`
остаётся решающим; вес HBI в scoring не виден (B3 CBU недоступен).
