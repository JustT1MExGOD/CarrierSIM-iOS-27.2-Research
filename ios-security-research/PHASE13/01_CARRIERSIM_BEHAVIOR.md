# Фаза 13 — фактическая работа CarrierSIM

## 1. Источник и отпечаток

- Файл: `C:\ipsw-tools\research-evidence-package\source\carrier.py`
- SHA-256: `0efcbfd8d08571194c262816f98a31c11b2a4ffa6e36e373c64989756f423dce`
- Размер: 167371 байт, 2807 строк. Дополнительно: `airtraffic_native.py`, `airtraffic_apple.py`, `bundle.yaml`, `launch.py`.

## 2. Главное: CarrierSIM — это НЕ установщик IPCC

CarrierSIM не подменяет carrier bundle через IPCC. Он создаёт **IMSI-симлинк** в пользовательском каталоге операторов, а IPCC использует только как **триггер** для принудительного пересканирования каталога системой. Это два разных механизма, которые нельзя смешивать.

Целевой каталог (записываемый пользовательский):
```
/var/mobile/Library/Carrier Bundles/iPhone
```
Системный (read-only) каталог:
```
/System/Library/Carrier Bundles/iPhone/*.bundle
```

## 3. Точная последовательность (по коду)

### 3.1. Чтение состояния SIM — `carrier_rows(device)` / `select_sims` (carrier.py:762, 1280)

- Через lockdownd `get_value` читается `CarrierBundleInfoArray` → для каждого слота: `Slot` (`kOne`/`kTwo`), `MCC`, `MNC`, `InternationalMobileSubscriberIdentity` (IMSI), `IntegratedCircuitCardIdentity` (ICCID), `CFBundleIdentifier` текущего bundle.
- `select_sims` валидирует: MCC = `\d{3}`, MNC = `\d{2,3}`, IMSI = `\d{15}` и начинается с `MCC+MNC`. Выбирает целевой bundle через `bundle_for(plmn, bundle.yaml)`.

`bundle_for` (1143): точное совпадение `config[plmn]` (например `25001: Vodafone_ro`), иначе `default`/BUNDLE для «домашних» MCC (250, 257). Зарубежная SIM без записи пропускается.

### 3.2. Выбор целевого bundle — `bundle_link` (1105)

```python
SYSTEM_PREFIX = '../../../../../../' + SYSTEM_BUNDLE_DIR + '/'
def bundle_link(name): return ('l', (SYSTEM_PREFIX+name).encode())
```
Симлинк — относительный путь с шестью `../`, выходящий из `/var/mobile/Library/Carrier Bundles/iPhone/<IMSI>` в `/System/Library/Carrier Bundles/iPhone/<Bundle>.bundle`. Для `Vodafone_hu` это ссылка `/<IMSI> -> .../Vodafone_hu.bundle`.

### 3.3. Подготовка симлинка и желаемого дерева — `make_plan` (1314)

`desired` = снимок текущего каталога + для каждой выбранной SIM запись `{<15-значный IMSI>: bundle_link(bundle)}`. `imsi_links` (1325) ищет корневые 15-значные симлинки. Системные ссылки валидируются регуляркой `[A-Za-z0-9_]+\.bundle`.

### 3.4. Подготовка установочного (staging) пакета — `staging_archive` (149)

Собирается ZIP: `META-INF/com.apple.ZipMetadata.plist` + каркас `p0/p1/p2/link` (симлинк `link -> ../../../var/mobile/Library/Carrier Bundles`) + `q0/q1/q2/q3/q4/payload` (желаемое дерево каталога). Шесть уровней `..` выводят из `/private/var/mobile/...` в `/`. Пакет загружается через `com.apple.streaming_zip_conduit` (662): `MediaSubdir=source`, затем сырые байты ZIP.

### 3.5. Передача на устройство — `transfer` (622) + AirTraffic assets

Три Book-asset формируются с `../../`-traversal в AssetID:

| idx | AssetID (destination) | назначение |
|---|---|---|
| 0 | `../../{source}/p0/p1/p2/link` → `airlift-link-*` | staging-симлинк в `/var/mobile/Media/{source}/p0/p1/p2/link` → `/var/mobile/Library/Carrier Bundles` |
| 1 | `../../{source}/../../Library/Carrier Bundles/iPhone` → `airlift-saved-*` | **экспорт** текущего каталога наружу в Media |
| 2 | `../../{final_source}` → `link/iPhone` | **запись** желаемого дерева обратно в `/var/mobile/Library/Carrier Bundles/iPhone` |

Регистрация в Books: `Books/Sync/Books.plist` содержит `{Persistent ID, Item ID, DSID}` для трёх asset. Host-сессия (AirTraffic/atc) обрабатывает манифест и для каждого `FileComplete` atc выполняет перемещение completed-файла «beneath AFC root».

### 3.6. Обработка системой — atc/AirTraffic move

atc (демон `com.apple.atc`, user `mobile`) обрабатывает AssetID и перемещает файл в destination. Destination вычисляется разрешением `../../`-пути. В Beta 2 move был NSFileManager-вызовом и допускал выход за пределы `/var/mobile/Media` через разрешение симлинка; в Beta 3/RC — dirfd-anchored `open(O_DIRECTORY|confinement)+mkdirat+renameatx_np(RENAME_NOFOLLOW)`, confine'ящий перемещение к AFC root.

### 3.7. Выбор bundle в CommCenter

CarrierSIM **не выбирает bundle сам** — вызывает `install_trigger` → `InstallationProxyService.install_from_local(ipcc)` (859). Штатный lockdownd IPCC-install. Установка IPCC заставляет CommCenter **пересканировать** каталог carrier bundles: CommCenter видит новый 15-значный IMSI-симлинк, резолвит его в системный `.bundle` и применяет этот профиль к соответствующей SIM. `commcenter.log` затем парсится (`report_log`, BUNDLE_BLOCK) для подтверждения выбора.

### 3.8. Активация операторских функций

Подтверждение `selected` в commcenter.log = CommCenter выбрал ожидаемый bundle. Финальное применение (VoLTE/VoWiFi/5G) — функция самого профиля и сети, не CarrierSIM.

## 4. Что подтверждено, что нет

| Шаг | Статус на iOS 27.2 |
|---|---|
| Чтение IMSI через lockdownd | ПОДТВЕРЖДЕНО (работает, read-only) |
| Создание IMSI-симлинка в каталоге | ЗАВИСИТ от записи через AirTraffic — **заблокировано на Beta 3/RC** |
| IPCC install (install_from_local) | ПОДТВЕРЖДЕНО как штатный канал |
| CommCenter пересканирует и выбирает IMSI-симлинк | РАБОТАЛО на ≤Beta 2; на RC не проверено |
| VoWiFi после выбора bundle | НЕ гарантировано |

## 5. Ключевой вывод

CarrierSIM = «записать IMSI-симлинк в живой каталог + заставить CommCenter пересканировать через штатный IPCC». Запись симлинка шла через приватное злоупотребление dataclass-синхронизацией atc (Book asset). Именно эту запись Apple закрыла в Beta 3 dirfd-confined move. Выбор bundle в CommCenter и IPCC-установка — ортогональные, штатные механизмы; они не являются точкой отказа.
