"""Readback differ for DESIGN.md \u00a73 K4 (stake-scaled paraphrase readback).

K4 contract: when sender flags a statement with `!`, the receiver must reply
\u221a plus a TRANSFORMED restatement. Verbatim echo proves copying, not
comprehension; the receiver must decode-and-reencode through their own
representation.

This module scores a (original, readback) pair WITHOUT an LLM. It is a
heuristic, not a semantic oracle; the scores are signals the A/B harness
can threshold on, not ground truth.

Outputs three deterministic signals:
  - verbatim_ratio   : longest-common-substring length / len(original)
  - edit_distance    : normalized Levenshtein on whitespace tokens
  - jaccard_token    : set-Jaccard over content tokens (closed-vocab + words)
  - verdict          : one of {"verbatim", "near_verbatim", "transformed",
                                "unrelated"} from threshold rules below

Thresholds (calibratable; documented):
  - verbatim_ratio > 0.85       \u2192 "verbatim"
  - 0.55 < verbatim_ratio <= 0.85 \u2192 "near_verbatim"
  - jaccard_token > 0.30        \u2192 at least "transformed" (not "unrelated")
  - else \u2192 "unrelated"

All thresholds are exposed as module constants for the harness to override.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


# Default thresholds. These are the initial calibration knobs; the A/B
# harness can override them after live data. Documented defaults:
#   verbatim       : LCS / len(original)            > 0.85
#   near_verbatim  : LCS / len(original)            > 0.55
#   transformed    : token-set Jaccard              >= 0.25
#   else           : 'unrelated'
VERBATIM_THRESHOLD = 0.85
NEAR_VERBATIM_THRESHOLD = 0.55
RELATED_JACCARD_THRESHOLD = 0.25


_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?", re.UNICODE)


def _tokens(s: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s)]


def _longest_common_substring(a: str, b: str) -> int:
    if not a or not b:
        return 0
    # O(n*m) DP, fine for paragraph-scale readback.
    m, n = len(a), len(b)
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        ai = a[i - 1]
        for j in range(1, n + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def _levenshtein(a: List[str], b: List[str]) -> int:
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ai = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


@dataclass
class ReadbackDiff:
    verbatim_ratio: float
    edit_distance_norm: float
    jaccard_token: float
    verdict: str

    def to_dict(self) -> dict:
        return {
            "verbatim_ratio": round(self.verbatim_ratio, 4),
            "edit_distance_norm": round(self.edit_distance_norm, 4),
            "jaccard_token": round(self.jaccard_token, 4),
            "verdict": self.verdict,
        }


def diff_readback(original: str, readback: str) -> ReadbackDiff:
    """Score a paraphrase readback against its original.

    `original`  : the sender's statement (in any form: Tokenese, English, or
                   the English projection of the Tokenese -- caller's choice).
    `readback`  : the receiver's reply payload (after stripping a leading \u221a).
    """
    orig = original.strip()
    rb = readback.strip()
    if not orig or not rb:
        return ReadbackDiff(0.0, 1.0, 0.0, "unrelated")

    lcs = _longest_common_substring(orig, rb)
    verb_ratio = lcs / max(len(orig), 1)

    toks_o = _tokens(orig)
    toks_r = _tokens(rb)
    if not toks_o or not toks_r:
        jac = 0.0
        ed_norm = 1.0
    else:
        set_o = set(toks_o)
        set_r = set(toks_r)
        inter = len(set_o & set_r)
        union = len(set_o | set_r)
        jac = inter / union if union else 0.0
        ed = _levenshtein(toks_o, toks_r)
        ed_norm = ed / max(len(toks_o), len(toks_r))

    if verb_ratio > VERBATIM_THRESHOLD:
        verdict = "verbatim"
    elif verb_ratio > NEAR_VERBATIM_THRESHOLD:
        verdict = "near_verbatim"
    elif jac >= RELATED_JACCARD_THRESHOLD:
        verdict = "transformed"
    else:
        verdict = "unrelated"

    return ReadbackDiff(
        verbatim_ratio=verb_ratio,
        edit_distance_norm=ed_norm,
        jaccard_token=jac,
        verdict=verdict,
    )
