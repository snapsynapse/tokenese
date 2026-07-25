# PROJECT_CONTEXT.md — Tokenese

ARCHIVED 2026-07-25. Repo is read-only, preserved as a measured post-mortem of the designed-interlingua idea. Read POST-MORTEM.md first; descriptions below are historical.

Context for content, docs, and skill workflows operating on this repo.

## What this is

Tokenese is a **token-native interlingua for LLM-to-LLM communication** — a
message format engineered to be simultaneously more compressed and more precise
than human prose, measured in real tokenizer tokens rather than characters. Its
defining discipline: a symbol is admitted to the lexicon only when it survives a
**reproducible cross-tokenizer audit** across seven certified tokenizers
(OpenAI `o200k_base`, Anthropic, Gemini, Qwen, DeepSeek, Llama 3, Gemma 4 E4B).
Every claim is measured, not asserted.

The repository is both the **specification** (root Markdown docs) and the
reference **translator + conformance scorer** (`tools/translator/`). The scorer
only reports; it never generates or repairs.

## Audience

- Teams building **multi-agent systems** who want machine-to-machine messages
  more compressed and precise than natural language, with each vocabulary symbol
  verified by audit rather than assertion.
- Coding agents and LLMs consuming the spec directly (a hosted assistant guide
  and `llms.txt` are provided for machine consumption).
- Contributors, who must pass the admission criteria in `INTENT.md`.

## Style and tone

Discernible from existing docs (README, INTENT, DESIGN, ROADMAP):

- **Rigorous and evidence-first.** "Claims must be measured, not asserted" is the
  cultural anchor. Docs openly record failed claims (e.g. an illustrative example
  was removed when token-counting contradicted its compression claim).
- **Precise, technical, unhyped.** Spec references (R5.3, R1.3, invariant 6) are
  used inline. Roadmap horizons are priority bands, not dates.
- **Honest about status.** Sections explicitly separate shipped work from open
  questions and pending measurements. A kill-criterion (N2) is stated plainly.
- Occasional vivid framing in vision copy ("watching film in black and white"),
  but body content stays spare and factual.

## Key URLs

- Canonical site: https://tokenese.org/
- Repo: https://github.com/snapsynapse/tokenese
- Assistant guide verification: https://guidecheck.org/verify
- Reserved tooling domain (future hosted checker): `tokenese.dev` (X4, not built)

## Current status

- Grammar **v0.3**; release **v0.3.9** (2026-06-25). Phase A complete.
- Seven-column tokenizer-audited lexicon; deterministic per-pair checker; CLI +
  MCP server; portable skill bundle; hosted WCAG 2.1 AA landing page; GuideCheck
  Level 4 DNS-anchored assistant guide with daily drift CI.
- Single open **Now** item: **N2**, the live cross-family A/B experiment that
  validates the core "more compressed AND more precise" claim. Phase B work is
  underway in `working-session/`.
- License: code MIT, specification text CC BY 4.0.

## Notes for content work

- Do not publish compression claims without reproducible token counts on the
  certified tokenizers, compared against **terse** (not verbose) English.
- The hosted assistant guide and its DNS anchor are drift-protected; edits to
  `docs/.well-known/assistant-guide.txt` must keep the sidecar manifest and TXT
  record in sync (CI enforces this).
