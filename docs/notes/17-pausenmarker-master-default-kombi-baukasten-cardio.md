# Pausenmarker: Master default + Kombi-Baukasten + Cardio (added 2026-09-29)

The last item on the Kombi-Baukasten rebuild's own backlog, plus a
matching gap the client spotted independently in Cardio: neither the
combo builder's block-to-block transition nor a multi-activity Cardio
session had any real rest between two things running back to back -
client's own reasoning: the right length genuinely depends on what
you're switching between (changing equipment, getting into position),
so it needs to be adjustable per transition, not one fixed value, and
always skippable.

- **`masterPrefs.defaultPauseS`** (new field, default 20s, 0-180 slider
  in a new Master-Einstellungen group): unlike the background-colour
  default, this is a **starting value only, read live** wherever a pause
  is actually used - never written/seeded into anything the way
  `applyMasterBgDefaultEverywhere()` does. There's no pre-existing
  "never touched" storage state to migrate for a brand-new field, so a
  simple `block.pauseAfterS ?? masterPrefs.defaultPauseS` fallback at the
  point of use is simpler and just as correct.
- **Kombi-Baukasten**: `renderComboBlockList()` now renders a
  `.combo-pause-row` (a slider, reusing the shared `.slider-row` markup
  conventions) between every two blocks - not after the last one, since
  nothing follows it. Dragging it sets `block.pauseAfterS` directly on
  that draft block (not persisted elsewhere - the combo draft/saved
  preset itself is where it lives, same as `pauseAfterS` living on each
  Cardio item below). At playback, `showComboTransition()` - the
  existing "next up" screen between blocks, previously a fixed silent 4s
  auto-advance with an early-skip button - now takes the finishing
  block's `pauseAfterS` (falling back to the Master default) as its real
  wait time, with a live countdown (`#comboTransitionCountdown`, reusing
  the `.pause-countdown` styling from the older VT-programme pause
  screen for a consistent look) and the skip button relabelled
  "Überspringen". A pause of 0s skips the whole transition screen
  outright rather than flashing a "0s" screen.
- **Cardio**: `withCardioPauses(items)` interleaves a
  `{ pause: true, durationS }` pseudo-item after every real activity
  except the last (same "durationS floor" mechanic every real activity
  already uses - `cardioTick()`'s existing "advance once durationS
  elapses" loop needed no new state machine, just a branch for
  `block.pause` that repurposes the existing activity-title/countdown/
  label elements to show "Pause" + what's next instead of building a
  second player screen). Each Cardio item gets its own `pauseAfterS` via
  a `.combo-pause-row` in `renderCardioList()`, identical in shape to the
  Kombi-Baukasten's own. **Real bug found while wiring this up**:
  `cardioSkipBtn` ("Nächste Aktivität »") used to just do
  `index++`, which after interleaving would land ON the pause pseudo-
  item instead of the real next activity when pressed mid-activity - a
  client explicitly skipping ahead clearly wants the next real activity,
  not a pause first either, so the handler now skips over a pause
  landed on immediately after incrementing. Also fixed: `finishCardio()`
  used to build its "X Übungen" summary and activity-name list directly
  from `cardioState.items`, which would have counted pauses as
  activities and called `findCardioActivity(undefined)` for each one
  once pauses existed - both now filter to real items first (`totalS`
  deliberately still includes pause seconds, same convention Workout's
  own `restS`/`setRestS` totals already use - a pause is real session
  time). `cardioItemsSeconds()` (used for every "ca. X Min" preview
  before starting) was updated the same way so those estimates stay
  accurate.

Tests: `tests/combo_pause_test.py` (Master default, per-block override,
live countdown, skip works, exactly one pause row between two blocks and
none after the last), `tests/cardio_pause_test.py` (same shape for
Cardio, plus confirming `cardioSkipBtn` during a real activity correctly
jumps past an interleaved pause, and that a 0s pause shows no screen at
all) - the latter needed a `performance.now()` + `requestAnimationFrame`
timestamp warp (not the `setTimeout`-multiplier trick used elsewhere in
this suite) to speed through Cardio's real-time, non-`setTimeout` tick
loop within the 60s `durationS` floor `loadCardioPrefs()` enforces. Also
reran `tests/cardio_test.py` to catch the `cardioSkipBtn` regression
above - it was already a real bug independent of test-writing.

