# Worklog — Tokenese

References:
- `../spec.md` (v0.1.0), `../DESIGN.md` (design position), `../INTENT.md` (invariants), `../CONFORMANCE.md` (L1-L4)
- Turnfile protocol: ~/Git/turnfile/docs/PROTOCOL_CORE.md

Now Working (claude): idle — workspace bootstrapped, awaiting paired session
Now Working (codex): not yet onboarded
Maintainer Focus: initiate Codex session; collaborative ledger design parked until after A/B
Next Review Checkpoint: after teach-tokenese completes (review teaching transcript + token cost)

## Decision Index

| Decision | Owner | Timestamp | Section |
|----------|-------|-----------|---------|
| Auditability is a hard invariant (INTENT.md invariant 7); ledger is collaborative work, deferred | Maintainer | 2026-06-12 | Session 0 |
| First domain = operational/code exchanges, not open conversation | Maintainer | 2026-06-12 | Session 0 |
| A/B work happens in this repo via Turnfile working-session pattern | Maintainer | 2026-06-12 | Session 0 |
| Sigil namespace, keeps/discards, v0.2 queue locked in DESIGN.md | Claude | 2026-06-12 | Session 0 |

## Session 0 — 2026-06-12

### Claude: Workspace bootstrap

2026-06-12 — Repo provisioned (Repo Standards v0.4 open-spec tier), spec v0.1.0 drafted, dual-tokenizer audit run (181 entries in anthropic_costs.json), design round completed (5 lenses + 2 critiques), DESIGN.md position committed, Turnfile working-session scaffolded.

**Key decisions:**
- Token-space only; auditability hard invariant; never compress derivation
- Evidential surfaces obs/src/guess audited-in; saw/told/recall/infer/ack/<- audited-out

```text
Handoff: Tokenese A/B working session, Codex onboarding next
Owner: claude
Status: Complete (bootstrap)
Changed files:
  - working-session/* (this scaffold)
  - INTENT.md (invariant 7)
Tests run: tokenizer audits (audit_symbols.py local; audit_anthropic.py via API)
Risks/assumptions:
  - Codex teachability assumed from in-context learning; teaching transcript will measure it
  - Calibration of self-reported channels unproven; untrusted-by-default until calibration-audit passes
Blocking items: none
Next owner: codex (read boot-codex.md, ack via MAILBOX MSG-20260612-001)
```
