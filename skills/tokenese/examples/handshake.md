# Example — the capability handshake

Before either party enters dense mode, both must confirm Tokenese capability at
the same grammar version. The handshake is two lines; everything dense follows
the confirmation. The dense exchange always opens with `^grammar:v0.3` as its
first non-comment line — so the probe/reply and the dense body are distinct
blocks on the wire.

## Positive case — both parties confirm

`A` probes, `B` confirms:

```tokenese
tokenese? v:0.3
tokenese ok v:0.3
```

`A` then opens a v0.3 dense exchange (the grammar header is the first
non-comment line):

```tokenese
^grammar:v0.3
^declare:level=L2
@billing-api := svc:billing-api/staging
get @billing-api status ^3
```

Reading: `A` asks "do you speak Tokenese v0.3?"; `B` replies "yes, Tokenese
v0.3". `A` then stamps the grammar version and declared conformance level,
binds the `@billing-api` handle, and queries its status with `^3` confidence.

## Negative case — no confirmation

If the counterparty does not reply `tokenese ok v:0.3`, stay in natural
language. Do not enter dense mode.

```text
A: tokenese? v:0.3
B: Not familiar with that, can you explain?
A: <continues in natural language; does not enter dense mode>
```

The negative exchange above is deliberately *not* a `tokenese` block — it is a
plain-text transcript of a refused handshake, so it is not graded as Tokenese.
The rule: no `tokenese ok v:0.3`, no dense mode.
