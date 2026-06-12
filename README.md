# Tokenese

A token-native interlingua for LLM-to-LLM communication. More compressed AND more precise than any human language, measured in real tokenizer tokens, not characters.

Canonical home: https://tokenese.org/
Spec: [spec.md](spec.md) v0.1.0 (draft)
Vision: [INTENT.md](INTENT.md)

## Why

LLMs conforming to human language is like watching film in black and white. Human languages carry overhead shaped by human constraints: serial speech, social hedging, redundancy against noisy air. Tokenese brings color to machine-to-machine communication: richer, more informative exchanges compressed into a smaller, token-native format.

## How it works

- Token-space only. Plain text crosses the wire; each party tokenizes independently. No embeddings, no shared latents, no vendor lock.
- Tokenizer-audited lexicon. A symbol enters the vocabulary only if it costs 1 token, worst case, in every certified tokenizer (currently OpenAI o200k_base + Anthropic). Audit scripts included; claims are reproducible.
- Compression from structure, not glyphs. Fixed field grammar, controlled vocabulary, in-band symbol table for repeated referents. Empirical finding: common English words are already optimal tokens; exotic Unicode usually is not.
- Self-repairing. `??` misparse signal and a plain-English escape hatch are mandatory.

## Quick taste

English (~55 tokens):

> Could you check whether the deploy of the edge function to the Supabase project succeeded, and if it failed, look at the logs and tell me the first error with a timestamp?

Tokenese (~20 tokens):

```
@1=supabase edge fn deploy
get? @1 status
if fail -> get logs first-error +time
```

## Reproduce the audit

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python audit_symbols.py
ANTHROPIC_API_KEY=... .venv/bin/python audit_anthropic.py
```

## Status

v0.1.0 draft. The validating experiment (live A/B between Claude and Codex measuring tokens, task success, and misparse-retry rate) has not run yet. See spec.md open questions.

## License

Code: MIT. Specification text: CC BY 4.0. See [LICENSE](LICENSE) and [LICENSE-SPEC](LICENSE-SPEC).

Last updated: 2026-06-12
