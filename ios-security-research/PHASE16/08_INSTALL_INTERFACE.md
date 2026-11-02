# Phase 16 · Отчёт 08 — CarrierBundleInstallInterface

## 1. Назначение документа

Исследование интерфейса установки carrier bundle, его источников,
проверок доверия и связи с SIM-to-bundle mapping.

## 2. Реализация (уровень A)

- `CarrierBundleInstallInterface` — C++ класс в CommCenter
  (`…InstallInterfaceD2Ev` — деструктор). XPC-обработчик через `xpc::dict`/
  `auto_reply`/`RestModule`.
- Точка входа: `kCarrierBundleTriggerInstallCarrierBundle` (см. отчёт 10).

## 3. Методы установки в CommCenter

| Метод | Сигнатура | Роль |
|---|---|---|
| `installCarrierBundle_sync` | `(CFSharedRef<__CFURL const>&, function<void(bool)>)` | установка из URL |
| `installiTunesUpdateBundles_sync` | `(CFSharedRef<__CFArray const>&, bool, function<void(bool)>)` | пакетная установка из iTunes-обновлений |
| `handleCellularPlanTransferCarrierBundleUpdateRequest_sync` | `(rest::TransferCarrierBundleUpdateRequest&&, rest::command_responder_t<...>&&)` | обработчик cross-device transfer |
| `checkForUpdatedBundlesWithAutoInstall:completion:` | ObjC IMP | авто-установка обновлений |
| `restoreToSystemBundles` | ObjC IMP | сброс к системным bundle |

## 4. Источники и доверие

- **Источники**: `__CFURL` (локальный пакет/путь), `__CFArray` iTunes-update,
  `rest::TransferCarrierBundleUpdateRequest` (cross-device).
- **Доверие**: строка `Development Signed Carrier Bundles: Not Allowed`
  (только B3) — **в B3 dev-signed bundles явно отклоняются**;
  `kOverrideBundle{Success,Failure}` — результат override-операции.
- `kCarrierBundleTriggerRemoteRestoreToDefault` — удалённый сброс.

## 5. Связь с SIM-to-bundle mapping

- Установка bundle — **отдельная** операция от match/selection:
  `installCarrierBundle_sync` принимает URL и callback, **не** SIM-slot/
  IMSI-mapping. Она кладёт bundle в `/System/Library/Carrier Bundles/iPhone`
  (или user-каталог), но **не назначает SIM→bundle**.
- Назначение — через match (`matchCarrierBundle_sync`) с критериями IMSI/
  MCC/MNC/GID/SPN, которые читаются из SIM, а не из установленного пакета.
- `installPendingPlan`/`installMultiplePlans`/`installPendingRemotePlan` —
  eSIM-plan установка (CellularPlan), не carrier-bundle mapping.

## 6. Может ли штатная установка изменить SIM-to-bundle mapping?

- Установка bundle добавляет **кандидат** в pool, но match к SIM решает
  `matchCarrierBundle_sync` по SIM-данным → **установка сама по себе не
  изменяет сопоставление конкретной SIM**.
- Для назначения чужого bundle SIM нужно влиять на match-критерии —
  IMSI-alias (`AllowedIMSIPrefixes`, `IMSIOverride`) или overlay
  (`HomeBundleIdentifier from overlay file`) — **не через install** .

## 7. Вывод

`CarrierBundleInstallInterface` — XPC-сервис установки bundle-пакетов.
Он **не** предоставляет операции изменения SIM-to-bundle mapping; install
и match — разные операции. CarrierSIM-совместимость определяется match-
механизмом и IMSI-алиасами, а не install-интерфейсом.
