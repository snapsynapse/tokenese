"""Smoke tests for the pure (MCP-independent) tool implementations.

These exercise the tool functions directly without requiring the optional
`mcp` SDK to be installed.
"""

from __future__ import annotations

import json
from pathlib import Path

from tokenese_translator import __version__, grammar_version
from tokenese_translator.mcp_server import (
    tool_check_pair,
    tool_grammar_info,
    tool_validate_framesets,
)
from tkab.checker import OUTPUT_SCHEMA_VERSION

_FIXTURES = Path(__file__).resolve().parent.parent / "tkab" / "fixtures"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


def test_tool_check_pair_win_conformant():
    pair = _load("TKAB-W1.pair.json")
    result = tool_check_pair(
        source_id=pair["source_id"],
        clone_id=pair["clone_id"],
        arm=pair["arm"],
        direction=pair["direction"],
        author=pair["author"],
        artifact_type=pair["artifact_type"],
        predicted_outcome=pair["predicted_outcome"],
        source_text=pair["source_text"],
        clone_text=pair["clone_text"],
    )
    assert result["outcome"] == "win-conformant"
    assert result["schema_version"] == OUTPUT_SCHEMA_VERSION


def test_tool_grammar_info():
    info = tool_grammar_info()
    assert info["package_version"] == __version__
    assert info["grammar_version_supported"] == grammar_version
    assert info["tkab_schema_version"] == OUTPUT_SCHEMA_VERSION
    assert info["frameset_registry"] == "tokenese-framesets-0.1"


def test_tool_validate_framesets():
    result = tool_validate_framesets("get @billing-api status ^3")
    assert result["schema_version"] == "tokenese-framesets-0.1"
    assert result["issues"] == []
