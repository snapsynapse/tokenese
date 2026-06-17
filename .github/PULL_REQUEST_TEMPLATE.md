## Summary

What this changes and why.

## Admission criteria (INTENT.md)

- [ ] Lexicon additions ship with audit evidence (worst-case 1 token in every certified tokenizer)
- [ ] Grammar changes preserve parse determinism (before/after parses included)
- [ ] Compression claims show token counts before and after on the example corpus
- [ ] No change increases misparse-retry rate in A/B (or it is reverted)

## Checklist

- [ ] CHANGELOG.md updated
- [ ] Version + date propagated to every surface that displays them (spec.md, CONFORMANCE.md, relationships.yaml, ontology.json) if this is a release
- [ ] Audit scripts run clean if the lexicon changed
