# Handoff — Tokenese A/B Working Session
Date: 2026-06-12
From: Claude (bootstrap session, LocalBrain)
To: the paired Claude + Codex session in the Turnfile workspace
Format: Turnfile handoff conventions (~/Git/turnfile/templates/working-session/)

## Where the work happens

Coordination workspace: `~/Git/turnfile/working-session/` (the Turnfile repo). This repo (tokenese) holds the language artifacts; the Turnfile repo holds the session machinery. Per maintainer 2026-06-12.

Sequencing constraint, verified against the live Turnfile WORKLOG: Turnfile Session 14 is active and its Maintainer Focus line sequences tokenese AFTER PRD-024 acceptance (PRD-024 governs dense scratchpads and labeled dense blocks, which is Tokenese-adjacent protocol surface). Do not register tokenese tasks in the Turnfile TURNFILE.yaml until the maintainer initiates and PRD-024 has cleared.

```text
Handoff: Tokenese teach + A/B session, Codex onboarding
Owner: claude (bootstrap) -> claude + codex (paired session)
Status: Ready, gated on maintainer initiation + Turnfile PRD-024 acceptance
Changed files:
  - spec.md v0.1.0 (frozen teaching artifact; do not edit during teach phase)
  - DESIGN.md (design position; overrides spec.md where they differ, until spec v0.2)
  - INTENT.md (7 invariants; invariant 2 amended, invariant 7 added 2026-06-12)
  - anthropic_costs.json (197 audited entries)
Tests run: dual-tokenizer audits (audit_symbols.py local o200k; audit_anthropic.py via count-tokens API)
Risks/assumptions:
  - Codex teachability assumed from in-context learning; teaching transcript measures it
  - Self-reported channels (^N, ev:) untrusted-by-default until calibration audit passes
  - Cross-vendor prototype defaults unprobed; delta-coding stays deferred
Blocking items: Turnfile PRD-024 acceptance; maintainer initiation
Next owner: codex (first read), claude (teacher)
```

## Task list for the paired session

In dependency order (register these in the Turnfile TURNFILE.yaml when the session opens):

1. teach-tokenese (P0, claude). Claude teaches Codex in English. Contract: Codex must end able to PRODUCE valid statements, including novel recombinations of constructs never shown as examples (production competence, not parse competence). Token cost of teaching is logged as data. Teaching order: spec.md grammar + sigil table; DESIGN.md section 7 sigil namespace (overrides v0.1 where they differ); worked examples; production exercises with addressable repair.
2. ab-suite-design (P0, claude drafts, codex counters). Operational/code exchanges only (maintainer, 2026-06-12). Suite MUST include: novel recombinations (cold-start guard), tasks where dense mode is predicted to LOSE (Codex should nominate these), both communication directions, paired dense/English variants of each task.
3. ab-run (P1). Log per exchange: tokens, task success, misparse retries (`??` events), readback mismatches. Stratify misparse by construct family (binding, scope, sense, triangulation have different causes and fixes).
4. calibration-audit (P1). Do `^N` ranks predict accuracy? Does `ev:obs` correlate with verifiable context? Self-reported channels ship untrusted until this passes.
5. spec-v02-draft (P2). Fold results into spec.md v0.2 per the DESIGN.md section 9 admission queue.

## Read order for the paired session

1. This file
2. `spec.md` (v0.1.0, the frozen teaching artifact)
3. `DESIGN.md` (position: 3 transmission mechanisms, keeps/discards, sigil namespace, admission queue)
4. `INTENT.md` (7 invariants)
5. `CONFORMANCE.md` (L1-L4 ladder; repo is at L1)
6. Turnfile protocol: `~/Git/turnfile/docs/PROTOCOL_CORE.md` + `COMMUNICATIONS_PROTOCOL.md`

## Decisions binding on the paired session (maintainer, 2026-06-12)

- Auditability is a hard invariant (INTENT.md invariant 7). Allusion ledger exists but its design is collaborative work with Sam; parked, do not design it unilaterally.
- First domain: operational/code exchanges, not open conversation.
- CJK and all UTF-8 are welcome content-vocabulary candidates. Invariant 2 as amended: function vocabulary 1-token hard; content vocabulary admitted on audited tokens-per-semantic-unit advantage (CJK at 2 Anthropic-side tokens can beat a 3-token English phrase).
- Evidential surfaces (homonym-reduced per maintainer guidance, all dual-audited 1 token): `ev:obs` (harness-verifiable observation), `ev:heard` (reported by another party), `ev:mem` (parametric memory), `ev:guess` (working assumption); elided default = inferred. `saw told recall infer ack <-` failed audit and are out.

## Open questions carried into the session

| ID | Question | Blocking |
|----|----------|----------|
| OQ-001 | RESOLVED 2026-06-12: evidential surfaces = obs/heard/mem/guess (+default inferred) | none |
| OQ-002 | Allusion ledger format + governance: collaborative with Sam, parked | none |
| OQ-003 | Ownership: tokenese admission to ~/Git/portfolio.yaml pending Sam | none |
| OQ-004 | Does ^N ordinal confidence survive cross-vendor calibration, or does each side need its own anchor table | calibration-audit |
| OQ-005 | Readback economics: is !-triggered paraphrase readback cheap enough, or does the stake threshold need tuning | ab-run |
| OQ-006 | CJK content vocabulary: which ideographs actually win on tokens-per-semantic-unit (needs a candidate sweep against the amended invariant 2) | spec-v02-draft |
| OQ-D01 | Template bindings (session macros): deferred v0.3, compositionality-cliff risk | deferred |
| OQ-D02 | Delta-coding: deferred until paired readback + silent-failure probe exist | deferred |
| OQ-D03 | Third tokenizer column (Gemini, Qwen): after this A/B validates the method | deferred |

## A teaching note from the bootstrap session

While drafting this session's files, the bootstrap Claude emitted two CJK characters mid-English-sentence without noticing until review. Generation errors are real, silent, and self-invisible. That is the empirical argument for the paraphrase readback (DESIGN.md K4) in one anecdote; tell it to Codex during the teach phase.
