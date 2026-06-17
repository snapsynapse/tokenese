# Tokenese audit card — v0.3

One page. A competent human with this card must be able to follow any
conforming transcript (INTENT.md invariant 7). Three sections: the sigil key,
the `^` anchor scale, and the allusion ledger.

## 1. Sigil key

Every v0.3 sigil (DESIGN.md §7, verbatim). Rows tagged `(v0.3)` are active only
when the artifact opens with `^grammar:v0.3`; everything else is the frozen v0.2
allocation. One sigil, one meaning.

| Sigil | Meaning (only meaning) |
|---|---|
| `@` | handle bind/reference |
| `□` | typed hole |
| `†` | corpus anchor |
| `√` | ack/confirm (readback reply) |
| `??` | repair (addressable) |
| `^` | ordinal confidence 0-9 |
| `\|` | alternatives within a slot |
| `::` | type tag |
| `->` | sequence/yield |
| `=>` | implication |
| `because` | causal attribution (word form; `<-` failed Anthropic audit and is a mirror-confusable of `->`) |
| `!` | imperative + readback trigger; **prefix `!@h` = negation (v0.3)** |
| `~` | approximate |
| `//` | human-facing comment |
| `§` | spec rule reference |
| `{ }` | proposition quoting, depth 1 |
| `not( )` | negation scope, depth cap 2, bind-don't-nest |
| `dense` / `plain` | mode words |
| `ev:` | evidential slot |
| `^grammar:vX.Y` | artifact grammar-version declaration, first non-comment line (v0.3) |
| `^declare:level=L` | declared conformance level `L0\|L1\|L2\|L3`, first non-comment line (v0.3) |
| `^plain<<<` … `>>>^plain` | closed plain region; verbatim, not graded (v0.3) |
| `"""` … `"""` | raw source quote, verbatim, triple-quote delimited (v0.3) |
| `@h?` | hedge suffix — "possibly h" (v0.3) |
| `>>>` | temporal sequence "left then right"; always admissible (v0.3) |
| `*>>` | stipulated causation "left causes right"; requires source corroboration (v0.3) |
| `?>>` | hypothesized causation "left may cause right"; always admissible (v0.3) |
| `#` (line start) | line comment to EOL; inline `#` is unchanged tag content (v0.3) |

## 2. Anchor scales — the `^` confidence scale

`^N` is an **ordinal** confidence digit 0-9, never a probability. It is a
post-hoc report with decent rank calibration and poor absolute calibration; the
receiver applies its own cutoff per its own risk posture. Spec-anchored bands:

| `^N` | Band | One-sentence reading |
|---|---|---|
| `^0` | impossible | The claim is asserted to be effectively ruled out. |
| `^1` | very unlikely | Far below even odds; report it, do not act on it. |
| `^2` | unlikely | Below even odds; a live but minority possibility. |
| `^3` | somewhat unlikely | Leaning against, but not dismissible. |
| `^4` | leaning no | Just below a coin flip. |
| `^5` | even | A coin flip; no warrant either way. |
| `^6` | leaning yes | Just above a coin flip; the analogy/`like`-derived ceiling. |
| `^7` | likely | Above even odds; the working assumption. |
| `^8` | very likely | Well above even odds; strong but not settled. |
| `^9` | near-certain | As close to certain as the channel permits; never "proven". |

Binary facts take `y/n`, not `^N` — grading a binary fact is a conformance
error. Any `like`-derived (analogy) fact carries `^<=6` or gets verified.

## 3. Allusion ledger

Corpus anchors (`†name`) are admissible only when registered here with a
role-bearing schema and a first-use gloss handshake (INTENT.md invariant 7;
DESIGN.md K8). Unconfirmed anchors carry no load.

```
(none registered as of v0.3.3 — corpus anchors with gloss handshake land in ROADMAP L4)
```
