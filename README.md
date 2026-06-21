# Tokenese

A token-native interlingua for LLM-to-LLM communication. More compressed AND more precise than any human language, measured in real tokenizer tokens, not characters.

Canonical home: https://tokenese.org/
Spec: [spec.md](spec.md) v0.3 (current). Grammar: [GRAMMAR-v0.3.md](GRAMMAR-v0.3.md).
Vision: [INTENT.md](INTENT.md)
Assistant guide: [assistant-guide.txt](assistant-guide.txt) (GuideCheck human-verifiable-assistant-guide profile 0.6.0, Level 4): a bounded, approval-gated guide for an assistant to install Tokenese and reproduce the audit. Verify before acting at https://guidecheck.org/verify

## Canonical URL

https://tokenese.org/

## What problem it solves

LLM-to-LLM communication defaults to verbose human prose, which wastes tokens and loses precision; Tokenese gives agents a token-native interlingua whose lexicon is admitted only when each symbol survives a reproducible cross-tokenizer audit.

## Who this is for

Teams building multi-agent systems who want machine-to-machine messages that are more compressed and more precise than natural language, with every vocabulary symbol verified by a reproducible tokenizer audit rather than asserted.

## Why

LLMs conforming to human language is like watching film in black and white. Human languages carry overhead shaped by human constraints: serial speech, social hedging, redundancy against noisy air. Tokenese brings color to machine-to-machine communication: richer, more informative exchanges compressed into a smaller, token-native format.

## How it works

- Token-space only. Plain text crosses the wire; each party tokenizes independently. No embeddings, no shared latents, no vendor lock.
- Tokenizer-audited lexicon. A symbol enters the vocabulary only if it costs 1 token, worst case, in every certified tokenizer (currently OpenAI o200k_base + Anthropic). Audit scripts included; claims are reproducible.
- Compression from structure, not glyphs. Fixed field grammar, controlled vocabulary, in-band symbol table for repeated referents. Empirical finding: common English words are already optimal tokens; exotic Unicode usually is not.
- Self-repairing. `??` misparse signal and a plain-English escape hatch are mandatory.

## Quick taste

A measured example is pending. The previous illustrative example was removed on
2026-06-18: token-counting on the certified tokenizers contradicted its
compression claim (the Tokenese form was larger than the English, not smaller).
A replacement will ship only with reproducible token counts on every certified
tokenizer, measured against *terse* English rather than verbose prose. See the
spec "Example exchange" section and the changelog for the finding.

## Tools

- **Translator + scorer:** [tools/translator/](tools/translator/) - base Tokenese->English translator (originally built for Turnfile) plus the deterministic TKAB per-pair scorer for the W1+L1 mini-pilot.
- **CLI:** `tokenese-check --pair fixture.json --pretty` after `pip install -e tools/translator`.
- **MCP server:** `python -m tokenese_translator.mcp_server` exposes parse / validate / validate_framesets / to-english / check-pair / score-pair tools.
- **Frameset registry:** [framesets.json](framesets.json) - report-only typed slot signatures for common ops. The registry feeds structural telemetry without changing parser acceptance or checker outcomes.
- **Conformance:** the checker reports mismatches (R5.3); it never generates or repairs. See [CONFORMANCE.md](CONFORMANCE.md).

## Reproduce the audit

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python audit_symbols.py
ANTHROPIC_API_KEY=... .venv/bin/python audit_anthropic.py
```

## Status

Grammar v0.3 current. Release v0.3.8 is a patch tooling release: the seven-column tokenizer audit is complete (the Gemma column is now native Gemma 4 E4B, the on-device PAICE production generator). The base translator, golden fixtures, TKAB deterministic scorer, grammar-v0.3 features, MCP smoke tests, and report-only frameset registry pass 144/144 tests; the repo-root security and Gemma 4 audit-surface tests add 7 more (151 total). A cross-surface portable skill ships at [skills/tokenese/](skills/tokenese/). The hosted assistant guide is anchored at GuideCheck Level 4 via a DNS TXT record at `_assistant-guide.tokenese.org`, with a daily drift-detection CI job. The validating A/B experiment between Claude and Codex remains the open downstream measurement; see [tools/translator/tkab/AUDIT_CARD.md](tools/translator/tkab/AUDIT_CARD.md).

## Contributing

Contributions welcome; every change passes the admission criteria in [INTENT.md](INTENT.md). See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: claims must be measured, not asserted.

## License

Code: MIT. Specification text: CC BY 4.0. See [LICENSE](LICENSE) and [LICENSE-SPEC](LICENSE-SPEC).

## For agents

Coding agents should read [AGENTS.md](AGENTS.md) first.

Last updated: 2026-06-17
