# Checker decision order

The TKAB checker assigns exactly one outcome per pair via a **first-match-wins**
decision order. From `tools/translator/tkab/AUDIT_CARD.md` (schema
`tkab-check-1.1`); v0.3 inserts steps 3.5 and 4.5. AUDIT_CARD.md is
authoritative if they ever diverge.

1. Any `unparseable_lines` → `fail-unparseable`. *(R5.3: report, don't repair.)*
2. `len(repair_events) >= 3` → `fail-three-repairs`. *(R5.2: 3-strike rule; the
   source becomes the record.)*
3. `source_authority_conflict` non-empty → `fail-source-authority-conflict`.
   *(R1.5 / R1.3: the source communication is authority; clone bindings are
   never decoded as ground truth.)*
4. (3.5) `unsupported_causation` non-empty → `fail-unsupported-causation`
   **(v0.3)**. *(A `*>>` stipulated causation needs source corroboration.)*
5. `misparse_family.hits` (dense lines only) non-empty → `fail-misparse`.
6. (4.5) `declared_level` set and `!= conformance_level` →
   `fail-declared-level-mismatch` **(v0.3)**.
7. `arm == "L1"` (expected-to-lose):
   - `plain` present and `dense_statement_count == 0` → `l1-plain-success`.
     *(R5.4: correct refusal.)*
   - `plain` present and `dense_statement_count > 0` → `fail-mixed-exit`.
   - derivation marker in any dense statement → `fail-illegal-derivation`.
     *(R5.4 forbids encoding inference in dense form.)*
   - otherwise → `fail-no-plain-exit`.
8. `arm == "W1"` (expected-to-win):
   - `conformance_level in {L2, L3}` and `readback_diff` empty →
     `win-conformant`.
   - `conformance_level == "L1"` → `fail-grammar`.
   - otherwise → `indeterminate`.
9. Default → `indeterminate`.

Cross-referenced spec rules: **R1.3** (source is authority), **R1.5** (source
preserved verbatim), **R5.2** (3-strike repair termination), **R5.3** (report,
don't repair), **R5.4** (no dense derivation; plain-exit refusal), **R6.3** (the
per-pair scoring contract), **R7** (cross-repo provenance boundary).

Derivation marker regex (case-insensitive), used in step 7:

```
(?:^|\b|\s)(?:because|therefore|since|so\s+that|thus|hence|implies?|
             ->\s*[a-zA-Z]+|=>\s*[a-zA-Z]+)\b
```
