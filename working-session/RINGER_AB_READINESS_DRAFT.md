# Ringer A/B Readiness Assessment (DRAFT, private R&D)

Date: 2026-07-03
Scope: read-only reconnaissance of `~/Git/tokenese` for the planned English-vs-Tokenese token-consumption A/B run through a swarm orchestrator that logs per-attempt token usage per engine.
Status: draft, not committed, not for distribution.

## Verdict

READY-WITH-CAVEATS. The measurement and validation infrastructure is genuinely strong (deterministic checker, TKAB scorer, N2 static report, 7-column tokenizer audit, a suite design with maintainer answers already inline). What does not exist is the experiment corpus: there is no ready-to-run set of paired English/Tokenese task prompts, and encoding is hand-authored by design. The one thing that would flip this to READY: a validated, committed paired fixture set covering the strawman's S1-S5 task classes with mechanical check scripts.

## 1. Repo state and maturity

- Version: v0.3.9 (tagged, released 2026-06-23). Grammar v0.3 (additive over v0.2, opt-in via `^grammar:v0.3` header). Spec v0.3 dated 2026-06-17.
- Last commit: `03a912a` 2026-06-25 "working session update". Two uncommitted modifications in `working-session/` only (TURNFILE.yaml, the Phase B strawman with maintainer OQ answers added in bold). Core repo tree is clean.
- What exists:
  - Spec surface: `spec.md` v0.3, `GRAMMAR-v0.3.md`, `DESIGN.md` (10 sections incl. the ratified precision-pivot direction), `INTENT.md` (7 invariants), `CONFORMANCE.md`.
  - Tooling: `tools/translator/` Python package. Parser, renderer, validator (L1/L2/L3), session state, MCP server (parse / validate / validate_framesets / to_english / check_pair / score_pair), `tokenese-translate` CLI, `tokenese-check` TKAB per-pair scorer, `tokenese-n2-report` static package report, `compression_eval` and `receiver_eval` harnesses. 156 translator tests + 7 repo-root audit-surface tests, all passing per the 2026-06-23 handoff and re-verified 2026-06-23 in the Phase B Turnfile session (WORKLOG).
  - Lexicon audit: `audit_*.py` across 7 tokenizer columns + `audit_check_intersection.py` CI gate.
  - Fixtures: 10 TKAB pair fixtures (`tools/translator/tkab/fixtures/`), 18 hypothesis eval cases, receiver cases (static floor min 0.85 vs 0.75 threshold).
  - Skill bundle: `skills/tokenese/` v1.0.1 (SKILL.md, audit card, install guide, 5 examples, hash-pinned via MANIFEST + CI drift guard).
  - Governance: RELEASE_CHECKLIST, provenance-pin policy, GuideCheck Level 4 live with DNS-anchor drift CI, hosted page at tokenese.org.
- Phase state: Phase A closed at v0.3.9. Phase B (live multi-family A/B) opened 2026-06-23 under Turnfile coordination; task t2 (suite design) is in_progress and stalled since ~2026-06-25 awaiting Codex apply-or-counter and fixture authorship.
- Maturity read: unusually well-governed for a v0.3.x spec repo. The gap is not rigor, it is corpus and live-run artifacts. ROADMAP N2 (this exact experiment) is the single "Now" item and the repo's self-declared kill-criterion.

## 2. Encoding capability today

- By tooling: NO. The reference translator is Tokenese-to-English only. English-to-Tokenese generation is explicitly de-scoped by maintainer decision, restated as a hard constraint in HANDOFF.md ("Do not add English-to-Tokenese generation") and in the skill bundle ("ships no generator... scoring-only scope lock").
- By documented manual procedure: YES. The intended path is hand-authoring against grammar v0.3 (spec.md wire grammar + GRAMMAR-v0.3.md delta + DESIGN.md section 7 sigil namespace + section 10 recommended forms), then deterministic validation via `validate` / `tokenese-check`. `skills/tokenese/examples/encode_decode.md` documents the round-trip workflow explicitly: author by hand, decode with `tokenese-translate` to check your reading, score with the checker.
- What is missing: nothing structural for the manual path, but each Tokenese-arm prompt for the A/B is bespoke authoring plus validation work. Also note the ban is on adding a generator to the toolchain; a model hand-authoring the dense arm during fixture creation (then checker-validating) is the established pattern (Codex was nominated as fixture author, strawman OQ-PhaseB-2, maintainer agreed).

## 3. Lexicon coverage for coding-task instructions

- Audited single-token core: 22 ASCII sigils, 12 digraphs, 9 brackets, 6 Unicode survivors, 30 core words (`do go if or and not yes no ok ask say get put run fix new old big all none true false done fail need want must may can will`). `anthropic_costs.json` carries 201 audited entries, 137 at cost 1, including 84 word entries (adds `after before because report set sync head tail fill drop hold quote cite src via per what when where who why how` etc.).
- Escape valve: spec.md explicitly allows any common English word as a content token ("prefer short, frequent words... When in doubt, audit"), and paths/URLs/ISO dates are bare literals. So "read file X, write a summary to Y, format as Z" IS expressible today, e.g. via `get <path>` / `put <path>` plus content tokens.
- Gaps for the coding-task register:
  - No audited ops for read, write, list, search, create, delete, summarize, format, test, build, review, diff, merge. `get`/`put`/`run`/`fix`/`set` stretch to cover some, but "summarize" and "format as Z" need unaudited content tokens whose per-tokenizer cost is unmeasured.
  - Frameset registry (`framesets.json`, report-only) covers only 5 ops: deploy, get, run, set, fix. Nothing for file I/O or text-production tasks.
  - The known tokenizer killers are exactly what coding prompts want: dotted handles (`@svc.logs.first-error` = 5 tokens), file paths, and kebab compounds (`edge-fn` = 3 tokens). Repeated-referent amortization via `@N` bindings is the designed answer; the 2026-06-18 handoff flags multi-turn reuse economics as measured-unknown ("do not assume").
- Net: coverage is adequate to author the arm, insufficient to author it well without per-prompt token measurement of the content vocabulary chosen.

## 4. The "tokenizer-audited" claim

- What exists: per-symbol worst-case cost (bare and space-prefixed) across 7 columns: OpenAI o200k_base, Anthropic count-tokens (claude-haiku-4-5), Gemini gemini-2.5-flash (REST count-tokens), Qwen2.5-7B, DeepSeek-V3, Llama-3-8B, Gemma 4 E4B native (`mlx-community/gemma-4-e4b-it-4bit`, the PAICE on-device production runtime). Reproducible via `audit_*.py` + `audit_check_intersection.py`; CI-gated against stale artifacts and silent alphabet expansion (INTENT invariant 5, shrink-only).
- Staleness: 6 columns audited 2026-06-17, Gemma 4 column 2026-06-18. About two weeks old as of today; low drift risk since tokenizers change only on model swaps. The Gemini column is the weak one: API-gated, rides on a single 2026-06-17 run, no CI re-derivation (ROADMAP X6 open).
- The important limitation for this experiment: the audit is per-symbol only. Whole-message token measurement (`compression_eval.py` / `token_count.py`) covers ONLY o200k_base and cl100k_base, both OpenAI tiktoken. No whole-message counts exist for Anthropic, Gemini, Qwen, DeepSeek, Llama, or Gemma. The N2 report's "13 wins / 4 losses / 1 break-even" is o200k-only. The swarm orchestrator's per-engine token logging is precisely the missing cross-tokenizer whole-message instrument, which is why this experiment is worth running and also why no prior cross-tokenizer compression claim should be assumed.

## 5. Known validity risks (from the repo's own docs)

- The compression premise re-examination (LocalBrain `1_Projects/PAICE.work PBC/tokenese/HANDOFF 2026-06-18 Tokenese compression premise re-examination.md`, folded into spec.md and INTENT.md). The flagship example reversed on measurement (English 36 vs Tokenese 47 on o200k); most apparent savings were terseness, not language design; designed sigil clusters and dotted handles tokenize worst; the surviving honest win is ~20-25 percent on structured/conditional payloads with single-token operators. Consequence: the English arm MUST be terse, equal-precision English (HANDOFF.md hard constraint; strawman S4). If the English arm is normal verbose agent prompts, any Tokenese "win" is confounded and the repo's own rules disqualify the result.
- Precision-pivot framing (INTENT "Retained compression goal and precision-pivot", DESIGN section 10): the project's current honest position is precision-preserving interlingua with regime-dependent compression. A flat-content task suite is predicted to break even at best; expected wins concentrate in multi-referent binding, evidence/confidence channels, ranked alternatives, and repair state. Suite composition determines the headline.
- Not-a-pidgin (invariant 3): acquisition cost is traded for precision. Worker models must be taught Tokenese in-context; the teaching payload (SKILL.md or a sigil key) rides in the Tokenese arm's prompt tokens unless amortized or cached. An A/B that omits teaching overhead from accounting overstates Tokenese; one that includes it per-attempt on short tasks will likely bury it. The accounting policy must be pre-declared.
- Kill-criterion is misparse-retry rate (invariant 6): if retries eat the savings, the spec says the design failed. The orchestrator's one-retry-with-failure-injection maps onto this but caps observable retry depth at 1; `??` repair events inside a run also need capturing per the strawman S3 schema (misparse family: binding/scope/sense/triangulation).
- Receiver comprehension floor is static, not live: the 0.85 receiver floor is a deterministic static score, and the cross-model receiver gate (OQ#6) passed on Claude, Gemini, and Codex, i.e. frontier-class models. Cheap swarm workers are a different population; live comprehension by that class is unmeasured. HANDOFF also requires dense-loses cases preserved in the suite (strawman S5).
- Doc drift that could poison the Tokenese arm: `skills/tokenese/examples/encode_decode.md` example 1 still presents the debunked hero example with the false "~55 vs ~22 tokens" framing and the exact syntax (dotted handles, `!@svc.ok?`, `*>>` clusters) the 2026-06-18 measurement showed tokenizes worst; SKILL.md frontmatter still advertises "2.5-4x compression", which spec.md marks under review. If the skill bundle is used to teach the encoding model, it teaches the anti-patterns. Author the arm from DESIGN section 10's recommended forms instead.
- Judgment authority: task success is judged from the English source authority, never the Tokenese form (PRD-027 R5.4). Identical mechanical pass/fail checks on both arms satisfies this cleanly; keep check scripts byte-identical across arms.

## 6. Minimum work plan to A/B-readiness

Ordered; estimates assume one competent agent session per step.

1. Ratify and commit Phase B decisions (0.5-1 h). The strawman already carries maintainer answers inline (third family: local Qwen preferred, Gemini Flash fallback; thresholds: wait for baseline; runs: concurrent; fixtures: Codex authors). Commit the working-session changes so the design is on record before data collection.
2. Pre-register the measurement protocol (1-2 h). Write down, before any run: terse-English baseline rule, teaching-overhead accounting policy for the Tokenese arm, per-attempt fields to harvest from the orchestrator log (engine, model version, prompt/completion tokens, attempt number, pass/fail), and the win definition (token delta at equal pass rate). This is the cheapest insurance against the 2026-06-18 failure mode recurring.
3. Author the paired prompt corpus (6-10 h; the long pole). 4-5 task classes x 3 instances per strawman S1/S2: terse English form + hand-authored grammar-v0.3 Tokenese form, every dense form validated with `validate` and `tokenese-check`, dense-loses class included. Only the deploy-status class has existing fixtures; code-diff review, spec-amendment, apply-or-counter, and free-text rationale are all new.
4. Write mechanical check scripts (3-4 h). One shell check per instance, exit 0 = pass, identical for both arms, aligned to the orchestrator's exit-code verification.
5. Build the run manifests and verify logging (2-3 h, gated on harness access). Confirm per-attempt token fields and per-task engine routing actually appear in the JSONL; adapt if the early-access format diverges.
6. Pilot run + harvest (2-4 h). One family end-to-end, parse the log into the S3 schema, regenerate `tokenese-n2-report` with live artifacts attached, then fan out to the remaining families.

Total: roughly 15-24 h. Single biggest blocker inside this repo: no paired prompt corpus exists and cannot be generated by tooling (encoder deliberately absent), so step 3 is unavoidable manual authoring plus validation. (External gate, tracked elsewhere: confirmed access to the orchestrator and its per-attempt token fields.)

## 7. Verdict line

READY-WITH-CAVEATS. A committed, checker-validated paired fixture set for the S1-S5 task classes (with byte-identical mechanical checks) is the one thing that would change it to READY.
