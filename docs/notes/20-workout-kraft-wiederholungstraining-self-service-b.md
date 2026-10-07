# Workout: Kraft-/Wiederholungstraining self-service builder (added 2026-09-30)

Closes a backlog item from the Kombi-Baukasten rebuild: Workout's "reps"
block (`{kind:"reps", exercise, sets, reps, restS}`) was, until now,
coach-plan-only - a client could run a fixed sets×reps block a coach set
up for them, but had no client-facing screen of their own for it (unlike
every other domain, and unlike Workout's own Tabata/circuit mode, which
already had `workoutTabataReady`). The client explicitly asked to close
that gap with real, researched rep-range guidance rather than just a bare
number picker - see the exercise-science research summary earlier in this
session (rep-range literature, time-under-tension research, double
progression) for the sources this is built on. Short version of what that
research actually says, since it shapes the design below:

- The classic strength/hypertrophy/endurance rep-range split (1-6 / 6-12 /
  15-20+) is still a reasonable rule of thumb, but Schoenfeld & Grgic's
  2021 "repetition continuum" re-examination shows proximity to failure
  matters more than the exact rep count - hence these are offered as
  presets with an explanatory hint, not hard-enforced boundaries.
- Time under tension is NOT an independent lever (Schoenfeld et al. 2015
  meta-analysis: 0.5-8s per rep gave similar hypertrophy) - it's really
  reps×tempo. So the new live set-timer is **informational only** and
  never gates anything; only reps actually achieved feed progression.
- "Double progression" (reps up to the top of the range, then increase
  load, drop back to the bottom) is the standard, well-supported practical
  method for progressive overload - that's what the suggestion nudge
  below implements.

**New client-facing screen** (`workoutRepsReady`, opened from a new
"Kraft-/Wiederholungstraining starten" card on `workoutHome`, parallel to
the existing "Intervall-Timer starten" card):
- Exercise picker (`workoutRepsExerciseGrid`) - single-select cards
  reusing the same `WORKOUT_EXERCISES`/`customWorkoutExercises` catalog
  and icon set the Tabata circuit builder already uses (shared "+ Eigene
  Übung hinzufügen" list - an exercise added from either screen appears in
  both). `.combo-add-btn.active` is a new CSS state added for this single-
  select use; every other use of that class (the circuit builder's "add to
  list" cards) has no selected state of its own.
- Rep-range presets (`REP_RANGE_PRESETS`: Kraft 1-6, Muskelaufbau 6-12,
  Kraftausdauer 15-20) each with a one-line research-backed hint text, plus
  a fourth "Eigener Bereich" choice with its own min/max sliders
  (`repRangeFor()` resolves whichever is active to a concrete `{min, max}`).
- Sets (2-5) and rest-between-sets (15-180s) choice-row/slider, same
  pattern as everywhere else in the app.

**Player-side additions** (all gated behind `block.rangeMin != null`, so
an existing fixed-`reps` coach-plan block - see `workout_combo_test.py` -
renders exactly as before, byte-for-byte): `renderRepsView()` shows the
range ("6–12 Wiederholungen") instead of a single number, starts a live
per-set stopwatch (`startWorkoutSetTimer()`/`stopWorkoutSetTimer()`,
`#workoutSetTimer`, informational per the research above), and shows a
"Geschafft" -/+ stepper (`#workoutRepsInputRow`) defaulting to the TOP of
the range - "aim to make the last rep genuinely hard" - instead of the
old blind "Satz erledigt". `workoutState.achieved` collects what was
logged each set.

**Double progression** (`recordWorkoutRepsProgress()`, keyed by exercise
id in `fwmc-workout-reps-progress-v1`): once a standalone (not coach-plan,
not combo - those have their own next-block flow with no natural place to
interrupt) reps-range block finishes, if EVERY set's logged reps reached
the top of the range, the done screen shows a "stark - nächstes Mal
schwerer machen?" suggestion (`#workoutDoneSuggestion`), and the same
exercise's ready screen shows the same nudge on the next visit
(`#workoutRepsSuggestionHint`) until the client trains it again.

**Two small pre-existing-pattern fixes needed along the way**:
`workoutAbort()`'s "Beenden" used to hardcode `showScreen("...
workoutTabataReady")` for every standalone (non-plan) block - fine when
Tabata/circuit was the only standalone mode, wrong for this one. Replaced
with `workoutStandaloneReturnScreen`, a variable each standalone start
function sets before calling `startStandaloneWorkoutBlock()`. And
`workoutBlockMeta()`'s "reps" branch now shows `sets×min–max` when
`rangeMin` is present, `sets×reps` otherwise (used by the coach-plan
overview list and the combo-transition screen).

Test: `tests/workout_reps_builder_test.py` - presets show their research
hint text and swap correctly to/from the custom range; the exercise grid
single-select and its "eigene Übung" flow both work; a 2-set run shows
the correct range, an advancing live timer, and a reps-input defaulting
to (and resetting to, each set) the top of the range; hitting the top on
every set produces the done-screen suggestion, which then persists onto
the ready screen's own hint on the next visit; "Beenden" mid-set returns
to `workoutRepsReady` specifically, not Tabata's ready screen; the new
elements stay fully hidden/inert on a fresh page load with no session
active. `workout_combo_test.py`/`workout_circuit_combo_test.py` (existing,
unmodified) confirm the coach-plan fixed-reps path and Tabata/circuit are
both untouched.

**Kombi-Baukasten integration** (added same day, once the client asked
whether Tabata/Wiederholungstraining/Cardio blocks could be freely mixed
and repeated within one combo): built via `openWorkoutRepsComboCapture()`/
`exitWorkoutRepsComboCapture()`/`commitWorkoutRepsComboCapture()`, the
exact same "reopen this domain's own ready screen" pattern as the circuit
block's own `openWorkoutComboCapture()` - added as a second entry in
`COMBO_CAPTURE_ENTRIES.workout` (`"Kraft-/Wiederholungstraining"`,
alongside `"Eigener Zirkel"`), with `COMBO_EDIT_OPENERS.workout` now
dispatching on `block.kind` to reopen the right one. A captured block
always stores an explicit `rangeMin`/`rangeMax` (never a preset key) - re-
editing lands on "Eigener Bereich" with those exact numbers prefilled,
not a guess at which named preset (if any) they came from. No runtime
engine changes were needed at all: `runWorkoutBlock()`/`workoutBlockLabel()`
/`Meta()`/`Seconds()` already dispatched on `block.kind`, and the range-
mode reps view only ever checks `block.rangeMin != null`, so a `kind:
"reps"` combo block just works.

The general answer this unblocks: **the Kombi-Baukasten draft is a plain
ordered array** (`comboDraftBlocks`) - every domain's "add" entry pushes
one block onto it, with no cap and no dedup, so any block type (Tabata/
circuit, Kraft-/Wiederholungstraining, Cardio, or anything from any other
domain) can be added any number of times, in any order, freely
interspersed with anything else. This was already true for Tabata and
Cardio before today; only the reps builder was missing a capture-mode
entry to join them. `renderComboBlockList()`'s `editOpener` guard still
excludes one thing: a plain fixed-number `kind:"reps"`/`kind:"tabata"`
block with no `rangeMin` (coach-authored, or predating this rebuild) has
no settings screen to reopen and stays non-editable - every block a
client can *add* through the builder is always editable.

Test: `tests/workout_reps_combo_test.py` - the entry is offered and
opens retitled ("Baustein: ..."); 6 interspersed blocks (Zirkel/Kraft-
Wdh./Zirkel/Cardio/Kraft-Wdh./Cardio) can be added in one draft, each
reopening fresh (no leftover state bleeding from one capture session to
the next); editing an already-added reps block reopens it correctly
prefilled and persists changes; a range-mode reps block plays back
correctly (right range, live timer, reps-input default) when reached
mid-combo-run, and aborting mid-block during a combo still works.

### Kraftplan: several exercises stacked, like Tabata (2026-10-02)

Client report: "Die Kraftübungen können nicht gestackt werden" - the
reps builder above only ever held ONE exercise, standalone and as a
Kombi-Baustein (several single-exercise Bausteine were possible, but not
one plan). Rebuilt `workoutRepsReady` into a Kraftplan builder that
mirrors the Tabata Zirkel builder: add-grid with info button + "+" and
a "N× im Plan" badge, an ordered item list, saved plans
(`fwmc-workout-reps-saved-v1`), and a "↑" button to reorder (Tabata has
none - cheap here and useful for strength order).
- **Per item** (`workoutRepsPrefs.items[]`: `{exercise, rangeKey,
  customMin, customMax, sets 1-10, restS 15-300, note}`): own range
  (select: the 3 presets or "Eigener Bereich" with min/max steppers),
  own sets, own Satzpause, own note (e.g. the weight used).
- **Plan-level pauses**: "Pause zwischen Übungen" (`exerciseRestS`,
  0-180s in 5s steps, default 60, 0 = straight on) and, in Feineinstellungen, a
  "Vorbereitungszeit" start countdown (`prepS`, 0-30s, default 10). The
  old range/sets/set-rest controls moved into Feineinstellungen as the
  **defaults for newly added exercises** (set-rest range widened to
  15-300s). No cool-down: a reps plan has no timed phase to append one to.
- **Block shape** played by the engine: `{kind:"strength", items:[{exercise,
  rangeMin, rangeMax, sets, restS, note}], exerciseRestS, prepS}`, built by
  `buildStrengthPlanBlock()`. `startStrengthBlock()` runs it on the same
  reps view/state as a single "reps" block (`workoutState.block` = current
  item, `workoutState.strength` = whole plan); `startRepsRest(s, mode)`
  takes `"set"`/`"item"`/`"start"` and labels the countdown accordingly
  ("Pause", "Pause – Übungswechsel" + "Als Nächstes: …", "Bereit machen").
  Set info reads "Übung 2 von 3 · Satz 1 von 4". Double progression is
  recorded per item at the end (standalone only, as before).
- **Kombi**: the whole Kraftplan is ONE Baustein (`kind:"strength"`),
  edit-in-place; re-editing maps an explicit min/max back to its preset
  when it matches one. An older single-exercise range-mode `kind:"reps"`
  combo block still plays and reopens as a 1-item plan (saved back as
  `strength`). Plain fixed coach "reps" blocks are untouched.
- **Migration**: an old saved single `exercise` becomes a 1-item plan.
Tests: `tests/workout_reps_builder_test.py`, `tests/workout_reps_combo_test.py`
(both rewritten for the plan builder).

### Kraftplan v3: Art, Pause danach, Supersatz (2026-10-02)

Fabian: a base pause for the whole plan, but every exercise may deviate
("ohne dass es unübersichtlich wird"), plus Supersätze, Pyramide and
isometric holds inside the reps plan. Tabata stays Tabata; mixing timed
circuits with reps goes through Kombi.
- **Art** per item (`mode`): `"range"` (as before, the only one with
  double progression), `"pyramid"` (`pyrFrom` -> `pyrTo` over `sets`
  steps, `pyrBack` adds the way back: 10-8-6-8-10), `"time"` (`holdS`,
  5-300 s; player shows "Halten starten", counts down with 3-2-1 beeps and
  completes the set itself, "Fertig" ends early). Plank/Wandsitz
  (`STRENGTH_HOLD_EXERCISES`) start as `"time"`.
- **Pause danach** (`restAfterS`, null = plan's `exerciseRestS`, 0-180 s)
  and **Supersatz** (`supersetNext` + `supersetGapS` 0-60 s) live in a
  folded "Pause danach / Supersatz" `<details>` per item (none on the last
  item); open state survives re-renders (`strengthOpenOptions`).
- **Engine**: `buildStrengthSteps(plan)` flattens the plan into sets, each
  with the pause that follows it. Linked items form a group played round
  by round (A1 B1 A2 B2; 3+ linked items = Zirkelsatz); the round pause is
  the group's FIRST item's `restS` (partners show a hint instead of their
  own stepper), after the last round comes the last member's pause-after.
  `strengthItemBlock()` precomputes `repsList` because its `sets` is the
  already-expanded pyramid count - recomputing from it doubled the pyramid
  (real bug, caught by the test).
- Fabian picked from the idea list: everything except EMOM (left out).
Test: `tests/strength_modes_test.py`.

### Kraftplan v4: Maximal, Seite, Tempo, Aufwärm- und Dropsätze (2026-10-02)

Same day, Fabian: offer "Maximal", build Dropsatz, Seitenwechsel "sehr
wichtig" (one arm/leg, also on machines, neuroathletic relevance), Tempo
and Aufwärmsätze (fixed reps or just a placeholder) - "muss clean aussehen".
- New Art `"amrap"` ("Maximal (so viele wie möglich)"): sets only; the
  reps input starts at this exercise's last logged number (10 at first).
  No double progression (range items only).
- Per item, folded in a second `<details class="strength-more">` ("Mehr
  Optionen", summary lists what is active, open state in
  `strengthOpenMore`), on every item incl. the last: `side` (both/lr/rl/
  l/r, `STRENGTH_SIDE_LABELS`) + `sideGapS` (0-60, default 5, only for
  lr/rl), `tempo` (free text ≤12, hidden for holds, shown in the player's
  note line as "Tempo …"), `warmupSets` 0-3 + `warmupReps` (0 = "frei")
  + `warmupRestS` (0-180, default 30), `dropSets` 0-3 (hidden for holds).
- Engine: `strengthExpandSet()` turns each set into one sub-set per side;
  the last working set of an item is followed on each side by its drop
  sets (rest 0, mode "drop" - straight on); between sides a "Seitenwechsel"
  pause; only the final sub-set carries the set's real pause. Warm-ups of
  all group members come before the group's first round. Steps carry
  `kind` (work/warmup/drop), `side`, `dropIdx`/`dropTotal`.
  `currentRepsMode()` returns "warmup"/"drop" for those steps (no reps
  logging, never progression), the item's mode otherwise.
  `strengthStepLabel()` feeds the "Als Nächstes" line (also on a side or
  warm-up -> work change within one exercise).
- EMOM (every minute on the minute) deliberately not built.
Test: `tests/strength_extras_test.py`.

### Töne & Ansagen + "Alle entfernen" (2026-10-02)

Fabian: an X to empty a whole built list (with "Bist du sicher? Ja/Nein"),
and configurable sounds/announcements, Master first, each area able to
deviate in its own Feineinstellungen.
- **"Alle entfernen"**: `.list-clear-btn` in the list title of Tabata-Zirkel
  (`#workoutCircuitClearBtn`), Kraftplan (`#workoutRepsClearBtn`), Cardio
  (`#cardioClearBtn`) and Kombi (`#comboClearBtn`), hidden while empty.
  Asks through the in-app `#confirmSheet` (`confirmDialog(text, onYes)`),
  never the browser's `confirm()`. Reuse `confirmDialog` for any new
  destructive one-tap action.
- **Settings shape**: `masterPrefs.cues` = `{countdownS 0|3|5, countStart,
  countEnd, tickS 0|10|15|30|60, announceNext, announceNote, announceHalf,
  announceLastRound, announceLastSet}` (`normalizeCueCfg`), plus
  `masterPrefs.cuesIgnoreSilent`. Per area (`tabata`/`strength`/`cardio`/
  `kombi`) an optional full copy in `fwmc-cue-overrides-v1`; `cueCfg(domain)`
  returns the override or the Master. UI is rendered by JS into
  `#masterCuesGroup` and each `#cueDomain_<domain>` (choice "Wie Master-
  Einstellungen" / "Eigene Einstellung", the latter seeded from the Master;
  `CUE_FIELD_LABELS` decides which options an area shows and their wording).
  Cardio and Kombi got a new "Feineinstellungen" `<details>` for this.
- **Playback**: `playCueTone()` (beeps 880 Hz short / 1180 Hz long, Takt-Ton
  620 Hz soft), `cueSay()` (device speech synthesis, queued, de-DE), both
  muted by the existing speaker toggle (`workoutSoundPrefs.enabled`).
  `cueCountdownBeep`/`cueTickCheck` fire each mark once per phase. Countdown
  "Aus" also drops the long transition beep (`cueTransitionBeeps`).
  - Tabata (`circuitTick`, `cueTabataFrameStart`): countdown to every work
    start/end, Takt-Ton in work phases, in each pause the next exercise
    (+ note if the pause is ≥ 8 s), "Letzte Runde" before the last pass,
    "Halbzeit" at half the total time (≥ 60 s).
  - Kraftplan (`startRepsRest`, `cueStrengthRestStart`, `startWorkoutHold`):
    countdown at the end of every pause (incl. "Bereit machen"), countdown +
    Takt-Ton in holds, at pause start "Halbzeit" (half the steps), "Letzter
    Satz" (once, not again for the second side), next exercise only when it
    changes, else "Seitenwechsel".
  - Cardio (`cueCardioTick`/`cueCardioAnnounce`): long beep at every
    activity/pause/interval-phase change with countdowns before them, Takt-
    Ton, next activity (+ its label as the "note"), "Letzte Aktivität",
    "Halbzeit".
  - Kombi (`showComboTransition`): next Baustein, "Letzter Baustein",
    countdown at the end of the pause.
- **iPhone silent switch** (checked 2026-10-02, not on a device): iOS puts
  web audio in the "ambient" session, which the switch mutes on the speaker
  (not on headphones); media volume alone doesn't help. The opt-in "Töne
  auch bei eingeschaltetem Stummschalter" sets `navigator.audioSession.type
  = "playback"` (Safari 17+), which plays through the switch but usually
  pauses other music. Needs a real-device check by Fabian.
- Vibration: parked until there is a native app (iPhone web apps can't).
Test: `tests/cues_test.py` (fake AudioContext records tones, `window.__cueLog`
records spoken texts).

### Pause während des Trainings: Pausen live bearbeiten (2026-10-02)

Fabian: while training, tap "Pause", change the pause running now (or the
one after the current exercise), open an overview to change every later
pause, then carry on exactly where it stopped. One shared sheet,
`#trainPauseOverlay` (`openTrainPause(adapter)` / `closeTrainPause()`,
next to `showComboTransition`), which JS moves into the running player.
Each domain passes an adapter `{host, pause(), resume(), current(),
list()}`; rows are `{title?, label, sub, get(), set(v)}`, ±5 s steps
snapped to the 5 s grid, 0-600 s.
- Tabata/Zirkel (`#workoutPauseBtn`, `circuitPauseAdapter`): pause frames
  are `prep`/`rest`/`setrest`; `circuitSetFrameDur()` shifts every later
  frame and `total`. While paused `workoutState.pausedAt` is set and the
  visibilitychange handler leaves `startTime` alone (no double shift).
- Kraftplan (same button, `repsPauseAdapter`): the rest countdown now
  lives in `workoutState.restRemaining`/`restTick`; hold timers read
  `st.holding.t0`, the set stopwatch keeps `workoutSetTimerT0`, so both
  resume without losing time. Later pauses = each step's `rest` (drop
  sets excluded).
- Cardio (`#cardioPauseBtn`, `cardioPauseAdapter`): edits the pause
  pseudo-items; a missing pause (0 s) can be added (spliced in).
- Kombi (`#comboTransitionPauseBtn` on the pause screen): the countdown is
  `comboTransitionState {remaining, run, stop}`. Every adapter's overview
  also lists the Kombi pauses still ahead when running inside a Kombi
  (`comboPauseRows`, edits a per-run copy of the def, saved Kombis stay).
- `hideAllPlayers()` closes the sheet, so Beenden while paused is safe.
Test: `tests/train_pause_edit_test.py`.

### Cardio: Hintergrund, Motivation, Zusatzreize an freien Stellen (2026-10-02)

Fabian: a background colour for Cardio, a big motivation field (image or
quote) per activity, Zusatzreize only where the quote/image isn't
("wirklich nur fein da, wo Buchstaben sind"), and a gallery that changes
on its own. Cardio only - in other areas the field would be in the way.
- **Hintergrund**: `cardioPrefs.bgColorKey/bgIntensity/bgCustom`, tints the
  whole `#cardioPlayer` (`applyCardioBg`), wired through
  `wireBgIntensityControl` on the ready screen ("Hintergrund & Motivation",
  `#cardioLookAdvanced`) and in the shared pause sheet (`#cardioPauseBgGroup`,
  shown only when the adapter carries `bgGroup`). In `MASTER_BG_TARGETS`.
  Cardio stage text is now fixed hex (was `var(--ink)`, a dark-mode bug).
- **Motivation per activity**: `item.motiv = {mode: keine|spruch|bild|galerie,
  text, imageId}`, a select under each activity in the list. Shown in
  `#cardioMotiv` while that activity runs (not in pauses).
  `copyCardioItem()` deep-copies items incl. `motiv` everywhere items are
  copied (saved units, Kombi capture, coach plans).
- **Images** never leave the device: canvas-compressed JPEG (max 900 px)
  in `fwmc-cardio-images-v1` (`{id: dataURL}`), items/gallery hold only
  the id. A full storage shows a hint instead of failing silently.
  `pruneCardioImage(id)` deletes an image only when no other localStorage
  value (and no in-memory Kombi draft/capture) still mentions its id.
- **Galerie**: `cardioPrefs.gallery` (quotes and images),
  `galleryChangeS` 15-600 s, `galleryOrder` zufall (no immediate repeat
  across reshuffles) or reihe; `cardioState.gallery` tracks position and
  shifts with the pause like every other timestamp.
- **Inline Zusatzreiz**: when the guest is `addon-flash`/`periph-flash` AND
  the motivation box is visible, `triggerCardioGuest()` starts
  `startCardioInlineFlash(cfg)` instead of a takeover: Cardio keeps running,
  characters flash in `#cardioFlashLayer` using the guest cfg (kind,
  colours vs. the Cardio background, Reiz-Dauer, Pause min/max, Größe,
  Bereich via `randPosFromCfg`). Placement rejects any box touching a glyph
  of the quote (each character measured by its own Range rect, so the gaps
  between lines/words stay usable), the image, title/timer/labels, the
  chapter nav and the player bar; no fit = that flash is skipped. Pause
  freezes it; any other guest, abort or finish stops it. Every other guest
  stays a full takeover.
Test: `tests/cardio_motiv_test.py`.

### Persönliche Nachricht im Code (2026-10-03)

Fabian: "Persönliche Nachricht oder Hausaufgabe im Code" - umsetzen. Any
code config (every type, bundles included) may carry `message` (free text,
max 1000 chars). The dashboard has a "Nachricht an den Kunden" field above
the Baukasten/JSON tabs (`#pMessage`, `loadCodeFields()`/`applyCodeFields()`
write it into the config on save, an empty field removes it). In the app,
`openProgramIntro()` calls `showCoachMessageIfNew(code, def)`: the sheet
`#coachMessageSheet` ("Nachricht von deinem Trainer" - never Fabian's name,
other trainers may use the app later) opens over the opened screen once per
text version (`fwmc-coach-message-seen-v1`, `{code: text}`), and again when
the trainer changes the text. `recordCodeUsage(code, def)` keeps the latest
text in the code history, so it stays readable under Grundeinstellungen >
Trainings-Code-Verlauf. Test: `tests/coach_message_test.py`.

### Mein Fortschritt (2026-10-03)

Fabian: "umsetzen". Heute has a "Mein Fortschritt" card (`#todayProgressOpenBtn`:
Wochenziel x von y, Serie, Trainings gesamt) that opens `#progressScreen`:
- Wochenziel 1-14 per week (−/+), with a bar and text for this week.
- Serie = weeks in a row with the goal reached. The running week counts
  only once it is reached, so an unfinished week never breaks the streak.
  Also shows the longest streak, total trainings and total time.
- Chart of the last 8 weeks (green = goal reached, dashed line = goal).
- Areas in the last 4 weeks (`historyAreaOf`, plus Kombi-Programm and Test).
- Meilensteine 1/5/10/25/50/100/150/200/300/500/750/1000 trainings.
Data lives in `fwmc-progress-v1` = `{weekGoal, days:{"YYYY-MM-DD":{n, s, a:{area:n}}}, seeded}`.
It is seeded once from the history; after that `addHistory()` calls
`recordProgress()`. Lifetime numbers therefore survive the history's
200-entry cap. Aborted runs never count.
A new area only needs its `historyAreaOf` mapping (and a `PLAN_AREAS`
entry for its label/colour).
Test: `tests/progress_test.py`.

### Codes mit Laufzeit: persönlich / Gruppe, Plätze, Ablauf (2026-10-03)

Fabian: "Datum kann vergeben werden, muss aber nicht"; team codes later.
Optional config fields on any code: `validFrom`/`validUntil` (ISO dates,
Berlin day, both inclusive), `codeKind: "gruppe"` + `seats` (1-1000).
Without `codeKind` a code is personal (no seat limit). The dashboard edits
them next to "Nachricht an den Kunden" (`loadCodeFields(config, code)` /
`applyCodeFields()` returns an error text, e.g. from after until), the
codes table has a "Laufzeit / Plätze" column (`codeRunText`), and
"Plätze freigeben" posts `/admin/code-seats-reset`.
- **App**: every lookup sends `&device=` (`deviceId()`, 20 random chars in
  `fwmc-device-id`, no personal data - explained in the "Datenschutz in der App" sheet).
  `lookupProgram()` maps 410 `expired` / 403 `not_yet` / 403 `full` to
  `__lookupError`; `showCodeError()` says when the code was valid or from
  when it is, and to contact "deinen Trainer". `codeValidityProblem(def)`
  checks the dates on the client too, so expiry works even with an older
  Worker. The code history shows "gültig bis …".
- **Worker**: checks the dates first, then seats in table `code_devices`
  (`code, device, first_seen`, created lazily): a known device always gets
  in, a new one only while seats are left. `/admin/programs` returns
  `seatsUsed` per code. Test: `tests/worker_hardening_test.py` (mock D1
  that dispatches on the SQL text).
- **Deployed 2026-10-03** with Fabian's yes (version 3a75e714, verified:
  /program 200, admin without token 401, foreign origin 403). Seats are
  enforced from now on.
Test: `tests/code_validity_test.py`.

### Datensicherung: Export/Import (2026-10-02)

Master-Einstellungen, group `#masterBackupGroup`. "Sicherung exportieren"
downloads `fwmc-sicherung-YYYY-MM-DD.json` = `{app:"fwmc-training",
version, exportedAt, data:{key: rawString}}` with EVERY localStorage key
starting with `fwmc-` (so a new feature's key is included automatically -
keep the `fwmc-` prefix for every new key). "Sicherung importieren"
(`applyBackup()`): wrong `app` or a newer `version` is rejected before
asking; otherwise `confirmDialog`, then only the keys in the file are
written (keys not in the file stay as they are, Fabian: "nur die Sachen
eingestellt, die bisher gespeichert wurden"), non-`fwmc-` keys and invalid
JSON are skipped and counted, a full storage stops with a message, then the
page reloads so every `load*Prefs()` migrates old shapes. A future change
to the file format bumps `BACKUP_VERSION` and adds a step to
`BACKUP_MIGRATIONS[oldVersion]`. Test: `tests/backup_test.py`.

### Atemtraining: Hörmodus (2026-10-03)

Fabian: "Hör-Modus ohne Bildschirm". The breathReady "Ansage" row has three
choices: An / Hörmodus / Aus (`breathPrefs.sound` + `breathPrefs.listen`).
Hörmodus speaks each phase, counts the seconds ("2", "3" ...), says the
remaining minutes at a phase start ("Noch N Minuten"/"Noch eine Minute")
and "Geschafft. Gut gemacht." at the end (standalone only). It covers the
player with the dark `#breathListenLayer` (fixed `#05090b`, z-index above
the player-bar, so a pocket tap can't hit Beenden); pausing needs a 900 ms
hold on `#breathListenHoldBtn` (`BREATH_LISTEN_HOLD_MS`, keyboard click
pauses directly). The layer hides while paused; voice "Aus" in the pause
sheet returns to the normal view. Kombi blocks and saved presets carry
`listen`; coach programmes keep the client's own setting.
Test: `tests/breath_listen_test.py`.

### Atemtraining: Ohne Zeitlimit + "Weiter atmen" (Idee 53, gebaut 2026-10-07)

Fabian 06.10.: "Haken 'Ohne Zeitlimit' unter Dauer + nach Ablauf 'Weiter
atmen'-Knopf, Kombi geht danach weiter; nur Atmung" (Wim-Hof not: it has
rounds, not a duration).
- Ready: `#breathNoLimitCheck` (`.checkbox-row.tap-row`) inside the Dauer
  group, `breathPrefs.noLimit` (saved in `fwmc-breath-v1`). On = help text
  `#breathNoLimitHelp`, the duration rows dimmed (`.breath-dur-off`); tapping a
  duration or the slider switches the limit back on.
- `startBreathSession(opts)`: `opts.open` wins (Kombi block `noLimit`,
  Atem-Programm always `false`, Weitermachen), else `breathPrefs.noLimit`.
  An open session has `open:true, plannedTotal:Infinity`; the bar clock counts
  up; stage shows Pause + `#breathFinishBtn` "Fertig" (primary), the pause
  sheet hides Restdauer and shows `#breathPauseFinishBtn` "Fertig" (the way
  out of Hörmodus). Fertig = completed with the real time (pauses excluded),
  history `note:"ohne Zeitlimit"`. "✕ Beenden" of a single open run also
  completes (like Gleichgewicht "Ohne Zeitvorgabe"); in a Kombi it aborts the
  Kombi as always, Fertig goes to the next Baustein.
- End of a timed run: `breathEnterEndHold()` holds `BREATH_MORE_HOLD_S` (10 s):
  "Geschafft", countdown in the circle, `#breathEndNowBtn` "Beenden" +
  `#breathMoreBtn` "Weiter atmen" in one row, `#breathEndNote` ("Ohne Tippen
  endet die Übung in N s." / "... geht es in N s weiter."), the bar's ✕ waits
  (`visibility:hidden`). No tap = ends as before (done panel / next Baustein /
  next programme block). "Weiter atmen" = same session goes on open-ended
  (`breathSetOpen`, new cycle, clock continues from the planned time).
  Neither button id ends in `BackBtn`, so no "Wirklich beenden?".
- Kombi: block `noLimit:true` (capture/edit via the same checkbox,
  `comboBlockMeta` "ohne Zeitlimit", `comboBlockSeconds` 0 like Gleichgewicht
  open). Presets store `noLimit` (label "ohne Zeitlimit · …").
- Weitermachen: an open run notes `{open:true, played, total:played, rest:0}`
  (≥ 30 s played); Heute shows "ohne Zeitlimit"; Fortsetzen runs open again.
- Heute plan entries open the ready screen, so the checkbox applies there.
Test: `tests/nacht_vollbild_atem_reaktion_1007_test.py`.

### Datenschutz in der App (2026-10-03)

Every footer's "Datenschutz" is a `.privacy-open-btn` that opens
`#privacySheet` (same `.sheet` pattern as the FAQ, placed after
`#faqSheet` in `_body.html` so it stacks above it; Escape closes it first).
Four plain-language items: what stays on the device, the code lookup
(code + random device id, stored only for group codes with seats), the IP
address (rate limiting only, not stored), videos/links. It ends with links
to the website's Datenschutzerklärung and Impressum. The FAQ storage answer
links to it with an inline `.privacy-open-btn.inline-link`. **Anything new
that sends data off the device must be added to this sheet in the same
commit.** Test: `tests/privacy_test.py`.

### Logo-Leiste (2026-10-03)

Fabian: a fixed top bar with the logo, also at the same place in pause and
end phases, with the pause controls moved so nothing is covered; branding
inside a running exercise is decided later. Every `.screen>.brandbar` is
`position:sticky;top:0` with a solid `var(--bg)` and sits flush in the
screen's top padding, so it looks unchanged at rest. `#appBar` (last
element in `_body.html`, same logo/sub/gear) is fixed at the top and shown
by a `body:has(...)` rule ONLY while a visible player shows a
`.pause-overlay`, a `.pause-screen` or a `.done-panel`, or a body-level
done/transition panel is open (`>.done-panel` inside `:has()` - a selector there is relative to `body`, so `body>.done-panel` never matched and the Kombi pause had no logo until fixed); while the exercise runs it stays hidden. In
that state `.player-bar`, `.pause-overlay`, `.pause-screen` and
`.done-panel` move down by `--appbar-h` (its real height, set by a
ResizeObserver in app.js, since it wraps to two rows on a phone) and stage
hints are hidden. A new player gets this for free as long as it uses those
classes. Test: `tests/app_bar_test.py`.

### Steuerleiste « ↻ » überall (2026-10-04)

Fabian: "sollte nachher überall identisch sein". One bar, `#stepNav`
(end of `_body.html`), fixed at the bottom of every running player and of
the pauses between Bausteine/blocks (`#comboTransition`,
`#breathTransition`, workout transition): « zurück, ↻ neu starten,
optional an extra button, » weiter. `updateStepNav()` (MutationObserver on
`hidden` + 400 ms interval) picks the context in `stepCtx()`:
- areas with their own nav LEND their buttons (moved into the slots,
  put back afterwards, ids/handlers unchanged): VT pause screen and
  programme `liveNav`, Cardio, Tabata, Remember Trainingsmodus;
  Kraftplan uses `stepRepsCtx()` (step by step, also in rests and the
  start countdown);
- Kombi/breath plan: « » jump Bausteine, ↻ restarts the current one
  (`stepComboJump`/`stepBreathJump`); in a pause ↻ repeats the one just
  done, » continues;
- every other player: ↻ restarts via the "Training starten" button that
  opened it (recorded in `startBtnByPlayer`), « » shown disabled.
- hidden while a pause overlay, done panel, Hörmodus layer or programme
  video is open; Cardio guests show it disabled.
Restart/jump stop the run through the player's own Beenden with
`stepNavSilent` (no history entry, `addHistory` returns early) and
`endConfirmBypass`. **A new player needs nothing extra** as long as its
exit button follows the `…BackBtn`/"Beenden" convention and it is a
`.player`; every `.player` keeps `--stepnav-h` free at the bottom (no
stage content under the bar). Test: `tests/step_nav_test.py`.

Same pass, consistency fixes from an audit: "Programm geschafft!"/
"Programm beendet" everywhere (no "Plan …"), sheet buttons "Los geht's",
done-back labels "Zur Übersicht" (own builder) / "Zur Startseite" /
"Zurück zu meinen Programmen", singular/plural via `countLabel()`
("1 Baustein", "1 Aktivität"), "Pause danach" shows "Keine" at 0
(`fmtPauseAfter`), Kombi "Training starten" disabled while empty. Open
proposals from that audit (transition designs, start countdowns, sound
toggle, presets, unit formats ...) went to Fabian as a decision list.

### Interval phase wording corrected (2026-09-30)

"Belastung"/"Erholung" (both the setup-screen phase labels and the live
`#cardioPhaseLabel` during playback) renamed to "Intensive Belastung"/
"Leichtere Belastung" - client's point: the interval's "off" phase is
still active Cardio work at a lower intensity (e.g. still cycling, just
slower), not a stop-and-rest pause, and "Erholung" reads like the
latter. Widened `.cardio-interval-phase-row span:first-child`'s
min-width (64px → 122px) for the longer label. The "lohnende Pause"
sports-science term was considered and explicitly rejected by the
client as too jargon-heavy for someone without training background.

