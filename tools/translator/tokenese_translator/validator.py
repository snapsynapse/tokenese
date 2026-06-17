"""Conformance validator. Reports L1 / L2 / L3 status per CONFORMANCE.md.

L1 Lexicon : every closed-vocabulary token used costs 1 (C1).
L2 Grammar : every line parses cleanly (no diagnostics) under the wire grammar.
L3 Repair  : the implementation honors `??`, `plain`, `dense`, and stops dense
             after three `??` on the same content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .lexicon import (
    ALL_OPS,
    CLOSED_VOCAB,
    COSTS,
    EVIDENTIALS,
    MODE_WORDS,
    RESERVED_SIGILS,
)
from .parser import (
    Binding,
    Handshake,
    ModeSwitch,
    Node,
    Repair,
    Statement,
    parse_line,
    parse_transcript,
)
from .session import Session


@dataclass
class LineReport:
    line_no: int
    raw: str
    l1_pass: bool = True
    l2_pass: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class TranscriptReport:
    l1_pass: bool
    l2_pass: bool
    l3_pass: bool
    line_reports: List[LineReport]
    session_issues: List[str]

    def to_dict(self) -> dict:
        return {
            "L1_lexicon": self.l1_pass,
            "L2_grammar": self.l2_pass,
            "L3_repair": self.l3_pass,
            "line_reports": [
                {
                    "line_no": lr.line_no,
                    "raw": lr.raw,
                    "L1": lr.l1_pass,
                    "L2": lr.l2_pass,
                    "issues": lr.issues,
                }
                for lr in self.line_reports
            ],
            "session_issues": self.session_issues,
        }


# Tokens we treat as audited 1-token even if not in COSTS keys (operators
# composed of audited atoms, etc.). Currently nothing extra; keep as a hook.
_GRAMMAR_PRIMITIVES = set(MODE_WORDS) | {"tokenese", "ok"} | set(ALL_OPS)


def _l1_check_word(token: str) -> bool:
    """Closed-vocabulary tokens must report cost 1 in COSTS.

    Content tokens (URLs, file paths, ad-hoc nouns) are not gated.
    """
    # Handle sigil-prefixed tokens (the prefix itself is what we check; the
    # tail is content vocabulary).
    if token in COSTS:
        return COSTS[token] == 1
    # Token like 'ev:obs' — composed; check the composed form first.
    if token in CLOSED_VOCAB:
        return True
    # Otherwise it is content vocabulary; not L1-gated.
    return True


def validate_line(line: str, line_no: int = 1) -> LineReport:
    node = parse_line(line)
    rpt = LineReport(line_no=line_no, raw=line.rstrip("\n"))

    # L2: parser diagnostics carry the L2 failures.
    diags = getattr(node, "diagnostics", []) or []
    if diags:
        # 'unknown op' is informational, not a grammar failure.
        hard = [d for d in diags if "not in audited closed vocabulary" not in d]
        soft = [d for d in diags if "not in audited closed vocabulary" in d]
        if hard:
            rpt.l2_pass = False
        rpt.issues.extend(hard + soft)

    # Per-slot L2 diagnostics
    if isinstance(node, Statement):
        for s in node.slots:
            for d in s.diagnostics or []:
                rpt.issues.append(d)
                rpt.l2_pass = False

    # L1: scan tokens that should be in CLOSED_VOCAB.
    if isinstance(node, Statement):
        # op (without ?/! suffix) — already stripped
        if not _l1_check_word(node.op):
            rpt.l1_pass = False
            rpt.issues.append(f"L1: op '{node.op}' fails 1-token audit")
        for s in node.slots:
            # Evidential surfaces must be one of the four audited.
            if s.key == "ev" and s.raw not in EVIDENTIALS:
                rpt.l1_pass = False
                rpt.issues.append(f"L1: evidential '{s.raw}' not in audited set")

    return rpt


def validate_transcript(text: str) -> TranscriptReport:
    """Run a full conformance pass. Mutates a local Session for L3."""
    session = Session()
    line_reports: List[LineReport] = []
    l1, l2 = True, True

    for i, raw_line in enumerate(text.splitlines(), start=1):
        lr = validate_line(raw_line, line_no=i)
        l1 = l1 and lr.l1_pass
        l2 = l2 and lr.l2_pass
        line_reports.append(lr)

        # Drive session forward for L3 checking.
        node = parse_line(raw_line)
        if isinstance(node, Handshake):
            if node.role == "probe":
                session.on_probe(node.version)
            else:
                session.on_ack(node.version)
        elif isinstance(node, ModeSwitch):
            session.on_mode(node.mode)
        elif isinstance(node, Binding):
            err = session.bind(node.handle, node.value)
            if err:
                session.diagnostics.append(err)
            session.remember_statement(node.raw)
        elif isinstance(node, Repair):
            session.on_repair(node.referent)
        elif isinstance(node, Statement):
            session.remember_statement(node.raw)

    # L3: did the session honor mode-pinning after three repairs?
    # Pass criterion: every (topic, count>=3) record has pinned_plain==True.
    l3 = all(
        rec.pinned_plain or rec.count < 3
        for rec in session.repair_history.values()
    )

    return TranscriptReport(
        l1_pass=l1,
        l2_pass=l2,
        l3_pass=l3,
        line_reports=line_reports,
        session_issues=session.diagnostics,
    )


def audit_lexicon() -> dict:
    """Re-derive C1 from the bundled audit data. Pure, deterministic.

    Returns a structured report: every entry in COSTS is reported with its
    cost and whether it is admitted to the closed function vocabulary.
    """
    admitted = []
    rejected = []
    for tok, cost in COSTS.items():
        entry = {"token": tok, "anthropic_cost": cost}
        if cost == 1:
            admitted.append(entry)
        else:
            rejected.append(entry)
    return {
        "C1_definition": "Closed function vocabulary must cost 1 token worst-case in every audited tokenizer.",
        "source": "data/anthropic_costs.json",
        "admitted_count": len(admitted),
        "rejected_count": len(rejected),
        "admitted": admitted,
        "rejected": rejected,
    }
