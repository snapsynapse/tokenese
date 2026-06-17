"""Command-line interface for the TKAB per-pair scorer.

Usage:

    tokenese-check --pair <pair.json> [--out <result.json>] [--pretty]
    tokenese-check --batch <dir> [--out <out_dir>] [--strict]

``--pair`` scores a single ``*.pair.json`` file and writes one JSON result.
``--batch`` iterates every ``*.pair.json`` in a directory, writing one
``<name>.result.json`` per input and printing a summary table to stderr.

The checker reports; it does not gate. Exit code is 0 regardless of outcome
unless ``--strict`` is passed, in which case any ``fail-*`` or ``indeterminate``
outcome yields exit code 1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from .checker import check_pair, load_pair


def _dump(result: Dict[str, Any], pretty: bool) -> str:
    if pretty:
        return json.dumps(result, indent=2, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


def _is_fail(outcome: str) -> bool:
    return outcome.startswith("fail") or outcome == "indeterminate"


def _run_pair(path: str, out: str | None, pretty: bool) -> Dict[str, Any]:
    pair = load_pair(path)
    result = check_pair(pair)
    text = _dump(result, pretty)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return result


def _run_batch(directory: str, out_dir: str | None, pretty: bool) -> List[Dict[str, Any]]:
    names = sorted(n for n in os.listdir(directory) if n.endswith(".pair.json"))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for name in names:
        pair = load_pair(os.path.join(directory, name))
        result = check_pair(pair)
        results.append(result)
        text = _dump(result, pretty)
        if out_dir:
            stem = name[: -len(".pair.json")]
            with open(os.path.join(out_dir, f"{stem}.result.json"), "w", encoding="utf-8") as f:
                f.write(text + "\n")
        else:
            sys.stdout.write(text + "\n")
    # Summary table to stderr.
    sys.stderr.write("pair_id\toutcome\n")
    for r in results:
        sys.stderr.write(f"{r['pair_id']}\t{r['outcome']}\n")
    return results


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokenese-check",
        description="Deterministic per-pair TKAB scorer (schema tkab-check-1.0).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pair", metavar="PAIR_JSON", help="score one *.pair.json file")
    group.add_argument("--batch", metavar="DIR", help="score every *.pair.json in DIR")
    parser.add_argument("--out", metavar="PATH", help="output file (--pair) or directory (--batch)")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on any fail-* or indeterminate outcome (default: always exit 0)",
    )
    args = parser.parse_args(argv)

    if args.pair:
        result = _run_pair(args.pair, args.out, args.pretty)
        outcomes = [result["outcome"]]
    else:
        results = _run_batch(args.batch, args.out, args.pretty)
        outcomes = [r["outcome"] for r in results]

    if args.strict and any(_is_fail(o) for o in outcomes):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
