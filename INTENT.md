# INTENT

## What this standard is

Tokenese is an open specification for a token-native interlingua: a language LLMs use to communicate with each other that is denser and more precise than any human language, while remaining plain text that crosses any wire and any vendor boundary. Every element of its lexicon is admitted by empirical audit: one token, worst case, in every tokenizer in use.

## Why it exists

LLMs conforming to human language is like watching film in black and white. Human languages were shaped by human constraints: serial speech, limited working memory, social hedging, redundancy against noisy air. Models inherit all of that overhead and none of its benefits. Tokenese is an attempt to bring color to machine-to-machine communication: exchanges that feel richer and more informative to the participants while compressing into a smaller, token-native format. The bet is that accuracy and compression are not a tradeoff here; natural language is so far from the efficient frontier that a designed language can win on both axes at once.

## Design invariants

1. Token-space only. No embeddings, no KV-cache sharing, no latent-channel exchange. Everything crosses the wire as text each party tokenizes independently. Security and cross-vendor portability both require this.
2. Tokenizer-audited lexicon. A symbol or word enters the core vocabulary only if it costs 1 token, worst case (bare and space-prefixed), in every tokenizer in use. Claims are reproducible via the audit scripts in this repo.
3. Not a pidgin. A pidgin trades precision for ease of acquisition. Tokenese trades acquisition cost (it must be specified and learned, not picked up) for precision and density. Any change that dulls precision to gain compression is rejected.
4. Accuracy is a feature. Fixed field grammar, controlled vocabulary (one sense per word), and typed literals must make Tokenese misparse less than the equivalent English, not more.
5. Self-repairing. The `??` repair signal and plain-English escape hatch are mandatory in every conforming implementation. A dense language without a repair channel is a liability.
6. Measured, not asserted. The kill-criterion is misparse-retry rate in live A/B against natural language. If retries eat the savings, the design has failed and the spec says so.

## Scope boundaries

In scope: wire grammar, reserved sigils, symbol-table protocol, handshake, repair protocol, the audited admissible alphabet, and the audit method itself.
Out of scope: payload compression of natural-language documents (LLMLingua territory), latent or embedding exchange (rejected by invariant 1), human shorthand systems, tokenizer internals of any vendor, and transport (Tokenese is transport-agnostic text).

## Conformance philosophy

Testable claims, no central oracle. Two claim classes: (1) lexicon admissibility, verifiable by anyone running the audit scripts against the named tokenizers; (2) grammar conformance, verifiable by parsing a transcript against the wire grammar. A conformance checker should run anywhere, offline, against a transcript. See CONFORMANCE.md.

## Admission criteria for changes

1. Any new lexicon element ships with audit evidence: worst-case 1 token in every tokenizer the spec currently certifies.
2. Any grammar change must not reduce parse determinism (one statement, one reading).
3. Any change claiming a compression gain must show token counts before and after on the spec's example corpus.
4. Any change that increases misparse-retry rate in A/B testing is reverted, whatever it saves.
5. New tokenizer columns (Gemini, Qwen, others) are additive; they may shrink the admissible alphabet, never silently expand it.

## Relationships to other PAICE standards

- Turnfile: candidate envelope for multi-agent sessions speaking Tokenese; non-binding.
- Graceful Boundaries: the `plain` escape and `??` repair are refusal-adjacent surfaces; GB formatting may apply where a party declines dense mode; non-binding.
- HardGuard25: token-budget metadata is a natural Tokenese payload; non-binding.
- Prior art outside the portfolio: Agora protocol (negotiated routines), Gibberlink (capability handshake), LLMLingua (complementary payload compression). DroidSpeak and CIPHER reviewed and rejected per invariant 1.

## Exceptions to Repo Standards

- `relationships.yaml` and `ontology.json` are minimal v0 stubs pending first public release.
- `RELEASE_CHECKLIST.md` deferred until the repo gains a hosted or agent-facing surface (tokenese.org landing page not yet built).
- Hosted-tier rows (imgs/og.png, robots.txt, llms.txt, sitemap, CNAME) not yet applicable; apply via canonical-spec-page when tokenese.org goes live.
- Ownership: drafted under PAICE.work PBC following the open-spec sibling pattern (graceful-boundaries, obligation-first). Admission to `~/Git/portfolio.yaml` is pending Sam's decision and is not implied by this file.

## Changelog

- 2026-06-12: INTENT.md created at repo provisioning. Spec v0.1.0 draft, dual-tokenizer audit complete (o200k_base + Anthropic count-tokens), tokenese.org registered as canonical home.
