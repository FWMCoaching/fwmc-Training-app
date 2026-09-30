#!/bin/sh
# Parallel version of run_full_suite.sh - same log format (one "=== file
# ===" section per test, full output beneath it, in filename order) so it
# works as a drop-in replacement with the existing completion monitor
# (`grep -c '^=== '` against the log), just much faster wall-clock: each
# Playwright test is I/O-bound (waiting on its own Chromium instance, own
# isolated browser context/profile), not CPU-bound, so running several at
# once scales well instead of queuing behind each other one at a time.
#
# Needs serve_utf8.py's ThreadingTCPServer (not plain TCPServer) to avoid
# the dev server itself becoming the bottleneck under concurrent load -
# restart it after pulling that change if it's still running the old code
# (`curl -s http://localhost:8845/index.html >/dev/null && echo up`).
#
# Usage: sh run_full_suite_parallel.sh [concurrency]   (default 6)
set -e
cd "$(dirname "$0")/tests" || exit 1
CONCURRENCY="${1:-6}"
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT INT TERM

n=0
for f in *.py; do
  n=$((n + 1))
  printf '%03d %s\n' "$n" "$f"
done > "$tmpdir/index"

# Each worker writes to its own numbered file so concurrent output never
# interleaves; results are concatenated back in the original (zero-padded,
# so numerically-sorted-by-plain-sort) order once everything's done. The
# worker body is passed as an inline script (not a shell function) since
# POSIX sh has no portable way to export a function into an xargs/sh -c
# child process.
xargs -P "$CONCURRENCY" -n 2 sh -c '
  n="$1"; f="$2"
  { echo "=== $f ==="; python3 "$f" 2>&1; echo; } > "'"$tmpdir"'/$n.out"
' sh < "$tmpdir/index"

for out in "$tmpdir"/*.out; do
  cat "$out"
done
