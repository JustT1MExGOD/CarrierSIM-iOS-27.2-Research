# PHASE8 — PHASE8_SUMMARY

## Scope

Phase 8 independently audited the transport reachability of `com.apple.amfi.nsxpc` for the two Phase 7 getter methods:

- `getSEPStateWithReply:`;
- `getStagedProfileWithReply:`.

Work was static and offline only. No iPhone connection, live IPC/XPC request, fuzzing, exploit development, sandbox bypass, protected-data extraction, binary modification, publication or Git push was performed.

## 1. Source inventory

Available:

- complete B2/B3 `amfid` Mach-O slices and disassembly;
- B2/B3 daemon entitlements;
- B2/B3 sandbox kexts;
- B2/B3 kernelcache files;
- B2 dyld shared-cache split set;
- RC diagnostic reports/logs.

Missing:

- amfid/MobileFileIntegrity launchd plist;
- decoded launchd bootstrap/service visibility metadata;
- effective App Store/system/client sandbox profiles;
- decoded allow/deny policy for `com.apple.amfi.nsxpc`;
- RC amfid and policy artifacts;
- authoritative LocalAuthentication mapping for LAStorage key `0xf`.

Detailed hashes and paths are in `01_SOURCE_INVENTORY.md`.

## 2. Mach service registration

B2/B3 `amfid` contain actual code:

```text
NSXPCListener alloc
initWithMachServiceName:@"com.apple.amfi.nsxpc"
setDelegate:AMFIDelegate
resume
```

Therefore the listener’s intended Mach-service name is **CONFIRMED** at the server code level. `AMFIDelegate` then sets `AMFIProtocol` as exported interface/object and returns `1` from `shouldAcceptNewConnection:`.

A separate `bootstrap_check_in("com.apple.MobileFileIntegrity")` path exists, but it is a different MIG/Mach endpoint and is not evidence about the NSXPC protocol.

What is not confirmed: launchd declaration, bootstrap namespace, service visibility and client lookup permissions.

## 3. Sandbox policy

B2/B3 sandbox kexts contain policy machinery and strings for:

- `mach-lookup`;
- `common-mach-lookups`;
- global/local Mach lookup exceptions;
- `bootstrap`/`mach-bootstrap`;
- `amfid`, AMFI and `AppleMobileFileIntegrity`;
- `com.apple.amfi.xpc` and `com.apple.amfi.nsxpc`.

The exact `com.apple.amfi.nsxpc` string occurs once in each kext. No decoded allow or deny rule for that service was recovered. A string occurrence is not an effective rule; no client profile assignment or runtime policy is available.

Result: lookup authorization **NOT VERIFIED**.

## 4. Client reachability matrix

| Client | Mach lookup | NSXPC connection | Getter methods |
|---|---|---|---|
| Ordinary App Store app | UNKNOWN | UNKNOWN | UNKNOWN |
| App with public entitlements | UNKNOWN | UNKNOWN | UNKNOWN |
| System app | UNKNOWN | UNKNOWN | UNKNOWN |
| Privileged Apple service | UNKNOWN | UNKNOWN | UNKNOWN |

The matrix deliberately retains `UNKNOWN`: server-side listener setup cannot establish client-side reachability.

## 5. Transport authorization

```text
Mach lookup → bootstrap → NSXPC listener → accept → AMFIProtocol dispatch → getter
```

- lookup/bootstrap: not recoverable from available materials;
- accept: visible callback has no audit/entitlement/rejection branch and returns `1`;
- dispatch: both getters are confirmed members of `AMFIProtocol`;
- handler: neither getter has a visible local entitlement/audit check;
- framework/transport policy: possible but not recovered.

The correct result is not “unrestricted” and not “inaccessible”; it is **NOT VERIFIED**.

## 6. Information sensitivity

### `getSEPStateWithReply:`

Reads `LAStorage dataForKey:0xf`, copies 49 bytes and returns:

```text
{ u32, u32, u32, { u8, { u32, u8[32] } } }
```

No raw key, credential, PII or protected secret is identified. The meaning of key `0xf` and 32-byte field is unknown. Best-supported classification: internal system/diagnostic metadata, LOW–MEDIUM sensitivity.

### `getStagedProfileWithReply:`

Reads the full UTF-8 contents of `/private/var/db/amfid/UPPStaging.plist` and returns the string without plist parsing or filtering. The normal writer is `stageProfileForUuid:`, which is entitlement-gated and writes a UUID-like string. Exact runtime contents are not extracted. Best-supported classification: staging/system metadata, LOW–MEDIUM sensitivity; arbitrary extra file content remains UNKNOWN.

## 7. Evidence matrix

| Method | A Exported | B Mach lookup | C Connect/invoke | D Insufficient authz | E Protected result |
|---|---|---|---|---|---|
| `getSEPStateWithReply:` | CONFIRMED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| `getStagedProfileWithReply:` | CONFIRMED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |

Neither method satisfies the evidence threshold for a confirmed security issue.

## 8. False-positive controls

Phase 8 explicitly rejects these inferences:

- exported method = public App Store API;
- accepted NSXPC connection = successful Mach lookup;
- no local entitlement check = no authorization anywhere;
- system metadata = secret;
- B2/B3 behavior = RC behavior;
- static string presence/absence = effective runtime policy.

## 9. Final status

| Method | Status |
|---|---|
| `getSEPStateWithReply:` | **INSUFFICIENT EVIDENCE** |
| `getStagedProfileWithReply:` | **INSUFFICIENT EVIDENCE** |

No `CONFIRMED SECURITY ISSUE` and no `PLAUSIBLE / NEEDS VALIDATION` finding was established. No reachability hypothesis was `RULED OUT`, because the required launchd/bootstrap and effective sandbox policy are absent.

## 10. Recommendation

Defer rather than close the broad `amfid` direction. Continue only if the following become available:

1. amfid/MobileFileIntegrity launchd plist;
2. bootstrap namespace and service visibility metadata;
3. decoded effective sandbox profiles and Mach lookup rules for ordinary/system clients;
4. RC amfid and policy material;
5. semantic documentation or implementation for LAStorage key `0xf` and the UPP staging format.

With the current corpus, the exact successful conclusion is: **server-side getter export and missing local gates are confirmed; transport reachability for unprivileged clients and protected-information disclosure are not established.**
