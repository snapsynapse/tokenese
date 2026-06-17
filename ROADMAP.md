# Tokenese Roadmap

Status: living document. Last updated 2026-06-17.

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
  to-english, check-pair, score-pair); TKAB scoring harness. 121/121 tests.
- Dual-tokenizer lexicon audit (OpenAI `o200k_base` + Anthropic count-tokens),
  reproducible via `audit_symbols.py` / `audit_anthropic.py`.
- Canonical landing page at https://tokenese.org/ (GitHub Pages, WCAG 2.1 AA).
- GuideCheck `assistant-guide.txt` at Level 3 live, Level 4 manifest in place
  (cross-channel DNS anchor pending, see N1).

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

### N3. Reconcile spec.md with the v0.3 grammar

`spec.md` still reads Version 0.1.0 while `GRAMMAR-v0.3.md` is current, and the two
have drifted. Fold the v0.2/v0.3 normative grammar into a single layered spec (or a
clear spec + delta structure) so an adopter reads one authoritative source.
Tie: invariant 7 (human-auditable) and reduced adopter confusion.

## Next (adoptability and utility)

### X1. Tokenese skill bundle

A portable Agent Skill that teaches any assistant to actually speak Tokenese:
run the capability handshake, encode and decode via the reference translator,
validate a transcript with the deterministic checker, use the repair protocol,
and consume the `assistant-guide.txt` before acting. Ship the one-page human audit
card (sigil key, anchor scales, allusion ledger) as part of the bundle.

- Cross-surface by design (Claude, ChatGPT, Gemini, Qwen), per the portfolio
  intent that skills work everywhere and the token-space-only invariant that makes
  Tokenese vendor-neutral.
- Skill Provenance tracked (`MANIFEST.yaml` + hashed `SKILL.md` + `CHANGELOG.md`),
  GuideCheck-aligned for its own install guide.

Tie: this is the highest-leverage "agents actually use it" item. The spec, page,
and guide make Tokenese legible; the skill makes it operable.

### X2. Additional tokenizer columns

Add audit columns for Gemini, Qwen, DeepSeek, and Llama tokenizers, with CI that
fails on regressions. New columns are additive: they may shrink the admissible
alphabet, never silently expand it.
Tie: invariant 5. Required before claiming cross-vendor generality beyond the
current OpenAI + Anthropic pair.

### X3. Vocabulary and frameset registry

A shared controlled-vocabulary file: one entry per op as a typed slot signature
(`deploy :: who what to:env -> status`), so both parties train against the same
surface (DESIGN K5; spec open question 2). Increases parse determinism and makes
malformed statements structurally detectable before semantic misparse.
Tie: invariant 4, utility.

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

### L6. Repo-standards follow-ups

Add `RELEASE_CHECKLIST.md` and run security-hardening-release (the repo is hosted
and agent-facing; this row is now applicable per INTENT exceptions).
Tie: repo standards.

## How items get promoted

An item moves from Later to Next to Now when (1) its dependencies are met, and
(2) it can demonstrate it passes the INTENT admission gates. N2 is the gravity
well: most Later items are worth more after there is a measured result to stand on,
and several are explicitly sequenced behind it.
