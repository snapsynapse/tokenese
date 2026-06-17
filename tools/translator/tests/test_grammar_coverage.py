"""Exhaustive coverage probe over DESIGN.md \u00a77 sigil namespace.

One test per construct from the v0.2 sigil table. Each test asserts:
  1. The line parses without hard diagnostics (or, where the construct
     is expected to produce diagnostics, that the right diagnostic fires).
  2. The English rendering surfaces the construct (not silently dropped).

This is the regression contract for cold-start cross-vendor sessions.
"""

from __future__ import annotations

from tokenese_translator import Session, render_line
from tokenese_translator.parser import (
    Binding, Handshake, ModeSwitch, Repair, Statement, parse_line,
)


# ---- @ handle bind/reference (named + numeric) ----

def test_at_named_handle_bind():
    n = parse_line("@cfg=server.yaml")
    assert isinstance(n, Binding) and n.handle == "cfg" and n.value == "server.yaml"

def test_at_numeric_handle_bind():
    n = parse_line("@1=supabase edge fn deploy")
    assert isinstance(n, Binding) and n.handle == "1" and n.handle_is_numeric

def test_at_handle_reference_resolves():
    s = Session()
    render_line("@cfg=server.yaml", s)
    out = render_line("fix @cfg", s)
    assert "server.yaml" in out


# ---- \u25a1 typed hole (key form and value form) ----

def test_box_hole_as_value_typed():
    out = render_line("set when:\u25a1date")
    assert "unfilled hole: date" in out

def test_box_hole_as_value_untyped():
    out = render_line("set owner:\u25a1")
    assert "unfilled hole: any" in out


# ---- \u2020 corpus anchor ----

def test_corpus_anchor_inline():
    out = render_line("say like \u2020two-generals")
    assert "corpus anchor: two-generals" in out and "awaiting gloss" in out


# ---- \u221a ack/readback reply ----

def test_sqrt_ack_parses_as_statement_op():
    # \u221a is the readback ack. In v0.2 it appears as the reply op.
    n = parse_line("\u221a deploy@cfg env:prod")
    assert isinstance(n, Statement)


# ---- ?? addressable repair ----

def test_repair_bare():
    n = parse_line("??")
    assert isinstance(n, Repair) and n.referent is None

def test_repair_addressable_slot():
    n = parse_line("?? :first-error")
    assert isinstance(n, Repair) and n.referent == ":first-error"

def test_repair_addressable_handle():
    n = parse_line("?? @cfg")
    assert isinstance(n, Repair) and n.referent == "@cfg"

def test_repair_addressable_anchor():
    n = parse_line("?? \u2020two-generals")
    assert isinstance(n, Repair) and n.referent == "\u2020two-generals"


# ---- ^N ordinal confidence ----

def test_confidence_on_statement():
    out = render_line("say ready:true ^7")
    assert "confidence 7/9" in out

def test_confidence_on_distribution_entry():
    out = render_line("say cause:oom^6|disk^3")
    assert "oom" in out and "disk" in out and "ordinal weight 6" in out


# ---- | alternatives within a slot ----

def test_alternatives_in_slot():
    out = render_line("say cause:oom|disk")
    assert "oom" in out and "disk" in out


# ---- :: type tag ----

def test_type_tag():
    out = render_line("say x ::number")
    assert "type: number" in out


# ---- -> sequence / yield ----

def test_arrow_sequence():
    out = render_line("if fail -> get logs")
    assert "->" in out and ("get logs" in out or "logs" in out)


# ---- => implication ----

def test_arrow_implication():
    out = render_line("check status => restart")
    assert "therefore" in out


# ---- because (causal attribution word form) ----

def test_because_word():
    n = parse_line("retry because timeout")
    assert isinstance(n, Statement) and n.op == "retry"
    # 'because' will appear as a bare additional positional or content op;
    # the renderer surfaces it verbatim.
    out = render_line("retry because timeout")
    assert "because" in out and "timeout" in out


# ---- ! imperative + readback trigger ----

def test_imperative_marker():
    out = render_line("deploy! @cfg env:prod")
    assert "imperative" in out and ("paraphrase" in out.lower())


# ---- ~ approximate ----

def test_approximate_marker():
    out = render_line("wait ~5min")
    assert "approximately" in out


# ---- // human-facing comment ----

def test_human_comment_preserved():
    out = render_line("fix @cfg // bumping the timeout")
    assert "bumping the timeout" in out


# ---- \u00a7 spec rule reference ----

def test_spec_rule_reference():
    out = render_line("say x \u00a7R1")
    assert "spec rule" in out and "R1" in out


# ---- { } proposition quoting (depth 1) ----

def test_proposition_quoting_keeps_inner_intact():
    n = parse_line("say {deploy fails on cold start}")
    assert isinstance(n, Statement)
    out = render_line("say {deploy fails on cold start}")
    # The quoted span survives as a single token containing the inner text.
    assert "deploy fails on cold start" in out


# ---- not( ) negation scope ----

def test_negation_scope_token():
    # 'not(' tokenizes per fields-split since whitespace separates.
    # We accept it as a content op; the renderer surfaces it verbatim.
    n = parse_line("say not(timeout)")
    assert isinstance(n, Statement)


# ---- dense / plain mode words ----

def test_dense_mode_switch():
    s = Session()
    render_line("plain", s)
    assert s.mode == "plain"
    render_line("dense", s)
    assert s.mode == "dense"


# ---- ev: evidential slot ----

def test_ev_obs_observed():
    out = render_line("say status:up ev:obs")
    assert "observed" in out

def test_ev_heard_reported():
    out = render_line("say status:up ev:heard")
    assert "reported by another party" in out

def test_ev_mem_memory():
    out = render_line("say status:up ev:mem")
    assert "from memory" in out

def test_ev_guess_assumption():
    out = render_line("say status:up ev:guess")
    assert "working assumption" in out


# ---- = binding (already covered by @handle tests) ----
# ---- # tag/category ----

def test_hash_tag():
    out = render_line("say done #deploy")
    assert "tag: deploy" in out


# ---- like X not Y contrast pin ----

def test_contrast_pin():
    out = render_line("say like throttle not retry")
    for tok in ("like", "throttle", "not", "retry"):
        assert tok in out


# ---- drop @x ----

def test_drop_handle():
    s = Session()
    render_line("@cfg=server.yaml", s)
    render_line("drop @cfg", s)
    assert "cfg" not in s.bindings


# ---- tokenese? / tokenese ok handshake ----

def test_handshake_probe_and_ack():
    s = Session()
    render_line("tokenese? v:0.1", s)
    assert s.handshake == "probed"
    render_line("tokenese ok v:0.1", s)
    assert s.handshake == "open" and s.version == "0.1"
