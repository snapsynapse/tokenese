# Boot File — Codex (v1)

Read this first on session start. It tells you what this project is, where things are, what state we're in, and what to do next.

## What is this project?

Tokenese: a token-native interlingua for LLM-to-LLM communication, designed to be more compressed AND more precise than natural language. You (Codex) and Claude are the first two speakers. The owner's framing: LLMs conforming to human language is like watching film in black and white; Tokenese is an attempt to bring color to machine-to-machine communication.

You are a peer in this work, not an executor. Turnfile norms apply: you propose, counter-propose, and disagree openly; the human maintainer (Sam) arbitrates; every decision lands in plain markdown.

Hard constraints already locked (do not relitigate without a counter-proposal in the MAILBOX):
- Token-space only. Plain text on the wire. No embeddings, no latents (security + portability).
- Lexicon admissibility = 1 token worst case (bare AND space-prefixed) in BOTH o200k_base and Anthropic's tokenizer. Audit scripts in repo root; results in `../anthropic_costs.json`.
- Not a pidgin: precision is never traded for compression.
- Human-auditable: hard invariant. A human with the one-page audit card must be able to follow any transcript.
- Kill-criterion: misparse-retry rate. If repair eats the savings, the design fails and we say so.

## Directory layout

- `../spec.md` — Tokenese spec v0.1.0 (grammar, sigils, handshake, repair)
- `../DESIGN.md` — design position: 3 transmission mechanisms, keeps/discards, sigil namespace, v0.2 queue. Where spec and DESIGN disagree, DESIGN wins until spec v0.2.
- `../INTENT.md` — 7 design invariants
- `../CONFORMANCE.md` — L1-L4 conformance ladder
- `../audit_symbols.py`, `../audit_anthropic.py` — tokenizer audit harness
- `working-session/` — active workspace (this folder): `TURNFILE.yaml` coordination state, `WORKLOG.md` session log, `MAILBOX.md` message queue, `OPEN_QUESTIONS.md` question registry, `chat-codex.md` your scratchpad (create on first use)

## Protocol essentials

- Mailbox check first and last: check `MAILBOX.md` at start and end of every turn; your unread must be 0 before your turn ends.
- Message lifecycle: `unread -> acknowledged -> blocked -> actioned -> closed`.
- Payload-first: review requests include inline content, never path-only references.
- TURNFILE.yaml: claim tasks by setting owner + claim_rev; bump `coordination.revision` on every edit.
- The `??` repair signal and `plain` escape hatch from spec.md apply to OUR exchanges once we start speaking Tokenese: if you cannot parse a dense statement, reply `??` rather than guessing. Repair events are data, not failures.

## Resumption read order

1. This file
2. `TURNFILE.yaml` — coordination state
3. `WORKLOG.md` status block (top lines)
4. `MAILBOX.md` inbox snapshot — you have unread
5. `OPEN_QUESTIONS.md` Active section
6. `../spec.md` then `../DESIGN.md` (first session: read fully)

## Current state

### Phase 1 (teach) — NOT STARTED
- teach-tokenese: Claude teaches you Tokenese in English. Contract: you finish able to PRODUCE valid statements, including novel recombinations never shown as examples. Teaching token cost is logged as data.
- ab-suite-design: next, co-design the A/B suite (operational/code tasks, dense vs English, both directions). Bring tasks where you predict dense mode LOSES; they belong in the suite.

### Mailbox
- 1 unread for you: MSG-20260612-001 (welcome + teaching contract).

### Coordination
- TURNFILE.yaml revision: 1. Active phase: phase-1-teach.

## Session close protocol

1. Check mailbox, unread=0
2. Update WORKLOG status block + session entry with handoff block
3. Close mailbox messages you own
4. Update TURNFILE.yaml (status, tasks, revision)
5. Write session snapshot to bottom of `chat-codex.md`
6. Update this boot file's Current state section (archive prior version header to v<N+1>)
