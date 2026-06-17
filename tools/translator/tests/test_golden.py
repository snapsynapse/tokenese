"""Drive every golden fixture through the scorer and validate predictions.

Each fixture is a .tkn file plus a .expect.json file describing expected
results. Readback-only fixtures are a single .json file with original +
readback fields.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import pytest

from tokenese_translator import (
    classify_transcript,
    diff_readback,
    score_pair,
    Session,
    render_transcript,
)


HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.abspath(os.path.join(HERE, "..", "golden"))


def _all_tkn_fixtures():
    out = []
    for fn in sorted(os.listdir(GOLDEN)):
        if fn.endswith(".tkn"):
            base = fn[:-4]
            expect_path = os.path.join(GOLDEN, base + ".expect.json")
            tkn_path = os.path.join(GOLDEN, fn)
            if os.path.exists(expect_path):
                out.append((base, tkn_path, expect_path))
    return out


def _all_readback_fixtures():
    out = []
    for fn in sorted(os.listdir(GOLDEN)):
        if fn.endswith(".json") and not fn.endswith(".expect.json"):
            path = os.path.join(GOLDEN, fn)
            with open(path) as f:
                spec = json.load(f)
            if "original" in spec and "readback" in spec:
                out.append((fn, spec))
    return out


def _get(d: Dict[str, Any], dotted: str, default=None):
    cur: Any = d
    for k in dotted.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


@pytest.mark.parametrize("base,tkn_path,expect_path", _all_tkn_fixtures())
def test_golden_tkn(base, tkn_path, expect_path):
    with open(tkn_path) as f:
        tokenese = f.read()
    with open(expect_path) as f:
        expect_doc = json.load(f)

    # English side: either a sibling .english.txt or the empty string.
    english_path = os.path.join(GOLDEN, base + ".english.txt")
    english = open(english_path).read() if os.path.exists(english_path) else ""

    payload = score_pair(english=english, tokenese=tokenese)
    expect = expect_doc["expect"]

    for key, want in expect.items():
        # Suffix conventions: _gte, _lt, _count, _count_gte, contains_all,
        # codes_contain, session_pinned_plain_for.
        if key == "unparseable_lines_count":
            assert len(payload["unparseable_lines"]) == want, (key, want, payload)
        elif key == "unparseable_lines_count_gte":
            assert len(payload["unparseable_lines"]) >= want, (key, want, payload)
        elif key == "decoded_contains_all":
            decoded = "\n".join(payload["tokenese"]["decoded_english"])
            for needle in want:
                assert needle in decoded, (needle, decoded)
        elif key == "misparse.codes_contain":
            codes = [h["code"] for h in payload["misparse"]["hits"]]
            for needle in want:
                assert needle in codes, (needle, codes)
        elif key.endswith("_gte"):
            base_key = key[: -len("_gte")]
            actual = _get(payload, base_key)
            assert actual is not None and actual >= want, (key, want, actual, payload)
        elif key == "tokenese_anthropic_lt_english_anthropic":
            assert payload["tokenese"]["tokens"]["anthropic"] < payload["english"]["tokens"]["anthropic"], payload
        elif key == "session_pinned_plain_for":
            sess = Session()
            render_transcript(tokenese, session=sess)
            rec = sess.repair_history.get(want)
            assert rec is not None and rec.pinned_plain, sess.repair_history
        else:
            actual = _get(payload, key)
            assert actual == want, (key, want, actual, payload)


@pytest.mark.parametrize("name,spec", _all_readback_fixtures())
def test_golden_readback(name, spec):
    diff = diff_readback(spec["original"], spec["readback"]).to_dict()
    for key, want in spec["expect"].items():
        suffix = key.split(".", 1)[-1] if "." in key else key
        assert diff.get(suffix) == want, (name, key, want, diff)
