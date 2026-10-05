# Coach-code boxes for Movement, Cardio, NAT (2026-09-29)

Client's ask: *"Movement cardio und NAT will ich auch ein Code Eingabe
Fenster wie bei den anderen"* - a `.code-card` coach-code entry box on
these three home screens too, matching the one Visual/Atemtraining/Workout
already have. Cardio's home screen deliberately had none before this (an
earlier scope decision in the same overnight session that built Cardio,
now reversed at the client's explicit request); Movement and NAT never had
one either.

Before building, checked what each domain could actually reach through a
coach code, since "add the box" and "make it do something real" are two
different amounts of work depending on the domain's engine:

- **NAT** turned out to be the cheap case: only its "Periphere Wahrnehmung"
  sub-tab is a real `EXERCISES` entry (`periph-flash`) running through the
  shared visual engine (`session`/`runSession()`/the `program` object) -
  Remember/Blitz-Raster/Flash Speicher Test/MOT each have their own bespoke
  standalone engine (`rememberState`/`blitzState`/`flashState`/`motState`),
  same pattern as dozens of Test-Bereich exercises, and are **not**
  reachable from a coach code yet (no code-per-engine work was done for
  them - flagged below as a backlog item, not started). So NAT's code box
  reuses the exact same `bundle`/default programme type Visual already
  uses (a `{blocks:[{exercise:"periph-flash",duration:…}]}` config authored
  in `dashboard.html`'s JSON tab, `periph-flash` needing no per-block
  fields since its behaviour comes entirely from the client's own global
  `periph*` settings, not the block) - no new program type, no new
  screens, just its own `NAT_CODE_CTX` (`homeScreen: "natHome"`) pointed at
  `openProgramIntro()`.
- **Movement** has exactly one engine and exactly one live configuration
  (`movementPrefs`), so a coach-authored `movement-plan` just needs the
  same "overwrite the prefs, persist, start" the saved-preset loader
  (`renderMovementSaved`'s `onStart`) already does - no per-block
  orchestration to build.
- **Cardio** already treats a whole sequence as one pre-built `items` array
  that `cardioTick()`/`startStandaloneCardio()` auto-advances through on
  its own (unlike Workout, which steps one block at a time via
  `runWorkoutBlock`/`workoutPlan.blockIndex`) - so a coach-authored
  `cardio-plan` is just a different *source* for that same `items` array,
  not a second playback engine. The client's own dual-task addon settings
  (`cardioAddonPrefs`) keep applying automatically to a coach-run sequence
  exactly like a self-built one, since they're global, not tied to which
  `items` array is currently running - deliberately no coach-side addon
  config field.

**Generalizing the shared Visual/NAT pipeline for ctx-aware routing**: the
existing `VISUAL_CODE_CTX`/`BREATH_CODE_CTX`/`WORKOUT_CODE_CTX` objects
already threaded a `homeScreen` through for the *not-found* fallback and
for `combo-program` routing, but the successful path
(`openBundleOverview()`/`renderProgramIntro()`, the default `bundle`/
plain-programme types) silently hardcoded `"home"` everywhere - fine while
only Visual Training used it, a real bug once NAT started reusing the same
pipeline (finishing or backing out of a NAT-origin code would have dumped
the client on Visual Training's home screen instead of NAT's). Fixed by
threading `ctx` through `openBundleOverview(bundleDef, code, ctx)` and
`renderProgramIntro(def, code, key, ctx)`, and two new module vars -
`bundleCtx` (which ctx opened the current bundle overview) and
`programIntroHomeScreen` (which ctx opened the current programme intro) -
read by `bundleBackToHome`/`programBackToHome`/`programDoneBackBtn`
instead of a bare `"home"`. Deliberately plain module vars rather than a
field on `program`/`originBundle`: the intro screen's own back button can
be pressed *before* `program` is ever set (that only happens once a
chapter is actually tapped to start), so anything read off `program` would
be stale or null while just viewing the intro.

**Movement/Cardio programme types**, each mirroring Workout's existing
`workout-plan`/`workout-bundle` shape and lifecycle (own intro/bundle
screens, own `…OriginBundle` var, abort-to-intro instead of abort-to-
builder, done-back routes to the bundle overview or home depending on
origin, history entries tagged `movement-plan`/`cardio-plan` with a
`progKey` instead of the generic `movement`/`cardio` kind):
- `movement-plan`: `{name, description, movements:[...ids], bpm,
  durationMin, preview, mirror, showLabel}` - `renderMovementProgramIntro`
  applies it onto `movementPrefs` (through `movementAllowedIds()`, which
  filters the coach's movement list through the client's *current* limb
  restriction the same way the manual picker already does, falling back to
  the full list if that would leave fewer than `MIN_MOVEMENTS`) then calls
  the existing `startMovementSession()` unchanged.
- `cardio-plan`: `{name, description, items:[{activity, durationS, label,
  interval}]}` - `renderCardioProgramIntro` shows a non-interactive
  chapter list (the sequence is linear, no per-item entry point) and its
  Start button hands `def.items` straight to the existing
  `startStandaloneCardio()`.
- Both got `-bundle` counterparts (`openMovementBundleOverview`/
  `openCardioBundleOverview`) identical in shape to
  `openWorkoutBundleOverview`.
- `free-template` (2026-10-05, no bundle form): `{name, trainings:[…]}` -
  not a programme to run but read-only "Eigenes Training" templates that
  `importTrainerTemplates` stores and shows in `#freeHome` under "Von
  deinem Trainer"; same code again = update. Details: notes/25.

`dashboard.html`'s JSON-tab hint text was updated to document all of this
(the new types' exact shapes, valid `movements`/`activity` values, and
which NAT sub-exercise the code box can currently reach) - it previously
didn't even mention `workout-plan`/`workout-bundle`, which already existed.

**Not done, explicit backlog** (same "flag it, don't silently skip it"
convention as the colour-vision-deficiency audit below): Remember,
Blitz-Raster, Flash Speicher Test, MOT (all of NAT except Periphere
Wahrnehmung), and every Test-Bereich exercise each have their own bespoke
engine/state object and are not reachable from a coach code - giving any
of them one would mean a genuinely new programme type per engine, not a
small extension of this work.

Tested in `tests/code_boxes_test.py`: presence of all three code boxes,
wrong-code error path staying on the *own* home screen (not Visual's) for
all three, a full movement-plan run (solo and bundle: intro, start,
mid-run abort back to its own intro, back-to-home/back-to-bundle
routing), a full cardio-plan run to completion (solo and bundle: intro,
start, mid-run abort, finish, done-back routing), and the NAT default-type
path (intro, ctx-aware back-before-starting, mid-exercise abort via the
shared player bar, ctx-aware back-after-that) - plus a regression check
that Visual Training's own code box still lands back on Visual home after
all this ctx-threading. Uses Playwright route interception on the
`CODE_API` URL to serve fake defs for each new type, since none of this
can be exercised via `dashboard.html` without a live Worker deploy.

