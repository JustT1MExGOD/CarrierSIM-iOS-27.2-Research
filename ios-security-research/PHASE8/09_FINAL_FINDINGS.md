# PHASE8 — 09_FINAL_FINDINGS

## `getSEPStateWithReply:`

**Final status: `INSUFFICIENT EVIDENCE`.**

### Confirmed

- method is exported through `AMFIProtocol`;
- method is implemented at `0x100004c0c` in B2/B3;
- visible handler has no entitlement/audit-token check;
- response is a fixed 49-byte structure derived from `LAStorage dataForKey:0xf`.

### Not verified

- ordinary App Store client can perform Mach lookup;
- ordinary client can establish NSXPC connection;
- no transport/framework authorization applies;
- key `0xf` contains protected information;
- response is prohibited to the relevant client category.

### Why not a security issue

The required client reachability and protected-result conditions are not established. The handler’s lack of a local gate is an architectural observation, not proof of boundary violation.

## `getStagedProfileWithReply:`

**Final status: `INSUFFICIENT EVIDENCE`.**

### Confirmed

- method is exported through `AMFIProtocol`;
- method is implemented at `0x100006230` in B2/B3;
- handler reads `/private/var/db/amfid/UPPStaging.plist` as UTF-8 text;
- it returns the read string without plist field filtering;
- normal write-side path is entitlement-gated by `com.apple.private.amfi.schedule-profile`.

### Not verified

- ordinary App Store client can perform Mach lookup/connect;
- staged file content is always only an UUID;
- returned content is protected information for the relevant client category;
- transport or filesystem policy provides the missing authorization.

### Why not a security issue

The read/write asymmetry is a genuine architectural observation, but no insufficiently privileged reachable client and no protected disclosure are proven.

## Overall classification

| Classification | Result |
|---|---|
| `CONFIRMED SECURITY ISSUE` | none |
| `PLAUSIBLE / NEEDS VALIDATION` | none as a concrete vulnerability |
| `ARCHITECTURAL OBSERVATION` | exported ungated getters; accept-all callback; read/write asymmetry |
| `RULED OUT` | no claim about actual ordinary-client reachability is ruled out |
| `INSUFFICIENT EVIDENCE` | both methods and transport reachability |

## Missing evidence that would change the result

1. amfid launchd plist with `MachServices` and bootstrap/session properties;
2. decoded effective sandbox profiles for App Store, system and privileged clients;
3. compiled policy evaluation showing allow/deny for `com.apple.amfi.nsxpc`;
4. client-side entitlement/exception mapping;
5. RC amfid and corresponding policy artifacts;
6. semantic mapping of LAStorage key `0xf` and authoritative UPP staging format.

## Recommendation

Do not close the broad evidence gap as `RULED OUT`, but do not continue treating the two methods as a likely vulnerability based solely on server-side absence of gates. Continue only if launchd/bootstrap and effective sandbox policy artifacts become available; otherwise mark the direction as **deferred / insufficient evidence**.
