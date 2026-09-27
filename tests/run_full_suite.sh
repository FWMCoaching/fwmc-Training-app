#!/bin/sh
cd "$(dirname "$0")"
for f in *.py; do
  echo "=== $f ==="
  timeout 150 python3 "$f"
  echo "EXIT:$?"
done
