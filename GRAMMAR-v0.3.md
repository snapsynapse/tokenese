# Tokenese Grammar v0.3

Version: 0.3.0
Date: 2026-06-17
Status: additive minor bump over v0.2 (DESIGN.md §7). Fully backward compatible.

This is a delta document. It lists every addition in v0.3, the surface syntax,
the AST node the parser produces, the admissibility rule the checker applies
(if any), and a one-line backward-compatibility statement. Nothing in v0.2 is
removed or changed; v0.3 features activate only when an artifact opens with
`^grammar:v0.3`.

## Dispatch: `^grammar:vX.Y`

- **Surface:** `^grammar:v0.3` as the first non-comment line of the artifact.
- **AST:** `GrammarVersion(version="v0.3")`.
- **Rule:** if absent, the parser assumes `v0.2` and every v0.3 sigil below is
  an unknown token (parsed exactly as v0.2 would — typically `Unparseable`). If
  the declared version is unsupported (e.g. `^grammar:v9.9`), the parser emits
  a single `Unparseable("unsupported grammar version: v9.9")` and refuses the
  artifact.
- **Backward compat:** v0.2 artifacts carry no `^grammar` line and are
  unaffected.

## 1. Closed plain regions

- **Surface:** `^plain<<<` on its own line, then any text, then `>>>^plain`.
- **AST:** `PlainBlock(text, start_line, end_line)` — content captured raw,
  byte-for-byte.
- **Rule:** plain regions are never scanned for misparse-family hits or graded
  for grammar conformance. `plain_mode_present` is true when at least one
  `PlainBlock` exists. The dense statement count, derivation markers, and
  misparse hits are computed only over non-plain spans.
- **Backward compat:** the legacy one-way `plain` mode toggle still works and
  still opens an implicit plain region to EOF or the next `dense`.

## 2. Declarative level

- **Surface:** `^declare:level=L2` (one of `L0|L1|L2|L3`).
- **AST:** `LevelDeclaration(level)`.
- **Rule:** may appear once, only as the first non-comment statement (position
  enforced by the parser — a late declaration becomes `Unparseable`). The
  checker compares the declared level against the achieved conformance level;
  a mismatch yields `fail-declared-level-mismatch`.
- **Backward compat:** absent declaration ⇒ no new outcome is possible; scoring
  is identical to v0.2.

## 3. Repair sub-taxonomy

- **Surface / AST:**
  | Surface | `repair_kind` |
  |---|---|
  | `??` (whole line) | `repair-statement` |
  | `??@handle` / `?? @handle` | `repair-handle` (`target=@handle`) |
  | `??: <reason>` | `repair-explained` (`reason=<reason>`) |
  | `?? <token>` | `repair-token` (`target=<token>`) |
- **Rule:** the `fail-three-repairs` rule counts all four kinds together;
  threshold (`>= 3`) and counting are unchanged. Output adds a `repair_kinds`
  by-kind aggregate (present even when zero).
- **Backward compat:** a bare `??` still classifies and counts as before.

## 4. Negation and hedge operators

- **Surface:** `!@handle` (negation prefix), `@handle?` (hedge suffix),
  `!@handle?` (composition).
- **AST:** `Negated(handle)`, `Hedged(handle)`, `Negated(inner=Hedged(...))`.
- **Rule:** none beyond rendering — "not h", "possibly h", "possibly not h".
  Neither operator changes the canonical handle name.
- **Backward compat:** `!` is only a negation prefix when an `@` immediately
  follows; otherwise it keeps its v0.2 imperative/priority meaning. A trailing
  `?` on a non-handle keeps its v0.2 query meaning.

## 5. Causal sigil operators

- **Surface / AST:**
  | Surface | AST | Admissibility |
  |---|---|---|
  | `left >>> right` | `Sequence` | always |
  | `left *>> right` | `StipulatedCausation` | requires source corroboration |
  | `left ?>> right` | `HypothesizedCausation` | always |
- **Rule:** `*>>` is admissible only when the source corroborates the link —
  both operands' English labels appear within 80 characters of a causal cue
  (`because|causes|caused by|due to|leads to|results in|->`). Otherwise the
  outcome is `fail-unsupported-causation`. These appear in output as
  `causal_events` with a `supported_by_source` flag.
- **Backward compat:** v0.2 has no causal sigils; the bare `>>` flow token is
  unchanged and is not one of these three-character sigils. The
  `fail-illegal-derivation` regex matches `->`, which none of `>>>`/`*>>`/`?>>`
  contain, so they do not false-positive.

## 6. Raw source quotes

- **Surface:** `"""raw text"""` (triple-quote delimited, may span lines, no
  escaping; the closer is the next `"""`).
- **AST:** `SourceQuote(text)` — verbatim contents.
- **Rule:** a `SourceQuote` is a verbatim source claim. If its text is not a
  case-insensitive substring of `source_text`, it contributes a
  `source_authority_conflict` (`fail-source-authority-conflict`).
- **Backward compat:** v0.2 has no triple-quote form; ordinary double-quote
  content is unaffected.

## 7. Centralized handle lexer

- **Module:** `tokenese_translator/handles.py`, `consume_handle(text, start)`.
- **Rule:** single source of truth for the handle charset (alphanumerics plus
  `_` and `-`; both snake_case and kebab-case) and the optional `!`/`?`
  decorations. `parser.py`, `renderer.py`, and `misparse.py` all delegate to
  it.
- **Backward compat:** the canonical handle name is unchanged from v0.2; this
  is a refactor with no surface change.

## 8. Line comments

- **Surface:** `#` at line start (after optional whitespace), running to EOL.
- **AST:** `Comment(text, line_no)`.
- **Rule:** comments contribute nothing to scoring — no misparse, no statement
  count, no repair count — and do not count as the "first non-comment
  statement" for `^declare:level` position enforcement. Reported as
  `comment_lines` (telemetry only).
- **Backward compat:** inline `#` (not at line start) keeps its v0.2 tag-slot
  meaning; only a leading `#` is a comment.

## Schema and outcomes

The per-pair checker schema bumps `tkab-check-1.0` → `tkab-check-1.1`, adding
`declared_level`, `grammar_version`, `repair_kinds`, `plain_blocks`,
`causal_events`, `unsupported_causation`, and `comment_lines`. Two new outcomes
join the closed enum: `fail-unsupported-causation` (decision step 3.5) and
`fail-declared-level-mismatch` (step 4.5). See `tools/translator/tkab/AUDIT_CARD.md`.
