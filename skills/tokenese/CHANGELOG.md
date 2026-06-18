# Skill Changelog — tokenese

All notable changes to the Tokenese skill bundle. This is the skill's own
changelog, separate from the repository `CHANGELOG.md`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The skill version tracks the bundle, not the spec; it targets grammar v0.3 and
schema `tkab-check-1.1`.

## [1.0.1] - 2026-06-18

### Changed

- `SKILL.md` "Trust anchors" section: assistant guide bumped from GuideCheck
  Level 3 to Level 4. The Level 3 sidecar-manifest sha256 is still authoritative;
  Level 4 adds a cross-channel DNS TXT anchor at
  `_assistant-guide.tokenese.org` that advertises the same hash. A verifier may
  now cross-check the guide against three independent sources (repo, manifest,
  DNS). Shipped in the main repo as ROADMAP N1 (v0.3.7).
- `MANIFEST.yaml`: `trust_anchors.assistant_guide.level` bumped from `3` to `4`;
  new `dns_anchor: _assistant-guide.tokenese.org` field. `SKILL.md` hash
  updated to reflect the trust-anchor copy edit and version bump;
  `audit_card.md` and `install_guide.md` are byte-for-byte unchanged.
- `released: 2026-06-18`.

### Notes

The Tokenese spec advanced from v0.3.2 to v0.3.8 across the parent repo while
this skill was at 1.0.0; the skill version tracks the bundle, not the spec.
No skill-surface contract change — grammar v0.3 and `tkab-check-1.1` are
unchanged. The scoring-only scope lock and English→Tokenese out-of-scope
rule still hold.

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
