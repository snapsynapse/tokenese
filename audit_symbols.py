#!/usr/bin/env python3
"""Tokenese symbol audit: measure real token cost of candidate glyphs in o200k_base.

A symbol is admissible to the Tokenese lexicon only if it costs 1 token
in every tokenizer both parties use. This script covers the OpenAI side
(o200k_base = GPT-4o/o-series/Codex era). cl100k_base included for reference.
Anthropic side measured separately via count-tokens API.

Cost is measured two ways: bare, and with a leading space (mid-sentence
position changes BPE merges). Worst case of the two is reported as cost.
"""
import unicodedata
import tiktoken

CANDIDATES = {
    "ascii-sigil": list("@#$%&*+-/|~!?^_=<>:;.,"),
    "ascii-digraph": ["->", "=>", "::", "||", "&&", ">>", "<<", "!=", "==",
                       ">=", "<=", "++", "--", "..", "//"],
    "bracket": list("()[]{}") + ["[[", "]]", "{{", "}}"],
    "arrow-math": list("→←↑↓⇒⇐↔∴∵∀∃∈∉⊂⊃∧∨¬±×÷≠≈≤≥∞∑∏√Δ∇"),
    "geometric-misc": list("•◦▸▹►▶○●□■◆◇★☆†‡§¶"),
    "greek": list("αβγδεζηθικλμνξοπρστυφχψω"),
    "cjk-sample": list("人事时地物因果前后大小新旧真假问答始终入出上下中外不可必有无同异"),
    "emoji-sample": list("✅❌⚠️🔴🟢🔵📌🔒🔓"),
    "short-words": ["do", "go", "if", "or", "and", "not", "yes", "no", "ok",
                     "ask", "say", "get", "put", "run", "fix", "new", "old",
                     "big", "all", "none", "true", "false", "done", "fail",
                     "need", "want", "must", "may", "can", "will"],
}

def cost(enc, s):
    bare = len(enc.encode(s))
    spaced = len(enc.encode(" " + s))
    return max(bare, spaced), bare, spaced

def main():
    o200k = tiktoken.get_encoding("o200k_base")
    cl100k = tiktoken.get_encoding("cl100k_base")
    print(f"{'class':<16} {'sym':<6} {'o200k':>5} {'(bare/sp)':>9} {'cl100k':>6}  name")
    admissible = {}
    for cls, syms in CANDIDATES.items():
        ok = []
        for s in syms:
            c, b, sp = cost(o200k, s)
            c1, _, _ = cost(cl100k, s)
            try:
                nm = unicodedata.name(s) if len(s) == 1 else ""
            except (ValueError, TypeError):
                nm = ""
            flag = "" if c == 1 else "  <-- COSTLY"
            print(f"{cls:<16} {s!r:<6} {c:>5} {f'{b}/{sp}':>9} {c1:>6}  {nm[:40]}{flag}")
            if c == 1:
                ok.append(s)
        admissible[cls] = ok
    print("\n=== ADMISSIBLE (1 token in o200k, worst case) ===")
    for cls, syms in admissible.items():
        print(f"{cls:<16} {len(syms):>3}/{len(CANDIDATES[cls]):<3} {' '.join(syms)}")

if __name__ == "__main__":
    main()
