#!/usr/bin/env python3
"""Qwen tokenizer audit for the Tokenese admissible alphabet.

Model: Qwen/Qwen2.5-7B (Hugging Face, ungated). Tokenizer is the Qwen2 BPE
used across the Qwen2/Qwen2.5 family. No API key required; the tokenizer.json
is fetched once from the Hub and cached locally.

Reproducible: pip install -r requirements.txt && python audit_qwen.py
"""
from __future__ import annotations

import sys

from audit_common import run_audit

MODEL = "Qwen/Qwen2.5-7B"
NAME = "qwen"


def load_tokenizer():
    from tokenizers import Tokenizer
    return Tokenizer.from_pretrained(MODEL)


def main() -> int:
    tok = load_tokenizer()

    def count_tokens(text: str) -> int:
        # add_special_tokens=False: measure content cost only, excluding any
        # BOS/EOS the model prepends, so columns are comparable to o200k/tiktoken.
        return len(tok.encode(text, add_special_tokens=False).ids)

    print(f"# {NAME}: {MODEL}")
    return run_audit(NAME, count_tokens)


if __name__ == "__main__":
    sys.exit(main())
