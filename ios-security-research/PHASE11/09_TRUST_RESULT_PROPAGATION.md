# Phase 11 Report 09 — Trust Result Propagation

Goal: understand how the validator's result fields (`isValid`,
`profile_valid`, `areEntitlementsValidated`, `profileAuxSig`,
`computedCdHash`, `signerType`) are produced, packed into the MIG reply,
and consumed by the caller — specifically whether `isValid=1` together with
`profile_valid=0` is a *reachable, meaningful* combination.

## 1. Where each result field is produced

Source of truth for the validator output is `sub_100004030` in `amfid` (B3
disasm). From the disassembly:

```
sub_100004030:
    ; 1. zero-initialise output structure
    ; 2. read security-token-like input from MIG message
    ; 3. validate that input
    ; 4. allocate AMFIPathValidator_ios
    ; 5. call initWithURL:withFileOffset:withFlags:
    ; 6. call validateWithError:
    ; 7. on success:
    ;       computedCdHash:withLength:  → fills caller-provided buffer
    ;       signerType                  → integer in reply
    ;       isValid                     → boolean in reply
    ;       areEntitlementsValidated    → boolean in reply
    ;       profileData                 → blob
    ;       profileAuxSig               → blob via vm_read
```

All seven output fields are populated **after** `validateWithError:`
returns. The fields are written independently — no atomic "all-or-nothing"
guard is visible in the B3 disasm.

## 2. Where `profile_valid` could diverge from `isValid`

`AppleMobileFileIntegrity` framework holds two *distinct* failure
vocabularies:

**Signature/CodeDirectory failures** (from `__TEXT` strings):
- `The signature on the file is invalid`
- `The file is unsigned`
- `The file is adhoc signed or signed by an unknown certificate chain`
- `The file is adhoc signed but contains restricted entitlements`

**Profile-matching failures** (from `__TEXT` strings):
- `Profile matching service is unavailable`
- `Profile requested is not currently staged`
- `The best matching profile has expired`
- `The best matching profile is not valid for this device`
- `The best matching profile is not validly signed`
- `No matching profile found`
- `The best matching profile does not provision the certificates used to sign this file`
- `The best matching profile does not match the entitlements of this file`
- `The entitlements in this file are malformed`

These are **separate classes of failure** — the signature can validate
while profile matching fails. A validator that reports `isValid` on the
signature axis and `profile_valid` on the profile axis can produce the
combination `isValid=1, profile_valid=0`.

However: a validator that treats "signature valid AND profile valid" as a
single pass/fail would produce only `isValid=0, profile_valid=0` or
`isValid=1, profile_valid=1`. The deciding evidence is the MIG reply-packing
code — which lives in `amfid` and has not been fully disassembled for this
phase.

## 3. MIG reply packing

`sub_10000b194` is the MIG caller for `verify_code_directory`. From the B3
disasm it marshals the validator outputs into a `reply` structure. The
reply fields are populated sequentially; a failure path in the middle of
the sequence can leave trailing fields at their zero-initialised values.

**Critical question:** does `sub_10000b194` early-return on `isValid=0`
*before* reading `profile_valid`/`profileAuxSig`, or does it always fill
all fields? Phase 10 and Phase 11 have not disassembled enough of
`sub_10000b194` to answer this. The MIG reply structure layout is what
matters.

## 4. Caller-side interpretation

There is no recovered MIG client binary — `misagent`, `online-auth-agent`,
or other potential callers are not in the local image set. Without a
caller, the hypothesis "caller accepts `isValid=1` with `profile_valid=0`
and acts on it" is **undecidable**.

## 5. Errors after successful validation

Even if `validateWithError:` returns success, the subsequent fields can
fail:

- `computedCdHash` — could return a zero-length buffer if CodeDirectory
  parsing fails.
- `profileData` — could be empty if no profile matched.
- `profileAuxSig` — explicitly *optional*: `HasAuxiliarySignature` column in
  `mis.db` indicates presence is conditional, and accessor names
  (`_getProfileAuxiliarySignature`, `_getTeamIDAuxiliarySignature`,
  `_createAuxiliarySignature`) suggest on-demand generation.

`amfid`'s `sub_100004030` reads `profileAuxSig` via `vm_read` after the
other fields — consistent with optional/conditional presence, not a
mandatory field.

## 6. Fields preserved on error

When `validateWithError:` fails:
- `isValid` is expected to remain 0.
- `profileData`/`profileAuxSig` are expected to be absent.
- `areEntitlementsValidated` would remain 0 because the validator bailed.

Whether the caller distinguishes "signature-valid-but-profile-missing"
from "everything-failed" depends entirely on the reply structure. The MIG
caller (`sub_10000b194`) decides this. That disassembly has not been
performed in this phase.

## 7. P9-H1 assessment

`isValid = 1, profile_valid = 0`:

| Condition | Status |
|---|---|
| The two fields are independent | PARTIALLY VERIFIED — they are produced by separate validator outputs and copied independently |
| The combination is reachable | NOT VERIFIED — depends on whether `validateWithError:` can return success while profile matching fails; requires `AMFIPathValidator_ios` internals |
| A real MIG caller consumes the combination | NOT VERIFIED — no client binary |
| The combination leads to a security consequence | NOT VERIFIED — cannot be asserted without caller semantics |
| There is no independent check elsewhere | NOT VERIFIED — `installd` performs its own `MICodeSigningVerifier` check (defense in depth) |

**Status: PARTIALLY VERIFIED — the necessary preconditions (independent
fields, distinct failure vocabularies) are confirmed; the reachability and
consumer-side semantics are not.**

## 8. What would be needed to settle P9-H1

1. Disassembly of `sub_10000b194` (MIG caller) to see whether reply fields
   are packed conditionally.
2. Disassembly of `AMFIPathValidator_ios`'s `validateWithError:` to see
   whether the signature and profile checks are serialised or independent.
3. A real client binary (`misagent`, `online-auth-agent`, or the XPC
   consumer of `verify_code_directory`) to see how the reply is consumed.

Items 1 and 2 are inside `amfid` itself — recoverable from the existing B3
disasm without needing `__LINKEDIT`. Item 3 requires a client binary that
is not present locally.
