# PHASE6 — 05_AUTHORIZATION_HYPOTHESES

Выбраны три гипотезы с наиболее содержательным сочетанием чувствительности операции и локального пробела в доказательствах. Это гипотезы для проверки, а не утверждения о наличии уязвимостей.

## H1 — неоднородная авторизация `installd`

**Гипотеза:** accept-all NSXPC endpoint и 12 exported methods без прямого вызова `_ValidateMIAllowedSPIEntitlement` могут образовывать путь к чувствительной операции без достаточной транзитивной проверки.

**Почему проверяется:** endpoint setup не содержит видимой rejection branch; прямой gate распределён неравномерно.

**Что должно быть доказано для security finding:**

1. недостаточно привилегированный клиент может выполнить bootstrap/lookup;
2. конкретный метод экспортирован и достижим через protocol;
3. downstream path не выполняет эквивалентную проверку;
4. метод имеет чувствительный эффект, а не только read-only/test response.

**Предварительный статус:** INSUFFICIENT EVIDENCE.

## H2 — no-gate getters `amfid`

**Гипотеза:** `getSEPStateWithReply:` или `getStagedProfileWithReply:` доступны через accept-all NSXPC endpoint без client authorization и раскрывают чувствительное trust/profile state.

**Почему проверяется:** у getters не наблюдается `verifyBoolEntitlement:`; endpoint принимает соединение без visible gate.

**Что должно быть доказано:** endpoint reachability для unprivileged caller, selector exposure through `proto_AMFIProtocol`, sensitive returned data и отсутствие bootstrap/sandbox restriction.

**Предварительный статус:** INSUFFICIENT EVIDENCE.

## H3 — confused deputy на `atc`

**Гипотеза:** клиент, имеющий доступ к одному AirTraffic service, может передать host-controlled asset/session metadata и заставить `atc` совершить нежелательную операцию от имени `mobile`, если session authorization отсутствует.

**Почему проверяется:** launchd plist содержит несколько endpoint names; полный per-session caller authorization map не восстановлен.

**Что должно быть доказано:** конкретный insufficiently privileged client reaches endpoint, session handler accepts its data, operation crosses intended authority boundary, а B3 confinement не блокирует relevant target.

**Предварительный статус:** INSUFFICIENT EVIDENCE.

## Не выбранные гипотезы

- отсутствие любого audit-token API в одном listener method — недостаточно самостоятельно;
- `getPidForTesting` как privilege escalation — операция не показана чувствительной;
- наличие entitlement у daemon — не доказательство права любого клиента;
- различие B2/B3 в amfid — не поддерживается доступным normalized diff.
