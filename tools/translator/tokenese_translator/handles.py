"""Centralized handle lexer (Tier 3 #7, grammar v0.3).

Before v0.3 the handle charset and the `@name` recognizer were duplicated
across ``parser.py``, ``renderer.py`` and ``misparse.py`` (plus three ad-hoc
patches added during the v0.2 cycle: parser ``:=`` binding, renderer kebab
support, misparse kebab support). This module is the single source of truth.

A handle is::

    ['!'] '@' NAME ['?']

where NAME is the canonical handle name (unchanged from v0.2): a run of
alphanumerics plus ``_`` and ``-`` (both snake_case and kebab-case are
accepted, continuing v0.2 behavior). The optional leading ``!`` is the v0.3
negation prefix and the optional trailing ``?`` is the v0.3 hedge suffix.
Negation/hedge are only *meaningful* under grammar v0.3 — callers decide
whether to honor them — but the charset itself is version-independent so the
canonical name never changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


# The canonical handle-name character set. Unchanged from v0.2: alphanumerics
# plus '_' and '-'. Lives in exactly one place now.
def _is_name_char(ch: str) -> bool:
    return ch.isalnum() or ch in ("_", "-")


@dataclass(frozen=True)
class Handle:
    """A parsed handle reference.

    ``name`` is the canonical handle (no sigils). ``negated`` reflects a
    leading ``!`` and ``hedged`` a trailing ``?``. Composition ``!@x?`` is
    ``Handle(name="x", negated=True, hedged=True)`` — "possibly not x".
    """

    name: str
    negated: bool = False
    hedged: bool = False

    @property
    def canonical(self) -> str:
        """The bare ``@name`` form, sigils stripped (v0.2-compatible)."""
        return f"@{self.name}"

    def surface(self) -> str:
        """Re-emit the full surface form including v0.3 sigils."""
        return f"{'!' if self.negated else ''}@{self.name}{'?' if self.hedged else ''}"


def consume_handle(text: str, start: int) -> Optional[Tuple[Handle, int]]:
    """Consume a handle beginning at ``text[start]``.

    Returns ``(Handle, end_index)`` where ``end_index`` is the position just
    after the handle (including any trailing ``?`` hedge), or ``None`` if there
    is no handle at ``start``.

    Accepts an optional leading ``!`` (negation) and an optional trailing
    ``?`` (hedge). The ``@`` and at least one name character are mandatory.
    """
    i = start
    n = len(text)
    negated = False
    if i < n and text[i] == "!":
        # Only treat '!' as negation if an '@' immediately follows.
        if i + 1 < n and text[i + 1] == "@":
            negated = True
            i += 1
        else:
            return None
    if i >= n or text[i] != "@":
        return None
    i += 1  # consume '@'
    name_start = i
    while i < n and _is_name_char(text[i]):
        i += 1
    if i == name_start:
        return None  # bare '@' with no name is not a handle
    name = text[name_start:i]
    hedged = False
    if i < n and text[i] == "?":
        hedged = True
        i += 1
    return Handle(name=name, negated=negated, hedged=hedged), i
