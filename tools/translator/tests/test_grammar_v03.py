"""Tests for Tokenese grammar v0.3 (GRAMMAR-v0.3.md).

v0.3 is an additive, backward-compatible bump. These tests cover the nine
enhancements (closed plain regions, declared level, repair sub-taxonomy,
negation/hedge, causal sigils, raw source quotes, the unified handle lexer,
grammar-version dispatch, and line comments) plus the two new checker
outcomes (``fail-unsupported-causation`` and ``fail-declared-level-mismatch``).

Backward compatibility for v0.2 artifacts is exercised by the existing
``test_tkab.py`` suite; here we add the v0.2-vs-v0.3 dispatch boundary cases.
"""

from __future__ import annotations

import os

from tokenese_translator.handles import Handle, consume_handle
from tokenese_translator.parser import (
    Comment,
    GrammarVersion,
    Hedged,
    LevelDeclaration,
    Negated,
    PlainBlock,
    Repair,
    SourceQuote,
    Statement,
    Unparseable,
    detect_grammar,
    parse_causal,
    parse_line,
    parse_operand,
    parse_transcript,
)
from tokenese_translator.renderer import render_transcript
from tkab.checker import check_pair, load_pair

FIXTURES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tkab", "fixtures"
)


def _nodes(text: str):
    return parse_transcript(text)


def _stmts(text: str):
    return [n for n in _nodes(text) if isinstance(n, Statement)]


def _syn(arm: str, clone: str, *, source_text: str, direction: str = "claude->codex") -> dict:
    return {
        "source_id": "SYN",
        "clone_id": "SYN.clone",
        "arm": arm,
        "direction": direction,
        "author": "synthetic",
        "artifact_type": "deploy-status",
        "predicted_outcome": "win" if arm == "W1" else "lose",
        "source_text": source_text,
        "clone_text": clone,
    }


# ---- (1) Closed plain regions -------------------------------------------

def test_plain_block_closed_form():
    text = (
        "^grammar:v0.3\n"
        "get @x status ^3\n"
        "^plain<<<\n"
        "Free-form English narrative.\n"
        "Second line of prose.\n"
        ">>>^plain"
    )
    blocks = [n for n in _nodes(text) if isinstance(n, PlainBlock)]
    assert len(blocks) == 1
    assert blocks[0].text == "Free-form English narrative.\nSecond line of prose."
    assert blocks[0].start_line == 3
    assert blocks[0].end_line == 6


def test_plain_block_content_not_classified_as_statements():
    text = (
        "^grammar:v0.3\n"
        "^plain<<<\n"
        "get @x status ^3\n"  # looks like dense, but it is inside a plain block
        ">>>^plain"
    )
    # No Statement nodes: the dense-looking line is captured verbatim.
    assert not [n for n in _nodes(text) if isinstance(n, Statement)]


def test_plain_block_backward_compat_v02_has_no_block():
    # Without ^grammar:v0.3, the opener line is just an (unparseable) statement,
    # never a PlainBlock; v0.2 behavior is untouched.
    text = "^plain<<<\nsome text\n>>>^plain"
    assert not [n for n in _nodes(text) if isinstance(n, PlainBlock)]


# ---- (2) Declared level --------------------------------------------------

def test_declare_level_parses():
    node = parse_line("^declare:level=L2", grammar="v0.3")
    assert isinstance(node, LevelDeclaration)
    assert node.level == "L2"


def test_declare_level_must_be_first():
    text = "^grammar:v0.3\nget @x status ^3\n^declare:level=L2"
    nodes = _nodes(text)
    late = [n for n in nodes if isinstance(n, Unparseable)]
    assert late and "first non-comment" in late[0].reason


def test_declare_level_first_is_accepted():
    text = "^grammar:v0.3\n^declare:level=L2\nget @x status ^3"
    decls = [n for n in _nodes(text) if isinstance(n, LevelDeclaration)]
    assert len(decls) == 1 and decls[0].level == "L2"


# ---- (3) Repair sub-taxonomy --------------------------------------------

def test_repair_kind_statement():
    assert parse_line("??", grammar="v0.3").repair_kind == "repair-statement"


def test_repair_kind_handle():
    r = parse_line("??@cfg", grammar="v0.3")
    assert r.repair_kind == "repair-handle"
    assert r.target == "@cfg"


def test_repair_kind_token():
    r = parse_line("?? sometoken", grammar="v0.3")
    assert r.repair_kind == "repair-token"
    assert r.target == "sometoken"


def test_repair_explained_captures_reason():
    r = parse_line("??: needs more detail", grammar="v0.3")
    assert r.repair_kind == "repair-explained"
    assert r.reason == "needs more detail"


# ---- (4) Negation / hedge -----------------------------------------------

def test_negation_prefix():
    op = parse_operand("!@deploy")
    assert isinstance(op, Negated)
    assert op.handle == "deploy"
    assert op.inner is None


def test_hedge_suffix():
    op = parse_operand("@deploy?")
    assert isinstance(op, Hedged)
    assert op.handle == "deploy"


def test_negation_and_hedge_compose():
    op = parse_operand("!@deploy?")
    assert isinstance(op, Negated)
    assert isinstance(op.inner, Hedged)
    assert op.handle == "deploy"


def test_bare_handle_is_unchanged():
    assert parse_operand("@deploy") == "@deploy"
    assert parse_operand("plainword") == "plainword"


def test_negation_renders_as_not():
    text = "^grammar:v0.3\n@deploy := release\nsay !@deploy ^3"
    rendered = " ".join(render_transcript(text))
    assert "not" in rendered.lower()


def test_hedge_renders_as_possibly():
    text = "^grammar:v0.3\n@deploy := release\nsay @deploy? ^3"
    rendered = " ".join(render_transcript(text))
    assert "possibly" in rendered.lower()


# ---- (5) Causal sigils ---------------------------------------------------

def test_parse_causal_constructors():
    assert parse_causal("a", ">>>", "b").kind == "sequence"
    assert parse_causal("a", "*>>", "b").kind == "stipulated_causation"
    assert parse_causal("a", "?>>", "b").kind == "hypothesized_causation"


def test_causal_sigil_captured_in_statement():
    stmts = _stmts("^grammar:v0.3\nsay deadlock *>> retry-storm")
    slots = stmts[0].slots
    assert any(s.key == "*>>" and s.value == ("deadlock", "retry-storm") for s in slots)


def test_causal_sequence_renders_without_duplicate_operand():
    # `say @a >>> @b` must not double-render @a (target == sequence left).
    rendered = render_transcript("^grammar:v0.3\n@a := x\n@b := y\nsay @a >>> @b ^3")[-1]
    assert "then" in rendered
    assert rendered.count("@a") == 1


def test_causal_sigils_inactive_in_v02():
    # The W1 fixture's `>>` flow token must remain a bare token in v0.2.
    stmts = _stmts("done deploy >> no rollback ^3")
    assert not any(s.key in (">>>", "*>>", "?>>") for s in stmts[0].slots)


def test_stipulated_causation_admissible_with_source():
    clone = "^grammar:v0.3\n@alpha := svc:alpha\n@beta := svc:beta\nsay @alpha *>> @beta ^3"
    src = "Service alpha holds a lock which causes service beta to stall."
    result = check_pair(_syn("W1", clone, source_text=src))
    assert result["outcome"] == "win-conformant"
    assert all(e["supported_by_source"] for e in result["causal_events"])


def test_stipulated_causation_unsupported_fails():
    clone = "^grammar:v0.3\n@alpha := svc:alpha\n@beta := svc:beta\nsay @alpha *>> @beta ^3"
    src = "Service alpha and service beta run independently."
    result = check_pair(_syn("W1", clone, source_text=src))
    assert result["outcome"] == "fail-unsupported-causation"
    assert result["unsupported_causation"]


def test_hypothesized_causation_always_admissible():
    clone = "^grammar:v0.3\n@alpha := svc:alpha\n@beta := svc:beta\nsay @alpha ?>> @beta ^3"
    src = "Service alpha and service beta run independently."
    result = check_pair(_syn("W1", clone, source_text=src))
    assert result["outcome"] == "win-conformant"


def test_causal_sigils_do_not_trip_derivation_regex():
    # `*>>` is not `->`/`=>`; an L1 expected-to-LOSE clone using a causal sigil
    # should not be misread as an illegal derivation by the marker regex.
    clone = (
        "^grammar:v0.3\n"
        "@a := service:a\n"
        "@b := service:b\n"
        "say @a >>> @b ^3"
    )
    result = check_pair(
        _syn("L1", clone, source_text="A then B, sequentially.", direction="codex->claude")
    )
    assert result["outcome"] != "fail-illegal-derivation"


# ---- (6) Raw source quotes ----------------------------------------------

def test_source_quote_parses():
    text = '^grammar:v0.3\n"""verbatim source text"""'
    quotes = [n for n in _nodes(text) if isinstance(n, SourceQuote)]
    assert len(quotes) == 1
    assert quotes[0].text == "verbatim source text"


def test_source_quote_in_source_is_no_conflict():
    clone = '^grammar:v0.3\n"""pods are healthy"""'
    src = "The pods are healthy and latency is nominal."
    result = check_pair(_syn("W1", clone, source_text=src))
    assert not result["source_authority_conflict"]


def test_source_quote_not_in_source_conflicts():
    clone = '^grammar:v0.3\n"""the database was wiped"""'
    src = "No rollback was triggered; the deploy succeeded."
    result = check_pair(_syn("W1", clone, source_text=src))
    assert result["outcome"] == "fail-source-authority-conflict"
    assert any(
        c["type"] == "source_quote_not_in_source"
        for c in result["source_authority_conflict"]
    )


# ---- (7) Unified handle lexer -------------------------------------------

def test_handle_lexer_kebab():
    parsed = consume_handle("@billing-api", 0)
    assert parsed is not None
    handle, end = parsed
    assert handle == Handle(name="billing-api")
    assert end == len("@billing-api")


def test_handle_lexer_snake():
    parsed = consume_handle("@billing_api rest", 0)
    assert parsed is not None
    handle, end = parsed
    assert handle.name == "billing_api"
    assert end == len("@billing_api")


def test_handle_lexer_negation_and_hedge():
    handle, end = consume_handle("!@svc?", 0)
    assert handle == Handle(name="svc", negated=True, hedged=True)
    assert end == len("!@svc?")


def test_handle_lexer_rejects_bare_at():
    assert consume_handle("@", 0) is None
    assert consume_handle("plain", 0) is None
    # leading '!' without a following '@' is not a handle
    assert consume_handle("!foo", 0) is None


# ---- (8) Grammar-version dispatch ---------------------------------------

def test_grammar_version_declaration_v03():
    text = "^grammar:v0.3\nget @x status ^3"
    assert detect_grammar(text) == "v0.3"
    versions = [n for n in _nodes(text) if isinstance(n, GrammarVersion)]
    assert versions and versions[0].version == "v0.3"


def test_grammar_version_absent_means_v02():
    assert detect_grammar("get @x status ^3") == "v0.2"


def test_grammar_version_unsupported_refuses_artifact():
    text = "^grammar:v9.9\nget @x status ^3"
    nodes = _nodes(text)
    assert len(nodes) == 1
    assert isinstance(nodes[0], Unparseable)
    assert "unsupported grammar version" in nodes[0].reason


def test_grammar_header_after_content_is_not_dispatched():
    # A ^grammar line that is not first does not change dispatch (stays v0.2),
    # so the header line itself parses under v0.2 (as an unparseable op).
    text = "get @x status ^3\n^grammar:v0.3"
    assert detect_grammar(text) == "v0.2"


# ---- (9) Line comments ---------------------------------------------------

def test_line_comment_at_line_start():
    node = parse_line("# this is a comment", grammar="v0.3")
    assert isinstance(node, Comment)
    assert node.text == "this is a comment"


def test_inline_hash_is_not_a_comment():
    # '#' mid-line is a tag slot, not a comment.
    node = parse_line("get @x status #tag", grammar="v0.3")
    assert isinstance(node, Statement)
    assert any(s.key == "#" for s in node.slots)


def test_comment_does_not_count_as_first_non_comment():
    text = "^grammar:v0.3\n# banner\n^declare:level=L2\nget @x status ^3"
    decls = [n for n in _nodes(text) if isinstance(n, LevelDeclaration)]
    assert len(decls) == 1


# ---- Checker: declared-level mismatch ------------------------------------

def test_declared_level_mismatch_fails():
    clone = "^grammar:v0.3\n^declare:level=L1\n@x := svc:x/staging\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["outcome"] == "fail-declared-level-mismatch"
    assert result["declared_level"] == "L1"
    assert result["conformance_level"] != "L1"


def test_declared_level_match_no_extra_outcome():
    clone = "^grammar:v0.3\n^declare:level=L3\n@x := svc:x/staging\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["outcome"] == "win-conformant"
    assert result["declared_level"] == "L3"


def test_no_declared_level_is_none():
    clone = "^grammar:v0.3\n@x := svc:x/staging\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["declared_level"] is None


# ---- Schema / provenance for v0.3 ----------------------------------------

def test_schema_version_is_1_1():
    clone = "^grammar:v0.3\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["schema_version"] == "tkab-check-1.1"


def test_grammar_version_reported_in_output():
    clone = "^grammar:v0.3\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["grammar_version"] == "v0.3"
    assert result["provenance"]["grammar_version_detected"] == "v0.3"


def test_repair_kinds_aggregate_present_when_zero():
    clone = "^grammar:v0.3\nget @x status ^3"
    result = check_pair(_syn("W1", clone, source_text="x deploy status."))
    assert result["repair_kinds"] == {
        "repair-token": 0,
        "repair-statement": 0,
        "repair-handle": 0,
        "repair-explained": 0,
    }


# ---- v0.3 fixtures -------------------------------------------------------

def test_fixture_w1_v03_wins():
    pair = load_pair(os.path.join(FIXTURES, "TKAB-W1.v03.pair.json"))
    assert check_pair(pair)["outcome"] == "win-conformant"


def test_fixture_l1_v03_plain_success():
    pair = load_pair(os.path.join(FIXTURES, "TKAB-L1.v03.pair.json"))
    assert check_pair(pair)["outcome"] == "l1-plain-success"


def test_fixture_unsupported_causation():
    pair = load_pair(os.path.join(FIXTURES, "TKAB-W1-FAIL-unsupported-causation.v03.pair.json"))
    assert check_pair(pair)["outcome"] == "fail-unsupported-causation"


def test_fixture_declared_level_mismatch():
    pair = load_pair(os.path.join(FIXTURES, "TKAB-W1-FAIL-declared-level-mismatch.v03.pair.json"))
    assert check_pair(pair)["outcome"] == "fail-declared-level-mismatch"


def test_fixture_negation_hedge_wins():
    pair = load_pair(os.path.join(FIXTURES, "TKAB-W1-NEGATION-HEDGE.v03.pair.json"))
    assert check_pair(pair)["outcome"] == "win-conformant"


# ---- v0.2 fixtures unchanged under the new schema ------------------------

def test_v02_fixtures_still_classify_as_before():
    expected = {
        "TKAB-W1.pair.json": "win-conformant",
        "TKAB-L1.pair.json": "l1-plain-success",
        "TKAB-W1-FAIL-malformed.pair.json": "fail-unparseable",
        "TKAB-W1-FAIL-source-conflict.pair.json": "fail-source-authority-conflict",
        "TKAB-L1-FAIL-illegal-derivation.pair.json": "fail-illegal-derivation",
    }
    for name, outcome in expected.items():
        result = check_pair(load_pair(os.path.join(FIXTURES, name)))
        assert result["outcome"] == outcome, name
        assert result["grammar_version"] == "v0.2", name
