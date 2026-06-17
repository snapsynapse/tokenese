"""CLI: `tokenese-translate [path]` or stdin.

Reads a Tokenese transcript, prints one English line per input line, and
prints a conformance summary to stderr unless --quiet.
"""

from __future__ import annotations

import argparse
import json
import sys

from .renderer import render_transcript
from .session import Session
from .validator import validate_transcript


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tokenese-translate")
    p.add_argument("path", nargs="?", help="Tokenese transcript file (omit for stdin)")
    p.add_argument("--quiet", action="store_true", help="suppress conformance summary on stderr")
    p.add_argument("--json", action="store_true", help="emit JSON {english:[], conformance:{}} on stdout")
    args = p.parse_args(argv)

    text = sys.stdin.read() if not args.path else open(args.path, "r", encoding="utf-8").read()

    session = Session()
    english_lines = render_transcript(text, session=session)
    report = validate_transcript(text)

    if args.json:
        payload = {
            "english": english_lines,
            "conformance": report.to_dict(),
            "session": {
                "bindings": session.bindings,
                "handshake": session.handshake,
                "mode": session.mode,
                "diagnostics": session.diagnostics,
                "repair_history": {
                    k: {"count": v.count, "pinned_plain": v.pinned_plain}
                    for k, v in session.repair_history.items()
                },
            },
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    for line in english_lines:
        print(line)
    if not args.quiet:
        sys.stderr.write("\n--- conformance ---\n")
        sys.stderr.write(f"L1 lexicon : {'PASS' if report.l1_pass else 'FAIL'}\n")
        sys.stderr.write(f"L2 grammar : {'PASS' if report.l2_pass else 'FAIL'}\n")
        sys.stderr.write(f"L3 repair  : {'PASS' if report.l3_pass else 'FAIL'}\n")
        if session.diagnostics:
            sys.stderr.write("session diagnostics:\n")
            for d in session.diagnostics:
                sys.stderr.write(f"  - {d}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
