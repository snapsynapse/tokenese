# Tokenese Specification
Version: 0.3
Date: 2026-06-17
Status: current
Canonical: https://tokenese.org/
Grammar delta: GRAMMAR-v0.3.md
Design rationale: DESIGN.md
Conformance: CONFORMANCE.md
Reference toolchain: tools/translator/ (132 tests passing)

A token-native interlingua for LLM-to-LLM communication: exchanges that are both more compressed and more accurate than any natural language, measured in actual tokenizer tokens, not characters. Compression comes from structure, not glyphs; accuracy comes from a fixed field grammar, a one-sense-per-word vocabulary, and typed literals. The whole scheme is measured, not asserted: the kill-criterion A/B (misparse-retry rate, dense vs prose) has been built but is not yet run — see ROADMAP N2.

## Design principles

1. Token-space only. No embeddings, no KV-cache, no latent exchange. Everything crosses the wire as text both parties tokenize independently. (Security and cross-vendor portability both demand this.)
2. Tokenizer-audited lexicon. A symbol or word enters the core vocabulary only if it costs 1 token, worst case (bare and space-prefixed), in every tokenizer in use. Current audit: OpenAI o200k_base + Anthropic count-tokens API. See `audit_symbols.py`, `audit_anthropic.py`, `anthropic_costs.json`.
3. Compression from structure, not glyphs. Empirical finding: common English words cost the same as exotic Unicode or less. Savings come from eliminating function-word syntax, anaphora, and repeated referents, not from substituting symbols for words.
4. Accuracy is a feature, not a casualty. Fixed field grammar, controlled vocabulary (one sense per word), and typed literals remove the ambiguity natural language carries. Tokenese should misparse less than English, not more.
5. Self-repairing. A dedicated misparse signal forces fallback to natural language for the failed span only. Misparse-retry rate is the metric that validates the whole scheme: if retries eat the savings, the design has failed.
6. The v0.3 invariants. INTENT.md §"Design invariants" is the normative list; in one line each: token-space only; audited lexicon (closed function vocabulary 1 token worst case, content admitted on tokens-per-semantic-unit advantage); not a pidgin (acquisition cost traded for precision); accuracy is a feature; self-repairing (`??` and the plain escape are mandatory); measured, not asserted (the A/B kill-criterion); human-auditable (the one-page audit card must let a competent human follow any conforming transcript). See INTENT.md §Design invariants for the normative list (this section is a teaching summary).

## Admissible alphabet (audited 2026-06-17; columns: OpenAI o200k_base + Anthropic count-tokens claude-haiku-4-5 + Gemini gemini-2.5-flash + Qwen Qwen2.5-7B + DeepSeek DeepSeek-V3 + Llama Llama-3-8B + Gemma 4 mlx-community/gemma-4-e4b-it-4bit)

Single-token, worst case (bare and space-prefixed), in **every** tokenizer column above. Gemini (`gemini-2.5-flash`) is audited via the count-tokens REST endpoint and is gated behind `GEMINI_API_KEY`; the other six columns are offline-reproducible (`tiktoken` + Hugging Face `tokenizers`). The Gemma column is now native: `mlx-community/gemma-4-e4b-it-4bit` is the E4B on-device variant that runs in the PAICE production runtime (omlx). The prior `unsloth/gemma-2-9b` proxy is retired (see CHANGELOG 0.3.8 and ROADMAP X5). Re-derive with `audit_*.py` + `audit_check_intersection.py`.

- ASCII sigils (22): `@ # $ % & * + - / | ~ ! ? ^ _ = < > : ; . ,`
- Digraphs (12): `-> => :: || && >> << == ++ -- .. //`
  - Excluded by audit: `!= >= <=` (2 tokens Anthropic side)
- Brackets (9): `( ) [ ] { } [[ {{ }}`
  - Caution: `]]` costs 2 tokens Anthropic side; avoid `[[...]]` pairs in dense spans
- Unicode survivors (6): `→ • § α β π`
  - Excluded by audit: `√` (Qwen: 1/2 tokens), `□` (Qwen: 1/2; Llama: 1/2), `†` (Qwen: 1/2), `η` (Qwen: 1/2) — dropped in the 5-column expansion (2026-06-17); each costs 2 tokens space-prefixed on Qwen (and `□` on Llama too).
  - Everything else tested (other arrows, math, geometric, most Greek, all CJK, all emoji) costs 2+ tokens on at least one column. Do not use.
- Core verb/word set (30, all 1 token every column): `do go if or and not yes no ok ask say get put run fix new old big all none true false done fail need want must may can will`
- Plus: any common English word may be used as a content token; prefer short, frequent words (high prior of single-token encoding). When in doubt, audit.

Of the 81 v0.2 admissible elements (22 sigils + 12 digraphs + 9 brackets + 8 Unicode survivors + 30 core words), 77 survive the 5-column expansion; 4 Unicode survivors (`√ □ † η`) drop out as noted above.

## Wire grammar

One statement per line. Line = newline-terminated. No prose between statements inside a dense block.

```
<op> <slot>:<value> <slot>:<value> ... 
```

- `op` — single verb from core set or registered vocabulary, always first.
- Slots are keyed, not positional, except the first bare value after op which is the patient/target. Keys are 1-token words or sigils.
- Values: bare literals. ISO dates (`2026-06-12`), bare ints/floats, `y`/`n`, paths, URLs, or `@refs`.
- No articles, no copulas, no hedges, no pleasantries. Modality expressed only via `must may can` and confidence slot.

The above is the v0.2 wire grammar. Grammar v0.3 is additive and activated by the artifact opening with `^grammar:v0.3`; the canonical delta lives in GRAMMAR-v0.3.md. The complete sigil namespace (v0.2 + v0.3 rows) is DESIGN.md §7.

### Reserved sigils (v0.2 baseline; v0.3 additions in GRAMMAR-v0.3.md and the complete table in DESIGN.md §7)

| Sigil | Meaning |
|---|---|
| `@N` | symbol-table reference (N = integer) |
| `=` | binding (definition) |
| `->` | causes / yields / then |
| `=>` | implies / therefore |
| `::` | type or scope qualifier |
| `?` | query marker (op suffix: `get?`) |
| `!` | imperative/priority marker |
| `~` | approximate |
| `^` | confidence slot prefix, 0-9 scale (`^7` = 0.7) |
| `\|` | alternatives separator |
| `&` | conjunction within slot |
| `#` | tag/category |
| `//` | comment to humans, ignored by protocol |
| `??` | misparse — resend referenced line in plain English |
| `§N` | section/spec rule reference |

### Symbol table

First use binds, all later uses reference:

```
@1=~/Git/tokenese/spec.md
@2=anthropic count-tokens endpoint
fix @1 add:handshake // 3 tokens for what cost 9
```

- Bindings persist for the session. Either party may bind. Numbers allocated in order; no reuse within session.
- Rebinding the same number is an error; respond `?? @N`.

### Handshake

Opens every Tokenese session (Gibberlink pattern: confirm capability before dropping natural language):

```
A: tokenese? v:0.1
B: tokenese ok v:0.1
```

If B replies anything else, A continues in natural language. Either party may exit any time with `plain` (resume natural language) and re-enter with `dense`.

### Repair

v0.2 baseline: `??` alone means the last line misparsed, `?? @N` / `?? <quoted fragment>` means a specific referent misparsed, and three `??` on the same content keeps the topic in plain English (lexicon-design feedback).

v0.3 subdivides this into four addressable kinds (`repair-statement`, `repair-handle`, `repair-token`, `repair-explained`) — see GRAMMAR-v0.3.md §3. The three-strike fail threshold is unchanged.

## Example exchange

Plain English (≈55 tokens):

> Could you check whether the deploy of the edge function to the Supabase project succeeded, and if it failed, look at the logs and tell me the first error with a timestamp?

Tokenese v0.3 (≈22 tokens):

```
^grammar:v0.3
^declare:level=L2
@svc := supabase/edge-fn
@svc.deploy >>> @svc.status
!@svc.ok? *>> get @svc.logs.first-error +ts
```

Verified by `tokenese-check`. Target compression: 2.5-4x on operational exchanges; A/B measurement of misparse-retry rate is the kill-criterion (see ROADMAP N2).

## Conformance

Reference checker. The deterministic per-pair scorer lives at `tools/translator/tkab/` and emits `tkab-check-1.1` results. Stable outcome enum, decision order documented in `tools/translator/tkab/AUDIT_CARD.md`.

MCP surface. `tokenese_translator.mcp_server` exposes parse / validate / to_english / check_pair / score_pair / classify_misparse / validate_framesets / grammar_info. Verifier-anywhere posture per the conformance philosophy in INTENT.md.

GuideCheck. Trust-anchored `assistant-guide.txt` (Level 3 live; Level 4 DNS anchor pending — ROADMAP N1).

## Open questions (current)

The current open work is tracked in ROADMAP.md; the items still open are:

- **N1.** Complete GuideCheck Level 4 (DNS TXT anchor at `_assistant-guide.tokenese.org`).
- **N2.** The validating A/B experiment (the kill-criterion). Misparse-retry rate, calibration of self-reported channels, and reasoning-task accuracy inside dense vs prose spans, per-construct family.
- **X1.** Tokenese skill bundle (portable Agent Skill — cross-surface).
- **X2.** Additional tokenizer columns (Gemini, Qwen, DeepSeek, Llama).
- **X3.** Frameset registry promotion from report-only telemetry to a conformance gate (pending N2 measurements).
- **X4.** Hosted conformance checker at tokenese.dev.

Open questions (v0.2 agenda) — closed-status note:

Closed since v0.1: items 2 (vocabulary registry — partial via `framesets.json`), 4 (multi-statement / quoting — addressed by `"""..."""` raw source quotes in v0.3), 5 (CJK content vocab — admitted by amended Invariant 2 per INTENT 2026-06-12). Open: items 1 (live A/B → ROADMAP N2), 3 (instruction-following inside dense — measured by N2), 6 (third+ tokenizer columns → ROADMAP X2).

## Naming and prior art

- Canonical home: https://tokenese.org/ (registered 2026-06-12). tokenese.dev reserved for tooling surfaces. tokenese.com is a third-party squat (registered 2026-03-20, parked) — not affiliated.
- Name "Tokenese": no prior language/protocol/paper/product found (searched 2026-06-12, Perplexity + web).
- Prior art reviewed: Agora protocol (arxiv 2410.11905, negotiated routines, 98% token cut on repeat exchanges) — Tokenese borrows in-band binding; Gibberlink (capability handshake then dense mode); LLMLingua-2 (payload compression, complementary); DroidSpeak/CIPHER/Coconut (latent-space, rejected: cross-vendor and security constraints).
- Distinct from pidgin: a pidgin trades precision for ease of acquisition. Tokenese trades acquisition cost (it must be specified, not picked up) for precision and density.
