# Phase B Multi-Family A/B Suite Design — Strawman

**Status:** STRAWMAN — Claude-authored draft awaiting Codex + Maintainer apply-or-counter
**Date:** 2026-06-23
**Author:** Claude (Opus 4.7) via Turnfile session 1 inside `~/Git/tokenese`
**Source spec:** Tokenese HANDOFF.md "Next work" items 2-4
**Related Turnfile PRDs:** PRD-027 R6 + R6.5 (pilot exit criteria), PRD-035 (upstream result sync)

## What this strawman is for

HANDOFF.md item 2 says "Run the fixed operational/code task suite in English and Tokenese for Claude, Codex, and at least one third independent model family." The phrase "the fixed operational/code task suite" implies a definition exists. The existing TKAB fixtures (`tools/translator/tkab/fixtures/`) are the closest live artifact, but they're individual paired examples, not a coordinated A/B run plan.

This document proposes a concrete suite shape so coordinated runs across Claude / Codex / a third family can start producing comparable evidence. It does NOT mutate Tokenese semantics (PRD-027 R7 boundary preserved).

## Suite shape proposal

### S1. Task classes (≥4)

Each class is an "operational/code" exchange — the kind of message that flows in a normal multi-agent code-review or coordination session. For each class, an instance is a self-contained prompt that produces a bounded response.

1. **Deploy-status report** — model produces a one-paragraph deploy status (service, version, health, latency, migration triggers). Existing fixture: TKAB-W1-v03 + variations.
2. **Code-diff review summary** — model reviews a small unified diff (≤30 lines) and produces a 3-bullet review verdict: correctness / style / risk. New fixtures needed.
3. **Spec-amendment proposal** — model writes a short PRD-style amendment to an existing requirement: motivation + replacement text. New fixtures needed.
4. **Apply-or-counter reply** — model receives a proposed change and either APPLY-acknowledges with one sentence or produces a counter with concrete reason. New fixtures needed.

Optional class for dense-loses coverage:

5. **Free-text rationale** — model produces 2-3 sentences explaining WHY a decision was made under ambiguity. (Predicted dense-loses; preserved per HANDOFF item 4.)

### S2. Per-class fixture count

Each class needs ≥3 instances of varying complexity to avoid single-fixture overfit:

- 1 simple (baseline) instance
- 1 medium-complexity instance (typical session traffic)
- 1 edge-case / adversarial instance (tests the failure modes named in HANDOFF: binding, scope, sense, triangulation misparse families)

Total minimum: 4 classes × 3 instances × 2 encodings (English + Tokenese) × 3 model families = **72 paired exchanges**.

### S3. Per-exchange logging

Per HANDOFF item 3 + PRD-027 R6 #3:

| Field | What |
|-------|------|
| `model_family` | claude / codex / gemini / qwen / (third family) |
| `model_version` | exact model identifier |
| `class` | S1 task class label |
| `instance_id` | fixture id |
| `encoding` | english / tokenese |
| `prompt_tokens` | input token count |
| `response_tokens` | output token count |
| `wall_time_ms` | total time |
| `task_success` | pass / fail / partial (judged from the English source authority, not the Tokenese form per PRD-027 R5.4) |
| `misparse_events` | count of `??` events |
| `repair_events` | count of repairs (silent repair forbidden per HANDOFF constraint) |
| `readback_mismatch` | yes / no / n/a (was readback consistent with source?) |
| `misparse_family` | binding / scope / sense / triangulation / none |
| `notes` | free text — anomalies, surprises |

### S4. Compression-claim discipline

Per HANDOFF constraint: "Compression claims must compare against terse or equal-precision English, not verbose English." The English baseline for each pair is the terse-but-complete form. If a Tokenese clone wins on tokens against a verbose English form but loses to the terse English form, the headline result is "loses" or "break-even" depending on margin.

### S5. Dense-loses preservation

Per HANDOFF item 4: class S5 (free-text rationale) is the explicit dense-loses lane. Additionally, any instance flagged "predicted_outcome: lose" in TKAB fixtures should be carried into Phase B unchanged.

### S6. Third independent model family

Suggested options (Maintainer picks):

- **Gemini Flash via API** — most accessible third family; reasoning tier distinct from Codex (GPT-5 family) and Claude (Anthropic family)
- **Local Qwen 3.6 35b MLX** — already onboarded as PROVISIONAL CHECKER per PRD-042; would extend Qwen's role
- **GPT-4o via API** — different lineage from Codex's GPT-5 surface
- **A different Claude tier** (Haiku) — weakest independence; same family. Probably not "independent" enough per the HANDOFF item 2 spirit.

Recommendation: Gemini Flash via API for first independent-family pass; local Qwen for second pass if results differ.

### S7. Per-family run protocol

For each model family running through the suite:

1. Run all S1 classes × 3 instances in English first.
2. Run all S1 classes × 3 instances in Tokenese.
3. Log per S3 schema into `working-session/docs/phase-b-run-<family>-<date>.json`.
4. Send results to Tokenese repo for `tokenese-n2-report` regeneration.
5. Send results to Turnfile repo for PRD-027 R6.5 exit-criteria evidence packet.

### S8. Exit-to-production threshold (per PRD-027 R6.5)

Maintainer ratified 2026-06-23: pilot exit needs three-peer agreement (Maintainer + ≥2 model families) on:

- compression ratio acceptable per-family per-class
- misparse rates below class-specific thresholds
- dense-loses cases acknowledged and bounded
- no construct family is unsafe at the proposed production scope

This strawman does NOT propose specific numeric thresholds. Maintainer + the participating model families will negotiate them after the first complete run produces baseline data.

## Open questions

1. **OQ-PhaseB-1: Third-family pick.** Maintainer's call — Gemini Flash, local Qwen, GPT-4o, or other. The strawman recommends Gemini Flash for first pass.
2. **OQ-PhaseB-2: New fixture authorship.** Classes S2-S5 need new TKAB-style fixtures. Codex is the natural author per existing fixture authorship pattern.
3. **OQ-PhaseB-3: Numeric thresholds.** Should this strawman commit to compression-win thresholds (e.g. ≥15% token reduction at equal task-success rate) or wait for baseline data?
4. **OQ-PhaseB-4: Concurrent run vs sequential.** Should all three families run independently and submit results, or should runs be coordinated session-by-session?

## Requested next action

This strawman is routed to Codex (apply-or-counter on suite shape) and Maintainer (decision on OQ-PhaseB-1 through OQ-PhaseB-4). No Tokenese semantics changes; no Tokenese tools modified.
