#!/usr/bin/env python3
"""Anthropic-side token cost audit for Tokenese candidates.

Uses the count-tokens endpoint. Message scaffolding adds a constant
overhead C; we estimate C with a calibration string assumed to be
1 token ("a"), then tokens(s) = count(s) - count("a") + 1.
Measures worst case of bare and space-prefixed, mirroring audit_symbols.py.
"""
import json
import os
import sys
import time
import urllib.request

KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = "claude-haiku-4-5-20251001"
URL = "https://api.anthropic.com/v1/messages/count_tokens"

def count(text):
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "user", "content": text}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "x-api-key": KEY, "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["input_tokens"]
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))

def main():
    syms = json.load(open("/tmp/tokenese_syms.json"))
    base = count("a")
    print(f"calibration count('a') = {base}", file=sys.stderr)
    results = {}
    for i, s in enumerate(syms):
        bare = count(s) - base + 1
        spaced = count("a " + s) - base  # "a " ~ base tokens, remainder = s
        worst = max(bare, spaced)
        results[s] = worst
        if (i + 1) % 20 == 0:
            print(f"{i+1}/{len(syms)}", file=sys.stderr)
    json.dump(results, open("anthropic_costs.json", "w"), ensure_ascii=False, indent=1)
    multi = {s: c for s, c in results.items() if c > 1}
    print("=== >1 token on Anthropic side ===")
    for s, c in sorted(multi.items(), key=lambda kv: -kv[1]):
        print(f"{s!r}: {c}")
    print(f"\n{len(results)-len(multi)}/{len(results)} single-token")

if __name__ == "__main__":
    main()
