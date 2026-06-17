"""Security regression tests for audit_anthropic.py.

These verify the credential-handling contract without making real API calls:
  - the module imports with no ANTHROPIC_API_KEY set (no import-time KeyError)
  - main() exits cleanly with a helpful message when the key is absent
  - the API key never appears in stdout/stderr or the output JSON

Run from the repo root: `python -m pytest test_audit_anthropic.py -q`.
Kept at repo root, separate from the tools/translator/ suite.
"""
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import audit_anthropic


SECRET = "sk-ant-test-DEADBEEF0123456789abcdef"


def test_import_without_key_does_not_raise(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import importlib
    # Re-import to prove module load never touches os.environ at top level.
    importlib.reload(audit_anthropic)


def test_main_exits_helpfully_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    err = io.StringIO()
    with redirect_stderr(err):
        try:
            audit_anthropic.main()
        except SystemExit as e:
            assert e.code == 2
        else:
            raise AssertionError("main() should SystemExit when key is absent")
    assert "ANTHROPIC_API_KEY is not set" in err.getvalue()


def test_no_credential_leaked_in_output(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    syms = ["@", "#", "$"]
    syms_path = tmp_path / "tokenese_syms.json"
    syms_path.write_text(json.dumps(syms))
    out_path = tmp_path / "anthropic_costs.json"

    calls = []

    def fake_count(text, key):
        calls.append((text, key))
        return 1

    real_open = open

    def routed_open(path, *args, **kwargs):
        if path == "/tmp/tokenese_syms.json":
            return real_open(syms_path, *args, **kwargs)
        if path == "anthropic_costs.json":
            return real_open(out_path, *args, **kwargs)
        return real_open(path, *args, **kwargs)

    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(audit_anthropic, "count", fake_count), \
            mock.patch("builtins.open", routed_open), \
            redirect_stdout(out), redirect_stderr(err):
        audit_anthropic.main()

    # The key was passed through to count(), but never printed anywhere.
    assert any(key == SECRET for _, key in calls)
    assert SECRET not in out.getvalue()
    assert SECRET not in err.getvalue()
    assert SECRET not in out_path.read_text()
