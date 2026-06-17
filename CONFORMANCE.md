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

## v0.3 admissibility rules

These rules apply only to artifacts that open with `^grammar:v0.3`. v0.2
artifacts are graded exactly as before (full backward compatibility).

- **Closed plain regions are not graded.** Content inside `^plain<<<` …
  `>>>^plain` is captured verbatim and is excluded from C2/C3 grammar and
  misparse checks. It is natural English by declaration, not Tokenese.
- **Declared level must match achieved level.** When an artifact carries
  `^declare:level=L`, the checker compares the declaration against the level
  actually achieved by the C1/C2/C3 ladder. A mismatch is reported as
  `fail-declared-level-mismatch`; the checker does not coerce the level.
- **`*>>` stipulated causation requires source corroboration.** An asserted
  causal link (`left *>> right`) is admissible only when the source text
  corroborates it (both operands' English labels appear within 80 characters
  of a causal cue word). Uncorroborated stipulated causation is
  `fail-unsupported-causation`; the source remains authority (R1.5).
- **`?>>` hypothesized causation is always admissible.** A hypothesis is a
  claim about a possibility, not an assertion about the source, so it needs no
  corroboration. `>>>` temporal sequence is likewise always admissible.
- **`!` negation and `?` hedge compose freely.** `!@h` is "not h", `@h?` is
  "possibly h", and `!@h?` is "possibly not h". Neither operator changes the
  canonical handle name, so they never affect handle resolution.

## Current status of this repo

The spec itself is at L1: the published admissible alphabet has full dual-tokenizer audit evidence (`anthropic_costs.json` + reproducible scripts). L2-L4 await the first live inter-model sessions. A mechanical parser/checker now ships in `tools/translator` (grammar v0.3, schema `tkab-check-1.1`).
