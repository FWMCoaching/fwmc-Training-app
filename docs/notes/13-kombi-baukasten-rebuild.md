# Kombi-Baukasten rebuild (started 2026-09-29, Cardio + Movement + Breath/Wim Hof + Visual + Workout slices done)

Client's ask, in one big message: Cardio needs the "Komplett-Programm aus
mehreren Bereichen" entry it was missing (a scope gap from the night
Cardio was built), and - much bigger - the cross-section combo builder
itself needs to grow from "a fixed, curated list of ~15 sample presets"
(`COMBO_PRESETS`, one comment literally says "not the full settings depth
of each section's own screen") into: every exercise from every domain
except Test-Bereich selectable, full fine-tuning per block (not the
canned defaults), access to the client's own saved presets per exercise
so a favourite setup can be dropped in without reconfiguring, and pause
markers between blocks. Explicitly asked to "go through everything
independently" rather than checking in after each piece.

**Architecture decision, before writing anything**: every domain's combo
block is already just *a snapshot of that domain's own settings, replayed
through its own existing start function* - `startComboBlock()`'s
`visual`/`movement`/`workout`/`breath`/`wimhof` branches all overwrite
`state`/`movementPrefs`/`workoutPlan`/`breathPrefs`/`wimhofSettings` from
the block's stored fields and call the domain's own unchanged
`start…Session()`. That's the exact same mechanism a saved preset's own
"load" button already uses. So instead of building a second, smaller
settings UI just for combo blocks, **a combo block should be captured by
briefly reopening that domain's own real settings screen** - which
already has the full fine-tune UI and the saved-preset list "for free" -
with its own start button doing "commit this configuration as a block and
return to the combo builder" instead of actually starting a session. This
is the pattern for every future domain in this rebuild, not just Cardio.

**Cardio slice, built as the first (and simplest) proof of this pattern**,
since Cardio's own builder (`cardioReady`) already IS a full multi-
activity settings screen with its own saved-preset list and dual-task
addon config - reusing it needed no new UI at all, just a capture-mode
branch:
- `comboCardioCaptureOriginal` (module var): the client's OWN standalone
  `cardioPrefs.items`, saved off the moment capture starts and restored
  (with `saveCardioPrefs()`) the moment it ends (commit or cancel) -
  capturing a combo block must never clobber the separate, persisted
  "Eigene Cardio-Einheit" on Cardio's own home screen. `cardioPrefs.items`
  itself becomes the block being built in between (blank for a new block,
  or the existing block's items when re-editing one already in the combo
  draft) - the exact same object every other Cardio UI function
  (`renderCardioList`, the add-grid, the interval steppers, …) already
  reads and writes, so none of them needed to change.
  `comboCardioEditIndex` tracks whether "commit" should push a new block
  or overwrite one already in `comboDraftBlocks` (tap an existing Cardio
  block in the combo list to re-edit it - the only domain in the list
  that's clickable so far; every other domain's block is still add-once,
  not yet re-editable, until this rebuild reaches them too).
- `cardioReadyTitle`/`cardioReadyHint` (new ids) swap text to "Baustein:
  Cardio" during capture; `cardioStartBtn`'s label swaps to "Baustein
  übernehmen" (`syncCardioUI()` made capture-aware); `cardioBackToHome`
  branches to exit capture (restore + `showScreen("comboScreen")`) instead
  of going to `cardioHome`.
- `renderCardioSaved()`'s "load a saved unit" callback had to become
  capture-aware too: outside capture it starts a live session immediately
  (existing behaviour), but during capture it must only fill the draft for
  review, never auto-start a session out from under the combo builder.
- `finishCardio()`/`abortCardio()` gained the same `if (comboProgram) {…}`
  hook every other domain's finish/abort function already has (Cardio was
  built before combo integration was ever a requirement, so it had none) -
  placed *before* the done-panel/history code, same position as Workout's,
  since a combo block never gets its own history entry, only
  `finishComboProgram()` records one for the whole run.
- `comboBlockLabel`/`Meta`/`Seconds` and `startComboBlock()` gained a
  `"cardio"` case; a Cardio combo block stores `{domain:"cardio",
  items:[...]}` - literally the same `items` shape `startStandaloneCardio()`
  already takes, so playing one back is a two-line addition, not a new
  engine.
- Cardio's own dual-task addon settings (`cardioAddonPrefs`) are
  deliberately untouched by any of this - they're the client's own
  standing setting that already applies to "ANY cardio run", combo
  included, exactly as designed the night Cardio was built.

Tested in `tests/cardio_combo_test.py`: the combo-entry-link now on
`cardioHome`, opening capture (blank, not the standalone unit), adding
activities, committing, re-editing an already-added Cardio block,
cancelling a capture (discarded, standalone unit still untouched
throughout all of this), and a full combo run through a Cardio block
(shows in the normal `cardioPlayer`, no per-block done panel, aborting
mid-block returns to the combo's own return screen). Also added
`tests/cardio_extras_test.py` for the small Tabata-style "N× in der
Einheit" count badge now on Cardio's activity add-grid (mirrors
`renderWorkoutCircuitAddGrid`'s badge exactly, re-renders the grid on
every add/remove so the count stays live).

**Movement slice**, the same pattern applied to `movementReady` (its
single-config settings screen):
- `comboMovementCaptureOriginal` (module var) saves off the client's whole
  `movementPrefs` object (deep-cloned) the moment capture starts, restored
  via `Object.assign` + `saveMovementPrefs()` the moment it ends - same
  "must never clobber the standalone setup" requirement as Cardio, just
  against a flat prefs object instead of an items array.
  `comboMovementEditIndex` mirrors Cardio's edit-in-place tracking.
- `movementReadyTitle`/`movementReadyHint` (new ids, `movementReady`'s
  `<h1>`/`<p class="page-sub">` previously had none) swap to "Baustein:
  Movement" during capture; `movementStartBtn`'s label swaps to "Baustein
  übernehmen".
- `renderMovementSaved()`'s "load a saved setting" callback made capture-
  aware the same way Cardio's was: fills the draft and re-syncs the picker
  UI without starting a session when capturing.
- No changes needed to `comboBlockLabel`/`Meta`/`Seconds` or
  `startComboBlock()`'s `"movement"` case - both already existed from the
  original curated-preset version and already read exactly the fields this
  capture flow writes.
- The 2 old canned `COMBO_PRESETS.movement` entries were removed entirely
  (superseded by the capture button) - `renderComboAddGrid()` now renders
  Cardio and Movement's capture-entry buttons from one small generic loop
  instead of two near-duplicate blocks, so a third domain joining this
  pattern is a one-line addition to that array, not copy-pasted markup.

Tested in `tests/movement_combo_test.py` (same shape as Cardio's own
combo test: capture opens blank/pre-filled correctly, commit, re-edit,
cancel discards and leaves the standalone setting untouched, a full combo
run through a Movement block, mid-block abort routing). Fixed
`tests/workout_combo_test.py`'s combo-builder section along the way - it
picked add-grid buttons by raw position (`.nth(4)` commented "// movement",
etc.), which silently broke (added the wrong exercises with no assertion
ever going red) once Cardio/Movement's buttons moved to the end of the
grid; switched it to text-based selectors, the same convention the new
combo tests use, so a future reshuffle of the grid can't silently degrade
it the same way again.

**Breath + Wim Hof slice**: Breath already had combo *playback* hooks
(`breathFinishSession()`/`breathAbort()` already checked `comboProgram`,
since Breath was one of the 5 original curated-preset domains, unlike
Cardio) - only capture UI was missing, same as Movement.
- Breath's 4 cycle patterns (coherent/box/relax478/custom) share one
  `openBreathComboCapture(patternKey, existingBlock, editIndex)`, since
  they share one settings screen (`breathReady`, already keyed by
  `breathPatternKey`). `comboBreathCaptureOriginal` only needs to snapshot
  `breathPrefs.durationMin`/`sound`/`custom` - `breathWorking` and
  `breathPatternKey` aren't persisted standalone state (`openBreathReady()`
  always sets them fresh), so there's nothing else to save off. The block
  shape gained one thing the old canned presets never had: `phases` is now
  always captured (not just for `"custom"`), so even a quick ad-hoc tweak
  to Box-Atmung's timing for one combo flows through, not just its fixed
  default.
- Wim Hof got its own `openWimhofComboCapture`/`exitWimhofComboCapture`/
  `commitWimhofComboCapture`, reusing `wimhofReady` - the safety
  acknowledgement checkbox is still required every time, capture/edit
  included ("Safety first, always" already applied to combo *playback*
  via `startComboBlock`'s wimhof branch forcing its own settings screen
  mid-run; requiring it at authoring time too is the same principle, not
  a new restriction). `syncWimhofStartBtn()`'s label became capture-aware
  the same way Cardio/Movement's start buttons did.
- `renderBreathSaved()`'s "load a saved setting" callback made capture-
  aware (fills the draft, doesn't auto-start), same pattern as Cardio's
  and Movement's saved-preset callbacks.
- `COMBO_PRESETS.breath` removed entirely (all 5 options - 4 patterns +
  Wim Hof - now come from `COMBO_CAPTURE_ENTRIES.breath`, up from 3 fixed
  patterns + 1 fixed Wim Hof preset before, and `"custom"` wasn't reachable
  from the combo builder at all previously).
- `renderComboAddGrid()`/`renderComboBlockList()` generalized further: a
  module-level `COMBO_CAPTURE_ENTRIES` (per domain, a list of
  `{label, meta, open}`) and `COMBO_EDIT_OPENERS` (per domain, an
  edit-in-place opener) replace the growing pile of near-duplicate
  per-domain blocks from the Cardio/Movement slices - adding the next
  domain to this rebuild is now a few lines in these two tables, not new
  rendering code. `COMBO_DOMAIN_ORDER` keeps the add-grid's section order
  stable now that domains can contribute presets, captures, both, or (once
  a domain fully migrates) neither.

Tested in `tests/breath_combo_test.py`: all 4 patterns + Wim Hof present
in the add grid, cycle-pattern capture (including an ad-hoc duration
tweak surviving into the block, re-editing it, cancelling leaves the
standalone pattern setting untouched), and Wim Hof capture (ack required
before the button enables/reads "Baustein übernehmen", commits, standalone
entry still demands a fresh ack afterward). Fixed the breath-related steps
in `tests/combo_reveal_test.py` and `tests/workout_combo_test.py`, which
assumed clicking a breath preset instantly added a block - true before
this slice, not anymore now that breath also opens its settings screen in
capture mode.

**Visual slice** - the biggest exercise count (11 home-grid exercises,
`vt-color` through `cone-compass`), reusing the shared `ready` screen
(`openReady()`, already the one settings screen every Visual exercise
funnels through) exactly like Breath's `breathReady`. Both playback hooks
(`finishSession()`/`abortTraining()`) already checked `comboProgram` -
Visual was an original curated-preset domain like Breath, so again only
capture UI was missing.
- `openReady()` calls `loadPrefs()` internally, which reloads `state`
  wholesale from localStorage - so, unlike Cardio/Movement/Breath where the
  existing-block override could happen inline, `openVisualComboCapture()`
  must call `openReady()` *first* and only then apply an existing block's
  field overrides, followed by a manual re-sync
  (`renderColorSwatches()`/`syncColorUI()`/`syncDurationUI()`/
  `syncTempoUI()`) - applying them before would just get wiped.
- Real bug fixed along the way, not just new capture UI: `startComboBlock()`'s
  `"visual"` branch only ever copied `block.colors` onto `state.colors`,
  gated on `usesColors` - the 3 old curated presets never happened to need
  `usesArrowColors`/`usesStroopColors` (Stroop's preset carried no colour
  override at all), so a Stroop or arrow-based combo block silently ignored
  any captured colour choice and played back whatever `state.stroopColors`/
  `state.arrowColors` happened to currently hold. Generalized to check all
  3 colour kinds via the exercise's own `usesColors`/`usesArrowColors`/
  `usesStroopColors` flags, matching the pattern already used elsewhere
  (`applyCardioGuestToState`). `commitVisualComboCapture()` captures
  whichever colour array the exercise actually uses the same way.
- `comboVisualCaptureEntries()` builds its add-grid entries *from the live
  DOM* (`document.querySelectorAll(".excard")`) on every render rather than
  a static list, and reuses `exerciseBlockedReason(card)` - the exact same
  check the home grid's cards already run for Master-Einstellungen's
  hearing restriction. A blocked exercise's combo button gets the same
  `.incompatible` greyed-out treatment (new: `.combo-add-btn.incompatible`
  in `styles.css`, same opacity rule as `.excard.incompatible`) and opens
  Master-Einstellungen on tap instead of capture - never a way to route
  around a restriction the home grid itself enforces.
- `COMBO_CAPTURE_ENTRIES`/`COMBO_EDIT_OPENERS` extended to allow a
  **function** value (resolved fresh on every `renderComboAddGrid()` call),
  not just a static array - Visual is the first, and so far only, domain
  that needs this (its "incompatible" state can change at runtime; every
  other domain's capture button is unaffected by anything Master-
  Einstellungen currently controls).
- `renderVTSaved()`'s "load a saved setting" callback made capture-aware,
  same pattern as every other domain's saved-preset callback so far.
- All 3 old curated `COMBO_PRESETS.visual` entries removed (superseded -
  same exercises, now with full fine-tuning and saved-preset access).

Tested in `tests/visual_combo_test.py`: all 11 exercises present in the
add grid, VT-Farbe capture (commit, re-edit, cancel leaves the standalone
exercise setting untouched), a Stroop-classic capture (proves the
colour-kind bugfix actually stores/replays `usesStroopColors`, not just
`usesColors`), a full combo run through a Visual block, and the
Master-Einstellungen hearing-restriction interaction (cross-modal's combo
button greys out and opens Master-Einstellungen instead of capture, same
as its home-grid card). Fixed the Visual-related steps in
`tests/combo_reveal_test.py` (originally switched to Workout's presets,
then to NAT's once Workout's own presets were removed too in the very
next slice - see below) and `tests/workout_combo_test.py` (added the same
capture-then-commit step the other domains needed), both broken the same
way the breath fix was - clicking a Visual exercise no longer adds a
block, it opens capture mode.

**Workout slice**: reuses the existing Tabata **circuit** builder
(`workoutTabataReady`/`workoutCircuitPrefs`) exactly like Cardio's own
slice - a combo "workout" block can already be a whole multi-exercise
circuit, not a single exercise, since `runWorkoutBlock()`/
`workoutBlockLabel()`/`Meta()`/`Seconds()` already dispatch on
`block.kind` and already handle `"circuit"` (built for the standalone
quick-start before this rebuild ever touched Workout) - so this slice
needed *zero* engine changes, only the capture UI:
- `comboWorkoutCaptureOriginal` snapshots `workoutCircuitPrefs`'s
  `items`/`restS`/`sets`/`setRestS` (not `defaultWorkS`/`prepS`/
  `cooldownS` - those are builder-UI defaults, not part of a saved
  circuit's own identity, matching exactly what
  `renderWorkoutCircuitSaved()`'s own preset loader already touches).
- `workoutTabataReadyTitle`/`workoutTabataReadyHint` (new ids) swap to
  "Baustein: Zirkel" during capture; `workoutTabataStartBtn`'s label
  swaps to "Baustein übernehmen" (`syncWorkoutCircuitUI()` made
  capture-aware, same as Cardio's `syncCardioUI()`).
- **Scope decision, made explicitly rather than silently**: only
  **circuit** mode joins the combo builder. "Reps" mode (feste Sätze/
  Wiederholungen, e.g. 3×12 Kniebeugen) has *no client-facing settings
  screen at all* - it's coach-plan-only today (`workoutOverview`/
  `workoutRepsView` only ever run from a `workout-plan` def) - so there
  is nothing to reopen in capture mode, the same category of gap as
  Blitz-Raster/Flash/MOT below. Rather than leave the 2 old curated
  presets (one reps, one tabata) in place as a non-editable leftover,
  both were removed - keeps one invariant true everywhere in this
  rebuild: anything addable to a combo is also re-editable.
  `renderComboBlockList()` also gained a guard for a workout block
  predating this change (or coach-authored) that's still `"reps"`/
  `"tabata"` kind: it's shown but deliberately not made clickable/
  editable, since there's no screen to reopen it into and naively
  reusing the circuit capture on it would silently discard its real
  config.
- `renderWorkoutCircuitSaved()`'s "load a saved circuit" callback made
  capture-aware, same pattern as every other domain's saved-preset
  callback so far.

Tested in `tests/workout_circuit_combo_test.py` (same shape as Cardio's:
capture opens blank/pre-filled correctly, commit, re-edit adding a 3rd
exercise, cancel discards and leaves the standalone circuit untouched, a
full combo run through a circuit block, mid-block abort routing). Fixed
`tests/combo_reveal_test.py` again (NAT's Remember presets are now the
*only* plain one-click-add domain left) and the Workout section of
`tests/workout_combo_test.py` (its own add-grid uses a separate info
button + `.ca-plus-btn` per exercise, not one clickable card like every
other domain's add-grid - a real, pre-existing UI inconsistency worth
knowing about even though this rebuild didn't set out to fix it).

**NAT's Remember, done (2026-09-29)**: the last domain on the original
backlog list to move from a fixed one-click preset to full capture mode.
Unlike every other domain capture-fied so far, none of Remember's 3 modes
(fixed/shuffle/training) has a natural end on its own - they only ever
stop via "Beenden" - so unlike Movement's `durationMin` (already a real
standalone setting, just reused), there was no existing duration control
to piggyback on. Added one from scratch, visible ONLY during capture
(`comboRememberDurationS`, a plain in-memory variable - never written to
`rememberPrefs`, since it belongs to the combo block, not the client's
day-to-day Remember setup): a `rememberComboDurationGroup` slider next to
the fixed/shuffle ready screen and a second `rememberTrainingComboDurationGroup`
next to the training-mode ready screen, both reusing VT/Periph's own
15-300s/step-5 "Gesamtdauer" range for consistency. `openRememberComboCapture(mode, existingBlock, editIndex)`
picks the right screen for the given mode the same way the standalone
open buttons already do; `commitRememberComboCapture()` produces the exact
same `{domain:"nat", mode, duration}` block shape the old fixed presets
already used (so old saved combos need no migration), and `startComboBlock()`'s
existing `nat` dispatch (`startRememberGame(block.mode || "fixed", {comboDurationS})`)
needed no changes at all - it was always mode-agnostic. `COMBO_PRESETS.nat`'s
2 old one-click entries were removed (now `COMBO_PRESETS = {}` - nothing
left uses the mechanism, kept in place rather than deleted in case a
future domain wants a plain preset again) and replaced with 3 capture
entries (fixed/shuffle/training - training was never offered as a preset
at all before tonight, since a fixed 60s preset made little sense for a
mode about deliberately starting at a chosen difficulty).

Test: `tests/remember_combo_test.py` - all 3 modes open the right capture
screen with the duration slider visible only in capture mode (hidden
again on a normal standalone open), duration carries over correctly on
re-edit, cancel discards a not-yet-committed block, and a fresh combo
with a short duration runs Remember and finishes automatically. Fixed
3 pre-existing tests that clicked the old one-click NAT presets directly:
`tests/combo_reveal_test.py`, `tests/nat_combo_test.py`,
`tests/nat_combo_abort_test.py` (each now clicks through the capture
screen's own start button, same fix pattern applied to every other
domain's tests earlier in this rebuild).

**Blitz-Raster/Flash Speicher Test/MOT-Fähigkeit, done (2026-09-29)**:
turned out to be bigger than the backlog note above suggested - Flash and
MOT each have 4 modes (not 1), so this was really 9 modes total across
3 domains, not "wire up 3 settings screens". Each got the exact template
Remember established: a combo-only duration slider (`comboBlitzDurationS`/
`comboFlashDurationS`/`comboMotDurationS`, plain in-memory vars, never
persisted to that domain's own prefs), a `finishXCombo()` that mirrors
`finishRememberCombo()` (clear the pending game timer, compute played
seconds, null the state, tear down fullscreen/wake-lock, call
`advanceComboProgram()`), and the same pause/resume symmetry (the
combo-duration timer is cancelled and its exact remaining delay captured
on pause, rescheduled on resume - copied from Remember's
`comboDurationFiresAt`/`comboRemainingMs` pair verbatim for each domain).
One new wrinkle MOT's engine has that the others don't: its tracking
phase runs on `requestAnimationFrame` rather than `setTimeout` alone, but
the combo-duration timer itself is still a plain independent
`setTimeout`, so `finishMotCombo()`/pause/resume just additionally
cancel/leave alone the `raf` handle exactly where the existing pause/
resume code already did for the non-combo case - no new mechanism needed.
- **Blitz-Raster**: single mode, so the capture UI is the simplest of the
  three - straight copy of Remember's fixed/shuffle shape without the
  "training has its own screen" split. Needed the LEAST scaffolding since
  `blitzStop()` had never gained a `comboProgram` abort branch before
  (Blitz was never combo-integrated at all pre-tonight) - added the same
  "Beenden mid-Kombi aborts the whole Kombi" branch Remember already had.
  Block shape carries its own `gridSize`/`zones`/`startCount` snapshot
  (not just `duration`), matching Movement's block-is-self-contained
  precedent rather than relying on `blitzPrefs` still holding the right
  values whenever the block eventually plays.
- **Flash Speicher Test** and **MOT-Fähigkeit**: both have the exact same
  shape as Remember - 3 modes sharing one ready screen (`flashReady`/
  `motReady`, both already had dynamic `*ReadyTitle`/`*ReadyDesc` elements
  from their own pre-existing multi-mode support) plus a 4th
  "Trainingsmodus" with its own separate static-heading screen
  (`flashTrainingReady`/`motTrainingReady`). `flashModeTitle(mode)`/
  `motModeTitle(mode)` extracted as small helpers (mirroring logic that
  already existed inline in `openFlashReady()`/`flashStop()` and
  `openMotReady()`/`motStop()`) so `comboBlockLabel()` could reuse the
  same title strings rather than a 4th copy of the same ternary chain.
  Block shape is the same `{domain, mode, duration}` shape as Remember's
  `nat` blocks - deliberately NOT reusing the `"nat"` domain key itself
  (that stays Remember-only, since `startComboBlock()`'s `nat` branch is
  hardcoded to `startRememberGame`) - `"blitz"`/`"flash"`/`"mot"` are new
  domain keys, grouped for DISPLAY under the same `COMBO_CAPTURE_ENTRIES.nat`
  array (all 4 are NAT sub-exercises from the client's perspective) but
  each block still carries its own real `domain` for dispatch.

Tests: `tests/blitz_combo_test.py`, `tests/flash_combo_test.py`,
`tests/mot_combo_test.py` - same shape as `remember_combo_test.py` for
each (capture opens the right screen with the duration slider visible
only there, duration carries over on re-edit, cancel discards, standalone
entry unaffected, a short-duration combo run finishes automatically,
mid-block pause/resume). `tests/nat_combo_test.py` now correctly reports
4 NAT presets in the add-grid (3 Remember + Blitz-Raster, since the other
9 modes render as capture buttons alongside them, not counted by that
test's own `.combo-add-btn` locator scoping - unaffected by this change,
verified by rerunning it, not a regression).

**Still open, explicit backlog for the rest of this rebuild**: Workout's
"reps" mode needs its own client-facing settings screen before it can
rejoin the combo builder (see above - a larger, separate product
decision, not just wiring). Pause markers between blocks (a
`{domain:"pause", seconds:…}` pseudo-block) also not started. With
Remember/Blitz/Flash/MOT all done, every exercise across every domain
except Test-Bereich (by original design - see the client's own scope
decision) can now be added to a combo with its own full fine-tuning.

