# Tokenese Roadmap

Status: living document. Last updated 2026-06-17 (post N3/X1/X2/L6 batch).

This roadmap is downstream of [INTENT.md](INTENT.md) and [DESIGN.md](DESIGN.md).
Every item must pass the admission criteria in INTENT: claims are measured not
asserted (invariant 6), new lexicon ships with tokenizer-audit evidence
(invariant 2), grammar changes preserve parse determinism (invariant 4), and
nothing breaks human-auditability (invariant 7) or the token-space-only rule
(invariant 1). Items that cannot meet those gates do not ship, however useful
they seem.

Horizons are priority bands, not dates. An item moves up only when its
dependencies are met.

## Shipped (baseline)

So the roadmap stays honest about what already exists:

- Grammar v0.3 with parser, renderer, and a centralized handle lexer; deterministic
  per-pair conformance checker; CLI (`tokenese-check`); MCP server (parse, validate,
  to-english, check-pair, score-pair); TKAB scoring harness. 144/144 tests.
- Initial report-only frameset registry (`framesets.json`) for common ops and
  canonical slot-order telemetry. This is an X3 partial, not a normative grammar
  gate: old artifacts still parse and score unchanged.
- Seven-column tokenizer-audited lexicon (OpenAI `o200k_base` + Anthropic
  count-tokens + Gemini + Qwen + DeepSeek + Llama 3 + Gemma 2 proxy),
  reproducible via `audit_*.py` + `audit_check_intersection.py`; CI-gated on regression.
  77 of 81 v0.2 admissible elements survive the expansion. **(X2 shipped v0.3.5)**
- Canonical landing page at https://tokenese.org/ (GitHub Pages, WCAG 2.1 AA).
- GuideCheck `assistant-guide.txt` at Level 3 live, Level 4 manifest in place
  (cross-channel DNS anchor pending, see N1).
- `spec.md` reconciled with v0.3 grammar; `relationships.yaml` and `ontology.json`
  promoted to v1.0.0 with v0.3 definitions. **(N3 shipped v0.3.3)**
- Portable Tokenese skill bundle at `/skills/tokenese/` (SKILL.md, MANIFEST.yaml
  with hashed provenance, audit_card, install_guide, 5 examples, references for
  sigil key + outcomes + decision order). 12 example-validation tests. **(X1 shipped v0.3.4)**
- `RELEASE_CHECKLIST.md` shipped with security-hardening-release pass
  (`audit_anthropic.py` credential handling, `.gitignore` `*.env`). 3 new
  security tests at repo root. **(L6 shipped v0.3.6)**

## Now (credibility-defining)

### N1. Complete GuideCheck Level 4

Publish the guide `sha256` on one independent control plane: a DNS TXT record at
`_assistant-guide.tokenese.org`. This is the only gap between the current Level 3
posture and full Level 4. Small, finishes the conformance story.
Tie: adoptability (verifiable provenance for any assistant that fetches the guide).

### N2. The validating A/B experiment (the kill-criterion)

The central claim, more compressed AND more accurate, is unproven until measured.
Run a live A/B between model families (Claude vs Codex, then a third) on a fixed
task suite, measuring, per construct family: misparse-retry rate, calibration of
self-reported channels, and reasoning-task accuracy inside dense vs prose spans
(DESIGN section 9). Add cold-start conformance: a fresh model given only the spec
must parse novel recombinations, not just spec-shaped examples.
Tie: invariant 6. This converts "a designed language" into "a measured language,"
which is the single biggest credibility and adoption lever. If retries eat the
savings, the spec says the design has failed; this is the experiment that says so.

## Next (adoptability and utility)

### X3. Vocabulary and frameset registry

A shared controlled-vocabulary file: one entry per op as a typed slot signature
(`deploy :: who what to:env -> status`), so both parties train against the same
surface (DESIGN K5; spec open question 2). Increases parse determinism and makes
malformed statements structurally detectable before semantic misparse.
Tie: invariant 4, utility.

Status: partially landed as report-only telemetry. Promotion to a conformance
gate is deferred until N2 measures whether the diagnostics predict real
misparse/retry reductions.

### X4. Hosted conformance checker

A verifier-anywhere web surface at `tokenese.dev` (reserved for tooling) that
validates a pasted or fetched transcript against the grammar and returns the
per-pair outcome, mirroring the offline checker. Add a conformance badge.
Tie: conformance philosophy (no central oracle, verifier-anywhere); adoptability.

## Later (ecosystem and reach)

### L1. Reference SDKs beyond Python

Thin encode/decode/validate libraries in TypeScript and Go so non-Python stacks
can integrate without shelling out. Token-space-only keeps the surface portable.
Tie: utility, integration reach.

### L2. Publish the MCP server

List the existing MCP server in a registry (via the mcp-server-publish flow) so
agents can discover and call it without cloning the repo.
Tie: adoptability.

### L3. Turnfile integration demo

A worked example of Tokenese as the envelope payload for a multi-agent Turnfile
session, with the handshake and repair protocol in a real exchange.
Tie: INTENT relationships (Turnfile is the candidate envelope); concrete interop.

### L4. Execute the remaining DESIGN v0.2 admission queue

Land the constructs from DESIGN section 9 not yet in the grammar, each with its
tokenizer audit and its validity-preserving string edits (the Leibniz criterion,
DESIGN R2): distribution slots, stake-scaled paraphrase readback on `!`,
evidentials with the harness-verifiable `ev:obs` split, corpus anchors with the
gloss handshake, and typed holes. Never compress derivation (DESIGN R1).
Tie: the spec's own normative roadmap; each item is gated by N2's measurements.

### L5. Promotion and distribution

Generate the `og.png` social card (currently omitted) and run the promo flow
(dev.to, blog, LinkedIn) once N2 has a result worth announcing. Announce on
evidence, not intent.
Tie: adoption; deliberately sequenced after N2 so the pitch is measured.

## How items get promoted

An item moves from Later to Next to Now when (1) its dependencies are met, and
(2) it can demonstrate it passes the INTENT admission gates. N2 is the gravity
well: most Later items are worth more after there is a measured result to stand on,
and several are explicitly sequenced behind it.
