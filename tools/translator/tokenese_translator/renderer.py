"""AST -> English renderer.

Goals (DESIGN.md §3, §5; INTENT.md invariants 4 and 7):
  - Honest. Epistemic structure is preserved, not smoothed away.
  - Auditable. A reader with the one-page key can map English back to Tokenese.
  - Deterministic. Same input + same session state always produces the same
    English output.

Trade-off taken: where natural-sounding English would erase a channel
(confidence, source, alternatives, repair markers, unfilled holes,
unconfirmed anchors), we emit a slightly clunkier but faithful rendering.

Output convention:
  - One English sentence (or fragment) per Tokenese line, in input order.
  - Bracketed notes carry meta-information (confidence, source, repair).
  - A `// comment` is appended as `Note: <comment>` in English.
"""

from __future__ import annotations

from typing import List, Optional

from .lexicon import EVIDENTIALS, EVIDENTIAL_DEFAULT_ENGLISH, english_for_word
from .parser import (
    Binding,
    CommentOnly,
    Empty,
    Handshake,
    ModeSwitch,
    Node,
    PlainPassthrough,
    Repair,
    Slot,
    Statement,
    Unparseable,
    parse_line,
    parse_transcript,
)
from .session import Session


# ----- slot value rendering -----

def _render_value(v) -> str:
    if v is None:
        return ""
    return str(v)


def _render_distribution(entries) -> str:
    """Render ranked alternatives: [('oom', 6), ('disk', 3)] -> 'OOM (rank 1) or disk (rank 2)'."""
    parts = []
    for i, (val, conf) in enumerate(entries):
        rank = i + 1
        weight = f", ordinal weight {conf}" if conf is not None else ""
        parts.append(f"{val} (rank {rank}{weight})")
    return " or ".join(parts)


def _render_slot(slot: Slot, session: Optional[Session]) -> str:
    k = slot.key
    if k == "ev":
        gloss = EVIDENTIALS.get(slot.raw, EVIDENTIAL_DEFAULT_ENGLISH)
        return f"[{gloss}]"
    if k == "^":
        return f"[confidence {slot.value}/9]"
    if k == "#":
        return f"[tag: {slot.value}]"
    if k == "::":
        return f"[type: {slot.value}]"
    if k == "->":
        return f"-> {_resolve_ref(slot.value, session)}"
    if k == "=>":
        return f"=> therefore {_resolve_ref(slot.value, session)}"
    if k == "|":
        return f"or {_resolve_ref(slot.value, session)}"
    if k == "~":
        return f"approximately {_resolve_ref(slot.value, session)}"
    if k == "!":
        return "[imperative; receiver should reply √ with a paraphrased restatement]"
    if k == "†":
        return f"[corpus anchor: {slot.value} — awaiting gloss]"
    if k == "□":
        type_tag = slot.value or "any"
        return f"[unfilled hole: {type_tag}]"
    if k == "??":
        if slot.value:
            return f"[repair requested on: {slot.value} (resend in plain English)]"
        return "[repair: resend in plain English]"
    if k == "§":
        return f"[spec rule §{slot.value}]"
    if k == "":
        # bare value (additional positional argument)
        return _resolve_ref(slot.value, session)

    # Generic key:value slot
    if slot.is_distribution:
        return f"{k}: {_render_distribution(slot.value)}"
    # Typed hole as value (e.g. when:□date).
    if isinstance(slot.value, dict) and slot.value.get("hole"):
        type_tag = slot.value.get("type") or "any"
        return f"{k}: [unfilled hole: {type_tag}]"
    conf_tail = f" [confidence {slot.confidence}/9]" if slot.confidence is not None else ""
    return f"{k}: {_resolve_ref(_render_value(slot.value), session)}{conf_tail}"


def _resolve_ref(text: str, session: Optional[Session]) -> str:
    """Expand @handle references inline when the session knows them."""
    if not isinstance(text, str) or "@" not in text:
        return str(text)
    if session is None:
        return text
    out_parts: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "@":
            j = i + 1
            while j < len(text) and (text[j].isalnum() or text[j] in ("_", "-")):
                j += 1
            handle = text[i + 1 : j]
            resolved = session.resolve(handle) if handle else None
            if resolved is not None:
                out_parts.append(f'"{resolved}" (@{handle})')
            else:
                out_parts.append(f"@{handle} (unbound)")
            i = j
        else:
            out_parts.append(text[i])
            i += 1
    return "".join(out_parts)


# ----- node renderers -----

def _render_statement(node: Statement, session: Optional[Session]) -> str:
    op_text = english_for_word(node.op)
    if node.op_query:
        op_text = f"query: {op_text}"
    if node.op_imperative:
        op_text = f"{op_text} (imperative; receiver should reply √ with paraphrased restatement)"
    parts: list[str] = [op_text]
    if node.target is not None:
        parts.append(_resolve_ref(node.target, session))
    # Group slots so that '->' / '=>' (sequence/implication) emit cleanly,
    # absorbing any trailing bare-value slots as the consequent payload.
    i = 0
    while i < len(node.slots):
        slot = node.slots[i]
        if slot.key in ("->", "=>") and (slot.value is None or slot.value == ""):
            tail_parts: list[str] = []
            j = i + 1
            while j < len(node.slots):
                tail = node.slots[j]
                if tail.key not in ("", "->", "=>"):
                    break
                tail_parts.append(_render_slot(tail, session))
                j += 1
            arrow = "then" if slot.key == "->" else "therefore"
            consequent = " ".join(tail_parts).strip()
            parts.append(f"-> {arrow}: {consequent}" if consequent else f"-> {arrow}")
            i = j
            continue
        parts.append(_render_slot(slot, session))
        i += 1
    out = " ".join(p for p in parts if p)
    if node.comment:
        out += f"  Note: {node.comment}"
    if node.diagnostics:
        out += "  [diagnostics: " + "; ".join(node.diagnostics) + "]"
    return out


def _render_binding(node: Binding, session: Optional[Session]) -> str:
    expanded = _resolve_ref(node.value, session) if session else node.value
    msg = f'bind @{node.handle} = "{node.value}"'
    if expanded != node.value:
        msg += f" (resolves to {expanded})"
    if node.comment:
        msg += f"  Note: {node.comment}"
    if node.diagnostics:
        msg += "  [diagnostics: " + "; ".join(node.diagnostics) + "]"
    return msg


def _render_handshake(node: Handshake) -> str:
    if node.role == "probe":
        v = f" version {node.version}" if node.version else ""
        return f"handshake probe: speak Tokenese?{v}"
    return f"handshake ack: Tokenese OK{' version ' + node.version if node.version else ''}"


def _render_repair(node: Repair, session: Optional[Session]) -> str:
    if not node.referent:
        last = session.last_statement_raw if session and session.last_statement_raw else None
        ref_note = f' (referring to: "{last}")' if last else ""
        return f"repair: last line misparsed, resend in plain English{ref_note}"
    return f"repair: '{node.referent}' misparsed, resend in plain English"


def _render_mode(node: ModeSwitch) -> str:
    if node.mode == "dense":
        return "[mode -> dense Tokenese]"
    return "[mode -> plain English]"


def _render_comment(node: CommentOnly) -> str:
    return f"(comment only) Note: {node.comment}"


def _render_plain(node: PlainPassthrough) -> str:
    return node.text


# ----- public API -----

def render_node(node: Node, session: Optional[Session] = None) -> str:
    if isinstance(node, Statement):
        return _render_statement(node, session)
    if isinstance(node, Binding):
        return _render_binding(node, session)
    if isinstance(node, Handshake):
        return _render_handshake(node)
    if isinstance(node, Repair):
        return _render_repair(node, session)
    if isinstance(node, ModeSwitch):
        return _render_mode(node)
    if isinstance(node, CommentOnly):
        return _render_comment(node)
    if isinstance(node, PlainPassthrough):
        return _render_plain(node)
    if isinstance(node, Empty):
        return ""
    if isinstance(node, Unparseable):
        return f"[UNPARSEABLE: {node.reason}]  raw: {node.raw!r}"
    return f"[unrenderable node: {node}]"


def render_line(line: str, session: Optional[Session] = None) -> str:
    """Parse + render a single Tokenese line, updating session if provided."""
    if session is not None and session.mode == "plain":
        # In plain mode, pass through verbatim until a 'dense' mode-switch line.
        stripped = line.strip()
        if stripped == "dense":
            node = parse_line(line)
            out = render_node(node, session)
            session.on_mode("dense")
            return out
        return PlainPassthrough(text=line, raw=line).text

    node = parse_line(line)
    # Update session state.
    if session is not None:
        _apply_to_session(node, session)
    return render_node(node, session)


def render_transcript(text: str, session: Optional[Session] = None) -> List[str]:
    """Render an entire transcript. Returns one English string per input line."""
    out: list[str] = []
    for raw_line in text.splitlines():
        out.append(render_line(raw_line, session))
    return out


def _apply_to_session(node: Node, session: Session) -> None:
    """Mutate session state based on a parsed node. Pure bookkeeping."""
    if isinstance(node, Handshake):
        if node.role == "probe":
            session.on_probe(node.version)
        else:
            session.on_ack(node.version)
        return
    if isinstance(node, ModeSwitch):
        session.on_mode(node.mode)
        return
    if isinstance(node, Binding):
        err = session.bind(node.handle, node.value)
        if err:
            session.diagnostics.append(err)
        session.remember_statement(node.raw)
        return
    if isinstance(node, Repair):
        session.on_repair(node.referent)
        return
    if isinstance(node, Statement):
        # `drop @x` is the explicit-drop op from DESIGN.md K1.
        if node.op == "drop" and node.target and node.target.startswith("@"):
            err = session.drop(node.target[1:])
            if err:
                session.diagnostics.append(err)
        session.remember_statement(node.raw)
        return
