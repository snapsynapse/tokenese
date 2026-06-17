# CAPABILITIES & Provenance — tokenese-translator

**Build:** `tokenese-translator` 0.1.0
**Schema:** `PairScore` 1.0
**Target grammar:** **Tokenese v0.2** as defined by `DESIGN.md §7` (the sigil namespace table that supersedes `spec.md` v0.1 where they differ), plus v0.1's wire grammar where DESIGN.md does not override.

This document is the single source of truth for what the translator does and does not do, the schema it emits, how it counts tokens, and where its ground-truth fixtures live.

## 1. Grammar target + commit pin

The translator parses everything Codex is taught for the A/B: every entry in DESIGN.md §7 plus every v0.1 construct DESIGN.md does not retire. The bundled `data/source_provenance/SHA256SUMS.txt` pins the exact source files this build is calibrated against.

| Source file | SHA256 |
|---|---|
| `spec.md` v0.1.0 | `68cb84e2dbb2aa36f9965c823afab770de64df0bd9df0bc1c878eb3aac5f761e` |
| `DESIGN.md` v0.1.0 | `5dc9338e7b6386d01ae46b47a6a7ba70478929460ecdea74b67e20afe204d520` |
| `INTENT.md` (7 invariants) | `5f783b8367feef6d9ab69a685ea5964419ba7222095b8b29a07aee1a9334ade0` |
| `CONFORMANCE.md` L1–L4 | `0250b71342c49603f40fe667700422d03a95855cd45c0825841a6a8f35e987c6` |
| `anthropic_costs.json` (197 entries) | `12e5fe083ecf44949ec1d55fb43c1f6f547979256f2f832fef4788afbd7c91d2` |
| `HANDOFF.md` | `16f948709345ee2d32ff363e90ec8782129be08d9aa3ddb7c4030afeab45c1b3` |

Every `score_pair` output emits these SHAs in its `provenance` block so each row in the A/B log is self-identifying.

### Constructs covered (33-case grammar probe in `tests/test_grammar_coverage.py`)

`@noun` and `@N` handles (bind, reference, drop) · `??` repair, including `?? :slot`, `?? @handle`, `?? †anchor` addressing · `^N` ordinal confidence (statement-level and per-distribution-entry) · `cause:a^6|b^3|c^1` ranked-alternative distribution slots (k≤3 enforced) · `□` typed holes (key form and value form) · `†anchor` corpus anchors with awaiting-gloss marker · `√` ack/readback reply · `{ }` proposition quoting (depth 1) · `not( )` negation scope · `ev:obs|heard|mem|guess` evidentials · `dense`/`plain` mode switching · `tokenese? v:0.1` / `tokenese ok v:0.1` handshake · `like X not Y` contrast pin · `because` causal attribution · `->` sequence/yield · `=>` implication · `~` approximate · `::` type tag · `#tag` · `§rule` references · `//` human comments · `!` imperative + readback trigger.

## 2. Six-capability coverage map

| # | Brief deliverable | Status | Where |
|---|---|---|---|
| (a) | Conformance checker L1/L2/L3 | **Present** | `tokenese_translator/validator.py`; tools `validate`, `score_pair.conformance` |
| (b) | Lexicon audit vs `anthropic_costs.json` | **Present** | `audit_lexicon()` re-derives C1 from bundled costs |
| (c) | Token counter, both tokenizers (o200k + Anthropic) | **Present** | `token_count.py`. o200k via `tiktoken` (local). Anthropic via cached `anthropic_costs.json` by default; live API opt-in |
| (d) | Tokenese → English decoder | **Present** | `renderer.py`; tool `to_english`. Preserves epistemic channels rather than smoothing them away |
| (e) | Readback differ (K4 transformed vs verbatim) | **Present** | `readback.py`; verdict ∈ `{verbatim, near_verbatim, transformed, unrelated}` from LCS + token-set Jaccard + Levenshtein. Thresholds exposed as module constants for the harness to override |
| (f) | Misparse-family classifier (binding/scope/sense/triangulation) | **Present** | `misparse.py`; deterministic rules over the AST + session state |

## 3. Determinism + constraints

- **No model calls** in the decode or score path. Period.
- **No network calls** by default. The only optional non-deterministic surface is `count_anthropic_live()`, gated by `live_anthropic=True` AND `ANTHROPIC_API_KEY`; it is **off by default**.
- **No randomness, no clock dependence.** Same inputs → same JSON output, byte for byte.
- **English → Tokenese is not implemented and not exposed.** This was explicitly de-scoped. The MCP service exposes decode + score only.

## 4. Machine output schema (`PairScore` 1.0)

`score_pair(english, tokenese, readback=None, live_anthropic=False)` returns:

```jsonc
{
  "schema_version": "1.0",
  "provenance": {
    "translator_version": "0.1.0",
    "schema_version": "1.0",
    "spec_sha256": "...",
    "design_sha256": "...",
    "intent_sha256": "...",
    "conformance_sha256": "...",
    "lexicon_sha256": "...",
    "grammar_target": "v0.2 (DESIGN.md §7) over v0.1 (spec.md)"
  },
  "english": {
    "text": "<verbatim>",
    "tokens": {
      "chars": int,
      "o200k": int | null,         // null if tiktoken not installed
      "o200k_method": "tiktoken" | "unavailable",
      "anthropic": int,
      "anthropic_method": "cached_costs+heuristic" | "live_api",
      "anthropic_unknown_atoms": [...]   // empty in pure-vocabulary text
    }
  },
  "tokenese": {
    "text": "<verbatim>",
    "tokens": { ... same shape ... },
    "decoded_english": ["<one line per input line>"]
  },
  "savings": {
    "anthropic_delta": int,        // english.anthropic - tokenese.anthropic (positive = tokenese wins)
    "anthropic_ratio": float,      // tokenese.anthropic / english.anthropic (lower = better)
    "o200k_delta": int | null,
    "o200k_ratio": float | null
  },
  "conformance": {
    "L1_lexicon": bool,
    "L2_grammar": bool,
    "L3_repair": bool,
    "session_issues": [...]
  },
  "misparse": {
    "by_family": { "binding": int, "scope": int, "sense": int, "triangulation": int },
    "hits": [
      { "family": "binding"|"scope"|"sense"|"triangulation",
        "code": "rebind"|"unbound_ref"|"drop_unbound"|"numeric_order"|"dist_on_imperative"|"too_many_holes"|"dist_too_wide"|"unknown_op"|"bad_evidential"|"bad_confidence"|"like_without_not"|"anchor_unconfirmed",
        "message": "...", "line_no": int, "raw": "..." }
    ]
  },
  "readback": null | {
    "verbatim_ratio": float,           // longest-common-substring / len(original)
    "edit_distance_norm": float,       // token-Levenshtein / max(len_a, len_b)
    "jaccard_token": float,
    "verdict": "verbatim" | "near_verbatim" | "transformed" | "unrelated"
  },
  "unparseable_lines": [
    { "line_no": int, "raw": "<verbatim>", "reason": "<explanation>" }
  ]
}
```

### Schema notes for `tk-ab-run`

- Stratify per-line by `misparse.hits[*].family` to get the binding/scope/sense/triangulation breakdown HANDOFF.md asks for.
- `savings.anthropic_ratio < 1` is the kill-criterion guard: if Tokenese is not winning on Anthropic-side cost, the construct under test is paying its own freight at best.
- `readback.verdict == "verbatim"` is a K4 failure regardless of content correctness.
- `unparseable_lines` is the parser's "I refuse to guess" surface. A non-empty list means the receiver should fall back to English for those lines.

## 5. Anthropic-side token method

**Default (offline, deterministic):** sum of cached per-symbol costs from `data/anthropic_costs.json` over a documented atom tokenization (digraphs + identifiers + numbers + sigils). Unknown atoms (content vocabulary) priced as `ceil(len/3)+1` and reported under `anthropic_unknown_atoms` so the harness can see how heuristic-heavy the count is. **No API key, no network, fully reproducible.**

**Opt-in (live API):** pass `live_anthropic=True` and set `ANTHROPIC_API_KEY`. Uses `anthropic.Anthropic().messages.count_tokens(model="claude-haiku-4-5", ...)`, matching the audit script in the repo. The result records `"anthropic_method": "live_api"` so mixed-mode runs are filterable.

**Recommendation for the A/B:** start with cached counts for the first sweep (deterministic, free), then re-run any rows that decided a hypothesis against the live API for confirmation.

## 6. Unparseable-input behavior

A line whose first field structurally cannot be an op (begins with a slot-internal sigil like `:`, `|`, `^` without being a digraph) is **never** rendered as a guessed English gloss. Instead it produces:

- An `Unparseable` AST node with a `reason` field.
- An English rendering of the form `[UNPARSEABLE: <reason>]  raw: '<verbatim>'`.
- An entry in `unparseable_lines` of the score payload.

Soft cases (unknown ops, unknown evidentials, malformed distributions) parse to a `Statement` with diagnostics attached — the renderer surfaces them, the validator counts them. The distinction: the parser refuses only when there is no honest reading at all.

## 7. Golden corpus

`golden/` ships ten labeled fixtures driven by `tests/test_golden.py`. Each `.tkn` file has a sibling `.expect.json` with predicted verdicts; readback-only fixtures live as standalone `.json` files.

| Fixture | Class | Tests |
|---|---|---|
| `01_canonical_deploy.tkn` | conformant | spec.md canonical example; both sides English↔Tokenese; tokenese.anthropic < english.anthropic |
| `02_v02_rich.tkn` | conformant | every v0.2 rich construct in one transcript |
| `03_binding_failures.tkn` | failing | `rebind`, `unbound_ref`, `drop_unbound` |
| `04_scope_failures.tkn` | failing | `dist_on_imperative`, `dist_too_wide`, `too_many_holes` |
| `05_sense_failures.tkn` | failing | `bad_evidential`, `unknown_op`, L1 fails |
| `06_triangulation_failures.tkn` | failing | `like_without_not`, `anchor_unconfirmed` |
| `07_unparseable.tkn` | refused | three structurally invalid lines → explicit UNPARSEABLE |
| `08_repair_pins_plain.tkn` | repair | three ?? on same topic → session pins plain |
| `09_readback_verbatim.json` | K4 fail | verbatim echo → verdict "verbatim" |
| `10_readback_transformed.json` | K4 pass | reordered paraphrase → verdict "transformed" |

Each `.expect.json` is the human-readable ground truth. To validate the oracle against the corpus:

```bash
cd tools/translator && python -m pytest tests/test_golden.py -v
```

All 10 golden fixtures pass against the current build (`59 passed in 0.39s` for the full suite: 16 unit + 33 grammar-coverage + 10 golden).

## 8. MCP service surface (final)

| Tool | Stateful | Purpose |
|---|---|---|
| `open_session()` | start | returns `session_id` |
| `close_session(session_id)` | end | |
| `to_english(session_id, text)` | yes | decode + update bindings, handshake, mode, repair history |
| `parse(text)` | no | AST as JSON |
| `validate(text)` | no | L1/L2/L3 conformance |
| `audit_lexicon_tool()` | no | re-derive C1 from bundled costs |
| `score_pair(english, tokenese, readback?, live_anthropic?)` | no | full `PairScore` 1.0 payload |
| `count_tokens(text, live_anthropic?)` | no | dual-tokenizer counts |
| `classify_misparse(text)` | no | misparse-family stratification only |
| `diff_readback(original, readback)` | no | K4 differ only |

## 9. Out of scope (explicit)

- English → Tokenese generation. The MCP service exposes scoring only.
- Frameset registry content (the *format* is honored; the *registry* is the maintainer's). Unknown ops surface as `sense.unknown_op` diagnostics, not L2 failures.
- Corpus-anchor gloss content. Anchors are flagged "awaiting gloss" and produce a `triangulation.anchor_unconfirmed` diagnostic until a gloss handshake is established. The translator refuses to invent gloss content (per spec, "unconfirmed anchors carry no load").
- Paraphrase readback **semantic correctness**. The differ scores transformation, not truth.

## 10. TKAB (Tokenese A/B mini-pilot scorer)

The `tkab` package provides `check_pair(...)` and the `tokenese-check`
CLI. It is the deterministic scorer for the W1+L1 mini-pilot. The
checker enforces R1.5 source-preservation, R5.3 report-don't-repair,
R5.4 derivation inadmissibility, R6.3 per-pair metrics, and R7
cross-repo boundary. Output schema: `tkab-check-1.1`. Outcomes are a
closed enumeration; see `tkab/AUDIT_CARD.md`.

The translator and checker support **grammar v0.3** (GRAMMAR-v0.3.md), an
additive, fully backward-compatible bump selected per-artifact by a
`^grammar:v0.3` header. v0.3 adds nine features: closed plain regions
(`^plain<<<`…`>>>^plain`, never graded); a declared conformance level
(`^declare:level=L`, verified against the achieved level); a four-way repair
sub-taxonomy (`repair-token`/`repair-statement`/`repair-handle`/`repair-explained`);
negation (`!@h`) and hedge (`@h?`) operators that compose freely; causal sigils
(`>>>` sequence, `*>>` stipulated-causation requiring source corroboration,
`?>>` hypothesized-causation); raw source quotes (`"""…"""`, matched verbatim
against the source); a centralized handle lexer (`handles.py`); grammar-version
dispatch (`^grammar:vX.Y`, unsupported versions refused); and line comments
(`#` at line start). Two outcomes are added — `fail-unsupported-causation` and
`fail-declared-level-mismatch` — and every v0.2 artifact scores identically.
