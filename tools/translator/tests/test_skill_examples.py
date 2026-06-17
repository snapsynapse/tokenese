"""Verify every Tokenese block we ship in the skill bundle is valid Tokenese.

This is the load-bearing test for ``skills/tokenese/``: it proves that every
fenced ``tokenese`` code block in ``skills/tokenese/examples/*.md`` parses under
the v0.3 grammar with no ``Unparseable`` nodes, and that any block annotated
with an expected checker outcome scores as claimed.

The examples live at the repo root (``skills/tokenese/examples/``), not inside
the translator package, so they are discovered via a path relative to
``__file__``.

Annotations recognized in the markdown (on a line shortly after a block):

* ``Validates to: <outcome>`` — build a pair from the immediately preceding
  ``tokenese`` block and assert ``check_pair`` returns ``<outcome>``. The arm
  defaults to ``W1``; an outcome beginning ``l1-`` or ``fail-no-plain``/
  ``fail-mixed``/``fail-illegal`` implies the ``L1`` arm.
* ``Validates fixture: <name> -> <outcome>`` — load
  ``tkab/fixtures/<name>`` and assert ``check_pair`` returns ``<outcome>``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tokenese_translator.parser import Unparseable, parse_transcript
from tkab.checker import check_pair

# repo_root/tools/translator/tests/this_file -> repo_root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLES_DIR = _REPO_ROOT / "skills" / "tokenese" / "examples"
_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tkab" / "fixtures"

_BLOCK_RE = re.compile(r"```tokenese\n(.*?)```", re.DOTALL)
_VALIDATES_TO_RE = re.compile(r"Validates to:\s*([a-z0-9-]+)")
_VALIDATES_FIXTURE_RE = re.compile(
    r"Validates fixture:\s*([\w.-]+)\s*->\s*([a-z0-9-]+)"
)

# Outcomes that only make sense on the expected-to-LOSE (L1) arm.
_L1_OUTCOMES = {
    "l1-plain-success",
    "fail-no-plain-exit",
    "fail-mixed-exit",
    "fail-illegal-derivation",
}


def _example_files():
    assert _EXAMPLES_DIR.is_dir(), f"examples dir not found: {_EXAMPLES_DIR}"
    return sorted(_EXAMPLES_DIR.glob("*.md"))


def _blocks(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    return [m.group(1) for m in _BLOCK_RE.finditer(text)]


def _all_blocks():
    out = []
    for f in _example_files():
        for i, block in enumerate(_blocks(f)):
            out.append(pytest.param(block, id=f"{f.name}#{i}"))
    return out


def test_examples_dir_present():
    files = _example_files()
    assert files, "no example markdown files discovered"


def test_at_least_one_tokenese_block():
    total = sum(len(_blocks(f)) for f in _example_files())
    assert total >= 5, f"expected several tokenese blocks, found {total}"


@pytest.mark.parametrize("block", _all_blocks())
def test_block_parses_with_no_unparseable(block):
    nodes = parse_transcript(block)
    bad = [n for n in nodes if isinstance(n, Unparseable)]
    assert not bad, "Unparseable nodes in shipped example: " + "; ".join(
        f"{n.reason!r} (raw={n.raw!r})" for n in bad
    )
    assert nodes, "example block parsed to zero nodes"


def _validates_to_cases():
    cases = []
    for f in _example_files():
        text = f.read_text(encoding="utf-8")
        blocks = list(_BLOCK_RE.finditer(text))
        for m in _VALIDATES_TO_RE.finditer(text):
            # Find the tokenese block immediately preceding this annotation.
            preceding = [b for b in blocks if b.end() <= m.start()]
            assert preceding, f"'Validates to:' in {f.name} with no preceding block"
            block = preceding[-1].group(1)
            outcome = m.group(1)
            cases.append(pytest.param(block, outcome, id=f"{f.name}:{outcome}"))
    return cases


@pytest.mark.parametrize("block,expected_outcome", _validates_to_cases())
def test_validates_to_annotation(block, expected_outcome):
    arm = "L1" if expected_outcome in _L1_OUTCOMES else "W1"
    pair = {
        "source_id": "SKILL-EXAMPLE",
        "direction": "a->b",
        "source_text": "skill example source",
        "clone_text": block,
        "arm": arm,
        "predicted_outcome": "win" if arm == "W1" else "lose",
    }
    result = check_pair(pair)
    assert result["outcome"] == expected_outcome, (
        f"expected {expected_outcome}, got {result['outcome']}"
    )


def _validates_fixture_cases():
    cases = []
    for f in _example_files():
        text = f.read_text(encoding="utf-8")
        for m in _VALIDATES_FIXTURE_RE.finditer(text):
            cases.append(
                pytest.param(
                    m.group(1), m.group(2), id=f"{f.name}:{m.group(1)}"
                )
            )
    return cases


@pytest.mark.parametrize("fixture_name,expected_outcome", _validates_fixture_cases())
def test_validates_fixture_annotation(fixture_name, expected_outcome):
    path = _FIXTURES_DIR / fixture_name
    assert path.is_file(), f"fixture not found: {path}"
    pair = json.loads(path.read_text(encoding="utf-8"))
    result = check_pair(pair)
    assert result["outcome"] == expected_outcome, (
        f"{fixture_name}: expected {expected_outcome}, got {result['outcome']}"
    )
