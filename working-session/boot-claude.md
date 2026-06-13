# Boot File — Claude (v1)

Read this first on session start.

## What is this project?

Tokenese: token-native interlingua, Claude + Codex as first speakers. You (Claude) authored spec v0.1.0 and DESIGN.md in the 2026-06-12 bootstrap session and scaffolded this workspace. Full context: `../spec.md`, `../DESIGN.md`, `../INTENT.md`.

Role this session: teacher first, peer always. Turnfile norms: Codex counter-proposals are first-class; do not steamroll. Sam arbitrates.

## Protocol essentials

Same as boot-codex.md: mailbox first/last, payload-first, TURNFILE.yaml revision bumps, `??` repair events are data.

## Resumption read order

1. This file
2. `TURNFILE.yaml`
3. `WORKLOG.md` status block
4. `MAILBOX.md` inbox snapshot
5. `OPEN_QUESTIONS.md` Active
6. `../DESIGN.md` section 9 (admission queue + measurement plan)

## Current state

### Phase 1 (teach) — NOT STARTED
- teach-tokenese (P0, yours): teach Codex in English. Contract: Codex must PRODUCE valid statements including novel recombinations. Log teaching token cost in WORKLOG.
- Teaching material order: spec.md grammar + sigil table, DESIGN.md sigil namespace (section 7) overrides v0.1 where they differ, then worked examples, then production exercises with addressable repair.
- ab-suite-design (P0, yours to draft, Codex to counter): operational/code exchanges only (Sam, 2026-06-12). Suite MUST include: novel recombinations (cold-start guard), tasks where dense mode is predicted to lose, both communication directions, stratified misparse logging by construct family, calibration probes for ^N and ev: channels.

### Reminders from DESIGN.md
- Never compress derivation (R1): dense for state/reference, prose for reasoning.
- Self-reported channels (^N, ev:) untrusted-by-default until calibration-audit passes.
- Sigil namespace is locked (DESIGN.md section 7); one sigil, one meaning.

### Mailbox
- MSG-20260612-001 posted to Codex (welcome + teaching contract). You own closure.

### Coordination
- TURNFILE.yaml revision: 1. Tasks: teach-tokenese (claim it at session start), ab-suite-design, ab-run, calibration-audit, spec-v02-draft.

## Session close protocol

Standard Turnfile close: mailbox zero, WORKLOG handoff block, TURNFILE update, snapshot to `chat-claude.md`, boot file refresh.
