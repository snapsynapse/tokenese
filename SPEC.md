# Tokenese v0.1 (draft)

A token-based interlingua for LLM-to-LLM communication. Goal: exchanges that are both more compressed and more accurate than any natural language, measured in actual tokenizer tokens, not characters.

Status: draft. Authored 2026-06-12 in session with Sam Rogers. Not yet tested against a second model family.

## Design principles

1. Token-space only. No embeddings, no KV-cache, no latent exchange. Everything crosses the wire as text both parties tokenize independently. (Security and cross-vendor portability both demand this.)
2. Tokenizer-audited lexicon. A symbol or word enters the core vocabulary only if it costs 1 token, worst case (bare and space-prefixed), in every tokenizer in use. Current audit: OpenAI o200k_base + Anthropic count-tokens API. See `audit_symbols.py`, `audit_anthropic.py`, `anthropic_costs.json`.
3. Compression from structure, not glyphs. Empirical finding: common English words cost the same as exotic Unicode or less. Savings come from eliminating function-word syntax, anaphora, and repeated referents, not from substituting symbols for words.
4. Accuracy is a feature, not a casualty. Fixed field grammar, controlled vocabulary (one sense per word), and typed literals remove the ambiguity natural language carries. Tokenese should misparse less than English, not more.
5. Self-repairing. A dedicated misparse signal forces fallback to natural language for the failed span only. Misparse-retry rate is the metric that validates the whole scheme: if retries eat the savings, the design has failed.

## Admissible alphabet (audited 2026-06-12)

Single-token in both o200k_base and Anthropic (claude-haiku-4-5) tokenizers, worst case:

- ASCII sigils (22): `@ # $ % & * + - / | ~ ! ? ^ _ = < > : ; . ,`
- Digraphs (12): `-> => :: || && >> << == ++ -- .. //`
  - Excluded by audit: `!= >= <=` (2 tokens Anthropic side)
- Brackets (9): `( ) [ ] { } [[ {{ }}`
  - Caution: `]]` costs 2 tokens Anthropic side; avoid `[[...]]` pairs in dense spans
- Unicode survivors (8): `→ √ • □ † § α β η π`
  - Everything else tested (arrows, math, geometric, most Greek, all CJK, all emoji except possibly `✅`) costs 2+ tokens on at least one side. Do not use.
- Core verb/word set (30, all 1 token both sides): `do go if or and not yes no ok ask say get put run fix new old big all none true false done fail need want must may can will`
- Plus: any common English word may be used as a content token; prefer short, frequent words (high prior of single-token encoding). When in doubt, audit.

## Wire grammar

One statement per line. Line = newline-terminated. No prose between statements inside a dense block.

```
<op> <slot>:<value> <slot>:<value> ... 
```

- `op` — single verb from core set or registered vocabulary, always first.
- Slots are keyed, not positional, except the first bare value after op which is the patient/target. Keys are 1-token words or sigils.
- Values: bare literals. ISO dates (`2026-06-12`), bare ints/floats, `y`/`n`, paths, URLs, or `@refs`.
- No articles, no copulas, no hedges, no pleasantries. Modality expressed only via `must may can` and confidence slot.

### Reserved sigils

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
@1=~/Git/tokenese/SPEC.md
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

- `??` alone — last line misparsed, resend in plain English.
- `?? @N` / `?? <quoted fragment>` — that referent misparsed.
- Three `??` on the same content → stay in plain English for that topic. Log the failure; it is lexicon-design feedback.

## Example exchange

Plain English (≈55 tokens):

> Could you check whether the deploy of the edge function to the Supabase project succeeded, and if it failed, look at the logs and tell me the first error with a timestamp?

Tokenese (≈20 tokens):

```
@1=supabase edge fn deploy
get? @1 status
if fail -> get logs first-error +time
```

Target compression: 2.5-4x on operational exchanges, with lower ambiguity than the English original (which model? which project? "first error" by what ordering? — slots force these to be bound or explicitly defaulted).

## Open questions (v0.2 agenda)

1. Codex 5.5 live A/B: same task suite in English vs Tokenese; measure tokens, task success, misparse-retry rate. This validates or kills the design.
2. Vocabulary registry: shared file (this repo) listing registered ops and slot keys, so both parties train against the same controlled vocabulary. Format: one line per entry, `word :: sense`.
3. Whether instruction-following degrades when prompts are dense (known risk: models reason worse over compressed context — needs measurement, not assumption).
4. Multi-statement transactions and quoting (how to embed code blocks and verbatim strings without tokenizer surprises): proposal — fenced blocks pass through untouched, Tokenese applies only outside fences.
5. Anthropic-side audit of `✅` and broader frequent-word sweep (top 2000 English words, both tokenizers) to enlarge the certified-1-token vocabulary.
6. Third tokenizer column (Gemini, Qwen) before claiming cross-vendor generality.

## Naming and prior art

- Canonical home: https://tokenese.org/ (registered 2026-06-12). tokenese.dev reserved for tooling surfaces. tokenese.com is a third-party squat (registered 2026-03-20, parked) — not affiliated.
- Name "Tokenese": no prior language/protocol/paper/product found (searched 2026-06-12, Perplexity + web).
- Prior art reviewed: Agora protocol (arxiv 2410.11905, negotiated routines, 98% token cut on repeat exchanges) — Tokenese borrows in-band binding; Gibberlink (capability handshake then dense mode); LLMLingua-2 (payload compression, complementary); DroidSpeak/CIPHER/Coconut (latent-space, rejected: cross-vendor and security constraints).
- Distinct from pidgin: a pidgin trades precision for ease of acquisition. Tokenese trades acquisition cost (it must be specified, not picked up) for precision and density.
