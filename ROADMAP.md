# Tokenese Roadmap

Status: living document. Last updated 2026-06-18 (X5 + L8 shipped; X6/X7 + L7/L9 carried).

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
  count-tokens + Gemini + Qwen + DeepSeek + Llama 3 + Gemma 4 E4B native),
  reproducible via `audit_*.py` + `audit_check_intersection.py`; CI-gated on regression.
  77 of 81 v0.2 admissible elements survive the expansion. **(X2 shipped v0.3.5; Gemma column promoted to native Gemma 4 in X5 v0.3.8)**
- Canonical landing page at https://tokenese.org/ (GitHub Pages, WCAG 2.1 AA).
- GuideCheck `assistant-guide.txt` at Level 4 live: repo + sidecar-manifest
  sha256 + DNS TXT anchor at `_assistant-guide.tokenese.org`.
- `spec.md` reconciled with v0.3 grammar; `relationships.yaml` and `ontology.json`
  promoted to v1.0.0 with v0.3 definitions. **(N3 shipped v0.3.3)**
- Portable Tokenese skill bundle at `/skills/tokenese/` (SKILL.md, MANIFEST.yaml
  with hashed provenance, audit_card, install_guide, 5 examples, references for
  sigil key + outcomes + decision order). 12 example-validation tests. **(X1 shipped v0.3.4)**
- `RELEASE_CHECKLIST.md` shipped with security-hardening-release pass
  (`audit_anthropic.py` credential handling, `.gitignore` `*.env`). 3 new
  security tests at repo root. **(L6 shipped v0.3.6)**
- GuideCheck Level 4 operational: DNS TXT record at
  `_assistant-guide.tokenese.org` advertises the live guide sha256 (cross-channel
  control plane independent of the hosted file). **(N1 shipped v0.3.7)**
- DNS-anchor drift guard (`check_dns_anchor.py` + `.github/workflows/dns_anchor.yml`):
  4-resolver TXT vs file-hash check on push to `main`, PR, and daily 12:17 UTC.
  Catches drift between the guide and the DNS anchor automatically. **(N4 shipped v0.3.7)**
- Gemma column promoted from `unsloth/gemma-2-9b` proxy to native Gemma 4
  (`mlx-community/gemma-4-e4b-it-4bit`, E4B on-device production runtime via
  omlx). New `audit_gemma4.py`; `audit_gemma.py` retired. **(X5 shipped v0.3.8)**
- Spec-page parity audit: `docs/index.html`, `docs/llms.txt`, `README.md`,
  `AGENTS.md`, and the `skills/tokenese/` bundle (1.0.1) refreshed to v0.3.8
  reality — seven tokenizer columns enumerated, native Gemma 4 noted, test
  count corrected (144 translator + 7 root = 151), GuideCheck Level 4
  reflected on the landing page and in the skill manifest. The
  DNS-anchored hosted assistant guide is intentionally untouched per
  RELEASE_CHECKLIST line 68. **(L8 shipped v0.3.8)**

## Now (credibility-defining)

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

### X6. Live tokenizer CI for the gated column

X2's Gemini column is gated behind `GEMINI_API_KEY` and skips cleanly without
one, so it currently rides on a single 2026-06-17 audit. Wire a CI secret and a
nightly job so the Gemini column is re-derived at the same cadence as the
offline columns and drift is caught fast. Same pattern can extend to any future
API-gated tokenizer (e.g. a hosted Anthropic model swap).
Tie: invariant 5, parity between offline and API-gated columns.

### X7. Skill-bundle hash drift guard

X1 (v0.3.4) pins three hashes in `skills/tokenese/MANIFEST.yaml` (SKILL.md,
audit_card.md, install_guide.md). Add a CI check via the shipped
`tools/skills/compute_hashes.sh` that fails when any of those files change
without the manifest being re-hashed. Mirrors the spirit of N4 at the skill
level.
Tie: skill provenance, GuideCheck alignment for the skill's own install guide.

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

### L7. Provenance-pin policy

Both N3 (v0.3.3) and X2 (v0.3.5) deliberately left
`tools/translator/data/source_provenance/*.json` untouched to keep
`_provenance()` byte-identical and the measurement claim stable across docs-only
releases. That was the right call — but the policy isn't written down. Document
when the provenance pins are allowed to roll forward (proposed: only on a
normative grammar minor bump, never on a patch release), and add a checklist
entry to `RELEASE_CHECKLIST.md` that calls out the decision explicitly.
Tie: invariant 6 (measured, not asserted); release discipline.

### L9. Reusable skill scaffolding

X1 shipped `tools/skills/compute_hashes.sh` as a one-off for the Tokenese skill
bundle. If a second skill ever ships (e.g. a Turnfile or GuideCheck skill),
generalize the script plus the MANIFEST schema into a reusable scaffold under
`tools/skills/scaffold/` so future bundles inherit GuideCheck-aligned provenance
for free.
Tie: portfolio reuse; not urgent until a second skill is on the docket.

## How items get promoted

An item moves from Later to Next to Now when (1) its dependencies are met, and
(2) it can demonstrate it passes the INTENT admission gates. N2 is the gravity
well: most Later items are worth more after there is a measured result to stand on,
and several are explicitly sequenced behind it.
