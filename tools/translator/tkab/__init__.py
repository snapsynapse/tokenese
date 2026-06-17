"""TKAB harness layer for PRD-027 mini-pilot scoring.

This package wraps the deterministic translator with the per-pair scoring
contract from PRD-027 R6.3 and the W1/L1 mini-pilot rules from
tokenese-ab-suite.md.

Public API:
    check_pair(pair: dict, *, live_anthropic=False) -> dict
        Score one paired-fixture dict against PRD-027 rules.
    load_pair(path: str) -> dict
        Load a *.pair.json fixture from disk.
"""

from .checker import check_pair, load_pair, OUTPUT_SCHEMA_VERSION

__all__ = ["check_pair", "load_pair", "OUTPUT_SCHEMA_VERSION"]
