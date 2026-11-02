# Phase 18 — Итоговый отчёт: CarrierBundleUtilities Recovery, Matcher Reconstruction & IMSI Alias Verification

## 1. Executive Summary

Phase 18 достигла решающего результата: **извлечён и дизассемблирован исполняемый
`__text` `CarrierBundleUtilities.dylib` B2** (0xddac, 14 187 инструкций, 234
PAC-функции) и подтверждено, что **IMSI-alias/symlink read path сохранён в B3** —
`_readlink`, `_realpath`, `_lstat`, `BundleLinks`, `eIMSI config subfolder
matching` идентичны B2. Главная коррекция архитектуры: CBU — это **движок
верификации подписи** (signature/version.xml/PRI), не matcher; IMSI-matching
живёт в CommCenter `matchCarrierBundle_sync`. Регрессия CarrierSIM — только
**запись симлинка** (AirTraffic `107 ENOTCAPABLE`), не чтение/match.

## 2. Результат cryptex DMG

B2 cryptex (`141-56439-025`) полностью доступен → dyld cache извлечён, CBU получен.
B3 cryptex (`141-56439-039`) читаем на каталогах, но все subcache **dataless** →
CBU B3 не извлечён (compression type 14 + пустой resource-fork + unresolved extents).

## 3. CarrierBundleUtilities

`/usr/lib/CarrierBundleUtilities.dylib` B2: VA `0x2c5643000`, UUID
`387c1f49-584a-37ba-a526-0ab0f6041e02`, `__text` SHA `68c66443…`. Полный Mach-O не
собран (LINKEDIT раздельный), но `__text` цел и дизассемблирован.

## 4. Проверка Mach-O

Magic/CPU/segment mapping/section offsets/VA↔file — все корректны. PAC-код
подтверждён. objc metadata вынесена в общий кэш (не извлечена — ограничение).

## 5. Функции matcher

CBU: readBundle, eIMSIConfig classifier, signature/digest/version.xml verify,
copyPRISignatureForDeviceName — **validator**, не matcher. CommCenter:
matchCarrierBundle_sync + кандидаты + IMSI-alias примитивы. IMP scoring не разрешён.

## 6. Алгоритм выбора bundle

`SIM → IMSI/MCC/MNC + eIMSI subfolder + HBI → matchCarrierBundle_sync (CommCenter)
→ IMSI-alias (BundleLinks+readlink) / operator / country / bootstrap / default →
sendBundleEvent_sync → signature verify (CBU) → active bundle`.

## 7. IMSI-симлинки

**Сохранены в B3**: `_readlink`, `_lstat`, `_realpath`, `BundleLinks`, `eIMSI
config subfolder matching`, `BCAM eIMSI config` — идентичны B2. Нет удаления
IMSI matching. Точка отказа — запись (AirTraffic).

## 8. CarrierBundleOverlay

Входное обогащение matching-info (HBI) через SupportedSIM/MVNO gate → влияет на
приоритет matcher, не override.

## 9. B2/B3 diff

Matcher/read path **без изменений**. Изменения: `injectMTsms`/`invalidateKey`
удалены, `addParticipants:` добавлен, `override_carrier_list.json` удалён,
`107 ENOTCAPABLE` на записи — единственное, что ломает CarrierSIM.

## 10. Гипотезы

| Гипотеза | Статус |
|---|---|
| H18-01 | SUPPORTED BUT INCOMPLETE (B2 да, B3 нет) |
| H18-02 | SUPPORTED BUT INCOMPLETE (validator+обвязка) |
| H18-03 | SUPPORTED BUT INCOMPLETE (read сохранён) |
| H18-04 | SUPPORTED BUT INCOMPLETE (в matcher нет diff) |
| H18-05 | SUPPORTED BUT INCOMPLETE (влияет как вход) |
| H18-06 | INSUFFICIENT EVIDENCE |
| H18-07 | RULED OUT |

## 11. Значение для CarrierSIM

IMSI-alias **полностью совместим** с B3 matcher — симлинк был бы разрешён.
CarrierSIM ломается **исключительно на записи** симлинка через AirTraffic
(`107 ENOTCAPABLE`). Восстановление требует альтернативного легального write-path,
который не найден и не исследовался как обход.

## 12. Ограничения

- B3 CBU недоступен (dataless subcache).
- `matchCarrierBundle_sync` IMP не разрешён — scoring не виден.
- `override_carrier_list.json` назначение не восстановлено.
- Нет runtime-подтверждения выбора bundle через симлинк.
- Связь readlink↔BundleLinks — по примитивам, не по единому CFG.

## 13. Рекомендация Phase 19

Самое полезное — **восстановить IMP `matchCarrierBundle_sync` и/или разобрать
dataless extents B3 subcache** (апгрейд `dpp`/`apfs` reader на j_type 13/deduped),
чтобы получить B3 CBU и провести прямой binary-diff matcher'а. Это единственный
пробел между «код присутствует» и «логика идентична».

## Ответы на вопросы

**Q1. Получена ли исполняемая реализация CarrierBundleUtilities?**
Да для B2 (`__text` извлечён и дизассемблирован). Нет для B3 (dataless).

**Q2. Восстановлен ли фактический алгоритм выбора carrier bundle?**
Частично — обвязка и кандидаты восстановлены; ядро scoring `matchCarrierBundle_sync`
не разрешено (UNKNOWN).

**Q3. Сохранилась ли обработка IMSI-симлинков на Beta 3?**
**Да** — read path (`readlink`/`lstat`/`realpath`/`BundleLinks`/eIMSI) идентичен B2.
Запись симлинка заблокирована отдельно (`107 ENOTCAPABLE`).

**Q4. Есть ли изменения matcher, влияющие на CarrierSIM?**
Нет — matcher без изменений. Единственная регрессия — write path AirTraffic.

**Q5. Как overlay влияет на выбор bundle?**
Обогащает matching-info (HBI) через SupportedSIM gate → сдвигает приоритет
внутри санкционированного набора; не override.

**Q6. Существует ли подтверждённый поддерживаемый путь восстановления CarrierSIM?**
**Нет** — запись симлинка заблокирована; легального пользовательского write-path
не найдено.

**Q7. Какое одно направление исследовать следующим?**
Разрешить IMP `matchCarrierBundle_sync` и извлечь B3 CBU (апгрейд reader на
dataless extents) — для прямого binary-diff matcher'а B2/B3.
