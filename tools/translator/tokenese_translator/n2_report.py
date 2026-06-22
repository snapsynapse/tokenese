"""N2 static package report.

N2 is the live A/B kill criterion. This module assembles the deterministic
pieces that can be verified before a live multi-family run: token-count suites,
receiver candidate term coverage, and TKAB fixture outcomes.

It intentionally does not close N2. A report can be "static-package-ready" while
the live A/B result remains open.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Iterable

from .compression_eval import DEFAULT_SUITE as COMPRESSION_SUITE
from .compression_eval import evaluate_suite, load_suite
from .receiver_eval import DEFAULT_SUITE as RECEIVER_SUITE
from .receiver_eval import evaluate_static, load_suite as load_receiver_suite
from tkab.checker import check_pair, load_pair


HERE = os.path.dirname(os.path.abspath(__file__))
HYPOTHESIS_SUITE = os.path.join(HERE, "evals", "hypothesis_cases.json")
TKAB_FIXTURES = os.path.abspath(os.path.join(HERE, "..", "tkab", "fixtures"))

FAIR_BASELINES = {
    "terse_english",
    "equal_precision_english",
    "explicit_terse_english",
    "disambiguating_english",
}


def _tkab_results(fixtures_dir: str = TKAB_FIXTURES) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name in sorted(os.listdir(fixtures_dir)):
        if not name.endswith(".pair.json"):
            continue
        path = os.path.join(fixtures_dir, name)
        result = check_pair(load_pair(path))
        results.append(
            {
                "fixture": name,
                "pair_id": result["pair_id"],
                "arm": result["arm"],
                "outcome": result["outcome"],
                "conformance_level": result["conformance_level"],
                "misparse_family": result["misparse_family"]["by_family"],
                "repair_events": len(result["repair_events"]),
            }
        )
    return results


def _relative_o200k_items(result: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for case in result["cases"]:
        for comparison in case["relative_counts"]:
            if comparison["baseline"] not in FAIR_BASELINES:
                continue
            metrics = comparison["by_tokenizer"]["o200k"]
            savings = metrics["savings_percent"]
            if savings is None:
                continue
            items.append(
                {
                    "case": case["id"],
                    "candidate": comparison["candidate"],
                    "baseline": comparison["baseline"],
                    "o200k_candidate": metrics["candidate"],
                    "o200k_baseline": metrics["baseline"],
                    "o200k_savings_percent": savings,
                }
            )
    return items


def _hypothesis_summary(result: dict[str, Any]) -> dict[str, Any]:
    items = _relative_o200k_items(result)
    wins = [item for item in items if item["o200k_savings_percent"] > 0]
    losses = [item for item in items if item["o200k_savings_percent"] < 0]
    break_even = [item for item in items if item["o200k_savings_percent"] == 0]
    return {
        "case_count": len(result["cases"]),
        "counts_available": result["counts_available"],
        "fair_baseline_comparison_count": len(items),
        "o200k_wins": len(wins),
        "o200k_losses": len(losses),
        "o200k_break_even": len(break_even),
        "top_o200k_wins": sorted(
            wins,
            key=lambda item: item["o200k_savings_percent"],
            reverse=True,
        )[:5],
        "top_o200k_losses": sorted(
            losses,
            key=lambda item: item["o200k_savings_percent"],
        )[:5],
    }


def _receiver_summary(result: dict[str, Any], min_score: float) -> dict[str, Any]:
    cases = []
    scores = []
    for case in result["cases"]:
        scored = case["candidate_term_score"]
        scores.append(scored["score"])
        cases.append(
            {
                "id": case["id"],
                "score": scored["score"],
                "misses": scored["misses"],
            }
        )
    minimum = min(scores) if scores else 1.0
    average = round(sum(scores) / len(scores), 4) if scores else 1.0
    return {
        "mode": result["mode"],
        "case_count": len(cases),
        "min_score_threshold": min_score,
        "min_score": minimum,
        "average_score": average,
        "threshold_pass": minimum >= min_score,
        "cases_below_threshold": [
            case for case in cases if case["score"] < min_score
        ],
    }


def build_report(
    *,
    receiver_min_score: float = 0.75,
    compression_suite: str = COMPRESSION_SUITE,
    hypothesis_suite: str = HYPOTHESIS_SUITE,
    receiver_suite: str = RECEIVER_SUITE,
    tkab_fixtures: str = TKAB_FIXTURES,
) -> dict[str, Any]:
    compression = evaluate_suite(load_suite(compression_suite))
    hypothesis = evaluate_suite(load_suite(hypothesis_suite))
    receiver = evaluate_static(load_receiver_suite(receiver_suite))
    tkab = _tkab_results(tkab_fixtures)
    outcomes = Counter(result["outcome"] for result in tkab)

    receiver_summary = _receiver_summary(receiver, receiver_min_score)
    static_ready = (
        compression["counts_available"]
        and compression["pass"]
        and hypothesis["counts_available"]
        and bool(tkab)
    )

    return {
        "schema_version": "tokenese-n2-static-package-0.1",
        "roadmap_item": "N2",
        "status": "static-package-ready/live-ab-open" if static_ready else "static-package-incomplete",
        "n2_closed": False,
        "closure_reason": "Live multi-family receiver A/B results are not attached to this package.",
        "static_gates": {
            "compression_counts_available": compression["counts_available"],
            "compression_expectations_pass": compression["pass"],
            "hypothesis_counts_available": hypothesis["counts_available"],
            "tkab_fixture_count": len(tkab),
            "receiver_static_term_floor_pass": receiver_summary["threshold_pass"],
        },
        "compression_regression": {
            "suite": os.path.relpath(compression_suite, os.getcwd()),
            "case_count": len(compression["cases"]),
            "pass": compression["pass"],
            "counts_available": compression["counts_available"],
            "baseline_policy": compression["baseline_policy"],
        },
        "hypothesis_counts": _hypothesis_summary(hypothesis),
        "receiver_static": receiver_summary,
        "tkab": {
            "fixture_dir": os.path.relpath(tkab_fixtures, os.getcwd()),
            "fixture_count": len(tkab),
            "outcomes": dict(sorted(outcomes.items())),
            "results": tkab,
        },
        "live_ab_requirements": [
            "Run the same fixed operational/code task suite in English and Tokenese.",
            "Include Claude, Codex, and at least one third independent model family.",
            "Log tokens, task success, misparse/repair events, readback mismatches, and receiver output per exchange.",
            "Stratify misparse/retry events by binding, scope, sense, and triangulation family.",
            "Keep dense-loses cases in the suite; do not promote syntax that only wins on cherry-picked payloads.",
        ],
        "revision_requirements_before_claim": [
            "Revise or retire receiver candidates below the static term floor before treating them as positive evidence.",
            "Use DESIGN.md section 10 direction: explicit near[...] and far_from[...] forms replace ~= and !~=.",
            "Report N2 as open until live A/B artifacts are present and reproducible.",
        ],
    }


def _markdown_lines(report: dict[str, Any]) -> Iterable[str]:
    yield "# N2 static package"
    yield ""
    yield f"Status: {report['status']}"
    yield f"N2 closed: {str(report['n2_closed']).lower()}"
    yield ""
    yield "## Static gates"
    yield ""
    yield "| gate | value |"
    yield "|---|---:|"
    for key, value in report["static_gates"].items():
        yield f"| {key} | {value} |"
    yield ""
    yield "## Hypothesis counts"
    yield ""
    h = report["hypothesis_counts"]
    yield f"- Cases: {h['case_count']}"
    yield f"- Fair-baseline comparisons: {h['fair_baseline_comparison_count']}"
    yield f"- o200k wins/losses/break-even: {h['o200k_wins']}/{h['o200k_losses']}/{h['o200k_break_even']}"
    yield ""
    yield "## Receiver static floor"
    yield ""
    r = report["receiver_static"]
    yield f"- Threshold: {r['min_score_threshold']}"
    yield f"- Minimum score: {r['min_score']}"
    yield f"- Average score: {r['average_score']}"
    if r["cases_below_threshold"]:
        yield "- Cases below threshold:"
        for case in r["cases_below_threshold"]:
            misses = ", ".join(case["misses"])
            yield f"  - {case['id']}: {case['score']} misses [{misses}]"
    else:
        yield "- Cases below threshold: none"
    yield ""
    yield "## TKAB outcomes"
    yield ""
    for outcome, count in report["tkab"]["outcomes"].items():
        yield f"- {outcome}: {count}"
    yield ""
    yield "## Live A/B requirements"
    yield ""
    for item in report["live_ab_requirements"]:
        yield f"- {item}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tokenese-n2-report")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--receiver-min-score", type=float, default=0.75)
    parser.add_argument("--strict", action="store_true", help="exit 1 unless static package is ready")
    args = parser.parse_args(argv)

    report = build_report(receiver_min_score=args.receiver_min_score)
    if args.format == "markdown":
        sys.stdout.write("\n".join(_markdown_lines(report)) + "\n")
    else:
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    if args.strict and report["status"] != "static-package-ready/live-ab-open":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
