#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

missing=0

# Find markdown files
mapfile -t files < <(find docs -type f -name "*.md")

for f in "${files[@]}"; do
  while IFS= read -r line; do
    # naive scan for patterns like ](path)
    link_part=$(echo "$line" | sed -n 's/.*](\([^)#?]*\)).*/\1/p') || true
    if [[ -n "${link_part}" ]]; then
      link="$link_part"
      # only check relative links under docs/
      if [[ "$link" != http* && "$link" != mailto:* && "$link" != *.png && "$link" != *.jpg && "$link" != *.svg ]]; then
        target="$(dirname "$f")/$link"
        if [[ ! -e "$target" ]]; then
          echo "Broken link in $f -> $link"
          missing=1
        fi
      fi
    fi
  done < "$f"

done

if [[ $missing -ne 0 ]]; then
  echo "Docs link check failed"
  exit 1
fi

echo "Docs link check passed"