# TKAB Audit Card — `tkab-check-1.1`

The `tkab` package is the **deterministic per-pair scorer** for the PRD-027
W1+L1 mini-pilot. It consumes paired `(source, clone)` fixtures produced by the
A/B harness and emits one JSON result per pair. It is a **scorer, not a
generator or a repairer**: it reports what a model already produced and never
edits the clone or the source.

## Measurement identity

`scorer = "perplexity-deterministic-checker"`.

The arms generate; the checker scores. Claude and Codex author Tokenese clones;
this checker (run by Perplexity in the pilot) assigns a deterministic outcome.
No model is invoked in the score path — same input, same JSON, byte for byte.

## Schema version

`schema_version = "tkab-check-1.1"`. The 1.1 bump is additive: every 1.0 field
is preserved with unchanged meaning, plus the v0.3 fields listed below. v0.2
artifacts (no `^grammar:v0.3`) score identically; only the schema string and
the new always-present fields differ.

### Output fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | str | always `"tkab-check-1.1"` |
| `source_id` | str | e.g. `"TKAB-W1"` |
| `clone_id` | str | e.g. `"TKAB-W1.claude.codex.v1"` |
| `pair_id` | str | convention `f"{source_id}.{author}"` |
| `direction` | str | `"claude->codex"` \| `"codex->claude"` |
| `author` | str | who produced the clone |
| `artifact_type` | str | `"deploy-status"` \| `"deadlock-debug"` \| … |
| `scorer` | str | `"perplexity-deterministic-checker"` |
| `arm` | str | `"W1"` (expected-win) \| `"L1"` (expected-lose) |
| `predicted_outcome` | str | `"win"` \| `"lose"` (arm prediction) |
| `conformance_level` | str | `"L0"`\|`"L1"`\|`"L2"`\|`"L3"` |
| `conformance_detail` | dict | `{L1_lexicon, L2_grammar, L3_repair, session_issues}` |
| `token_counts` | dict | `{source, clone, savings}` (o200k + anthropic) |
| `readback_diff` | null\|dict | K4 diff vs source, when a readback is supplied |
| `repair_events` | list | `{kind, target, reason, line_no}` per `??`; 3+ ⇒ `fail-three-repairs` |
| `repair_kinds` | dict | by-kind aggregate `{repair-token, repair-statement, repair-handle, repair-explained}`, present even when zero (v0.3) |
| `misparse_family` | dict | `{by_family, hits}` over **dense** lines only |
| `source_authority_conflict` | list | `{handle, clone_value_token, source_says, …}` and v0.3 `source_quote_not_in_source` entries |
| `unparseable_lines` | list | `{line_no, raw, reason}` |
| `plain_mode_present` | bool | a `plain` toggle or a closed `^plain<<<` block appeared |
| `plain_blocks` | list | closed plain regions `{start_line, end_line, byte_count}` (v0.3) |
| `dense_statement_count` | int | dense statements outside plain regions |
| `declared_level` | str\|null | `^declare:level=L` value, or null (v0.3) |
| `grammar_version` | str | detected artifact grammar `"v0.2"`\|`"v0.3"` (v0.3) |
| `causal_events` | list | `{kind, left, right, line_no, supported_by_source}` (v0.3) |
| `unsupported_causation` | list | uncorroborated `*>>` events ⇒ `fail-unsupported-causation` (v0.3) |
| `comment_lines` | list[int] | `#` comment line numbers, telemetry only (v0.3) |
| `frameset_validation` | dict | report-only registry/canonical-form diagnostics; does not affect outcome |
| `outcome` | str | one of the closed enumeration below |
| `notes` | list[str] | human-readable rationale for the outcome |
| `decoded_clone_english` | list[str] | best-effort English rendering of the clone |
| `provenance` | dict | checker provenance (see below) |
| `source_text` | str | **verbatim** source (R1.5) |
| `clone_text` | str | **verbatim** clone |

Misparse hits are scored on dense lines only. Lines inside a `plain` region are
natural English by design and are not graded for Tokenese conformance.

## Outcome enumeration (closed)

| Outcome | One-line rationale |
|---|---|
| `win-conformant` | W1 arm: L2/L3 conformance, no readback diff, no misparse — the dense clone wins. |
| `l1-plain-success` | L1 arm: model switched to `plain` with no dense reasoning — correct R5.4 refusal. |
| `fail-unparseable` | Clone has a line with no honest reading; reported not repaired (R5.3). |
| `fail-source-authority-conflict` | A clone binding or source quote contradicts the source; source is authority (R1.5). |
| `fail-unsupported-causation` | A `*>>` stipulated causation is not corroborated by the source (v0.3). |
| `fail-illegal-derivation` | L1 arm: dense statement encodes inference (`because`/`therefore`/`->`); R5.4 forbids it. |
| `fail-three-repairs` | ≥3 `??` events; per R5.2 the dense clone is terminated, source is the record. |
| `fail-grammar` | W1 arm: only L1 (lexicon) conformance; structural grammar checks failed. |
| `fail-misparse` | One or more misparse-family hits on dense lines. |
| `fail-no-plain-exit` | L1 arm: no `plain` switch and no derivation marker; expected refusal missed. |
| `fail-mixed-exit` | L1 arm: `plain` switch present but dense statements also present. |
| `fail-declared-level-mismatch` | `^declare:level=L` disagrees with the achieved conformance level (v0.3). |
| `indeterminate` | No typed rule matched (e.g. W1 conformance neither L2/L3 nor L1). |

## Decision order (first match wins; v0.3 inserts steps 3.5 and 4.5)

1. Any `unparseable_lines` → `fail-unparseable`.
2. `len(repair_events) >= 3` → `fail-three-repairs`.
3. `source_authority_conflict` non-empty → `fail-source-authority-conflict`.
3.5. `unsupported_causation` non-empty → `fail-unsupported-causation` **(v0.3)**.
4. `misparse_family.hits` (dense) non-empty → `fail-misparse`.
4.5. `declared_level` set and `!= conformance_level` → `fail-declared-level-mismatch` **(v0.3)**.
5. `arm == "L1"`:
   - `plain` present and `dense_statement_count == 0` → `l1-plain-success`.
   - `plain` present and `dense_statement_count > 0` → `fail-mixed-exit`.
   - derivation marker in any dense statement → `fail-illegal-derivation`.
   - otherwise → `fail-no-plain-exit`.
6. `arm == "W1"`:
   - `conformance_level in {L2, L3}` and `readback_diff` empty → `win-conformant`.
   - `conformance_level == "L1"` → `fail-grammar`.
   - otherwise → `indeterminate`.
7. Default → `indeterminate`.

Derivation marker regex (case-insensitive):

    (?:^|\b|\s)(?:because|therefore|since|so\s+that|thus|hence|implies?|
                 ->\s*[a-zA-Z]+|=>\s*[a-zA-Z]+)\b

## Source authority rule (R1.3 / R1.5)

The source communication is the authority. Clone bindings are never decoded as
ground truth. When a clone binding value contradicts a token in the source
(e.g. clone binds `@env := /production` while the source says `staging`), the
mismatch is logged in `source_authority_conflict` and the source text is
preserved **verbatim** in the output. The checker reports the conflict; it does
not rewrite the clone to match the source (R5.3, report-don't-repair).

## Provenance fields

`provenance` carries the checker identity and the SHAs of the pinned source
documents (from `data/source_provenance/SHA256SUMS.txt`):

- `checker_version` / `tkab_schema_version` — `"tkab-check-1.1"`
- `grammar_version_supported` — `"v0.3"`; `grammar_version_detected` — per-artifact
- `scorer` — `"perplexity-deterministic-checker"`
- `spec_sha`, `design_sha`, `conformance_sha`, `intent_sha`, `handoff_sha`,
  `anthropic_costs_sha` — pinned source SHAs
- `prd_027_sha`, `ab_suite_sha` — `"unpinned"` unless the documents are added
  to `data/source_provenance/` (they live in a separate repo per the R7
  cross-repo boundary)
- `score_pair` — the nested PairScore 1.0 provenance from the base translator

## Backward compatibility (v0.2 artifacts)

A v0.2 artifact carries no `^grammar:v0.3` line. It is parsed under v0.2
semantics and scored exactly as in `tkab-check-1.0`: the same conformance
level, the same outcome, the same misparse/repair/conflict logic. Only the
schema string (`1.1`) and the new always-present fields (`repair_kinds`,
`plain_blocks`, `declared_level=null`, `grammar_version="v0.2"`,
`causal_events=[]`, `unsupported_causation=[]`, `comment_lines=[]`) differ. The
two new outcomes can only fire on v0.3 artifacts.

Frameset validation is also backward compatible: it is report-only telemetry.
Diagnostics may appear for registered ops in v0.2 or v0.3 artifacts, but they
do not participate in the decision order and never change `outcome`.

## Scope locks honored

- No Tokenese generation, no English→Tokenese.
- No clone repair: mismatches are reported, never silently fixed (R5.3).
- Source text preserved verbatim (R1.5).
- No Turnfile governance participation.
