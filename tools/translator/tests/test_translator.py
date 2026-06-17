"""End-to-end tests for the Tokenese -> English translator.

Covers:
  - Lexicon C1 audit (every admitted closed-vocabulary entry costs 1).
  - The canonical spec.md example (Supabase deploy check).
  - v0.2 constructs: @cfg handles, ev: evidentials, ^N confidence,
    distribution slots, ??slot repair, □ typed holes, †corpus anchors,
    !-imperative readback trigger, like X not Y contrast pin, drop @x.
  - Handshake, mode-switch, three-?? mode-pinning.
"""

from __future__ import annotations

import json

import pytest

from tokenese_translator import (
    Session,
    parse_line,
    parse_transcript,
    render_line,
    render_transcript,
    validate_line,
    validate_transcript,
)
from tokenese_translator.lexicon import CLOSED_VOCAB, COSTS
from tokenese_translator.validator import audit_lexicon


# ---------- L1 audit ----------

def test_c1_audit_self_consistent():
    rep = audit_lexicon()
    assert rep["admitted_count"] + rep["rejected_count"] == len(COSTS)
    for entry in rep["admitted"]:
        assert entry["anthropic_cost"] == 1
        assert entry["token"] in CLOSED_VOCAB
    for entry in rep["rejected"]:
        assert entry["anthropic_cost"] != 1


# ---------- spec.md canonical example ----------

def test_spec_canonical_example():
    transcript = (
        "@1=supabase edge fn deploy\n"
        "get? @1 status\n"
        "if fail -> get logs first-error +time\n"
    )
    sess = Session()
    out = render_transcript(transcript, session=sess)
    assert len(out) == 3
    assert sess.bindings == {"1": "supabase edge fn deploy"}
    # Binding line mentions the value.
    assert "supabase edge fn deploy" in out[0]
    # Query line resolves @1.
    assert "query: get" in out[1]
    assert '"supabase edge fn deploy"' in out[1] or "@1" in out[1]
    # Conditional line preserves the ->.
    assert "->" in out[2]


# ---------- handshake ----------

def test_handshake_and_mode():
    sess = Session()
    render_line("tokenese? v:0.1", sess)
    assert sess.handshake == "probed"
    assert sess.version == "0.1"
    render_line("tokenese ok v:0.1", sess)
    assert sess.handshake == "open"
    render_line("plain", sess)
    assert sess.mode == "plain"
    # In plain mode, lines are passed through verbatim.
    out = render_line("this is plain english passthrough", sess)
    assert out == "this is plain english passthrough"
    render_line("dense", sess)
    assert sess.mode == "dense"


# ---------- v0.2: named handles ----------

def test_named_handles_and_drop():
    sess = Session()
    render_line("@cfg=server.yaml", sess)
    assert sess.bindings == {"cfg": "server.yaml"}
    out = render_line("fix @cfg add:timeout", sess)
    assert "server.yaml" in out
    render_line("drop @cfg", sess)
    assert "cfg" not in sess.bindings


# ---------- v0.2: evidentials ----------

def test_evidentials_render_meaning():
    sess = Session()
    out = render_line("say status:up ev:obs", sess)
    assert "observed" in out
    out = render_line("say status:up ev:guess", sess)
    assert "working assumption" in out
    out = render_line("say status:up ev:heard", sess)
    assert "reported by another party" in out
    out = render_line("say status:up ev:mem", sess)
    assert "from memory" in out


# ---------- v0.2: confidence ----------

def test_confidence_slot():
    out = render_line("say ready:true ^7")
    assert "confidence 7/9" in out


# ---------- v0.2: distribution slots (ranked alternatives) ----------

def test_distribution_slots():
    out = render_line("say cause:oom^6|disk^3|net^1")
    # Order preserved, ranks assigned.
    assert "oom" in out
    assert "(rank 1" in out
    assert "disk" in out
    assert "(rank 2" in out
    assert "net" in out
    assert "(rank 3" in out


# ---------- v0.2: typed holes ----------

def test_typed_hole():
    out = render_line("set when:□date owner:□")
    assert "unfilled hole: date" in out
    assert "unfilled hole: any" in out


# ---------- v0.2: corpus anchor ----------

def test_corpus_anchor_awaits_gloss():
    out = render_line("say like †two-generals")
    assert "corpus anchor: two-generals" in out
    assert "awaiting gloss" in out


# ---------- v0.2: imperative + readback ----------

def test_imperative_readback_marker():
    out = render_line("deploy! @cfg env:prod")
    assert "imperative" in out
    assert "paraphrased" in out or "paraphrase" in out


# ---------- v0.2: addressable repair ----------

def test_addressable_repair():
    sess = Session()
    render_line("fix @cfg add:timeout", sess)
    out = render_line("?? :timeout", sess)
    assert "repair" in out.lower()
    assert "timeout" in out


# ---------- repair: three on the same content pins to plain ----------

def test_three_repair_pins_plain():
    sess = Session()
    render_line("fix bug status:fail", sess)
    render_line("?? bug", sess)
    render_line("?? bug", sess)
    render_line("?? bug", sess)
    rec = sess.repair_history.get("bug")
    assert rec is not None
    assert rec.count == 3
    assert rec.pinned_plain is True


# ---------- validator: L1/L2 across a clean transcript ----------

def test_validator_clean_transcript_passes():
    transcript = (
        "tokenese? v:0.1\n"
        "tokenese ok v:0.1\n"
        "@cfg=server.yaml\n"
        "get? @cfg status\n"
        "say cause:oom^6|disk^3 ev:obs\n"
    )
    rep = validate_transcript(transcript)
    assert rep.l1_pass
    # L2 should pass; ops like 'say', 'get', 'fix' are in ALL_OPS.
    assert rep.l2_pass


# ---------- validator: bad evidential is L1 failure ----------

def test_bad_evidential_fails_l1():
    rep = validate_line("say status:up ev:bogus")
    assert not rep.l1_pass
    assert any("evidential" in i.lower() for i in rep.issues)


# ---------- comments survive ----------

def test_comment_is_preserved():
    out = render_line("fix @cfg // bumping the timeout")
    assert "bumping the timeout" in out


# ---------- contrast pin ----------

def test_contrast_pin_rendered():
    # 'like throttle not retry' is a multi-field construct; we render the
    # three fields in order. The renderer surfaces 'like', 'throttle', 'not',
    # 'retry' as their normal English with no smoothing — which is fine
    # because the v0.2 spec leaves the surface form intentionally
    # transparent. Audit goal: a reader can recover the pin.
    out = render_line("say like throttle not retry")
    assert "like" in out
    assert "throttle" in out
    assert "not" in out
    assert "retry" in out
