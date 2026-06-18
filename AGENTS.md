# Agents Guide — snapsynapse/tokenese

This repository contains the Tokenese token-native interlingua specification (`spec.md`, `DESIGN.md`, `CONFORMANCE.md`, `INTENT.md`, `GRAMMAR-v0.3.md`) and a deterministic Tokenese→English translator + scorer under `tools/translator/`.

Read this file before making changes. It defines architecture, scope locks, conventions, and how to verify changes.

## Architecture

Repo root: spec + design + conformance + governance docs. Treat as read-mostly.

`tools/translator/`: Python package (`tokenese_translator`) + scorer package (`tkab`). Self-contained, installable with `pip install -e .`.

- `tokenese_translator/`: base Tokenese→English translator originally built for the Turnfile project. Modules:
  - `handles.py` — centralized handle lexer (kebab + snake + negation/hedge)
  - `parser.py` — parse Tokenese transcript to AST nodes (Binding, Statement, ModeSwitch, Repair, PlainBlock, LevelDeclaration, GrammarVersion, Comment, Unparseable)
  - `renderer.py` — render AST back to natural English
  - `misparse.py` — misparse-family classifier (dense-line scoped)
  - `score.py` — pair scoring + `_provenance()` SHAs
  - `readback.py`, `validator.py`, `session.py`, `lexicon.py`, `lexer.py`, `token_count.py`
  - `cli.py` — `tokenese-translate` command (decode + conformance summary; `--json` for structured output)
  - `mcp_server.py` — MCP server exposing translator + scorer tools
- `tkab/`: deterministic per-pair scorer for the PRD-027 W1+L1 mini-pilot.
  - `checker.py` — `check_pair(...)` classifier (output schema `tkab-check-1.1`)
  - `cli.py` — `tokenese-check` command
  - `AUDIT_CARD.md` — schema, outcome enum, decision order
  - `fixtures/` — 10 pair files (5 v0.2 + 5 v0.3)
- `tests/`: 144 tests (as of v0.3.8). `test_translator.py` (base), `test_golden.py`, `test_grammar_coverage.py`, `test_tkab.py`, `test_grammar_v03.py`, and feature-specific suites added across v0.3.3 – v0.3.8.

## Scope locks (do not violate)

1. **Scoring-only.** Do NOT add English→Tokenese generation. The checker scores; it does not generate or repair.
2. **No Tokenese clone generation.** Fixture `clone_text` content is hand-authored, not produced by a model.
3. **No Turnfile concepts.** This repo is independent of Turnfile (the translator was originally built there; this repo is now its canonical home).
4. **Report, don't repair (R5.3).** Mismatches, misparses, repair events, and source-authority conflicts are reported in the output. Never silently fixed.
5. **Source is authority (R1.3/R1.5).** The clone's `source_text` is preserved byte-for-byte in checker output. Clone bindings are never decoded as ground truth.

## Conventions

- Python: stdlib-only where possible. The only required runtime dep is `tiktoken` (lexicon audit). The translator package itself is dep-free.
- All new features must include tests in `tools/translator/tests/`. Naming pattern: `test_<feature>.py` or extend an existing file.
- Grammar changes: bump `__version__` (semver), add a `[X.Y.Z]` CHANGELOG entry, update `GRAMMAR-v0.3.md` or create `GRAMMAR-v<new>.md`, and add backward-compatibility tests proving older artifacts still parse.
- Spec changes (`spec.md`, `DESIGN.md`, `CONFORMANCE.md`, `INTENT.md`): require corresponding scorer updates so the checker stays in sync with the spec.

## Verification gate

Before opening any PR, run:

```
cd tools/translator
pip install -e .
pytest -q
```

Must show `144 passed` minimum as of v0.3.8 (more is fine; fewer means regression). Repo-root tests (`test_audit_anthropic.py`, `test_audit_gemma4.py`) add 7 more; intersection check runs in CI.

For grammar changes, also manually verify a v0.2 fixture still classifies correctly:

```
tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.pair.json
```

Expected: outcome `win-conformant`.

## Commit hygiene

Commit in logical chunks. Suggested chunking when adding features:

1. Lexer / handle infrastructure
2. Parser AST nodes
3. Renderer
4. Misparse detector
5. Scorer (checker) logic
6. Tests
7. Fixtures
8. Spec docs

## PR conventions

- Branch naming: `tools/<area>` for tooling, `grammar/v<X.Y.Z>` for grammar bumps, `spec/<topic>` for spec edits, `fix/<short-description>` for fixes.
- PR title: declarative, mentions the spec reference(s) it touches (e.g., `R6.3`, `R5.4`).
- PR body: summary, list of additions/changes, scope-locks-honored statement, pytest tally, link to relevant AUDIT_CARD or GRAMMAR doc.

## Known gh CLI quirk

`gh pr edit` and some `gh pr view --json` queries hit a deprecated GraphQL field (`repository.pullRequest.projectCards`) and fail. Workaround for body updates:

```
gh api --method PATCH /repos/snapsynapse/tokenese/pulls/<num> --input - <<'JSON'
{"body": "..."}
JSON
```

## Quick reference — outcomes (TKAB)

Stable enum (do not reorder; checker decision logic depends on iteration order in some tests):

```
win-conformant
l1-plain-success
fail-unparseable
fail-source-authority-conflict
fail-unsupported-causation         # v0.3, step 3.5
fail-illegal-derivation
fail-three-repairs
fail-grammar
fail-misparse
fail-no-plain-exit
fail-mixed-exit
fail-declared-level-mismatch       # v0.3, step 4.5
indeterminate
```

Decision order: see `tools/translator/tkab/AUDIT_CARD.md`.

## Provenance

Pinned SHAs for spec/design/conformance/intent/handoff/anthropic_costs live in `tools/translator/data/source_provenance/SHA256SUMS.txt`. `_provenance()` reads these at scorer-init time. Update SHAs when spec files change.
