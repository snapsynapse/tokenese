#!/usr/bin/env python3
"""Shared candidate symbol set for all Tokenese tokenizer-column audits.

Single source of truth so every audit_<vendor>.py iterates the *identical*
candidate set. The set is the one originally defined in audit_symbols.py
(OpenAI o200k_base audit); it is re-exported here unchanged and audit_symbols.py
continues to define its own copy for backward compatibility.

If you add a candidate, add it here and the whole 7-column matrix picks it up.
"""
from __future__ import annotations

# Mirrors audit_symbols.py CANDIDATES exactly (keep in sync).
CANDIDATES = {
    "ascii-sigil": list("@#$%&*+-/|~!?^_=<>:;.,"),
    "ascii-digraph": ["->", "=>", "::", "||", "&&", ">>", "<<", "!=", "==",
                      ">=", "<=", "++", "--", "..", "//"],
    "bracket": list("()[]{}") + ["[[", "]]", "{{", "}}"],
    "arrow-math": list("→←↑↓⇒⇐↔∴∵∀∃∈∉⊂⊃∧∨¬±×÷≠≈≤≥∞∑∏√Δ∇"),
    "geometric-misc": list("•◦▸▹►▶○●□■◆◇★☆†‡§¶"),
    "greek": list("αβγδεζηθικλμνξοπρστυφχψω"),
    "cjk-sample": list("人事时地物因果前后大小新旧真假问答始终入出上下中外不可必有无同异"),
    "emoji-sample": list("✅❌⚠️🔴🟢🔵📌🔒🔓"),
    "short-words": ["do", "go", "if", "or", "and", "not", "yes", "no", "ok",
                    "ask", "say", "get", "put", "run", "fix", "new", "old",
                    "big", "all", "none", "true", "false", "done", "fail",
                    "need", "want", "must", "may", "can", "will"],
}

# v0.3 multi-character sigils from DESIGN.md §7. Audited too, so the spec
# footnote can be updated if a new tokenizer splits any of them.
V03_SIGILS = [">>>", "*>>", "?>>", "^plain<<<", ">>>^plain", '"""']


def all_candidates():
    """Yield (category, symbol) pairs for the full audited set including v0.3 sigils."""
    for category, syms in CANDIDATES.items():
        for s in syms:
            yield category, s
    for s in V03_SIGILS:
        yield "v03-sigil", s
