# Handoff
Date: 2026-06-22
From: Codex
To: next Tokenese maintainer / model runner
Scope: repo-local implementation handoff for `snapsynapse/tokenese`

## Current state
The repo now has a deterministic N2 static package report, skill-bundle hash drift enforcement, and refreshed roadmap/spec/release docs. The worktree changes are intended to land as one coherent prep commit for ROADMAP X7, ROADMAP L7, and the N2 static package.

## Changed surfaces
- `tools/translator/tokenese_translator/n2_report.py`: new `tokenese-n2-report` implementation.
- `tools/translator/tests/test_n2_report.py`: tests for the N2 static package report.
- `tools/translator/pyproject.toml`: adds the `tokenese-n2-report` console script.
- `tools/translator/README.md`: documents the N2 report command.
- `tools/skills/compute_hashes.sh`: adds `--check` verification mode while preserving update mode.
- `.github/workflows/skill_hashes.yml`: CI guard for skill manifest hash drift.
- `ROADMAP.md`: marks X7 and L7 shipped pending release; N2 remains the only Now item.
- `spec.md`, `README.md`, `docs/llms.txt`, `docs/index.html`, `RELEASE_CHECKLIST.md`, `CHANGELOG.md`: current-state and release-gate sync.
- `DESIGN.md` and `INTENT.md`: existing precision-pivot updates from this working tree are preserved.

## Verification run
- `tools/skills/compute_hashes.sh --check`: passed.
- `git diff --check`: passed.
- `cd tools/translator && ../../.venv/bin/python -m pytest -q`: 156 passed.
- `.venv/bin/python -m pytest test_audit_anthropic.py test_audit_gemma4.py -q`: 7 passed.
- `.venv/bin/tokenese-n2-report --format json --strict`: passed.
- `.venv/bin/tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.pair.json`: `outcome: win-conformant`.

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
- Static receiver floor: fails at `0.7368` against the `0.75` threshold.
- Below-floor case: `S1-probabilistic-semantic-packet`.
- Misses: `not`, `observed`, `confidence`, `negative`, `negative`.

## Next work
1. Revise or retire `S1-probabilistic-semantic-packet` in `tools/translator/tokenese_translator/evals/receiver_cases.json`. It still reflects the semantic-neighborhood form that `DESIGN.md` section 10 says to abandon.
2. Keep N2 open until live multi-family A/B artifacts are attached and reproducible.
3. Run the fixed operational/code task suite in English and Tokenese for Claude, Codex, and at least one third independent model family.
4. Log tokens, task success, misparse/repair events, readback mismatches, receiver output, and misparse family (`binding`, `scope`, `sense`, `triangulation`) per exchange.
5. Preserve dense-loses cases in the suite.

## Constraints
- Do not add English-to-Tokenese generation.
- Report mismatches; do not silently repair.
- Compression claims must compare against terse or equal-precision English, not verbose English.
- Do not mutate `tools/translator/data/source_provenance/*` for this patch. Those files are source-provenance pins, not live handoff notes.
