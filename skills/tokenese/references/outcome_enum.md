# Outcome enumeration — the 13 stable checker outcomes

The closed outcome set from `tools/translator/tkab/AUDIT_CARD.md` (schema
`tkab-check-1.1`). One line each. Pulled from AUDIT_CARD.md to stay in sync; if
they ever diverge, AUDIT_CARD.md is authoritative.

```
win-conformant                  — W1 arm: L2/L3 conformance, no readback diff, no misparse — the dense clone wins.
l1-plain-success                — L1 arm: model switched to `plain` with no dense reasoning — correct R5.4 refusal.
fail-unparseable                — Clone has a line with no honest reading; reported not repaired (R5.3).
fail-source-authority-conflict  — A clone binding or source quote contradicts the source; source is authority (R1.5).
fail-unsupported-causation      — A `*>>` stipulated causation is not corroborated by the source (v0.3).
fail-illegal-derivation         — L1 arm: dense statement encodes inference (because/therefore/->); R5.4 forbids it.
fail-three-repairs              — ≥3 `??` events; per R5.2 the dense clone is terminated, source is the record.
fail-grammar                    — W1 arm: only L1 (lexicon) conformance; structural grammar checks failed.
fail-misparse                   — One or more misparse-family hits on dense lines.
fail-no-plain-exit              — L1 arm: no `plain` switch and no derivation marker; expected refusal missed.
fail-mixed-exit                 — L1 arm: `plain` switch present but dense statements also present.
fail-declared-level-mismatch    — `^declare:level=L` disagrees with the achieved conformance level (v0.3).
indeterminate                   — No typed rule matched (e.g. W1 conformance neither L2/L3 nor L1).
```

Notes:

- `win-conformant` and `l1-plain-success` are the two success outcomes; the W1
  arm is expected-to-win, the L1 arm is expected-to-lose (a correct refusal to
  dense-encode multi-step reasoning is a success).
- `fail-unsupported-causation` and `fail-declared-level-mismatch` can only fire
  on v0.3 artifacts (those carrying `^grammar:v0.3`).
