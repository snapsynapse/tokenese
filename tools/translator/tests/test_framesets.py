"""Frameset registry telemetry.

Framesets are report-only in v0.3.x: they expose structural drift for registered
ops without changing parser acceptance, conformance levels, or TKAB outcomes.
"""

from __future__ import annotations

from tkab.checker import check_pair
from tokenese_translator.framesets import (
    load_frameset_registry,
    registered_ops,
    validate_framesets,
)


def _syn(clone: str) -> dict:
    return {
        "source_id": "SYN-FRAMESET",
        "clone_id": "SYN-FRAMESET.clone",
        "arm": "W1",
        "direction": "claude->codex",
        "author": "synthetic",
        "artifact_type": "deploy-status",
        "predicted_outcome": "win",
        "source_text": "bot deployed svc to production.",
        "clone_text": clone,
    }


def test_registry_loads_registered_ops():
    registry = load_frameset_registry()
    assert registry["schema_version"] == "tokenese-framesets-0.1"
    assert "deploy" in set(registered_ops(registry))
    assert registry["ops"]["deploy"]["signature"] == "deploy :: who what to:env when:date -> status"


def test_get_frameset_accepts_canonical_shape():
    result = validate_framesets("get @billing-api status ^3")
    assert result["checked_ops"] == ["get"]
    assert result["issues"] == []


def test_deploy_frameset_reports_missing_required_slot():
    result = validate_framesets("deploy @bot @svc ^3")
    assert any(i["code"] == "missing_required_slot" and i["severity"] == "error" for i in result["issues"])


def test_deploy_frameset_reports_noncanonical_slot_order():
    result = validate_framesets("deploy @bot @svc when:2026-06-22 to:prod ^3")
    assert any(i["code"] == "noncanonical_slot_order" for i in result["issues"])


def test_unknown_content_ops_are_not_frameset_errors():
    result = validate_framesets("customop @thing slot:value ^3")
    assert result["checked_statement_count"] == 0
    assert result["unregistered_ops"] == ["customop"]
    assert result["issues"] == []


def test_flow_consequents_are_not_positional_args():
    result = validate_framesets("run deploy @v -> done ^3")
    assert result["checked_ops"] == ["run"]
    assert not any(i["code"] == "extra_positional" for i in result["issues"])


def test_tkab_reports_framesets_without_changing_outcome():
    result = check_pair(_syn("@bot := actor:bot\n@svc := svc:api\ndeploy @bot @svc ^3"))
    assert result["outcome"] == "win-conformant"
    assert any(i["code"] == "missing_required_slot" for i in result["frameset_validation"]["issues"])
