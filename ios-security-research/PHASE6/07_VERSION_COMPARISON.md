# PHASE6 — 07_VERSION_COMPARISON

## Сравнительная таблица

| Компонент | B2 | B3 | Security-relevant delta | Вывод |
|---|---|---|---|---|
| `amfid` listener | тот же recovered NSXPC setup | тот же setup | disassembly texts byte-for-byte identical | no observed IPC authorization delta |
| `amfid` mutating methods | method-specific entitlement checks | те же checks | normalized mnemonic diff: 0 | no observed missing-gate regression or fix |
| `amfid` getters | `getSEPState`/`getStagedProfile` no visible gate | same | no observed change | open evidence question, not regression |
| `amfid` entitlement plist | relevant daemon entitlement set | line-for-line same | no observed entitlement delta | daemon entitlements do not prove client policy |
| `atc` host | 84,160 B; normalized disassembly | 84,160 B; normalized disassembly | only UUID/build metadata differences in available host | no host-level IPC authorization delta |
| AirTraffic framework | string/path-based move behavior | dirfd/kernel-constrained move | substantive B2→B3 filesystem change | operation boundary strengthened, but not caller auth |
| `installd` | older method set | +2 methods and 19 changed functions | install/replacement/extension-validation changes | no demonstrated IPC gate regression |

## Interpretation limits

1. Identical disassembly does not prove identical external dependencies, launchd policy, sandbox profile or framework behavior.
2. Binary metadata differences are not treated as authorization changes.
3. A B3 filesystem fix is not automatically an IPC authorization fix.
4. `installd` changes require separate full call-graph review before classifying any method as newly reachable or newly ungated.
5. No version comparison can substitute for proof of bootstrap lookup and caller identity.

## Version verdict

В доступном evidence нет подтверждённого B2→B3 IPC/XPC authorization regression в выбранных службах. Основной подтверждённый security delta остаётся в AirTraffic filesystem confinement; он не доказывает ни наличие, ни отсутствие caller authorization.
