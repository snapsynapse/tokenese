# Example — encode and decode (round trips)

This skill ships **no generator**: the English→Tokenese direction is out of
scope (ROADMAP / scoring-only scope lock). You author the dense form by hand
against grammar v0.3. The decode direction (Tokenese→English) is what the
reference translator does — call it to check your reading:

- CLI: `tokenese-translate <file.tkn>`
- MCP: the `to_english` tool on `tokenese_translator.mcp_server`

Each example below shows the natural English, the hand-authored v0.3 Tokenese,
and the translator's round-trip decode.

## 1. The README hero example

Natural English (~55 tokens):

> Could you check whether the deploy of the edge function to the Supabase
> project succeeded, and if it failed, look at the logs and tell me the first
> error with a timestamp?

Hand-authored Tokenese v0.3 (~22 tokens):

```tokenese
^grammar:v0.3
^declare:level=L2
@svc := supabase/edge-fn
@svc.deploy >>> @svc.status
!@svc.ok? *>> get @svc.logs.first-error +ts
```

Decode (via `tokenese-translate`), abbreviated:

> bind @svc = "supabase/edge-fn"; @svc.deploy then @svc.status; query:
> !@svc.ok @svc.logs.first-error causes get +ts

## 2. The TKAB-W1 deploy-status source (v0.2)

Natural English source:

> billing-api deployed to staging at version 1.7.2. Three pods are healthy and
> latency p95 is 240ms. No rollback was triggered.

Hand-authored Tokenese v0.2 (no `^grammar:` header → frozen v0.2 allocation):

```tokenese
@billing-api := svc:billing-api/staging
@v := 1.7.2
@p95 := 240ms
get @billing-api status ^3
run deploy @v -> done ^3
say pods healthy ^3
say latency @p95 ^3
done deploy >> no rollback ^3
```

Decode (via `tokenese-translate`), abbreviated:

> bind @billing-api = "svc:billing-api/staging"; … get @billing-api status
> [confidence 3/9]; run deploy @v -> then: done [confidence 3/9]; … done
> deploy >> no rollback [confidence 3/9]

This is the source for the `TKAB-W1.pair.json` fixture; scoring it is shown in
`validate_transcript.md`.

## 3. An operational exchange (v0.3, with stipulated causation)

Natural English source:

> billing-api deployed to staging at version 1.7.2. Three pods are healthy and
> latency p95 is 240ms. No rollback was triggered. The migration step completed
> which causes the cache warmer to start.

Hand-authored Tokenese v0.3 (the `*>>` causation is corroborated by the source
"which causes"):

```tokenese
^grammar:v0.3
@billing-api := svc:billing-api/staging
@v := 1.7.2
@p95 := 240ms
@migration := step:migration
@cache := step:cache-warmer
get @billing-api status ^3
run deploy @v -> done ^3
say pods healthy ^3
say latency @p95 ^3
say @migration *>> @cache ^3
```

Decode (via `tokenese-translate`), abbreviated:

> bind @billing-api …; … say @migration causes @cache [confidence 3/9]

This is the source for `TKAB-W1.v03.pair.json`; its checker outcome is verified
in `validate_transcript.md`.
