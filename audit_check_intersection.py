#!/usr/bin/env python3
"""CI gate for the Tokenese multi-column tokenizer audit.

Enforces INTENT.md invariant 5 ("the admissible alphabet may shrink as new
columns reject candidates, never silently expand"). Run after the per-vendor
audits have written their data/source_provenance/<name>_costs.json artifacts.

Rules
-----
FAIL (exit 1) if:
  1. Any audit_<name>.py exists without a fresh data/source_provenance/<name>_costs.json
     (missing, or older than the script -> stale artifact).
  2. A symbol that spec.md's "Admissible alphabet" section claims is admissible
     is rejected (worst-case >= 2 tokens) by ANY audited tokenizer, and spec.md
     has not been updated to drop / annotate it.

WARN (exit 0) if:
  3. A symbol that spec.md does NOT list as admissible is single-token on a new
     tokenizer (additive expansion would need a spec change, but never blocks).

Reproducible: python audit_check_intersection.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROV = ROOT / "data" / "source_provenance"
SPEC = ROOT / "spec.md"

# Vendor columns audited by the data artifacts. anthropic_costs.json uses a
# flat {symbol: worst} schema; the new columns use the nested
# {category: {symbol: {bare,spaced,worst}}} schema. Both are handled.
# gemma4 replaces the prior gemma (gemma-2 proxy) column as of v0.3.8 (X5).
# Column-of-record: mlx-community/gemma-4-e4b-it-4bit (E4B, on-device prod runtime).
KNOWN_VENDORS = ["qwen", "deepseek", "llama", "gemma4", "gemini"]


def load_worst(path: Path) -> dict[str, int]:
    """Return {symbol: worst_case_token_count} for either cost-json schema.

    Raises SystemExit with a helpful message if the file is a placeholder
    (top-level ``_placeholder`` key) rather than a real audit artifact.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "_placeholder" in data:
        raise SystemExit(
            f"FAIL: {path} is a placeholder. Run the audit script for this "
            "column and replace the file with the real snapshot before "
            "running audit_check_intersection.py."
        )
    flat: dict[str, int] = {}
    for k, v in data.items():
        if k.startswith("_"):  # provenance envelopes, etc.
            continue
        if isinstance(v, dict) and "worst" in v:
            flat[k] = int(v["worst"])
        elif isinstance(v, dict):
            for sym, info in v.items():
                flat[sym] = int(info["worst"]) if isinstance(info, dict) else int(info)
        else:
            flat[k] = int(v)
    return flat


def staleness_failures() -> list[str]:
    """Each audit_<name>.py (for offline vendors) must have a fresher cost json."""
    fails = []
    for vendor in KNOWN_VENDORS:
        script = ROOT / f"audit_{vendor}.py"
        if not script.exists():
            continue
        artifact = PROV / f"{vendor}_costs.json"
        # Gemini is API-gated and may legitimately be absent in an offline run.
        if not artifact.exists():
            if vendor == "gemini":
                print(f"  note: {artifact.name} absent (Gemini is API-gated) — skipping")
                continue
            fails.append(f"missing artifact: {artifact} (run audit_{vendor}.py)")
            continue
        if artifact.stat().st_mtime < script.stat().st_mtime:
            fails.append(f"stale artifact: {artifact} is older than {script.name} "
                         f"(re-run audit_{vendor}.py)")
    return fails


# --- spec.md admissible-alphabet parsing -----------------------------------
# We read the bullet lists under "## Admissible alphabet". Backtick-wrapped
# glyphs separated by spaces are the claimed-admissible elements per sub-list.
SECTION_RE = re.compile(r"## Admissible alphabet.*?(?=\n## )", re.S)
BULLET_RE = re.compile(r"^- (ASCII sigils|Digraphs|Brackets|Unicode survivors|"
                       r"Core verb/word set)\b.*?:\s*`(.+?)`\s*$", re.M)


def parse_spec_admissible() -> dict[str, list[str]]:
    text = SPEC.read_text(encoding="utf-8")
    m = SECTION_RE.search(text)
    if not m:
        raise SystemExit("Could not find '## Admissible alphabet' section in spec.md")
    section = m.group(0)
    out: dict[str, list[str]] = {}
    for label, body in BULLET_RE.findall(section):
        # Body is the space-separated glyph run inside the first backticks.
        out[label] = [tok for tok in body.split() if tok]
    return out


def main() -> int:
    print("== audit_check_intersection ==")
    cost_columns: dict[str, dict[str, int]] = {}
    for vendor in KNOWN_VENDORS:
        artifact = PROV / f"{vendor}_costs.json"
        if artifact.exists():
            cost_columns[vendor] = load_worst(artifact)
    # Anthropic column lives top-level (flat schema) — include if present.
    anth = ROOT / "anthropic_costs.json"
    if anth.exists():
        cost_columns["anthropic"] = load_worst(anth)

    if not cost_columns:
        raise SystemExit("No *_costs.json artifacts found — run the audits first.")
    print(f"  loaded columns: {', '.join(sorted(cost_columns))}")

    fails: list[str] = []
    fails += staleness_failures()

    spec_admissible = parse_spec_admissible()
    spec_symbols = {s for syms in spec_admissible.values() for s in syms}
    print(f"  spec lists {len(spec_symbols)} admissible elements across "
          f"{len(spec_admissible)} sub-lists")

    # Rule 2: every spec-admissible symbol must be 1-token worst-case in every column.
    for label, syms in spec_admissible.items():
        for s in syms:
            rejecters = [(v, col[s]) for v, col in cost_columns.items()
                         if s in col and col[s] >= 2]
            if rejecters:
                detail = ", ".join(f"{v}:{w}tok" for v, w in rejecters)
                fails.append(f"spec claims [{label}] {s!r} admissible, but rejected by "
                             f"{detail}. Drop/annotate it in spec.md.")

    # Rule 3: additive-expansion warnings (non-blocking). Only meaningful for the
    # symbols the audits actually measured; we report glyphs single-token on a
    # NEW column that spec does not list. Kept terse to avoid noise.
    new_cols = {v: c for v, c in cost_columns.items() if v in KNOWN_VENDORS}
    measured = set().union(*[set(c) for c in new_cols.values()]) if new_cols else set()
    expand = []
    for s in sorted(measured):
        if s in spec_symbols:
            continue
        onetok = [v for v, c in new_cols.items() if c.get(s, 9) == 1]
        if len(onetok) == len(new_cols) and new_cols:
            expand.append(s)
    if expand:
        print(f"  WARN (non-blocking): {len(expand)} measured symbol(s) are "
              f"1-token on all new columns but not listed admissible in spec.md:")
        print("    " + " ".join(repr(s) for s in expand[:40]))
        print("    (additive expansion needs a deliberate spec edit; not failing.)")

    if fails:
        print("\nFAIL:")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("\nOK: admissible alphabet has not silently expanded; all spec-listed "
          "elements are 1-token worst-case across every audited column.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
