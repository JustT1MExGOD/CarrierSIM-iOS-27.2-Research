# PHASE8 — 04_CLIENT_REACHABILITY_MATRIX

## Матрица

`UNKNOWN` используется намеренно: Mach-service имя и accept-all listener не устанавливают client reachability.

| Клиентская категория | Mach lookup | NSXPC connection | Getter methods | Источник/ограничение |
|---|---|---|---|---|
| Обычное App Store приложение | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Нет client sandbox profile, launchd bootstrap policy или runtime test; amfid accept code не доказывает lookup |
| Приложение с публичными entitlements | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Публичные entitlements в корпусе не сопоставлены с mach-lookup exception для этого имени |
| Системное приложение | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Нет конкретного system-app profile/launchd namespace и нет client identity map |
| Привилегированная служба Apple | **UNKNOWN** | **UNKNOWN** | **UNKNOWN** | Daemon entitlements amfid — это entitlements самого amfid, не allowlist его клиентов; client service material отсутствует |

## Допустимые более узкие утверждения

- `com.apple.amfi.nsxpc` используется listener'ом amfid: **CONFIRMED**.
- `AMFIProtocol` включает оба getter'а: **CONFIRMED**.
- `shouldAcceptNewConnection:` не отклоняет соединение в видимом коде: **CONFIRMED**.
- Для B2/B3 неизвестно, может ли обычное приложение выполнить Mach lookup: **NOT VERIFIED**.
- Для B2/B3 неизвестно, какие клиенты могут получить содержательный getter response: **NOT VERIFIED**.

## Почему ни одна строка не заменена на CONFIRMED

Для `Mach lookup` требуется effective policy конкретного клиента: bootstrap namespace, launchd service visibility и sandbox `mach-lookup` rules. Для `NSXPC connection` дополнительно требуется успешный transport handshake. Для getter method требуется protocol dispatch и обработка reply. В локальном корпусе подтверждён только последний server-side этап, а client-side path отсутствует.

## RC

Для RC (`24B119`) нет amfid binary, launchd plist или sandbox artifact. Поэтому B2/B3 reachability results нельзя распространять на RC.
