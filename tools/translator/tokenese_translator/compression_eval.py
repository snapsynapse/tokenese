"""Whole-message compression benchmark evaluator.

This is intentionally separate from grammar conformance. It measures complete
messages against fair baselines so compression claims cannot be inferred from
lexicon audits or parser success.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Iterable

from .token_count import count_cl100k, count_o200k


DEFAULT_SUITE = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "evals",
        "compression_cases.json",
    )
)


@dataclass(frozen=True)
class CountedForm:
    label: str
    text: str
    o200k: int | None
    cl100k: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "text": self.text,
            "tokens": {
                "o200k": self.o200k,
                "cl100k": self.cl100k,
            },
        }


def _count(label: str, text: str) -> CountedForm:
    return CountedForm(
        label=label,
        text=text,
        o200k=count_o200k(text),
        cl100k=count_cl100k(text),
    )


def _compare(forms: dict[str, CountedForm], lhs: str, op: str, rhs: str) -> dict[str, Any]:
    by_tokenizer: dict[str, dict[str, Any]] = {}
    passed = True
    for tokenizer in ("o200k", "cl100k"):
        left = getattr(forms[lhs], tokenizer)
        right = getattr(forms[rhs], tokenizer)
        if left is None or right is None:
            ok = False
            delta = None
            ratio = None
        else:
            if op == "lt":
                ok = left < right
            elif op == "lte":
                ok = left <= right
            elif op == "gt":
                ok = left > right
            elif op == "gte":
                ok = left >= right
            else:
                raise ValueError(f"unsupported comparison op: {op}")
            delta = right - left
            ratio = round(left / right, 4) if right else None
        passed = passed and ok
        by_tokenizer[tokenizer] = {
            "lhs": left,
            "rhs": right,
            "delta_rhs_minus_lhs": delta,
            "ratio_lhs_over_rhs": ratio,
            "pass": ok,
        }
    return {
        "lhs": lhs,
        "op": op,
        "rhs": rhs,
        "pass": passed,
        "by_tokenizer": by_tokenizer,
    }


def _relative_counts(
    forms: dict[str, CountedForm],
    candidates: list[str],
    baselines: list[str],
) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for candidate in candidates:
        for baseline in baselines:
            by_tokenizer: dict[str, dict[str, Any]] = {}
            for tokenizer in ("o200k", "cl100k"):
                cand_count = getattr(forms[candidate], tokenizer)
                base_count = getattr(forms[baseline], tokenizer)
                if cand_count is None or base_count is None:
                    delta = None
                    ratio = None
                    savings_percent = None
                else:
                    delta = base_count - cand_count
                    ratio = round(cand_count / base_count, 4) if base_count else None
                    savings_percent = (
                        round((base_count - cand_count) * 100 / base_count, 2)
                        if base_count
                        else None
                    )
                by_tokenizer[tokenizer] = {
                    "candidate": cand_count,
                    "baseline": base_count,
                    "delta_baseline_minus_candidate": delta,
                    "ratio_candidate_over_baseline": ratio,
                    "savings_percent": savings_percent,
                }
            metrics.append(
                {
                    "candidate": candidate,
                    "baseline": baseline,
                    "by_tokenizer": by_tokenizer,
                }
            )
    return metrics


def _all_counts_available(forms: dict[str, CountedForm]) -> bool:
    return all(
        getattr(form, tokenizer) is not None
        for form in forms.values()
        for tokenizer in ("o200k", "cl100k")
    )


def evaluate_suite(suite: dict[str, Any]) -> dict[str, Any]:
    cases = []
    all_pass = True
    all_counts_available = True
    for case in suite["cases"]:
        forms = {
            form["label"]: _count(form["label"], form["text"])
            for form in case["forms"]
        }
        comparisons = [
            _compare(forms, item["lhs"], item["op"], item["rhs"])
            for item in case.get("expect", [])
        ]
        case_pass = all(item["pass"] for item in comparisons)
        all_pass = all_pass and case_pass
        counts_available = _all_counts_available(forms)
        all_counts_available = all_counts_available and counts_available
        baselines = case.get("baselines", [])
        candidates = case.get("candidates", [])
        cases.append(
            {
                "id": case["id"],
                "description": case.get("description", ""),
                "idea_ids": case.get("idea_ids", []),
                "test_kind": case.get("test_kind", "token-count"),
                "behavioral_metrics": case.get("behavioral_metrics", []),
                "pass": case_pass,
                "counts_available": counts_available,
                "forms": [forms[form["label"]].to_dict() for form in case["forms"]],
                "comparisons": comparisons,
                "relative_counts": _relative_counts(forms, candidates, baselines),
            }
        )
    return {
        "schema_version": suite.get("schema_version", "tokenese-compression-eval-1.0"),
        "baseline_policy": suite.get("baseline_policy", ""),
        "tokenizers": ["o200k", "cl100k"],
        "ideas": suite.get("ideas", []),
        "suspected_payoff_rank": suite.get("suspected_payoff_rank", []),
        "synergy_groups": suite.get("synergy_groups", []),
        "counts_available": all_counts_available,
        "pass": all_pass,
        "cases": cases,
    }


def load_suite(path: str = DEFAULT_SUITE) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _markdown_rows(result: dict[str, Any]) -> Iterable[str]:
    yield "| case | form | o200k | cl100k |"
    yield "|---|---:|---:|---:|"
    for case in result["cases"]:
        for form in case["forms"]:
            tokens = form["tokens"]
            yield (
                f"| {case['id']} | {form['label']} | "
                f"{tokens['o200k']} | {tokens['cl100k']} |"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokenese-compression-eval",
        description="Run whole-message Tokenese compression benchmark fixtures.",
    )
    parser.add_argument("--suite", default=DEFAULT_SUITE, help="compression_cases.json path")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--strict", action="store_true", help="exit 1 if any expectation fails")
    args = parser.parse_args(argv)

    result = evaluate_suite(load_suite(args.suite))
    if args.format == "markdown":
        sys.stdout.write("\n".join(_markdown_rows(result)) + "\n")
    else:
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if args.strict and (not result["pass"] or not result["counts_available"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
