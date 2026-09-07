# Tokenese: negative results and an unfinished validation

Archived: 2026-07-25. Amended: 2026-09-07.
Status: archived and unmaintained. The spec, tooling, and audit scripts remain
available as experimental artifacts.

## Verdict

Tokenese failed to demonstrate its founding promise: cross-vendor LLM
communication that is both more compact and more precise than natural language.
Its flagship compression claim was falsified. The live A/B experiment needed
to evaluate accuracy and repair costs was never completed.

Archiving remains justified by the negative measurement, weak adoption signal,
and unresolved costs of teaching, integration, and semantic coordination.
The evidence supports stopping investment; it does not establish that every
designed agent language must fail. Narrower benefits remain unproven.

## What Tokenese claimed

The original INTENT.md proposed a plain-text interlingua that would be denser
and more precise than human language. The spec targeted 2.5-4x compression.
Its explicit failure criterion was live misparse-retry accounting: if retries
consumed the token savings, the design had failed.

Lexicon audits and parser conformance were necessary checks, but neither
could establish this combined behavioral claim.

## What measurement showed

On 2026-06-18, token counting contradicted the flagship example's estimated
saving. These counts were reproduced on 2026-09-07:

| Form | o200k_base | cl100k_base |
|---|---|---|
| Verbose English | 36 | 37 |
| Terse English | 18 | 19 |
| Tokenese v0.3 | 47 | 48 |

The claimed figures, approximately 55 English tokens versus 22 Tokenese
tokens, had been estimated rather than measured. Tokenese actually cost about
1.3x the verbose English and 2.5-2.6x the terse English on this example.
The result disproves that compression claim, not the efficiency of every
possible designed representation.

The subsequent precision pivot explored repeated references, evidence labels,
confidence, ranked alternatives, and repair state. Re-running the exploratory
suite yields 13 token-count wins, four losses, and one tie on o200k_base across
18 comparisons. These are hand-authored candidates, not a representative
sample of successful live exchanges.

Baseline choice materially affects those results. In the symbol-table case,
the supplied English repeats the full referent and costs 84 tokens against
44 for the candidate. Stating the subject once reduces the English to 38
(cl100k_base: 92, 45, and 40 respectively). The shorter wording preserves the
requested operations on inspection; receiver equivalence has not been tested.

Shortened English used for that check:

> For pcegwmrsxzzznowwnksu Supabase edge-function deploy: check status; if failed, return first log error with timestamp; then report owner and retry state.

The reported static receiver floor, minimum 0.85 against a 0.75 threshold,
measures expected-term coverage in the candidate text. It does not measure
receiver comprehension, correct bindings, negation, or task accuracy. Earlier
receiver smoke tests informed syntax revisions but did not complete the
planned comparative evaluation.

## Why the project stopped

The archive review recorded zero stars, forks, and external adopters; five
unique visitors in the preceding 14 days; and an unpublished package. These
are historical observations from 2026-07-25, not current measurements or a
controlled test of demand.

That limited adoption signal and the lack of a validated advantage supported
ending investment. They did not answer the live A/B experiment's technical
question. N2 was closed administratively without being run; the original
behavioral failure criterion was not experimentally established.

## Historical evidence and its limits

Related work identifies recurring obstacles, but the projects below tested
different objectives. Their outcomes are not repeated tests of Tokenese's
compression-and-accuracy hypothesis.

| Comparison | Evidence | Implication for Tokenese |
|---|---|---|
| FIPA-ACL | Its formal semantics left implementation conformance testing unresolved. [Specification](https://fipa.org/specs/fipa00037/PC00037E.html) | Defining meaning does not prove that implementations preserve it. |
| Controlled natural languages | Caterpillar replaced an unenforceable approach with narrower translation goals; General Motors' controlled authoring reached production. [Survey](https://aclanthology.org/J14-1005.pdf) | Outcomes are mixed; enforceability and a bounded use case matter. |
| RDF and SPARQL | Wikimedia operates a SPARQL query service using RDF. [Implementation](https://doc.wikimedia.org/wikidata-query-rdf/query-service-parent/index.html) | Specialized adoption contradicts a blanket failure verdict without establishing universal suitability. |
| Agora | It combines natural language with standardized and generated routines according to communication frequency. [Paper](https://arxiv.org/abs/2410.11905) | Reuse and specialization are relevant alternatives to a universal replacement language. |
| LLMLingua | It reports prompt-compression gains on specified datasets. [Paper](https://arxiv.org/abs/2310.05736) | It provides comparative evidence for another approach, not a test of Tokenese. |

This history supports skepticism about whether broad benefits can repay
teaching, integration, semantic coordination, and adoption costs. Tokenese
provided no compelling evidence that it overcame those obstacles. Specialized
success would support its tested workload, not the original general claim.

The former lineage table mixed translation systems, logical languages,
knowledge representation, audio transport, and LLM research into a single
failure narrative. This amendment replaces that narrative with sourced
comparisons. Historical analogy informs the investment decision; it cannot
substitute for the missing experiment.

## Alternatives and unresolved costs

1. Whole-message token counts matter. Cheap vocabulary elements did not make
   the flagship message cheap. This does not establish that English is an
   optimal encoding of meaning.
2. Schemas and constrained decoding can enforce output structure. They do not
   ensure correct values or shared interpretation. [Structured Outputs limitations](https://openai.com/index/introducing-structured-outputs-in-the-api/)
3. Teaching and integration costs must be counted for every approach. Shared
   setup may amortize over repeated exchanges; Tokenese did not establish
   an end-to-end advantage after setup, readbacks, repairs, and fallbacks.
4. Caching and other compression methods belong in a workload-specific
   comparison. Falling token prices alone neither prove nor disprove a
   language's relative efficiency.

## What survives

- Reproducible cross-tokenizer audits for evaluating vocabulary and syntax.
- The measured failure of the flagship compression claim.
- A translator, validator, scorer, MCP interface, and archived test suite
  (163 passing tests reported at closure).
- Exploratory fixtures and syntax observations that can inform future tests,
  with their baseline and semantic-validation limits made explicit.

## Conditions for reconsideration

A small benchmark win alone would not justify reopening. Reconsideration
would require a concrete recurring workload, evidence of a material benefit,
and an explanation of which historical obstacle the approach overcomes.
A bounded evaluation would need to:

1. Freeze candidates and success thresholds before testing on held-out tasks
   across independent receiver families.
2. Compare against carefully shortened English and compact structured data
   carrying equivalent information.
3. Count setup, messages, readbacks, repairs, fallbacks, and failures; measure
   meaning preservation and successful task completion.
4. Demonstrate a useful advantage after integration costs. Any conclusion
   applies to the tested workload and conditions.

Until such evidence exists, the repository remains archived. The unresolved
hypothesis does not itself justify further investment.

## Timeline

- 2026-06-12: repo provisioned. Spec v0.1.0, dual-tokenizer audit.
- 2026-06-16: repo public, tokenese.org live, landing page ships.
- 2026-06-17: seven-column audit complete, GuideCheck Level 4 anchoring.
- 2026-06-18: pre-publish validation falsifies the flagship example. The
  announcement post is pulled. Premise re-examination measured and recorded.
- 2026-06-22: precision-pivot ratified into spec and INTENT.
- 2026-06-23: v0.3.9 released. Phase A closed. Phase B (live A/B) opened.
- 2026-06-25: Phase B stalls at fixture authorship. Implementation work stops.
- 2026-07-25: viability teardown run. Baseline: 0 stars, 0 forks, 5 unique
  visitors in 14 days, 0 external adopters, package never published. Archive
  verdict taken. This document written. Repo archived.
- 2026-09-07: conclusion corrected; counts reproduced and baseline sensitivity
  checked. Archive retained; the live A/B remains unrun.

## Reproduce the headline result

Literal
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./.venv/bin/python - <<'PY'
import tiktoken
o = tiktoken.get_encoding("o200k_base"); c = tiktoken.get_encoding("cl100k_base")
def m(s): return len(o.encode(s)), len(c.encode(s))
english = ("Could you check whether the deploy of the edge function to the "
           "Supabase project succeeded, and if it failed, look at the logs and "
           "tell me the first error with a timestamp?")
tokenese = ("^grammar:v0.3\n^declare:level=L2\n@svc := supabase/edge-fn\n"
            "@svc.deploy >>> @svc.status\n!@svc.ok? *>> get @svc.logs.first-error +ts")
terse = ("Check Supabase edge-function deploy status. If failed, return first "
         "log error with timestamp.")
print("verbose english", m(english))   # (36, 37)
print("tokenese v0.3  ", m(tokenese))  # (47, 48)
print("terse english  ", m(terse))     # (18, 19)
PY
```
The full lexicon audit remains reproducible via `audit_symbols.py` and
siblings; see README.

## Provenance and correction

The original post-mortem was compiled on 2026-07-25 from repository artifacts,
token measurements, recorded GitHub traffic, and a historical landscape review.
The 2026-09-07 amendment reproduces the headline counts, examines the
[exploratory fixtures](tools/translator/tokenese_translator/evals/hypothesis_cases.json)
and [receiver scoring](tools/translator/tokenese_translator/receiver_eval.py),
and replaces broad historical assertions with the sources linked above.

The amendment corrects the inference from a failed example to a failed
category, the substitution of adoption figures for behavioral validation,
and the description of static term coverage as comprehension. The archive
decision is retained. No live A/B result is claimed.
