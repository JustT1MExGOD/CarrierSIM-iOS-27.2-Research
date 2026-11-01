# PHASE4 — 07_FINDINGS_ASSESSMENT: итоговая оценка IOS-SEC-004 и IOS-SEC-005

## IOS-SEC-004 — delta-манифест и связанные файловые операции

**Статус: RULED OUT** (как реальная TOCTOU-уязвимость).

Обоснование по 4 условиям (см. 05):
- Разделённые операции: CONFIRMED (path-check затем path-use).
- Изменяемое состояние: CONFIRMED структурно (path-объект, не locked-fd).
- Доступный субъект: **CONTRADICTED** — домен AppBundles закрыт для всех,
  кроме installd и его trusted helper-service. Непривилегированного
  субъекта с write нет.
- Значимое последствие: NOT VERIFIED (эффект ограничен доменом; выход —
  anti-symlink блокируется).

Поскольку необходимое условие «доступный недоверенный субъект» опровергнуто,
TOCTOU-класс не реализуется как повышение привилегий. Последовательность
`realpath→path-op` — безопасная часть штатной архитектуры installd:
контролирующий субъект и защищаемый объект в одной trust-domain
(`_installd`/AppBundles). Это НЕ race для внешнего атакующего.

Дополнительное основание: delta-patch parser идентичен B2↔B3 (см. Phase 3
06) — это стабильный, давно существующий код, а не новая поверхность.

## IOS-SEC-005 — общие проверки путей и файловые операции installd

**Статус: ARCHITECTURAL OBSERVATION.**

Обоснование: паттерн `realpath/lstat/symlink-check → path-syscall`
подтверждён как штатная anti-symlink защита внутри installd-домена, а не
уязвимость. Он защищает от того же класса, который AirTraffic B3 закрыл
dirfd+jail — но AirTraffic работает на shared `/var/mobile/Media` (нужен
kernel-anchor), а installd — на приватном AppBundles (достаточно
DAC+anti-symlink). Различие объяснено владельцем root.

Нет подтверждённого сценария, где непривилегированный клиент заставляет
installd писать в путь, который клиент может мутировать — все file-ops
идут по installd-контролируемым destination (existingBundleContainer,
staging, AppBundles), резолвящимся installd'ом, не клиентом.

## Почему не PLAUSIBLE / не CONFIRMED

- PLAUSIBLE требует конкретного подозрительного дефекта — здесь нет
  субъекта, способного инициировать race, только теоретическое окно,
  доступное уже-privileged процессам (что не повышает права).
- CONFIRMED требует доказанного дефекта — он отсутствует.
- INSUFFICIENT EVIDENCE не ставлю: материала достаточно, чтобы закрыть
  гипотезу — домен и provenance path подтверждены.

## Что было бы нужно для поднятия статуса (честно)

Если бы нашёлся субъект вне trust-domain, который может писать в
`existingBundleContainer`/`staging`/AppBundles между `realpath` и
`rename`/`link` — тогда это был бы PLAUSIBLE race. Такого не найдено;
проверка установленности/placeholder перед apply дополнительно
подтверждает, что destination — легитимный installd-контейнер.

## Сводка

| Кандидат | Статус | Главное основание |
|---|---|---|
| IOS-SEC-004 | RULED OUT | нет недоверенного writer в AppBundles; окно только для privileged |
| IOS-SEC-005 | ARCHITECTURAL OBSERVATION | anti-symlink защита в своём домене, не дефект |
