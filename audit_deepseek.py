#!/usr/bin/env python3
"""DeepSeek tokenizer audit for the Tokenese admissible alphabet.

Model: deepseek-ai/DeepSeek-V3 (Hugging Face, ungated). Uses the DeepSeek-V3
byte-level BPE tokenizer. No API key required; tokenizer.json is fetched once
from the Hub and cached locally.

Reproducible: pip install -r requirements.txt && python audit_deepseek.py
"""
from __future__ import annotations

import sys

from audit_common import run_audit

MODEL = "deepseek-ai/DeepSeek-V3"
NAME = "deepseek"


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
