# Cardio + dual-task "Zusatzübung" windows (2026-09-28)

Client's ask, in the order it actually arrived: a separate Cardio area
(general and interval-configurable) that could later couple into Kombi;
then, refined - an exercise-selection-style picker of cardio activities
(Joggen/Rad fahren/Crosstrainer/...), each block its own duration and an
optional free-text label (Warm-up/Cooldown/anything, not position-locked),
each block optionally itself structured as an interval (Belastung/
Erholung); then, further extended - cardio activities are a natural fit
for dual-task training, reusing "wie auch die Zahlen peripher einblenden
Geschichte bei anderen Übungen" (the existing Zusatzaufgabe) as the
model, but not limited to that one stimulus - "auch andere sinnvolle
Übungen" should be combinable too, each individually fine-tunable and
saved under its own position so switching which ones are enabled never
overwrites another's settings. Presented as a small/large fork (extend
the existing addon vs. a generic "exercise window" host); client chose
**large**, explicitly confirming it should work automatically for the
client (a settings toggle they set for themselves, like the existing
Zusatzaufgabe, not something a coach has to author into a training code)
and should support multiple simultaneously-eligible guest exercise types,
not just the flash.

**New top-level domain**: a 7th `section-tab`/`SCREENS` entry (`cardio`
→ `cardioHome`), inserted into all 6 existing nav-bar copies between
Workout and NAT (`_body.html` repeats this nav verbatim per screen -
there is no shared partial). `cardioHome` → `cardioReady` (the builder,
reached via `#cardioStartCard`, structurally a close mirror of
`workoutTabataReady`: `combo-add-grid` picker, `circuit-item-row` block
list, `wirePresetSaveForm`/`makePresetStore`/`renderPresetList` for named
presets - all reused verbatim, not reinvented) → `cardioPlayer` (the
running timer) → `cardioDonePanel`. **No coach-authored Cardio codes and
no custom/own activities yet** - `CARDIO_ACTIVITIES` is a fixed 7-item
catalog (Joggen/Rad fahren/Crosstrainer/Rudergerät/Walking/
Treppensteigen/Schwimmen); both are easy to add later the same way
Workout's own custom-exercise form and `lookupProgram()` dispatch work,
skipped tonight to keep scope honest rather than half-build either.

**Cardio block** (`cardioPrefs.items[]`, `fwmc-cardio-v1`): `{activity,
durationS, label, interval: null|{onS,offS}}`. Duration steps in whole
minutes (60s increments, 1-60 min) since Cardio blocks are naturally much
longer than a bodyweight-exercise rep; interval on/off phases step in
5s increments separately (5-300s) since those are the short sub-cycle.
Deliberately **no "Sätze"/repeat-the-whole-sequence concept** like
Workout circuits have - the client's own example ("10 min joggen, dann
10 min radfahren, dann 10 min crosstrainer") is a straight one-pass
sequence, and no inter-block rest screen either (switching cardio
machines isn't a rest the way switching bodyweight exercises is) -
`cardioTick()` just updates the activity name/label/countdown/phase
continuously as `cardioState.index` advances, no transition screen.

**Dual-task engine** (`cardioAddonPrefs`, `fwmc-cardio-addon-v1`):
`{enabled, pool:[...ids], intervalMinS, intervalMaxS, perType:{[id]:cfg}}`.
Client-facing exactly like the existing Zusatzaufgabe - one on/off toggle,
works during ANY cardio run (self-built today; automatically also for a
future coach-authored one, since it's read from the client's own prefs,
not from the programme). `CARDIO_GUEST_TYPES` is a **deliberately curated
pool**, not "every exercise in the app": the existing peripheral flash,
plus VT-Farbe, Stroop-klassisch, 4-Pfeile-gerade - short, single-glance,
quick-reaction tasks that suit a brief look mid-cardio. Explicitly
excluded: anything needing several seconds of *sustained* uninterrupted
attention (Corsi/Change-Detection/N-Back-style delayed recall, MOT) - a
glance mid-jog can't sustain that, so it was never a small-vs-large
question, just a "what's actually usable here" one. Each pool member gets
its own fine-tune panel (`renderCardioAddonFineTune()`) - Dauer/Reiz-Dauer/
Pause-min/-max/Farben, plus a Zeichentyp choice for the flash - stored
separately per type under `perType`, so enabling/disabling pool members
never touches another member's remembered settings. The flash's own
Bereich/Zonen/Größenmodus controls (real, rich options on Periphere
Wahrnehmung's own ready screen and the normal per-exercise Zusatzaufgabe)
are **deliberately not exposed here** - fixed sensible defaults
(`addonDefaultOwn()`) instead, to keep the settings surface buildable in
one pass; easy to add later the same way the per-exercise version already
has it, if ever wanted.

**How a guest window actually plays** (`triggerCardioGuest()`/
`returnFromCardioGuest()`, `app.js`): reuses the real
`runSession()`/`finishSession()`/`session`/`raf` exercise lifecycle
as-is for real exercise types (`vt-color`/`stroop-classic`/`4-straight`),
*and* for the flash - via a synthetic `EXERCISES["cardio-flash-host"]`
entry (`type:"flash-host"`) whose schedule is one giant `"blank"` frame
spanning the window (`buildFlashHostSchedule` - reuses `drawScene`'s
existing "blank" case: neutral background + fixation point, no new
drawing code), with the *real* Zusatzaufgabe engine
(`buildAddonSchedule`/`drawAddonOverlay`/`drawPeriphChar`) doing the
actual flashing on top of it via one special-case branch at the top of
`buildAddonSchedule` that sources config from `cardioAddonPrefs.perType
["addon-flash"]` instead of the normal per-exercise `ADDON_KEY` store.
This means "port the peripheral flash onto Cardio" and "add three more
exercise types as options" turned out to be **the same mechanism** once
the flash was wrapped in a fake host exercise - worth remembering if this
pattern is ever wanted for another non-canvas timer screen.
`applyCardioGuestToState()` mirrors `startSession()`'s own colour-active
setup (`usesColors`/`usesArrowColors`/`usesStroopColors` branch to
`active.colors`/`.arrowColors`/`.stroopColors`) since a guest run is more
"standalone single exercise" than "coach programme block". Nothing here
needs to restore `state` afterward - `openReady()` already
unconditionally does `loadPrefs()` before setting `state.exercise` on
its own next visit (a pre-existing idiom, the same one `program` blocks
already relied on), so a guest's transient mutation is self-healing.

**The one real structural trap, hit and fixed here too** (same shape as
the Step-3 video-player bug above): `cardioPlayer` is a "player" overlay
like `els.player`/`workoutPlayer`, not a `SCREENS` member - `showScreen()`
never hides or shows it. `triggerCardioGuest()` correctly relies on
`runSession()`'s own `hideAllPlayers()` call to hide it (full-screen
takeover is exactly what's wanted for a guest window), and
`returnFromCardioGuest()` correctly re-shows it after its own
`hideAllPlayers()`. But `abortCardio()` - reached from the plain
"Beenden" button on the Cardio *timer* screen itself, no guest involved -
originally only called `showScreen("cardioReady")` and forgot
`cardioPlayer` needs an explicit hide too; caught by a Playwright
assertion (`tests/cardio_test.py`), not by eye. `abortTraining()` also
gained a `cardioGuestActive` branch (checked before it mutates the flag
via `leavePlayer()`), mirroring the existing `comboProgram`/`program`
branches exactly, so the shared player bar's "Beenden" mid-guest-window
correctly tears down the whole Cardio session, not just the guest.

**Wake lock & backgrounding**: `finishSession()` skips `releaseWakeLock()`
when `cardioGuestActive` (mirrors the `program`/`comboProgram` branches -
Cardio's own `finishCardio()` releases it once, at the very end of the
whole sequence, not per guest window). The `visibilitychange` handler
**deliberately does not** shift `cardioState.blockStartTime` forward the
way it does for `session`/`workoutState`/etc. - those pause-and-resume on
backgrounding by design (a reaction-time exercise shouldn't silently
count down with the phone screen off), but a Cardio activity is real
physical exertion that keeps happening regardless of screen state, so its
countdown should keep counting through a backgrounded phone. It still
needs the same wake-lock recovery on return, so `cardioState` was added
to that one OR-chain only.

**Own state, deliberately**: `cardioState`/`cardioRaf` are Cardio's own
module-level globals, never `workoutState`/`session` - so a nested guest
exercise (which only ever touches `session`/`raf`) genuinely cannot
collide with a running Cardio sequence, the same isolation Workout's
`workoutState`/`workoutRaf` already relies on next to the visual engine's
own `session`/`raf`.

Tested end to end in `tests/cardio_test.py` (33 assertions): builder UI
(picker, duration/label/interval editing, saved presets, all persisted
across reload), the dual-task settings UI (toggle, pool multi-select,
timing, per-type fine-tune, persisted), a full run (multi-block
sequencing via skip, the interval phase label, an actual dual-task guest
window triggering and full-exercise takeover and returning correctly),
completion (done panel, history entry), and both abort paths (mid-cardio,
mid-guest-window) with the fix above confirmed.

