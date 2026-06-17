#!/usr/bin/env bash
# Recompute the sha256 hashes in skills/tokenese/MANIFEST.yaml for the three
# hashed files (SKILL.md, audit_card.md, install_guide.md) as committed.
#
# Run from anywhere; paths resolve relative to this script.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$here/../../skills/tokenese"
manifest="$skill_dir/MANIFEST.yaml"

for f in SKILL.md audit_card.md install_guide.md; do
  sum="$(sha256sum "$skill_dir/$f" | awk '{print $1}')"
  # Replace the value after "  <f>: " inside the hashes: block.
  sed -i -E "s|^(  $f: ).*|\1$sum|" "$manifest"
  echo "$f -> $sum"
done

echo "updated $manifest"
