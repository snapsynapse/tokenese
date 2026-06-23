from __future__ import annotations

from tokenese_translator.n2_report import build_report


def test_n2_report_is_static_ready_but_live_open():
    report = build_report()

    assert report["schema_version"] == "tokenese-n2-static-package-0.1"
    assert report["roadmap_item"] == "N2"
    assert report["status"] == "static-package-ready/live-ab-open"
    assert report["n2_closed"] is False
    assert "Live multi-family receiver A/B" in report["closure_reason"]


def test_n2_report_summarizes_non_cherry_picked_hypotheses():
    report = build_report()
    counts = report["hypothesis_counts"]

    assert counts["counts_available"]
    assert counts["case_count"] >= 18
    assert counts["o200k_wins"] > 0
    assert counts["o200k_losses"] > 0
    assert any(
        item["case"] == "I1-symbol-table-amortization"
        for item in counts["top_o200k_wins"]
    )


def test_n2_report_passes_receiver_static_floor():
    report = build_report()
    receiver = report["receiver_static"]

    assert receiver["threshold_pass"] is True
    assert receiver["min_score"] >= receiver["min_score_threshold"]
    assert receiver["cases_below_threshold"] == []


def test_n2_report_includes_tkab_fixture_outcomes():
    report = build_report()
    tkab = report["tkab"]

    assert tkab["fixture_count"] >= 10
    assert tkab["outcomes"]["win-conformant"] >= 1
    assert tkab["outcomes"]["l1-plain-success"] >= 1
    assert any(
        result["outcome"] == "fail-source-authority-conflict"
        for result in tkab["results"]
    )
