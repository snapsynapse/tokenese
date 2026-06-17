#!/usr/bin/env python3
"""Llama 3 tokenizer audit for the Tokenese admissible alphabet.

Model: meta-llama/Llama-3-8B (Hugging Face, GATED). Because the canonical repo
requires accepting Meta's license (and an HF_TOKEN), this audit falls back to
NousResearch/Meta-Llama-3-8B, an ungated mirror that ships the *identical*
Llama 3 tiktoken-derived BPE tokenizer (128k vocab). Set HF_TOKEN and override
LLAMA_MODEL to use the gated original.

Reproducible: pip install -r requirements.txt && python audit_llama.py
"""
from __future__ import annotations

import os
import sys

from audit_common import run_audit

PREFERRED = "meta-llama/Llama-3-8B"
FALLBACK = "NousResearch/Meta-Llama-3-8B"  # ungated mirror, same tokenizer
NAME = "llama"


def load_tokenizer():
    from tokenizers import Tokenizer
    override = os.environ.get("LLAMA_MODEL")
    candidates = [override] if override else [PREFERRED, FALLBACK]
    last_err = None
    for model in candidates:
        try:
            tok = Tokenizer.from_pretrained(model)
            print(f"# loaded tokenizer from {model}")
            return tok
        except Exception as e:  # gated / network / not found -> try next
            last_err = e
            print(f"# could not load {model}: {type(e).__name__}", file=sys.stderr)
    raise SystemExit(f"Failed to load any Llama 3 tokenizer. Last error: {last_err}")


def main() -> int:
    tok = load_tokenizer()

    def count_tokens(text: str) -> int:
        # add_special_tokens=False: Llama 3 prepends a BOS (128000); exclude it
        # so we measure content cost only, comparable to o200k/tiktoken.
        return len(tok.encode(text, add_special_tokens=False).ids)

    print(f"# {NAME}: Llama 3 (preferred {PREFERRED}, fallback {FALLBACK})")
    return run_audit(NAME, count_tokens)


if __name__ == "__main__":
    sys.exit(main())
