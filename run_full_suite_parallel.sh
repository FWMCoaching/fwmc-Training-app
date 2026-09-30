#!/bin/sh
# Parallel version of run_full_suite.sh - same log format (one "=== file
# ===" section per test, full output beneath it) so it works as a drop-in
# replacement with the existing "pipe to a log file, poll `grep -c '^=== '`
# against it" pattern, just much faster wall-clock: each Playwright test is
# I/O-bound (waiting on its own Chromium instance, own isolated browser
# context/profile), not CPU-bound, so running several at once scales well
# instead of queuing behind each other one at a time.
#
# Unlike the sequential loop, sections appear in COMPLETION order, not
# filename order (whichever of the concurrent workers finishes first
# writes first) - each is still one complete, un-interleaved block though
# (flock serializes the appends), and every section still shows up
# incrementally as its own test finishes, not all at once at the very
# end - an earlier version of this script buffered everything until the
# whole run was done, which defeated the point of polling `grep -c` for
# progress.
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
lockfile="$tmpdir/.lock"

n=0
for f in *.py; do
  n=$((n + 1))
  printf '%03d %s\n' "$n" "$f"
done > "$tmpdir/index"

# Each worker writes its own complete output to a private temp file first
# (so one test's output is never torn mid-write), then appends that
# already-finished file to this script's own stdout under an flock lock
# (so two workers finishing at the same instant can't interleave their
# appends either) - the caller's own `> logfile` redirect on invoking this
# script is what turns that stdout into the shared log. The worker body is
# passed as an inline script (not a shell function) since POSIX sh has no
# portable way to export a function into an xargs/sh -c child process.
xargs -P "$CONCURRENCY" -n 2 sh -c '
  n="$1"; f="$2"
  out="'"$tmpdir"'/$n.out"
  { echo "=== $f ==="; python3 "$f" 2>&1; echo; } > "$out"
  flock "'"$lockfile"'" cat "$out"
' sh < "$tmpdir/index"
