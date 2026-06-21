from __future__ import annotations

from tokenese_translator.compression_eval import evaluate_suite, load_suite


def _case(result, case_id):
    return next(case for case in result["cases"] if case["id"] == case_id)


def _tokens(case, label, tokenizer):
    form = next(form for form in case["forms"] if form["label"] == label)
    return form["tokens"][tokenizer]


def test_compression_eval_suite_expectations_pass():
    result = evaluate_suite(load_suite())
    assert result["pass"], result


def test_old_flagship_example_is_larger_than_english_baselines():
    result = evaluate_suite(load_suite())
    case = _case(result, "old-flagship-deploy-status")

    assert _tokens(case, "verbose_english", "o200k") == 36
    assert _tokens(case, "verbose_english", "cl100k") == 37
    assert _tokens(case, "tokenese_v03_old", "o200k") == 47
    assert _tokens(case, "tokenese_v03_old", "cl100k") == 48
    assert _tokens(case, "tokenese_v03_old", "o200k") > _tokens(case, "terse_english", "o200k")
    assert _tokens(case, "tokenese_v03_old", "cl100k") > _tokens(case, "terse_english", "cl100k")


def test_narrow_structured_wins_are_measured_against_terse_english():
    result = evaluate_suite(load_suite())
    structured = _case(result, "structured-user-query")
    conditional = _case(result, "conditional-build-deploy")

    assert _tokens(structured, "compact_form", "o200k") < _tokens(structured, "terse_english", "o200k")
    assert _tokens(structured, "compact_form", "cl100k") < _tokens(structured, "terse_english", "cl100k")
    assert _tokens(conditional, "compact_form", "o200k") < _tokens(conditional, "terse_english", "o200k")
    assert _tokens(conditional, "compact_form", "cl100k") < _tokens(conditional, "terse_english", "cl100k")
