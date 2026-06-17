"""Tokenese parser. Produces an AST per line; transcripts are a list of ASTs.

Grammar implemented (spec.md v0.1 + DESIGN.md v0.2 deltas):

  line       := empty | comment-only | handshake | mode-switch | repair
              | binding | statement
  handshake  := 'tokenese?' 'v:' VER          (probe)
              | 'tokenese' 'ok' 'v:' VER      (ack)
  mode-switch:= 'dense' | 'plain'
  repair     := '??' [referent]                (referent: @handle, †anchor,
                                                 ::type, :slotname, or quoted)
  binding    := '@' NAME '=' VALUE...          (NAME: integer or noun)
  statement  := OP [TARGET] (SLOT)*  [tail]
  OP         := word, optionally with '?' or '!' suffix
  TARGET     := bare value (the patient/target)
  SLOT       := KEY ':' VALUE_OR_DISTRIBUTION
              | '#' TAG
              | '^' DIGIT                       (confidence on the statement)
              | 'ev:' EVIDENTIAL                (special-case slot)
              | '::' TYPE                       (type/scope qualifier)
              | 'like' X 'not' Y                (contrast pin, multi-field)
              | '->' VALUE                      (sequence/yield)
              | '=>' VALUE                      (implication)
              | '|' VALUE                       (alternative in op chain)
              | '!' (bare)                       (priority on a slot)
              | '~' VALUE                       (approximate marker before val)
              | '??' SLOT_REF                   (intra-statement repair)
              | '†' ANCHOR                      (corpus anchor reference)
              | '□' [TYPE]                       (typed hole)
              | bare value                      (additional target / arg)

  VALUE_OR_DISTRIBUTION
              := VALUE                          (plain literal/@ref/etc)
              | VALUE ('^' DIGIT)? ('|' VALUE ('^' DIGIT)?){1,2}   (k<=3 distribution)

We are LIBERAL on the parser side and STRICT on the validator side: the
parser will attach diagnostics rather than refuse to parse, so a non-conformant
line still produces an AST the renderer can show with a warning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .lexer import LexResult, lex
from .lexicon import (
    ALL_OPS,
    EVIDENTIALS,
    HANDSHAKE_ACK,
    HANDSHAKE_PROBE,
    HANDSHAKE_VERSION_KEY,
    MODE_WORDS,
    REPAIR_TOKEN,
    CLOSED_VOCAB,
)


# ---------- AST node types ----------

@dataclass
class Slot:
    """A keyed slot, possibly with a distribution value."""
    key: str                              # e.g. 'cause', 'status', 'when', 'ev', '#', '^', '::', '->', '=>', 'like', '□', '†', '~', '!'
    raw: str                              # raw field as it appeared
    value: Any = None                     # parsed value or list of (val, rank) for distributions
    is_distribution: bool = False
    is_approx: bool = False
    confidence: Optional[int] = None      # ^N attached to value
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class Statement:
    op: str
    op_query: bool = False                # op had '?' suffix
    op_imperative: bool = False           # op had '!' suffix (also triggers readback)
    target: Optional[str] = None          # first bare value after op
    slots: List[Slot] = field(default_factory=list)
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "statement"


@dataclass
class Binding:
    handle: str                           # 'cfg' for @cfg=..., '1' for @1=...
    handle_is_numeric: bool = False
    value: str = ""                       # right-hand side, raw
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "binding"


@dataclass
class Handshake:
    role: str                             # 'probe' or 'ack'
    version: Optional[str] = None
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "handshake"


@dataclass
class Repair:
    referent: Optional[str] = None        # the thing being repaired, or None for 'last line'
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "repair"


@dataclass
class ModeSwitch:
    mode: str                             # 'dense' or 'plain'
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "mode"


@dataclass
class CommentOnly:
    comment: str
    raw: str = ""
    kind: str = "comment"


@dataclass
class Empty:
    raw: str = ""
    kind: str = "empty"


@dataclass
class PlainPassthrough:
    """A line emitted while session mode is 'plain'. Parsed as opaque text."""
    text: str
    raw: str = ""
    kind: str = "plain"


@dataclass
class Unparseable:
    """A line we refuse to interpret. Emitted in lieu of a guessed gloss."""
    reason: str
    raw: str = ""
    kind: str = "unparseable"


Node = Union[Statement, Binding, Handshake, Repair, ModeSwitch, CommentOnly, Empty, PlainPassthrough, Unparseable]


# ---------- Parse helpers ----------

def _parse_distribution(field_value: str) -> tuple[list[tuple[str, Optional[int]]], bool]:
    """Parse a slot value that may be a distribution: 'oom^6|disk^3|net^1'.

    Returns (entries, is_distribution). Each entry is (value, ordinal_rank).
    """
    if "|" not in field_value:
        # Not a distribution; check for single value with ^N.
        v, conf = _split_confidence(field_value)
        return [(v, conf)], False
    parts = field_value.split("|")
    entries: list[tuple[str, Optional[int]]] = []
    for p in parts:
        v, conf = _split_confidence(p)
        entries.append((v, conf))
    return entries, True


def _split_confidence(s: str) -> tuple[str, Optional[int]]:
    if "^" in s:
        # rightmost ^ binds confidence
        i = s.rfind("^")
        base = s[:i]
        conf_str = s[i + 1 :]
        if conf_str.isdigit() and len(conf_str) == 1:
            return base, int(conf_str)
    return s, None


def _parse_slot(f: str) -> Slot:
    """Parse one field that is structurally a slot (contains ':' or starts with a sigil)."""
    diag: list[str] = []

    # Pure-sigil-prefixed slots first.
    if f.startswith("^") and len(f) == 2 and f[1].isdigit():
        return Slot(key="^", raw=f, value=int(f[1]), confidence=int(f[1]))
    if f.startswith("#"):
        return Slot(key="#", raw=f, value=f[1:])
    if f.startswith("::"):
        return Slot(key="::", raw=f, value=f[2:])
    if f.startswith("->"):
        return Slot(key="->", raw=f, value=f[2:])
    if f.startswith("=>"):
        return Slot(key="=>", raw=f, value=f[2:])
    if f.startswith("|"):
        return Slot(key="|", raw=f, value=f[1:])
    if f.startswith("~"):
        return Slot(key="~", raw=f, value=f[1:], is_approx=True)
    if f.startswith("!") and f == "!":
        return Slot(key="!", raw=f, value=True)
    if f.startswith("†"):
        return Slot(key="†", raw=f, value=f[1:])
    if f.startswith("□"):
        return Slot(key="□", raw=f, value=f[1:] if len(f) > 1 else "")
    if f == REPAIR_TOKEN:
        return Slot(key="??", raw=f, value=None)
    if f.startswith("??"):
        return Slot(key="??", raw=f, value=f[2:])
    if f.startswith("§"):
        return Slot(key="§", raw=f, value=f[1:])

    # Evidential surface (special-case: 'ev:obs' etc).
    if f.startswith("ev:"):
        ev_value = f[3:]
        if f not in EVIDENTIALS:
            diag.append(f"unknown evidential surface 'ev:{ev_value}' (expected obs|heard|mem|guess)")
        return Slot(key="ev", raw=f, value=ev_value, diagnostics=diag)

    # Generic key:value slot.
    if ":" in f:
        key, _, val = f.partition(":")
        # Typed-hole-as-value: 'when:□date' or 'owner:□'.
        if val.startswith("□"):
            type_tag = val[1:]
            return Slot(key=key, raw=f, value={"hole": True, "type": type_tag or "any"}, diagnostics=diag)
        entries, is_dist = _parse_distribution(val)
        if is_dist:
            if len(entries) > 3:
                diag.append(f"distribution slot has {len(entries)} entries; spec caps k<=3")
            return Slot(key=key, raw=f, value=entries, is_distribution=True, diagnostics=diag)
        v, conf = entries[0]
        return Slot(key=key, raw=f, value=v, confidence=conf, diagnostics=diag)

    # Bare value (treated as positional argument, not a real slot).
    return Slot(key="", raw=f, value=f)


def _parse_op(field0: str) -> tuple[str, bool, bool]:
    """Split op suffix markers '?' and '!'."""
    op = field0
    is_query = False
    is_imp = False
    if op.endswith("?"):
        op = op[:-1]
        is_query = True
    elif op.endswith("!"):
        op = op[:-1]
        is_imp = True
    return op, is_query, is_imp


# ---------- Public API ----------

def parse_line(line: str) -> Node:
    """Parse a single line into a Node. Does not consult session state."""
    lr: LexResult = lex(line)
    fields = lr.fields
    comment = lr.comment
    raw = lr.raw

    if not fields and comment is None:
        return Empty(raw=raw)
    if not fields and comment is not None:
        return CommentOnly(comment=comment, raw=raw)

    # Handshake
    if fields[0] == HANDSHAKE_PROBE:
        version = None
        for f in fields[1:]:
            if f.startswith(HANDSHAKE_VERSION_KEY + ":"):
                version = f.split(":", 1)[1]
        return Handshake(role="probe", version=version, comment=comment, raw=raw)
    if fields[0] == HANDSHAKE_ACK and len(fields) >= 2 and fields[1] == "ok":
        version = None
        for f in fields[2:]:
            if f.startswith(HANDSHAKE_VERSION_KEY + ":"):
                version = f.split(":", 1)[1]
        return Handshake(role="ack", version=version, comment=comment, raw=raw)

    # Mode switch (must be the whole line, by itself)
    if len(fields) == 1 and fields[0] in MODE_WORDS:
        return ModeSwitch(mode=fields[0], comment=comment, raw=raw)

    # Repair
    if fields[0] == REPAIR_TOKEN:
        referent = " ".join(fields[1:]) if len(fields) > 1 else None
        return Repair(referent=referent, comment=comment, raw=raw)

    # Binding: starts with @NAME=... (inline) or @NAME := ... (whitespace form, v0.2)
    if fields[0].startswith("@") and "=" in fields[0]:
        head = fields[0]
        at_idx = head.find("=")
        handle = head[1:at_idx]
        first_val = head[at_idx + 1 :]
        rest = fields[1:]
        value = " ".join([first_val, *rest]).strip()
        is_num = handle.isdigit()
        diag: list[str] = []
        if not handle:
            diag.append("empty handle name in binding")
        return Binding(
            handle=handle,
            handle_is_numeric=is_num,
            value=value,
            comment=comment,
            raw=raw,
            diagnostics=diag,
        )
    if (
        fields[0].startswith("@")
        and len(fields) >= 2
        and fields[1] in (":=", "=")
    ):
        handle = fields[0][1:]
        value = " ".join(fields[2:]).strip()
        is_num = handle.isdigit()
        diag: list[str] = []
        if not handle:
            diag.append("empty handle name in binding")
        return Binding(
            handle=handle,
            handle_is_numeric=is_num,
            value=value,
            comment=comment,
            raw=raw,
            diagnostics=diag,
        )

    # Otherwise, statement.
    op_field = fields[0]
    # Refuse to invent meaning for lines whose first field is structurally
    # invalid as an op (starts with a slot-internal sigil that cannot be an op).
    if op_field and op_field[0] in {":", "|", "&", "^"} and op_field not in {"::", "||", "&&"}:
        return Unparseable(
            reason=f"first field '{op_field}' begins with slot-internal sigil; not a valid op",
            raw=raw,
        )
    op, is_q, is_imp = _parse_op(op_field)
    diag: list[str] = []
    if op not in ALL_OPS and op not in CLOSED_VOCAB:
        # Allow it; this is a content-vocabulary op (registered or ad-hoc).
        # Validator will flag at L1 if user requested strict mode.
        diag.append(f"op '{op}' not in audited closed vocabulary (allowed as content op)")

    target: Optional[str] = None
    slots: list[Slot] = []
    field_idx = 1
    # First bare field after op is target (patient), per spec.
    while field_idx < len(fields):
        f = fields[field_idx]
        is_slotty = (
            ":" in f
            or f.startswith(("^", "#", "::", "->", "=>", "|", "~", "!", "†", "□", "??", "§"))
            or f.startswith("ev:")
        )
        if not is_slotty and target is None:
            target = f
            field_idx += 1
            continue
        # Anything else is a slot.
        slot = _parse_slot(f)
        slots.append(slot)
        field_idx += 1

    return Statement(
        op=op,
        op_query=is_q,
        op_imperative=is_imp,
        target=target,
        slots=slots,
        comment=comment,
        raw=raw,
        diagnostics=diag,
    )


def parse_transcript(text: str) -> List[Node]:
    """Parse a multi-line transcript into a list of AST nodes."""
    return [parse_line(line) for line in text.splitlines()]
