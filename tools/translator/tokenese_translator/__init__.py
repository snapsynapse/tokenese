"""Tokenese -> English translator (deterministic, no LLMs).

Targets spec v0.2 per DESIGN.md; spec.md v0.1 is the frozen baseline.
"""

from .lexer import lex
from .misparse import classify_transcript
from .parser import parse_line, parse_transcript
from .readback import diff_readback
from .renderer import render_line, render_transcript
from .score import score_pair, score_pair_json
from .session import Session
from .token_count import count_dual, count_anthropic_cached, count_o200k
from .validator import audit_lexicon, validate_line, validate_transcript

__all__ = [
    "lex",
    "parse_line",
    "parse_transcript",
    "render_line",
    "render_transcript",
    "Session",
    "validate_line",
    "validate_transcript",
    "audit_lexicon",
    "count_dual",
    "count_o200k",
    "count_anthropic_cached",
    "diff_readback",
    "classify_transcript",
    "score_pair",
    "score_pair_json",
]

__version__ = "0.1.0"
