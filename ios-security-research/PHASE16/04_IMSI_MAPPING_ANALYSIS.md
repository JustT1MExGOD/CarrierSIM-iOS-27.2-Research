# Phase 16 · Отчёт 04 — Анализ IMSI-маппинга

## 1. Назначение документа

Доказательство того, как CommCenter обрабатывает IMSI-идентификаторы и
существует ли в исполняемом коде механизм разрешения IMSI-симлинков из
`/var/mobile/Library/Carrier Bundles/iPhone` — исторический канал CarrierSIM.

## 2. IMSI-обработка в `__TEXT` (уровень A)

| Символ/строка | Роль |
|---|---|
| `copyMCCMNCFromIMSI` | извлечение MCC/MNC из IMSI |
| `createIMSIFromMccMnc` | обратное построение IMSI из MCC+MNC |
| `DigitMNCWithIMSI` | учёт переменной длины MNC (2/3 цифры) |
| `AllowedIMSIPrefixes` | **whitelist префиксов IMSI** — доказывает, что IMSI-матчинг ограничен допустимыми префиксами |
| `IMSIOverride` | флаг/ключ переопределения IMSI при match |
| `EnableIMSISwitch` / `commCenterIMSISwitchEvent` / `commCenterIMSISwitch` | переключение SIM по IMSI |
| `UseIMSIDuringProvisioning` | использование IMSI при provisioning |
| `DontUseImpiForImsi` | не использовать IMPI как IMSI |
| `EnableUnprovisionnedIMSIRemediation` | remediation для незарегистрированного IMSI |
| `kSubscriberImsi/Mcc/Mnc/Iccid/IsEsim/SimTrayStatus` | ключи subscriber-данных |
| `SIM2GID1`, `SIM2GID2` | GID1/GID2 — поля матчинга |
| `_kCTPhoneNumberRegistrationImsiKey`, `_kCTPostponementInfoIMSI`, `_kCTPostponementInfoIMSIOverride` | регистрация/отсрочка по IMSI |

## 3. Что доказывает наличие механизма IMSI-match

- `copyMCCMNCFromIMSI` + `AllowedIMSIPrefixes` + `IMSIOverride` —
  **существует код, принимающий решение по IMSI-префиксу** (не только по
  MCC/MNC): выбор bundle по диапазону IMSI — это именно то, чем пользуется
  CarrierSIM-симлинк.
- `IMSIOverride` — ключ, позволяющий переопределить IMSI при match: прямая
  поддержка механизма «SIM X показать как IMSI оператора Y».
- `EnableIMSISwitch`/`commCenterIMSISwitchEvent` — активное переключение
  по IMSI, а не пассивное поле.

## 4. Разрешение симлинка — что видно

В `__TEXT` присутствуют файловые операции и пути:

- `Carrier Bundles/iPhone` (path-литерал — проверен, есть в `__cstring`/`__const`
  как часть путей match);
- `override_carrier_list.json` (только B2 — механизм override-листа удалён в B3);
- `CarrierBundleOverlay.cpp`/`CarrierBundleOverlay` — overlay-механизм:
  `Added HomeBundleIdentifier from overlay file to matching info` —
  **overlay-файл подмешивает `HomeBundleIdentifier` в match-info** —
  документированный способ влиять на результат match без правки bundle.

## 5. Прямой ответ на задачу

| Вопрос | Ответ (доказательство) |
|---|---|
| Формируется ли путь из IMSI? | **`copyMCCMNCFromIMSI`/`createIMSIFromMccMnc` + `AllowedIMSIPrefixes` — да, IMSI-префикс используется для match** |
| Разрешаются ли симлинки из `/var/mobile/Library/Carrier Bundles/iPhone`? | `Carrier Bundles/iPhone` path-строка есть; `readlink`/`realpath`/`lstat` — **не выделено в отдельный видимый вызов**: резолюция происходит внутри `CarrierBundleUtilities.dylib` (недоступна) или через обычный `open()`/`stat()` каталога — `INSUFFICIENT EVIDENCE` для конкретного `readlink` |
| Продолжает ли B3 обрабатывать IMSI-симлинки? | Все IMSI-символы/методы присутствуют в B3 с идентичными счётчиками; match-методы идентичны по normalized-hash → **да, логика не изменилась**; доступ к файловому пути не проверялся кодом readlink |

## 6. Вывод

Механизм IMSI→bundle match реализован и **поддерживается штатно**
(`AllowedIMSIPrefixes`, `IMSIOverride`, `EnableIMSISwitch`, `createIMSIFromMccMnc`).
Точная файловая резолюция симлинка (readlink/lstat/порядок проверки
`/var/mobile` vs `/System`) находится в недоступной `CarrierBundleUtilities.dylib`
или в общем коде чтения каталога → `INSUFFICIENT EVIDENCE` для конкретного
системного вызова, но **SUPPORTED** для самого факта обработки IMSI-префиксов.
