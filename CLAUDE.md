# CLAUDE.md — agent guidance for `tokenese`

Concise orientation for coding agents. For the full architecture, scope locks,
and PR conventions, read [AGENTS.md](AGENTS.md) first — this file summarizes and
points into it.

## Purpose

Tokenese is a **token-native interlingua for LLM-to-LLM communication**: a
message format designed to be more compressed *and* more precise than human
prose, measured in real tokenizer tokens. A symbol enters the lexicon only if it
survives a reproducible cross-tokenizer audit (currently OpenAI `o200k_base` +
Anthropic + Gemini + Qwen + DeepSeek + Llama 3 + Gemma 4 E4B). Canonical home:
https://tokenese.org/

The repo holds both the **specification** (repo root) and a **deterministic
Tokenese→English translator + scorer** (`tools/translator/`). Claims are
measured, not asserted (INTENT invariant 6).

## Stack

- **Python** (stdlib-first). Only required runtime dep is `tiktoken` (lexicon
  audit); the translator package itself is dependency-free. See
  `requirements.txt` / `requirements-optional.txt`.
- Installable package under `tools/translator/` (`pip install -e .`), exposing
  console scripts `tokenese-translate`, `tokenese-check`, `tokenese-n2-report`,
  and an MCP server (`python -m tokenese_translator.mcp_server`).
- Docs/spec in Markdown; data in JSON/YAML; hosted landing page in `docs/`
  (GitHub Pages from `main` `/docs`).

## Directory layout

- Repo root — spec + governance docs (read-mostly): `spec.md`, `DESIGN.md`,
  `CONFORMANCE.md`, `INTENT.md`, `GRAMMAR-v0.3.md`, `ROADMAP.md`, `HANDOFF.md`,
  `CHANGELOG.md`, `RELEASE_CHECKLIST.md`.
- `audit_*.py`, `audit_common.py`, `audit_check_intersection.py`,
  `check_dns_anchor.py` — lexicon tokenizer audits + DNS anchor check. Cost
  fixtures pinned under `data/source_provenance/`.
- `tools/translator/` — the `tokenese_translator` package + `tkab` scorer,
  `tests/` (156+ tests), `golden/` fixtures, `data/source_provenance/`
  (pinned SHAs — do not mutate for handoff updates).
- `skills/tokenese/` — portable cross-surface skill bundle (hash-pinned via
  `MANIFEST.yaml`).
- `docs/` — hosted spec site + `.well-known/assistant-guide.txt` (GuideCheck
  Level 4, DNS-anchored).
- `working-session/` — live Phase B working notes (WORKLOG, MAILBOX, strawman).
- `.github/workflows/` — CI (see below).

## Conventions (see AGENTS.md for full detail)

- **Scope locks (do not violate):** scoring-only — never add English→Tokenese
  generation; the checker reports mismatches, never repairs (R5.3); source text
  is authority, preserved byte-for-byte (R1.3/R1.5); no Turnfile concepts in
  this repo.
- Compression claims must compare against **terse or equal-precision** English,
  never verbose prose.
- All new features ship with tests under `tools/translator/tests/`
  (`test_<feature>.py`). Grammar changes: bump `__version__` (semver), add a
  CHANGELOG `[X.Y.Z]` entry, update the GRAMMAR doc, add backward-compat tests.
- Spec changes require matching scorer updates so the checker stays in sync, and
  provenance-pin SHAs (`tools/translator/data/source_provenance/SHA256SUMS.txt`)
  update only on normative grammar releases.

## Build / test (from docs — do not run unless asked)

```
# translator package
cd tools/translator && pip install -e . && pytest -q       # expect 156+ passed
# reproduce lexicon audit
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python audit_symbols.py
ANTHROPIC_API_KEY=... .venv/bin/python audit_anthropic.py
# repo-root security/audit-surface tests add 7 more
```

## CI (`.github/workflows/`)

- `audit.yml` — offline lexicon audits on PRs touching audit scripts / spec.
- `dns_anchor.yml` — daily + on-push check that the `_assistant-guide.tokenese.org`
  TXT record matches the live hosted assistant guide (drift detection).
- `skill_hashes.yml` — fails when pinned skill files drift from
  `skills/tokenese/MANIFEST.yaml`.

## Current state

Grammar **v0.3** current; release **v0.3.9** (2026-06-25, tagged + published).
Phase A complete: seven-column tokenizer audit done, N2 static package report
ships, skill-bundle hash drift enforced, static receiver floor clears the 0.75
threshold. The single open **Now** item is **N2** — the live cross-family A/B
experiment (Claude vs Codex vs a third family) that converts "a designed
language" into "a measured language." That work is in progress under
`working-session/` (Phase B). Do not register Tokenese tasks in Turnfile until
the maintainer initiates that phase.
