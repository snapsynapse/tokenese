"""Tokenese lexer.

A Tokenese line is whitespace-separated 'fields'. The lexer splits a line
into top-level fields and strips trailing `// human comment` (spec.md §
"Reserved sigils" — comments are ignored by protocol).

We deliberately do NOT decompose a slot like `cause:oom^6|disk^3` here — that
is the parser's job, because slot-internal grammar (`:` `^` `|` `&` `::`) is
key-dependent. The lexer produces fields; the parser interprets them.

Special cases handled here:
  - `//` to end of line is a comment, stripped and returned as a separate field.
  - `??` alone is the repair token; with a trailing reference (`?? @cfg`)
    the trailing field is still a separate top-level field.
  - Leading/trailing whitespace is discarded; empty lines yield no fields.
  - `dense` and `plain` mode words appear as standalone fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LexResult:
    fields: List[str]
    comment: Optional[str]  # text after //, with leading space stripped, or None
    raw: str                # the original line (newline-stripped)


def lex(line: str) -> LexResult:
    raw = line.rstrip("\n")
    # Pull off a trailing // comment, but not // inside quoted strings.
    # v0.2 allows `{ }` proposition quoting, depth 1. We respect single-level
    # brace quoting so `//` inside `{...}` stays inside the value.
    comment: Optional[str] = None
    in_quote = 0
    i = 0
    while i < len(raw) - 1:
        ch = raw[i]
        if ch == "{":
            in_quote += 1
        elif ch == "}":
            in_quote = max(0, in_quote - 1)
        elif in_quote == 0 and ch == "/" and raw[i + 1] == "/":
            comment = raw[i + 2 :].lstrip()
            raw = raw[:i].rstrip()
            break
        i += 1

    # Whitespace split, preserving brace-quoted spans as single fields.
    fields: List[str] = []
    buf: List[str] = []
    depth = 0
    for ch in raw:
        if ch == "{":
            depth += 1
            buf.append(ch)
        elif ch == "}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch.isspace() and depth == 0:
            if buf:
                fields.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        fields.append("".join(buf))

    return LexResult(fields=fields, comment=comment, raw=line.rstrip("\n"))
