#!/usr/bin/env python3
"""Gemini tokenizer audit for the Tokenese admissible alphabet.

Model: gemini-2.5-flash via the google-genai SDK count-tokens REST endpoint.
Unlike the Hugging Face columns this is NOT offline: it requires GEMINI_API_KEY.
If the key is unset (or google-genai is not installed) the audit SKIPS CLEANLY
with exit code 0 and a warning, so it never blocks the offline CI matrix.

The REST count_tokens call returns total_tokens for the supplied content; we
measure bare and space-prefixed cost, mirroring the other columns.

Reproducible (optional):
    pip install -r requirements-optional.txt
    GEMINI_API_KEY=... python audit_gemini.py
"""
from __future__ import annotations

import os
import sys

from audit_common import run_audit

MODEL = "gemini-2.5-flash"
NAME = "gemini"


def main() -> int:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not set — skipping Gemini audit (clean skip).",
              file=sys.stderr)
        return 0
    try:
        import google.genai as genai
    except ImportError:
        print("google-genai not installed (pip install -r requirements-optional.txt)"
              " — skipping Gemini audit (clean skip).", file=sys.stderr)
        return 0

    client = genai.Client(api_key=key)

    def count_tokens(text: str) -> int:
        r = client.models.count_tokens(model=MODEL, contents=text)
        return r.total_tokens

    print(f"# {NAME}: {MODEL} (count-tokens REST)")
    return run_audit(NAME, count_tokens)


if __name__ == "__main__":
    sys.exit(main())
