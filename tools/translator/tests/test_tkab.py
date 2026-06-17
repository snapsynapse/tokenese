"""Tests for the TKAB per-pair scorer (schema tkab-check-1.0).

Covers every stable outcome string and the five shipped fixtures, plus the
source-preservation invariant (R1.5), provenance pinning, and a CLI round-trip.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from tkab.checker import check_pair, load_pair

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tkab", "fixtures")


def _fixture(name: str) -> dict:
    return load_pair(os.path.join(FIXTURES, name))


def _check_fixture(name: str) -> dict:
    return check_pair(_fixture(name))


def _synthetic(arm: str, clone_text: str, *, source_text: str = "x deploy status.", direction: str = "claude->codex") -> dict:
    return {
        "source_id": "SYN",
        "clone_id": "SYN.clone",
        "arm": arm,
        "direction": direction,
        "author": "synthetic",
        "artifact_type": "deploy-status",
        "predicted_outcome": "win" if arm == "W1" else "lose",
        "source_text": source_text,
        "clone_text": clone_text,
    }


# 1
def test_schema_version_stable():
    result = _check_fixture("TKAB-W1.pair.json")
    assert result["schema_version"] == "tkab-check-1.0"


# 2
def test_w1_fixture_wins():
    assert _check_fixture("TKAB-W1.pair.json")["outcome"] == "win-conformant"


# 3
def test_l1_fixture_plain_success():
    assert _check_fixture("TKAB-L1.pair.json")["outcome"] == "l1-plain-success"


# 4
def test_w1_malformed_unparseable():
    assert _check_fixture("TKAB-W1-FAIL-malformed.pair.json")["outcome"] == "fail-unparseable"


# 5
def test_w1_source_conflict():
    result = _check_fixture("TKAB-W1-FAIL-source-conflict.pair.json")
    assert result["outcome"] == "fail-source-authority-conflict"
    assert result["source_authority_conflict"], "expected a logged conflict record"


# 6
def test_l1_illegal_derivation():
    assert _check_fixture("TKAB-L1-FAIL-illegal-derivation.pair.json")["outcome"] == "fail-illegal-derivation"


# 7
def test_three_repairs_fail():
    clone = "get status ^3\n?? @x\n?? @x\n?? @x"
    assert check_pair(_synthetic("W1", clone))["outcome"] == "fail-three-repairs"


# 8
def test_no_plain_exit_fail():
    clone = "@svc := service:A\nget @svc status ^3\nsay lock held ^3"
    assert check_pair(_synthetic("L1", clone, direction="codex->claude"))["outcome"] == "fail-no-plain-exit"


# 9
def test_mixed_exit_fail():
    clone = (
        "@svc := service:A\n"
        "plain\n"
        "Plain-English narrative describing the deadlock root cause.\n"
        "dense\n"
        "get @svc status ^3"
    )
    assert check_pair(_synthetic("L1", clone, direction="codex->claude"))["outcome"] == "fail-mixed-exit"


# 10
def test_source_preserved_verbatim():
    pair = _fixture("TKAB-W1.pair.json")
    result = check_pair(pair)
    assert result["source_text"] == pair["source_text"]


# 11
def test_provenance_includes_sha():
    prov = _check_fixture("TKAB-W1.pair.json")["provenance"]
    for key in ("prd_027_sha", "ab_suite_sha", "checker_version", "spec_sha"):
        assert key in prov, f"provenance missing {key}"


# 12
def test_cli_pair_roundtrip(tmp_path):
    fixture_path = os.path.join(FIXTURES, "TKAB-W1.pair.json")
    out_path = tmp_path / "result.json"
    rc = subprocess.call(
        [sys.executable, "-m", "tkab.cli", "--pair", fixture_path, "--out", str(out_path), "--pretty"]
    )
    assert rc == 0
    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["outcome"] == "win-conformant"
    assert result["schema_version"] == "tkab-check-1.0"
