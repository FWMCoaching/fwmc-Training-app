# FWMC Online-Training

A single-page training web app for Fabian Westermann Mentalcoaching:
Visual Training (VT), Atemtraining (breathing), Movement, Workout, NAT
(neuroathletic exercises like Positionen merken and Periphere
Wahrnehmung), Cardio and Test (an experimentation area - read
`docs/notes/23-test-bereich.md` before touching it). German-language
product; respond to the user in German.

Slimmed 2026-10-05 (Spar-Konzept). Every rule is still here, in short;
the verbatim long version with all reasons is
`docs/notes/24-claude-md-langfassung-2026-10-05.md`. Project status for
humans/threads: `/mnt/project-files/app/STAND.md` (read it first).

## Push notifications (client, 2026-09-30)

Every `PushNotification` starts with a fixed prefix, in every session:
- **🟢** - a stretch of work is genuinely finished, nothing pending on him
  (a natural stopping point, not after every small step).
- **❗🟢** - continuing needs a decision only he can make.

## Architecture: one source of truth, two deploy targets

`_body.html` (all screens), `app.js` (all logic, one IIFE, no framework),
`styles.css`. `sh build.sh` (self-contained, works from any checkout)
wraps `_body.html` into `index.html` (committed, served by Pages) and
`artifact-body.html` (not committed, input for the Artifact publish).
Run it after every edit. This repo is the working directory; there is
no other source location.

Deploy targets:
- **GitHub Pages** from `main`: `https://fwmcoaching.github.io/fwmc-Training-app/`
  (capital T; the old lowercase URL 404s since the rename - if someone
  says the app "doesn't load", check the URL first). Dashboard:
  `.../fwmc-Training-app/dashboard.html`. A rename/custom domain under
  `fabian-westermann.de` was being planned - ask before assuming the URL
  is final. Report "live" only after `curl` shows the new build on the
  real page (Pages builds can queue).
- **Claude Artifact** `https://claude.ai/artifact/MXieTDSa8y6W4BeRMfAw8K`:
  publish `artifact-body.html` as `file_path`, `app.js`/`styles.css` (and
  other changed assets) via `files`. Read the artifact once first in a new
  session (`url` must be read or published by this session).

## Local development

`python3 serve_utf8.py` serves this directory on :8845 with correct
charset headers (a `ThreadingTCPServer`, so parallel test browsers don't
queue). Open `http://localhost:8845/index.html`. Check it is alive with
`curl -s -o /dev/null -w "%{http_code}" http://localhost:8845/index.html`.

## Testing convention

Playwright, headless Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, `args=["--no-sandbox"]`,
viewport 390x844. Every new feature gets its own `tests/<name>_test.py`:
happy path, edge cases (zero-selected, persistence across reload,
boundary clamping) and empty `pageerror`/console `error`. Run tests from
inside `tests/` (see `tests/README.md`); a dev server must be running.
Shared rendering code (`drawScene`, colour pickers, `hideAllPlayers()`)
breaks more often than it looks, so the full suite runs before a release.

- **Chromium only**: no WebKit/Firefox, no iOS/Android device here. Never
  imply Chromium covers Safari (service worker, Fullscreen API, audio
  autoplay, viewport/notch differ). Name the concrete things Fabian should
  check on his own iPhone/iPad instead.
- **Full suite**: `sh run_full_suite_parallel.sh [concurrency]` (default 6,
  lower it if tests flake under load) appends one `=== file ===` section
  per test in completion order. Run it in the background and wait with a
  second background command, not by polling by hand:
  ```
  nohup sh run_full_suite_parallel.sh > /tmp/suite.log 2>&1 &
  total=$(ls tests/*.py | wc -l)
  until [ "$(grep -c '^=== ' /tmp/suite.log 2>/dev/null)" -ge "$total" ]; do sleep 20; done; echo "SUITE COMPLETE"
  ```
  Then grep the log for `[Tt]raceback`/`Error:`/unexpected `: False`.
  Never edit `app.js`/`_body.html`/`styles.css` while a run is in flight.

## Deploy checklist (nothing is automatic)

1. `node --check app.js`
2. `sh build.sh`
3. Full regression suite (see above) against `localhost:8845`
4. Update this file or the matching `docs/notes/` file if a lasting
   pattern, an open item or the workflow changed - same commit
5. Commit with the attribution footer from the current session's system
   prompt (never a stale one), push to `main` (Pages builds from it)
6. Publish to the Artifact (separate, always manual)

**Quality gate before every release (Fabian, 2026-10-04)**: an independent
reviewer (separate Agent, fresh context) gets screenshots of every changed
screen and its siblings (390px and 1024px, light and dark), task "find
everything that would bother Fabian", calibrated with the "Nachgetragene
Punkte" table in /mnt/project-files/firma/abgabe-check.md. Fix its finds
before pushing. Anything Fabian still finds becomes a general automatic
check (the kind of error, not the single case). Once a quarter: the home
screen of every area (about 12 screenshots).

**Bundle releases (Fabian, 2026-10-04)**: bundle 3-4 changes per release,
full suite once at the end; while building run only the tests at hand. A
pure documentation change needs no suite run. Urgent fixes Fabian waits
on may go out alone. Ideas go to Fabian first as a short list with a
recommendation; only what he approves gets built.

## Working conventions

- Never use the `AskUserQuestion` tool; put options in plain text.
- **Silence is not approval (client, 2026-10-01: "Diese Aussagen gilt
  generell immer übrigens, wenn ich auf Sachen nicht eingehe.")**: points
  he didn't answer stay open ("Wiedervorlage"); never build them as if
  approved.

## Rules from the audit (2026-10-02)

Audit report: https://claude.ai/artifact/UaiRhm8pPY7BB2mPKW2L3H.
- Stage hints below a wrapping player-bar: `placeHintBelowBar(hintEl, barEl)`,
  never a fixed `top`; set any bar-wrapping text (status pill) BEFORE
  `stageTopClearanceY()` measures.
- Kombi blocks carry their own settings (NAT `prefs` snapshot via
  `prefsOverride`; Movement keeps direction/figureStyle);
  `startComboBlock()` backs up the client's prefs once per run
  (`comboPrefsBackup`), `restoreComboPrefs()` restores them on finish/abort.
  A Kombi run never changes standalone settings.
- Training codes: `lookupProgram()` times out after 12 s
  (`{__lookupError:"network"}`), `codeDefProblem(def)` checks before opening,
  `showCodeError()` is the one message; a broken def never throws out of
  `openProgramIntro()`.
- Backup excludes `fwmc-admin-token` (`BACKUP_EXCLUDE`).
- Destructive actions only via `confirmDialog()`, never `confirm()`.
- Inputs are 16 px on touch devices; section nav is a 4-column grid above
  480 px; `.player-status:empty` is hidden.
- Audio: `unlockCueAudio()` creates the AudioContext on first pointerdown;
  tests faking AudioContext install it with `add_init_script`.
- Tests never depend on the live Worker: route `CODE_API` with `page.route`.
Test: `tests/audit_fixes_test.py`.

**Naming (Fabian, 2026-10-02), every client-facing text:**
- **Kombi-Programm** (never Komplett-Programm/Kombi-Baukasten), parts are
  **Bausteine**. NAT home heading "NAT – Neuroathletik", tab stays "NAT".
  "Name noch offen" tags stay until Fabian decides.
- **Grundeinstellungen** for the gear sheet (code names like `masterPrefs` stay).
- NAT: **Positionen merken** (was Remember), **Flash-Speicher-Test**,
  **Objektverfolgung (MOT)** - everywhere incl. Kombi, history, Cardio picker.
- Every start button reads **"Training starten"** (Kombi capture mode:
  "Baustein übernehmen"). Test: `tests/start_labels_test.py`.
- Cardio extra exercise = **Zusatzaufgabe** ("+ Zusatzaufgabe",
  "Zusatzaufgabe · 0:20"; never Zusatzimpuls/Zusatzübung).

**Player behaviour (same day):**
- "Wirklich beenden?": after 60 s of a run (`END_CONFIRM_MIN_MS`), any
  button whose id ends in `ackBtn` with "Beenden" asks via `confirmDialog()`
  (one capture-phase listener; Kombi/Plan count as one run; in fullscreen
  the sheet moves into the fullscreen element). Test: `tests/end_confirm_test.py`.
- Auto-pause: on visibilitychange→hidden, `autoPauseOnLeave()` clicks the
  visible `button[id$="PauseBtn"]` starting with "Pause" (not while a
  `.pause-overlay` is open, not for Cardio).
- Footer "Stand: TT.MM.JJJJ, HH:MM" comes from `__APP_STAND__`, replaced by
  `build.sh` (Berlin time) - never hand-edit. No "Beta" tag.
- Cardio fullscreen `#cardioFsBtn` (`wireFullscreen`); `hideAllPlayers()`
  leaves fullscreen when its element got hidden.
  Test: `tests/autopause_version_fs_test.py`.
- Kombi Bausteine have ↑/↓ (`.combo-block-move`, its "Pause danach" moves along).
- Skipping past the end counts as aborted (coach programme, Tabata Zirkel,
  Cardio unit, last Workout block): "… beendet" without check mark,
  "Abgebrochen · …", history `aborted: true, note: "abgebrochen"`
  (`setDonePanelAborted`; Cardio counts real elapsed time). Natural end or
  "Übung beenden" = completed. Test: `tests/audit_round3_test.py`.
- Decided, no build: both Stroop versions stay, no grey in Stroop,
  Movement diagonal later, old codes dig01/dig02/xppbsp-1 stay, NAT lock
  code and Kids mode parked.
- Zusatzaufgabe is on every exercise of the shared VT canvas engine
  (automatic for new ones); excluded only Hütchen sortieren and NAT's own
  engines (Positionen merken, Blitz-Raster, Flash-Speicher-Test, MOT).

## Hard rule: one design, "aus einer Feder" (client, 2026-10-03)

- Reuse the closest sibling's pattern (classes, colours, layout, spacing,
  labels, explanation texts). A code entry is always `.code-card` with
  "Du hast einen Trainings-Code von deinem Trainer? Gib ihn hier ein."
- Client-facing text says "dein Trainer", never "Coach" or a name. The
  dashboard is the "Trainer-Dashboard".
- A deviation needs a real reason and goes to Fabian as a proposal first.
- Before every go-live: screenshot the new element next to a sibling
  (390px, light and dark) yourself; Fabian must never be the one to spot it.
- Dashboard follows light/dark (tokens in `:root` + prefers-color-scheme),
  uses Magra/Public Sans, never scrolls sideways at 390px (`.table-scroll`).
`tests/consistency_test.py` checks this; extend it for every new shared pattern.

## Hard rule: every exercise works everywhere (client, 2026-10-02)

"Solche Fehler dürfen nicht passieren." Every new or changed exercise
outside the Test-Bereich covers, unasked, in the same piece of work:
1. **Einzeln**: own ready screen, Feineinstellungen, saved presets.
2. **Kombi-Baustein**: `COMBO_CAPTURE_ENTRIES`, commit back to
   `comboScreen`, `COMBO_EDIT_OPENERS` (re-editable), playback in `startComboBlock()`.
3. **Plan-Stapeln** wherever the domain has a plan builder (Workout Zirkel,
   Kraftplan, Cardio-Einheit): addable several times, own values each.
4. **Pausen** wherever the paradigm has them (reference: `workoutCircuitPrefs`).
   "Pause zwischen Übungen" is always a slider 0-180 s in 5 s steps
   (0 = straight on): `#workoutCircuitRestSlider` (default 10 s),
   `#workoutRepsExerciseRestSlider` (60 s), `.combo-pause-slider`. Rest
   between Kraftplan SETS goes up to 300 s on purpose.
5. **Grundeinstellungen**: `MASTER_BG_TARGETS`, `CVD_EXERCISES`/`CVD_FB_SELECTORS`,
   restriction filters.
6. **Cardio-Zusatzaufgabe** parity for VT/NAT.
7. **Wochenplan**: `PLAN_AREAS`/`NAT_SUBS`, `historyAreaOf`.
Test-Bereich exercises are exempt until promoted out of Test (then this
applies as part of the promotion). Before calling it done, compare item
by item with a complete sibling (e.g. a new Workout mode vs. Tabata).
`tests/exercise_coverage_test.py` enforces 1-3 and the pause slider on
the live DOM; if it fails, fix the app, never loosen the test.

## Detail notes (docs/notes/) - read only what your task touches

Open the file for the area you change before touching its code; update
that file (not this one) when its details change. A new rule that applies
everywhere goes here, short.

| File | What is in it |
|---|---|
| 01-established-patterns-worth-reusing | stageTopClearanceY, hint/bar overlap rule, nav tab headroom, multi-select, presets, bg-colour rollout, makeBgApplier, live pause, swipe nav, FAQ |
| 02-known-open-items | parked ideas, NAT status (Positionen merken/Blitz/Flash/MOT), fixpoint, dark-mode hex rule, Dominanz, Zusatzaufgabe engine, live-pause-adjust |
| 03-master-einstellungen | Grundeinstellungen sheet, restrictions, code history, Farbschwäche-Unterstützung (CVD) |
| 04-startseite-heute-kalender-wochenplan | Heute, calendar, plan model, ?bereich= start parameter |
| 05-movement / 06-workout | Movement engine, duration, direction; Workout catalog, Tabata extras, sound cues |
| 07-ziel-signalfarbe... | SIGNAL_DEFS, Stroop colour weights |
| 08 / 09 recherche... | competitor/camera research, 20 researched exercise candidates (unbuilt) |
| 10-trainer-dashboard-worker-repo | dashboard.html, Worker API, Baukasten, deploys |
| 11 / 21 cardio... | Cardio domain, dual-task guests, live "+ Zusatzaufgabe" picker, full settings parity |
| 12-coach-code-boxes... | code boxes, movement-plan/cardio-plan types |
| 13-kombi-baukasten-rebuild | capture mode per domain, COMBO_CAPTURE_ENTRIES/EDIT_OPENERS |
| 14-19 | Master bg default, contrast hints, welcome text, pause markers, bg reset, Periph colours |
| 20-workout-kraft... | Kraftplan v1-v4, Töne & Ansagen, live pause editing, Cardio motivation, coach message, Mein Fortschritt, codes with validity/seats, backup, Hörmodus, privacy sheet, logo bar, step-nav « ↻ », phase wording |
| 22-client-security... | Worker hardening, Test unlock word, epilepsy note, open review items |
| 23-test-bereich | **Instructions for the "Test-Bereich" Routine** (read fully if woken by it), roster, open questions |
| 24-claude-md-langfassung-2026-10-05 | verbatim CLAUDE.md before the 2026-10-05 slimming (reasons, history) |

## Must-do rules collected from the detail notes

For every new or changed exercise/screen, in the same commit:
- Nothing on a stage under the hint or a player-bar button: place content
  via `stageTopClearanceY()`/`placeHintBelowBar()`, set hint text BEFORE
  measuring; add the exercise to `tests/hint_overlap_all_test.py`.
- Player/stage visuals use fixed hex colours, never `var(--...)`.
- No word broken mid-word, no overflow, tap targets ≥ 44 px, at 375-1366 px:
  new screens go into `tests/text_wrap_audit_test.py` (AREAS). Never give a
  text label a fixed width.
- Every area has the same frame (code card, tiles, Kombi-Programm,
  Gesamter Trainingsverlauf) - compare with a sibling before shipping.
- Right/wrong feedback or fixed colours: `CVD_EXERCISES`/`CVD_FB_SELECTORS`;
  fixed signal colour: `SIGNAL_DEFS` + `SIGNAL_CSS` + `data-sig` spans.
- Background colour: `makeBgApplier` + `wireBgIntensityControl` + `MASTER_BG_TARGETS`.
- Plannable on Heute: `PLAN_AREAS`/`NAT_SUBS` + `historyAreaOf`.
- VT/NAT exercise: Cardio guest parity (`CARDIO_GUEST_TYPES`, full settings,
  `prefsOverride` isolation) and Kombi capture/edit/playback.
- New localStorage keys start with `fwmc-` (backup picks them up).
- Anything that sends data off the device goes into the privacy sheet.
- Player conventions: exit button id `…BackBtn` + "Beenden", pause button
  id `…PauseBtn` + "Pause", class `.player` (gives step-nav, auto-pause,
  end-confirm for free).
- Einheitliche Steuerung (2026-10-05): a regular exercise without its own
  lead-in gets the shared 3-2-1 overlay (`LEADIN_START_IDS` in app.js, its
  start button must read "Training starten"); VT draws its own, Tabata/
  Kraftplan use "Bereit machen". Grundeinstellungen "Countdown 3-2-1 vor dem
  Start" (`masterPrefs.startCountdown`) and "Töne und Ansagen"
  (`workoutSoundPrefs.enabled`, also 🔊 `#stepSoundBtn` in the step bar).
  Tests that need an instant start seed `fwmc-master-v1` with
  `{"startCountdown":false}`. Every sub page gets the logo bar with its
  `.back-link` moved in as the round ‹ button (JS, from `.readyhead`); a new
  sub page only needs the usual `.readyhead > .back-link`.
  Logo mittig (2026-10-05): every top bar (`.brandbar`, `.app-bar-inner`)
  is one grid "back | logo + sub | gear", so the logo sits at the same
  place on every page; `--appbar-h` follows its height (light/dark).
- Tabs never wrap (2026-10-05): `.section-tab`/`.sub-tab` are nowrap, NAT
  sub-tabs a 2-/3-per-row grid; `tests/text_wrap_audit_test.py` flags a
  two-line tab. Answer keys grow with the screen (Flash keypad width capped
  by 66vh, `*-response-btn` zoom steps at 430/700/1000 px) and stay ≥ 44 px
  on a 375 px phone: `tests/tap_size_1005_test.py`. A new answer button
  named `…-response-btn` gets the scaling for free.
- New dashboard catalog entries: add them to dashboard.html's own copies too.
- Größe + Farbe (2026-10-05): an exercise that shows circles/characters/
  objects gets "Größe der …" (+ "Farbe der …" if it has text) via
  `LOOK_SPECS` in app.js: add a spec, put `<div class="look-host"
  data-look="…">` before the "Hintergrund" group of each ready screen, call
  `syncLook()` in its openers, copy the value into its state in start…Game
  and cap the size in the engine (no overlap, stays on the stage, tap targets
  ≥ 44 px). Cardio guest panel: `cardioLookFieldsHtml`. Test:
  `tests/start_install_look_1005_test.py`.
- Startbild + Startbildschirm-Hinweis (2026-10-05): `#appSplash` (teal +
  logo-white.png) fades out at the end of init (automated browsers drop it
  unless `fwmc-test-splash`); iOS startup images in `splash/` (made from the
  same picture, linked in build.sh), manifest background #007094. The Heute
  card `#installHint` shows once on phones/tablets in the browser
  (`fwmc-install-hint-dismissed`; tests force it with `fwmc-test-install`).
  A new logo means regenerating logo-white.png and splash/.
- Seitenübergänge + Wischen + Offline (2026-10-05): one MutationObserver on
  `hidden` animates every `.screen` (deeper = `tr-push` from the right, back
  = `tr-pop`, between area homes = `tr-fade`), `.player` (fade only, never a
  transform: engines measure rects at start) and `.done-panel` (`tr-rise`);
  reduced motion = fade. Off in automated browsers unless
  `fwmc-test-transitions`. Swipe from the left edge (≤ 28 px) clicks the
  visible `.bar-back-btn`. A new screen needs nothing extra. sw.js: network-
  first with a 3 s fallback to the cache (works offline); bump `CACHE` when
  the precache list changes. Test: `tests/swipe_offline_transitions_1005_test.py`.
- Untere Leiste (2026-10-05, Fabian "probieren wir aus"): fixed `#bottomNav`
  with Heute / Training (`#trainingHub`, tiles from `PLAN_AREAS` + Test when
  unlocked) / Fortschritt / Mehr (`#moreScreen`: code card, Grundeinstellungen,
  Tipps, FAQ, Datenschutz, Website, Impressum). The old 8-tab grid and the
  Heute "Bereiche" tiles are hidden via `body.has-bottom-nav`; area homes get
  a ‹ back to Training. Shown only while a `.screen` is visible (never in a
  player). Off in automated browsers unless `fwmc-test-bottomnav`. **Undo if
  Fabian says "zurück"**: set `bottomNavOn = false` in app.js (old layout comes
  back unchanged), or revert to merge 482c1f7 (state before the bar). Test:
  `tests/bottom_nav_1005_test.py`.
- Tests load `index.html?bereich=visual` (or the area); Test-Bereich tests
  pre-seed `fwmc-test-unlocked`.
