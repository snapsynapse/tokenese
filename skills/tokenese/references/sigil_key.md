# Sigil key — v0.3

Mirror of DESIGN.md §7 (sigil namespace, collision resolution). This is
intentionally redundant: a skill consumer must not need to navigate the repo to
find the sigil table. The repo's DESIGN.md §7 is authoritative if they ever
diverge.

Grammar version stamp: **v0.3** (additive over v0.2; see GRAMMAR-v0.3.md). Rows
tagged `(v0.3)` are new and only active when the artifact opens with
`^grammar:v0.3`; everything else is the frozen v0.2 allocation.

The five lenses, designed in isolation, claimed several sigils multiple ways.
Binding allocation, one sigil one meaning:

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

The v0.1 uses of `=` (binding) and `#` (inline tag) stand. The bare flow
operator `>>` is still unallocated and unchanged; the v0.3 causal sigils
`>>>`/`*>>`/`?>>` are distinct three-character tokens and do not collide with
it. `<<` remains unallocated except as the `^plain<<<` opener fragment.
