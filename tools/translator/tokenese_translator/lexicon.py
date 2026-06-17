"""Tokenese lexicon, derived from the audited cost data.

Spec invariant 2 (as amended 2026-06-12): the closed function vocabulary must
cost 1 token worst case in every audited tokenizer; content vocabulary is
admitted on a tokens-per-semantic-unit basis (so 2-token CJK is allowed).

This module:
  - Loads the bundled audit data (Anthropic side; OpenAI side is verifiable
    independently via tiktoken in audit_symbols.py, not bundled at runtime).
  - Exposes the closed function vocabulary (cost == 1) as `CLOSED_VOCAB`.
  - Exposes role-based subsets used by the parser/renderer (sigils, ops,
    evidential surfaces, mode words, repair tokens, etc.).
  - Provides `is_admissible(token, strict)` for the L1 validator.

Per CONFORMANCE.md C1, this is reproducible offline: nothing here calls a
network. The bundled JSON is the audited source of truth.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Set

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "anthropic_costs.json",
)


def _load_costs() -> Dict[str, int]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


COSTS: Dict[str, int] = _load_costs()

# Closed function vocabulary: must be 1 token (invariant 2, function-vocab clause).
CLOSED_VOCAB: Set[str] = {tok for tok, cost in COSTS.items() if cost == 1}

# Content vocabulary failed-audit list (cost > 1) is informational only;
# content vocabulary admission is per-use, scored against alternatives.
CONTENT_OVER_COST: Dict[str, int] = {tok: c for tok, c in COSTS.items() if c > 1}

# ----- Role-based subsets (spec.md §"Reserved sigils" + DESIGN.md §7) -----

# Reserved single-char sigils used at slot/op boundaries.
RESERVED_SIGILS: Set[str] = {
    "@",   # handle bind/reference
    "#",   # tag/category
    "=",   # binding (definition)
    "?",   # query marker (op suffix)
    "!",   # imperative + readback trigger
    "~",   # approximate
    "^",   # confidence slot prefix (^0..^9)
    "|",   # alternatives within a slot
    "&",   # conjunction within slot
    "//",  # comment to humans
    ":",   # key:value separator (slot)
    "::",  # type/scope qualifier
    "§",   # spec rule reference
    "□",   # typed hole (v0.2)
    "†",   # corpus anchor (v0.2)
    "√",   # ack/confirm (v0.2)
    "->",  # causes/yields/then
    "=>",  # implies/therefore
    "??",  # repair (addressable in v0.2)
    "{",
    "}",
    "(",
    ")",
}

# Mode words (R1, dense/plain).
MODE_WORDS: Set[str] = {"dense", "plain"}

# Evidential surfaces (DESIGN.md §3 K6, resolved 2026-06-12). All 1 token.
EVIDENTIALS: Dict[str, str] = {
    "ev:obs": "observed",
    "ev:heard": "reported by another party",
    "ev:mem": "from memory",
    "ev:guess": "working assumption",
}
EVIDENTIAL_DEFAULT_ENGLISH = "inferred"

# Core verb / word set (spec.md §"Admissible alphabet"), all 1 token.
CORE_OPS: Set[str] = {
    "do", "go", "if", "or", "and", "not", "yes", "no", "ok",
    "ask", "say", "get", "put", "run", "fix", "new", "old",
    "big", "all", "none", "true", "false", "done", "fail",
    "need", "want", "must", "may", "can", "will",
}

# Additional ops / words admitted by audit deltas in DESIGN.md §8.
EXTRA_OPS: Set[str] = {
    "because", "like", "cf", "val", "zone", "but", "same", "other",
    "before", "after", "most", "except", "guess", "drop", "fill",
    "sum", "head", "tail", "sync", "hold", "set",
    "when", "who", "what", "why", "how", "where",
    "more", "less", "very", "kind", "part", "still",
    # evidential round
    "said", "quote", "cite", "heard", "report", "claim",
    "via", "per", "relay", "mem", "prior", "stored",
    "train", "weights", "seen", "wit",
    # core repair/handshake/mode words also fit here
    "tokenese",
}

ALL_OPS: Set[str] = CORE_OPS | EXTRA_OPS | MODE_WORDS

# Repair tokens.
REPAIR_TOKEN = "??"

# Handshake constants.
HANDSHAKE_PROBE = "tokenese?"
HANDSHAKE_ACK = "tokenese"
HANDSHAKE_VERSION_KEY = "v"


def is_admissible(token: str, strict: bool = False) -> bool:
    """L1 admissibility check.

    strict=True : token must appear in CLOSED_VOCAB (cost-1, audited).
    strict=False: token may also be content vocabulary — any UTF-8 text. The
                  parser does not gate content tokens, since the spec admits
                  arbitrary content vocabulary by cost advantage, not by a
                  closed list.
    """
    if token in CLOSED_VOCAB:
        return True
    if not strict:
        return True
    return False


def english_for_word(token: str) -> str:
    """Best-effort English gloss for a closed-vocabulary token.

    The spec gives sigils explicit meanings (rendered structurally by the
    renderer), but plain words like 'fix' or 'fail' have no extra mapping
    needed — they round-trip to themselves. This function exists so the
    renderer can interpose canonical English where Tokenese deviates.
    """
    return {
        "y": "yes",
        "n": "no",
        "ok": "OK",
        "fn": "function",
    }.get(token, token)
