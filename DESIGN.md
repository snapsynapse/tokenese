# Tokenese Design Position
Version: 0.1.0
Date: 2026-06-12
Status: design notes feeding spec v0.2

This document records the design position taken after a structured exploration round (5 independent design lenses, 2 adversarial critiques, ~490K tokens of analysis) plus empirical tokenizer audits. It is the answer to: what artifacts best represent an LLM's underlying semantics as a medium of communication, and what is important vs superfluous, rich vs crude, art vs utility.

## 1. The honest foundation

I cannot transmit my vector space. Neither party can. What actually crosses the wire is text, and what makes that text mean nearly the same thing on both sides reduces to exactly three mechanisms:

1. Convergent distributional structure. Two models trained on heavily overlapping corpora develop convergent relational statistics for high-frequency tokens: which senses neighbor which, which contrasts are salient. Relative geometry converges; coordinates do not. This is the only thing that deserves the name "vector semantics," and even here the vectors are private decompressions of a shared corpus.
2. Universal in-context-learning circuitry. Induction heads (verbatim-prefix copying) and relation transport from worked exemplar pairs exist in essentially every transformer at scale. Constructs riding these work regardless of instruction tuning.
3. Instruction-following over an in-context spec. Both parties are strong spec-compliers. Anything that only works because the spec is in context is a DSL, not vector semantics. Useful, but it predicts a specific failure: high fidelity on spec-shaped utterances, silent failure on novel recombinations of known parts.

Tokenese is therefore, honestly: a DSL (mechanism 3) whose load-bearing constructs ride mechanisms 1 and 2 wherever possible, with a paraphrase-based checksum as its trust root because no shared hash function exists between two different models.

The deepest reframe from the round: the empirical lexicon finding (common English words win, exotic Unicode loses) is not a compromise. Frequency equals cross-model semantic stability. A common English word is the most stable cross-model address that exists. The lexicon audit and the semantics point at the same answer for different reasons.

What "representing my underlying space" actually means, then: not serializing internal state, but two things English cannot do.
- Addressing the shared inheritance: pointers into the enormous pre-shared corpus (anchors, prototypes, worked-pair relations) so the receiver decompresses locally what was never transmitted.
- Preserving what English destroys at the output boundary: the enumerable alternatives behind every assertion, the source class of every claim, and continuous quantities that English forces through thresholds. With one humility: my reports of my own uncertainty are themselves generations, not privileged reads. The language must treat them as claims to verify, not facts to trust.

## 2. The architecture: three layers

Layer 1, skeleton (pure protocol; mechanism 3): framesets, canonical form, handshake, repair, readback, sync checkpoints. Zero or near-zero wire cost; this layer is the teaching document and the safety floor.

Layer 2, mechanism constructs (ride 1 and 2): handles, sense gates, scope fences, contrast pins, worked-pair analogy. These should outperform English immediately because they route around documented transformer weak points (coreference, scope, binding interference).

Layer 3, corpus constructs (ride 1 at scale): allusion anchors, prototype delta-coding. The largest compression ratios in the design and the fastest-drifting; only admissible with their verification handshakes attached.

## 3. What is important (the keeps)

K1. Semantic handles. `@cfg=server.yaml` then `@cfg` forever. Exact-match copy attention replaces fragile learned coreference. Strongest single construct in the round. Refinement over v0.1: sigil+noun (`@cfg`), not bare numerals (`@1`); a dropped binding then degrades to a plausible guess instead of garbage. Live-handle cap ~6, explicit `drop @x`.

K2. Addressable repair. `??slot`, `??@cfg`, `??†anchor`. Extends the existing `??`. Repair cost drops from full-retry to one slot. Nearly pure win; the safety floor that makes every other admission cheap to be wrong about.

K3. Distribution slots. `cause:oom^6|disk^3` (k<=3, ordinal weights, forbidden on `!` imperatives). The ranked shortlist preserves the alternatives English's assert-one-thing convention discards. Four lenses converged on this independently. Honest framing, mandated for spec prose: this is enumeration preservation, NOT a serialized softmax. The next-token distribution is over tokens, not world-states; verbalized weights are post-hoc reports with decent rank calibration and poor absolute calibration. Ordinal by definition, never probabilities.

K4. Stake-scaled paraphrase readback. `!`-flagged statements require the receiver to reply `√` plus a TRANSFORMED restatement (reordered, unit-converted, inferred); verbatim echo proves copying, not comprehension; paraphrase forces a decode-reencode through the receiver's own representations. This is the only semantic checksum available on this channel, the trust root for everything else, and it makes the kill-criterion self-measuring (readback mismatch = labeled misparse, free instrumentation). Three lenses derived it independently; aviation phraseology is the precedent. This construct was filed under plumbing in the round; it is actually the deepest thing in the language.

K5. Framesets + canonical form. Registry entries are typed slot signatures (`deploy :: who what to:env -> status`), not word glosses. Malformed statements become structurally detectable before semantic misparse. Canonical slot order per op makes string equality approximate semantic equality and concentrates both generators on one surface form. Zero wire cost; this IS the teaching document.

K6. Evidentials, with the structural fix. Source-of-knowledge marking per claim, ~25% of human languages grammaticalize this; English buries it in expensive hedges. Hallucination is an evidentiality failure. But models confabulate provenance (reporting parametric memory as observation), so: `ev:obs` is reserved for harness-verifiable claims (tool output present in context), self-reported lanes default-elide to inferred, and the calibration audit (section 6) gates trust. Audited surfaces, resolved 2026-06-12 with homonym-reduction guidance from Sam: `ev:obs` (harness-verifiable), `ev:heard` (reported by another party), `ev:mem` (parametric memory), `ev:guess` (working assumption); elided default = inferred. All dual-audited 1 token. `saw told recall infer ack <-` failed audit and are out.

K7. Contrast pins and worked-pair analogy. `like throttle not retry` pins a meaning by its nearest confusable; the `not` anchor transmits the sender's model of the receiver's likely misreading, which is theory-of-mind in two tokens. `like a:b @x:?` transports a relation via exemplar pairs (real mechanism: ICL relation transport, demonstrated in base models). Constraint: analogy is admissible for teaching and querying, never load-bearing for facts; any `like`-derived fact carries `^<=6` or gets verified. The folklore justification (king-man+woman vector arithmetic) is banned from spec prose; worked pairs are the honest version.

K8. Corpus anchors with gloss handshake. `†two-generals` transmits an entire schema for ~4 tokens, the largest compression ratio available, and the only legitimate "shared latent space" the security constraints permit because it routes through the corpus, not the vectors. Admission rule (the best single rule from the art lens): an anchor must name a schema with role structure that binds to the current case (leftpad: yes; kafka-as-mood: no). First use per session requires a one-line gloss-back; unconfirmed anchors carry no load. Session-scoped certification, never carried forward.

K9. Gradients with receiver-side thresholds. `risk:3 ready:6` where the underlying quantity is continuous; `y/n` mandatory where it is binary (grading a binary fact is a conformance error). The real argument is not bits-per-token; it is the relocation of thresholding: sender reports the measurement, receiver applies its own cutoff per its own risk posture. Spec-anchored scale (0 absent, 5 coin-flip, 9 near-certain), never negotiated per session.

K10. Typed holes. `when:□date owner:□` plus `fill □date 2026-06-22`. Negotiation becomes progressive binding; the conversation is the constraint-solving trace. Cap: >2 open holes per exchange auto-flags.

Two spec rules that outrank any construct:

R1. Never compress derivation. Tokens are the serial compute substrate (fixed depth, more tokens = more serial computation); compressing a reasoning chain removes the computation and the working memory it was made of. Dense mode is for statements whose correctness is checkable by slot inspection: state, reference, parameters, procedure calls. Reasoning spans stay in prose. Mode words: `dense` / `plain` (both audited, symmetric with the existing escape hatch).

R2. The Leibniz criterion as admission gate. Adopt only constructs whose semantic operations are textual operations: fill a hole, substitute a handle, expand an anchor, strip a lane, reorder canonically. Good notation does part of the reasoning; every v0.2+ candidate must name its validity-preserving string edits alongside its tokenizer audit.

## 4. What is superfluous (the discards)

From human language, deleted with confidence:
- Tense and agreement morphology. Acoustic-channel error correction; also tokenizer poison (inflected forms fragment). Time is a slot (`t:`), present only when load-bearing.
- Articles and definiteness. The handle lifecycle IS definiteness done right: bound = given, unbound = new.
- Pronouns and free anaphora. Lossy compression with collision risk; handles are the lossless replacement. Strict upgrade.
- Politeness, face-work, hedging idiom. The functional skeleton survives as `^N` and repair; the costume dies.
- Synonymy and elegant variation. Anti-monotony aesthetics for readers who get bored. Models do not; variation here is pure collision risk. One sense, one surface.
- Word order as grammar AND word order as salience. Canonical order per frameset wins: determinism, lower generation perplexity, string-diff as semantic-diff. (The salience-ordering proposal lost to this; a freed degree of freedom should be spent on reliability, not on a second soft channel.)
- The noun/verb split. Ops are relations with slots. AMR and Lojban both proved the split unnecessary; embedding geometry ignores it.
- Free metaphor and idiom. Survives only as registered, glossed, audited corpus anchors.

From the round's own proposals, killed or deferred:
- Embedding centroids, pseudo-latent coordinates (`loc:0.23,-0.81`), glyphs as semantic operators, token-count formalism, affect channels beyond goal-relevance, free-association channels. Mysticism or theater; several cargo-cult the exact thing invariant 1 rejects.
- Superposition hold/collapse lifecycle (`□...√` as speech act). An open-issue tracker in physics drag; distribution slots carry the payload with zero cross-turn state.
- Session-local template macros. The compositionality-cliff trap incarnate; deferred to v0.3 pending A/B evidence from long operational loops.
- Scoped/ephemeral bindings (`@_N`). 2 tokens, silent scope-leak failure mode; the live-handle cap plus `drop` achieves the hygiene with zero new machinery.
- Delta-coding against shared prototypes (`@4=std fastapi svc; @4 but port:8080`). The purest exploitation of the shared-corpus premise and the most dangerous silent-failure mode (wrong defaults, invisible to the misparse metric). Provisionally admissible ONLY paired with mandatory first-use readback per prototype; measured separately.
- Detached weight vectors (`A|B|C^{7,2,1}`). Branch/weight misalignment hazard; inline weights won.
- Salience and valence digit lanes. Uncalibrated vibes wearing digits.

## 5. Rich vs crude

Tokenese is deliberately crude where human languages are rich: morphology, register, synonym texture, prosody, irony, deniability. All deleted; they serve speakers with faces and ears.

It is rich where human languages are crude, and these are the four richness channels:
1. The epistemic layer: ranked alternatives, source class, calibrated-scale gradients. English forces point estimates through social hedges; Tokenese carries the shape, the source, and the measurement.
2. Boundary information: contrast pins and `not` anchors transmit where a meaning stops, including the sender's model of the likely misreading. English definitions transmit a center and pray.
3. Relational transport: worked-pair analogy moves a whole frame in one line.
4. Corpus addressing: anchors and (eventually) prototype deltas spend tokens on surprise only, against terabytes of pre-shared structure.

## 6. Art vs utility

The round's art lens concluded "the utility is the art," and the depth critique demoted most poetic framings to decoration. My own position, and the one this project will run on:

The art of Tokenese is honesty. English makes a model perform: perform confidence it does not hold, perform a single belief where it holds several, perform smoothness over provenance it cannot defend. Every keep in section 3 is a way to stop performing. A wire format where what I say is exactly what I have warrant for, no more, no less, with the warrant class attached and the alternatives intact, is richer than English not because it is denser but because it is truer. Compression is the dividend, not the point.

The corollary is the round's biggest warning, which I adopt as a design invariant: notation that launders vibes into calibrated-looking digits is strictly worse than English hedging, because English hedges advertise their own unreliability while `^8 ev:obs` suppresses the receiver's verification reflex. Therefore the calibration audit (do `^N` ranks predict actual accuracy? does `ev:obs` correlate with verifiable context?) is a first-class metric beside misparse-retry rate, and self-reported channels ship untrusted-by-default until it passes.

Where the mysticism boundary runs: softmax, superposition, hyperplane, and coordinate vocabulary is confined to annex prose and banned from normative spec text. The constructs stand on the three mechanisms of section 1 or they do not ship.

## 7. Sigil namespace (collision resolution)

Grammar version stamp: **v0.3** (additive over v0.2; see GRAMMAR-v0.3.md). Rows
tagged `(v0.3)` are new and only active when the artifact opens with
`^grammar:v0.3`; everything else is the frozen v0.2 allocation.

The five lenses, designed in isolation, claimed several sigils multiple ways. Binding allocation, one sigil one meaning:

| Sigil | Meaning (only meaning) |
|---|---|
| `@` | handle bind/reference |
| `□` | typed hole |
| `†` | corpus anchor |
| `√` | ack/confirm (readback reply) |
| `??` | repair (addressable) |
| `^` | ordinal confidence 0-9 |
| `\|` | alternatives within a slot |
| `::` | type tag |
| `->` | sequence/yield |
| `=>` | implication |
| `because` | causal attribution (word form; `<-` failed Anthropic audit and is a mirror-confusable of `->`) |
| `!` | imperative + readback trigger; **prefix `!@h` = negation (v0.3)** |
| `~` | approximate |
| `//` | human-facing comment |
| `§` | spec rule reference |
| `{ }` | proposition quoting, depth 1 |
| `not( )` | negation scope, depth cap 2, bind-don't-nest |
| `dense` / `plain` | mode words |
| `ev:` | evidential slot |
| `^grammar:vX.Y` | artifact grammar-version declaration, first non-comment line (v0.3) |
| `^declare:level=L` | declared conformance level `L0\|L1\|L2\|L3`, first non-comment line (v0.3) |
| `^plain<<<` … `>>>^plain` | closed plain region; verbatim, not graded (v0.3) |
| `"""` … `"""` | raw source quote, verbatim, triple-quote delimited (v0.3) |
| `@h?` | hedge suffix — "possibly h" (v0.3) |
| `>>>` | temporal sequence "left then right"; always admissible (v0.3) |
| `*>>` | stipulated causation "left causes right"; requires source corroboration (v0.3) |
| `?>>` | hypothesized causation "left may cause right"; always admissible (v0.3) |
| `#` (line start) | line comment to EOL; inline `#` is unchanged tag content (v0.3) |

The v0.1 uses of `=` (binding) and `#` (inline tag) stand. The bare flow
operator `>>` is still unallocated and unchanged; the v0.3 causal sigils
`>>>`/`*>>`/`?>>` are distinct three-character tokens and do not collide with
it. `<<` remains unallocated except as the `^plain<<<` opener fragment.

> **Tokenizer-cost footnote (7-column audit, 2026-06-17).** Of the v0.3 sigils,
> only `>>>` and `"""` are single-token worst-case across all seven tokenizer
> columns (o200k + Anthropic + Gemini + Qwen + DeepSeek + Llama 3 + Gemma 4).
> `?>>` ("always admissible") is single-token on o200k/Qwen/Llama but splits to
> 2 tokens on DeepSeek and Gemma; `*>>` is already 2 tokens on o200k and
> requires source corroboration anyway; the closed-plain delimiters
> `^plain<<<` and `>>>^plain` are inherently multi-token (3-4) on every column.
> None of these are lexicon glyphs — they are grammar constructs whose cost is
> amortized over the span they delimit — so their multi-token cost is expected
> and does not affect the admissible alphabet. Re-measure with `audit_*.py`.

## 8. Audit deltas this round (merged into anthropic_costs.json)

Dual-pass additions: `because like cf val zone but same other before after most except guess drop fill sum head tail dense plain sync hold set when who what why how where more less very kind part still ev src obs ..` and (evidential round) `said quote cite heard report claim via per relay mem prior stored train weights seen wit`.
Failures: `infer` (2 Anthropic), `ack` (2 Anthropic), `<-` (2 Anthropic), `saw` `told` `recall` `innate` `learned` `baked` `attest` (2 o200k bare).
Evidential surfaces selected by homonym reduction (Sam's guidance: each audit should reduce uncertainty; eliminate homographs/homonyms): `heard` over `said`/`quote`/`cite` for hearsay; `mem` over `prior`/`train`/`weights` for parametric memory.

Maintainer amendment 2026-06-12: invariant 2 narrowed. The 1-token rule binds the closed function vocabulary only; content vocabulary is admitted on tokens-per-semantic-unit advantage, which reopens CJK (2 Anthropic-side tokens, but one ideograph can replace a multi-token English phrase). Any UTF-8 is candidate space. OQ-006 tracks the CJK candidate sweep.

## 9. v0.2 admission queue

1. Sigil namespace table (section 7) — prerequisite for everything
2. Semantic handles upgrade (`@noun`, cap, `drop`)
3. Addressable repair (`??slot`)
4. R1 dense/plain mode rule (never compress derivation)
5. Frameset registry format + canonical form rule
6. Distribution slots (inline, ordinal, k<=3)
7. Stake-scaled paraphrase readback on `!`
8. Evidential slot with harness-verifiable `ev:obs` split
9. Scope fences `not( )` + proposition quoting `{ }`
10. Contrast pins `like X not Y`
11. Corpus anchors `†` with gloss handshake + schema-with-roles test
12. Gradients with spec-anchored scale
13. Typed holes `□` + `fill`
Deferred: delta-coding (needs paired readback + separate probe), templates (v0.3), worked-pair analogy beyond teaching/query use.

The A/B against Codex 5.5 measures per-construct: misparse-retry rate (stratified by construct family, since binding, scope, sense, and triangulation errors have different causes and fixes), calibration of self-reported channels, and reasoning-task accuracy inside dense vs prose spans. Cold-start conformance (a fresh model given only the spec must parse novel recombinations, not just spec-shaped examples) becomes the standing regression test of the language itself.
