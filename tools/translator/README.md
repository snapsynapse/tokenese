# Tokenese Translator (Tokenese → English)

A deterministic, script-based translator from Tokenese to English. **No LLMs, no network, no external assets at runtime.** All grammar and lexicon rules are encoded as plain Python against the spec.

- Spec target: **v0.2** (DESIGN.md governs where it differs from spec.md v0.1)
- Direction: **Tokenese → English only** (English → Tokenese is out of scope by design)
- Session-scoped: handles (`@cfg=...`), handshake state, repair history, and mode (`dense`/`plain`) persist per session
- Conformance: parser reports **L1 (lexicon)** and **L2 (grammar)** for each input; **L3 (repair)** is reported across a session transcript

## What it preserves

The renderer honors DESIGN.md §3 "rich" channels rather than smoothing them away:

| Tokenese | English rendering |
|---|---|
| `^7` | "(confidence 7/9)" |
| `ev:obs` / `ev:heard` / `ev:mem` / `ev:guess` | "(observed)" / "(reported by another party)" / "(from memory)" / "(working assumption)"; elided = "(inferred)" |
| `cause:oom^6\|disk^3` | "cause: OOM (rank 1) or disk (rank 2)" |
| `??slot` | "[repair requested on slot in plain English]" |
| `□date` | "[unfilled date]" |
| `†two-generals` | "[corpus anchor: two-generals — awaiting gloss]" |
| `like throttle not retry` | "like throttle, not retry" |

A faithful English rendering preserves epistemic structure even when it sounds less natural. This is invariant 4 (accuracy is a feature) and 7 (human-auditable) from INTENT.md.

## Install

```bash
cd tools/translator
pip install -e .            # core translator + CLI
pip install -e .[mcp,dev]   # MCP server + test deps
```

## CLI usage

```bash
echo '@1=supabase edge fn deploy
get? @1 status
if fail -> get logs first-error +time' | tokenese-translate

# Or against a file:
tokenese-translate transcript.tkn
```

Output is one English line per Tokenese statement, in input order, with a session-level conformance summary at the end (sent to stderr unless `--quiet`).

## MCP service

```bash
tokenese-mcp   # stdio transport
```

Tools exposed:

| Tool | Purpose |
|---|---|
| `open_session()` | start a new translator session; returns `session_id` |
| `close_session(session_id)` | drop session state |
| `to_english(session_id, text)` | translate; updates session bindings, handshake, repair history |
| `parse(text)` | stateless parse to AST (JSON) |
| `validate(text)` | stateless conformance check; returns L1/L2/L3 pass/fail + diagnostics |
| `validate_framesets(text)` | report-only typed frameset/canonical slot-order diagnostics |
| `audit_lexicon()` | re-run C1 against the bundled audit data; returns pass/fail per element |

## tokenese-check (TKAB scorer)

`tokenese-check` is the deterministic per-pair scorer for the TKAB
mini-pilot (PRD-027 §W1+L1). It consumes JSON pair files produced by the
A/B harness and emits per-pair JSON results conformant to schema
`tkab-check-1.1`.

    tokenese-check --pair tkab/fixtures/TKAB-W1.pair.json --pretty
    tokenese-check --batch tkab/fixtures/ --out results/

The checker does not generate or repair Tokenese. It reports
misparses, repair events, source-authority conflicts, and outcome
according to PRD-027 R5.3/R5.4 and R6.3. Outcomes are a closed
enumeration documented in `tkab/AUDIT_CARD.md`.

## Grammar v0.3

The translator and checker support grammar **v0.3** — an additive, fully
backward-compatible bump over v0.2. An artifact opts in with a `^grammar:v0.3`
header on its first non-comment line; without it the artifact is parsed and
scored exactly as v0.2 (the 71 v0.2 tests pass unchanged).

v0.3 adds: closed plain regions (`^plain<<<` … `>>>^plain`), a declared
conformance level (`^declare:level=L2`), a four-way repair sub-taxonomy,
negation (`!@h`) and hedge (`@h?`) operators, causal sigils (`>>>` sequence,
`*>>` stipulated causation, `?>>` hypothesized causation), raw source quotes
(`"""…"""`), a centralized handle lexer, grammar-version dispatch, and line
comments (`#`). The checker schema bumps to `tkab-check-1.1` and gains two
outcomes (`fail-unsupported-causation`, `fail-declared-level-mismatch`). See
[`GRAMMAR-v0.3.md`](../../GRAMMAR-v0.3.md) for the full delta.

## Frameset registry

`framesets.json` is an experimental, report-only controlled-vocabulary registry
for common op shapes. Each registered op carries a typed slot signature such as
`deploy :: who what to:env when:date -> status`, plus machine-readable
positional and slot metadata. The validator reports missing required slots,
extra positional args, noncanonical registered-slot order, and unregistered
slots for registered ops.

This is deliberately not a grammar gate in v0.3.x. Unknown content ops remain
legal, and frameset diagnostics do not change parser acceptance, conformance
level, or TKAB outcome. They are telemetry for the A/B harness and a staging
point for the roadmap X3 registry work.

## Architecture

```
tokenese_translator/
  lexicon.py     # closed vocabulary, derived from data/anthropic_costs.json (cost==1)
  lexer.py       # split a Tokenese line into raw tokens
  parser.py      # AST: Statement(op, target, slots[], comment) + Binding + Handshake + Repair + Mode
  session.py     # symbol table, handshake state, mode, repair history
  renderer.py    # AST -> English, preserving epistemic channels
  validator.py   # L1/L2/L3 conformance
  cli.py
  mcp_server.py
```

## Conformance

Run `pytest` from `tools/translator/`. The suite includes:

- C1 audit re-derivation from `data/anthropic_costs.json` (round-trips the lexicon)
- Grammar examples from `spec.md` (handshake, symbol table, `if fail ->`, etc.)
- v0.2 examples from `DESIGN.md` (`@cfg` handles, `??slot` repair, distribution slots, `□` holes, `†` anchors, `ev:` evidentials, `^N` confidence, `!` readback flag, `like X not Y`)
- Repair sequence (three `??` on the same content → mode-pinned plain)

## Out of scope (and why)

- English → Tokenese: explicitly de-scoped by the maintainer.
- Frameset registry (DESIGN.md §3 K5): the registry *format* is spec-defined but the registry contents are session-collaborative; the validator reports unknown ops as warnings, not errors, since a session may register vocabulary live.
- Corpus-anchor gloss content (`†two-generals` → schema): the renderer surfaces the anchor token and a "awaiting gloss" marker. Per spec, an unconfirmed anchor "carries no load," so we refuse to invent a gloss.
- Paraphrase readback semantics: we render the `!` marker and the receiver's expected `√` reply as English, but we do not verify that a `√` reply is a valid paraphrase (that requires a model).
