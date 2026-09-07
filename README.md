# Tokenese

> Archived 2026-07-25. This repository is preserved as a post-mortem of Tokenese's negative results and unfinished validation. Read [POST-MORTEM.md](POST-MORTEM.md) first: it is the authoritative closing document. The spec and tools below remain as evidence and remain runnable, but the project is concluded and unmaintained.

Tokenese was an attempt at a token-native interlingua for LLM-to-LLM communication, intended to be more compressed and more precise than human prose, measured in real tokenizer tokens. The flagship example cost more tokens than terse English; the broader behavioral claim remained unproven. See [POST-MORTEM.md](POST-MORTEM.md).

Canonical home: https://tokenese.org/
Spec: [spec.md](spec.md) v0.3 (final). Grammar: [GRAMMAR-v0.3.md](GRAMMAR-v0.3.md).
Vision: [INTENT.md](INTENT.md)

## Canonical URL

https://tokenese.org/

## What problem it tried to solve

LLM-to-LLM communication defaults to verbose human prose. The bet was that a token-native interlingua, with every lexicon element admitted by a reproducible cross-tokenizer audit, could beat prose on both cost and precision. The flagship syntax cost more tokens than terse English. The combined compression and accuracy claim remained unproven. POST-MORTEM.md carries the full accounting.

## Who this is for now

Anyone designing DSL syntax, identifiers, or structured output formats that LLMs will emit: the cross-tokenizer audit methodology here remains reproducible and useful. And anyone tempted to design a machine language for agents: read the post-mortem first.

## Why it existed

The founding metaphor: LLMs conforming to human language is like watching film in black and white. Human languages carry overhead shaped by human constraints: serial speech, social hedging, redundancy against noisy air. The flagship compression claim failed measurement. That result did not establish an optimal encoding of meaning or resolve the broader behavioral hypothesis.

## How it works

- Token-space only. Plain text crosses the wire; each party tokenizes independently. No embeddings, no shared latents, no vendor lock.
- Tokenizer-audited lexicon. A symbol enters the vocabulary only if it costs 1 token, worst case, in every certified tokenizer (currently OpenAI o200k_base + Anthropic). Audit scripts included; claims are reproducible.
- Compression from structure, not glyphs. Fixed field grammar, controlled vocabulary, in-band symbol table for repeated referents. Measurement rule: individual token costs require audit; whole-message savings require separate measurement.
- Self-repairing. `??` misparse signal and a plain-English escape hatch are mandatory.

## Quick taste

No measured example ever shipped, and none will. The original illustrative
example was removed on 2026-06-18 when token-counting on the certified
tokenizers reversed its compression claim (the Tokenese form was 1.3x larger
than the English, not 2.5x smaller). That finding, reproduced on two tokenizers,
is the negative result documented in [POST-MORTEM.md](POST-MORTEM.md), which includes the
reproduction script.

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

Archived 2026-07-25. Release v0.3.9 (2026-06-23) is the final release. The N2 live cross-family A/B experiment, the project's self-declared kill-criterion, was designed but never run. Limited adoption and the lack of a validated advantage supported archiving, without settling the technical hypothesis. [POST-MORTEM.md](POST-MORTEM.md) is the closing document.

## Contributing

The repo is archived and read-only. Corrections that come with measurements are welcome via the contact on https://tokenese.org/. The historical admission criteria remain in [INTENT.md](INTENT.md) and [CONTRIBUTING.md](CONTRIBUTING.md); the short version was always: claims must be measured, not asserted.

## License

Code: MIT. Specification text: CC BY 4.0. See [LICENSE](LICENSE) and [LICENSE-SPEC](LICENSE-SPEC).

## For agents

Coding agents should read [AGENTS.md](AGENTS.md) first.

Last updated: 2026-09-07 (conclusion amended; archive retained)
