# INTENT

## What this standard is

Tokenese is an open specification for a token-native interlingua: a language LLMs use to communicate with each other that is denser and more precise than any human language, while remaining plain text that crosses any wire and any vendor boundary. Every element of its lexicon is admitted by empirical audit: one token, worst case, in every tokenizer in use.

## Why it exists

LLMs conforming to human language is like watching film in black and white. Human languages were shaped by human constraints: serial speech, limited working memory, social hedging, redundancy against noisy air. Models inherit all of that overhead and none of its benefits. Tokenese is an attempt to bring color to machine-to-machine communication: exchanges that feel richer and more informative to the participants while compressing into a smaller, token-native format. The bet is that accuracy and compression are not a tradeoff here; natural language is so far from the efficient frontier that a designed language can win on both axes at once.

## Design invariants

1. Token-space only. No embeddings, no KV-cache sharing, no latent-channel exchange. Everything crosses the wire as text each party tokenizes independently. Security and cross-vendor portability both require this.
2. Tokenizer-audited lexicon. Every lexicon element carries an empirically audited worst-case cost (bare and space-prefixed) in every tokenizer in use; no element ships unaudited. The closed function vocabulary (sigils, reserved operators, evidentials) must be 1 token worst case on all sides. Content vocabulary is admitted on tokens-per-semantic-unit advantage over the natural-language alternative: a 2-token CJK ideograph that replaces a 3-token English phrase wins admission. Any UTF-8 character is candidate space. Claims are reproducible via the audit scripts in this repo. (Amended 2026-06-12 per Sam: CJK welcome; the audit prices it, density justifies it.)
3. Not a pidgin. A pidgin trades precision for ease of acquisition. Tokenese trades acquisition cost (it must be specified and learned, not picked up) for precision and density. Any change that dulls precision to gain compression is rejected.
4. Accuracy is a feature. Fixed field grammar, controlled vocabulary (one sense per word), and typed literals must make Tokenese misparse less than the equivalent English, not more.
5. Self-repairing. The `??` repair signal and plain-English escape hatch are mandatory in every conforming implementation. A dense language without a repair channel is a liability.
6. Measured, not asserted. The kill-criterion is misparse-retry rate in live A/B against natural language. If retries eat the savings, the design has failed and the spec says so.
7. Human-auditable. A competent human with the one-page audit card (sigil key, anchor scales, allusion ledger) must be able to follow any conforming transcript. Constructs that produce opacity a ledger cannot cure are rejected regardless of token savings. Corpus anchors are admissible only when ledger-registered. (Hard invariant per Sam, 2026-06-12.)

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
- `RELEASE_CHECKLIST.md` still deferred; now applicable (repo is hosted + agent-facing as of 2026-06-16) and queued as a follow-up via security-hardening-release.
- Hosted + agent-facing tier rows adopted 2026-06-16: `docs/index.html` canonical landing page, `favicon.svg`, `sitemap.xml`, `robots.txt` (per-bot allows), `llms.txt`, `site.webmanifest`, `404.html`, `CNAME`. Served via GitHub Pages from `main` `/docs`. `imgs/og.png` still pending (omitted; backfill via promo-orchestrator / blog-image-prompt). `llms-full.txt` omitted (llms.txt is comprehensive standalone for a single-page spec).
- Ownership: drafted under PAICE.work PBC following the open-spec sibling pattern (graceful-boundaries, obligation-first). Admitted to `~/Git/portfolio.yaml` as an open-spec component 2026-06-16 (private repo, pre-release; hosted-tier rows still deferred until tokenese.org ships).

## Changelog

- 2026-06-17 (release v0.3.2): X3 partial, report-only frameset registry. Added typed slot signatures for common ops (`deploy`, `get`, `run`, `set`, `fix`), packaged `validate_framesets`, MCP surface, and TKAB `frameset_validation` telemetry. Patch release; no normative grammar change and no checker outcome changes.
- 2026-06-17 (release v0.3.1): GuideCheck adoption. Added `assistant-guide.txt` (bounded "install Tokenese and reproduce the lexicon audit" task) as a trust-anchored byte-identical pair (repo root + `docs/.well-known/`) with a Level 4 sidecar manifest. Synced the landing page and `llms.txt` to grammar v0.3. Patch release; no normative grammar change. Level 4 cross-channel hash anchor (DNS TXT at `_assistant-guide.tokenese.org`) pending one registrar record; Level 3 structure complete until it propagates.
- 2026-06-16 (later): canonical-spec-page. Built tokenese.org landing page (`docs/`), repo flipped to public so spec/GitHub links resolve, GitHub Pages enabled from `main` `/docs`. WCAG 2.1 AA clean (0 axe violations). DNS at registrar still pending. Hosted + agent-facing tier rows adopted.
- 2026-06-16: Repo-standards walk + repo-polish. Private GitHub repo created and pushed, v0.1.0 tagged + released, `.github/` templates + GH metadata added, admitted to `portfolio.yaml` as an open-spec component. HANDOFF docs moved to gitignored `working/`.
- 2026-06-12 (later): Invariant 2 amended per Sam: 1-token rule narrowed to the closed function vocabulary; content vocabulary admitted on tokens-per-semantic-unit advantage, reopening CJK and other multi-token UTF-8 candidates. Invariant 7 (human-auditability, hard) added per Sam. Evidential surfaces audited and selected: ev:obs / ev:heard / ev:mem / ev:guess, default = inferred.
- 2026-06-12: INTENT.md created at repo provisioning. Spec v0.1.0 draft, dual-tokenizer audit complete (o200k_base + Anthropic count-tokens), tokenese.org registered as canonical home.
