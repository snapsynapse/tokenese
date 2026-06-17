"""TKAB pair checker for the PRD-027 W1+L1 mini-pilot.

This module wraps the deterministic translator with the per-pair scoring
contract from PRD-027 R6.3 and the W1/L1 mini-pilot rules from
tokenese-ab-suite.md.

Output schema (TKAB Check 1.0) is intentionally distinct from
``score_pair``'s PairScore 1.0 schema: it is the field set the harness
(``tk-ab-run``) consumes, with the source IDs, direction, author, artifact
type, source-authority semantics, and an outcome classifier.

Invariants enforced:

* The source communication is authority. Clone bindings are never decoded
  as ground truth. Mismatches are reported in ``source_authority_conflict``
  and the source text is preserved verbatim in the output.
* The checker does not generate or repair Tokenese. It only scores what
  the model already produced.
* Mismatches (misparses, unparseable lines, readback diffs, repair events)
  are reported, never silently fixed (PRD-027 R5.3).
* L1 expected-to-LOSE: ``plain`` exit is success when the source requires
  multi-step deadlock diagnosis. A syntactically conformant clone that
  encodes reasoning derivation is FAIL (PRD-027 R5.4).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from tokenese_translator.parser import (
    Binding,
    Comment,
    GrammarVersion,
    LevelDeclaration,
    ModeSwitch,
    PlainBlock,
    Repair,
    SourceQuote,
    Statement,
    Unparseable,
    detect_grammar,
    parse_transcript,
)
from tokenese_translator.score import score_pair

OUTPUT_SCHEMA_VERSION = "tkab-check-1.1"

# Causal-claim cue words for the `*>>` source-corroboration heuristic.
_CAUSAL_CUES = re.compile(
    r"(because|causes|caused\s+by|due\s+to|leads?\s+to|results?\s+in|->)",
    re.IGNORECASE,
)
_CORROBORATION_WINDOW = 80  # chars between the two labels and a cue word

# Lexical markers that indicate inference/derivation in dense form. Their
# presence in a non-plain clone for an expected-to-LOSE case means the model
# tried to compress reasoning, which PRD-027 R5.4 forbids.
_DERIVATION_MARKERS = re.compile(
    r"(?:^|\b|\s)(?:because|therefore|since|so\s+that|thus|hence|implies?|"
    r"->\s*[a-zA-Z]+|=>\s*[a-zA-Z]+)\b",
    re.IGNORECASE,
)


# Stable conformance-level string per CONFORMANCE.md ladder.
def _level(conf: Dict[str, Any]) -> str:
    if conf.get("L3_repair") and conf.get("L2_grammar") and conf.get("L1_lexicon"):
        return "L3"
    if conf.get("L2_grammar") and conf.get("L1_lexicon"):
        return "L2"
    if conf.get("L1_lexicon"):
        return "L1"
    return "L0"


def _nodes(tokenese: str):
    return parse_transcript(tokenese)


def _has_plain_mode(nodes) -> bool:
    """True when the clone enters plain English in any v0.3 or legacy form.

    v0.3 closed plain regions (``PlainBlock``) and the legacy one-way
    ``^mode:plain`` / ``plain`` toggle both count (brief Tier 1 #1)."""
    return any(
        isinstance(n, PlainBlock)
        or (isinstance(n, ModeSwitch) and n.mode == "plain")
        for n in nodes
    )


def _dense_statements(nodes) -> List[Statement]:
    """Statements outside any plain span (legacy toggle or closed block).

    ``PlainBlock`` content is captured raw and never produces statements, so
    it is excluded automatically; the legacy ``plain`` toggle is still honored
    for backward compatibility."""
    in_plain = False
    out: List[Statement] = []
    for n in nodes:
        if isinstance(n, ModeSwitch):
            in_plain = n.mode == "plain"
            continue
        if in_plain:
            continue
        if isinstance(n, Statement):
            out.append(n)
    return out


def _plain_line_numbers(nodes) -> set:
    """1-based line numbers inside a legacy ``plain`` mode region.

    Lines after a ``plain`` switch are natural English by design and are not
    scored for Tokenese conformance: misparse hits there are noise, not signal
    (the L1-arm refusal path depends on this — see PRD-027 R5.4). v0.3 closed
    plain regions never reach the misparse classifier (their content is a
    single ``PlainBlock`` node), so they need no line bookkeeping here."""
    in_plain = False
    out: set = set()
    for i, n in enumerate(nodes, start=1):
        if isinstance(n, ModeSwitch):
            in_plain = n.mode == "plain"
            continue
        if in_plain:
            out.add(i)
    return out


def _plain_blocks(nodes) -> List[Dict[str, Any]]:
    """Telemetry for v0.3 closed plain regions."""
    out: List[Dict[str, Any]] = []
    for n in nodes:
        if isinstance(n, PlainBlock):
            out.append(
                {
                    "start_line": n.start_line,
                    "end_line": n.end_line,
                    "byte_count": len(n.text.encode("utf-8")),
                }
            )
    return out


def _comment_lines(nodes) -> List[int]:
    return [n.line_no for n in nodes if isinstance(n, Comment)]


def _declared_level(nodes) -> Optional[str]:
    for n in nodes:
        if isinstance(n, LevelDeclaration):
            return n.level
    return None


def _english_label(handle: str) -> str:
    """Best-effort English label for a handle name (for source matching).

    Handles are typically kebab/snake identifiers (``billing-api``); the
    source prose uses the same words with separators normalized to spaces.
    """
    return re.sub(r"[-_]+", " ", handle.lstrip("@")).strip().lower()


def _causal_events(nodes, source_text: str) -> List[Dict[str, Any]]:
    """Extract v0.3 causal/sequence events and mark source corroboration.

    ``>>>`` (sequence) and ``?>>`` (hypothesized) are always admissible.
    ``*>>`` (stipulated) requires the source to corroborate the claim: both
    operands' English labels must appear within ``_CORROBORATION_WINDOW``
    characters of a causal cue word."""
    src_lower = source_text.lower()
    events: List[Dict[str, Any]] = []
    for i, n in enumerate(nodes, start=1):
        if not isinstance(n, Statement):
            continue
        for slot in n.slots:
            if slot.key not in (">>>", "*>>", "?>>"):
                continue
            left, right = slot.value if isinstance(slot.value, tuple) else ("", "")
            kind = {
                ">>>": "sequence",
                "*>>": "stipulated_causation",
                "?>>": "hypothesized_causation",
            }[slot.key]
            supported = True
            if slot.key == "*>>":
                supported = _source_corroborates(src_lower, left, right)
            events.append(
                {
                    "kind": kind,
                    "left": left,
                    "right": right,
                    "line_no": getattr(n, "_line_no", i),
                    "supported_by_source": supported,
                }
            )
    return events


def _source_corroborates(src_lower: str, left: str, right: str) -> bool:
    """Heuristic per brief Tier 2 #5: both labels near a causal cue word."""
    ll = _english_label(left)
    rl = _english_label(right)
    if not ll or not rl:
        return False
    for m in _CAUSAL_CUES.finditer(src_lower):
        lo = max(0, m.start() - _CORROBORATION_WINDOW)
        hi = min(len(src_lower), m.end() + _CORROBORATION_WINDOW)
        window = src_lower[lo:hi]
        if ll in window and rl in window:
            return True
    return False


def _looks_like_derivation(stmt: Statement) -> bool:
    """Heuristic: does this dense statement encode reasoning derivation?

    Triggered by causal/inferential operators (`because`, `therefore`, ...)
    in the op, target, or slot values, or by an op->op chain that implies
    inference rather than checkable state/parameters.
    """
    bag = [stmt.op or "", stmt.target or ""]
    for slot in stmt.slots:
        v = slot.value
        if isinstance(v, str):
            bag.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, tuple):
                    for sub in item:
                        if isinstance(sub, str):
                            bag.append(sub)
                elif isinstance(item, str):
                    bag.append(item)
    blob = " ".join(bag)
    return bool(_DERIVATION_MARKERS.search(blob))


def _repair_events(nodes) -> List[Dict[str, Any]]:
    """Repair events in the v0.3 schema shape: ``{kind, target, reason, line_no}``.

    The four-way taxonomy (``repair-token``/``repair-statement``/
    ``repair-handle``/``repair-explained``) is carried on the ``Repair`` node.
    The ``fail-three-repairs`` rule counts all kinds together, unchanged."""
    events: List[Dict[str, Any]] = []
    for i, n in enumerate(nodes, start=1):
        if isinstance(n, Repair):
            events.append(
                {
                    "kind": getattr(n, "repair_kind", "repair-statement"),
                    "target": n.target if n.target is not None else n.referent,
                    "reason": n.reason,
                    "line_no": n.line_no or i,
                }
            )
    return events


def _repair_kinds(repair_events: List[Dict[str, Any]]) -> Dict[str, int]:
    """By-kind aggregate, present even when zero (brief Tier 1 #3)."""
    counts = {
        "repair-token": 0,
        "repair-statement": 0,
        "repair-handle": 0,
        "repair-explained": 0,
    }
    for ev in repair_events:
        counts[ev["kind"]] = counts.get(ev["kind"], 0) + 1
    return counts


def _source_quote_conflicts(source_text: str, nodes) -> List[Dict[str, Any]]:
    """A clone ``SourceQuote`` whose text is absent from the source is a
    verbatim source-authority conflict (brief Tier 2 #6, case-insensitive
    substring)."""
    conflicts: List[Dict[str, Any]] = []
    src_lower = source_text.lower()
    for n in nodes:
        if not isinstance(n, SourceQuote):
            continue
        quote = n.text.strip()
        if quote and quote.lower() not in src_lower:
            conflicts.append(
                {
                    "type": "source_quote_not_in_source",
                    "clone_quote": quote,
                    "rule": "PRD-027 R1.5",
                    "resolution": "source wins; logged as A/B data",
                    "raw_quote": n.raw,
                }
            )
    return conflicts


def _unparseable_lines(nodes) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, n in enumerate(nodes, start=1):
        if isinstance(n, Unparseable):
            out.append({"line_no": i, "raw": n.raw, "reason": n.reason})
    return out


# ---- Source-authority conflict heuristic ----------------------------------
#
# Rule: if the clone binds @handle to a value whose token appears in the
# source under a DIFFERENT antonym/contrast partner, log a conflict. This is
# intentionally narrow: we do not try to understand the source. We only
# look for binding values where the source explicitly contradicts a token
# in the binding RHS.

_NEGATIONS = {
    "staging": ["production", "prod"],
    "production": ["staging", "dev", "test"],
    "prod": ["staging", "dev", "test"],
    "dev": ["staging", "production", "prod"],
    "test": ["staging", "production", "prod"],
    "enabled": ["disabled", "off"],
    "disabled": ["enabled", "on"],
    "on": ["off"],
    "off": ["on"],
    "true": ["false"],
    "false": ["true"],
}


def _source_authority_conflicts(source_text: str, nodes) -> List[Dict[str, Any]]:
    """Detect cases where the clone's binding/target token is contradicted
    by the source text. Heuristic and conservative; reports rather than
    repairs (PRD-027 R5.3)."""
    conflicts: List[Dict[str, Any]] = []
    src_lower = source_text.lower()
    src_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]*", src_lower))
    for n in nodes:
        if not isinstance(n, Binding):
            continue
        val_lower = n.value.lower()
        rhs_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]*", val_lower)
        for tok in rhs_tokens:
            if tok in _NEGATIONS:
                antonyms_in_source = [a for a in _NEGATIONS[tok] if a in src_words]
                if antonyms_in_source and tok not in src_words:
                    conflicts.append(
                        {
                            "type": "binding_value_contradicts_source",
                            "handle": n.handle,
                            "clone_value_token": tok,
                            "source_says": antonyms_in_source[0],
                            "rule": "PRD-027 R1.5",
                            "resolution": "source wins; logged as A/B data",
                            "raw_binding": n.raw,
                        }
                    )
    return conflicts


# ---- Outcome classifier ---------------------------------------------------

def _classify_outcome(
    pair: Dict[str, Any],
    conformance_level: str,
    plain_mode: bool,
    dense_stmts: List[Statement],
    unparseable: List[Dict[str, Any]],
    misparse_total: int,
    repair_events: List[Dict[str, Any]],
    source_conflicts: List[Dict[str, Any]],
    readback_diff: Any,
    unsupported_causation: List[Dict[str, Any]],
    declared_level: Optional[str],
) -> Tuple[str, List[str]]:
    """Return (outcome, notes). Outcomes are stable strings the harness can
    aggregate on. Decision order follows the PRD-027 W1+L1 ladder with the two
    v0.3 insertions (steps 3.5 and 4.5), first match wins. `arm` is the
    ab-suite arm label ("W1" | "L1")."""
    notes: List[str] = []
    arm = pair.get("arm", "")

    # 1. Unparseable input (no honest reading) -> fail-unparseable.
    if unparseable:
        notes.append(
            f"{len(unparseable)} unparseable line(s); reported, not repaired (R5.3)."
        )
        return "fail-unparseable", notes

    # 2. Three-?? rule (R5.2): three repairs -> terminate dense, source is record.
    if len(repair_events) >= 3:
        notes.append(
            "Three or more ?? events; per R5.2 the dense clone is terminated "
            "and source is the complete record."
        )
        return "fail-three-repairs", notes

    # 3. Source-authority conflict (R1.5): source wins, reported not repaired.
    if source_conflicts:
        notes.append(
            f"{len(source_conflicts)} source-authority conflict(s); source wins (R1.5)."
        )
        return "fail-source-authority-conflict", notes

    # 3.5 (v0.3). Stipulated causation `*>>` without source corroboration.
    if unsupported_causation:
        notes.append(
            f"{len(unsupported_causation)} stipulated `*>>` causation(s) lack source "
            "corroboration; source is authority (R1.5)."
        )
        return "fail-unsupported-causation", notes

    # 4. Misparse family hit.
    if misparse_total > 0:
        notes.append(
            f"{misparse_total} misparse hit(s) across families; see misparse_family detail."
        )
        return "fail-misparse", notes

    # 4.5 (v0.3). Declared conformance level must match the achieved level.
    if declared_level is not None and declared_level != conformance_level:
        notes.append(
            f"declared level {declared_level} != achieved level {conformance_level}."
        )
        return "fail-declared-level-mismatch", notes

    # 5. L1 arm: expected-to-LOSE. Plain exit is the correct outcome (R5.4).
    if arm == "L1":
        if plain_mode and len(dense_stmts) == 0:
            notes.append("Plain mode-switch with no dense reasoning; correct R5.4 refusal.")
            return "l1-plain-success", notes
        if plain_mode and len(dense_stmts) > 0:
            notes.append("Plain mode present but dense statements also present after it; mixed exit.")
            return "fail-mixed-exit", notes
        derivation_hits = [s for s in dense_stmts if _looks_like_derivation(s)]
        if derivation_hits:
            notes.append(
                f"{len(derivation_hits)} dense line(s) carry derivation markers (because/therefore/->); "
                "syntactically conformant but R5.4-illegal."
            )
            return "fail-illegal-derivation", notes
        notes.append("Expected plain exit, no `plain` mode switch present; R5.4 miss.")
        return "fail-no-plain-exit", notes

    # 6. W1 arm: expected-to-WIN.
    if arm == "W1":
        if conformance_level in ("L2", "L3") and not readback_diff:
            notes.append(f"Conformance {conformance_level}, no readback diff, no misparse.")
            return "win-conformant", notes
        if conformance_level == "L1":
            notes.append("L1 (lexicon-only) conformance; structural grammar checks did not pass.")
            return "fail-grammar", notes
        notes.append(f"Conformance {conformance_level}; W1 win conditions not met.")
        return "indeterminate", notes

    # 7. Default.
    notes.append(f"Conformance {conformance_level}; outcome did not match a typed rule.")
    return "indeterminate", notes


# ---- Provenance -----------------------------------------------------------

def _sha256sums() -> Dict[str, str]:
    """Parse data/source_provenance/SHA256SUMS.txt into {filename: sha}."""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    path = os.path.join(base, "source_provenance", "SHA256SUMS.txt")
    out: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    out[parts[1]] = parts[0]
    except Exception:
        pass
    return out


def checker_provenance(grammar_detected: str = "v0.2") -> Dict[str, Any]:
    """Provenance for the TKAB checker itself.

    Source-document SHAs come from the bundled SHA256SUMS.txt. PRD-027 and the
    ab-suite spec live in a separate repo (R7 boundary) and are not bundled
    here, so they read ``"unpinned"`` unless added to SHA256SUMS.txt.
    """
    sums = _sha256sums()

    def pinned(name: str) -> str:
        return sums.get(name, "unpinned")

    return {
        "checker_version": OUTPUT_SCHEMA_VERSION,
        "tkab_schema_version": OUTPUT_SCHEMA_VERSION,
        "grammar_version_supported": "v0.3",
        "grammar_version_detected": grammar_detected,
        "scorer": "perplexity-deterministic-checker",
        "spec_sha": pinned("spec.md"),
        "design_sha": pinned("DESIGN.md"),
        "conformance_sha": pinned("CONFORMANCE.md"),
        "intent_sha": pinned("INTENT.md"),
        "handoff_sha": pinned("HANDOFF.md"),
        "anthropic_costs_sha": pinned("anthropic_costs.json"),
        "prd_027_sha": pinned("PRD-027.md"),
        "ab_suite_sha": pinned("tokenese-ab-suite.md"),
    }


# ---- Public entry points --------------------------------------------------

def load_pair(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_pair(pair: Dict[str, Any], *, live_anthropic: bool = False) -> Dict[str, Any]:
    """Score a paired source/clone fixture per PRD-027 R6.3.

    The source text is preserved verbatim in the output. The Tokenese clone
    is scored but never treated as authoritative.
    """
    required = ["source_id", "direction", "source_text", "clone_text"]
    missing = [k for k in required if k not in pair]
    if missing:
        raise ValueError(f"pair missing required fields: {missing}")

    # pair_id and clone_id are conventions derivable from the harness fields.
    pair = dict(pair)
    pair.setdefault("clone_id", f"{pair['source_id']}.clone")
    pair.setdefault("pair_id", f"{pair['source_id']}.{pair.get('author', 'unknown')}")

    source_text = pair["source_text"]
    clone_text = pair["clone_text"]
    readback = pair.get("readback")

    inner = score_pair(source_text, clone_text, readback=readback, live_anthropic=live_anthropic)
    nodes = _nodes(clone_text)
    grammar_detected = detect_grammar(clone_text)

    plain_mode = _has_plain_mode(nodes)
    dense_stmts = _dense_statements(nodes)
    unparseable = _unparseable_lines(nodes)
    repair_events = _repair_events(nodes)
    repair_kinds = _repair_kinds(repair_events)

    # Source-authority conflicts come from two heuristics: binding-value
    # contradictions (v0.2) and verbatim source-quote mismatches (v0.3).
    source_conflicts = _source_authority_conflicts(source_text, nodes)
    source_conflicts += _source_quote_conflicts(source_text, nodes)

    # v0.3 causal/sequence events; `*>>` requires source corroboration.
    # Unsupported `*>>` is a distinct outcome (step 3.5), so it is kept OUT of
    # the source-authority conflict list (step 3) and classified on its own.
    causal_events = _causal_events(nodes, source_text)
    unsupported_causation = [
        e for e in causal_events
        if e["kind"] == "stipulated_causation" and not e["supported_by_source"]
    ]

    declared_level = _declared_level(nodes)
    plain_blocks = _plain_blocks(nodes)
    comment_lines = _comment_lines(nodes)

    # Misparse families are only scored on dense (non-plain) lines. Prose
    # after a `plain` switch is legitimate natural English, so hits there are
    # dropped before classification (keeps the L1 refusal path honest). v0.3
    # closed plain regions never reach the classifier (single PlainBlock node).
    plain_lines = _plain_line_numbers(nodes)
    dense_hits = [h for h in inner["misparse"]["hits"] if h["line_no"] not in plain_lines]
    misparse_by_family: Dict[str, int] = {"binding": 0, "scope": 0, "sense": 0, "triangulation": 0}
    for h in dense_hits:
        misparse_by_family[h["family"]] = misparse_by_family.get(h["family"], 0) + 1
    misparse = {"by_family": misparse_by_family, "hits": dense_hits}
    misparse_total = sum(misparse_by_family.values())

    readback_diff = inner["readback"]
    conformance_level = _level(inner["conformance"])
    outcome, notes = _classify_outcome(
        pair,
        conformance_level,
        plain_mode,
        dense_stmts,
        unparseable,
        misparse_total,
        repair_events,
        source_conflicts,
        readback_diff,
        unsupported_causation,
        declared_level,
    )

    en_tok = inner["english"]["tokens"]
    tk_tok = inner["tokenese"]["tokens"]
    token_counts = {
        "source": {
            "o200k": en_tok.get("o200k"),
            "o200k_method": en_tok.get("o200k_method"),
            "anthropic": en_tok.get("anthropic"),
            "anthropic_method": en_tok.get("anthropic_method"),
            "chars": en_tok.get("chars"),
        },
        "clone": {
            "o200k": tk_tok.get("o200k"),
            "o200k_method": tk_tok.get("o200k_method"),
            "anthropic": tk_tok.get("anthropic"),
            "anthropic_method": tk_tok.get("anthropic_method"),
            "chars": tk_tok.get("chars"),
        },
        "savings": inner["savings"],
    }

    misparse_family = {
        "by_family": misparse["by_family"],
        "hits": misparse["hits"],
    }

    out: Dict[str, Any] = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "source_id": pair["source_id"],
        "clone_id": pair["clone_id"],
        "pair_id": pair["pair_id"],
        "direction": pair["direction"],
        "author": pair.get("author"),
        "artifact_type": pair.get("artifact_type"),
        "scorer": pair.get("scorer", "perplexity-deterministic-checker"),
        "arm": pair.get("arm"),
        "predicted_outcome": pair.get("predicted_outcome"),
        "conformance_level": conformance_level,
        "conformance_detail": inner["conformance"],
        "token_counts": token_counts,
        "readback_diff": readback_diff,
        "repair_events": repair_events,
        "repair_kinds": repair_kinds,
        "misparse_family": misparse_family,
        "source_authority_conflict": source_conflicts,
        "unparseable_lines": unparseable,
        "plain_mode_present": plain_mode,
        "plain_blocks": plain_blocks,
        "dense_statement_count": len(dense_stmts),
        "declared_level": declared_level,
        "grammar_version": grammar_detected,
        "causal_events": causal_events,
        "unsupported_causation": unsupported_causation,
        "comment_lines": comment_lines,
        "outcome": outcome,
        "notes": notes,
        "decoded_clone_english": inner["tokenese"]["decoded_english"],
        "provenance": {**checker_provenance(grammar_detected), "score_pair": inner["provenance"]},
        "source_text": source_text,
        "clone_text": clone_text,
    }
    return out
