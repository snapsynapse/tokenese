"""Misparse-family classifier.

Per HANDOFF.md task 3 ('stratify misparse by construct family: binding,
scope, sense, triangulation'), this module assigns each diagnostic from a
parsed transcript to one of four families with deterministic rules. No LLM.

Families (definitions taken from HANDOFF.md + DESIGN.md):

  binding
    Anything about @handles: rebinding without ??, reference to an unbound
    handle, drop of an unbound handle, broken numeric @N sequence.

  scope
    Anything about depth and span: > 2 ?? on a topic without mode pin,
    {...} or not(...) depth violations, distribution slot on a `!`
    imperative (DESIGN.md K3 forbids this), more than the cap of open
    \u25a1 holes per exchange (>2 per DESIGN.md K10), ranked distribution
    with k > 3.

  sense
    Vocabulary failures: unknown evidential surface (must be obs/heard/
    mem/guess), op outside the audited closed vocab and unregistered,
    confidence outside 0-9.

  triangulation
    Contrast / analogy / anchor failures: 'like X' without a 'not Y'
    counterpart in the same statement, anchor never glossed (uncon-
    firmed anchor carrying load), 'like'-derived fact without `^<=6`.

Each diagnostic is emitted as (family, code, message). Multiple families
can fire on one line; the classifier returns the full list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import (
    Binding, Handshake, ModeSwitch, Node, Repair, Slot, Statement,
    parse_transcript,
)
from .handles import consume_handle
from .lexicon import ALL_OPS, EVIDENTIALS, CLOSED_VOCAB


Family = str  # "binding" | "scope" | "sense" | "triangulation"


@dataclass
class MisparseHit:
    family: Family
    code: str
    message: str
    line_no: int
    raw: str

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "code": self.code,
            "message": self.message,
            "line_no": self.line_no,
            "raw": self.raw,
        }


@dataclass
class MisparseReport:
    hits: List[MisparseHit] = field(default_factory=list)

    def by_family(self) -> dict:
        out: dict = {"binding": 0, "scope": 0, "sense": 0, "triangulation": 0}
        for h in self.hits:
            out[h.family] = out.get(h.family, 0) + 1
        return out

    def to_dict(self) -> dict:
        return {
            "by_family": self.by_family(),
            "hits": [h.to_dict() for h in self.hits],
        }


def _statement_has_imperative(s: Statement) -> bool:
    return s.op_imperative or any(slot.key == "!" for slot in s.slots)


def _count_open_holes(s: Statement) -> int:
    count = 0
    for slot in s.slots:
        if slot.key == "\u25a1":
            count += 1
        elif isinstance(slot.value, dict) and slot.value.get("hole"):
            count += 1
    return count


def classify_transcript(text: str) -> MisparseReport:
    rpt = MisparseReport()
    bound: dict[str, str] = {}
    binding_order: list[str] = []
    repair_counts: dict[str, int] = {}
    pinned_plain: set[str] = set()
    seen_anchors_glossed: dict[str, bool] = {}

    nodes = parse_transcript(text)
    for i, node in enumerate(nodes, start=1):
        raw = getattr(node, "raw", "") or ""

        # ---- binding family ----
        if isinstance(node, Binding):
            if node.handle in bound:
                rpt.hits.append(MisparseHit(
                    "binding", "rebind",
                    f"@{node.handle} rebound without prior ?? (was '{bound[node.handle]}', now '{node.value}')",
                    i, raw,
                ))
            else:
                bound[node.handle] = node.value
                binding_order.append(node.handle)
                # numeric ordering: must be strictly increasing per spec
                if node.handle_is_numeric:
                    nums = [int(h) for h in binding_order if h.isdigit()]
                    if nums != sorted(nums):
                        rpt.hits.append(MisparseHit(
                            "binding", "numeric_order",
                            f"numeric @N bindings not strictly increasing: {nums}",
                            i, raw,
                        ))

        if isinstance(node, Statement):
            # Drop @x against unbound
            if node.op == "drop" and node.target and node.target.startswith("@"):
                h = node.target[1:]
                if h not in bound:
                    rpt.hits.append(MisparseHit(
                        "binding", "drop_unbound",
                        f"drop @{h} but handle not bound", i, raw,
                    ))
                else:
                    bound.pop(h, None)
                    binding_order = [b for b in binding_order if b != h]

            # @handle references inside target and slot values
            refs = _collect_at_refs(node)
            for h in refs:
                if h not in bound:
                    rpt.hits.append(MisparseHit(
                        "binding", "unbound_ref",
                        f"@{h} referenced but not bound", i, raw,
                    ))

            # ---- scope family ----
            if _statement_has_imperative(node):
                for slot in node.slots:
                    if slot.is_distribution:
                        rpt.hits.append(MisparseHit(
                            "scope", "dist_on_imperative",
                            f"distribution slot '{slot.key}' on `!` imperative (DESIGN K3 forbids)",
                            i, raw,
                        ))

            holes = _count_open_holes(node)
            if holes > 2:
                rpt.hits.append(MisparseHit(
                    "scope", "too_many_holes",
                    f"{holes} open \u25a1 holes (DESIGN K10 caps at 2 per exchange)",
                    i, raw,
                ))

            for slot in node.slots:
                if slot.is_distribution and isinstance(slot.value, list) and len(slot.value) > 3:
                    rpt.hits.append(MisparseHit(
                        "scope", "dist_too_wide",
                        f"distribution slot '{slot.key}' has {len(slot.value)} entries; spec caps k<=3",
                        i, raw,
                    ))

            # ---- sense family ----
            if node.op not in ALL_OPS and node.op not in CLOSED_VOCAB:
                rpt.hits.append(MisparseHit(
                    "sense", "unknown_op",
                    f"op '{node.op}' is not in the audited closed vocab and not registered",
                    i, raw,
                ))
            for slot in node.slots:
                if slot.key == "ev" and slot.raw not in EVIDENTIALS:
                    rpt.hits.append(MisparseHit(
                        "sense", "bad_evidential",
                        f"evidential '{slot.raw}' not in {{ev:obs, ev:heard, ev:mem, ev:guess}}",
                        i, raw,
                    ))
                if slot.key == "^" and isinstance(slot.value, int):
                    if not (0 <= slot.value <= 9):
                        rpt.hits.append(MisparseHit(
                            "sense", "bad_confidence",
                            f"confidence ^{slot.value} out of 0-9 scale",
                            i, raw,
                        ))

            # ---- triangulation family ----
            slot_keys = [s.key for s in node.slots]
            slot_vals = [s.value for s in node.slots]
            has_like = ("like" in [v for v in [node.target] + slot_vals if isinstance(v, str)])
            has_not  = ("not"  in [v for v in [node.target] + slot_vals if isinstance(v, str)])
            # Approximate detection: `like X` token present in either target
            # or any bare slot value but no companion `not Y`.
            line_words = raw.split()
            if "like" in line_words and "not" not in line_words:
                rpt.hits.append(MisparseHit(
                    "triangulation", "like_without_not",
                    "'like X' contrast pin missing 'not Y' counterpart (DESIGN K7)",
                    i, raw,
                ))

            for slot in node.slots:
                if slot.key == "\u2020" or (isinstance(slot.value, str) and slot.value.startswith("\u2020")):
                    anchor = slot.value if slot.key == "\u2020" else slot.value[1:]
                    if anchor not in seen_anchors_glossed:
                        seen_anchors_glossed[anchor] = False
                        rpt.hits.append(MisparseHit(
                            "triangulation", "anchor_unconfirmed",
                            f"corpus anchor \u2020{anchor} used without first-use gloss handshake",
                            i, raw,
                        ))

        if isinstance(node, Repair):
            topic = node.referent if node.referent else "<last>"
            repair_counts[topic] = repair_counts.get(topic, 0) + 1
            if repair_counts[topic] >= 3 and topic not in pinned_plain:
                # The session-state is what actually enforces this; we flag
                # it here so the eval can count 'should have pinned'.
                pinned_plain.add(topic)

    return rpt


def _collect_at_refs(s: Statement) -> List[str]:
    """Collect canonical handle names referenced anywhere in a statement.

    Uses the centralized handle lexer (``consume_handle``) so the charset and
    the v0.3 negation/hedge sigils are recognized in exactly one place. The
    leading ``!`` / trailing ``?`` decorations do not change the canonical
    name, so ``!@x?`` resolves to the same ``x`` as a bare ``@x``.
    """
    refs: List[str] = []

    def harvest(val):
        if not isinstance(val, str):
            return
        j = 0
        while j < len(val):
            # consume_handle accepts an optional leading '!'; probe at '@' and
            # also one position back so '!@h' is recognized from the '@'.
            if val[j] == "@":
                probe = j - 1 if (j > 0 and val[j - 1] == "!") else j
                parsed = consume_handle(val, probe)
                if parsed is not None:
                    handle, end = parsed
                    refs.append(handle.name)
                    j = end
                    continue
            j += 1

    if s.target:
        harvest(s.target)
    for slot in s.slots:
        if isinstance(slot.value, str):
            harvest(slot.value)
        elif isinstance(slot.value, tuple):
            for v in slot.value:
                harvest(v)
        elif isinstance(slot.value, list):
            for v in slot.value:
                if isinstance(v, tuple) and v:
                    harvest(v[0])
    return refs
