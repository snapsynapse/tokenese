# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.9] - 2026-06-23

### Added

- Social/OpenGraph image at `docs/imgs/og.png` (1280x634), reclaimed from the
  GitHub repository social-preview upload. `docs/index.html` now declares
  `og:image` and `twitter:image` pointing at `https://tokenese.org/imgs/og.png`,
  closing the missing-preview gap surfaced during repo-polish.
- `tools/skills/compute_hashes.sh --check` and `.github/workflows/skill_hashes.yml`
  for ROADMAP X7. The check fails when `skills/tokenese/SKILL.md`,
  `audit_card.md`, or `install_guide.md` drift from the hashes pinned in
  `skills/tokenese/MANIFEST.yaml`.
- `tokenese-n2-report`: a deterministic ROADMAP N2 static package report that
  combines compression regression counts, hypothesis counts, receiver term
  coverage, TKAB fixture outcomes, and the remaining live A/B closure
  requirements.

### Changed

- Synced the precision-pivot spec-direction and open questions resolution to
  `DESIGN.md` (new section 10) and `INTENT.md` after the OQ#6 cross-model
  receiver gate was fully satisfied. The long-term compression goal is
  explicitly retained as the North-Star in `INTENT.md` alongside the precision-pivot
  trajectory.
- `ROADMAP.md`, `spec.md`, and `RELEASE_CHECKLIST.md` now reflect the shipped
  GuideCheck Level 4, skill-bundle, and tokenizer-column work. ROADMAP L7 is
  closed by documenting the source-provenance pin policy in the release gates.
- Current-status docs now report the live verification baseline: 156 translator
  tests plus 7 repo-root audit-surface tests.
- Retired the stale S1 receiver fixture form that still used abandoned
  `~=` / `!~=` semantic-neighborhood operators. S1 now uses explicit
  `near[...]`, polarity-safe `far_from[...]`, and `confidence:8/9`, bringing the
  deterministic receiver static floor above the `0.75` release threshold.

## [0.3.8] - 2026-06-18

### Changed — Gemma column promoted to native Gemma 4 (ROADMAP X5)

- Column-of-record swap: the "Gemma" admissible-alphabet column is now
  **`mlx-community/gemma-4-e4b-it-4bit`** (E4B on-device variant, the
  generator that runs in the PAICE production runtime under omlx on
  localhost:8000). The prior `unsloth/gemma-2-9b` proxy is retired.
- New `audit_gemma4.py` at repo root. `audit_gemma.py` deleted. The prior
  `gemma_costs.json` (Gemma 2 proxy snapshot from v0.3.5) is preserved at the
  v0.3.7 tag for forensic comparison; it is **not** carried forward.
- New `test_audit_gemma4.py` at repo root (mirrors `test_audit_anthropic.py`).
- `audit_check_intersection.py` `KNOWN_VENDORS` updated: `gemma` → `gemma4`.
- `spec.md` admissible-alphabet header and `DESIGN.md` 7-column footnote
  updated to name Gemma 4 instead of Gemma 2.

### Parity claim

Identity is proved via `audit_gemma4.py --verify-hash <sha256>` against the
cached `tokenizer.json` (the MLX 4-bit conversion ships an unquantized
tokenizer). The sibling Ollama GGUF `gemma4:latest` (8B Q4_K_M, manifest
digest `c6eb396dbd59`) is **not** used as a parity backend: it is a
different size variant. Ollama modelfile inspection confirms the production
renderer/parser pair is `gemma4` and the TEMPLATE is passthrough
(`{{ .Prompt }}`), so the raw-symbol audit contract (no chat wrap, no BOS,
`add_special_tokens=False`) is also what the production runtime ingests when
the build script sends prompts.

### Admissible-alphabet impact (enumerated per invariant 5)

INTENT.md invariant 5 (additive shrinkage, no silent expansion) requires every
symbol newly rejected by the column-of-record to be named with a one-line
rationale. Diff source: `data/source_provenance/gemma4_costs.json` (Gemma 4
E4B, 198 measured symbols, 163 single-token) vs. the v0.3.7-tagged
`gemma_costs.json` (Gemma 2 9B proxy, 167 single-token).

Across the 198 audited symbols, **7 symbols** that the Gemma 2 proxy column
admitted (worst=1) are rejected by the Gemma 4 column (worst=2). All seven
show the same failure mode: bare=1 but spaced=2 — the Gemma 4 SentencePiece
vocabulary lacks the leading-space (`▁`) variant for these glyphs, so any
in-sentence occurrence (preceded by a space) splits into two tokens. Under
the worst-of-{bare,spaced} contract these symbols are no longer admissible:

- `‡` (U+2021 DOUBLE DAGGER, category `geometric-misc`) — Gemma 4 vocab has
  the bare glyph but no `▁‡`; spaced=2. Rationale: low-frequency typographic
  mark, dropped by Gemma 4's curated vocabulary.
- `↔` (U+2194 LEFT RIGHT ARROW, category `arrow-math`) — bare=1, spaced=2.
  Rationale: less-common bidirectional arrow; only the unprefixed form is in
  vocab.
- `◦` (U+25E6 WHITE BULLET, category `geometric-misc`) — bare=1, spaced=2.
  Rationale: small white bullet has no leading-space variant; the more common
  `•` (U+2022) remains admissible.
- `假` (U+5047 "false / borrow", category `cjk-sample`) — bare=1, spaced=2.
  Rationale: this specific CJK ideograph lacks `▁假` in the Gemma 4 vocab
  (other CJK samples in the audit set still admit).
- `必` (U+5FC5 "must / necessarily", category `cjk-sample`) — bare=1, spaced=2.
  Rationale: same pattern — bare ideograph kept, leading-space variant
  pruned.
- `问` (U+95EE "ask / question", simplified, category `cjk-sample`) —
  bare=1, spaced=2. Rationale: same pattern; the traditional `問` may still
  admit but is not in the audit set.
- `️` (U+FE0F VARIATION SELECTOR-16, category `emoji-sample`) — bare=1,
  spaced=2. Rationale: the invisible emoji-presentation selector has no
  leading-space variant; in practice it never appears word-initial in
  natural text, but the contract is symmetric so it is recorded as dropped.

These 7 leave the admissible alphabet in v0.3.8 — invariant 5 wins, the
production-of-record IS the floor.

**Three symbols are newly single-token under Gemma 4** that the Gemma 2
proxy rejected: `∀` (U+2200), `∑` (U+2211), `◇` (U+25C7). These are **not**
admissible-alphabet additions: the cross-vendor intersection in
`audit_check_intersection.py` still excludes them because other columns
(Anthropic, GPT-4o, Llama, Mistral, Qwen, DeepSeek) continue to reject
them. They are recorded here for completeness — silent expansion is
forbidden by invariant 5, so any future promotion would require an explicit
spec edit, not a snapshot swap.

Provenance pin policy (ROADMAP L7) applies: the Gemma 2 → Gemma 4 swap is a
column-of-record forward roll, allowed at this patch boundary because the
X5 roadmap entry explicitly authorized it.

### Note

Patch release: audit tooling and docs only. No normative grammar change; no
checkpoint code touched in `tokenese_translator/`. Backward-compat fixture
`TKAB-W1.pair.json` still scores `win-conformant`. 144/144 translator tests
still pass; root security tests (3) still pass; new `test_audit_gemma4.py`
adds surface tests that import-without-cache and CLI dispatch are correct.

## [0.3.7] - 2026-06-17

### Added — GuideCheck Level 4 anchor + drift guard (ROADMAP N1 + N4)

- DNS TXT record at `_assistant-guide.tokenese.org` now advertises the live guide hash `sha256=151c29d182d8410681f3a40bfaa2875e8620e17e95995a27e0896f2f4d2de8dc`. With the cross-channel anchor in place, GuideCheck Level 4 is operational — a verifier can hash the fetched guide and compare against an independent control plane.
- `check_dns_anchor.py`: dependency-light CLI that resolves the TXT record across the authoritative nameserver plus three public resolvers (Cloudflare, Google, Quad9), extracts the advertised `sha256=...`, and asserts equality with the sha256 of `docs/.well-known/assistant-guide.txt`. Strict by default; `--allow-stale-public` tolerates public-resolver lag inside the TTL window (only the authoritative answer is treated as gating in that mode).
- `.github/workflows/dns_anchor.yml`: CI runs the check on every push to `main` that touches the guide or the check script, on every relevant PR, and on a daily 12:17 UTC schedule. Catches DNS drift even when no commits land.
- `RELEASE_CHECKLIST.md` trust-anchor gates now reference the DNS update step and the workflow that enforces it; the version-bump section now lists `skills/tokenese/MANIFEST.yaml` alongside `pyproject.toml` and `__init__.py`.

### Note

Patch release: tooling and CI only. No normative grammar change; no checker behavior changes; no code touched in `tokenese_translator/`. 144/144 translator tests still pass; 3/3 root security tests still pass. Closes ROADMAP N1 (DNS TXT anchor) and ROADMAP N4 (DNS-anchor drift guard).

## [0.3.6] - 2026-06-17

### Added — Release hygiene (ROADMAP L6)

- `RELEASE_CHECKLIST.md` at repo root: bounded, repeatable procedure for patch / minor / major releases, plus security / trust-anchor / hosted-page / roadmap gates.

### Changed — Security hardening pass

- `audit_anthropic.py`: API key is now read inside `main()` (via `_require_key()`) instead of at module import time. The script exits with code 2 and a helpful message when `ANTHROPIC_API_KEY` is unset, and the key is threaded as a parameter rather than a module global — the key never appears in stdout, stderr, or the output JSON.
- `.gitignore`: added `*.env` so environment files like `prod.env` are ignored (previously only `.env` and `.env.*` were covered).
- Added root-level `test_audit_anthropic.py` (3 tests) verifying the credential-handling contract with a mocked API — kept outside the `tools/translator/` suite, which stays at 132 passing.

Security sweep results: secrets sweep (history + tree) clean; `mcp_server.py` reviewed (no path-traversal / shell / arbitrary-code surface); dependencies reviewed (all pinned `>=`, standard sources); no GitHub Actions workflows present; trust anchors byte-identical with sha256 matching the manifest. No follow-up issues required.

### Note

Patch release: hygiene only. No grammar / spec / parser changes in `tools/translator/` (only the `__version__` / `pyproject.toml` version stamps were bumped per the release ritual). No follow-up issues were required (sweep clean apart from the two fixes above). INTENT.md §Exceptions row for `RELEASE_CHECKLIST.md` is now closed.

## [0.3.5] - 2026-06-17

### Added — Lexicon audit expansion (ROADMAP X2)

- Five new tokenizer audit scripts at the repo root: `audit_gemini.py`, `audit_qwen.py`, `audit_deepseek.py`, `audit_llama.py`, `audit_gemma.py`. Each writes a `data/source_provenance/<name>_costs.json` artifact (plus a top-level convenience copy, mirroring `anthropic_costs.json`). A shared `audit_candidates.py` (single source of truth for the candidate set) and `audit_common.py` (driver) keep all columns measuring the identical glyphs.
- `audit_check_intersection.py`: CI gate that fails on stale audit artifacts or silently-expanded admissible sets. Wired into `.github/workflows/audit.yml`.
- Lexicon admissibility now claimed across **7 tokenizer columns** (OpenAI o200k_base + Anthropic count-tokens + Gemini + Qwen + DeepSeek + Llama 3 + Gemma 2 as proxy for the unreleased Gemma 4).

### Changed

- `spec.md` §"Admissible alphabet" audit date bumped to 2026-06-17 and re-derived as the intersection across all 7 tokenizer columns. 4 of 8 Unicode survivors dropped: `√` `□` `†` `η` (each 2 tokens space-prefixed on Qwen; `□` also 2 tokens on Llama 3). The remaining 77 of 81 v0.2 admissible elements (all 22 ASCII sigils, 12 digraphs, 9 brackets, the 6 surviving Unicode glyphs `→ • § α β π`, and all 30 core words) survive the expansion.
- `DESIGN.md` §7: added a 7-column tokenizer-cost footnote noting that only `>>>` and `"""` are single-token across all columns; `?>>` splits to 2 tokens on DeepSeek/Gemma. These are grammar constructs, not lexicon glyphs, so the admissible alphabet is unaffected.

### Note

Patch release: audit-only. No grammar change. The admissible alphabet may shrink as new columns reject candidates, never silently expand (INTENT invariant 5). Required dependency added: `tokenizers>=0.19.0` for Hugging Face tokenizer access. `audit_gemini.py` requires `GEMINI_API_KEY` to run; skipped cleanly if absent (its optional dependency lives in `requirements-optional.txt`).

## [0.3.4] - 2026-06-17

### Added — Tokenese Skill Bundle (ROADMAP X1)

- New cross-surface portable skill at `skills/tokenese/` (v1.0.0). `SKILL.md` is the loadable instructions; `MANIFEST.yaml` provides provenance + hashes; `audit_card.md` is the one-page human reference; `install_guide.md` is the GuideCheck-aligned bounded-task guide; `examples/` covers handshake / encode-decode / validation / repair / assistant-guide consumption; `references/` mirrors the v0.3 sigil key, the 13 outcomes, and the checker decision order.
- New test `tests/test_skill_examples.py` parses every Tokenese block in `skills/tokenese/examples/*.md` and asserts validity; outcome-annotated examples are also checker-verified.

### Note

Patch release: docs/skill bundle only. No normative grammar change; no checker behavior changes. The skill ships no generator (encoding remains hand-authored or delegated to the reference translator), honoring the scoring-only scope lock.

## [0.3.3] - 2026-06-17

### Changed

- **spec.md reconciled with v0.3 grammar.** Version stamp updated 0.1.0 → 0.3. Spec now points authoritatively at GRAMMAR-v0.3.md for the v0.3 delta and DESIGN.md §7 for the complete sigil namespace, eliminating the v0.1↔v0.3 drift that landed on the public spec page. Added a Conformance section listing the checker / MCP surface / GuideCheck posture. Open-questions list replaced with the current ROADMAP cross-reference; the v0.2 open-questions list is annotated for closed vs open items. Hero example updated to use `^grammar:v0.3`.
- **`relationships.yaml` v1.** Bumped 0.1.0 → 1.0.0. Added grammar, reference_implementation, trust_anchors, roadmap top-level keys describing v0.3 grammar, the 132-test toolchain, the MCP server, the GuideCheck posture, and the ROADMAP. All existing relationships and prior-art entries preserved verbatim.
- **`ontology.json` v1.** Bumped 0.1.0 → 1.0.0. Added 10 v0.3 definitions (assistant_guide, causal_sigil, checker, conformance_level, frameset, grammar_version, handle, plain_block, repair_kind, source_authority). All 7 v0.1 definitions preserved verbatim; alphabetized.

### Note

Patch release: documentation and metadata only. No normative grammar change; no checker outcome changes; no code touched. 132/132 tests still passing. Resolves ROADMAP N3 (spec/grammar reconciliation) and closes the long-standing INTENT.md exception that called out `relationships.yaml` and `ontology.json` as v0 stubs.

## [0.3.2] - 2026-06-17

### Added

- `ROADMAP.md`: living roadmap grounded in INTENT/DESIGN. Highest-priority items: complete GuideCheck Level 4 (DNS anchor), the validating A/B experiment (the kill-criterion), and spec/grammar reconciliation. Next: a portable Tokenese skill bundle, more tokenizer columns, a vocabulary/frameset registry, a hosted conformance checker.
- Initial report-only frameset registry (`framesets.json`) with typed slot signatures for common ops (`deploy`, `get`, `run`, `set`, `fix`), plus `tokenese_translator.framesets.validate_framesets(...)`, MCP `validate_framesets`, and TKAB `frameset_validation` telemetry. This is an X3 partial: structural drift is reported but does not affect parser acceptance, conformance level, or checker outcome.

### Changed

- Package version bumped to `0.3.2`; public web, agent-facing, and repository docs now report the 132-test toolchain and the report-only frameset registry. Patch release; no normative grammar change.

## [0.3.1] - 2026-06-17

### Added

- GuideCheck `assistant-guide.txt` (human-verifiable-assistant-guide profile 0.6.0) for the bounded "install Tokenese and reproduce the lexicon audit" task: trust-anchored byte-identical pair (repo root + `docs/.well-known/`) plus a Level 4 sidecar manifest (`assistant-guide-manifest.txt`) with `guide-sha256`, `guide-bytes`, and immutable release URL. Discovery via `llms.txt`, `<link rel="assistant-guide">`, and a landing-page footer link.

### Changed

- Landing page (`docs/index.html`) synced to grammar v0.3: hero example uses the checker-verified v0.3 exchange, sigil table reflects the v0.3 operators (causal `>>> *>> ?>>`, negation `!@h`, hedge `@h?`, `^declare:level`, closed plain regions, repair sub-taxonomy, line comments), Tools/checker surfaced, version labels and dates refreshed.
- `llms.txt` updated for grammar v0.3 and the reference toolchain; added the assistant-guide reference.

### Note

- Patch release: agent-facing and web surfaces only, no normative grammar change. `spec.md` holds the foundational wire grammar; `GRAMMAR-v0.3.md` is the current grammar.

## [0.3.0] - 2026-06-16

### Added — Grammar v0.3.0 (backward-compatible minor)

- **Closed plain regions:** `^plain<<< ... >>>^plain` delimiters. Bare `^mode:plain` remains supported for backward compatibility.
- **Declarative conformance level:** `^declare:level=L<n>` artifact-level header. New outcome `fail-declared-level-mismatch` when declared level disagrees with achieved level.
- **Repair sub-taxonomy:** four kinds — `repair-token`, `repair-statement`, `repair-handle`, `repair-explained` (`??: <reason>`). Three-repair fail threshold unchanged.
- **Negation and hedge operators:** `!@handle` (negation prefix) and `@handle?` (hedge suffix). Compose freely.
- **Causal sigils:** `>>>` (temporal sequence), `*>>` (stipulated causation, requires source corroboration), `?>>` (hypothesized causation). New outcome `fail-unsupported-causation` for unsupported `*>>`.
- **Raw source quotes:** `"""..."""` form passes verbatim through parser; conflict detector treats content as verbatim source claim.
- **Centralized handle lexer:** new `tokenese_translator/handles.py` unifies kebab, snake, negation, and hedge handling across parser/renderer/misparse.
- **Grammar version dispatch:** `^grammar:v0.3` artifact header opts into v0.3 sigils. Absence is treated as v0.2 (backward compatibility).
- **Line comments:** `#` at line start runs to EOL. Inline `#` is not a comment.
- **TKAB layer:** deterministic per-pair scorer for the W1+L1 mini-pilot (`tools/translator/tkab/`). `tokenese-check` CLI, 5 v0.2 fixtures + 5 v0.3 fixtures, AUDIT_CARD, 12 TKAB tests + 25 grammar tests + 13 additional v0.3 tests.
- **Schema bump:** `tkab-check-1.0` → `tkab-check-1.1`. New fields: `declared_level`, `grammar_version`, `repair_kinds`, `plain_blocks`, `causal_events`, `comment_lines`, `unsupported_causation`.

### Changed

- `tokenese_translator/__init__.py` now exports `__version__ = "0.3.0"` and `grammar_version = "v0.3"`.
- `_provenance()` extended with `grammar_version_supported`, `grammar_version_detected`, `tkab_schema_version`.
- TKAB checker decision order now includes step 3.5 (`fail-unsupported-causation`) and step 4.5 (`fail-declared-level-mismatch`).

### Backward compatibility

All 71 v0.2-era tests and all 5 original TKAB v0.2 fixtures pass unchanged. v0.2 artifacts without `^grammar:v0.3` continue to parse and score identically.

## [0.1.0] - 2026-06-12

### Added

- spec.md v0.1.0 draft: wire grammar, reserved sigils, in-band symbol table, handshake, `??` repair protocol, admissible alphabet.
- Dual-tokenizer lexicon audit: `audit_symbols.py` (o200k_base + cl100k_base via tiktoken) and `audit_anthropic.py` (Anthropic count-tokens API), with results in `anthropic_costs.json`.
- Repo provisioning per Repo Standards v0.4 open-spec tier: INTENT.md, README.md, CHANGELOG.md, LICENSE (MIT, code) + LICENSE-SPEC (CC BY 4.0, spec text), CONTRIBUTING.md, SECURITY.md, CONFORMANCE.md, relationships.yaml, ontology.json, baseline .gitignore.
- Canonical home registered: https://tokenese.org/ (tokenese.dev reserved for tooling).
- Repo-polish pass: `.github/` issue + PR templates, README contributing section, GitHub description + homepage metadata, private repo created and pushed.
