# Workout

`WORKOUT_EXERCISES` (app.js, near `WORKOUT_ICONS`) is the built-in exercise
catalog used by Tabata/Zirkel-building and reps-based workout blocks -
fully data-driven (`allWorkoutExerciseEntries()` merges it with the
client's own `customWorkoutExercises`), so adding an entry here is enough
for it to show up everywhere (picker, Tabata player, combo builder) with
no other wiring needed. Each entry needs a `name`, an `icon` key with a
matching hand-drawn stick-figure pictogram in `WORKOUT_ICONS` (same
minimalist style throughout: `viewBox="0 0 24 24"`, `stroke="#fff"`,
`stroke-width="1.8"`, a filled `r="2"` circle for the head, everything
else `fill="none"`), and a one-line form-cue `note`. **Extended
2026-09-27** (client asked directly, not the autonomous Test-Bereich
routine) from the original 6 (Kniebeugen/Liegestütze/Ausfallschritte/
Plank/Hampelmann/Bergsteiger) with 8 more classics: Burpees, Sit-ups,
Superman, Hüftheben (Brücke), Kniehebelauf, Wandsitz, Trizeps-Dips,
Sprungkniebeugen - deliberately appended AFTER the original 6 rather than
inserted anywhere among them, since `tests/workout_combo_test.py` picks
exercises from the picker grid by fixed index (`.nth(0)`/`.nth(4)`) and
would have broken silently otherwise.

**Split-tap picker row (added 2026-09-28)**: the client liked that tapping
an exercise in the Tabata/Zirkel picker (`#workoutCircuitAddGrid`,
`renderWorkoutCircuitAddGrid()`) adds it straight to the circuit, but
wanted a way to read the exercise's form cue (`ex.note`) first without
committing to adding it. Split each row's single `.combo-add-btn` into two
separate `<button>`s (can't nest a button in a button) inside the same
`.custom-exercise-add-row`: the icon+name area keeps the `.combo-add-btn`
class/look and now opens a new `#workoutExerciseInfoSheet` (icon, name,
`ex.note`, same `.sheet`/`.sheet-inner` overlay + focus-trap pattern as the
FAQ/Master-Einstellungen sheets) via `openWorkoutExerciseInfo(ex)`; a new
adjacent `.ca-plus-btn` (just the "+") keeps the original add-to-circuit
behaviour. Updated the four pre-existing tests that clicked
`#workoutCircuitAddGrid .combo-add-btn` to add an exercise (they now open
the info sheet instead, which then blocked further clicks as an overlay) -
`workout_combo_test.py`, `workout_save_position_test.py`,
`workout_saved_test.py`, `note_distinction_test.py` all now target
`.ca-plus-btn` for that. The general Kombi-builder's own `.combo-add-btn`
grid (`#comboScreen`, a different function/screen) is untouched - still a
single button that adds directly, no info-vs-add split there.

**Vorbereitungszeit, Cool-down, Pause-zwischen-Sätzen as Feineinstellungen
(added 2026-09-28)**: all three now live in `#workoutCircuitAdvanced` as
sliders, for the client's own self-built Zirkel only (`workoutCircuitPrefs`
- coach-authored `tabata`/`reps` plan blocks are untouched, see below).
- **Vorbereitungszeit** (`workoutCircuitPrefs.prepS`, 3-30s, default 5):
  the length of the "Bereit machen" start countdown before the first
  exercise. `buildCircuitSchedule(block, prepS, cooldownS)` gained two
  optional parameters (both default when omitted) instead of hardcoding
  the pre-existing `TABATA_PREP_S` constant into the schedule - so
  `startCircuitBlock()` (the self-built Zirkel's own start path) passes
  `workoutCircuitPrefs.prepS`/`.cooldownS`, while `startTabataBlock()`
  (coach-authored single-exercise `tabata` blocks, a separate call site)
  calls it with no third/fourth argument and gets the original fixed
  5s/0s behaviour - a coach already chose those timings deliberately,
  they're not meant to be client-adjustable.
- **Cool-down** (`workoutCircuitPrefs.cooldownS`, 0-120s step 5, default 0
  = "Aus"/no cooldown at all): an optional quiet phase appended after the
  very last set, before the done panel. `buildCircuitSchedule` only pushes
  a `type: "cooldown"` schedule frame when `cooldownS > 0`; `circuitTick`
  shows the last exercise's icon/name (for a calm reference point, not as
  something to actively perform) under a "Cool-down" / "Gleich geschafft"
  label, reusing the existing `phase-rest` styling.
- **Pause zwischen Sätzen** (`workoutCircuitPrefs.setRestS`): existed
  already as a 3-choice row (20/30/60s) directly on the main ready screen;
  moved into Feineinstellungen as a slider (10-120s step 5) instead, for
  finer control alongside the two new settings above and consistent with
  how "Standard-Dauer für neu hinzugefügte Übungen" already works there.
  Still hidden whenever `sets <= 1` (unchanged behaviour, just relocated)
  - `#workoutCircuitSetRestGroup` moved bodily into
  `#workoutCircuitAdvanced .advanced-body`. The old `data-wo-setrest`
  choice buttons are gone; `#workoutCircuitSetRestSlider` replaces them.

None of prepS/cooldownS/setRestS are saved per named preset ("gespeicherter
Zirkel") - like `defaultWorkS`, they're one shared preference across every
self-built circuit, not part of a saved circuit's own identity.

**Hinweistöne (added 2026-09-28)**: client asked for start/end audio cues
for every exercise interval - "kurz kurz kurz lang" (3-2-1-GO), explicitly
NOT as a hearing-based exclusion mechanism (unlike `exerciseBlockedReason`'s
`data-tags="ton"` system for exercises that genuinely NEED sound - Tabata
never gets tagged `ton` and stays fully playable muted), with a toggle
reachable both from the ready screen ("in der Übersicht") and during the
live player ("während dem laufenden Training"). Lives with the rest of the
Tabata schedule/tick machinery since both entry points (self-built circuit
AND coach-authored single-exercise blocks) share `circuitTick`:
- `workoutSoundPrefs.enabled` (own `fwmc-workout-sound-v1` key, default
  `true`) is a standalone pref, not part of `workoutCircuitPrefs` -
  coach-authored `tabata` blocks never read that object, but should still
  respect the same mute toggle.
- Two buttons write/read the same flag: `#workoutTabataSoundToggleBtn` on
  `workoutTabataReady` (top of the ready screen, always visible, not
  tucked into Feineinstellungen - sound is more discoverable-worthy than a
  timing tweak) and `#tabataSoundToggleBtn` on the live `workoutTabataView`
  itself. Both call the same `toggleWorkoutSound()`/`syncWorkoutSoundUI()`
  pair, swapping a speaker/muted-speaker emoji (🔊/🔇) and an `.is-off` CSS
  class - same "emoji as icon" convention the gear/master-settings button
  already uses.
- `playWorkoutBeep(long)` is plain Web Audio (`OscillatorNode` + `GainNode`,
  no audio file assets) - short beep 110ms/880Hz for the 3-2-1 countdown,
  long beep 350ms/1180Hz marking the actual start/end instant. Audio
  unlocks on the same tap that starts the circuit (`AudioContext` is only
  ever created lazily inside `playWorkoutBeep`, and browsers count a click
  a few function calls upstream of that as the unlocking gesture).
- Scheduling lives in `circuitTick`, keyed off the existing flat schedule
  frames rather than a second timer: `workoutBeepFrame`/`workoutBeepedSeconds`
  (reset via `resetWorkoutBeepTracking()` in both `startCircuitBlock`/
  `startTabataBlock`) track which frame is current and which of its
  3/2/1-second marks already fired, so a beep fires exactly once even
  though `circuitTick` itself runs every animation frame (~60/s). A frame
  change where either the outgoing or incoming frame is `type: "work"`
  fires the long beep - since `buildCircuitSchedule` always interleaves
  work frames with exactly one gap frame (rest/setrest/prep/cooldown)
  between them, EVERY transition boundary in the schedule is a work
  start or end, so this one condition naturally covers "Start und Ende
  einer Übung" everywhere without needing to special-case rest vs. setrest
  vs. prep. Short beeps fire during the final 3 seconds of any frame that
  either IS `work` (counting down to its end) or is immediately followed
  by one (counting down to its start) - which excludes cool-down, correctly,
  since nothing ever follows it and it isn't itself a work interval. The
  very last work interval's own end (when there's no cool-down to absorb
  the "transition") needed a small special case: `circuitTick`'s normal
  finish path (`elapsed >= workoutState.total`) returns before ever seeing
  a "new frame", so it fires that final long beep itself, right before
  calling `finishWorkoutBlock()`.
- Not built: per-beep pitch/volume Feineinstellung, a distinct sound for
  "last rep" vs. a normal one - not asked for, and the base cue already
  reuses the same short/long shape the client specifically requested.

