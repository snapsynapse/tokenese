# Example — the repair protocol

Repair is the safety floor: any misparse gets an addressable `??` instead of a
full retry. All four kinds parse under `^grammar:v0.3`. The 3-strike rule
terminates the dense exchange when repair on the same content does not converge.

## The four repair kinds in context

A statement is (mis)parsed, then each repair kind addresses a different target:

```tokenese
^grammar:v0.3
@billing-api := svc:billing-api/staging
get @cluster status ^3
??
??@billing-api
??: timeout reading binding
?? cluster-status
```

- `??` alone — repair the last (mis)parsed statement (`repair-statement`).
- `??@billing-api` — repair an unresolved handle (`repair-handle`).
- `??: timeout reading binding` — repair with an explicit reason
  (`repair-explained`).
- `?? cluster-status` — token-level repair of a single token
  (`repair-token`).

Note: three `??` events appear here only as a *catalogue of kinds*, not as
three strikes on one piece of content — the targets differ. Real escalation is
below.

## The 3-strike escalation

Three `??` events on the same content terminate the dense exchange. The checker
fires `fail-three-repairs` at ≥3 repair events (R5.2); the source becomes the
record and the parties fall back to plain English on that topic.

```tokenese
^grammar:v0.3
get @cluster status ^3
??
??
??
```

Validates to: fail-three-repairs

After the third strike, drop dense mode for this topic:

```text
A: <3× ?? on cluster status did not converge>
A: Falling back to English: can you tell me the current cluster status and
   which node is unhealthy?
```

The plain-text block above is intentionally natural language — it is the
fallback, not a graded Tokenese statement.
