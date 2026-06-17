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

# Grammar versions this parser understands. ``"v0.2"`` is the implicit default
# (backward compatible); ``"v0.3"`` enables the additive v0.3 sigils.
SUPPORTED_GRAMMARS = ("v0.2", "v0.3")
DEFAULT_GRAMMAR = "v0.2"

# v0.3 infix causal/sequence sigils, mapped to their AST constructors.
_CAUSAL_SIGILS = {">>>", "*>>", "?>>"}
_CAUSAL_KIND = {
    ">>>": "sequence",
    "*>>": "stipulated_causation",
    "?>>": "hypothesized_causation",
}


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
    # v0.3 repair sub-taxonomy (backward compatible: v0.2 callers ignore these).
    repair_kind: str = "repair-statement"   # repair-token|repair-statement|repair-handle|repair-explained
    target: Optional[str] = None             # handle/slot reference being repaired
    reason: Optional[str] = None             # explanation text for repair-explained
    line_no: int = 0                         # 1-based line; filled by parse_transcript


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


# ---------- v0.3 AST node types ----------

@dataclass
class GrammarVersion:
    """``^grammar:vX.Y`` artifact-level declaration (v0.3)."""
    version: str
    comment: Optional[str] = None
    raw: str = ""
    kind: str = "grammar_version"


@dataclass
class LevelDeclaration:
    """``^declare:level=L2`` artifact-level declaration (v0.3)."""
    level: str                            # 'L0'|'L1'|'L2'|'L3'
    comment: Optional[str] = None
    raw: str = ""
    diagnostics: List[str] = field(default_factory=list)
    kind: str = "level_declaration"


@dataclass
class Comment:
    """A whole-line ``# ...`` comment (v0.3). Contributes nothing to scoring."""
    text: str
    raw: str = ""
    line_no: int = 0
    kind: str = "line_comment"


@dataclass
class PlainBlock:
    """A closed ``^plain<<< ... >>>^plain`` region (v0.3). Captured raw."""
    text: str                             # verbatim inner content, byte-for-byte
    start_line: int = 0                   # 1-based line of the opener
    end_line: int = 0                     # 1-based line of the closer
    raw: str = ""
    kind: str = "plain_block"


@dataclass
class SourceQuote:
    """A ``\"\"\" ... \"\"\"`` raw source quote (v0.3). Verbatim contents."""
    text: str
    raw: str = ""
    line_no: int = 0
    kind: str = "source_quote"


Node = Union[
    Statement, Binding, Handshake, Repair, ModeSwitch, CommentOnly, Empty,
    PlainPassthrough, Unparseable, GrammarVersion, LevelDeclaration, Comment,
    PlainBlock, SourceQuote,
]


# ---------- v0.3 expression operands (negation / hedge / causal) ----------

@dataclass
class Negated:
    """``!@handle`` — negation prefix (v0.3)."""
    handle: str                           # canonical handle name (no sigils)
    inner: Optional["Hedged"] = None      # set when composed as !@x?
    kind: str = "negated"


@dataclass
class Hedged:
    """``@handle?`` — hedge suffix (v0.3)."""
    handle: str
    kind: str = "hedged"


@dataclass
class Sequence:
    """``left >>> right`` — temporal sequence (v0.3)."""
    left: str
    right: str
    kind: str = "sequence"


@dataclass
class StipulatedCausation:
    """``left *>> right`` — asserted causation, requires source support (v0.3)."""
    left: str
    right: str
    kind: str = "stipulated_causation"


@dataclass
class HypothesizedCausation:
    """``left ?>> right`` — hypothesized causation, always admissible (v0.3)."""
    left: str
    right: str
    kind: str = "hypothesized_causation"


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


def parse_operand(token: str):
    """Parse a single value-position token into a v0.3 operand AST node.

    Recognizes the negation prefix (``!@h``), the hedge suffix (``@h?``), and
    their composition (``!@h?`` → ``Negated(inner=Hedged(...))``). A plain
    ``@handle`` or any non-handle token is returned unchanged (as a ``str``),
    so callers can use this uniformly.
    """
    from .handles import consume_handle

    parsed = consume_handle(token, 0)
    if parsed is None:
        return token
    handle, end = parsed
    if end != len(token):
        return token  # trailing junk: treat as opaque content, not an operand
    if handle.negated and handle.hedged:
        return Negated(handle=handle.name, inner=Hedged(handle=handle.name))
    if handle.negated:
        return Negated(handle=handle.name)
    if handle.hedged:
        return Hedged(handle=handle.name)
    return token  # bare @handle — no v0.3 decoration


def parse_causal(left: str, sigil: str, right: str):
    """Construct the causal/sequence AST node for an infix sigil."""
    kind = _CAUSAL_KIND.get(sigil)
    if kind == "sequence":
        return Sequence(left=left, right=right)
    if kind == "stipulated_causation":
        return StipulatedCausation(left=left, right=right)
    if kind == "hypothesized_causation":
        return HypothesizedCausation(left=left, right=right)
    return None


def _parse_repair_v03(fields: List[str], comment: Optional[str], raw: str) -> Repair:
    """Classify a ``??`` line into the v0.3 repair sub-taxonomy.

    | surface                         | kind             |
    | ``??`` alone                    | repair-statement |
    | ``??@handle`` / ``?? @handle``  | repair-handle    |
    | ``??: <reason>``                | repair-explained |
    | ``?? <token>`` (other)          | repair-token     |
    """
    head = fields[0]
    rest = fields[1:]

    # repair-explained: '??:' prefix, reason runs to EOL.
    # Surfaces: '??: reason...' (head=='??:') or '??:reason' (head=='??:reason').
    if head == "??:" or head.startswith("??:"):
        inline = head[3:]
        reason_parts = [p for p in ([inline] if inline else []) + rest]
        reason = " ".join(reason_parts).strip() or None
        return Repair(
            referent=reason, repair_kind="repair-explained", reason=reason,
            comment=comment, raw=raw,
        )

    # Determine the referent token (handle/slot/anchor) the way v0.2 did.
    if head == REPAIR_TOKEN:
        referent = " ".join(rest) if rest else None
    else:
        # Attached form like '??@cfg' or '??:slot' (slot handled above).
        attached = head[2:]
        referent = " ".join([attached, *rest]).strip() if (attached or rest) else None

    if not referent:
        return Repair(
            referent=None, repair_kind="repair-statement",
            comment=comment, raw=raw,
        )
    if referent.startswith("@"):
        return Repair(
            referent=referent, repair_kind="repair-handle", target=referent,
            comment=comment, raw=raw,
        )
    # Any other addressed referent (slot, anchor, bare token) is a token repair.
    return Repair(
        referent=referent, repair_kind="repair-token", target=referent,
        comment=comment, raw=raw,
    )


# ---------- Public API ----------

def parse_line(line: str, grammar: str = DEFAULT_GRAMMAR) -> Node:
    """Parse a single line into a Node. Does not consult session state.

    ``grammar`` selects the surface dialect. ``"v0.2"`` (default) preserves
    the original behavior byte-for-byte; ``"v0.3"`` additionally recognizes
    line comments, the ``^grammar`` / ``^declare:level`` header sigils, the
    repair sub-taxonomy, and the negation/hedge/causal operators.
    """
    v03 = grammar == "v0.3"
    raw_full = line.rstrip("\n")

    # v0.3 line comment: '#' at line start (after optional whitespace) runs to
    # EOL. Inline '#' is NOT a comment (handled by the lexer/parser as content).
    if v03:
        stripped = raw_full.lstrip()
        if stripped.startswith("#"):
            return Comment(text=stripped[1:].lstrip(), raw=raw_full)

    lr: LexResult = lex(line)
    fields = lr.fields
    comment = lr.comment
    raw = lr.raw

    if not fields and comment is None:
        return Empty(raw=raw)
    if not fields and comment is not None:
        return CommentOnly(comment=comment, raw=raw)

    # v0.3 header sigils.
    if v03:
        if fields[0].startswith("^grammar:") and len(fields) == 1:
            return GrammarVersion(version=fields[0].split(":", 1)[1], comment=comment, raw=raw)
        if fields[0].startswith("^declare:level=") and len(fields) == 1:
            level = fields[0].split("=", 1)[1]
            diag: list[str] = []
            if level not in {"L0", "L1", "L2", "L3"}:
                diag.append(f"unknown declared level '{level}' (expected L0|L1|L2|L3)")
            return LevelDeclaration(level=level, comment=comment, raw=raw, diagnostics=diag)

        # v0.3 repair sub-taxonomy. The bare '??' families are recognized here
        # before the v0.2 repair path so they carry the richer fields.
        if fields[0] == REPAIR_TOKEN or fields[0].startswith("??"):
            return _parse_repair_v03(fields, comment, raw)

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
        # v0.3 infix causal sigils: capture `<prev> SIGIL <next>` as a slot
        # whose value is (left, right). They only activate under v0.3 — in
        # v0.2 they fall through to bare values exactly as before.
        if v03 and f in _CAUSAL_SIGILS and field_idx + 1 < len(fields):
            left = target if target is not None else (slots[-1].value if slots else "")
            right = fields[field_idx + 1]
            slots.append(Slot(key=f, raw=f, value=(left, right)))
            field_idx += 2
            continue
        is_slotty = (
            ":" in f
            or f.startswith(("^", "#", "::", "->", "=>", "|", "~", "†", "□", "??", "§"))
            or f.startswith("ev:")
            or (f.startswith("!") and not (v03 and f.startswith("!@")))
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


def detect_grammar(text: str) -> str:
    """Return the declared grammar version, or ``DEFAULT_GRAMMAR`` if none.

    A ``^grammar:vX.Y`` declaration is honored only when it is the first
    non-empty, non-comment line. Comments here are recognized leniently (a
    leading ``#``) so a v0.3 file may carry a banner comment above its
    declaration. An unsupported version is reported by ``parse_transcript``;
    this helper just surfaces the *declared* string for dispatch.
    """
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        if s.startswith("^grammar:"):
            return s.split(":", 1)[1].strip()
        return DEFAULT_GRAMMAR
    return DEFAULT_GRAMMAR


def parse_transcript(text: str) -> List[Node]:
    """Parse a multi-line transcript into a list of AST nodes.

    Detects the artifact's grammar version (``^grammar:vX.Y`` as the first
    non-comment line) and dispatches accordingly. Under v0.3 it also resolves
    the multi-line constructs — closed plain regions and triple-quoted source
    quotes — that a single line cannot express.
    """
    declared = detect_grammar(text)
    if declared.startswith("^grammar:"):
        declared = declared.split(":", 1)[1]

    if declared not in SUPPORTED_GRAMMARS:
        # Unsupported version: refuse the whole artifact with one diagnostic.
        return [Unparseable(reason=f"unsupported grammar version: {declared}", raw=text.splitlines()[0] if text else "")]

    grammar = declared
    v03 = grammar == "v0.3"
    lines = text.splitlines()
    nodes: List[Node] = []
    seen_non_comment = False  # for ^declare:level position enforcement
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # ---- v0.3 multi-line: closed plain region ----
        if v03 and stripped == "^plain<<<":
            start = i + 1
            body: List[str] = []
            j = i + 1
            closed = False
            while j < n:
                if lines[j].strip() == ">>>^plain":
                    closed = True
                    break
                body.append(lines[j])
                j += 1
            block_text = "\n".join(body)
            if not closed:
                # Unclosed region runs to EOF (still a PlainBlock; honest).
                nodes.append(PlainBlock(text=block_text, start_line=i + 1, end_line=n, raw=line))
                seen_non_comment = True
                break
            nodes.append(PlainBlock(text=block_text, start_line=i + 1, end_line=j + 1, raw=line))
            seen_non_comment = True
            i = j + 1
            continue

        # ---- v0.3 multi-line: triple-quoted source quote ----
        if v03 and '"""' in line:
            node, consumed = _consume_source_quote(lines, i)
            if node is not None:
                node.line_no = i + 1
                nodes.append(node)
                seen_non_comment = True
                i += consumed
                continue

        node = parse_line(line, grammar=grammar)

        # Position enforcement for ^declare:level (must be first non-comment).
        if isinstance(node, LevelDeclaration):
            if seen_non_comment:
                node = Unparseable(
                    reason="^declare:level must be the first non-comment statement",
                    raw=node.raw,
                )
            else:
                node.line_no = i + 1  # type: ignore[attr-defined]
        elif isinstance(node, (Comment, GrammarVersion)):
            pass  # comments and the grammar header do not count as content
        else:
            seen_non_comment = True

        # Stamp 1-based line numbers. Dataclass fields that expose line_no keep
        # their public field; every node also gets _line_no for telemetry.
        setattr(node, "_line_no", i + 1)
        if isinstance(node, (Repair, Comment, SourceQuote)):
            node.line_no = i + 1
        nodes.append(node)
        i += 1

    return nodes


def _consume_source_quote(lines: List[str], i: int):
    """If a triple-quoted span opens at ``lines[i]``, capture it verbatim.

    Returns ``(SourceQuote, n_lines_consumed)`` or ``(None, 0)`` when the line
    merely contains ``\"\"\"`` as part of something else (no opener position).
    The opener is the first ``\"\"\"`` on the line; everything up to the
    matching closer ``\"\"\"`` (possibly on a later line) is the verbatim body.
    """
    line = lines[i]
    open_at = line.find('"""')
    if open_at < 0:
        return None, 0
    after = line[open_at + 3 :]
    # Same-line closer?
    close_at = after.find('"""')
    if close_at >= 0:
        return SourceQuote(text=after[:close_at], raw=line), 1
    # Multi-line: scan forward for the closer.
    body_parts = [after]
    j = i + 1
    n = len(lines)
    while j < n:
        cidx = lines[j].find('"""')
        if cidx >= 0:
            body_parts.append(lines[j][:cidx])
            text = "\n".join(body_parts)
            return SourceQuote(text=text, raw="\n".join(lines[i : j + 1])), (j - i + 1)
        body_parts.append(lines[j])
        j += 1
    # Unclosed: capture to EOF.
    text = "\n".join(body_parts)
    return SourceQuote(text=text, raw="\n".join(lines[i:])), (n - i)
