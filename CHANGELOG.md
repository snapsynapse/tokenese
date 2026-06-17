# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
