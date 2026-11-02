# Phase 16 · Отчёт 10 — Триггер установки carrier bundle

## 1. Назначение документа

Разбор `kCarrierBundleTriggerInstallCarrierBundle` — где используется,
какие функции обрабатывает, связь с IPCC и SIM-to-bundle mapping.

## 2. Идентификатор (уровень A)

`kCarrierBundleTriggerInstallCarrierBundle` — строковый ключ с полным
XPC-прототипом в mangled-имени:

```
…ERKNS_10shared_ptrIK8RegistryEERKN3ctu10RestModuleE
 RKN8dispatch5queueERKN3xpc4dictENSI_10auto_replyEEUlbE_FvbEEE
```

→ обработчик принимает `Registry`, `ctu::RestModule`, `dispatch::queue`,
`xpc::dict`, `xpc::auto_reply` — это **XPC/REST-команда** внутри CommCenter
(ctu::rest framework — `command_t`/`command_responder_t`).

## 3. Семейство триггеров

- `kCarrierBundleTriggerInstallCarrierBundle` — установка bundle;
- `kCarrierBundleTriggerGetUpdatedCarrierBundle` — получение обновления;
- `kCarrierBundleTriggerResetCarrierBundle` — сброс;
- `kCarrierBundleTriggerRemoteRestoreToDefault` — удалённый сброс к default;
- `kCarrierBundleWatchBundleMatchCriteria` — подписка на критерии match.

Это **ctu::rest command-surface** — стандартный REST/XPC набор команд
CommCenter, а не свободная запись в файловую систему.

## 4. Что запускает обработчик

`installCarrierBundle_sync(CFSharedRef<__CFURL const>&, function<void(bool)>)`
— установка из URL + callback(bool success). `installiTunesUpdateBundles_sync`
— пакетная. Это **файловая установка bundle-пакета**, не изменение match.

## 5. Связь с IPCC

- IPCC (`.ipcc`) — это именно carrier-bundle package, устанавливаемый через
  `installCarrierBundle_sync`/`installiTunesUpdateBundles_sync`.
- `installation_proxy`/`streaming_zip_conduit` — AFC-канал загрузки .ipcc
  на устройство; CommCenter получает URL и ставит bundle.
- **Install ≠ match**: триггер ставит bundle как кандидата; привязка к SIM
  решается `matchCarrierBundle_sync` по IMSI/MCCMNC — отдельно.

## 6. Авторизация

- Триггер — XPC-команда, гейтится `EntitlementChecker`/
  `requiredEntitlementForRequest:` (см. отчёт 09).
- `Development Signed Carrier Bundles: Not Allowed` (B3) — dev-signed
  bundle отклоняется → install доверия проверяется.
- **Без анализа авторизации нельзя объявить триггер доступным** обычному
  процессу — это entitlement-gated REST-команда.

## 7. Может ли штатная установка изменить SIM-to-bundle mapping?

- Триггер **устанавливает** bundle (новый кандидат в pool), но не назначает
  SIM→bundle — это задача match.
- Для CarrierSIM-совместимости важен match-путь + IMSI-alias, а не install.
