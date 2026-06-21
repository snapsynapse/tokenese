"""Blind receiver eval for Tokenese candidate payloads.

The live runner sends only the candidate payload plus generic decoding
instructions to an OpenAI-compatible chat endpoint. It then scores whether the
receiver preserved expected terms. This is intentionally a second-level smoke
test, not a final semantic-accuracy benchmark.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_SUITE = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "evals",
        "receiver_cases.json",
    )
)


SYSTEM_PROMPT = """You are a receiver in a Tokenese-style LLM-to-LLM communication eval.
Decode the payload into ordinary English meaning without using any hidden answer key.
Preserve bindings, abbreviations, evidence labels, confidence values, ranked alternatives,
negative sense anchors, repair requests, and conditional branches.
Return only JSON with keys: paraphrase, bindings, actions, evidence, ranks, repairs, ambiguities."""


def load_suite(path: str = DEFAULT_SUITE) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def score_text(text: str, expected_terms: list[str]) -> dict[str, Any]:
    normalized = _normalize(text)
    hits = []
    misses = []
    for term in expected_terms:
        if _normalize(term).strip() in normalized:
            hits.append(term)
        else:
            misses.append(term)
    score = len(hits) / len(expected_terms) if expected_terms else 1.0
    return {
        "score": round(score, 4),
        "hits": hits,
        "misses": misses,
        "hit_count": len(hits),
        "expected_count": len(expected_terms),
    }


def _chat_completion(
    base_url: str,
    model: str,
    candidate: str,
    *,
    api_key: str | None = None,
    timeout_seconds: int = 120,
) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": candidate},
            ],
            "temperature": 0.1,
            "seed": 42,
            "max_tokens": 2048,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:500]}") from exc
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not text:
        raise RuntimeError("chat endpoint returned empty content")
    return text


def evaluate_static(suite: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in suite["cases"]:
        scored = score_text(case["candidate"], case["expected_terms"])
        cases.append(
            {
                "id": case["id"],
                "candidate": case["candidate"],
                "expected_terms": case["expected_terms"],
                "candidate_term_score": scored,
            }
        )
    return {
        "schema_version": suite.get("schema_version", "tokenese-receiver-eval-1.0"),
        "mode": "static-candidate-term-check",
        "cases": cases,
    }


def evaluate_live(
    suite: dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    cases = []
    for case in suite["cases"]:
        output = _chat_completion(base_url, model, case["candidate"], api_key=api_key)
        scored = score_text(output, case["expected_terms"])
        cases.append(
            {
                "id": case["id"],
                "candidate": case["candidate"],
                "receiver_output": output,
                "score": scored,
            }
        )
    return {
        "schema_version": suite.get("schema_version", "tokenese-receiver-eval-1.0"),
        "mode": "live-receiver",
        "model": model,
        "base_url": base_url,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tokenese-receiver-eval")
    parser.add_argument("--suite", default=DEFAULT_SUITE)
    parser.add_argument("--live", action="store_true", help="call an OpenAI-compatible chat endpoint")
    parser.add_argument("--base-url", default=os.environ.get("TRANSLATE_API_BASE", "http://localhost:8000"))
    parser.add_argument("--model", default=os.environ.get("TRANSLATE_MODEL", "gemma-4-e4b-it-4bit"))
    parser.add_argument("--api-key", default=os.environ.get("TRANSLATE_API_KEY", ""))
    parser.add_argument("--min-score", type=float, default=0.75)
    args = parser.parse_args(argv)

    suite = load_suite(args.suite)
    try:
        if args.live:
            result = evaluate_live(
                suite,
                base_url=args.base_url,
                model=args.model,
                api_key=args.api_key or None,
            )
            scores = [case["score"]["score"] for case in result["cases"]]
        else:
            result = evaluate_static(suite)
            scores = [case["candidate_term_score"]["score"] for case in result["cases"]]
    except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if all(score >= args.min_score for score in scores) else 1


if __name__ == "__main__":
    raise SystemExit(main())
