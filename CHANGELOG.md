# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
