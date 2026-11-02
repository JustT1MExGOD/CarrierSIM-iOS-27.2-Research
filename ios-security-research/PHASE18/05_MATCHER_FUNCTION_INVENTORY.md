# Phase 18 · Отчёт 05 — Инвентаризация функций matcher

## 1. Распределение ролей

`CarrierBundleUtilities.dylib` (B2, `__text` `0xddac`, 234 PAC-функции) — это **движок верификации подписи и чтения bundle**, а не matcher. Функции восстановлены по строковым xref (PAC-функция → набор строк). IMP-адреса из CommCenter — отдельно.

## 2. Функции CarrierBundleUtilities (B2)

| Адрес (B2 VA) | Роль | Доказательства (строки) | Уверенность |
|---|---|---|---|
| `0x2c5645c04` | разбор bundle-формата | `Invalid file format`, `esimBootstrapConfig`, `loctable`, `lproj` | A |
| `0x2c5646540` | **readBundle** — чтение + классификация | `Error in readBundle`, `Failed to classify eIMSI config structure` | A |
| `0x2c5646cb4` | работа с `signatures` каталогом | `signatures` | A |
| `0x2c564725c` | **eIMSIConfig classifier + dir-read** | `Unable to read directory contents`, `eIMSIConfig_` | A |
| `0x2c5647784` | verify group signatures | `Unable to verify the signatures of the %s files` | A |
| `0x2c56479f4` | CBSignature digest/prefix | `CBSignature`, `digest type` | A |
| `0x2c564801c` | signature dict lookup | `signature dictionary for the file` | A |
| `0x2c5648650` | common-files digest | `No set of common files`, `FileDataMap` digest | A |
| `0x2c564901c` | remove signatures dir | `remove signatures directory` | A |
| `0x2c564c764` | version.xml parse | `Invalid version.xml`, `MobileDeviceCarrierBundlesByProductVersion` | A |
| `0x2c564d3e0` | SecKey algorithm check | `kSecKeyAlgorithmECDSASignatureDigestX962SHA384` | A |
| `0x2c564d69c` | CarrierBundle SecKey verify | `Signature verification has passed`, `Unable to read the CarrierBundle` | A |
| `0x2c564d900` | dev/prod signature fallback | `production signing`, `dev signing` | A |
| `0x2c564dcf0`/`0x2c564e090` | version.xml Format1/Format2 | `CarrierBundleSignatures`, `Format1/2`, `signature3` | A |
| `0x2c564ea80` | CountryBundles signature | `CountryBundles`, `CountryBundleSignatures` | A |
| `0x2c564ee90` | verify dispatch | `%s Verification succeeded/failed` | A |
| `0x2c564f1d0` | device signature match | `Found match, file %s contains this device's signature` | A |
| `0x2c564f828` | directory pattern scan + `overrides` | `searching for pattern`, `overrides` | A |
| `0x2c564fea4` | **copyPRISignatureForDeviceName** | `copyPRISignatureForDeviceName` | A |

## 3. Функции CommCenter (обе версии)

| Функция | B2 | B3 | Роль |
|---|---|---|---|
| `matchCarrierBundle_sync` | внутри `CarrierBundleHandler` | same | ядро выбора (не CBU) |
| `match{Operator,Country,Bootstrap,Default,DefaultBCAM}Bundle_sync` | — | — | кандидаты |
| `copyMCCMNCFromIMSI`/`createIMSIFromMccMnc` | — | — | IMSI → MCC/MNC |
| `installCarrierBundle_sync` | — | — | установка |

IMP `matchCarrierBundle_sync` не разрешён (C++ метод); восстановлен по именам/строкам — **B-level**.

## 4. IMSI-alias / symlink релевантность

- **CBU не содержит IMSI-symlink чтения** — нет `readlink`/`BundleLinks`/IMSI-path логики; он проверяет подпись выбранного bundle.
- **CommCenter содержит**: `_readlink`, `_realpath`, `_lstat`, `BundleLinks`, `eIMSI config subfolder matching '%s'` — IMSI-alias в CommCenter.
