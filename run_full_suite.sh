#!/bin/sh
cd "$(dirname "$0")/tests" || exit 1
for f in *.py; do
  echo "=== $f ==="
  python3 "$f"
done
