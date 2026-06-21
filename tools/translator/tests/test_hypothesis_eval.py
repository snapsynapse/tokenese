from __future__ import annotations

import os

from tokenese_translator.compression_eval import evaluate_suite, load_suite
from tokenese_translator.receiver_eval import score_text


HERE = os.path.dirname(os.path.abspath(__file__))
HYPOTHESIS_SUITE = os.path.abspath(
    os.path.join(
        HERE,
        "..",
        "tokenese_translator",
        "evals",
        "hypothesis_cases.json",
    )
)


def test_hypothesis_suite_covers_all_ten_ideas():
    suite = load_suite(HYPOTHESIS_SUITE)
    idea_ids = {idea["id"] for idea in suite["ideas"]}
    case_ideas = {
        idea_id
        for case in suite["cases"]
        for idea_id in case.get("idea_ids", [])
        if isinstance(idea_id, int)
    }

    assert idea_ids == set(range(1, 11))
    assert idea_ids <= case_ideas


def test_hypothesis_suite_records_rank_and_synergies():
    suite = load_suite(HYPOTHESIS_SUITE)
    case_idea_sets = {tuple(case["idea_ids"]) for case in suite["cases"]}

    assert suite["suspected_payoff_rank"][0]["idea_ids"] == [8, 9, 10]
    assert len(suite["synergy_groups"]) >= 5
    assert any(group["idea_ids"] == [1, 3, 7] for group in suite["synergy_groups"])
    assert any(group["idea_ids"] == [2, 5, 6] for group in suite["synergy_groups"])
    for group in suite["synergy_groups"]:
        assert tuple(group["idea_ids"]) in case_idea_sets, group
    assert any(len(group["idea_ids"]) == 2 for group in suite["synergy_groups"])


def test_hypothesis_suite_evaluates_token_counts_for_every_candidate():
    result = evaluate_suite(load_suite(HYPOTHESIS_SUITE))

    assert result["counts_available"]
    assert len(result["cases"]) >= 14
    for case in result["cases"]:
        assert case["counts_available"], case["id"]
        assert case["relative_counts"], case["id"]
        for comparison in case["relative_counts"]:
            for tokenizer in ("o200k", "cl100k"):
                counts = comparison["by_tokenizer"][tokenizer]
                assert isinstance(counts["candidate"], int)
                assert isinstance(counts["baseline"], int)


def test_hypothesis_cases_are_exploratory_not_claim_gates():
    result = evaluate_suite(load_suite(HYPOTHESIS_SUITE))
    losing_cases = {
        case["id"]
        for case in result["cases"]
        for comparison in case["relative_counts"]
        if comparison["by_tokenizer"]["o200k"]["savings_percent"] < 0
    }

    assert "I4-dense-table-status" in losing_cases
    assert "I6-tokenizer-native-operators" in losing_cases
    assert "S3-tokenizer-native-grammar-redesign" in losing_cases


def test_receiver_term_scorer_detects_missing_expected_terms():
    result = score_text("status up observed confidence 8", ["status", "observed", "rollback"])

    assert result["score"] == 0.6667
    assert result["hits"] == ["status", "observed"]
    assert result["misses"] == ["rollback"]
