# Tokenese Conformance

Version: 0.1.0
Date: 2026-06-12
Status: draft (mirrors spec.md v0.1.0)

Testable claims, no central oracle. Anyone can verify a conformance claim offline with the artifacts in this repo.

## Claim classes

### C1: Lexicon admissibility

Claim: every element of an implementation's vocabulary costs 1 token, worst case (bare and space-prefixed), in every tokenizer the implementation certifies.

Verify: run `audit_symbols.py` (OpenAI side) and `audit_anthropic.py` (Anthropic side) against the vocabulary list. All elements must report cost 1.

### C2: Grammar conformance

Claim: a transcript parses under the wire grammar in spec.md (one statement per line, op-first, keyed slots, reserved sigils used per the sigil table).

Verify: mechanical parse of the transcript. Any line that admits two readings, or uses an unreserved sigil in a reserved position, fails.

### C3: Repair conformance

Claim: the implementation honors `??` (plain-English resend), `plain` (mode exit), and `dense` (mode re-entry), and never continues dense after three `??` on the same content.

Verify: transcript inspection against the repair rules in spec.md.

## Conformance levels

| Level | Requirements |
|---|---|
| L1 Lexicon | C1 passes for the full vocabulary in use |
| L2 Grammar | L1 + C2 passes on a complete session transcript |
| L3 Repair | L2 + C3 demonstrated in at least one transcript containing a repair event |
| L4 Measured | L3 + published A/B token counts and misparse-retry rate vs natural-language baseline on the same tasks |

## Current status of this repo

The spec itself is at L1: the published admissible alphabet has full dual-tokenizer audit evidence (`anthropic_costs.json` + reproducible scripts). L2-L4 await the first live inter-model sessions. A mechanical parser/checker is an open deliverable.
