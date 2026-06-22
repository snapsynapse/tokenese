#!/usr/bin/env bash
# Recompute or verify the sha256 hashes in skills/tokenese/MANIFEST.yaml for the
# three pinned files (SKILL.md, audit_card.md, install_guide.md).
#
# Usage:
#   tools/skills/compute_hashes.sh          # update MANIFEST.yaml in place
#   tools/skills/compute_hashes.sh --check  # verify without writing
#
# Run from anywhere; paths resolve relative to this script.
set -euo pipefail

mode="update"
if [[ "${1:-}" == "--check" ]]; then
  mode="check"
elif [[ "${1:-}" != "" ]]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$here/../../skills/tokenese"
manifest="$skill_dir/MANIFEST.yaml"
files=(SKILL.md audit_card.md install_guide.md)

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

manifest_hash() {
  local file="$1"
  awk -v f="$file" '$1 == f ":" { print $2 }' "$manifest"
}

replace_manifest_hash() {
  local file="$1"
  local sum="$2"
  local tmp
  tmp="$(mktemp)"
  awk -v f="$file" -v s="$sum" '
    $1 == f ":" { print "  " f ": " s; next }
    { print }
  ' "$manifest" > "$tmp"
  mv "$tmp" "$manifest"
}

failed=0
for f in "${files[@]}"; do
  sum="$(sha256 "$skill_dir/$f")"
  current="$(manifest_hash "$f")"
  if [[ "$mode" == "check" ]]; then
    if [[ "$current" != "$sum" ]]; then
      echo "hash mismatch: $f manifest=$current actual=$sum" >&2
      failed=1
    else
      echo "$f ok"
    fi
  else
    replace_manifest_hash "$f" "$sum"
    echo "$f -> $sum"
  fi
done

if [[ "$mode" == "check" ]]; then
  exit "$failed"
fi

echo "updated $manifest"
