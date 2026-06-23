# Handoff
Date: 2026-06-23
From: Codex
To: next Tokenese maintainer / model runner
Scope: repo-local implementation handoff for `snapsynapse/tokenese`

## Current state
Phase A is complete. Tokenese `v0.3.9` has been committed, tagged, pushed, and published as a GitHub Release.

The repo now has a deterministic N2 static package report, skill-bundle hash drift enforcement, refreshed roadmap/spec/release docs, and the stale S1 receiver fixture has been revised away from abandoned semantic-neighborhood operators. The static receiver floor now clears the `0.75` threshold, so the repo is ready for the pre-Turnfile handoff point.

Release artifacts:
- Commit: `d69a0aa Release Tokenese v0.3.9`
- Tag: `v0.3.9`
- Release: `https://github.com/snapsynapse/tokenese/releases/tag/v0.3.9`

## Changed surfaces
- `tools/translator/tokenese_translator/n2_report.py`: new `tokenese-n2-report` implementation.
- `tools/translator/tests/test_n2_report.py`: tests for the N2 static package report and the now-passing receiver static floor.
- `tools/translator/pyproject.toml`: adds the `tokenese-n2-report` console script and bumps the package to `0.3.9`.
- `tools/translator/tokenese_translator/__init__.py`: bumps `__version__` to `0.3.9`.
- `tools/translator/README.md`: documents the N2 report command.
- `tools/translator/tokenese_translator/evals/receiver_cases.json`: revises `S1-probabilistic-semantic-packet` to use explicit `near[...]`, polarity-safe `far_from[...]`, and `confidence:8/9`.
- `tools/translator/tokenese_translator/evals/hypothesis_cases.json`: removes remaining live fixture uses of abandoned `~=` / `!~=` semantic-neighborhood forms.
- `tools/skills/compute_hashes.sh`: adds `--check` verification mode while preserving update mode.
- `.github/workflows/skill_hashes.yml`: CI guard for skill manifest hash drift.
- `ROADMAP.md`: marks X7 and L7 shipped in `v0.3.9`; N2 remains the only Now item.
- `spec.md`, `README.md`, `docs/llms.txt`, `docs/index.html`, `RELEASE_CHECKLIST.md`, `CHANGELOG.md`: current-state and release-gate sync.
- `DESIGN.md` and `INTENT.md`: existing precision-pivot updates from this working tree are preserved.

## Verification run
- `tools/skills/compute_hashes.sh --check`: passed.
- `git diff --check`: passed.
- `cd tools/translator && ../../.venv/bin/python -m pytest -q`: 156 passed.
- `.venv/bin/python -m pytest test_audit_anthropic.py test_audit_gemma4.py -q`: 7 passed.
- `.venv/bin/tokenese-n2-report --format json --strict`: passed. It required an unsandboxed run in Codex because `tiktoken` needed access to the `cl100k_base` cache/network path; the repo itself did not require code changes for this.
- `.venv/bin/tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.pair.json`: `outcome: win-conformant`.
- `git push origin main`: pushed `d69a0aa`.
- `git push origin v0.3.9`: pushed tag.
- `gh release create v0.3.9 --title "Tokenese v0.3.9" --notes-file /tmp/tokenese-v0.3.9-notes.md`: published release.

## N2 static package result
Run:
```bash
.venv/bin/tokenese-n2-report --format markdown
```
Current report:
- Status: `static-package-ready/live-ab-open`.
- N2 closed: `false`.
- Hypothesis counts: 18 fair-baseline comparisons, 13 o200k wins, 4 losses, 1 break-even.
- TKAB fixtures: 10 total.
- Static receiver floor: passes. Minimum score is `0.85` against the `0.75` threshold.
- Cases below threshold: none.
- Revised S1 score: `1.0`.

## Next work
1. Keep N2 open until live multi-family A/B artifacts are attached and reproducible.
2. Run the fixed operational/code task suite in English and Tokenese for Claude, Codex, and at least one third independent model family.
3. Log tokens, task success, misparse/repair events, readback mismatches, receiver output, and misparse family (`binding`, `scope`, `sense`, `triangulation`) per exchange.
4. Preserve dense-loses cases in the suite.
5. Do not register Tokenese tasks in Turnfile until the maintainer initiates that phase.

## Constraints
- Do not add English-to-Tokenese generation.
- Report mismatches; do not silently repair.
- Compression claims must compare against terse or equal-precision English, not verbose English.
- Do not mutate `tools/translator/data/source_provenance/*` for handoff updates. Those files are source-provenance pins, not live handoff notes.
