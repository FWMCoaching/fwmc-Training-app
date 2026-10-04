# Cardio: manual "+ Zusatzimpuls" live picker (Tier 2, added 2026-09-30)

First shipped as a single button that fired the existing automatic
dual-task system's `triggerCardioGuest()` on demand (same random pick
from the client's pre-configured `cardioAddonPrefs.pool`, same
per-type-configured duration) - see git history for that first version.
The client then clarified the actual ask was bigger: not just "trigger
whatever's pre-configured", but actively **choose** which guest exercise
**and** for how long, right now, mid-Cardio-activity - "ich mache jetzt
zwei Minuten Blitzreiz-Reaktionstraining" - plus a way to still see
Cardio's own status while doing the guest exercise, including a warning
before Cardio needs the client back.

Before building, worked through three tiers of how "reachable while
Cardio keeps running" could actually be implemented:
1. What already existed: full takeover, no live choice, no visible Cardio
   status at all during the guest exercise.
2. **Built** (this section): full-screen takeover of the *chosen* guest
   exercise (still only one real "Player" active at a time - the app's
   pervasive single-active-player assumption, see the note at
   `hideAllPlayers()`, is untouched), with a small independent floating
   badge reading Cardio's still-ticking state layered on top. "Bild-im-
   Bild", not two interactive screens.
3. True simultaneous split-screen (two independently interactive
   Players at once) - would need that single-active-player assumption
   reworked everywhere it's assumed (fullscreen API, wake-lock,
   pause overlays, back/abort-button logic). Assessed and explicitly
   **not** built: Tier 2's own UI flow (the picker, the "return to
   Cardio afterward" mechanics) is additive groundwork for Tier 3, not
   a dead end that would need reworking if Tier 3 is ever wanted later -
   so there is no real future-proofing cost to starting with Tier 2.

**The picker** (`openCardioAddonPicker()`/`renderCardioAddonPicker()`,
the `#cardioAddonPicker` sheet, a `.pause-overlay` nested *inside*
`#cardioPlayer`): offers all `CARDIO_GUEST_TYPES`, not just the
automatic system's own configured pool - "jede andere Übung" was the
explicit ask, and every type already has valid defaults in
`cardioAddonPrefs.perType` regardless of pool membership (see
`loadCardioAddonPrefs()`, which initialises all of them unconditionally).
A duration stepper (15s steps, 15s-180s, defaulting to that type's own
configured duration but never writing back to it - a live in-the-moment
choice, not a settings change) sits below it. Because opening the picker
never touches `cardioRaf`, Cardio's own countdown keeps visibly ticking
behind the semi-transparent overlay while choosing - the "ich sehe im
Hintergrund trotzdem noch, wie lange ich machen muss" ask, satisfied for
free during the choosing step by reusing the existing `.pause-overlay`
pattern. "Abbrechen" just hides the sheet again, no side effects.
`triggerCardioGuest(explicitId, explicitDurationS)` now takes optional
overrides - called with both from the picker's "Jetzt starten", called
with neither (unchanged) from the automatic interval path in
`cardioTick()`, which still picks randomly from the configured pool at
the configured duration.

**The status badge** (`#cardioGuestBadge`, a small fixed-position pill
OUTSIDE every `.player` element - deliberately not nested inside
`#cardioPlayer` or `#player`, so `hideAllPlayers()` never hides it):
shown for the guest exercise's whole duration once it starts
(`showCardioGuestBadge()`/`hideCardioGuestBadge()`), reading
`cardioState` directly (`block.durationS - (performance.now() -
cardioState.blockStartTime) / 1000`, clamped to 0) once a second rather
than depending on `cardioTick` (which isn't running during the guest
exercise). Turns to a pulsing `.warn` state once that remaining time
drops to 15s or under - the "sagt mir auch Bescheid, wenn ich die Übung
gleich wechseln muss" ask.

- **Visibility** (`syncCardioAddonTriggerBtn()`): the trigger button is
  now always shown whenever a Cardio session is running, independent of
  the automatic system's own `cardioAddonPrefs.enabled`/`pool` - those
  now only govern the *automatic* randomized-interval path; the client
  picks live, so no advance configuration is needed for the manual path
  at all. A deliberate behaviour change from the first version.
- Reuses `applyCardioGuestToState()`/`runSession()`/
  `returnFromCardioGuest()` exactly as the automatic path does - the
  picker only changes *what* gets passed in and *when* it fires, not the
  playback mechanism itself.

Test: `tests/cardio_addon_picker_test.py` (replaces the deleted
`tests/cardio_addon_manual_test.py`) - trigger button visible with zero
addon configuration; picker offers all 4 types with Cardio's own
countdown still ticking visibly behind it; switching the selected type,
the duration stepper's floor clamp, and Abbrechen all work; starting
takes over full-screen; the badge appears, reads and counts down
correctly, is not yet warning early in a block but is already warning if
opened late in a block; returns cleanly to the same still-running
activity afterward (not reset), badge and trigger button state reset
correctly. `tests/cardio_test.py` (existing, unmodified) continues to
cover the automatic randomized-interval path, untouched by this change.

### Follow-up: per-type background colour, trigger time window, rename (2026-09-30)

Trying the Tier 2 picker surfaced three concrete gaps, all fixed together:

1. **Background colour + intensity per guest type was simply missing.**
   `applyCardioGuestToState()` never touched `state.bgColorKey`/
   `state.bgIntensity` at all, so a guest exercise's background was
   whatever was left over from the last standalone use of that exercise -
   not a real setting. Added `bgColorKey`/`bgIntensity` to
   `cardioAddonPrefs.perType` (validated in `loadCardioAddonPrefs()` like
   every other field there) and a swatch-row + intensity slider per type
   in `renderCardioAddonFineTune()`, gated by `cardioGuestBgAllowed()`
   (`!EXERCISES[realId].bgIsStimulus` - skipped for vt-color, whose
   background already IS the trained colour, same rule the standalone
   Feineinstellungen already follows for it via `currentBgFill()`).
   Deliberately its own lightweight control, NOT wired into
   `wireBgIntensityControl()`'s Master-Einstellungen-cascade/preset-
   transfer machinery: that system assumes stable, always-present DOM,
   and this panel is torn down and rebuilt (`innerHTML = ""`) on every
   pool-selection change - a real architectural mismatch, not a shortcut
   taken for convenience. Consequence: these 3 background settings don't
   follow the app-wide Master default and have no "Auf Standard
   zurücksetzen" - a client who wants those specifically should say so
   and it can be added as a dedicated follow-up.
2. **Time window for the AUTOMATIC trigger** (`cardioAddonPrefs.windowEnabled`/
   `windowStartS`/`windowEndS`, `#cardioAddonWindowToggle` +two minute
   sliders): restricts `cardioTick()`'s existing randomized-interval check
   to a client-chosen sub-range of the total session time, measured
   against `cardioState.sessionStartTime` (new - separate from
   `blockStartTime`, which is per-activity and resets on every block/
   pause transition). Deliberately does NOT apply to the manual "+
   Zusatzimpuls" picker - that's the client's own in-the-moment choice,
   meant to work any time, which is exactly what they asked for when they
   first clarified the Tier 2 ask.
3. **Naming, corrected twice in one session.** The client asked whether
   `addon-flash` was actually Periphere Wahrnehmung's own Blitzreiz
   exercise - it was first renamed from "Zusatzaufgabe · Zahlen/
   Buchstaben" to "Ziffer/Buchstabe lesen · kurzer Reiz" on the mistaken
   assumption that it was a *different* thing from Blitzreiz. It isn't:
   checked against the actual rendering code, both draw through the exact
   same `drawPeriphChar()` (fixation point, a coloured digit/letter
   flashing briefly at a random peripheral position, same
   `PERIPH_AXIS_KEYS`/`PERIPH_ZONE_KEYS` positioning) - `addon-flash` IS
   the Blitzreiz mechanic, just running through the "Zusatzaufgabe"
   dual-task system (normally an add-on layered ON TOP of another
   exercise, see `buildAddonSchedule`) standalone on a blank host frame
   (`EXERCISES["cardio-flash-host"]`) instead of on top of a host
   exercise. Corrected back to **"Zusatzaufgabe · Ziffer/Buchstabe"** -
   the name this mechanism already carries everywhere else in the app
   (every other exercise's own "Zusatzaufgabe" add-on section uses this
   exact word) - per the client's explicit ask: one consistent name for
   one mechanism, wherever it shows up, rather than inventing a new one
   just for this Cardio context.

Test: `tests/cardio_addon_settings_test.py` - pool grid shows the
settled "Zusatzaufgabe · Ziffer/Buchstabe" label; background controls
appear for addon-flash but not vt-color; colour + intensity choices
persist across reload; window toggle/sliders sync, clamp (dragging
start past end pulls end along), and persist; functionally, a due
automatic-trigger interval is correctly blocked by an already-closed
window and correctly still fires inside an open one.

### Follow-up: "Beenden" inside a guest exercise no longer ends the whole session (2026-09-30)

Reported bug, found by the client trying the picker: pressing "Beenden"
(`#backBtn`, the shared player-bar's exit button) *inside* a running
guest exercise ended the entire Cardio session, not just the guest
exercise - clearly not what anyone wants from a 20-second dual-task
detour. Root cause: `abortTraining()`'s `cardioGuestActive` branch called
`abortCardio()` (ends everything) instead of `returnFromCardioGuest()`
(back to the still-running Cardio session, same as a guest exercise
finishing on its own). One-line fix - `returnFromCardioGuest()` was
already exactly the right function, just not the one being called here.
`leavePlayer()` still runs first either way (cancels the guest's own
raf, releases its wake lock, exits fullscreen, etc.) before handing off.

This also directly covers the client's "wechseln" (switch guest
exercise) ask: end the current one via Beenden (now correctly returns to
Cardio without losing progress), then tap "+ Zusatzimpuls" again and
pick a different one - no separate "switch" affordance was needed.

Test: `tests/cardio_addon_abort_test.py` - Beenden mid-guest-exercise
returns to the still-running `cardioPlayer` (not `cardioReady`/
`cardioHome`), badge and trigger button reset correctly, same activity
continues (not restarted); repeatable; Cardio's own `#cardioBackBtn`
(when NOT inside a guest exercise) still correctly ends the whole
session as before. `tests/cardio_test.py`'s own "abort mid-guest"
section was updated in place - it had encoded the old (buggy) behaviour
as its expected outcome.

### Phase 1: guest-type pool extended to the rest of the VT catalog (2026-09-30)

The client asked to start Phase 1 (the "gestuft, VT/NAT zuerst" plan from
the earlier tier-2-vs-tier-3 discussion). Investigating turned up a
correction to that plan worth recording: "VT and NAT share the same
engine" was only half true.

- **Visual Training** (the `EXERCISES` catalog `runSession()`/`tick()`/
  `state.exercise` shares) really is one engine end to end - confirmed by
  checking that `applyCardioGuestToState()` needed **zero** changes to
  support 8 more types, since it already dispatches purely off each
  exercise's own `usesColors`/`usesArrowColors`/`usesStroopColors`/
  `bgIsStimulus`/`type` flags. Added: `vrw-original`, `stroop-bg`,
  `4-diag`, `8-solo`, `8-vrw`, `cross-modal`, `cone-compass` (all trivial:
  same shape as the existing 4), and `cone-tap` ("Hütchen sortieren" -
  turned out easy too: its own `startConeTap()` engine already goes
  through the exact same shared `finishSession()`/`abortTraining()`
  lifecycle cardio-guest mode already depends on, so
  `triggerCardioGuest()` only needed one extra branch - call
  `startConeTap()` instead of `runSession()` when
  `EXERCISES[realId].type === "color-tap"`, mirroring the same dispatch
  `startSession()` itself already uses). `CARDIO_GUEST_TYPES` is now 12
  entries.
  - New gating helpers used throughout (`cardioGuestNeedsColors()`,
    `cardioGuestIsConeTap()`) so the Feineinstellungen panel only shows a
    colour row / stimulus-interval fields / background row for a type
    that actually uses them - `cardioGuestBgAllowed()` was tightened to
    match `currentBgFill()`'s real exclusion (`type === "color-tap" ||
    bgIsStimulus`, not just the latter) so cone-tap's background row
    (which would have had zero visible effect - its stage is hard-coded
    white in CSS) is correctly left out too.
  - **Not yet added**, deliberately: `periph-flash` (Periphere
    Wahrnehmung) - technically the same engine, but its settings surface
    (fixation point, zones, zone weights, ...) is much larger than a
    quick addition; own follow-up.
- **NAT domain** (Periphere Wahrnehmung aside) does **not** share this
  engine at all, despite the original "gestuft" assessment assuming it
  did. Checked directly: `EXERCISES` only ever contained the 13 VT-style
  entries; every NAT exercise (Merkspanne, Blitz-Raster, Flash, MOT, Go/
  No-Go, N-Back, Trail Making, Flanker, UFOV, Posner, Rotation, Simon,
  Suchtest, Doppelziel, Antizipationstest, Hick, Corsi, Reaktionsfeld, TS,
  Anti, Subitize, Alarm, Vorlauf, Stop, DSST, WCST, Navon, Iconic - ~25 in
  total) has its own dedicated player/prefs/finish path (see
  `hideAllPlayers()`'s long explicit list). Bridging each into
  `triggerCardioGuest()`/`returnFromCardioGuest()` individually is real,
  separate work - closer in size to the already-deferred Atemtraining/
  Movement/Workout lift than to "mechanical". Left for its own future
  phase rather than silently expanding this one; told to the client
  before proceeding rather than after.

Test: `tests/cardio_addon_phase1_test.py` - pool grid offers all (now 14,
updated again in the NAT batch below); fine-tune panels correctly show/
hide their colour row, background row, and stimulus/interval fields per
type (checked on `vrw-original`, `cross-modal`, `cone-tap` as
representative cases); the live picker offers all; each of the 8 new
types actually takes over full-screen (cone-tap via `#coneOrderStage`,
the rest via the canvas `#player`) and returns cleanly to the still-
running Cardio session via Beenden. `tests/cardio_addon_picker_test.py`'s
own exercise-choice count was updated alongside each batch that changes it.

### NAT batch 1: Periphere Wahrnehmung + Blitz-Raster (2026-09-30)

The client asked for "leg eine Reihenfolge fest und mach" (decide an
order and just do it) after the Phase-1 NAT-vs-Test mix-up was
explained. Investigating the actual nav markup (`data-nat-sub` tabs)
turned up a second correction: the NAT domain isn't ~25 exercises at
all - it's exactly **five**: Periphere Wahrnehmung, Remember,
Blitz-Raster, Flash Speicher Test, MOT-Fähigkeit. The ~25-exercise list
from the Phase-1 note (Go/No-Go, N-Back, Trail Making, ...) all belongs
to the separately-excluded Test domain (`testHome`) - confirmed by
checking `_body.html` directly (every one of those `OpenBtn` ids sits
inside `#testHome`, none inside `#natHome`). Corrected in the Phase 1
comment block in `app.js` alongside this batch.

Chose to start with the two NAT exercises that don't need a sub-mode
picker (Remember/Flash/MOT each have multiple starting modes - training
vs. fixed vs. shuffle vs. ... - and adding a mode-choice step to the
Cardio picker is real, separate UI work saved for the next batch):

- **`periph-flash`** (Periphere Wahrnehmung) turned out to be the exact
  same `runSession()`/`tick()` engine as everything in Phase 1 -
  `buildPeriphSchedule()` dispatches through the identical path. Only
  held back in Phase 1 because it reads its stimulus config from its own
  `state.periph*` fields (`periphKind`/`periphAxes`/`periphUseZones`/
  `periphZones`/`periphSizeMode`/`periphColors`) rather than the
  `active.colors`/etc. mechanism the `usesColors`/`usesArrowColors`/
  `usesStroopColors` flags drive - `applyCardioGuestToState()` got one
  new branch writing into those fields instead. Its cfg reuses the exact
  same `addonDefaultOwn()` shape as `addon-flash` (`cardioGuestIsPeriphLike()`
  now covers both) - same depth of configurability (kind, colours,
  duration, background), deliberately not adding axes/zones/zone-weight
  controls here either, matching addon-flash's own existing
  simplification rather than introducing new inconsistency between the two.
- **`blitz-raster`** (Blitz-Raster) is the first genuinely separate-
  engine NAT exercise bridged in, proving the harder pattern before
  Remember/Flash/MOT reuse it:
  - `startBlitzGame()` gained a second parameter, `prefsOverride` -
    when set (only from `triggerCardioGuest()`), the game runs with that
    config instead of the client's own saved `blitzPrefs`, and **never
    reads or writes `blitzPrefs`** - verified directly in
    `cardio_addon_nat_batch1_test.py` (grid size changed in Cardio's
    panel, client's own Blitz-Raster grid size and best-score checked
    unchanged afterward). `zones` stays at `PERIPH_ZONE_KEYS` (all of
    them) under an override, matching the "no zones picker in this
    panel" simplification used elsewhere.
  - `blitzStop()` (the "Beenden" handler) and `finishBlitzCombo()` (the
    existing duration-driven auto-finish Blitz-Raster already uses for
    Kombi blocks - reused as-is for the Cardio guest burst, passing
    `{ comboDurationS: cfg.duration }`) both got a
    `cardioGuestActive` branch calling `returnFromCardioGuest()`, mirroring
    the pattern already used for `comboProgram`. No best-score/history
    entry is recorded for a guest burst, matching how no other guest
    type gets its own history entry either.
  - A synthetic `EXERCISES["blitz-raster"]` entry (same idea as
    `cardio-flash-host`, never shown in any real picker) lets the
    generic `cardioGuestBgAllowed()`/`cardioGuestNeedsColors()` helpers
    look it up the same uniform way as a real catalog exercise.
  - Its Feineinstellungen panel is its own distinct field set (no
    stimulus/interval/colour fields at all - see `cardioGuestIsBlitz()`):
    Dauer, Startanzahl, a Leicht/Mittel/Schwer difficulty row (maps to
    `BLITZ_DIFFICULTIES`), a 3×3–8×8 grid-size row, a "Bei Fehler" row,
    and the standard background row - same labels/options as Blitz-
    Raster's own Ready screen for consistency.
- **Category grouping**: `CARDIO_GUEST_TYPES` entries now carry a
  `group: "vt" | "nat"` field (`CARDIO_GUEST_GROUPS` holds the display
  names); both the Feineinstellungen pool grid and the live picker
  render a heading before each new group, sorted Visual Training then
  Neuroathletik (NAT) - unprompted request from the client ("in diesem
  Auswahlmodus das auch nach den übergeordneten Themen sortieren"), done
  now since there's finally a second real group to show.

Deferred to the next batch, not silently folded in: **Remember, Flash
Speicher Test, MOT-Fähigkeit** - each needs the `prefsOverride` pattern
proven above AND a new sub-mode-picker step in the Cardio picker flow
(the client's explicit ask: "muss natürlich dann auch die Möglichkeit
bestehen, in diese Untermenüs zu gehen, wie man diese Übung dann starten
will").

Test: `tests/cardio_addon_nat_batch1_test.py` - pool grid and live picker
both grouped correctly; `periph-flash`'s panel has the same field depth
as `addon-flash`; `blitz-raster`'s panel shows only its own field set
(no colour row, no generic stimulus/interval fields) plus the background
row; both types actually take over full-screen and return to the still-
running Cardio session on Beenden (blitz-raster checked both via its own
duration running out AND an early Beenden mid-round); the client's own
real Blitz-Raster best score and grid-size setting are provably
untouched by a Cardio guest burst that used different settings.
`tests/cardio_addon_picker_test.py`/`cardio_addon_phase1_test.py`'s
exercise-choice counts updated to 14. Existing `blitz_test.py`/
`blitz_combo_test.py`/`blitz_grid_size_test.py`/`periph_test.py`/
`addon_periph_test.py`/`periph_pause_test.py`/`periph_stimcolor_test.py`
all re-verified passing unchanged - the `prefsOverride` parameter and
the two `cardioGuestActive` branches don't alter normal (non-Cardio)
behaviour.

### NAT batch 2: Remember, Flash Speicher Test, MOT-Fähigkeit (2026-09-30)

Closes out the NAT domain in the Cardio "+ Zusatzaufgabe" system -
`CARDIO_GUEST_TYPES` now has all 17 entries (12 Visual Training + 5 NAT).
These three share a shape batch 1 didn't need to handle yet: each has
several distinct **starting modes** (Remember: feste/bewegte Positionen,
Trainingsmodus; Flash: Konstant, Steigend-direkt, Steigend-mit-
Wiederholung, Trainingsmodus; MOT: Tempo/Anzahl/Beides steigt,
Trainingsmodus) - the client's explicit ask from the original request:
"muss natürlich dann auch die Möglichkeit bestehen, in diese Untermenüs zu
gehen, wie man diese Übung dann starten will".

- **`CARDIO_GUEST_MODE_LISTS`/`cardioGuestModeList(guestId)`**: one entry
  per domain, titles matching each domain's own mode names exactly. Used
  in two places - the live picker (a new sub-step, `cardioAddonPickerModeGroup`/
  `cardioAddonPickerModeRow`, shown only once a mode-bearing type is
  selected) and the Feineinstellungen panel (a persisted `perType[id].mode`
  default for the *automatic* randomized-interval trigger, which never
  goes through the picker at all).
- **`prefsOverride`, same pattern as Blitz-Raster in batch 1**:
  `startRememberGame`/`startFlashGame`/`startMotGame` all gained a third
  parameter; when set, the game reads every setting through it instead of
  the client's own saved `rememberPrefs`/`flashPrefs`/`motPrefs` and never
  touches them. `finishRememberCombo`/`rememberStop`,
  `finishFlashCombo`/`flashStop`, `finishMotCombo`/`motStop` each gained a
  `cardioGuestActive` branch calling `returnFromCardioGuest()` instead of
  their normal finish/abort path - no history entry, no best-score write
  for a guest burst, same as every other guest type.
- **Proportionate scope, same principle as every earlier batch**: the
  Cardio panel exposes Dauer, the mode choice, a difficulty row
  (Remember/Flash/MOT's own Leicht/Mittel/Schwer presets), a "Bei Fehler"
  row, and (Flash/MOT only) their own field particular to that domain
  (Flash: Buchstaben/Zahlen/Gemischt; MOT: Objektfarbe) plus the standard
  background row - deliberately not exposing each mode's own numeric
  starting parameters (`trainingStart`/`startCount`/`growStartObjects`/
  etc.), consistent with skipping Blitz's zones and periph-flash's
  axes/zone-weights earlier.
- Synthetic `EXERCISES["remember"/"flash"/"mot"]` entries, same purpose as
  `blitz-raster`'s in batch 1 (`cardioGuestBgAllowed()`/
  `cardioGuestNeedsColors()` lookups only, never shown in a real picker).

Test: `tests/cardio_addon_nat_batch2_test.py` - pool grid at 17 types; all
three panels show mode-row/difficulty-row/error-row (plus Flash's kind-row,
MOT's colour-row) and nothing from the generic stimulus/interval field set;
live picker's mode sub-step appears only for these three and offers the
right mode count each; all three take over full-screen via their own
players and return to the still-running Cardio session on Beenden; the
client's own real Remember best score is untouched by the guest bursts.
`cardio_addon_phase1_test.py`/`cardio_addon_picker_test.py`/
`cardio_addon_nat_batch1_test.py`'s exercise-choice counts updated to 17
(the last one had been missed in an earlier pass and briefly regressed to
"False" before this fix).

### Cardio-Zusatzaufgabe: Zeitfenster-Slider auf Plan-Gesamtzeit begrenzt (2026-09-30)

Client-reported bug: the "nur in einem bestimmten Zeitfenster"
ab/bis-sliders could be dragged out to a fixed 60 Min. regardless of how
much time the client had actually put together in the Cardio-Einheit
itself ("Ich kann jetzt gerade bis über 25 Minuten schieben, aber habe nur
10 Minuten Joggen ausgewählt"). Fixed by capping both sliders' `max`
attribute live to `cardioItemsSeconds(cardioPrefs.items)` (the same total-
including-interleaved-pauses helper the "ca. X Min." previews already use)
via a new `syncCardioAddonWindowBounds()`, re-run whenever that total can
have changed (activity added/removed/resized, pause adjusted).

Deliberately **display-only** - it never overwrites the stored
`windowStartS`/`windowEndS` themselves, only what's shown/draggable right
now. An early version did persist the clamp and broke on the very first
render: `openCardioReady()` renders this panel before the client has
picked any activity yet (`cardioPrefs.items` still empty, total 0), so the
cap would have permanently shrunk the default 600s (10 Min.) down to
almost nothing and saved that - exactly backwards from the client's own
follow-up requirement ("Sollte ich jetzt was Zweites hinzufügen, muss das
untere dann halt auch in der Skala weiterspringen, dass ich dann die
Möglichkeit habe, weiterzuziehen"). With the display-only fix, adding time
back simply raises the max again and the client's last actual choice
reappears - nothing was ever destroyed, it was just temporarily
unreachable while the plan was smaller.

Test: `tests/cardio_addon_window_bounds_test.py` - one 10 Min. activity
caps both sliders at 10 and a programmatic drag past it is pulled back;
adding a second activity raises the cap and dragging out to the new max
actually works; removing that activity again shrinks the cap back down to
10 without leaving the displayed value stranded above it.
`cardio_addon_settings_test.py`'s "ab" sweeps past "bis" case updated
from its old arbitrary 15 Min. (now unreachable with only one 10 Min.
activity in that test) to first lowering "bis" to 5 and then dragging "ab"
to 8, inside the new 10 Min. cap.

### Cardio: bidirectional chapter-nav (vor/zurück/neu starten) + größerer Abbrechen-Button (2026-09-30)

Client's own comparison to Tabata: "Nächste Aktivität" during a running
Cardio session used to be one-directional (forward-only, dynamic text
label swap). Now matches Tabata's own `.chapter-nav` triple (« vorherige /
↻ neu starten / weiter »), plus swipe left/right, plus the ability to
restart just the current activity's clock without moving position.

- **`cardioJumpToIndex(idx, dir)`**: Cardio's own engine is index-based
  (`cardioState.index`/`blockStartTime`), unlike Tabata's frame-schedule-
  offset one (`circuitJumpToWorkIndex()`) - jumping is direct index
  arithmetic + a `blockStartTime` reset rather than recomputing a
  `startTime` offset. `dir` says which way a landed-on pause pseudo-item
  gets skipped past (a pause is never adjacent to another pause, so one
  extra step in the same direction always lands back on a real activity) -
  mirrors the existing forward-skip's own pause-skipping logic exactly,
  just made symmetric for `cardioPrevBtn` too. Skipping past the last
  activity (or index goes negative at the very first one, clamped to 0)
  reaches the same `finishCardio()`/no-op-restart edges a natural run would.
- **`cardioRestartBtn`**: just resets `blockStartTime`, no index change.
- The markup swap to icon-only buttons (from `.pause-skip` text buttons)
  had shipped a commit ahead of this JS wiring by an oversight - caught
  before it reached a client-visible state, since `cardioTick()` was still
  overwriting the icon with a full text string
  (`"Pause überspringen »"`/`"Nächste Aktivität »"`) on every phase
  change. Fixed alongside: those two lines now update `.title`/
  `aria-label` instead, leaving the icon itself untouched.
- **Abbrechen button** in the Cardio "+ Zusatzaufgabe" live picker was
  effectively browser-default-sized (`.pause-skip` alone carries no
  padding/font-size of its own) - client-reported as too small next to
  "Jetzt starten". Given its own ID-scoped rule instead of enlarging
  `.pause-skip` itself, which is shared with `pauseSkipBtn`/
  `wimhofHoldDoneBtn`/`workoutRestSkipBtn` elsewhere - none of those were
  part of the report and shouldn't resize just because this one needed to
  grow. Sits visibly between the old tiny default and the full `.start-btn`
  size, matching the client's own "nicht ganz so groß, aber jeweils
  größer" framing.

Test: `tests/cardio_chapter_nav_test.py` - all three buttons present;
skip/prev correctly hop over the interleaved pause onto the next/previous
REAL activity in both directions; restart keeps the same activity but
visibly resets its countdown; prev at the first activity is a safe no-op;
skipping past the last activity finishes the session same as running out
the clock. `cardio_addon_picker_test.py` gained a size check confirming
Abbrechen sits strictly between the old default and "Jetzt starten".

### Cardio-Zusatzaufgabe: volle Feineinstellungen auch live im Picker (2026-09-30/10-01)

Client's follow-up, using Periphere Wahrnehmung and Blitz-Raster as the
illustrating example: pre-start Feineinstellungen lets you configure every
field of a guest type ("alle Details einstellen"), but triggering the SAME
exercise live from inside a running Cardio session only ever offered the
exercise pick itself - every "Unterpunkt" was missing. Generalized
immediately afterward to all 17 types ("bei allen Übungen die gleichen
Einstellungsmöglichkeiten... überall volle Kontrolle"), then once more to
mean truly the same depth as the standalone exercise itself ("genau so als
wenn man die Übung einzeln machen würde"), not the "proportionate scope"
simplification this file had documented as a conscious choice in every
earlier batch.

- **`buildCardioGuestFieldsHtml(t, cfg)`**: the markup-only half of what
  used to be inline in `renderCardioAddonFineTune()`, now shared verbatim
  between it and the live picker. Takes a type and a cfg object, returns
  the same field HTML either caller renders.
- **`wireCardioGuestFields(container, getCfg, { onSelect, onPersist })`**:
  the wiring half, parameterized over where the mutable cfg comes from
  (`getCfg`) and what happens after a change - `onSelect` (full rebuild,
  for a button-style choice whose "active" class has to move) vs.
  `onPersist` (no rebuild, for a plain value/checkbox/slider edit, matching
  the original code's own distinction - a full rebuild on every pixel of a
  dragged bg-intensity slider would be janky).
- **Pre-start panel** (`renderCardioAddonFineTune`): unchanged behaviour,
  `getCfg` resolves `cardioAddonPrefs.perType[type]`, `onSelect`/`onPersist`
  both call `saveCardioAddonPrefs()` as before.
- **Live picker** (`renderCardioAddonPickerDetail`, new): `cardioAddonPickerCfg`
  is an EPHEMERAL deep copy of the selected type's saved `perType` entry -
  seeded fresh every time a type is (re-)selected
  (`cardioAddonPickerSelectType()`), and never written back
  (`onPersist` is a no-op there) - this is still the in-the-moment "just for
  this once" choice, not a settings change, same principle the duration-only
  override already followed before this. `triggerCardioGuest()`'s signature
  simplified from `(explicitId, explicitDurationS, explicitMode)` to
  `(explicitId, explicitCfg)` - the picker now hands over a complete,
  already-fully-configured cfg object instead of two narrow overrides
  layered onto the saved default.
- The old dedicated duration-stepper markup (`cardioAddonPickerDurationRow`/
  `Minus`/`Plus`/`Value`, 15-180s floor/ceiling) and mode-group markup
  (`cardioAddonPickerModeGroup`/`Row`) are gone - both are now just part of
  whichever type's shared field markup renders into
  `#cardioAddonPickerDetail` (Dauer: the same 5-120s range the pre-start
  panel already used; mode-row: already built into
  `buildCardioGuestFieldsHtml()`'s Remember/Flash/MOT branch).

Test: `tests/cardio_addon_picker_full_settings_test.py` (new) - a plain
generic type, Periphere Wahrnehmung and Blitz-Raster each show the exact
field rows their own Feineinstellungen panel would; a live kind/grid-size
edit visibly takes effect (Blitz-Raster's rendered cell count actually
changes, 16 -> 36 for a live 4x4 -> 6x6 edit) while the saved per-type
default stays untouched throughout, including after actually starting the
live-edited burst - the central guarantee restated for the new flow.
`cardio_addon_picker_test.py` updated for the new Dauer field (replacing
its old stepper assertions) plus the same persisted-default-untouched
check for duration specifically. `cardio_addon_nat_batch2_test.py`'s mode-
group assertions updated to the unified `[data-mode-row]` selector inside
`#cardioAddonPickerDetail`.

Client confirmed via follow-up how deep this should go on the two points
that genuinely needed asking about (zone-dominance weighting; each mode's
own further numeric fields): include them too, each nested under its own
collapsible "Feineinstellungen" sub-section rather than flattened into the
main field list - "mit rein, aber ... weggeklappt, ausklappbar" for both.
Proceeding batch by batch, same discipline as the NAT batches above.

### Full-Parität Batch A: Periphere Wahrnehmung/addon-flash - Achsen, Zonen, Dominanz, Größe (2026-10-01)

`buildCardioGuestFieldsHtml()` gained, for both periph-like types
(`cardioGuestIsPeriphLike()`): the "Bereich" axis row (Horizontal/Vertikal/
Diagonal + "Überall", multi-select, can reach zero with a warning hint -
`data-axis`/`data-axis-all`) with a mutually-exclusive toggle to a 3×3
zone-selection grid (`data-zones-toggle`/`data-zone`, minimum one zone
enforced, same rules as the standalone Ready screen's own `periphFieldRow`/
`periphZoneGrid`/`periphAllBtn`), and "Größe der Reize" (`data-sizemode`:
gleich/wachsend). `cardioGuestDefaultCfg()`'s periph-like branch already
carried `axes`/`useZones`/`zones`/`sizeMode` in its cfg shape via
`addonDefaultOwn()` - genuinely new here was only the UI to reach them, not
new data fields.

**Zone-dominance weighting is periph-flash-only**
(`cardioGuestHasZoneWeights()`): addon-flash's own standalone "Zusatzaufgabe"
panel (`#addonGroup`) never had this control either, so giving it to
addon-flash here would be LESS "genau so wie einzeln", not more. Added
`zoneWeights` to the periph-like cfg shape (harmless unused data for
addon-flash) and to `loadCardioAddonPrefs()`'s validation, and
`applyCardioGuestToState()` now also writes `state.periphZoneWeights` (it
didn't before - the actual gameplay reads it via `randPosFromCfg()`, not
just the display). Rendered only when `cfg.zones.length > 1` (weighting one
zone against nothing is meaningless, matching `renderPeriphZoneWeights()`'s
own `show` condition), inside a `<details class="advanced">` reusing the
same collapsible styling/plus-minus icon as `#cardioAddonAdvanced` itself,
one `Dominanz` slider per currently-selected zone.

Test: `tests/cardio_addon_picker_periph_fields_test.py` - both periph-like
types show the new rows pre-start and live; axis multi-select/"Überall"
(including the "only reaches zero from an already-fully-on state, not from
a partial one" nuance) and the zone grid's minimum-one-zone rule behave
exactly like the standalone Ready screen; periph-flash's own "Feineinstel-
lungen" collapsible appears only when it has >1 zone selected and
addon-flash never shows it at all; a live zone-weight/axis/size edit is
provably never written back to the saved per-type default, including after
actually starting the live-edited burst.

### Full-Parität Batch D: Modus-Feinwerte Remember/Flash/MOT (2026-10-01)

Closes out the "genau so als wenn man die Übung einzeln machen würde" arc
started by Batches A-C: each mode's own further numeric fields, nested
inside the type's existing "Feineinstellungen" collapsible (client's own
confirmed answer to the clarifying question) and shown/hidden purely based
on `cfg.mode` - exactly which fields a mode needs mirrors each domain's own
dedicated Ready screens field-for-field:

- **Remember** - "Trainingsmodus" only: Startzahl (`trainingStart`, 2-16),
  Positionsart (`trainingPositionMode`: fest/bewegt) and Nach Erfolg
  (`trainingProgress`). "Feste Positionen"/"Bewegte Positionen" modes need
  nothing extra - their own behaviour is fully determined by the mode
  choice itself (`REMEMBER_MODES[mode].keepPositions`).
- **Flash** - all three non-training modes differ: "Konstant" shows
  Anzahl der Zahlen (`constantCount`, 2-6); "Steigend" (climb/climbRepeat)
  shows Startanzahl (`startCount`, 2-9), with "Steigend, mit Wiederholung"
  additionally showing Wiederholungen je Stufe (`repsPerLevel`, 2 or 3);
  "Trainingsmodus" shows its own Startzahl (2-9, a different range than
  Remember's) + Nach Erfolg.
- **MOT** - "Tempo steigt" shows the FIXED Anzahl Objekte/Ziele
  (`objectCount`/`targetCount`); "Anzahl steigt"/"Beides steigt" show the
  GROWING Start-Anzahl pair (`growStartObjects`/`growStartTargets`);
  "Trainingsmodus" shows its own Start-Anzahl pair plus Start-Tempo-Stufe
  (`trainingSpeedStep`) and Nach Erfolg.
- A single shared `[data-progressfield]` click handler covers all three
  domains' own "Nach Erfolg" boolean toggle (the field name to set comes
  from the button's own `data-progressfield` attribute) - Remember's
  `data-posmode` and Flash's `data-repsperlevel` have no equivalent in the
  other domains, so those stay their own small handlers.

**Real isolation bugs fixed** (same class as every earlier batch):
`startRememberGame()` read `trainingStart`/`trainingProgress`/
`trainingPositionMode` straight from `rememberPrefs`; `startFlashGame()`
did the same for `constantCount`/`startCount`/`trainingProgress`/
`startLevel`/`trainingStartLevel`; `startMotGame()` did the same for
`objectCount`/`targetCount`/`growStart*`/`training*`. All now read `p`
(the override when one is given) instead.

**Real pre-existing standalone bug fixed as a side effect**: `flashState`
never actually carried its own `repsPerLevel` field at all (only
`flashPrefs.repsPerLevel` existed) - `flashSuccessTransition()`'s own
"climbRepeat" branch does `flashState.repsDone >= flashState.repsPerLevel`,
which compared against `undefined` and could therefore never actually
advance past the first count, in standalone play too, not just under a
Cardio override. Threading `p.repsPerLevel` through for the Cardio
isolation fix fixed this for real play as a direct byproduct.

Test: `tests/cardio_addon_picker_mode_fields_test.py` - for all three
domains, switching through every mode shows exactly the right field(s) and
hides the others (Flash's climb-vs-climbRepeat distinction and MOT's three
distinct field-pairs both explicitly checked); a live edit to each new
field type is proven to move independently; the saved per-type default is
untouched by any of it, including after cancelling out of the picker.
`remember_test.py`/`remember_combo_test.py`/`flash_test.py`/
`flash_combo_test.py`/`mot_test.py`/`mot_combo_test.py` re-verified passing
unchanged.

With Batch D done, the Cardio "+ Zusatzaufgabe" live picker and the
pre-start Feineinstellungen panel are now field-for-field identical for
every one of the 17 guest types - the client's "genau so als wenn man die
Übung einzeln machen würde" ask, fully closed.

**Standing convention going forward (client, 2026-10-01)**: this parity is
not a one-time backfill, it's now a permanent requirement for anything
added to `CARDIO_GUEST_TYPES`'s two groups (`vt`/`nat`) from here on -
whether it's a brand-new Visual-Training/NAT exercise built directly, or a
Test-Bereich exercise the client later decides is good enough to promote
out of Test (see "Test-Bereich (autonomous, ongoing)" below). Whoever adds
such an exercise must, in the same piece of work: add it to
`CARDIO_GUEST_TYPES`, give `cardioGuestDefaultCfg()` a full default config
for it, extend `buildCardioGuestFieldsHtml()`/`wireCardioGuestFields()`
with whatever fields that exercise's own Ready screen exposes (mode-
conditional where relevant, deep/exotic ones nested under a collapsible
`<details class="advanced">`), and double-check its own `start*Game()`
reads every one of those fields from `prefsOverride` (`p`), never straight
from the real saved prefs object - that exact isolation-leak mistake was
made and caught seven separate times during Batches B-D (see each batch's
own section above). The client does not want to be asked about this each
time; treat it as implied scope on any new exercise, the same way a new
screen is implied to need its own test file.

### Drei Probleme behoben (2026-10-01, client: "Beseitige die Probleme")

The first two are pre-existing and unrelated to Cardio, surfaced
incidentally while running full regression suites around the Batch A-D
work above (confirmed via `git stash` at the time not to be caused by any
of it). The third is Cardio's own, reported with screenshots right after.

- **Corsi block occasionally overlapping the hint/player-bar**
  (`stage_hint_overlap_audit_test.py`, RNG-dependent - only showed up with
  certain random layouts). Root cause: `startCorsiGame()` called
  `renderCorsiBoard(buildCorsiBoard())` BEFORE setting
  `els.corsiHint.textContent`, so `corsiStageBounds()`'s own
  `stageTopClearanceY()` call measured the hint element's still-empty
  pre-round height, not the "Gleich geht's los …" text's real rendered
  height that appears moments later - letting a block land in the gap
  between the two. Fixed by setting the hint text first, so the collision-
  avoidance math sees the real clearance it needs to avoid from the start.
  Confirmed with 10 consecutive runs of the audit test (previously failed
  intermittently) plus `corsi_test.py`, both clean.
- **`flash_fixpoint_test.py`'s "fixpoint visible by default" check was
  stale**, not flaky (reproduced deterministically every run). The test's
  own polling loop waits for `#flashInputPanel` to become visible before
  reaching that assertion - but `flashOpenInput()` deliberately hides the
  fixpoint the moment the answer-input phase begins (it would otherwise
  cover the keypad), restoring it only for the next round's own flash/gap
  phase. By the time the assertion ran, it was therefore always checking
  the wrong phase, regardless of the actual setting. Fixed by moving the
  assertion (and its companion grey-dot-colour check) to right after
  starting the round, before that polling loop - still well within the
  flash/gap sequence, which is what the check was always meant to cover.
  `flash_test.py`/`flash_combo_test.py` re-verified passing unchanged.
- **The floating "Cardio: noch M:SS" guest badge covered the "Vollbild"
  button** of several guest players (screenshots: a cone-tap-style guest
  and an arrow exercise, both showing "Vollbild" peeking out from behind
  the badge in the top-right corner). `.cardio-guest-badge`'s `top` was a
  single hardcoded offset, assuming every guest player's own top-right
  button lived further down than it - true for the generic VT player's
  `#fsBtn`, not for several of the separate-engine domains' own
  `.player-bar` (which can wrap to two rows on a narrow phone, same note
  already on `.player-bar button,.player-status` elsewhere in this file).
  New `cardioGuestBadgeTop()` measures whichever `.player-bar` is actually
  rendered right now (0-height for every hidden one, `cardioPlayerBar`
  itself excluded - it sits behind the guest, out of view) and positions
  the badge just below its real bottom edge, recomputed on every 1s tick
  (`updateCardioGuestBadge()`) so it stays correct even if that bar's own
  height changes mid-run.

  Test: `tests/cardio_guest_badge_overlap_test.py` - checks real
  bounding-rect overlap between the badge and each guest player's own
  Vollbild button, across the generic VT player (both an arrow exercise
  and cone-tap, matching the two screenshots) and all four separate-engine
  domains. `cardio_addon_picker_test.py`/`cardio_test.py`/
  `cardio_addon_nat_batch1_test.py`/`cardio_addon_nat_batch2_test.py`
  re-verified passing unchanged.

### Full-Parität Batch C: Flash Speicher Test und MOT - restliche Felder (2026-10-01)

**Flash Speicher Test** reuses the exact same "Bereich" (axes/zones)
mechanism Batch A built for Periphere Wahrnehmung - same
`PERIPH_AXIS_KEYS`/`PERIPH_ZONE_KEYS`, same generic `data-axis`/`data-zone`
wiring already in `wireCardioGuestFields()` (no new handlers needed, it
already works for any type whose cfg carries `axes`/`zones`/`useZones` -
the widened gate is just `cardioGuestIsPeriphLike(t.id) ||
cardioGuestIsFlash(t.id)`), no dominance-weighting (flashPrefs never had
that) and no "Größe der Reize" (kept periph-only - flashPrefs has no
`sizeMode` concept at all). Plus its own **Fixpunkt** (fixation point)
nested under a new "Feineinstellungen" (`#flashAdvanced`'s own grouping):
enable/disable toggle, character text input (`data-fixchar`), a single-
select colour row reusing `FIX_COLOR_LIB` (grey + the Stroop palette,
radio-based like the background colour picker) and a size slider - plus
raw Einblenddauer/Pause sliders (`stimulusS`/`intervalS`) for the same
"go beyond the three difficulty presets" reason Batch A's zone-weighting
nests under a collapsible.

**MOT-Fähigkeit** gets "Darstellung" (flach/3D-Optik, `style`) and a
second, independent colour picker "Farbe des Ziels" (`targetColors`,
same `STROOP_COLOR_LIB` multi-select mechanism as the existing "Farbe der
Objekte", just its own cfg field and `data-targetcolor` attribute so
`wireCardioGuestFields()` can tell the two checkbox groups apart), plus
raw Geschwindigkeit/Verfolgungsdauer/Markierdauer sliders under its own
Feineinstellungen.

**Real isolation bugs found and fixed** (same class as Batch B's Blitz-
zones fix - reading straight from the client's own real prefs object even
under a `prefsOverride`, silently ignoring the override entirely):
`startFlashGame()`'s state construction read `axes`/`zones`/`useZones` from
`flashPrefs` unconditionally; `renderFlashFixpoint()` read `fixEnabled`/
`fixChar`/`fixColor`/`fixSize` from `flashPrefs` with no override path at
all (now prefers `flashState`'s own captured fix* fields once a round is
running, falling back to `flashPrefs` only in the Ready-screen preview
context before `flashState` exists); `startMotGame()`'s state construction
read `style`/`targetColors` from `motPrefs` unconditionally. All three are
fixed now that the Cardio panel actually carries these fields to read
instead. `objectCount`/`targetCount`/`growStart*`/`training*` still read
from `motPrefs`/`flashPrefs` directly - same open gap, left for Batch D
(not exposed in the Cardio panel yet, so there is nothing else to read
from).

Also generalized the shared `input[data-f]` handler in
`wireCardioGuestFields()`: it now updates a companion
`[data-fvalue="type-field"]` label for any range-slider field (not just
the one-off `data-bgintensity` case), which is what lets Remember's
`revealBaseS`/`revealStepS`, Flash's `stimulusS`/`intervalS`/`fixSize` and
MOT's `speed`/`trackS`/`highlightS` all reuse the exact same generic
wiring as sliders instead of each needing its own bespoke handler.

Test: `tests/cardio_addon_picker_flash_mot_fields_test.py` - all new rows
present pre-start and live for both types; a live fixation-disable and
zone-narrowing on Flash is provably reflected in the running game
(`#flashFixpointEl` actually hidden, not the untouched real default) and
never written back to the saved default; a live MOT style edit actually
renders (`.mot-object.style-3d` present), same isolation guarantee
afterward. `flash_test.py`/`flash_combo_test.py`/`mot_test.py`/
`mot_combo_test.py`/`remember_test.py`/`remember_combo_test.py`/
`cardio_addon_nat_batch2_test.py` re-verified passing unchanged. Two pre-
existing, unrelated issues surfaced incidentally while running the full
suite around this batch (confirmed via `git stash` that they reproduce
identically without any of this batch's changes, so out of scope here):
`stage_hint_overlap_audit_test.py`'s Corsi block placement is RNG-flaky
(occasionally overlaps the hint/bar depending on the random layout drawn);
`flash_fixpoint_test.py`'s "fixpoint visible by default" check is stale -
by the time its polling loop reaches that assertion, Flash's own input
phase has already begun, which deliberately hides the fixpoint regardless
of settings (`flashOpenInput()`'s own comment: "Always hide it here...").

### Full-Parität Batch B: Blitz-Raster - eigene Zonen-Auswahl (2026-10-01)

Blitz-Raster's own "Bereich" is simpler than Periphere Wahrnehmung's
(Batch A): no axes concept at all, no `useZones` toggle - the 3×3-Zonen-
Raster directly restricts which grid cells can light up, always on, same
as the standalone Ready screen's own `blitzZoneGroup`/`blitzZoneGrid`/
`blitzZoneAllBtn`. No dominance-weighting either - `blitzPrefs` never had
that concept. Added `zones` to the cfg shape (`cardioGuestDefaultCfg()`'s
blitz-raster branch, `loadCardioAddonPrefs()`'s validation - same "forces
non-empty on load" rule `loadBlitzPrefs()` itself already applies) and new
`[data-blitzzone]`/`[data-blitzzone-all]` markup/wiring (kept distinct from
Periph's `[data-zone]`/`[data-axis-all]` since the two domains' zero-
reachability rules differ: Blitz's own "Überall" can reach zero from a
fully-on state, same as Periph's axis "Überall", but Blitz's INDIVIDUAL
zone clicks enforce a minimum of one, unlike Periph's zones which also
enforce that minimum - cross-wiring them would have been wrong for neither
domain, so they stay separate).

Fixed a real, previously-undetected bug while at it: `startBlitzGame()`'s
`prefsOverride` path had `zones: (prefsOverride ? PERIPH_ZONE_KEYS :
p.zones).slice()` - under ANY Cardio guest burst, zones were silently
forced to "all of them" regardless of what the (until now nonexistent)
panel said, because the override branch never looked at `p.zones` at all.
Now reads `p.zones` directly (falling back to all only if genuinely
missing), so a live zone edit actually restricts gameplay instead of being
silently discarded.

Test: `tests/cardio_addon_picker_blitz_zones_test.py` - zone grid present
pre-start and live; "Überall"'s partial-state-vs-fully-on nuance and the
minimum-one-zone rule behave exactly like the standalone Ready screen; a
live zone edit is provably never written back to the saved default, even
after actually running the live-edited burst. `blitz_test.py`/
`blitz_combo_test.py`/`blitz_grid_size_test.py`/
`cardio_addon_nat_batch1_test.py` re-verified passing unchanged.

