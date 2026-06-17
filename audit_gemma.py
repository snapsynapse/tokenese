#!/usr/bin/env python3
"""Gemma tokenizer audit for the Tokenese admissible alphabet.

Target model per ROADMAP X2: google/gemma-4-9b. As of 2026-06-17 Gemma 4 is
not released on the Hugging Face Hub (repo 404s). Per the brief we use Gemma 2
as a proxy and label the column accordingly. google/gemma-2-9b is GATED, so we
fall back to unsloth/gemma-2-9b, an ungated mirror shipping the identical Gemma
SentencePiece BPE tokenizer (256k vocab). Override GEMMA_MODEL to force a model.

COLUMN LABEL: gemma-2 (proxy for gemma-4 pending release)

Reproducible: pip install -r requirements.txt && python audit_gemma.py
"""
from __future__ import annotations

import os
import sys

from audit_common import run_audit

PREFERRED = "google/gemma-4-9b"        # not yet released as of 2026-06-17
PROXY_GATED = "google/gemma-2-9b"      # gated; needs HF_TOKEN + license accept
PROXY_MIRROR = "unsloth/gemma-2-9b"    # ungated mirror, same tokenizer
NAME = "gemma"


def load_tokenizer():
    from tokenizers import Tokenizer
    override = os.environ.get("GEMMA_MODEL")
    candidates = [override] if override else [PREFERRED, PROXY_GATED, PROXY_MIRROR]
    last_err = None
    for model in candidates:
        try:
            tok = Tokenizer.from_pretrained(model)
            print(f"# loaded tokenizer from {model}")
            return tok
        except Exception as e:  # unreleased / gated / network -> try next
            last_err = e
            print(f"# could not load {model}: {type(e).__name__}", file=sys.stderr)
    raise SystemExit(f"Failed to load any Gemma tokenizer. Last error: {last_err}")


def main() -> int:
    tok = load_tokenizer()

    def count_tokens(text: str) -> int:
        # add_special_tokens=False: Gemma prepends a BOS (2); exclude it so we
        # measure content cost only, comparable to o200k/tiktoken.
        return len(tok.encode(text, add_special_tokens=False).ids)

    print(f"# {NAME}: gemma-2 (proxy for gemma-4 pending release)")
    return run_audit(NAME, count_tokens)


if __name__ == "__main__":
    sys.exit(main())
