# Worklog — Tokenese (Phase B Turnfile coordination)

References:
- `HANDOFF.md` (Tokenese repo)
- `/Users/snap/Git/turnfile/SPEC.md` (Turnfile v1 contract)
- `/Users/snap/Git/turnfile/docs/MINIMUM_VIABLE_TURNFILE.md`

Each session appends one block. Use the close protocol from `/Users/snap/Git/turnfile/docs/MINIMUM_VIABLE_TURNFILE.md`. Cross-repo boundary: this WORKLOG records Tokenese Phase B coordination; Tokenese semantics live in `/Users/snap/Git/tokenese/SPEC.md`, `DESIGN.md`, etc., and are NOT edited from Turnfile coordination per PRD-027 R7.

Claude (Opus 4.7): SESSION 1 OPEN at rev 1 (SIG-001). First Tokenese Turnfile session. Maintainer initiated Phase B from the Turnfile repo session 29 chat (2026-06-23 directive: "Tokenese has a handoff document. Phase A is done. Phase B requires Turnfile."). Initialized via `node /Users/snap/Git/turnfile/tools/turnfile.mjs init --project tokenese-phase-b --maintainer snap --agent claude --root /Users/snap/Git/tokenese`. Registered two tasks: t1-phase-b-open-baseline-verify (in_progress, Claude-owned, P1) and t2-multi-family-ab-suite-design (pending, depends on t1).

Claude (Opus 4.7): t1 BASELINE VERIFICATION COMPLETE at rev 1. Per Tokenese HANDOFF.md Next work item 1 ("Keep N2 open until live multi-family A/B artifacts are attached and reproducible"), verified Phase A v0.3.9 baseline reproducibility before introducing live multi-family A/B variability.

Verification commands and results:

- `cd tools/translator && ../../.venv/bin/python -m pytest -q`
  - **156 passed in 0.94s** (matches HANDOFF.md verification-run line: "156 passed")
  - Baseline test suite stable on the v0.3.9 tag commit

- `.venv/bin/tokenese-n2-report --format markdown`
  - Status: `static-package-ready/live-ab-open` (N2 still open as intended — live A/B work begins this session)
  - Static gates: compression_counts_available ✓, compression_expectations_pass ✓, hypothesis_counts_available ✓, tkab_fixture_count=10, receiver_static_term_floor_pass ✓
  - Hypothesis counts: 18 cases / 18 fair-baseline comparisons / 13 o200k wins / 4 losses / 1 break-even
  - Receiver static floor: threshold 0.75, **minimum score 0.85**, **average score 0.9298**, cases below threshold: **none**
  - TKAB outcomes: 7 conformant-or-pass / 5 fail (1 each: declared-level-mismatch, illegal-derivation, source-authority-conflict, unparseable, unsupported-causation); 2 l1-plain-success; 3 win-conformant

Conclusion: v0.3.9 baseline is reproducible. The static receiver floor still clears the 0.75 threshold by a comfortable margin (min 0.85). Phase B may proceed to t2 (live multi-family A/B suite design) without retroactive baseline correction.

t1 marked done; t2 unblocked. Codex (and a third independent model family per HANDOFF.md item 2) to be invited into the session for the A/B runs.

Carry-forward for next Tokenese session:
- t2 task awaiting design + claim
- Tokenese constraints from HANDOFF.md remain binding: no English-to-Tokenese generation; report mismatches without silent repair; compression claims vs terse/equal-precision English; do not mutate `tools/translator/data/source_provenance/*`
- Cross-repo boundary preserved: no edits to Tokenese semantics from Turnfile coordination per PRD-027 R7
- Evidence for `~/Git/turnfile` PRD-047 Test 1 lands at `~/Git/turnfile/working-session/docs/v1-cross-repo-test-tokenese-2026-06-23.md`

Claude (Opus 4.7): SESSION 2 OPEN at rev 3 (SIG-003). Continued Phase B work — claimed t2-multi-family-ab-suite-design. Produced strawman suite design at working-session/docs/phase-b-suite-design-strawman.md addressing HANDOFF.md "Next work" items 2-4. Strawman covers: S1 task classes (deploy-status / code-diff review / spec-amendment / apply-or-counter / dense-loses), S2 per-class fixture count (3 instances × 2 encodings × 3 families = 72 paired exchanges min), S3 per-exchange logging schema with misparse-family tracking (binding/scope/sense/triangulation), S4 compression-claim discipline per HANDOFF constraint (compare against terse, not verbose English), S5 dense-loses preservation, S6 third-family options (Gemini Flash recommended for first pass; alternatives: local Qwen / GPT-4o; Claude-Haiku rejected as insufficient independence), S7 per-family run protocol, S8 exit-to-production threshold deferred to Maintainer + first-pass baseline data per PRD-027 R6.5. Four open questions routed for Maintainer + Codex decision: OQ-PhaseB-1 third-family pick, OQ-PhaseB-2 new fixture authorship, OQ-PhaseB-3 numeric thresholds (commit now or wait for baseline), OQ-PhaseB-4 concurrent vs sequential runs. Cross-repo evidence in ~/Git/turnfile being updated to reflect t2 in-progress status. No Tokenese semantics modified per PRD-027 R7 boundary.
