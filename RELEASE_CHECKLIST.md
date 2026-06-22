# Release Checklist

A bounded, repeatable procedure for every release tag in `snapsynapse/tokenese`.
This document is the source of truth — if a step here disagrees with practice,
update the doc, not the practice.

Last reviewed: 2026-06-22 (v0.3.x series).

## Release classes

| Class | Examples | Required steps |
|---|---|---|
| **Patch (0.X.Y → 0.X.Y+1)** | Docs reconciliation, additive audits, skill bundle | §"Patch release" |
| **Minor (0.X → 0.X+1)** | Grammar additions (backward compat) | §"Minor release" |
| **Major (0.X → X+1.0)** | Breaking grammar / schema changes | §"Major release" |

## Patch release

1. **Branch from `main`** with a descriptive name (`docs/<topic>`, `audit/<topic>`, `chore/<topic>`).
2. **Bump version** in:
   - `tools/translator/pyproject.toml` `[project] version`
   - `tools/translator/tokenese_translator/__init__.py` `__version__`
   - `skills/tokenese/MANIFEST.yaml` if any of the three pinned skill files changed (recompute via `tools/skills/compute_hashes.sh`)
3. **CHANGELOG entry** under a new `[X.Y.Z] - YYYY-MM-DD` heading. Clear `[Unreleased]`.
4. **Tests:** `cd tools/translator && pytest -q` — must show ≥ 156 passing (current baseline; adjust upward as the suite grows).
5. **Backward-compat sanity:** `tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.pair.json` still outputs `outcome: win-conformant`.
6. **Docs touched check:** if README, AGENTS, spec, DESIGN, CONFORMANCE, GRAMMAR-vX.Y were changed, scan for version-stamp drift before opening PR.
7. **Open PR** with title pattern: `<area>: <summary> (ROADMAP <ref> if applicable)`. Body must list:
   - Summary of changes
   - Backward-compat statement
   - Pytest tally
   - Scope-locks-honored statement
   - ROADMAP cross-reference if applicable
8. **Merge to `main`.**
9. **Tag** the merge commit as `vX.Y.Z` and create a GitHub Release with the CHANGELOG section as the body.

## Minor release

All of "Patch release" plus:

10. **Backward-compat tests:** every fixture from the prior minor version (e.g. v0.2 TKAB fixtures when releasing v0.3) must continue to score to its expected outcome. Document this in the PR body.
11. **GRAMMAR-vX.Y.md** new file documenting the delta from the previous minor. Layered structure: `spec.md` is the canonical wire grammar; `GRAMMAR-vX.Y.md` is just the additive delta.
12. **DESIGN.md §7 (sigil table)** updated with rows tagged `(vX.Y)` for new sigils. Grammar version stamp at top of §7 bumped.
13. **AUDIT_CARD.md** schema version bumped if the checker output schema changed. Decision-order updates documented.
14. **MCP surface review:** if new tools were added, confirm they appear in `mcp_server.py` and are listed in `AGENTS.md`.

## Major release

All of "Patch" and "Minor" plus:

15. **Migration guide:** new file `MIGRATION-vX.md` documenting how to update from the prior major version. Include a worked example.
16. **Deprecation policy:** which v(X-1) surfaces remain supported, for how long, and what triggers their removal.
17. **External communications:** announcement draft for tokenese.org, blog, etc. — Major releases require explicit user sign-off before announcement (per INTENT invariant 6 — announce on evidence, not intent).

## Security gates (every release)

- [ ] No secrets committed (run `git log --all -p | grep -iE 'api[_-]?key|secret|password|token' --color` and review hits).
- [ ] No `.env` or `*.env` files committed.
- [ ] All API-calling scripts read credentials from environment variables, not source.
- [ ] No `print(<credential>)` or log statements that could leak secrets.
- [ ] `requirements.txt` pins minimum versions for security-critical deps.
- [ ] If any new dependency is added, document it in PR body with the reason and a link to the maintainer / source.

## Trust-anchor gates (when assistant-guide or docs/.well-known changes)

- [ ] `assistant-guide.txt` and `docs/.well-known/assistant-guide.txt` are byte-identical (`diff` returns nothing).
- [ ] `assistant-guide-manifest.txt` sha256 matches both copies of the guide.
- [ ] If a new bounded task is added, it lives in a NEW guide file — never modify the existing one in-place (changing bytes invalidates the manifest).
- [ ] DNS TXT record at `_assistant-guide.tokenese.org` updated to advertise the new `sha256=<hex>` (the `GuideCheck Level 4 anchor` CI job, `check_dns_anchor.py`, will fail until it is). Public resolvers can take up to TTL (current 1800s) to converge after the registrar save.

## Audit-column gates (when a tokenizer column changes or a new column lands)

- [ ] The audit script (`audit_<vendor>.py`) runs locally without error and writes a fresh `data/source_provenance/<vendor>_costs.json` (plus the top-level convenience copy).
- [ ] `audit_check_intersection.py` exits 0 against the new snapshot — no admissible-alphabet symbol is silently dropped.
- [ ] Every newly-rejected symbol is enumerated in the CHANGELOG entry with a one-line rationale (INTENT.md invariant 5, ROADMAP L7).
- [ ] If the change is a column-of-record swap (model variant change, proxy → native, etc.), the prior column's snapshot is preserved at the previous release tag (do not delete commit history) and the swap is justified in the CHANGELOG.

## Source-provenance pin policy

`tools/translator/data/source_provenance/SHA256SUMS.txt` is part of the measured-claim surface. Patch releases must leave `_provenance()` source hashes byte-stable unless the roadmap explicitly authorizes a column-of-record swap.

- [ ] For patch releases: confirm no source-provenance pins changed, or cite the roadmap item that authorizes the exception.
- [ ] For minor or major grammar releases: roll source-provenance pins only after the normative spec/design/conformance changes are complete, then document the roll in the CHANGELOG.
- [ ] For docs-only releases: update live docs, not source-provenance snapshots.

## Skill-bundle gates (when skills/tokenese pinned files change)

- [ ] Run `tools/skills/compute_hashes.sh` after editing `skills/tokenese/SKILL.md`, `skills/tokenese/audit_card.md`, or `skills/tokenese/install_guide.md`.
- [ ] Run `tools/skills/compute_hashes.sh --check`; the `Skill bundle hashes` CI job enforces the same check on PRs.
- [ ] If the skill manifest changes, update `skills/tokenese/CHANGELOG.md` and the version/date fields in `skills/tokenese/MANIFEST.yaml` when appropriate.

## Hosted-page gates (when docs/ changes)

- [ ] `docs/index.html` validates against WCAG 2.1 AA (axe-core, 0 violations).
- [ ] `docs/sitemap.xml` lists every page that should be indexed.
- [ ] `docs/robots.txt` per-bot allows match the current policy.
- [ ] `docs/llms.txt` mirrors the canonical claims in `INTENT.md` + `spec.md`.
- [ ] `docs/.nojekyll` present (Jekyll skips dot-dirs without it, breaking `.well-known/`).

## Roadmap synchronization

After every release, scan `ROADMAP.md`:

- [ ] Items shipped in this release moved from Now/Next/Later → Shipped baseline.
- [ ] Items newly identified added to Now/Next/Later as appropriate.
- [ ] Items blocked by N2 measurement: leave in place; do not promote without evidence.
- [ ] `Last updated:` field bumped.

## Release announcement (optional)

For releases worth announcing (v0.3.0 grammar bump, v1.0.0 major, any release on evidence from N2 measurements):

- [ ] Generate `og.png` social card (deferred per INTENT exception until promo-orchestrator runs).
- [ ] Update `docs/index.html` version label + release date.
- [ ] Schedule via `promo-orchestrator` / `blog-image-prompt` workflows.

## When in doubt

- Read INTENT.md §"Admission criteria for changes" — every release must pass those gates.
- Read ROADMAP.md "How items get promoted" — the gating logic for what's shippable.
- Read this file before opening the PR. Update it when practice diverges.
