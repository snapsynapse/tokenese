"""Tokenizer token counters.

Returns token counts for a piece of text under:
  - o200k_base (OpenAI/GPT-4o/o-series/Codex era) via tiktoken and the
    bundled verified BPE table.
  - cl100k_base (OpenAI GPT-4/GPT-3.5 era) via tiktoken.
  - Anthropic (claude-haiku-4-5 was the audited tokenizer per spec.md v0.1)
    via either (a) the cached per-symbol costs in data/anthropic_costs.json,
    summed conservatively, or (b) live API if --live-anthropic AND
    ANTHROPIC_API_KEY is set.

Determinism:
  - tiktoken path is local, deterministic, and does not fetch tokenizer data
    at runtime when the bundled BPE table is present.
  - cached Anthropic path is local, deterministic. It sums symbol costs
    over a whitespace tokenization, with any unknown atom priced as
    len(atom)//3 + 1 (a documented worst-case heuristic; flagged in the
    result). This is the recommended offline default.
  - live Anthropic path is the only optional non-deterministic surface
    and is opt-in.

For the A/B harness, use `count_dual(text)` and read `o200k` + `anthropic`
fields. The result object always reports the method used so the eval can
filter to comparable measurements.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from .lexicon import COSTS


# ---- o200k (OpenAI) via tiktoken ----

_O200K = None
_O200K_BPE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "o200k_base.tiktoken",
)
_O200K_BPE_SHA256 = "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d"
_O200K_PAT_STR = "|".join(
    [
        r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
        r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
        r"""\p{N}{1,3}""",
        r""" ?[^\s\p{L}\p{N}]+[\r\n/]*""",
        r"""\s*[\r\n]+""",
        r"""\s+(?!\S)""",
        r"""\s+""",
    ]
)

def _o200k():
    global _O200K
    if _O200K is not None:
        return _O200K
    try:
        import tiktoken  # type: ignore
        if os.path.exists(_O200K_BPE_PATH):
            from tiktoken.load import load_tiktoken_bpe  # type: ignore
            mergeable_ranks = load_tiktoken_bpe(
                _O200K_BPE_PATH,
                expected_hash=_O200K_BPE_SHA256,
            )
            _O200K = tiktoken.Encoding(
                name="o200k_base",
                pat_str=_O200K_PAT_STR,
                mergeable_ranks=mergeable_ranks,
                special_tokens={"<|endoftext|>": 199999, "<|endofprompt|>": 200018},
            )
        else:
            _O200K = tiktoken.get_encoding("o200k_base")
        return _O200K
    except Exception:
        return None


def count_o200k(text: str) -> Optional[int]:
    enc = _o200k()
    if enc is None:
        return None
    return len(enc.encode(text))


# ---- cl100k (OpenAI) via tiktoken ----

_CL100K = None


def _cl100k():
    global _CL100K
    if _CL100K is not None:
        return _CL100K
    try:
        import tiktoken  # type: ignore

        _CL100K = tiktoken.get_encoding("cl100k_base")
        return _CL100K
    except Exception:
        return None


def count_cl100k(text: str) -> Optional[int]:
    enc = _cl100k()
    if enc is None:
        return None
    return len(enc.encode(text))


# ---- Anthropic via cached costs (offline default) ----

# Sub-token splitter: words (alnum+underscore), digraphs/sigils, whitespace.
_ATOM_RE = re.compile(
    r"(->|=>|::|\|\||&&|>>|<<|!=|==|>=|<=|\+\+|--|\.\.|//|"
    r"[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|"
    r"\s+|.)",
    flags=re.UNICODE,
)


@dataclass
class AnthropicCachedResult:
    total: int
    unknown_atoms: list[str] = field(default_factory=list)
    method: str = "cached_costs+heuristic"


def count_anthropic_cached(text: str) -> AnthropicCachedResult:
    """Offline Anthropic token estimate from anthropic_costs.json.

    Algorithm: tokenize into atoms (regex above), look up each atom in COSTS;
    for atoms not present, fall back to ceil(len/3) + 1 and record the atom
    so the caller can see how heuristic-heavy this count is.
    """
    total = 0
    unknown: list[str] = []
    for m in _ATOM_RE.finditer(text):
        atom = m.group(0)
        if atom.isspace():
            continue
        if atom in COSTS:
            total += COSTS[atom]
            continue
        # Heuristic fallback for content vocabulary.
        unknown.append(atom)
        total += max(1, (len(atom) + 2) // 3)
    return AnthropicCachedResult(total=total, unknown_atoms=unknown)


# ---- Anthropic via live API (opt-in) ----

def count_anthropic_live(text: str, model: str = "claude-haiku-4-5") -> Optional[int]:
    """Live count via the anthropic SDK. Requires ANTHROPIC_API_KEY.

    Returns None if the SDK is not installed or the key is missing.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore
    except Exception:
        return None
    try:
        client = anthropic.Anthropic()
        # count_tokens is the documented endpoint name in the spec audit script.
        resp = client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}],
        )
        # SDK shape: resp.input_tokens
        return int(getattr(resp, "input_tokens", 0))
    except Exception:
        return None


# ---- Unified API ----

@dataclass
class DualCount:
    text_len_chars: int
    o200k: Optional[int]
    o200k_method: str          # "tiktoken" or "unavailable"
    anthropic: int
    anthropic_method: str      # "cached_costs+heuristic" or "live_api"
    anthropic_unknown_atoms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chars": self.text_len_chars,
            "o200k": self.o200k,
            "o200k_method": self.o200k_method,
            "anthropic": self.anthropic,
            "anthropic_method": self.anthropic_method,
            "anthropic_unknown_atoms": self.anthropic_unknown_atoms,
        }


def count_dual(text: str, live_anthropic: bool = False) -> DualCount:
    o = count_o200k(text)
    o_method = "tiktoken" if o is not None else "unavailable"

    a_live = count_anthropic_live(text) if live_anthropic else None
    if a_live is not None:
        return DualCount(
            text_len_chars=len(text),
            o200k=o,
            o200k_method=o_method,
            anthropic=a_live,
            anthropic_method="live_api",
        )

    cached = count_anthropic_cached(text)
    return DualCount(
        text_len_chars=len(text),
        o200k=o,
        o200k_method=o_method,
        anthropic=cached.total,
        anthropic_method=cached.method,
        anthropic_unknown_atoms=cached.unknown_atoms,
    )
