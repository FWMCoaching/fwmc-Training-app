# Regression tests

Playwright (Python, async API) scripts against a locally served copy of
this app. Each script covers one feature area end-to-end in a headless
browser and prints `ERRORS: []` at the end if no `pageerror`/console
`error` events occurred.

## Running

1. Serve the repo root: `python3 ../serve_utf8.py` (serves on `:8845`)
2. From this directory: `python3 <script>.py`, or run them all:
   ```
   for f in *.py; do echo "=== $f ==="; python3 "$f"; done
   ```

Chromium path expected by these scripts:
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` (pre-installed in
Claude's remote execution environment). Adjust if running elsewhere.

Screenshots go to `screenshots/` (gitignored, not asserted against —
visual sanity checks only, open them manually if a test's behaviour is
unclear from its printed output).

## Convention for new tests

Before every deploy, run the *entire* suite, not just a script for the
newest feature — shared code (the canvas `drawScene` dispatch, the
colour-picker system, `hideAllPlayers()`) is touched more often than a
change's description suggests. When adding a feature, add a script here
covering: the happy path, zero/boundary-selection states, persistence
across `page.reload()`, and any interaction with other exercises' state
(e.g. a setting that must NOT leak into an unrelated exercise).
