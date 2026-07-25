# POST-MORTEM: Tokenese, and the designed-interlingua idea

Date: 2026-07-25
Status: final. This repository is archived. The spec, tooling, and audit
scripts are preserved intact below this document as evidence, not as product.
Verdict scope: not just this repo. This document is a measured post-mortem of
the idea this repo espoused: that a designed, compressed, machine-native
language for LLM-to-LLM communication can beat natural language on cost and
precision at once.

## Verdict

The idea loses. Not narrowly, and not because this implementation was sloppy.
It loses structurally, for reasons that apply to every project in the
70-year lineage it belongs to, and this repository is unusual only in that it
built the instruments to measure its own failure and then did so.

The one-sentence version: the winners bolted precision onto the outside of
natural language (schemas and constrained decoding) and pushed density below
the text (caching, pricing, latent exchange), leaving the language layer
human-native. Every project that instead created a new surface form died.

## What Tokenese claimed

From INTENT.md as originally written:

> Tokenese is an open specification for a token-native interlingua: a language
> LLMs use to communicate with each other that is denser and more precise than
> any human language. [...] The bet is that accuracy and compression are not a
> tradeoff here; natural language is so far from the efficient frontier that a
> designed language can win on both axes at once.

The headline example claimed a >2x token saving. The spec targeted 2.5-4x
compression. Every lexicon element was to be admitted only by reproducible
cross-tokenizer audit, which turned out to be the project's most important
design decision, because the audit is what killed the claim.

## What measurement showed

On 2026-06-18, pre-publish validation of an announcement post re-counted the
flagship example on the certified tokenizers. The claim reversed.

| Tokenizer | English | Tokenese | Result |
|---|---|---|---|
| o200k_base | 36 | 47 | Tokenese 1.31x LARGER |
| cl100k_base | 37 | 48 | Tokenese 1.30x LARGER |

The claimed figures (English ~55, Tokenese ~22) had been eyeballed, never
measured, violating the repo's own invariant 6 ("measured, not asserted").
Controlled re-examination of the premise followed. Same semantic task, encoded
multiple ways:

| Form | o200k | cl100k |
|---|---|---|
| Verbose polite English (the old baseline) | 36 | 37 |
| Terse English | 18 | 19 |
| Tokenese v0.3 as specified (sigils, dotted handles) | 47 | 48 |
| Word-based Tokenese | 17 | 18 |
| Keyword-minimal English | 16 | 17 |

Findings, in order of importance:

1. Most of the apparent savings was terseness, not language design. Verbose
   36 to terse 18 is a 2x win with zero spec, zero learning cost, and full
   readability. The fair baseline for any designed language is terse English,
   and against that baseline the designed forms are a wash.
2. The designed syntax actively hurt. Dotted handles and sigil clusters are
   out-of-distribution for BPE tokenizers and shatter: `@svc.logs.first-error`
   is 5 tokens, `!@svc.ok?` is 5, `edge-fn` is 3. The v0.3 grammar used
   exactly the constructs that tokenize worst.
3. A narrow honest win survived: roughly 20-25% over terse English on
   structured/conditional payloads built from operators that audit to a single
   token (`->`, `>>>`, `::`). Real, modest, fragile, and nowhere near the
   2.5-4x target.
4. BPE tokenizers are trained on natural text, so English is already near one
   token per word, including function words. There is no large efficiency
   frontier gap for a designed language to capture. The founding premise is
   false for short messages, which is what inter-agent messages are.

The spec pivoted honestly (the "precision-pivot": lead with precision,
auditability, portability; retain compression as a long-term goal). The live
cross-family A/B experiment (ROADMAP N2, the self-declared kill-criterion) was
designed but never run. It does not need to run. The demand evidence
(five unique visitors in the final fortnight, zero external adopters, zero
inbound interest across six weeks public) answers the question the experiment
was built to ask at a level below its resolution.

## What was built

Recorded so the testament shows the failure was not rigor:

- A spec with seven design invariants, wire grammar v0.3, conformance claim
  classes, and admission criteria for changes.
- A seven-column tokenizer audit (OpenAI o200k_base, Anthropic count-tokens,
  Gemini, Qwen2.5, DeepSeek-V3, Llama 3, Gemma 4 E4B native), reproducible via
  the `audit_*.py` scripts, CI-gated against silent alphabet expansion.
- A deterministic Tokenese-to-English translator, validator, per-pair scorer
  (TKAB), MCP server, and 163 passing tests. Scoring only, never generation,
  by scope lock.
- GuideCheck Level 4 trust anchoring with a DNS TXT hash anchor and daily
  drift CI (retired at archive).
- A static receiver-comprehension floor (min 0.85 against a 0.75 threshold)
  and an N2 static package report.

The audit methodology is the salvage. It is, as far as we know, the only
reproducible cross-vendor worst-case token-cost audit of a designed lexicon,
and it is exactly the instrument that falsified the project that built it.

## The lineage: 70 years of the same idea

Tokenese is not a new idea. It is the LLM-era instance of a recurring one.

| Era | Project | Intent | Method | Fate |
|---|---|---|---|---|
| 1950s-90s | Interlingua MT (KBMT, Eurotra) | N squared language pairs become N via a universal meaning representation | Hand-crafted language-neutral semantics | Lost to statistical, then neural MT, which learned from the substrate instead of designing above it |
| 1955- | Loglan / Lojban | An unambiguous logical language | Predicate-logic grammar, one parse per utterance | Never adopted for MT or agents; hobbyist community |
| early 1990s | KQML | Knowledge-level agent messaging | Speech-act performatives (`ask-if`, `tell`), layered envelope | Performative semantics too weak; implementations could not interoperate |
| ~2000 | FIPA-ACL | Fix KQML with formal semantics | Logic-grounded pre/postconditions over agent beliefs and intentions | Semantic over-engineering, heavyweight tooling; the web and REST won; agent research went dormant |
| 2001- | Semantic Web (RDF, OWL, SPARQL) | Machine-interpretable meaning layer for the web | Triples, description-logic ontologies, reasoners | High modeling cost, poor ergonomics; survives in niche knowledge graphs; JSON+REST won the general case |
| 1990s- | Controlled natural languages (Attempto, ASD-STE100) | Restrict English until it parses deterministically | Grammar subset plus controlled vocabulary | Survives only where regulation mandates it; nobody volunteers into it |
| 2023- | LLMLingua | Compress prompts, keep performance | Statistical token pruning of natural language | Real traction: up to 20x on long prompts, peer-reviewed. Note what it is not: not a language |
| 2025 | SynthLang | Glyph/kanji symbolic prompt language | Symbol substitution for verbose instructions | Self-reported 40-70% claims, no independent validation, requires decoding rules in-prompt; hobby traction |
| 2025 | TOON and compact-JSON notations | Token-cheaper structured payloads | Slims JSON syntax overhead | Niche traction. Compresses JSON, not language |
| 2025 | Gibberlink | Agent-to-agent audio handshake | GGWave encoding | Viral demo, zero infrastructure adoption |
| 2024- | Agora protocol | Negotiated efficient routines between agents | Protocol negotiation with NL fallback | Conceptual; no ecosystem |
| 2024- | DroidSpeak, CIPHER, neuralese / latent communication | Skip text entirely | KV-cache exchange, embedding exchange, emergent codes | Where efficiency research actually went: 2-24x latency wins reported, TTFT speedups up to two orders of magnitude. Architecture-coupled, not cross-vendor |
| 2026 | Tokenese (this repo) | Token-native audited interlingua, denser and more precise at once | Empirical tokenizer-audit admission gate, fixed field grammar, repair channel | Premise measured false by its own instruments; archived |

## The common intent

Four bets recur across the entire lineage, near-verbatim:

1. Ambiguity is waste, and formal semantics will fix it. FIPA's belief-logic
   preconditions, Lojban's single parse, Attempto's controlled grammar,
   Tokenese invariant 4 ("one statement, one reading").
2. The machine channel should not pay human-language overhead. Interlingua MT,
   SynthLang, neuralese, Tokenese's founding metaphor of models "watching film
   in black and white."
3. A neutral interlingua beats N squared pairwise mappings. Interlingua MT,
   KIF, Tokenese's cross-vendor portability invariant.
4. Machine communication should be auditable and verifiable. FIPA formal
   semantics, OWL reasoners, Tokenese invariant 7 (human-auditability).

All four intents are legitimate. That is the trap. Each intent is real, and
each has now been satisfied by a mechanism that is not a designed language.

## The common methodology

The lineage also shares its methods:

- An operator or performative vocabulary (KQML performatives, Tokenese sigils,
  SynthLang glyphs).
- A grammar restricted until parsing is deterministic.
- A controlled vocabulary, one sense per word.
- An admission gate for new elements (FIPA standardization, Tokenese's
  tokenizer audit; the audit being empirical was this repo's novelty).
- A teaching payload: because none of these languages exist in training data,
  every participant must be taught in-context or in-spec, per session or per
  developer, forever.

## The failure law

Stated once, plainly:

Every project that created a new surface form died. Every survivor compressed
within the incumbent substrate.

- LLMLingua prunes English. Survived.
- TOON slims JSON. Survived, niche.
- Constrained decoding restricts English and JSON emission. Won outright.
- KV-cache and latent exchange skip text where both ends share an
  architecture. Thriving in research.
- KQML, FIPA-ACL, Lojban, the Semantic Web's reasoning layer, SynthLang,
  Gibberlink, Tokenese introduced new surfaces. All dead or dying.

## Why JSON plus natural language won

Four mechanisms, each independently sufficient:

1. Substrate gravity. Tokenizers are trained on English, code, and JSON, so
   the incumbent is near-optimal in the very currency (tokens) that
   challengers compete on. A designed language fights the training prior, the
   tokenizer economics, and the tooling ecosystem simultaneously. This repo
   measured the effect precisely: the designed form was 1.3x larger than the
   prose it replaced.
2. Precision was solved orthogonally. The winning stack separates carrier
   from contract: the carrier stays familiar text, and precision comes from
   JSON Schema plus constrained decoding, which makes invalid output
   unrepresentable at the sampler. That is better determinism than any grammar
   spec can offer, enforced at generation time rather than checked after, at
   zero acquisition cost. MCP (JSON-RPC) and A2A (typed JSON schemas) are
   explicit about this design choice, and they are the only protocols in this
   space with adoption: on the order of 97M monthly SDK downloads and
   production use in a large majority of enterprise agent teams by mid-2026.
3. Compression was solved orthogonally. Prompt caching, falling token prices,
   growing context windows, statistical pruning (LLMLingua), and latent
   exchange turned compression into an infrastructure property rather than a
   language property. The ~20-25% residual win Tokenese measured on narrow
   payload classes is smaller than a typical quarter of token price decline.
4. Asymmetric acquisition cost. The incumbent costs every participant nothing.
   A designed language charges a teaching payload per session, per model,
   forever, against per-message savings that round to noise. FIPA paid this
   cost in developer learning; Tokenese pays it in prompt tokens. Same ledger,
   same sign.

## What survives

- The audit methodology. A reproducible, CI-gated, worst-case cross-tokenizer
  cost audit is useful to anyone designing identifiers, DSL syntax, or
  structured output formats that LLMs will emit. The scripts remain in this
  repo and remain runnable.
- The negative result itself. Published measured falsifications are rare in
  this space; most projects in the lineage table simply stopped updating.
- The discipline. "Measured, not asserted" (invariant 6) is the reason this
  post-mortem exists instead of a slowly rotting landing page.
- The precision intents. They were legitimate, and they are served today by
  JSON Schema, constrained decoding, and typed protocol contracts.

## Revival conditions

Pre-registered and falsifiable, so this document can be proven wrong rather
than argued with. The designed-interlingua idea becomes worth revisiting only
if at least one of these becomes true:

1. A major vendor ships a tokenizer deliberately trained on a designed
   agent-language corpus, making the designed surface cheap by construction
   and collapsing the substrate-gravity argument.
2. A vendor-neutral latent-exchange standard emerges, collapsing the
   cross-vendor rationale that forced token-space text in the first place
   (invariant 1), and a plain-text interlingua becomes the fallback layer of
   that standard.
3. Someone demonstrates, with reproducible cross-tokenizer counts and a live
   misparse-retry accounting, a designed language beating terse English by
   more than 2x on a general task distribution, not a curated payload class.
4. Inference pricing inverts its trend for multiple consecutive years, making
   per-message token savings economically decisive again.

Absent those, the answer to "should we design a language for the machines?"
is: no. Be terse, emit JSON against a schema, cache your prompts, and let the
sampler enforce your grammar.

## Timeline

- 2026-06-12: repo provisioned. Spec v0.1.0, dual-tokenizer audit.
- 2026-06-16: repo public, tokenese.org live, landing page ships.
- 2026-06-17: seven-column audit complete, GuideCheck Level 4 anchoring.
- 2026-06-18: pre-publish validation falsifies the flagship example. The
  announcement post is pulled. Premise re-examination measured and recorded.
- 2026-06-22: precision-pivot ratified into spec and INTENT.
- 2026-06-23: v0.3.9 released. Phase A closed. Phase B (live A/B) opened.
- 2026-06-25: Phase B stalls at fixture authorship. No further substantive
  work occurs.
- 2026-07-25: viability teardown run. Baseline: 0 stars, 0 forks, 5 unique
  visitors in 14 days, 0 external adopters, package never published. Archive
  verdict taken. This document written. Repo archived.

## Reproduce the falsification

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./.venv/bin/python - <<'PY'
import tiktoken
o = tiktoken.get_encoding("o200k_base"); c = tiktoken.get_encoding("cl100k_base")
def m(s): return len(o.encode(s)), len(c.encode(s))
english = ("Could you check whether the deploy of the edge function to the "
           "Supabase project succeeded, and if it failed, look at the logs and "
           "tell me the first error with a timestamp?")
tokenese = ("^grammar:v0.3\n^declare:level=L2\n@svc := supabase/edge-fn\n"
            "@svc.deploy >>> @svc.status\n!@svc.ok? *>> get @svc.logs.first-error +ts")
terse = ("Check Supabase edge-function deploy status. If failed, return first "
         "log error with timestamp.")
print("verbose english", m(english))   # (36, 37)
print("tokenese v0.3  ", m(tokenese))  # (47, 48)
print("terse english  ", m(terse))     # (18, 19)
PY
```
The full lexicon audit remains reproducible via `audit_symbols.py` and
siblings; see README.

## Provenance

Compiled 2026-07-25 by the maintainer with agent assistance, from: the
2026-06-18 premise re-examination (measured in this repo's own venv), the
repo's spec and design documents, GitHub traffic instruments, and a survey of
the protocol landscape as of mid-2026 (MCP/A2A adoption reporting, latent
communication survey literature, and the public record of each lineage
project). Corrections that come with measurements are welcome; the repo is
archived, so file them against the maintainer's active projects or via the
contact on tokenese.org.
