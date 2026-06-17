# Skill Changelog — tokenese

All notable changes to the Tokenese skill bundle. This is the skill's own
changelog, separate from the repository `CHANGELOG.md`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The skill version tracks the bundle, not the spec; it targets grammar v0.3 and
schema `tkab-check-1.1`.

## [1.0.0] - 2026-06-17

### Added

- Initial cross-surface portable skill at `skills/tokenese/` (ROADMAP X1).
- `SKILL.md`: the loadable instructions — handshake, encode/decode, validate,
  repair, trust anchors, scope locks, provenance.
- `MANIFEST.yaml`: provenance, version, and sha256 hashes of `SKILL.md`,
  `audit_card.md`, and `install_guide.md`.
- `audit_card.md`: one-page human reference (sigil key, anchor scales,
  allusion ledger).
- `install_guide.md`: GuideCheck-aligned bounded-task guide for installing the
  skill and verifying the toolchain.
- `examples/`: handshake, encode/decode, validate, repair, and
  assistant-guide consumption walkthroughs.
- `references/`: the v0.3 sigil key, the 13 stable checker outcomes, and the
  checker decision order.
- `tests/test_skill_examples.py`: parses every Tokenese block in `examples/`
  and asserts validity; outcome-annotated examples are checker-verified.

### Notes

- Scoring-only: the skill teaches calling the reference toolchain, not
  substituting for it. No generator ships; the English→Tokenese direction is
  out of scope. Source-as-authority preserved.
