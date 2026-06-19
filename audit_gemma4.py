#!/usr/bin/env python3
"""Gemma 4 tokenizer audit for the Tokenese admissible alphabet.

Column-of-record: ``mlx-community/gemma-4-e4b-it-4bit``. This is the on-device
generator that ships in the PAICE production runtime (omlx on
localhost:8000). The 4-bit quantization affects weights, not the tokenizer;
the underlying tokenizer.json is upstream Google's Gemma 4 file.

Closes ROADMAP X5 (promote Gemma column from gemma-2 proxy to native Gemma 4).
Replaces ``audit_gemma.py`` (deleted in the same commit). The prior
``gemma_costs.json`` snapshot is preserved at the v0.3.7 tag for forensic
comparison; it is NOT carried forward.

Tokenization contract (matches the other six columns)::

    add_special_tokens=False   # no BOS, no chat template
    raw symbol cost only       # bare + space-prefixed = worst-case

Reproducible::

    pip install -r requirements.txt
    python audit_gemma4.py                            # full sweep
    python audit_gemma4.py --verify-hash <sha256>     # identity proof
    python audit_gemma4.py --probe "..."              # token-ID dump
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from audit_common import run_audit

NAME = "gemma4"

# Column-of-record. Variant choice is intentional: E4B is the on-device
# generator shipped in production. The Tokenese audit tracks what actually
# runs, not the largest sibling. See ROADMAP X5 rationale.
DEFAULT_MODEL = "mlx-community/gemma-4-e4b-it-4bit"


def _load_tokenizer(model_id: str):
    """Load the HF fast tokenizer for *model_id*.

    Uses the local Hugging Face cache (``~/.cache/huggingface/hub``) when
    present and falls through to a network fetch otherwise. Fails loudly on
    cache miss + offline.
    """
    try:
        from tokenizers import Tokenizer
        tok = Tokenizer.from_pretrained(model_id)
    except Exception as e:
        raise SystemExit(
            f"Failed to load tokenizer for {model_id}: {type(e).__name__}: {e}\n"
            "Ensure the model is in your HF cache, or set HF_HUB_OFFLINE=0 and "
            "re-run with network access."
        )
    print(f"# loaded tokenizer from {model_id}")
    return tok


def _resolve_tokenizer_json(model_id: str) -> Path | None:
    """Best-effort: locate the cached tokenizer.json file for *model_id*.

    Returns ``None`` if it can't be found (the audit still runs; the
    ``--verify-hash`` and provenance steps require it).
    """
    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return None
    path = try_to_load_from_cache(repo_id=model_id, filename="tokenizer.json")
    if path is None or path is False:
        return None
    p = Path(str(path))
    return p if p.is_file() else None


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _cmd_probe(model_id: str, probe: str) -> int:
    """Emit token IDs for *probe* under the column-of-record tokenizer.

    Useful for cross-checking against a sibling tokenizer (e.g. an Ollama
    gemma4 GGUF via /api/tokenize) when divergence diagnostics are needed.
    """
    tok = _load_tokenizer(model_id)
    enc = tok.encode(probe, add_special_tokens=False)
    out = {
        "model": model_id,
        "probe": probe,
        "ids": enc.ids,
        "tokens": enc.tokens,
        "n_tokens": len(enc.ids),
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def _cmd_verify_hash(model_id: str, expected: str) -> int:
    """Assert the cached tokenizer.json hashes to *expected* (sha256, hex).

    Per the X5 design note: this is the parity claim. If the MLX 4-bit
    conversion ships an unquantized tokenizer identical to upstream Google's
    Gemma 4 file (or to whatever value is pinned in gemma4_costs.json
    provenance), identity is proven without a second runtime.
    """
    tj = _resolve_tokenizer_json(model_id)
    if tj is None:
        print(
            f"ERROR: could not find tokenizer.json for {model_id} in the HF "
            "cache; ensure the model is downloaded.",
            file=sys.stderr,
        )
        return 2
    actual = _sha256_of(tj)
    print(f"# tokenizer.json: {tj}")
    print(f"# expected sha256: {expected}")
    print(f"# actual   sha256: {actual}")
    if actual.lower() != expected.lower():
        print("MISMATCH: tokenizer.json hash diverges from the pinned value.",
              file=sys.stderr)
        return 1
    print("OK: tokenizer identity verified.")
    return 0


def _print_provenance(model_id: str) -> None:
    """Echo a JSON envelope to stdout for the human running the audit to
    paste into ``data/source_provenance/gemma4_costs.json`` alongside the
    per-symbol payload (or for the maintainer to manually pin the hash).
    """
    tj = _resolve_tokenizer_json(model_id)
    env = {
        "_provenance": {
            "column": "gemma4",
            "model_id": model_id,
            "tokenizer_class": "tokenizers.Tokenizer",
            "tokenizer_json_path": str(tj) if tj else None,
            "tokenizer_sha256": _sha256_of(tj) if tj else None,
        }
    }
    print("# provenance envelope (paste under top-level key in costs JSON):")
    print(json.dumps(env, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--model",
        default=os.environ.get("GEMMA4_MODEL", DEFAULT_MODEL),
        help=f"HF model id (default: {DEFAULT_MODEL}; or set GEMMA4_MODEL).",
    )
    p.add_argument(
        "--verify-hash",
        metavar="SHA256",
        help="Assert the cached tokenizer.json sha256 equals SHA256 and exit.",
    )
    p.add_argument(
        "--probe",
        metavar="STRING",
        help="Tokenize STRING and print {ids, tokens} as JSON, then exit. "
        "Use to compare against sibling tokenizers (e.g. Ollama).",
    )
    args = p.parse_args(argv)

    if args.verify_hash:
        return _cmd_verify_hash(args.model, args.verify_hash)
    if args.probe is not None:
        return _cmd_probe(args.model, args.probe)

    tok = _load_tokenizer(args.model)

    def count_tokens(text: str) -> int:
        # add_special_tokens=False: same contract as the other six columns
        # (no BOS, no template). Measures raw symbol cost only.
        return len(tok.encode(text, add_special_tokens=False).ids)

    rc = run_audit(NAME, count_tokens)
    _print_provenance(args.model)
    return rc


if __name__ == "__main__":
    sys.exit(main())
