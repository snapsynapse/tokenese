"""MCP service wrapper.

Exposes six tools over stdio:
  - open_session() -> session_id
  - close_session(session_id)
  - to_english(session_id, text) -> {english, session, diagnostics}
  - parse(text) -> AST as JSON
  - validate(text) -> conformance report
  - audit_lexicon() -> C1 report

The MCP Python SDK is an optional dependency. Install with:
    pip install tokenese-translator[mcp]

If `mcp` is not importable, `main()` prints install instructions and exits 1.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict

from .renderer import render_transcript
from .session import Session
from .validator import audit_lexicon, validate_transcript
from .parser import parse_transcript
from .score import score_pair as _score_pair
from .token_count import count_dual as _count_dual
from .misparse import classify_transcript as _classify_transcript
from .readback import diff_readback as _diff_readback


# In-memory session store; cleared when the process exits.
_SESSIONS: Dict[str, Session] = {}


def _serialize(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


# ----- pure tool implementations (also usable without MCP) -----

def tool_open_session() -> Dict[str, Any]:
    sess = Session()
    _SESSIONS[sess.session_id] = sess
    return {"session_id": sess.session_id}


def tool_close_session(session_id: str) -> Dict[str, Any]:
    existed = _SESSIONS.pop(session_id, None) is not None
    return {"closed": existed}


def tool_to_english(session_id: str, text: str) -> Dict[str, Any]:
    sess = _SESSIONS.get(session_id)
    if sess is None:
        return {"error": f"unknown session_id '{session_id}'. Call open_session first."}
    english = render_transcript(text, session=sess)
    return {
        "english": english,
        "session": {
            "session_id": sess.session_id,
            "handshake": sess.handshake,
            "version": sess.version,
            "mode": sess.mode,
            "bindings": sess.bindings,
            "diagnostics": sess.diagnostics,
            "repair_history": {
                k: {"count": v.count, "pinned_plain": v.pinned_plain}
                for k, v in sess.repair_history.items()
            },
        },
    }


def tool_parse(text: str) -> Dict[str, Any]:
    nodes = parse_transcript(text)
    return {"ast": [_serialize(n) for n in nodes]}


def tool_validate(text: str) -> Dict[str, Any]:
    return validate_transcript(text).to_dict()


def tool_audit_lexicon() -> Dict[str, Any]:
    return audit_lexicon()


def tool_score_pair(english: str, tokenese: str, readback: Any = None,
                    live_anthropic: bool = False) -> Dict[str, Any]:
    return _score_pair(english, tokenese, readback=readback, live_anthropic=live_anthropic)


def tool_count_tokens(text: str, live_anthropic: bool = False) -> Dict[str, Any]:
    return _count_dual(text, live_anthropic=live_anthropic).to_dict()


def tool_classify_misparse(text: str) -> Dict[str, Any]:
    return _classify_transcript(text).to_dict()


def tool_diff_readback(original: str, readback: str) -> Dict[str, Any]:
    return _diff_readback(original, readback).to_dict()


# ----- MCP wiring -----

def main() -> int:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:  # pragma: no cover - exercised manually
        sys.stderr.write(
            "MCP SDK not installed. Install with:\n"
            "    pip install tokenese-translator[mcp]\n"
        )
        return 1

    mcp = FastMCP("tokenese-translator")

    @mcp.tool()
    def open_session() -> dict:
        """Start a new translator session. Returns session_id."""
        return tool_open_session()

    @mcp.tool()
    def close_session(session_id: str) -> dict:
        """Close a translator session by id."""
        return tool_close_session(session_id)

    @mcp.tool()
    def to_english(session_id: str, text: str) -> dict:
        """Translate Tokenese text to English within a session.

        Updates the session's bindings, handshake, mode, and repair history.
        Returns the English rendering plus the resulting session state.
        """
        return tool_to_english(session_id, text)

    @mcp.tool()
    def parse(text: str) -> dict:
        """Parse Tokenese text to an AST (JSON). Stateless."""
        return tool_parse(text)

    @mcp.tool()
    def validate(text: str) -> dict:
        """Run L1/L2/L3 conformance checks against Tokenese text. Stateless."""
        return tool_validate(text)

    @mcp.tool()
    def audit_lexicon_tool() -> dict:
        """Re-derive C1 lexicon admissibility from the bundled audit data."""
        return tool_audit_lexicon()

    @mcp.tool()
    def score_pair(english: str, tokenese: str, readback: str = "",
                   live_anthropic: bool = False) -> dict:
        """Score one (english, tokenese[, readback]) pair for the A/B harness.

        Returns a structured JSON object: conformance, dual token counts,
        savings, misparse-family classification, readback diff (when
        readback is non-empty), and unparseable-line list.
        """
        rb = readback if readback else None
        return tool_score_pair(english, tokenese, readback=rb, live_anthropic=live_anthropic)

    @mcp.tool()
    def count_tokens(text: str, live_anthropic: bool = False) -> dict:
        """Dual-tokenizer count (o200k + Anthropic)."""
        return tool_count_tokens(text, live_anthropic=live_anthropic)

    @mcp.tool()
    def classify_misparse(text: str) -> dict:
        """Stratify diagnostics by misparse family (binding/scope/sense/triangulation)."""
        return tool_classify_misparse(text)

    @mcp.tool()
    def diff_readback(original: str, readback: str) -> dict:
        """Score a K4 paraphrase readback (transformed vs verbatim)."""
        return tool_diff_readback(original, readback)

    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
