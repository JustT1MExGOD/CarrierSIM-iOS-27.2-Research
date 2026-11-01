# 05_VERSION_DIFFS — построечный дифф iOS 27.2 Beta 2 → Beta 3

Метод: пословный нормализованный diff дизассемблера (mnemonic-последовательность
на функцию, адреса/иммедиаты, зависящие от сдвига, отброшены). Источник:
`{atc,amfid,installd}_{B2,B3}.bin` + AirTraffic `__text`-срезы.
«Изменение ≠ фикс уязвимости» — каждая дельта помечена классом и уверенностью.
UUID'ы и SHA-256 — в 01_INVENTORY.

---

## 1. atc — B2 vs B3: ИДЕНТИЧНЫ [OBSERVED, HIGH]
- Размер обоих 84 160 B; байтовых отличий **126** — это UUID
  (C5B4B497…→CA2F88E5…) и build-id. Нормализованный дизасм совпадает
  полностью (255 строк, 0 расхождений).
- => Весь фикс Airlock **не в atc**, а в `AirTraffic.framework`. atc — тонкий
  host-wrapper. Не security-изменение.

## 2. amfid — B2 vs B3: ФУНКЦИОНАЛЬНО ИДЕНТИЧНЫ [OBSERVED, HIGH]
- Нормализованная последовательность инструкций совпадает на 100%
  (0 расхождений по mnemonics). Байтовых отличий 2 601 — UUID + версия +
  строковые константы. Ни одна security-функция не изменилась.
- Per-method gating `AMFIService` (B3): все mutating-методы
  (`setTrustForTeamID`, `setManagedState`, `setDemoState`,
  `commitProfileForUuid`, `stageProfileForUuid`, `signTeamID`,
  `removeTrustforTeamID`, `initiateDataMigration`,
  `initiateDeveloperModeDaemons`, `setSupervisedState`, `removeManagedState`)
  вызывают `verifyBoolEntitlement:`; только read-getter'ы
  (`getSEPState`, `getStagedProfile`) — нет. => консистентно, без
  неравномерности. B2==B3 → гейтинг не менялся.
- => По amfid регрессионных изменений НЕТ. Это опровергает гипотезу,
  что B3 что-то менял в trust-eval логике.

## 3. installd — B2 vs B3: точечные изменения [OBSERVED, HIGH]
- Общих функций 1075; изменились **19** (по mnemonic-последовательности).
- Методов `MIClientConnection` стало 97 (было 95): добавлены
  `endAppReplacementWithStatus:forApp:completion:` и
  `pushReplacementInfoForApp:replacingApp:withCompletion:` — оба GATED.
- Security-релевантные изменённые функции:

| Функция | b2 ops → b3 ops | Интерпретация [INFERRED] |
|---|---|---|
| `-[MIInstallableBundle _performAppExtensionValidationForAppBundleSigningInfo:validatingResources:allowFreeProfileValidation:error:]` | 350 → 434 | +84 инструкции: усиление валидации app-extension. Класс — ужесточение проверки подписи/entitlement расширения. CONFIDENCE MED — изменение есть, смысл подтверждён именем, конкретная новая проверка не разобрана поисково. |
| `-[MIInstallableBundle performInstallationWithError:]` | 314 → 323 | +9: минорное изменение основного install-пути. |
| `-[MIClientConnection prepareReplacementOfApp:byApp:extensionBundleIDs:withCompletion:]` | 486 → 546 | +60: app-replacement путь расширен. |
| `-[MIClientConnection setLaunchProhibited:forApp:withCompletion:]` | 282 → 365 | +83: launch-prohibition логика усилена/расширена. |
| `+[MILaunchServicesOperationManager _reconcileOperations:…]` / `_reconcileOperations:` | 424→630, 394→623 | крупное расширение reconcile-пути (добавление mount-point регистрации/derегистрации). |
| `-[MIAppReplacementOperation *]` (init/prepare/_bestEffortDiscard/cxx_destruct) | мелкие дельты | app-replacement операция переработана (4 связанных метода). |

- НИ ОДНА функция-валидатор (`_ValidateMIAllowedSPIEntitlement`,
  `valueForEntitlement`, `_checkEligibilityForAppWithSigningInfo`)
  **не изменилась** — entitlement-логика installd стабильна B2→B3.
- Тема кластера: **app-extension validation + app-replacement/launch-prohibition**
  — Apple усиливал именно механизм замены приложений и проверки расширений.
  Не «дыра закрыта в AirTraffic», а усиление install-пути.

## 4. AirTraffic framework — B2 vs B3: ГЛАВНЫЙ security-фикс [OBSERVED, HIGH]
(полностью разобрано в AIRLOCK_* отчётах; здесь — сводка для реестра)
- B2: move = Foundation/ObjC BOOL-call (`moveItemAtPath:`-подобный) +
  строковая проверка «Cannot move asset outside of AFC root» → обходилась
  `../../`+symlink.
- B3: move = `open(0x40100000)` → dirfd → `mkdirat` →
  `renameatx_np(RENAME_NOFOLLOW)` → `unlinkat` + `%{errno}d` +
  `beneath AFC root` (новые строки, 0→4 / 0→3). Ядро возвращает errno 107.
- [CLASS] path traversal → kernel-anchored confinement. Подтверждённый
  security-фикс (закрывает известную Airlift-цепочку).

## 5. kernelcache / sandbox-kext — НЕ разобраны [GAP]
- Оба образа присутствуют (B2+B3), но filetype=12 kernelcache и sandbox-kext
  требуют распаковки kext-секций — вне текущего прохода. Дифф политики
  sandbox между B2/B3 — открытая задача (там вероятно и живёт errno-107
  проверка). [NEEDS_MATERIAL/effort]

## 6. Сводка диффа для реестра
| Компонент | Изменение B2→B3 | Тип | Уверенность |
|---|---|---|---|
| atc | идентичен | — | HIGH |
| amfid | идентичен | — | HIGH |
| installd | +2 метода, 19 функций (extension-validation, app-replacement) | усиление проверок | HIGH факт / MED смысл |
| AirTraffic | строковая проверка → dirfd+kernel confinement | security-фикс | HIGH |
| kernel/sandbox | не разобрано | GAP | — |

Главное следствие: B3-«патч» — это точечное ужесточение (AirTraffic
confinement + install-path), а не широкий редизайн. Поверхность для
поиска уязвимостей сохраняется.
