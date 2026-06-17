# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-12

### Added

- spec.md v0.1.0 draft: wire grammar, reserved sigils, in-band symbol table, handshake, `??` repair protocol, admissible alphabet.
- Dual-tokenizer lexicon audit: `audit_symbols.py` (o200k_base + cl100k_base via tiktoken) and `audit_anthropic.py` (Anthropic count-tokens API), with results in `anthropic_costs.json`.
- Repo provisioning per Repo Standards v0.4 open-spec tier: INTENT.md, README.md, CHANGELOG.md, LICENSE (MIT, code) + LICENSE-SPEC (CC BY 4.0, spec text), CONTRIBUTING.md, SECURITY.md, CONFORMANCE.md, relationships.yaml, ontology.json, baseline .gitignore.
- Canonical home registered: https://tokenese.org/ (tokenese.dev reserved for tooling).
- Repo-polish pass: `.github/` issue + PR templates, README contributing section, GitHub description + homepage metadata, private repo created and pushed.
