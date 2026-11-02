# PHASE8 — 08_FALSE_POSITIVE_REVIEW

## 1. Exported method ≠ public method

**Проверка:** обе функции действительно входят в `AMFIProtocol`, а `AMFIDelegate` устанавливает этот протокол как `exportedInterface`.

**Correction:** это доказывает server-side export to accepted NSXPC connections, не публичную доступность обычному приложению. Client reachability — `UNKNOWN`.

## 2. Accepted connection ≠ Mach lookup

**Проверка:** `shouldAcceptNewConnection:` возвращает `1` без visible rejection branch.

**Correction:** callback исполняется после того, как connection уже достиг listener. Он ничего не доказывает о sandbox `mach-lookup`, bootstrap namespace или launchd visibility.

## 3. No local entitlement check ≠ no system authorization

**Проверка:** getter bodies не вызывают `verifyBoolEntitlement`, а listener не проверяет audit token.

**Correction:** возможные controls остаются на launchd, bootstrap, client sandbox, transport и framework layers. Их отсутствие в корпусе классифицировано `NOT VERIFIED`, не `CONTRADICTED`.

## 4. Metadata ≠ secret

**Проверка:** `getSEPState` возвращает 49-byte typed structure; `getStagedProfile` получает UTF-8 text from staging path.

**Correction:** нет evidence raw keys, credentials, PII or protected secret. SEP key `0xf` semantics and arbitrary staging content remain unknown. Sensitivity classified LOW–MEDIUM/NOT VERIFIED.

## 5. B2/B3 ≠ RC

**Проверка:** B2/B3 amfid disassembly and entitlement files are identical.

**Correction:** no RC amfid or RC policy artifact is available. B2/B3 conclusions are not applied to RC.

## 6. Static configuration ≠ runtime policy

**Проверка:** sandbox kext contains `mach-lookup`, `common-mach-lookups`, AMFI-related names and exact `com.apple.amfi.nsxpc` string.

**Correction:** a compiled string is not a decoded allow/deny rule. No effective client profile assignment or launchd policy was recovered.

## 7. “No exact rule found” ≠ “lookup denied”

Neither allow nor deny is assigned based on a failed string search. The correct status is `NOT VERIFIED`.

## 8. “Privileged daemon entitlement” ≠ “client entitlement”

`amfid_B2/B3.entitlements.plist` describes amfid itself. It cannot be used as evidence that a client with the same or a similarly named entitlement can reach `com.apple.amfi.nsxpc`.

## False-positive conclusion

Phase 7’s two `INSUFFICIENT EVIDENCE` classifications survive review. Phase 8 narrows the missing evidence to launchd/bootstrap visibility, effective client sandbox `mach-lookup` policy, and semantic sensitivity of the returned state. No prior claim is upgraded to a security issue.
