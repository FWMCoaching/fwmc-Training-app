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
before pushing. Automatic part of it: `tests/fabian_blick_test.py` walks every
screen/sheet/exercise start it can reach (iPhone 375/430, Android 360,
iPad 768/1024, laptop 1440 px; light/dark - Fabian 2026-10-06: every
device keeps the one design) and
checks error kinds (Umbruch, Überlappung, Tasten < 44 px, Kopfleiste,
Farben, Kontrast, Stil, alte Namen, Einfrieren nach Scrollen); known finds
sit in `tests/fabian_blick_baseline.json`, only new ones fail. Report and
screenshots: `tests/screenshots/fabian_blick/`. `tests/ios_gefuehl_test.py`
compares transitions/gestures with iOS plus the automatable points of
/mnt/project-files/app/benchmark-gute-app.md (KNOWN = open finds); the walk
also checks pressed states, light patches in dark mode, one primary button,
tabular timer digits. A new kind of
error Fabian finds becomes a check there. Anything Fabian still finds becomes a general automatic
check (the kind of error, not the single case).
**App-Gefühl is Claude's job (Fabian 2026-10-05: "Das musst du selbst
bemerken. Du bist der Experte")**: every release that touches navigation,
sheets, transitions or touch also gets checked against native iOS app
conventions, unasked - motion 0.3-0.4 s with a real slide (not a fade),
swipe back / pull down to close / tap active tab to top, grab bars, safe
areas, 44 px targets, no sticky hover. The reviewer prompt includes this. Once a quarter: the home
screen of every area (about 12 screenshots).

**Bundle releases (Fabian, 2026-10-04)**: bundle 3-4 changes per release,
full suite once at the end; while building run only the tests at hand. A
pure documentation change needs no suite run. Urgent fixes Fabian waits
on may go out alone. **Tests at night (Fabian 2026-10-07)**: during the
day only build (node --check, build.sh, preview), even 10-15 changes; the
full suite, reviewer and Fabian-Blick run as one batch at night, repairs
after it, then go live. Ideas go to Fabian first as a short list with a
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
  leaves fullscreen when its element got hidden. In a Kombi the button makes
  the whole page fullscreen (stays across Bausteine, Kombi end/abort leaves
  it); no Fullscreen API (iPhone) = `html.no-fs-api` hides every `…FsBtn`.
  A new player only needs `wireFullscreen` (docs/notes/13).
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
  "Dein Trainer stellt dir einen Plan zusammen, der genau zu dir passt: deine
  Übungen, dein Tempo, dein Ziel. Du bekommst dafür einen Code. Gib ihn hier
  ein." + the "Noch keinen Trainer?" link (JS, `PLAN_REQUEST_URL`); collapsed
  it reads "Dein persönlicher Trainingsplan / Code eingeben oder individuell
  angepassten Plan anfragen" (Fabian 07.10.).
- Client-facing text says "dein Trainer", never "Coach" or a name. The
  dashboard is the "Trainer-Dashboard".
- A deviation needs a real reason and goes to Fabian as a proposal first.
- Before every go-live: screenshot the new element next to a sibling
  (390px, light and dark) yourself; Fabian must never be the one to spot it.
- Dashboard follows light/dark (tokens in `:root` + prefers-color-scheme),
  uses Magra/Public Sans, never scrolls sideways at 390px (`.table-scroll`).
`tests/consistency_test.py` checks this; extend it for every new shared pattern.

## Hard rule: Feinheiten quer prüfen (Fabian, 2026-10-06)

"Wenn wir irgendwo an Feinheiten schrauben, immer prüfen, wo sie uns sonst
fehlen, damit es uns nicht in kleinen Schritten auffällt." Every new or
changed fine-tuning (live sound/volume/tempo, pause handling, size/colour,
dark player, lead-in, resume, fullscreen, presets ...) is checked, unasked,
against every sibling exercise in the same piece of work: build it where it
plainly fits, and list the rest for Fabian with a recommendation. The matrix
lives in /mnt/project-files/app/feinheiten-matrix.md - update it with every
such change.

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
the live DOM (since 2026-10-07 for every area on the Training page, read
from the hub, and every card of every area home; ready-made programmes are
not Bausteine); if it fails, fix the app, never loosen the test.

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
| 25-freier-baustein | Freie Bausteine area: model, kinds, Dehnen template, editor, player, Kombi/plan/history wiring |
| 26-erinnerungen | Push reminders before planned trainings: Grundeinstellungen section, payload, sw.js push, Worker /reminders + cron, deploy |
| 27-trainingsplanung | Plan model (phases, weeks A-D, pauses, weekOps, Sonderwochen, dayOv), planWeekMap, Mein Plan, scope question, trainer plan code + versions; nothing changes training automatically |
| 28-farbfelder | Farbfelder (VT, 2x2 mat grid): modes, rule function, Abfolge timing, Kombi/Cardio wiring, generic Hilfsmittel note |
| 29-huetchen-farbe-zahl | Hütchen · Farbe + Zahl (VT, 3-6 numbered fields): cnFields, colour cap, drawing, Kombi/Cardio/preset wiring |
| 30-farbbrille | Farbbrille (Rot-Grün-Brille, Test-Bereich): shared settings `fwmc-anaglyph-v1`, mandatory calibration `#anaglyphCalib`, lock `anaglyphGate`/`anaglyphStart`, pre-start hint, exercise "Jedes Auge zählt" |
| 31-aktivierung-optodrum | Aktivierung (8th area `activation`): frame, `ACTIVATION_LINKS` for later link cards; Optodrum: prefs, shared ready/pause controls, canvas engine, Wechsel, Sanfte Reize cap, Kombi/plan/history; shared renderer `optoPaint` + Bewegter Hintergrund (`MOVING_BG`) |
| 32-zusatz-rechnen | Zusatzaufgabe "Rechnen" (VT canvas + Cardio `addon-math`): statements, Doppelkreis/Nur stimmt/Laut, placement, scoring |
| 33-huetchen-laufweg | Hütchen · Laufweg (VT, cone map with drawn path): why VT-catalog architecture, path maker, variants, what is not wired |
| 34-ton-sequenz | Ton-Sequenz (Test-Bereich): step model, audio graph (merger, fades, cueVolume), Kanal-Test, Suchlauf, presets, safety, iPhone checks |
| 35-richtungskreuz-zusaetze-regeln | Richtungskreuz (VT, 4 directions, Farbregel), Zusätze für oben (`ZUSAETZE`, signal), ⓘ Regeln + Meine Notiz (`REGELN_EXERCISES`, notes in presets/Kombi, trainer note) |
| 36-qr-uebergabe | QR-Übergabe trainer → client: range screen, payload fields, split codes, import/dedupe, iPhone Safari copy + paste field, Kunden-Training (own store, snapshot of bests), in-app scanner, trainer codes as QR (`#code=`), Freischaltungen (`FEATURE_UNLOCKS`) |
| 37-neuro-aktivierung | Neuro-Aktivierung (hidden 9th area `neuro`, unlocked by code type `neuro-unlock`): step player, `NEURO_EXERCISES`, Kombi/plan only when unlocked, "Spezialübung von deinem Trainer" in trainer Kombi codes, dashboard builder, texts Fabian reviews |

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
  Gesamter Trainingsverlauf) - compare with a sibling before shipping. Order
  (hero, code card, Beispiel-Programme, exercises, Kombi, Verlauf; Kraft/
  Ausdauer exempt) is enforced by `tests/bereiche_reihenfolge_1008_test.py`.
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
  `{"startCountdown":false}`. Hütchen sortieren (VT start button, no
  canvas) and the first Kombi-Baustein (`startComboProgram`, unless VT/
  Kraft/Wim-Hof bring their own) also get it via `runLeadIn()` (2026-10-06).
  Ton (2026-10-06): every tone and spoken word goes through `cueVolume()`
  (🔊 off = 0, else `masterPrefs.volume`, the one "Lautstärke" in the
  Grundeinstellungen); a new sound multiplies its gain/`u.volume` by it and
  returns at 0. Gleichgewicht's own Lautstärke multiplies on top.
  Test: `tests/ton_lautstaerke_1006_test.py`. Takt-Ton (Reaktionstraining:
  `movementPrefs.tick/tickVolume` via `mvTickOf`, carried by Kombi/presets/
  Weitermachen; Gleichgewicht), Wim-Hof cues at every phase (`wimhofCue`)
  and Wim-Hof pause/3-2-1; MOT/Flash pause sheets change tempo for the run
  only. Test: `tests/takt_tempo_wimhof_1006_test.py`. Every sub page gets the logo bar with its
  `.back-link` moved in as the round ‹ button (JS, from `.readyhead`); a new
  sub page only needs the usual `.readyhead > .back-link`.
  Kopfleiste eine Zeile (2026-10-05, Fabian chose draft A, replaced "Logo
  mittig"): every top bar (`.brandbar`, `.app-bar-inner`) is one flex row
  "‹ back (sub pages) | logo | FWMC Online-Training | gear", 53 px
  (`--appbar-h`), thin bottom line; dark mode swaps in logo-white.png via
  CSS `content:url()` (no white plate). The title is always two lines
  "FWMC / Online-Training" (`.nowrap` span is a block) so it looks the same
  with and without ‹; under 380 px logo/text shrink, from 700 px they grow.
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
  with Heute / Training (`#trainingHub`: code card - moved here from Mehr,
  Fabian 2026-10-05, ids still `moreCode*` - and tiles from `PLAN_AREAS` + Test
  when unlocked) / Fortschritt / Mehr (`#moreScreen`: Grundeinstellungen,
  Tipps, Hilfsmittel, FAQ, Datenschutz, Website, Impressum). The old 8-tab grid and the
  Heute "Bereiche" tiles are hidden via `body.has-bottom-nav`; area homes get
  a ‹ back to Training. Shown only while a `.screen` is visible (never in a
  player). Off in automated browsers unless `fwmc-test-bottomnav`. **Undo if
  Fabian says "zurück"**: set `bottomNavOn = false` in app.js (old layout comes
  back unchanged), or revert to merge 482c1f7 (state before the bar). Test:
  `tests/bottom_nav_1005_test.py`.
- NAT wie Visual Training (2026-10-05): no sub-tab row; the 5 exercises are
  `.nat-tile` cards (VT tile look) under "Einzelne Übungen", variants are a
  "Modus" row on the ready screen (`NAT_MODES` in app.js; the mode buttons
  click the old hidden variant cards, so openers/Kombi/Heute stay as they
  are; last mode in `fwmc-nat-mode-v1`). A new NAT exercise needs a tile
  and, if it has variants, a `NAT_MODES` entry. Off in automated browsers
  unless `fwmc-test-natmodes`. Test: `tests/nat_modes_1005_test.py`.
- Stufen-Vorschlag (2026-10-05, Fabian's favourite idea): after 3 very good
  runs in a row on Leicht/Mittel, the result panel of Positionen merken,
  Blitz-Raster, Flash and MOT suggests the next difficulty
  (`levelSuggestAfter`, `LEVEL_SUGGEST_EX` in app.js, state in
  `fwmc-level-suggest-v1`); per exercise "nicht mehr vorschlagen", master
  switch `masterPrefs.levelSuggest` in Grundeinstellungen. Details and the
  assumed thresholds: docs/notes/02. A new NAT exercise with difficulty
  levels gets a `LEVEL_SUGGEST_EX` entry. Test: `tests/level_suggest_1005_test.py`.
- Eigenes Training (2026-10-05, first built as "Freie Bausteine", renamed by Fabian the same day; client-facing name everywhere is "Eigenes Training", one item is "ein Training"): 7th area `free` (`#freeHome`, Training hub
  tile, `?bereich=free`), the client's own activities as Abhaken / Mit Zeit /
  Checkliste in `fwmc-free-blocks-v1` + read-only templates (`FREE_TEMPLATES`,
  "Dehnen"). Kombi blocks keep their own copy (`{domain:"free", free}`),
  plan entries can name one (`what: "free:<id>"`), history kind `free`.
  A new template is one `FREE_TEMPLATES` entry. Details: docs/notes/25.
  Test: `tests/free_block_1005_test.py`.
- Erinnerungen (2026-10-05): Grundeinstellungen `#reminderGroup` (prefs
  `fwmc-reminders-v1`, not in backups). The app sends only the next 14 days
  as `{at, title, body}` + push subscription to the Worker (`POST/DELETE
  /reminders`, cron every 5 min, Web Push with VAPID); every `savePlan()`/
  `addHistory()` resyncs via `reminderPlanChanged()`. Reminder texts use area
  labels only, never free text or names. `REMINDER_VAPID_PUBLIC_KEY` in app.js
  is the deployed Worker's key (live since 2026-10-05; tests force the
  "not set up" state with `fwmc-test-reminder-key` = "off"). Details: docs/notes/26. Test:
  `tests/reminders_1005_test.py`, Worker: `cd worker && npm test`.
- Gesten (2026-10-05): tap the active bottom tab again = to the top /
  back to the tab's page; swipe the Heute calendar = ‹ / ›; ≡ drag handle
  reorders Kombi-Bausteine and checklist points (`wireDragReorder`, drop
  calls the same function as ↑/↓, which stay); long press on area tiles /
  exercise cards = `#tileActionSheet` (`LP_SEL`, `lpActions`). A new
  sortable list or tile kind hooks into these, details in docs/notes/01.
  Test: `tests/gestures_1005_test.py`.
- Erfolge spürbar (2026-10-05, Fabian: "Haken ja, kein Ton. Konfetti
  nein."): one observer on every `.done-panel` (`initDoneEffects` in app.js)
  draws the SVG check mark (brand #007094, ~0.6 s) when the panel opens with
  `.done-check` visible - aborted runs (`setDonePanelAborted`) get none. A
  new best: call `markBest(summaryEl, anchor, value)` right after setting the
  summary text ("Zahl ", 7); the number counts up, then pulses 3x (~2 s),
  "Neue Bestleistung!" gets its own line. textContent always holds the final
  value (counting digits are drawn via `::after`). Without `markBest` the
  phrase alone pulses. No sound, no confetti; reduced motion = final state.
  A new done panel only needs `.done-check` + `.done-summary`. Test:
  `tests/erfolge_onboarding_1005_test.py`.
- Erster Start (2026-10-05): 3 slides `#onboarding` (Willkommen / Heute +
  Training / Startbildschirm, swipe + dots + "Überspringen") only when
  `fwmc-onboarding-v1`, `fwmc-tips-seen` and the history are all empty;
  order Startbild → slides → tips sheet (`startOnboarding()` at start-up).
  The first close of the tips sheet rings the "Mehr" tab + toast
  (`showTipsWhereHint`). Off in automated browsers unless
  `fwmc-test-onboarding` / `fwmc-test-tipshint`. Same test as above.
- Wischen in Listen (2026-10-05, Fabian approved): swipe a list row left =
  "Bearbeiten" / "Löschen" behind it (iOS Mail style; touch only, one row
  open, swipe right / tap closes, direction after 10 px, not from x ≤ 28).
  Rows + actions in `SWIPE_ROWS` (app.js); actions call the list's existing
  functions (`askDeleteEvent`, `askDeleteFree`, `removePlanEntry`, the row's
  own ✎/✕), "Löschen" always via `confirmDialog()`. A new list with
  edit/delete = one `SWIPE_ROWS` entry + `touch-action:pan-y` in styles.css.
  Details docs/notes/01, test `tests/list_swipe_1005_test.py`.
- Trainer-Vorlagen per Code (2026-10-05): code type `free-template`
  (`{trainings:[…]}` in the Eigenes-Training shape) adds read-only templates
  "Von deinem Trainer" to `#freeHome` (`fwmc-free-trainer-v1`, ids
  `tr-<code>-<n>`, same code again = update); built in the dashboard
  (Bereich "Eigenes Training"). Worker stores configs generically, no deploy
  needed. Details docs/notes/25 + 10, test `tests/trainer_template_1005_test.py`.
- Zurück + langes Drücken + App-Gefühl A/B/C (2026-10-06): every deeper
  screen gets a browser-history entry (`histSync` in app.js, from the screen
  observer); popstate taps the visible ‹ (`edgeBackTarget`), so Safari's own
  edge swipe (Safari owns the left edge, our touch handler only works in the
  home-screen app), Android back and the browser back button all go back.
  In-app ‹ drops the entry silently. A new screen needs nothing extra.
  Long press: the sheet ignores clicks while the opening finger is down and
  250 ms after (`lpSheetBlockUntil`), contextmenu from a touch is ignored,
  tiles have no iOS callout/selection. Fabian-Blick checks both on every
  state ("zurueck", "lange"). `.screen > .start-btn[id$=StartBtn]` gets
  `.start-sticky`, wrapped in an opaque `.start-sticky-bar` (stays above the bottom bar, A; never use a transparent cover); Mehr list shows SVG › / ↗ (B);
  Heute calendar buttons ≥ 44 px, borderless SVG ‹ › in a row with the week
  range, heading names the week shown + "Heute" pill (C).
  Tests: `tests/history_back_1006_test.py`, `tests/app_feel_1006_test.py`.
- Kein Sprung nach Übergängen (2026-10-06, Fabian: Box-Atmung "wird auf einmal
  größer"): anything that slides sideways (screens in `tr-push`/`tr-pop`, the
  edge-swipe drag) must never make the document wider than the phone, or the
  phone zooms out and snaps back afterwards. `html,body{overflow-x:clip}` and
  `.screen.tr-push/.tr-pop{overflow-x:clip}` guard it; a new sideways animation
  stays inside a clipping box. Fabian-Blick "sprung" (mobile viewport,
  transitions on) checks every page on slide-in and edge swipe.
- Weitermachen, Schriftgröße, Kurzbefehle (2026-10-06): multi-block runs
  (Kombi, Workout-Plan, Atem-Programm, Trainer-Programm) store their block in
  `fwmc-resume-v1` (`resumeNote` in each start…Block, `resumeClear` in each
  finish…); Heute shows "Weitermachen" (Fortsetzen / Von vorne / Verwerfen)
  from block 2 on, max 3 days, below a planned training as one line. A new
  multi-block runner gets the same two calls + a `resumeRun` branch. Text
  sizes 10.5-22 px in styles.css are `calc(Npx * var(--ts,1))`; `--ts`
  follows the iPhone text size (`applyTextScale`, 0.95-1.25; tests:
  `fwmc-test-textscale`) - write new text sizes the same way, keep tabs
  capped (`min(var(--ts,1),1.05)`). The wrap audit also runs at x1.25/x0.9.
  manifest.json `shortcuts` (Android only) use `?bereich=heute|training|
  breath|fortschritt`. Install hint on iOS: "+ Zum Startbildschirm" shows
  `#installPointer` (arrow to Safari's share button, iPad: top).
  Test: `tests/resume_install_1006_test.py`.
- Design-Runde + Namen (2026-10-06, Fabian "Alles deutsch"): client-facing
  area names are Visuelles Training, Atemtraining, NAT ("NAT – Neuroathletik"
  as heading), Reaktionstraining (code: movement), Krafttraining (workout),
  Ausdauertraining (cardio), Eigenes Training; section tabs use the short
  forms Visuell/Reaktion/Kraft/Ausdauer; no "Name noch offen" tags. Old
  history entries keep their stored titles. `.code-card` is quiet and
  collapsed behind `.code-toggle` (test flag `fwmc-test-codequiet`);
  `.player.calm` (Atem, Wim-Hof) is dark petrol in dark mode; Fortschritt
  without history shows `#progressEmpty`; with the bottom bar the Kombi link
  shows only on Training (Heute dropped it, Fabian 06.10. abends). Weitermachen also for single Atem/
  Reaktionstraining runs (`fwmc-resume-single-v1`, ≥ 3 min, ≥ 30 s played),
  the card names the 3-day deadline. Sunday on Heute: Wochenabschluss
  (`#todayWeekReview`, check marks + one sentence + optional Vorsatz in
  `fwmc-week-intent-v1`, shown Mon-Sat). Tests: `tests/design_1006_test.py`,
  `tests/resume_week_1006_test.py`.
- Ruhige Kopfleiste, warmer Ton, dunkle Übungen (2026-10-06): main pages keep
  an empty 44 px ‹ slot (`.brandbar::before` when no visible back button), so
  logo/title never jump; the title's two lines sit on the logo's text lines
  (`--lg` = logo height drives size/offset; a hidden back button uses
  `visibility:hidden`, never `display:none`, and `barVis` ignores it). Tokens
  are warm (light bg #f7f4ef, dark bg #0c1b20). Heute greeting is a soft
  `.today-hello` card. In dark mode the lead-in and the players of Atem
  (`.player.calm`), Ausdauer, Eigenes Training and Krafttraining
  (`.player.calm-dk`) are dark; exercises whose background colour matters stay
  light. Test: `tests/design_1006_test.py`.
- Trainings-Übersicht (2026-10-06): the lower "Dazu" tiles are 2 per row
  like the core tiles (4 from 700 px), icon on top, names nowrap with a
  capped font (`.hub-extra`); never back to full-width rows. Headings
  (Fabian 06.10. abends): "Unser Schwerpunkttraining" / "Neurozentrierte
  Grundlagen gezielt trainieren." above the core tiles ("Unser" is the one
  deliberate "we" in the app), "Frei kombinierbar, auch mit den Bereichen
  oben." under "Dazu", then heading "Alles verbinden" + the Kombi tile
  (`.combo-entry-card`, Fabian 07.10. Variante H: calm tile, icon = four squares in the
  core area colours, filled from `HUB_CORE` in `renderHubAreaGrid`, so a dropped core
  area is replaced by a "Dazu" colour; Heute has none since 06.10. evening); tile texts
  start equally far left in both groups. Reaktionstraining keeps its core place with a
  `.hub-test-mark` "Test" pill (Test-Bereich colours, `HUB_TEST_MARK` in app.js,
  Fabian 07.10. while it is reworked; remove the key to drop it).
- Reaktionstraining neu + Test-Look + Tipps-Karte (2026-10-07): Anzeige
  `movementPrefs.layout` "zeilen" (rows of `rowLen` 3-5 glide up per frame,
  `mvRowsDraw`) / "feld" (still N x N page) / "band" (old strip; Vorschau +
  Laufrichtung only there); Symbole `figureStyle` felder/punkte/pfeil/figur/
  abstrakt ("Kreise"). Presets/Kombi/Weitermachen carry both via `mvLookOf`
  (no layout = band). An area that is open but unfinished gets `.test-look`
  on its screens (Test yellow kicker/bars/tab) + `.test-note` "Noch im Test"
  + `HUB_TEST_MARK`. Heute `#todayTipsCard` (between week and progress)
  until "Ausblenden" (`fwmc-tips-card-hidden`, toast "unter Mehr").
  Test: `tests/reaktion_anzeige_1007_test.py`.
- Gleichgewicht + Größe live (2026-10-06): 6th NAT exercise (letter sticks,
  Nein-Nein/Ja-Ja/Ohr-Schulter/Diagonal/Sakkaden, metronome, sets or open-ended,
  stance shown/spoken, drag + pinch, live tempo/Takt/Zeit anhalten/Lautstärke);
  details docs/notes/02 (letter colour per stick, colours/length/width/font
  live in the pause sheet, one-time silent-switch hint; music like Spotify keeps playing). Every LOOK_SPECS exercise also gets its size live in the
  pause sheet and by pinch (`LIVE_LOOK`); a new one needs one entry there.
  Tests: `tests/gleichgewicht_1006_test.py`, `tests/live_size_1006_test.py`.
- Antwort-Tippen + Pause-Tempo (2026-10-07): game answer buttons (Positionen
  merken, Blitz-Raster, MOT, Flash keys) count on pointerdown via
  `onGameTap(el, fn)` (iOS drops clicks on a slide or second finger); a new
  answer button uses it and joins `GAME_TAP_SEL` (never half of a pinch).
  Pause sheets of all four edit timing and "Bei Fehler" for this run only
  (`addPauseChoiceRow` clones the ready row). Test: `tests/nat_pause_tempo_1007_test.py`.
- Haken & Kreuz (2026-10-07): off by default; An/Aus in every fb exercise's
  pause sheet; weak green/red contrast on the chosen background asks once at
  the start (`FB_HINT_STARTS`, NAT). `confirmDialog(text, onYes, {title, yes,
  no, onNo})`. Details docs/notes/03, test `tests/fb_haken_1007_test.py`.
- Tippen beim Aufsetzen everywhere (2026-10-07): every game tap target is in
  `FAST_TAP_SEL` (one delegated pointerdown listener); a new answer button or
  tap area joins it unless its handler needs the tap coordinates.
- Hilfsmittel (2026-10-07): an exercise that needs equipment gets one
  `HILFSMITTEL` entry in app.js (text + optional `link`, shown only when set);
  the VT ready screen renders it as `.hilfsmittel-note`. Details docs/notes/28.
  A new Hilfsmittel = one HILFSMITTEL entry (`gear`) + its `GEAR_ITEMS` card
  (page "Hilfsmittel und Starterpaket" under Mehr, `#gearScreen`, 2026-10-08).
  Meine Hilfsmittel (2026-10-08): ticks in `fwmc-gear-v1` (Grundeinstellungen,
  page, "Hab ich"); unticked `gear` = card greyed + start "Braucht: …" with
  one confirmDialog, never blocked; `optional: true` never greys, `anyOf: true`
  needs one. Automated browsers own everything unless `fwmc-test-gear`.
  Details docs/notes/28, test `tests/meine_hilfsmittel_1008_test.py`.
- Sanfte Reize (2026-10-07): Grundeinstellungen "Sehen und Reize"
  (`masterPrefs.softStimuli`, + Schriftgröße `textSize` on top of `--ts`).
  Every exercise with fast light changes honours it: VT canvas exercises get
  it for free (`vtShowS`/`softGap`/cross-fade); any other engine adds one
  `SOFT_EXERCISES` entry (ready screens get the "Sanfte Reize sind an" note +
  override, the pause sheet the live switch) and reads `softOn(ex)` for
  longer minimum times / softer fades. Details docs/notes/03.
- Aktivierung (2026-10-08): 8th area `activation` (`#activationHome`, hub
  "Dazu" tile, `?bereich=aktivierung`), own exercises in `ACTIVATION_EXERCISES`
  (plan `what: "act:<id>"`), existing exercises later as one
  `ACTIVATION_LINKS` entry each (never a copied engine). First exercise
  Optodrum (`#optoReady`/`#optoPlayer`, Kombi domain `optodrum`). A new area
  needs: PLAN_AREAS + `--area-<key>` token, home screen in SCREENS/
  AREA_HOME_IDS/HOME_SCREENS/HISTORY_PREFIXES, `?bereich=`, a Kombi group,
  `historyAreaOf`. Details docs/notes/31, test `tests/aktivierung_optodrum_1008_test.py`.
- Bewegter Hintergrund (2026-10-08): the Optodrum pattern (`optoPaint`/`optoAdvance`, one
  renderer) behind Gleichgewicht, Positionen merken, Flash. A new exercise gets it via one
  `MOVING_BG` entry + `mbg: mbgCopy(p.mbg)` in its run state + `mbgStart(kind)` (controls in
  Feineinstellungen and the pause sheet come for free). Gleichgewicht also has "Wörter"
  (`content`). Kombi/Trainer-Programm block scores: `blockResultPush(run, label, text)`.
  Details docs/notes/31 + 02.
- Zusatzaufgabe-Arten (2026-10-08): "Zeichen am Rand" and "Rechnen"
  (`#addonTaskRow`, entry `task`); a new kind = one `task` value, its body
  in `#addonGroup`, a branch in `buildAddonSchedule`/`drawAddonOverlay`/
  `finishSession`, a Cardio type appended LAST to `CARDIO_GUEST_TYPES`
  (picker tests count the types). Overlay taps stop propagation on
  pointerdown so host taps never see them. Details docs/notes/32.
- Tones on purpose (Ton-Sequenz, 2026-10-08): every audible tone goes
  through `cueVolume()`, starts with a fade-in, ear choice via
  ChannelMerger; docs/notes/34.
- Zusätze für oben (2026-10-08): a new Zusatz = one `ZUSAETZE` entry (sheet,
  chips, notes, Regeln, presets, Kombi, codes follow); an exercise done by
  stepping joins `ZUS_EXERCISES`. Signal Zusätze only through cueVolume().
- ⓘ Regeln + Meine Notiz (2026-10-08): every exercise with rules gets ⓘ via
  `REGELN_EXERCISES` (VT catalog exercises automatically via "@vt" +
  `vtRuleLines`, which must describe a new VT type's settings; NAT/other
  engines one entry: ready screens, bar, pause overlays, domain). The bar ⓘ
  pauses via the visible `…PauseBtn` and resumes via `…ResumeBtn`.
  Details docs/notes/35.
- QR-Übergabe (2026-10-08): history entries travel only in the URL
  fragment (`#import=`), never via a server; a new history field that
  Fortschritt needs goes into `hoPack`/`hoUnpack`. Anything that records a
  run goes through `addHistory()` (Kunden-Training diverts it there), and a
  new per-exercise best/level store is named `fwmc-…-best-v1` or added to
  `HO_SNAP_RE`. `qrcode.js` and `jsqr.js` (vendored) belong in every
  Artifact publish. Trainer tools ("An Kunden übergeben", "Kunden-Training
  starten") only after a `feature-unlock` code with `trainer-tools`
  (`fwmc-features-v1`); "Trainer-QR-Code scannen" (in-app camera,
  BarcodeDetector or lazy jsQR) is always there and reads handover codes
  and trainer codes (`#code=<CODE>` or bare; same path as the code card,
  `openCodeAsTyped`). Details docs/notes/36, tests
  `tests/qr_uebergabe_1008_test.py`, `tests/pruefer_fixes_1008_test.py`.
- Freischaltungen (2026-10-08): code type `feature-unlock` (several
  features per code, `lock` hides again); a new unlockable feature = one
  `FEATURE_UNLOCKS` entry in app.js (label, toast texts, screen, `apply`,
  automatic `body.feat-<key>`) + one entry in dashboard.html's copy. Every
  trainer code can be shown as QR in the dashboard ("QR-Code zeigen").
- Prüfer-Runde (2026-10-08), everywhere: one checkbox style (brand accent,
  22 px in rows); a player bar with ⓘ stays one row from 360 px (icon
  buttons ≤ 480 px, short status via `barCompact()`); colour meanings are
  chip rows (`colorChoiceRowsHtml`), never a `<select>`; German "1,5 s" and
  "80 %". Details docs/notes/01.
- Trainer-Menü (2026-10-08 abends): the `trainer-tools` unlock shows a round
  button in the ‹ slot of the main pages; modes Mein Training / Mit Kunde /
  Ausprobieren ("Test"), all trainer stores 14 days, selection before every QR,
  overview "Gespeicherte Trainings"; sent runs leave history + Fortschritt,
  deleted own runs are only hidden. Anything that records a run still goes
  through `addHistory()` (it diverts by mode). Details docs/notes/36. A button
  must stay readable on its background in light and dark:
  `tests/knopf_lesbar_1008_test.py` (contrast ≥ 3:1 everywhere).
- Neuro-Aktivierung (2026-10-08): hidden area `neuro`, visible only after a
  `neuro-unlock` code (`fwmc-neuro-unlocked-v1`; tests seed `fwmc-test-neuro`).
  Anything that lists areas/exercises (hub, PLAN_AREAS, Kombi groups, tray,
  gear cards) must follow `neuroUnlocked()`; neuro blocks in a trainer Kombi
  code always play, tagged "Spezialübung von deinem Trainer" when locked, and
  never get copied into own Kombis (`neuroStripBlocks`). A new template = one
  `NEURO_EXERCISES` entry + dashboard `NEURO_EX`. Details docs/notes/37, test
  `tests/neuro_aktivierung_1008_test.py`.
- Pausen mit Atemführung (2026-10-08): `masterPrefs.pauseBreath` (Grundeinstellungen,
  off). A new rest pause wraps its countdown in `.breath-host` + a hidden
  `.breath-label` and calls `breathGuideFor(host, label, pauseS)` / `breathGuideStop`
  (one helper, also the trainer pause; < 10 s = plain countdown; the countdown
  stays full size inside the circle). Details docs/notes/03, test
  `tests/atemfuehrung_1008_test.py`.
- Termin-Serien (2026-10-08): own events `repeat` weekly/biweekly (no end, `skip[]`);
  anything reading events by date uses `eventsOn`/`eventNextDate`, planning
  recommendations `loadSingleEvents`. A choice "only this / all" uses
  `confirmDialog(..., {cancel})` so tapping beside never deletes. docs/notes/04.
- Tests load `index.html?bereich=visual` (or the area); Test-Bereich tests
  pre-seed `fwmc-test-unlocked`.
