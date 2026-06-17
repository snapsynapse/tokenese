"""Per-pair scoring for the A/B harness.

`score_pair(english, tokenese, readback=None)` returns a single `PairScore`
JSON-serializable dict with everything tk-ab-run needs for one stratification
slice. Deterministic. No LLM. Anthropic token counts come from the cached
costs by default; pass live_anthropic=True to use the API (opt-in).

Schema (stable; bump `schema_version` for breaking changes):

  {
    "schema_version": "1.0",
    "provenance": {
       "spec_sha256": "...",
       "design_sha256": "...",
       "lexicon_sha256": "...",
       "translator_version": "0.1.0"
    },
    "english": {
       "text": "...",
       "tokens": {"chars": int, "o200k": int|null, "o200k_method": str,
                  "anthropic": int, "anthropic_method": str,
                  "anthropic_unknown_atoms": [...]}
    },
    "tokenese": {
       "text": "...",
       "tokens": {... same shape ...},
       "decoded_english": ["..."]    # one English line per Tokenese line
    },
    "savings": {
       "anthropic_delta": int,      # english.anthropic - tokenese.anthropic
       "anthropic_ratio": float,    # tokenese / english (lower = better)
       "o200k_delta": int|null,
       "o200k_ratio": float|null
    },
    "conformance": {
       "L1_lexicon": bool, "L2_grammar": bool, "L3_repair": bool,
       "session_issues": [...]
    },
    "misparse": {
       "by_family": {"binding": int, "scope": int, "sense": int, "triangulation": int},
       "hits": [{"family":..., "code":..., "message":..., "line_no":..., "raw":...}]
    },
    "readback": null | {
       "verbatim_ratio": float, "edit_distance_norm": float,
       "jaccard_token": float, "verdict": str
    },
    "unparseable_lines": [{"line_no": int, "raw": str, "reason": str}]
  }
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from .misparse import classify_transcript
from .parser import Unparseable, parse_transcript
from .readback import diff_readback
from .renderer import render_transcript
from .session import Session
from .token_count import count_dual
from .validator import validate_transcript


SCHEMA_VERSION = "1.0"
_TRANSLATOR_VERSION = "0.1.0"


def _sha256_file(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def _sha_from_sums(src: str, filename: str) -> Optional[str]:
    """Read a pinned SHA for `filename` from SHA256SUMS.txt, if listed."""
    sums = os.path.join(src, "SHA256SUMS.txt")
    try:
        with open(sums, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2 and parts[1] == filename:
                    return parts[0]
    except Exception:
        pass
    return None


def _provenance() -> Dict[str, Any]:
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    src = os.path.join(base, "source_provenance")
    # PRD-027 and the ab-suite spec are not bundled in this repo. If a future
    # build drops them into data/source_provenance/ (or pins them in
    # SHA256SUMS.txt), they resolve here; otherwise they read "unpinned".
    prd_027_sha = (
        _sha256_file(os.path.join(src, "PRD-027.md"))
        or _sha_from_sums(src, "PRD-027.md")
        or "unpinned"
    )
    ab_suite_sha = (
        _sha256_file(os.path.join(src, "tokenese-ab-suite.md"))
        or _sha_from_sums(src, "tokenese-ab-suite.md")
        or "unpinned"
    )
    return {
        "translator_version": _TRANSLATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "spec_sha256": _sha256_file(os.path.join(src, "spec.md")),
        "design_sha256": _sha256_file(os.path.join(src, "DESIGN.md")),
        "intent_sha256": _sha256_file(os.path.join(src, "INTENT.md")),
        "conformance_sha256": _sha256_file(os.path.join(src, "CONFORMANCE.md")),
        "lexicon_sha256": _sha256_file(os.path.join(base, "anthropic_costs.json")),
        "grammar_target": "v0.2 (DESIGN.md \u00a77) over v0.1 (spec.md)",
        "prd_027_sha": prd_027_sha,
        "ab_suite_sha": ab_suite_sha,
    }


def score_pair(
    english: str,
    tokenese: str,
    readback: Optional[str] = None,
    live_anthropic: bool = False,
) -> Dict[str, Any]:
    """Score one (english, tokenese) pair.

    `readback` is the receiver's reply payload (after stripping leading \u221a)
    to a `!`-flagged statement. When present, the readback differ runs.
    """
    en_tok = count_dual(english, live_anthropic=live_anthropic).to_dict()
    tk_tok = count_dual(tokenese, live_anthropic=live_anthropic).to_dict()

    # Decode the Tokenese side (with a fresh session for determinism)
    sess = Session()
    decoded = render_transcript(tokenese, session=sess)

    # Conformance + misparse classification
    conformance = validate_transcript(tokenese).to_dict()
    misparse = classify_transcript(tokenese).to_dict()

    # Unparseable lines
    nodes = parse_transcript(tokenese)
    unparseable: List[Dict[str, Any]] = []
    for i, n in enumerate(nodes, start=1):
        if isinstance(n, Unparseable):
            unparseable.append({"line_no": i, "raw": n.raw, "reason": n.reason})

    # Savings
    def _safe_delta(a: Optional[int], b: Optional[int]) -> Optional[int]:
        if a is None or b is None:
            return None
        return a - b

    def _safe_ratio(num: Optional[int], den: Optional[int]) -> Optional[float]:
        if num is None or den in (None, 0):
            return None
        return round(num / den, 4)

    savings = {
        "anthropic_delta": _safe_delta(en_tok["anthropic"], tk_tok["anthropic"]),
        "anthropic_ratio": _safe_ratio(tk_tok["anthropic"], en_tok["anthropic"]),
        "o200k_delta": _safe_delta(en_tok["o200k"], tk_tok["o200k"]),
        "o200k_ratio": _safe_ratio(tk_tok["o200k"], en_tok["o200k"]),
    }

    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "provenance": _provenance(),
        "english": {"text": english, "tokens": en_tok},
        "tokenese": {
            "text": tokenese,
            "tokens": tk_tok,
            "decoded_english": decoded,
        },
        "savings": savings,
        "conformance": {
            "L1_lexicon": conformance["L1_lexicon"],
            "L2_grammar": conformance["L2_grammar"],
            "L3_repair": conformance["L3_repair"],
            "session_issues": conformance.get("session_issues", []),
        },
        "misparse": misparse,
        "readback": None,
        "unparseable_lines": unparseable,
    }

    if readback is not None:
        # K4 reference text: the English projection of the Tokenese is what
        # the receiver should have been paraphrasing. If the harness wants
        # to score readback against the English original instead, it can
        # do so by passing english as the readback's reference — but the
        # default here matches the K4 protocol (paraphrase the dense form).
        reference = "\n".join(decoded).strip()
        diff = diff_readback(reference, readback).to_dict()
        payload["readback"] = diff

    return payload


def score_pair_json(*args, **kwargs) -> str:
    return json.dumps(score_pair(*args, **kwargs), indent=2, ensure_ascii=False)
