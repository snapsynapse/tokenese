# Example — validate a transcript

Never treat a transcript as authoritative until the deterministic checker has
scored it. The checker is a scorer, not a generator or repairer: same input,
same JSON, byte for byte. Invoke it on a paired `(source, clone)` fixture:

```
tokenese-check --pair <file.json> --pretty
```

or the MCP `check_pair` tool. The output conforms to the `tkab-check-1.1`
schema.

## A v0.2 fixture

`tools/translator/tkab/fixtures/TKAB-W1.pair.json` is the deploy-status W1 arm
(expected-to-win) with no `^grammar:` header — frozen v0.2 allocation. The
clone for this fixture is example 2 in `encode_decode.md`.

```
tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.pair.json --pretty
```

Key fields of the result:

```json
{
  "schema_version": "tkab-check-1.1",
  "source_id": "TKAB-W1",
  "arm": "W1",
  "outcome": "win-conformant",
  "conformance_level": "L3",
  "declared_level": null,
  "grammar_version": "v0.2",
  "repair_kinds": {"repair-token": 0, "repair-statement": 0, "repair-handle": 0, "repair-explained": 0},
  "causal_events": []
}
```

Validates fixture: TKAB-W1.pair.json -> win-conformant

## A v0.3 fixture

`tools/translator/tkab/fixtures/TKAB-W1.v03.pair.json` is the same deploy-status
arm authored to v0.3, adding the `*>>` stipulated causation (corroborated by the
source's "which causes"). The clone is example 3 in `encode_decode.md`.

```
tokenese-check --pair tools/translator/tkab/fixtures/TKAB-W1.v03.pair.json --pretty
```

Key fields of the result:

```json
{
  "schema_version": "tkab-check-1.1",
  "source_id": "TKAB-W1-v03",
  "arm": "W1",
  "outcome": "win-conformant",
  "conformance_level": "L3",
  "declared_level": null,
  "grammar_version": "v0.3",
  "repair_kinds": {"repair-token": 0, "repair-statement": 0, "repair-handle": 0, "repair-explained": 0},
  "causal_events": [
    {"kind": "stipulated_causation", "left": "@migration", "right": "@cache", "line_no": 12, "supported_by_source": true}
  ]
}
```

Validates fixture: TKAB-W1.v03.pair.json -> win-conformant

## The key fields

- `outcome` — one of the 13 closed outcomes (`references/outcome_enum.md`).
  Decided by the first-match-wins order (`references/decision_order.md`).
- `conformance_level` — `L0` | `L1` | `L2` | `L3` achieved by the clone.
- `declared_level` — the `^declare:level=L` value, or null when undeclared. If
  it disagrees with `conformance_level`, the outcome is
  `fail-declared-level-mismatch`.
- `grammar_version` — detected artifact grammar: `v0.2` (no header) or `v0.3`.
- `repair_kinds` — by-kind aggregate of `??` events, present even when zero.
  Three or more total repair events ⇒ `fail-three-repairs`.
- `causal_events` — `>>>` / `*>>` / `?>>` events with `supported_by_source`. An
  uncorroborated `*>>` ⇒ `fail-unsupported-causation`.
