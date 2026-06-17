#!/usr/bin/env python3
"""Shared audit driver for the Tokenese tokenizer-column audits.

Each audit_<vendor>.py supplies a `count_tokens(text) -> int` callable and a
vendor name; this module iterates the shared candidate set (audit_candidates.py),
measures bare + space-prefixed cost, writes the JSON artifact, and prints the
1 / 2 / >2 token breakdown.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from audit_candidates import CANDIDATES, V03_SIGILS

OUT_DIR = Path("data/source_provenance")


def run_audit(name: str, count_tokens: Callable[[str], int],
              top_level_symlink: bool = True) -> int:
    """Measure every candidate, write <name>_costs.json, print a breakdown.

    Returns a process exit code (0 on success).
    """
    results: dict[str, dict[str, dict[str, int]]] = {}
    categories = {**CANDIDATES, "v03-sigil": V03_SIGILS}
    for category, candidates in categories.items():
        results[category] = {}
        for c in candidates:
            bare = count_tokens(c)
            spaced = count_tokens(" " + c)
            results[category][c] = {
                "bare": bare,
                "spaced": spaced,
                "worst": max(bare, spaced),
            }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}_costs.json"
    payload = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out.write_text(payload, encoding="utf-8")
    print(f"Wrote {out}")

    if top_level_symlink:
        # Repo convention: anthropic_costs.json lives top-level too. Write a
        # plain copy (not a symlink) so it survives checkout on any platform.
        top = Path(f"{name}_costs.json")
        top.write_text(payload, encoding="utf-8")
        print(f"Wrote {top}")

    total = sum(len(v) for v in results.values())
    one = sum(1 for cat in results.values() for r in cat.values() if r["worst"] == 1)
    two = sum(1 for cat in results.values() for r in cat.values() if r["worst"] == 2)
    many = total - one - two
    print(f"{one}/{total} candidates are 1 token worst-case on this tokenizer")
    print(f"breakdown: 1-token={one}  2-token={two}  >2-token={many}")
    return 0
