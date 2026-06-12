# Security Policy

## Scope

Tokenese is a specification plus audit scripts. The primary security surface is the protocol design itself, not running services.

Design-level security properties (see INTENT.md invariant 1):

- Token-space only. The spec forbids embedding, KV-cache, or latent-channel exchange between models. Everything crossing the wire is inspectable plain text.
- No hidden channels by construction. A conforming Tokenese transcript is human-auditable; the `//` comment sigil marks human-facing annotations explicitly.
- Repair protocol (`??`, `plain`) prevents a party from being trapped in a mode it cannot parse.

## Reporting a vulnerability

Report protocol-level issues (e.g. a grammar construct that enables smuggling instructions past a human auditor, symbol-table poisoning across session boundaries, or handshake spoofing) by opening a GitHub issue. For sensitive reports, email founder@snapsynapse.com instead.

Expect acknowledgment within 7 days.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (draft) | Yes |
