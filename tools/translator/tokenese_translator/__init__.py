"""Tokenese -> English translator (deterministic, no LLMs).

Targets grammar v0.3 (GRAMMAR-v0.3.md governs). v0.2 (DESIGN.md §7) remains
fully backward compatible; spec.md v0.1 is the frozen baseline.
"""

from .handles import Handle, consume_handle
from .framesets import load_frameset_registry, registered_ops, validate_framesets
from .lexer import lex
from .misparse import classify_transcript
from .parser import (
    detect_grammar,
    parse_causal,
    parse_line,
    parse_operand,
    parse_transcript,
)
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
    "parse_operand",
    "parse_causal",
    "detect_grammar",
    "consume_handle",
    "Handle",
    "load_frameset_registry",
    "registered_ops",
    "validate_framesets",
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

__version__ = "0.3.3"
grammar_version = "v0.3"
GRAMMAR_VERSION_SUPPORTED = "v0.3"
