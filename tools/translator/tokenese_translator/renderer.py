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

from .handles import consume_handle
from .lexicon import EVIDENTIALS, EVIDENTIAL_DEFAULT_ENGLISH, english_for_word
from .parser import (
    Binding,
    Comment,
    CommentOnly,
    Empty,
    GrammarVersion,
    Handshake,
    LevelDeclaration,
    ModeSwitch,
    Node,
    PlainBlock,
    PlainPassthrough,
    Repair,
    Slot,
    SourceQuote,
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
    if k in (">>>", "*>>", "?>>"):
        # v0.3 causal/sequence sigils; value is (left, right).
        left, right = slot.value if isinstance(slot.value, tuple) else ("", "")
        lr = _resolve_ref(left, session)
        rr = _resolve_ref(right, session)
        if k == ">>>":
            return f"{lr} then {rr}"
        if k == "*>>":
            return f"{lr} causes {rr}"
        return f"{lr} may cause {rr}"
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
    """Expand @handle references inline when the session knows them.

    Handle scanning is delegated to the centralized lexer (``consume_handle``),
    so kebab/snake names and the v0.3 negation/hedge decorations are handled in
    one place. ``!@h`` renders as "not <h>" and ``@h?`` as "<h> (possibly)".
    """
    if not isinstance(text, str) or "@" not in text:
        return str(text)
    out_parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        probe = i
        # consume_handle accepts a leading '!'; start the probe there so the
        # negation prefix is captured with the handle.
        if ch == "!" and i + 1 < n and text[i + 1] == "@":
            probe = i
        elif ch != "@":
            out_parts.append(ch)
            i += 1
            continue
        parsed = consume_handle(text, probe)
        if parsed is None:
            out_parts.append(ch)
            i += 1
            continue
        handle, end = parsed
        resolved = session.resolve(handle.name) if session else None
        if resolved is not None:
            core = f'"{resolved}" (@{handle.name})'
        else:
            core = f"@{handle.name}" + (" (unbound)" if session else "")
        # Compose so ``!@x?`` reads "possibly not x" (negation inside hedge).
        if handle.negated:
            core = f"not {core}"
        if handle.hedged:
            core = f"possibly {core}"
        out_parts.append(core)
        i = end
    return "".join(out_parts)


# ----- node renderers -----

def _render_statement(node: Statement, session: Optional[Session]) -> str:
    op_text = english_for_word(node.op)
    if node.op_query:
        op_text = f"query: {op_text}"
    if node.op_imperative:
        op_text = f"{op_text} (imperative; receiver should reply √ with paraphrased restatement)"
    parts: list[str] = [op_text]
    # A v0.3 causal slot captures the statement target as its `left` operand
    # (``say @a >>> @b`` parses target=@a, slot left=@a). Render the target
    # only when no causal slot already consumes it, so it is not duplicated.
    target_consumed_by_causal = any(
        s.key in (">>>", "*>>", "?>>")
        and isinstance(s.value, tuple)
        and s.value[0] == node.target
        for s in node.slots
    )
    if node.target is not None and not target_consumed_by_causal:
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


def _render_plain_block(node: PlainBlock) -> str:
    return node.text


def _render_comment_node(node: Comment) -> str:
    return f"(comment) {node.text}"


def _render_grammar_version(node: GrammarVersion) -> str:
    return f"[grammar version: {node.version}]"


def _render_level_declaration(node: LevelDeclaration) -> str:
    return f"[declared conformance level: {node.level}]"


def _render_source_quote(node: SourceQuote) -> str:
    return f'[source quote: "{node.text}"]'


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
    if isinstance(node, Comment):
        return _render_comment_node(node)
    if isinstance(node, PlainPassthrough):
        return _render_plain(node)
    if isinstance(node, PlainBlock):
        return _render_plain_block(node)
    if isinstance(node, GrammarVersion):
        return _render_grammar_version(node)
    if isinstance(node, LevelDeclaration):
        return _render_level_declaration(node)
    if isinstance(node, SourceQuote):
        return _render_source_quote(node)
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
    """Render an entire transcript. Returns one English string per AST node.

    For v0.2 artifacts this is one English string per input line (unchanged).
    For v0.3 artifacts the transcript is parsed as a whole so multi-line
    constructs (closed plain regions, triple-quoted source quotes) render as a
    single node; the returned list therefore has one entry per node, which may
    be fewer than the line count when such constructs are present.
    """
    from .parser import detect_grammar

    if detect_grammar(text) != "v0.3":
        out: list[str] = []
        for raw_line in text.splitlines():
            out.append(render_line(raw_line, session))
        return out

    # v0.3: parse the full transcript (resolves multi-line constructs) and
    # render node by node, threading session state for handle resolution.
    out = []
    for node in parse_transcript(text):
        if session is not None:
            _apply_to_session(node, session)
        out.append(render_node(node, session))
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
