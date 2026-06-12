# Contributing to Tokenese

Tokenese is an open specification. Contributions are welcome, but every change passes the admission criteria in [INTENT.md](INTENT.md). The short version: claims must be measured, not asserted.

## Ground rules

1. Lexicon additions require audit evidence. Run `audit_symbols.py` and `audit_anthropic.py` (or the equivalent for a newly certified tokenizer) and include the output in your PR. A symbol that costs 2+ tokens worst case in any certified tokenizer is rejected, however elegant.
2. Grammar changes must preserve parse determinism: one statement, one reading. Include before/after parses of any affected example.
3. Compression claims require token counts on the spec's example corpus, before and after.
4. Nothing that dulls precision to gain compression. Tokenese is not a pidgin (INTENT.md invariant 3).
5. Spec text changes follow the versioning rules in the spec header: bump version, date, and CHANGELOG.md together.

## Workflow

1. Open an issue describing the change and which invariant or open question it addresses.
2. Fork, branch, make the change with its evidence.
3. PR with audit output attached. CI (when present) re-runs the audit scripts.

## What we especially want

- Third and fourth tokenizer columns (Gemini, Qwen, Mistral) with audit data.
- A/B transcripts: same task in English and Tokenese, with token counts and misparse-retry counts.
- Frequent-word sweeps that enlarge the certified single-token vocabulary.

## Licensing of contributions

Code contributions are accepted under MIT; spec text contributions under CC BY 4.0. See LICENSE and LICENSE-SPEC.
