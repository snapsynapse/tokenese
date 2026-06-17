#!/usr/bin/env python3
"""GuideCheck Level 4 DNS-anchor drift guard.

Resolves the TXT record at `_assistant-guide.tokenese.org`, extracts the
advertised `sha256=...`, and asserts it equals the sha256 of the live guide
file (`docs/.well-known/assistant-guide.txt` in this repo).

Designed to be cheap and dependency-light: stdlib + a single `dig` call. Exits
non-zero on any mismatch or resolution failure, so CI fails loudly.

Usage:
    python check_dns_anchor.py
    python check_dns_anchor.py --domain _assistant-guide.tokenese.org \
                               --guide docs/.well-known/assistant-guide.txt

Roadmap: N4 (DNS-anchor drift guard).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DOMAIN = "_assistant-guide.tokenese.org"
DEFAULT_GUIDE = "docs/.well-known/assistant-guide.txt"
# Public resolvers to cross-check. Authoritative first, then public caches.
# All must agree for the check to pass; this also catches half-propagated
# updates where the registrar saved but a public resolver is still stale.
RESOLVERS = [
    ("authoritative", "dns1.registrar-servers.com"),
    ("cloudflare", "1.1.1.1"),
    ("google", "8.8.8.8"),
    ("quad9", "9.9.9.9"),
]

SHA_RE = re.compile(r"sha256=([a-f0-9]{64})")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def dig_txt(domain: str, resolver: str) -> str:
    """Return the first TXT answer (whitespace-joined, quotes stripped)."""
    out = subprocess.run(
        ["dig", "+short", "TXT", domain, f"@{resolver}"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if out.returncode != 0:
        raise RuntimeError(f"dig failed for {domain}@{resolver}: {out.stderr.strip()}")
    line = (out.stdout or "").strip().splitlines()
    if not line:
        raise RuntimeError(f"no TXT record at {domain} via {resolver}")
    # dig wraps the record in quotes; strip them and join split chunks.
    return " ".join(part.strip().strip('"') for part in line)


def extract_sha(txt_value: str) -> str:
    m = SHA_RE.search(txt_value)
    if not m:
        raise ValueError(f"no sha256=... token found in TXT: {txt_value!r}")
    return m.group(1)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--domain", default=DEFAULT_DOMAIN)
    p.add_argument("--guide", default=DEFAULT_GUIDE)
    p.add_argument(
        "--allow-stale-public",
        action="store_true",
        help=(
            "Treat mismatches at public resolvers as warnings (still fails on "
            "authoritative mismatch). Use during the first ~30 min after a "
            "registrar update while public caches refresh."
        ),
    )
    args = p.parse_args()

    if not shutil.which("dig"):
        print("ERROR: `dig` not found on PATH; install bind/bind9-dnsutils.", file=sys.stderr)
        return 2

    guide_path = Path(args.guide)
    if not guide_path.is_file():
        print(f"ERROR: guide file not found: {guide_path}", file=sys.stderr)
        return 2
    file_sha = sha256_of(guide_path)
    print(f"[guide] {guide_path}: sha256={file_sha}")

    failures: list[str] = []
    for label, resolver in RESOLVERS:
        try:
            txt = dig_txt(args.domain, resolver)
            dns_sha = extract_sha(txt)
        except Exception as e:
            failures.append(f"{label} ({resolver}): {e}")
            print(f"[{label:14s}] ERROR: {e}")
            continue
        ok = dns_sha == file_sha
        marker = "OK " if ok else "MISMATCH"
        print(f"[{label:14s}] sha256={dns_sha}  {marker}")
        if not ok:
            msg = f"{label} ({resolver}): dns={dns_sha} != file={file_sha}"
            if label == "authoritative" or not args.allow_stale_public:
                failures.append(msg)

    if failures:
        print("\nDNS-anchor drift detected:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nAll resolvers agree with the guide file. Level 4 anchor verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
