# Client security/product review follow-ups (2026-10-01)

The client asked for an intensive, wide-angle review ("recherchiere
intensiv... 60 Minuten lang") covering everything open across the whole
app, backend included - not just Cardio. That review surfaced several
things outside anything previously tracked in this file, mainly because
they live outside app.js (the Cloudflare Worker, dashboard.html) or are
product/content decisions rather than bugs. The client then worked through
the findings point by point; this section records what was decided/built
and, per the client's own instruction ("alles andere... musst du mir
danach nochmal vorlegen"), what is still open for a future round.

**Training-code guessability (worker/src/index.js's public, unauthenticated
`GET /program?code=...`)**: the review flagged that codes are free-text
coach-chosen strings (dashboard placeholder: `dig01`) with no rate-limiting
on that endpoint, so a plausible/sequential code could be guessed/
enumerated and would hand back a stranger's full personalised programme
`config` - a privacy issue between the client's own customers, not a
theoretical one. The client's own proposed fix - keep a short recognisable
prefix (their own bookkeeping, e.g. a date or sequence) but make the rest
of the code enough random characters that it can't be guessed - is correct
and is the standard shape for this problem (a public-but-unguessable
token, with human-friendly metadata kept separately). Two things worth
being explicit about, agreed with the client: (1) the *order*/*date* a
code was issued should NOT be encoded into the code text itself (e.g. a
literal running number) - that leaks exactly the kind of structure that
makes guessing easier (seeing `...-003` tells an attacker `...-001` and
`...-002` likely exist too); it already lives for free in the `programs`
table's own `created_at`/`updated_at` columns and the dashboard's "Trainings-
Codes" table, sorted by `Geändert`. (2) The actual secret-facing value
(`program_code`, what's typed into the app and sent to `/program`) and the
coach's own per-customer bookkeeping label (`client_code`/"Kürzel" in
`client_history`, never sent to that public endpoint, already behind the
admin token) are two different fields in the existing schema - only the
first one needs to be unguessable, the second can stay human-readable with
zero privacy exposure, since only the coach, authenticated, ever sees it.

Implemented: `dashboard.html`'s "Trainings-Codes" panel, next to `#pCode`,
got a new "Zufällig ergänzen" button (`randomCodeSuffix()`, 10 characters,
`crypto.getRandomValues`, an alphabet with visually ambiguous characters
removed - no `0`/`o`, `1`/`l`/`i` - since a human still has to read/type
these by hand) that appends a random, unguessable tail to whatever prefix
the coach optionally typed first. This is a pure dashboard UI change - the
Worker API already accepts any string as `code`, so there was no schema or
backend change needed, and nothing about already-issued codes changes
automatically. **Left open, needs the client's own call**: existing
already-issued codes are NOT retrofitted with a random suffix (that would
break them for whoever already has them) - purely a going-forward
improvement for codes created from now on, unless the client decides some
or all existing clients should be migrated to a new, longer code (their
own relationship to manage, not something to do silently). Client asked to
be SHOWN the existing codes before deciding - this session has no access
to the Cloudflare D1 database or the `ADMIN_TOKEN` (`wrangler secret`,
never in this repo), so that list can't be pulled from here; it already
lives in the coach's own dashboard's "Trainings-Codes" table. Still open
until the client either looks there themselves or pastes the list here.
Also still
open, lower urgency now that codes themselves resist guessing: the
Worker's CORS header is `*` on every route including the admin ones (could
be narrowed to the dashboard's actual origin), the admin-token comparison
is a plain `!==` (not constant-time; low real-world risk over HTTPS/
Cloudflare's own network jitter), and there is still no server-side rate-
limiting on `/program` at all (now a much smaller risk with a ~10-character
random tail - 32^10 combinations - but not zero, e.g. against a very high
request-volume scripted attempt). **All three done 2026-10-02 (Fabian:
"ja")** in `worker/src/index.js`: admin routes answer CORS only for
`ADMIN_ORIGINS` (GitHub Pages origin + localhost:8845) and refuse a
foreign browser origin with 403 (curl/scripts without an Origin header
still work with the token); constant-time token compare
(`timingSafeEqual`); `/program` rate limited per IP via the
`LOOKUP_LIMITER` `[[ratelimits]]` binding in `wrangler.toml` (30/min,
wrangler 4.36+, the code skips the check if the binding is missing).
**Deployed 2026-10-03** (version 480d6c01, verified: /program 200,
admin routes 401 without token, foreign origin 403). Deploys run in the
Claude Code environment "FWMC-automation" (holds CLOUDFLARE_API_TOKEN as
an environment variable, network access "Vollständig"; a network change
only applies to NEW sessions) - this project's own environment cannot
reach api.cloudflare.com. If the dashboard ever moves to a
custom domain, add that origin to `ADMIN_ORIGINS`. Test:
`tests/worker_hardening_test.py` (runs `worker/test/hardening.mjs` in
plain node against a mocked D1).

**Test-Bereich visibility**: implemented as described in "Test-Bereich
(autonomous, ongoing)" below - hidden-by-default nav tab, revealed
permanently on a browser by typing `testbereich-frei` into any section's
existing training-code box. This is a client-side-only, obscurity-not-
security gate (the word sits in the same public `app.js` as everything
else) - appropriate for what the client actually asked for ("nicht jedem
sofort sichtbar"), not meant to withstand someone actually inspecting the
page source. Caught one real regression from hiding the tab while running
the full suite afterwards: `nav_overflow_test.py`'s 768px overlap check
queried every `.section-tab` including the now-hidden "Test" one, whose
collapsed `(0,0,0,0)` rect read as a false overlap against the real last
tab's right edge - fixed by scoping that one query to `:not([hidden])`
(the other checks in that file measure `scrollWidth`/`clientWidth` on the
container, which a `display:none` child never affects, so only this one
rect-based query needed it). Client confirmed `testbereich-frei` is fine
as the unlock word (2026-10-01) - no change needed, still a one-line
constant (`TEST_UNLOCK_WORD` near `CODE_API` in app.js) if that ever
changes.

**Test-Bereich's own public mentions - load conditionally, not remove
(resolved 2026-10-01, client follow-up)**: the first pass removed every
FAQ/welcome-text mention of the Test-Bereich outright (flagged above as a
judgment call). Client's actual ask once asked directly: don't delete the
copy, just gate it the same way as the tab itself - "Test teaser usw dann
mit reinladen, wenn jemand den Code eingeloggt hat." Implemented by
wrapping each mention in `<span class="test-teaser" hidden>`/
`<details class="faq-item test-teaser" hidden>` (the dedicated "Was ist
der Test-Bereich?" FAQ entry came back verbatim, plus the two trimmed
sentences in "Was ist FWMC Online-Training?"/"Was ist der Unterschied..."
and `#tipsWelcome`'s area list) and having `applyTestTabVisibility()`
toggle every `.test-teaser`'s `hidden` attribute in lockstep with the tab
itself - one state, one function, nothing to keep in sync by hand.

**Test-Bereich now has its own visual identity, separate from the rest of
the app** (same client follow-up: "sollte dann irgendwie nochmal einen
'mit Code aktiviert' Hinweis haben und farblich bisschen abgehoben sein,
damit niemand später denkt, der würde regulär dazu gehören"). Two parts:
(1) a `.test-unlock-badge` ("Mit Code freigeschaltet") next to the
existing "Experimentierbereich" tag in `#testHome`'s hero - always
visible there (reaching `#testHome` at all already implies unlocked, no
extra gating needed); (2) a dedicated `--test-accent`/`--test-accent-deep`/
`--test-accent-pale` colour triple (amber, both light- and dark-mode
variants, same 3-block pattern as `--brand`/`--brand-deep`/`--brand-pale`
in styles.css's `:root`) that `#testHome`'s own hero-kicker, active nav
tab, and `.featured-card`s (the exercise-entry cards, same class NAT/VT
use elsewhere - only re-pointed from `--brand` to `--test-accent` while
scoped under `#testHome`) all pick up instead of the app's normal teal
brand colour. The effect: once you're actually inside Test, everything
about it visibly reads as "a different, temporary area" rather than just
another permanent tab among equals.

Test: `tests/test_unlock_test.py` extended with both pieces (all
`.test-teaser` spots hidden before/shown after unlock, badge visibility,
exact accent colour `rgb(180, 83, 9)`).

**Epilepsy/photosensitivity note for fast-flashing exercises**: the
existing Epilepsie warning (`#wimhofSheet`'s "Bitte vorher lesen" box) only
covers "Kraftvolle Atmung"'s own hyperventilation/fainting risk - nothing
anywhere mentioned visual flash/strobe risk for the fast-cycling visual
exercises (Blitz-Raster, UFOV down to a 33ms exposure floor, Flash
Speicher Test, Posner-Cueing, MOT). Client's own instinct (no per-exercise
badge, too noisy/alarming on every single exercise card; belongs in the
extended welcome text, possibly the FAQ too) matches what the review
recommended. Implemented as a 5th bullet in `#tipsSheet`'s practical-tips
list ("Schnelle Lichtreize...") - seen by everyone on first visit and
recallable any time via "So trainierst du richtig" - plus a new FAQ entry
("Gibt es Übungen, bei denen ich besonders vorsichtig sein sollte?"),
generic (no technical exercise names) rather than per-exercise, cross-
referencing the existing Wim-Hof warning rather than duplicating it. No
further action needed unless the client wants per-exercise flagging after
all for specific high-intensity settings.

**iPad: "Atemtraining" mid-word-broke in the top-level nav (client
screenshot, reported 2026-10-01)**: root cause confirmed, NOT a one-off -
`.section-switch{max-width:580px}` (styles.css) was explicitly sized for 6
tabs (its own comment: "widened from 420 to 580px... so a 6th tab (added
for the new Test section) still gets enough room"), but the client's
screenshot shows all 7 (Test included) - a 7th tab past what that cap was
tuned for leaves too little width for "Atemtraining" (one unbreakable
compound word, `overflow-wrap:break-word` has no space to break at, so it
cuts mid-word into "Atemtraini"/"ng") on a tablet-width screen. Reproduced
with Playwright at 768/810/834px: 6 tabs (Test hidden, the new default) -
fine; 7 tabs (Test unlocked) - reproduces exactly. So hiding Test by
default already incidentally fixed this for every ordinary visitor, but
not for the client themselves or any tester who unlocks it, which is
exactly who'd actually see it. Fixed at the root rather than patched
around: `body.nav-test-unlocked .section-switch{max-width:680px}`, toggled
by `applyTestTabVisibility()` in lockstep with the tab itself, so the cap
always matches the actual tab count instead of a number baked in for
whatever the count happened to be at the time. Test: `nav_overflow_test.py`
extended - a container-level `scrollWidth<=clientWidth` check (what the
file already did) can't catch this at all, since the container itself
never overflows, only one tab's own text wraps inside it, so the new check
compares "Atemtraining"'s rendered height against "Movement"'s (same font/
padding, short enough to never wrap) at 768px with Test unlocked.

**Everything else the review raised, not acted on this round (carried
forward, client's own words: "musst du mir danach nochmal vorlegen")**:
- Silent data loss: fixed 2026-10-02 (see "Audit-Fixes" below) -
  `writeJSON()` now shows `#storageWarning` once when a write fails.
- The whole Playwright suite only ever runs against Chromium, while the
  app is clearly built for iPhone PWA use (apple-touch-icon, standalone
  display, `apple-mobile-web-app-capable`) - iOS Safari's own service-
  worker/fullscreen/audio-autoplay quirks have never been exercised by any
  test here. Not addressed.
- The regression suite's 8 standing "known-benign" always-False lines
  (`arrow_colors_test.py` ×2, `combo_play_test.py`,
  `nat_combo_abort_test.py`, `nat_combo_test.py`, `note_distinction_test.py`,
  `remember_error_test.py`, `test_section_test.py`, `trail_hint_overlap_test.py`)
  keep growing as an allow-list that has to be mentally filtered out of
  every suite run rather than actually fixed or formally retired. Not
  addressed.
- The 15 scientific-validity/UX caveats already tracked in "Offene Fragen"
  at the end of this file (small per-run sample sizes, `setTimeout` timing
  precision, simplifications vs. published clinical protocols, fixed block
  order, the Wortfarben-Test/Stroop redundancy question) - unchanged,
  still waiting on the client's own read-through.
- No app-level lint/type-checking/bundler at all (`node --check` is syntax-
  only) over a 21k+-line single `app.js` - not a bug, just a standing
  maintainability risk that grows with every future batch of work. Not
  addressed, no action proposed unless the client wants to discuss it.

