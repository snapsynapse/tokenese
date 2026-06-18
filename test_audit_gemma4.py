"""Surface tests for audit_gemma4.py.

These verify the CLI contract without loading the actual Gemma 4 tokenizer
(which requires a multi-GB local HF cache that CI runners don't have):

  - module imports with no model present (no import-time tokenizer load)
  - ``--verify-hash`` exits with a useful message when the model is not cached
  - ``--probe`` is wired and parses arguments
  - ``DEFAULT_MODEL`` points at the column-of-record string

Mirrors the test_audit_anthropic.py pattern (root-level, deliberately separate
from the tools/translator suite).

Run from the repo root: ``python -m pytest test_audit_gemma4.py -q``.
"""
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import audit_gemma4


def test_default_model_is_e4b_4bit():
    assert audit_gemma4.DEFAULT_MODEL == "mlx-community/gemma-4-e4b-it-4bit", (
        "Column-of-record must remain the production-runtime variant. Change "
        "this constant only via a roadmap-tracked column swap (see X5/L7)."
    )


def test_import_does_not_load_tokenizer():
    # Reload to prove module-import never reaches _load_tokenizer().
    import importlib
    importlib.reload(audit_gemma4)


def test_verify_hash_fails_loudly_without_cache(monkeypatch):
    # huggingface_hub.try_to_load_from_cache may not even exist in the test
    # environment; stub it to return None so we exercise the "no cache" branch.
    def _no_cache(*a, **kw):
        return None
    monkeypatch.setattr(
        audit_gemma4, "_resolve_tokenizer_json", lambda model_id: None
    )
    err = io.StringIO()
    with redirect_stderr(err):
        rc = audit_gemma4.main(
            ["--verify-hash", "deadbeef" * 8, "--model", "mlx-community/fake"]
        )
    assert rc == 2
    assert "could not find tokenizer.json" in err.getvalue()


def test_probe_requires_tokenizer():
    # With no tokenizer available, --probe should SystemExit from _load_tokenizer,
    # not silently succeed. We don't assert the exact code (depends on whether
    # `tokenizers` is installed) — only that it raises.
    err = io.StringIO()
    out = io.StringIO()
    raised = False
    try:
        with redirect_stderr(err), redirect_stdout(out):
            audit_gemma4.main(
                ["--probe", "Tokenese", "--model", "mlx-community/definitely-not-a-real-model-xyz"]
            )
    except SystemExit:
        raised = True
    assert raised, "Expected SystemExit when the model can't be loaded"
