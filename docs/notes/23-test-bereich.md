# Test-Bereich (autonomous, ongoing)

**If you were woken by the "FWMC Test-Bereich Auto-Build" Routine, this
section is your instructions — read all of it before touching anything.**

The user explicitly asked (2026-09-25) for a standing, self-directed
process: research and build small, purposeful visual/cognitive/perceptual
training exercises on an ongoing basis, without being re-prompted each
time, the same way this app itself grew one exercise at a time (Visual
Training → Atemtraining → Movement → Workout → NAT, each added when it
made sense, not all planned upfront). A recurring Routine
(`trig_01PhmeZCsdzf9Xewn4tb3RcX`, cron `47 7,13,19 * * *` UTC, fires a
**fresh session** each time — no memory of previous firings, everything
that matters must live in this file) drives this: roughly three times a
day, spend about one focused hour researching and building ONE new
exercise, entirely on your own judgment.

**Hard rule, repeated because it is the one that must never slip**: only
ever add to the "Test" top-level section (`#testHome`, its own nav tab
next to NAT, and each exercise's own dedicated ready/player screens under
it — same pattern as NAT's Remember/Blitz/Flash/MOT, NOT the shared VT
arrow-engine's `data-exercise` dispatch). Never modify, refactor, or
change the behaviour of anything in Visual Training, Atemtraining,
Movement, Workout, or NAT. This is the client's own production coaching
tool; the Test section exists precisely so experiments can't put that at
risk. Reading those other sections for reference/reuse is fine and
encouraged (e.g. reusing `buildStimColorPicker`, `mixHex`,
`wireBgIntensityControl`, `pickRandomSubset`) — editing them is not.

**The "Test" tab is hidden by default as of 2026-10-01 (client security/
product review) — this is intentional, do not "fix" it.** Every section's
nav bar still has the `<button class="section-tab" data-section="test">`
markup (untouched, still there for this Routine's own build/test work to
target), but `applyTestTabVisibility()` in app.js (near `CODE_API`) hides
it via `.hidden` unless `localStorage['fwmc-test-unlocked']` is set.
Typing the word `testbereich-ein` (older word `testbereich-frei` still
accepted) into ANY section's existing training-
code box sets that flag (through `openProgramIntro()`'s own intercept,
before the real code lookup) and reveals the tab permanently on that
browser (typing `testbereich-aus` the same way hides it again and
removes the flag) - see "Client security/product review (2026-10-01)" further below
for the full rationale. **This does not change anything about how you
build here**: keep developing exercises exactly as before, the scaffold
and every existing Test-Bereich test still works because `tests/*_test.py`
files for this section pre-seed that same localStorage flag via
`page.add_init_script(...)` before navigating - add that same one line to
any new Test exercise's test file (copy it from `tests/gng_test.py` or any
other existing one in this section). The tab being hidden from ordinary
visitors is a reason to keep building here, not a sign something broke.

**Promoting an exercise OUT of Test** (client's own call, done in a
regular session, never by the autonomous Routine itself): once the client
says a Test exercise is good enough, it moves to its natural home (NAT for
anything neuroathletic-perception-shaped, Visual Training for anything
arrow/colour/reaction-shaped) - relocate its screens/state/wiring from the
Test pattern to that section's own existing pattern (its own nav/tab
placement, not `#testHome`), remove it from the Test roster below, and -
per the standing convention in the Cardio-Zusatzaufgabe section above -
give it full Cardio-"+ Zusatzaufgabe" parity in the same pass, exactly as
if it had been built there from scratch. Until that happens, a Test
exercise stays Test-only: it is deliberately NOT in `CARDIO_GUEST_TYPES`
and NOT in `COMBO_DOMAIN_ORDER`'s domains, since this section's exercises
are plain fixed-trial-count paradigms (see "Offene Fragen" at the end of
this file) whose scoring would be meaningless if cut short mid-run by
Cardio's own duration/time-window - and because the Test section was built
specifically to be low-risk/disposable, not wired into every other feature
by default.
`wireBgIntensityControl`, `pickRandomSubset`) — editing them is not.

**Scaffold already in place** (built 2026-09-25, do not rebuild):
`#testHome` screen with the standard 6-tab `section-switch` nav (now
including a "Test" tab on every other section's nav bar too), a hero
("Neue Ideen, direkt ausprobiert."), and an empty `#testPanel` with
`#testEmptyHint` ("Noch keine Übung hier …") shown until the first
exercise is added. JS wiring: `sec === "test"` in the section-switcher
ternary, `"testHome"` in `SCREENS`, `els.testHome`/`testPanel`/
`testEmptyHint`, and `currentHomeScreen()`'s ternary. Test:
`tests/test_section_test.py` (scaffold/navigation only — each actual
exercise gets its OWN test file, same convention as NAT).

**Style conventions for Test exercises** — reuse what fits, skip what
doesn't:
- Reuse: single source `_body.html`+`app.js`+`styles.css`+`build.sh`;
  dark-mode-safe fixed hex colours (never `var(--...)`) for anything
  player/stage-scoped; Bei-Fehler `reset2`/`backOne`/`stay`; pause
  cancels/replays timers with live background adjustment;
  "Beenden"-doubles-as-Finish; a done-panel with rating + `addHistory()`.
- Optional, explicitly per the client's own instruction — include only
  when it's basically free (you're already touching the relevant helper
  for another reason), skip otherwise so research+build actually fits in
  an hour: background colour/intensity/transfer+presets, a Trainingsmodus
  variant, multiple progression modes, a configurable object/stimulus
  colour picker. A first version of an exercise can be simpler than
  MOT/Flash ended up being — those grew over several client-directed
  rounds, not in one sitting.
- Ground new exercises in a real paradigm when one exists (name it, cite
  what a quick web search found, same as MOT-Fähigkeit's NeuroTracker/
  Pylyshyn grounding) rather than inventing parameters from scratch.
- Testing/deploy checklist is NOT optional and is identical to every other
  feature in this app: `node --check app.js` → `sh build.sh` → new
  `tests/<name>_test.py` → full regression suite (all `tests/*_test.py` +
  `tests/v25_pause_check.py`) clean, no concurrent edits while it runs →
  update this section (roster + Offene Fragen below) → commit (with the
  attribution footer your own system prompt specifies) → push to `origin
  main` → read then republish the Claude Artifact
  (`https://claude.ai/artifact/MXieTDSa8y6W4BeRMfAw8K`) with the changed
  files. If the suite doesn't come back clean, do not push — fix it, or
  revert just the files you touched and note the blocker below instead.
  **The `git push` is the step that actually saves your work - the
  Artifact is only a preview mirror, republished from whatever this
  container has on disk right now.** The container is reclaimed once your
  turn ends; anything not pushed to `origin main` by then is gone. If
  you're running short on time and can only do one of the two, push to
  git and skip the Artifact republish (the client's own session can catch
  that up) - never the other way round. Confirm the push actually landed
  with `git log --oneline -3` (or `git status` showing a clean tree
  up to date with `origin/main`) before ending your turn; a firing that
  published to the Artifact but didn't push (this happened once, 2026-09-25 -
  the Go/No-Go exercise below was built entirely correctly but the session
  ended before `git push` ran, and had to be recovered by hand from the
  Artifact's published files in the next session) has not actually saved
  anything.

### Roster (what's been added under Test so far)

- **Go/No-Go Reaktionstest** (first autonomous entry, 2026-09-25): classic
  inhibitory-control paradigm - a run of single stimuli, most demanding a
  fast tap ("Go", green circle), a minority (`GNG_NOGO_RATIO = 0.2`, ~20% of
  `GNG_TRIAL_COUNT = 24` trials) demanding the tap be withheld ("No-Go",
  red) - grounded in the sport/exercise inhibitory-control literature
  (cited in-code: a 2023 meta-analysis on inhibitory control in sport
  performance, and PMC8048576/PMC12650625-style go/no-go ISI designs); the
  ~20% minority split (not 50/50) is deliberate so a "just respond"
  impulse actually builds up and there's something real to inhibit -
  50/50 would just be simple choice reaction time. Trials are shuffled but
  never place two No-Go trials back to back (`buildGngTrials()`), so the
  client can't just switch "respond" off for a stretch. Reports accuracy %
  (hits + correct inhibitions) and average reaction time on Go trials
  instead of a level - this task has no natural "level", it's a fixed-length
  test, so `GNG_BEST_KEY` tracks best accuracy % per difficulty rather than
  best level reached. `gngPrefs.difficulty` (leicht/mittel/schwer) sets
  `stimMs`/`isiMin`/`isiMax`; no Bei-Fehler, no background customisation,
  no Trainingsmodus - all correctly skipped per the "optional, skip what
  doesn't fit in an hour" guidance above, since none of them make sense for
  a fixed-trial accuracy test. Pause/resume uses the same
  scheduleXTimer-remaining-delay trick as Blitz/Remember. Reuses
  `.remember-hint` for the on-stage hint text and the standard done-panel/
  rating/`addHistory()`/`wireFullscreen()` conventions; new CSS is just
  `.gng-stage`/`.gng-stimulus` (a plain circle, green/red states, fixed
  hex colours, no `var(--...)`). Test: `tests/gng_test.py`.
- **Positions-Gedächtnis (N-Back)** (second autonomous entry, 2026-09-25,
  same firing that also recovered the Go/No-Go push - see the note above):
  classic spatial N-back working-memory task - one cell in a 3×3 grid
  lights up per trial, the client taps "Übereinstimmung!" whenever the
  current position matches the one shown N trials back. Explicitly
  grounded in Jaeggi et al. 2008's adaptive dual/single N-back protocol
  (cited in-code): block length `NBACK_BLOCK_BASE_TRIALS + N` (20 + N),
  `NBACK_MATCH_PROB = 0.3` (the standard ~20-35% target-trial rate), and
  the adaptive rule after each block - ≤2 errors → N goes up, >5 → N goes
  down, otherwise unchanged (`testNbackFinishBlock()`). No fixed "level" a
  client sets themselves like Remember/Blitz/Flash/MOT; the exercise picks
  its own difficulty via this adaptive rule, so the done-panel/best-hint
  report "höchstes erreichtes N" instead. Each trial is stimulus
  (`NBACK_STIMULUS_MS` = 500ms) + ISI (`NBACK_ISI_MS` = 2500ms); the
  correct/wrong flash on the match button is DEFERRED to the end of that
  window (`testNbackEndTrial()`), not shown immediately on tap - a trial's
  correctness can't be judged until its full response window (which spans
  both the "show" and "gap" phases) actually closes. Reuses
  `.remember-hint`, pause/resume-with-timer-remaining, `wireFullscreen()`,
  done-panel/rating/`addHistory()` conventions; new CSS is
  `.nback-stage`/`.nback-grid`/`.nback-cell`/`.nback-match-btn` (fixed hex
  colours throughout, no `var(--...)`). Built independently alongside
  Go/No-Go with no collision or duplication - the firing correctly read
  the roster above before picking this. Test: `tests/nback_test.py`.
- **Verbindungstest (Trail Making)** (third autonomous entry, 2026-09-26):
  grounded in the Trail Making Test (Reitan 1958, part of the
  Halstead-Reitan Neuropsychological Battery) - scattered circles tapped in
  ascending order, Teil A pure numbers (1,2,3…), Teil B alternating
  number/letter (1,A,2,B…) for an added set-shifting/cognitive-flexibility
  demand. Also cited in-code as a standard component of sports-concussion
  baseline/return-to-play batteries - a direct fit for this app's context.
  Scored by real completion time + error count (`TRAIL_BEST_KEY`, lower
  time wins, only ever recorded for a fully finished run) - no artificial
  "level" and no Bei-Fehler reset2/backOne/stay, since a wrong tap here is
  simply counted while the client keeps aiming at the same next target
  (`trailTapMarker()`), exactly like an examiner redirecting a participant
  without stopping the clock on the real paper test. Difficulty is just
  circle count (15/20/25 - 25 matches the original test's own sheet), not
  speed or anything else. Fresh random scatter layout every run
  (anti-overlap rejection-sampling copy-adapted from Remember's own
  placement helper, per this file's "copy-adapt when the engine differs"
  convention) rather than the paper test's one fixed printed sheet, so
  repeat play trains genuine visual search instead of layout memorisation.
  No background colour/Zusatzaufgabe/Trainingsmodus - all correctly
  skipped, none would add anything to a task whose stimulus is the
  scattered layout itself. Test: `tests/trail_test.py`.
- **Ablenkungstest (Flanker)** (fourth autonomous entry, 2026-09-27):
  grounded in the Eriksen flanker task (Eriksen & Eriksen, 1974) - a
  central target arrow flanked by four distractor arrows that either point
  the same way ("kongruent") or the opposite way ("inkongruent"); the
  client responds only to the CENTRE arrow's direction (tapping one of two
  big on-screen `←`/`→` buttons) as fast as possible, ignoring the
  flankers. Also researched and cited in-code as an established measure of
  selective attention/interference control in sport-science research (e.g.
  a collegiate-football variant, PMC5811505, where players showed smaller
  interference costs than non-player controls) - a good fit for FWMC's
  "visuelle Entscheidungsgeschwindigkeit" focus. Deliberately distinct from
  every existing Test/NAT mechanic: Go/No-Go tests withholding a response
  to a single stimulus (response inhibition), Flanker always demands the
  SAME central response every trial and instead tests filtering out
  simultaneous conflicting visual information alongside it (selective
  attention/interference control) - a complementary, not overlapping,
  executive-function facet; the existing VT "4/8 Pfeile" exercises are
  plain direction-cue reaction tasks with one unambiguous arrow, not an
  interference paradigm, so no overlap there either. Fixed 32-trial run
  (`FLANKER_TRIAL_COUNT`, balanced 16 kongruent/16 inkongruent and 16
  links/16 rechts, shuffled with a same-direction-max-3-in-a-row guard so a
  "just keep pressing the same button" motor strategy can't pass
  undetected), no artificial "level"/Bei-Fehler - reports accuracy% plus
  average correct RT split by kongruent/inkongruent, and their difference
  as the actual "Interferenz-Kosten" (the classic flanker effect, the real
  outcome measure this paradigm exists to surface), tracking best accuracy%
  per `flankerPrefs.difficulty` (leicht/mittel/schwer, controlling the
  response time window + ISI, same shape as `GNG_DIFFICULTIES`) via
  `FLANKER_BEST_KEY` - same "fixed-trial accuracy test" shape as Go/No-Go,
  for the same reason (no natural level to progress). No background
  colour/Zusatzaufgabe/Trainingsmodus - all correctly skipped per the
  "optional, skip what doesn't fit in an hour" guidance, none would add
  anything to a task whose whole point is a fixed black-on-white arrow row.
  Pause/resume uses the same scheduleXTimer-remaining-delay trick as
  Go/No-Go/Blitz/Remember. New CSS is `.flanker-stage`/`.flanker-row`/
  `.flanker-arrow`/`.flanker-response-row`/`.flanker-response-btn` (fixed
  hex colours throughout, no `var(--...)`); the target arrow gets a plain
  underline marker (`.flanker-target`) so a first-time client can find "the
  middle one" at a glance - this doesn't affect the paradigm's validity
  since the target position is fixed and known every trial regardless.
  Test: `tests/flanker_test.py`.
- **Blickfeld-Test (UFOV)** (fifth autonomous entry, 2026-09-27): grounded
  in the Useful Field of View test (Ball & Owsley, 1987/1993) - a measure
  of visual processing speed AND divided attention, i.e. how much
  information can be taken in from a cluttered display in one brief glance
  without moving the eyes. The real protocol runs three subtests of rising
  demand (central discrimination only; central+peripheral divided
  attention; the same plus distractors) with a 3-down/1-up staircase over
  a 16.67-500ms exposure range (16.67ms = one 60Hz frame) - this exercise
  builds a single, simplified subtest combining the divided-attention and
  selective-attention ideas (a central shape AND a peripheral target among
  distractors, every trial, same staircase shape), not a clinical replica
  - hence "UFOV-inspired" in the client-facing copy rather than claiming to
  be the validated instrument. Also researched as linked to athletic
  expertise in more recent work (e.g. table-tennis players and action-
  video-game players showing UFOV divided/selective-attention advantages
  over untrained controls), a good fit for FWMC's peripheral-vision focus.
  Each trial: a circle or square flashes at fixation while, simultaneously,
  one of 8 positions around a compass-style ring shows a diamond target
  among plain-dot distractors; both are then backward-masked (a repeating-
  stripe pattern, standard in the real protocol to wipe out any iconic-
  memory afterimage) before the client answers first the central shape,
  then the peripheral position (sequential taps rather than one combined
  gesture - a UI simplification, not a change to what's actually being
  judged). The exposure duration is the one adaptive variable: three
  consecutive fully-correct trials shorten it, any error lengthens it
  (`UFOV_STAIRCASE_HITS_NEEDED = 3`, matching Ball & Owsley's own staircase
  design) - starts easy (`UFOV_START_MS = 500`, the ceiling) and steps by
  `UFOV_STEP_MS = 33` down to a `UFOV_MIN_MS = 33` floor; the real
  protocol's own 16.67ms-frame steps were coarsened to 33ms (2 frames)
  since `setTimeout`-driven browser timing can't reliably resolve single-
  frame differences the way calibrated lab hardware can (see Offene Fragen
  below). No client-set "level"/Bei-Fehler - like N-Back, the exercise
  itself is the adaptive difficulty; the done-panel reports the average
  exposure duration of the last 10 trials as the "Schwelle" (threshold, ms
  - LOWER is better here, the opposite direction from every accuracy%-based
  best score, so `saveUfovBest`/`UFOV_BEST_KEY` do their own `<` comparison
  rather than reusing the `>` pattern) plus overall accuracy%. `ufovPrefs.
  length` (kurz/mittel/lang = 20/30/40 trials) is the only client-facing
  setting - no background colour/Zusatzaufgabe/Trainingsmodus, all
  correctly skipped per the "optional, skip what doesn't fit in an hour"
  guidance (nothing to configure beyond the built-in adaptive difficulty).
  Genuinely distinct from every existing Test/NAT mechanic: Periphere
  Wahrnehmung trains detecting/naming a single peripheral flash with no
  central task, no masking, and no adaptive threshold - this is a DIVIDED-
  attention dual task (a central AND a peripheral judgement every trial)
  reporting a processing-speed threshold, not a client-configurable
  detection game. Pause/resume uses the same scheduleXTimer-remaining-
  delay trick as Flanker/Go-No-Go/Blitz/Remember (a no-op during the two
  untimed response phases, which just wait on a tap - pause still blocks
  input via a `paused` flag and the overlay). A wrong answer, on either
  sub-task, reveals the true answer alongside the wrong one (same "show
  what it actually was" convention as MOT's wrong-tap reveal). New CSS is
  `.ufov-*` (fixed hex colours throughout, no `var(--...)`); the 8 ring
  positions/response buttons share one set of `.ufov-p-n/-ne/-e/-se/-s/-sw/
  -w/-nw` placement classes between the stage and the answer screen so the
  spatial layout stays visually consistent between "what you saw" and
  "where you tap". Test: `tests/ufov_test.py` (staircase feedback classes,
  the true-answer reveal on a miss, pause/resume, Beenden-doubles-as-
  finish, length persistence - the exact numeric staircase progression
  itself isn't unit-tested, since no internal hook exposes it; verified by
  reading the logic plus the behavioural checks above, the same approach
  already used for the addon colour/position logic).
- **Hinweisreiz-Test (Posner-Cueing)** (sixth autonomous entry, 2026-09-27):
  grounded in the Posner cueing task (Posner, 1980) - one of two side boxes
  briefly lights up as a spatial cue, then a target dot appears in the cued
  box on 80% of trials ("valid", the classic validity ratio Posner himself
  used) or the OTHER box on the remaining 20% ("invalid"); the client taps
  the box where the dot actually appears, not the one that merely cued.
  Reports accuracy% plus average valid/invalid reaction time and their
  difference as the "Umlenkungs-Kosten" (the classic cueing/validity effect
  - the RT cost of disengaging attention from an incorrectly cued location
  and re-orienting to the real target), tracking best accuracy% per
  `posnerPrefs.difficulty` (leicht/mittel/schwer, controlling cue duration,
  cue-target SOA and response window - shorter SOA = harder, same shape as
  `FLANKER_DIFFICULTIES`/`GNG_DIFFICULTIES`) via `POSNER_BEST_KEY`. Also
  researched as sport-relevant: a 2025 multilevel Bayesian meta-analysis
  across 72 studies/885 athletes found cueing/benefit effects scale with cue
  validity, and athletes in several sports (boxers, volleyball players, ...)
  show more efficient attentional orienting (smaller valid/invalid RT gaps)
  than non-athletes - a direct fit for FWMC's "visuelle
  Entscheidungsgeschwindigkeit"/Aufmerksamkeit focus. Genuinely distinct
  from every existing Test/NAT mechanic: unlike Go/No-Go (withholding a
  response), Flanker (filtering simultaneous conflicting stimuli) and UFOV
  (a divided-attention glance under adaptive time pressure), this is the
  only one that isolates the cost of VOLUNTARILY SHIFTING spatial attention
  between two known locations. Fixed 40-trial run (`POSNER_TRIAL_COUNT`, 32
  valid/8 invalid, balanced left/right, shuffled with the same same-target-
  side-max-3-in-a-row guard `buildFlankerTrials()` already uses, so a "just
  tap the same side" motor strategy can't pass undetected). No Bei-Fehler/
  background colour/Zusatzaufgabe/Trainingsmodus - all correctly skipped
  per the "optional, skip what doesn't fit in an hour" guidance, same
  reasoning as Flanker/Go-No-Go (a fixed-trial accuracy/RT test, nothing to
  configure beyond difficulty). Pause/resume uses the same scheduleXTimer-
  remaining-delay trick as Flanker/Go-No-Go/Blitz/Remember. New CSS is
  `.posner-*` (fixed hex colours throughout, no `var(--...)`); the two
  response boxes double as both the cue display and the tap targets,
  reusing the Flanker/Go-No-Go green=correct/red=wrong feedback convention.
  Test: `tests/posner_test.py`.
- **Rotationstest (Mentale Rotation)** (seventh autonomous entry,
  2026-09-27): grounded in the classic mental-rotation/character-rotation
  chronometric paradigm (Cooper & Shepard, 1973) - a letter or digit
  (`ROTATION_CHARS`, asymmetric ones only so mirrored really looks
  different from normal) is shown rotated to one of 8 orientations
  (`ROTATION_ANGLES`, 0-315 in 45 degree steps) around the full circle,
  either in its normal form or mirror-reversed (mirrored FIRST, then
  rotated, matching the real-world order these transforms are physically
  applied and not commutative with each other except at 0/180); the client
  judges "Normal" or "Gespiegelt" as fast as possible. Reports accuracy%
  plus average RT for characters near upright (<=90 degrees disparity) vs.
  far from upright (>90) and their difference as "Rotations-Kosten" - the
  actual angular-disparity effect (RT rises with rotation distance from
  upright) this paradigm exists to surface, tracking best accuracy% per
  `rotationPrefs.difficulty` (leicht/mittel/schwer, controlling the
  response window and ISI, same shape as `FLANKER_DIFFICULTIES`/
  `POSNER_DIFFICULTIES`) via `ROTATION_BEST_KEY`. Also researched as
  sport-relevant: a 2023 Exp Brain Res VR study and a 2024/2025
  behavioural+fNIRS study both link athletes in high-spatial-demand/axial-
  rotation sports to better mental-rotation performance than non-athletes
  ("embodied cognition" from years of training) - a fit for FWMC's
  "bewegungsnahes mentales Training" angle specifically, not just a desk
  task. Genuinely distinct from every existing Test/NAT mechanic: none of
  Go/No-Go (inhibition), Flanker (interference filtering), UFOV (divided
  attention under time pressure) or Posner-Cueing (voluntary spatial-
  attention shift) asks the client to judge a SPATIAL TRANSFORMATION of a
  single stimulus. Fixed 32-trial run (`ROTATION_TRIAL_COUNT` = 8 angles x
  normal/mirrored x 2 repeats, every orientation sampled equally in both
  forms rather than an artificial near/far split, since the disparity
  effect is continuous not binary), shuffled with the same same-answer-
  max-3-in-a-row guard the other Test exercises use. No Bei-Fehler/
  background colour/Zusatzaufgabe/Trainingsmodus - correctly skipped, same
  reasoning as Flanker/Posner (a fixed-trial accuracy/RT test). Pause/
  resume uses the same scheduleXTimer-remaining-delay trick as Flanker/
  Posner/Go-No-Go. New CSS is `.rotation-*` (fixed hex colours throughout,
  no `var(--...)`); the character itself is a plain styled `<span>` rotated
  via CSS `transform`, not a canvas/SVG element. Test: `tests/rotation_test.py`.
  Note: this run's session stalled for a long stretch after finishing the
  implementation (files stopped changing well before the environment
  itself appears to have restarted) and never got to testing/committing on
  its own - recovered and finished (test written, full suite run, this
  entry added, committed+pushed) directly in the parent session rather
  than by a fresh autonomous firing.
- **Merkspanne-Test (Change Detection)** (eighth autonomous entry,
  2026-09-27): grounded in the classic visual working-memory change-
  detection paradigm (Phillips, 1974; popularised by Luck & Vogel, 1997,
  Nature 390:279-281) - a sample array of N scattered, non-overlapping
  coloured squares (N=4/6/8 for leicht/mittel/schwer) briefly appears,
  then after a blank retention interval reappears at the same positions,
  either unchanged or with exactly one square's colour changed; the client
  judges "Gleich" or "Verändert" for the WHOLE display at once. Scored
  with Pashler's K = N x (hitRate - falseAlarmRate) / (1 - falseAlarmRate)
  - the correct capacity-correction formula for this whole-display method
  (Cowan's simpler K applies only to the single-item-probe variant, which
  this is not), tracking best K per difficulty. Also researched as sport-
  relevant: a 2026 Frontiers study links visuospatial working-memory
  capacity to faster/more efficient tactical decisions in soccer players -
  flagged honestly alongside a PLOS ONE finding that evidence for athlete/
  non-athlete differences on this specific RT-free paradigm is mixed
  (reported both ways in the roster rather than only the flattering one).
  Genuinely distinct from every existing Test/NAT memory mechanic: N-Back
  is sequential match-back, Remember/Blitz-Raster tests recalling WHICH
  positions were shown, Flash is digit-sequence recall - this is the only
  one holding a whole array and probing a single FEATURE via a global
  same/different judgment. Anti-overlap scatter placement adapted from
  Trail Making's own. No Bei-Fehler/background colour/Zusatzaufgabe/
  Trainingsmodus - correctly skipped (a fixed-trial capacity test, nothing
  to configure beyond difficulty). New CSS is `.merk-*` (fixed hex colours
  throughout, no `var(--...)`). Test: `tests/merk_test.py`. Note: this
  run's own session was also forced to hand back before finishing (see
  the Rotationstest note above for the pattern) - it had already reported
  its full regression-suite run as still in progress when it handed back;
  that run was left going and finished cleanly (51/51 green) rather than
  being restarted, then this entry was added and the result committed+
  pushed, directly in the parent session.
- **Farbkonflikt-Test (Simon-Aufgabe)** (ninth autonomous entry,
  2026-09-27): grounded in the Simon task (Simon & Rudell, 1967; Simon,
  1969) - a coloured dot (blue or orange) appears in a left or right slot;
  the client always taps the SAME fixed-position button matching the dot's
  COLOUR (Blau = links, Orange = rechts, this mapping never changes during
  a run), entirely ignoring which slot the dot appeared in. When the dot's
  on-screen side happens to match its colour's button side that's
  "congruent" (fast, accurate); when it conflicts that's "incongruent"
  (slower, more error-prone) - the classic Simon effect, the automatic,
  uncued activation of a spatial response tendency by a task-irrelevant
  stimulus location. Also researched as sport-relevant: open-skill-sport
  athletes (e.g. futsal players) show reduced Simon-effect interference
  versus non-athletes, and action-video-game training has been shown to
  shrink the Simon effect too - both point to this specific interference-
  control facet being trainable, a fit for FWMC's "visuelle
  Entscheidungsgeschwindigkeit" focus. Genuinely distinct from every
  existing Test/NAT mechanic: Flanker's conflict comes from simultaneous
  DISTRACTOR stimuli surrounding an unambiguous central target; Posner-
  Cueing tests voluntarily/endogenously shifting attention between two
  known locations after an explicit cue; Simon's conflict instead comes
  from the single target stimulus's own task-irrelevant location
  automatically priming a response side, with no cue, distractor, or shift
  instruction involved at all - a third, complementary facet of
  interference control. Fixed 40-trial run (`SIMON_TRIAL_COUNT`, a full
  balanced 2x2 design - colour x side, 20 congruent/20 incongruent, 20
  blue/20 orange, 20 left/20 right), shuffled with the same same-correct-
  side-max-3-in-a-row guard the other Test exercises use. Reports
  accuracy% plus average congruent/incongruent RT and their difference as
  the "Simon-Effekt" (ms) - the actual outcome measure this paradigm
  exists to surface - tracking best accuracy% per `simonPrefs.difficulty`
  (leicht/mittel/schwer, reusing FLANKER_DIFFICULTIES' exact response-
  window/ISI numbers, a single-stimulus immediate-response task of
  comparable load) via `SIMON_BEST_KEY`. No Bei-Fehler/background colour/
  Zusatzaufgabe/Trainingsmodus - all correctly skipped per the "optional,
  skip what doesn't fit in an hour" guidance, same reasoning as Flanker/
  Posner/Rotationstest (a fixed-trial accuracy/RT test, nothing to
  configure beyond difficulty). Pause/resume uses the same scheduleXTimer-
  remaining-delay trick as Flanker/Posner/Rotation. New CSS is `.simon-*`
  (fixed hex colours throughout, no `var(--...)`); unlike Flanker/Posner's
  tap feedback (a solid background swap), correct/wrong here is a colour-
  neutral ring (`box-shadow`) on top of the button's own permanent blue/
  orange fill, deliberately, so feedback semantics never get confused with
  the stimulus/response colour coding the whole task is built around. The
  two response buttons show their colour name as visible text ("Blau"/
  "Orange") rather than a silent key mapping the client must memorise
  beforehand (the classic lab version uses unlabelled keys) - a deliberate,
  documented touchscreen simplification, not a compromise worth flagging:
  the actual measured effect (does an irrelevant stimulus location speed or
  slow the colour-based response) is unaffected by whether the mapping is
  labelled or memorised. Test: `tests/simon_test.py`.
- **Suchtest (Visuelle Suche)** (tenth autonomous entry, 2026-09-27):
  grounded in the classic visual-search paradigm and Treisman & Gelade's
  Feature Integration Theory (1980) - a single target hides among several
  distractors. "Merkmalssuche" (feature search): every distractor is a
  plain grey circle, the target is the only RED circle - one salient
  feature makes it "pop out" instantly, near-independent of how many
  distractors are on screen (parallel processing). "Verbindungssuche"
  (conjunction search): the target is a red SQUARE among red circles
  (share colour) and grey squares (share shape) - no single feature is
  unique, forcing a slower, roughly serial item-by-item scan whose
  reaction time rises with set size. Both conditions run across three set
  sizes (6/12/18 items, `SEARCH_SET_SIZES`) in one balanced run
  (`searchPrefs.length` kurz/mittel/lang = 12/24/36 trials, reusing the
  UFOV-style "length" setting shape since there's no natural difficulty
  dial otherwise), and the done-panel reports the actual outcome measure
  this paradigm exists to surface: the RT-by-set-size SLOPE per condition
  (ms per added object, `searchSlope()` - a two-point slope between the
  smallest/largest set size's average correct RT), not just an overall
  average - a genuinely new kind of reported result on this Test tab
  (every other exercise reports a flat average or a single interference
  cost, never a slope). Treisman & Gelade's own colour-conjunction data
  implies a slope on the order of ~25-30ms per added item (cited in later
  reanalyses as "28.7 ms"), against feature search's near-flat slope - the
  actual parallel-vs-serial-search contrast this exercise is built to make
  visible. Also researched as sport-relevant: a 2026 Frontiers systematic
  review/meta-analysis found expert athletes show more EFFICIENT visual
  search than novices (fewer but more informative fixations, better
  foveal/peripheral coordination) - a direct fit for FWMC's "visuelle
  Entscheidungsgeschwindigkeit"/peripheral-vision focus. Genuinely
  distinct from every existing Test/NAT mechanic: MOT tracks objects that
  stay identical to each other throughout a continuous movement phase;
  Trail Making scans a scattered layout in a KNOWN ascending order; UFOV
  is a brief masked glance with no active scanning at all - this is the
  only exercise whose display stays up and static while the client
  actively searches it, the textbook visual-search setup. Unlike
  Simon/Flanker/Posner's FIXED response window (a trial always runs its
  full duration before advancing, whether tapped early or not), this task
  is genuinely SELF-PACED - a trial ends the instant something is tapped,
  only an 8s safety-net timeout (`SEARCH_TIMEOUT_MS`) advances an
  unanswered trial - so `scheduleSearchTimer` always clears any
  still-pending timer before scheduling the next one (an early-tap
  transition would otherwise leave a stale timeout to fire later on top
  of an already-advanced trial - `scheduleSimonTimer` doesn't need this
  since Simon's own fixed-cadence design never transitions early). A
  short pre-array text cue ("Ziel: Roter Kreis"/"Ziel: Rotes Quadrat",
  `SEARCH_CUE_MS` + a brief ISI) names the target before the array
  appears, so reaction time is measured from array onset, not from
  reading the instruction - the target identity is otherwise constant per
  condition (feature search always targets a red circle, conjunction
  search always a red square), so the cue is a near-zero-cost categorical
  label, not a new judgement each trial. Anti-overlap scatter placement
  (`searchRandomPixelPosition`/`searchStageBounds`) copy-adapted from
  Trail Making's own, sized for up to 18 simultaneous items
  (`SEARCH_ITEM_PX = 34`). No Bei-Fehler/background colour/Zusatzaufgabe/
  Trainingsmodus - correctly skipped per the "optional, skip what doesn't
  fit in an hour" guidance (a fixed-trial RT/slope measure, nothing to
  configure beyond length). New CSS is `.search-*` (fixed hex colours
  throughout: `#d64545` target red, `#8a97a3` distractor grey, no
  `var(--...)`); shape (circle vs. square) is a CSS class, colour an
  inline style, matching Merkspanne-Test's own item-rendering pattern.
  Test: `tests/search_test.py`.
- **Doppelziel-Test (Attentional Blink)** (eleventh autonomous entry,
  2026-09-27): grounded in the classic RSVP (rapid serial visual
  presentation) attentional-blink paradigm (Raymond, Shapiro & Arnell,
  1992) - a fast stream of single letters flashes one at a time at
  fixation; one letter is coloured (T1, the first target - only its colour
  marks it, identity must still be read and remembered) and, at a variable
  "lag" (number of items later), the fixed letter X may or may not appear
  (T2). The hallmark, endlessly-replicated finding this paradigm exists to
  surface: correctly registering T1 measurably impairs detecting T2 for a
  brief window afterwards (deepest around lag 2-3, spared at lag 1, fully
  recovered by roughly lag 8) even though the eyes see it just fine -
  attention needs a moment to disengage and re-engage. This exercise
  samples exactly those three points (`AB_LAGS = [1, 3, 8]`) rather than
  every lag in between, to make the dip-and-recovery shape visible within a
  practical trial count. Also researched as sport-relevant: Overney,
  Blanke & Herzog (2008, PLOS ONE), "Enhanced Temporal but Not Attentional
  Processing in Expert Tennis Players", used this exact white-letter-T1/
  X-as-T2 RSVP design and found expert tennis players process the temporal
  stream itself faster than novices - though, honestly, NOT a smaller
  attentional-blink magnitude specifically, flagged both ways rather than
  only the flattering half (same spirit as Merkspanne-Test's own mixed-
  evidence note). Separately, a 2012 PNAS study (Choi et al.) found the
  blink itself can shrink substantially and durably with repeated RSVP
  practice - the actual rationale for treating this as a trainable
  exercise rather than a fixed trait. Genuinely distinct from every
  existing Test/NAT mechanic: every other exercise here presents stimuli
  either continuously visible (Merkspanne/Suchtest), one at a time with a
  real gap between items (Go/No-Go, Flanker, Posner, Simon, Rotationstest),
  or as a spatial layout (Trail Making, N-Back, Remember, Blitz-Raster) -
  none is a fast, gapless TEMPORAL stream where recognising one target
  costs attention needed for the next. 24 fixed trials (3 lags x
  6-T2-present + 2-T2-absent each, the absent trials a signal-detection
  false-alarm control, shuffled with the same same-lag-max-3-in-a-row
  guard used elsewhere), `abPrefs.difficulty` (leicht/mittel/schwer)
  controlling only the RSVP rate (`itemMs`: 140/100/70ms - 100ms matches
  the classic ~10 items/sec rate) and inter-trial gap. Both response
  questions are asked UNTIMED after the stream ends (same "wait for a tap,
  no countdown" convention as UFOV's own two post-glance questions) -
  deliberately no second speed pressure on top of the fast stream itself,
  since the whole point is measuring what got through DURING it. T2
  accuracy is scored only among trials where T1 was ALSO correctly
  identified (the standard AB scoring convention - the blink is
  specifically about attention actually being engaged by T1), reported per
  lag in the done-panel plus "Aufmerksamkeitslücke" = lag-8 accuracy minus
  lag-3 accuracy, the actual dip magnitude; overall tracked best is a
  combined T1+T2 accuracy% (`AB_BEST_KEY`), same `>`-is-better shape as
  most other fixed-trial exercises. No Bei-Fehler/background colour/
  Zusatzaufgabe/Trainingsmodus - correctly skipped per the "optional, skip
  what doesn't fit in an hour" guidance. New CSS is `.ab-*` (fixed hex
  colours throughout; the T1 colour reuses the app's own brand teal
  `#007094`, already used elsewhere as a "this one matters" highlight -
  Flanker's target underline, Posner's cued-box tint). Test:
  `tests/ab_test.py`.
- **Antizipationstest (Coincidence-Anticipation Timing)** (twelfth
  autonomous entry, 2026-09-27): grounded in the Coincidence-Anticipation
  Timing (CAT) paradigm from sport science - predicting WHEN a moving
  object will arrive at a target location and timing a response to
  coincide exactly, rather than simply reacting after the fact. Classically
  measured with the "Bassin Anticipation Timer" (a runway of sequentially-
  lit LEDs simulating an approaching object), widely used across soccer/
  tennis/volleyball/baseball/racket-sport research; scored via the standard
  three-way error decomposition (Schutz & Roy, 1973/1977) - Absolute Error
  (AE, overall timing accuracy), Constant Error (CE, signed early/late
  bias), Variable Error (VE, consistency). Reimplemented on a phone screen:
  a ball moves at constant speed across a horizontal track toward a marked
  target zone; the client taps once, at the moment they believe the ball
  arrives, and the trial reports how early/late that tap actually was.
  `ANTIZIP_DIFFICULTIES` (leicht/mittel/schwer) sets both the ball's travel
  time (jittered per trial within a range so a client can't just count
  seconds instead of watching) and the "Treffer" tolerance window - the
  same slow/moderate/fast speed manipulation the real CAT literature uses.
  Best score tracked as lowest mean Absolute Error in ms (`ANTIZIP_BEST_KEY`,
  lower-is-better, same shape as UFOV's own exposure-duration threshold).
  Genuinely distinct from every existing Test/NAT mechanic: MOT tracks
  continuously-moving objects but never needs a precisely-timed response
  (only an eventual identification tap after motion has already stopped);
  every RT-based exercise (Go/No-Go, Flanker, Posner, Simon, Rotationstest)
  measures how FAST a client responds to an already-present or just-
  appeared stimulus - this is the only one where the stimulus stays
  continuously visible and moving, and being precisely ACCURATE in timing
  (neither too early nor too late) is the entire point, not speed. A direct
  fit for FWMC's "bewegungsnahes mentales Training" angle - the same skill
  needed to time a strike, catch, or interception of a moving ball or
  opponent. No Bei-Fehler/background colour/Zusatzaufgabe/Trainingsmodus -
  correctly skipped (a fixed-trial timing-accuracy test, nothing to
  configure beyond difficulty). New CSS is `.antizip-*` (fixed hex colours
  throughout, no `var(--...)`). Test: `tests/antizip_test.py`.
- **Wahlreaktionstest (Hick's Law)** (thirteenth autonomous entry,
  2026-09-27): grounded in Hick's Law (Hick, 1952, "On the rate of gain of
  information", Quarterly Journal of Experimental Psychology; reviewed in
  Proctor & Schneider, 2018, QJEP) - choice reaction time rises linearly
  with the log2 of the number of stimulus-response alternatives (RT = a +
  b·log2(N)), the foundational quantitative law of decision speed. A
  block of N boxes is shown (N=2, then 4, then 8, always in that ascending
  order - a fixed block design, matching how Hick studies are actually run,
  since the client needs to learn the current mapping before a block
  starts); each trial one box lights up and the client taps that SAME box
  as fast as possible (a spatially-compatible stimulus=response-target
  mapping, same "the lit box IS the tap target" convention as
  Posner-Cueing's boxes, deliberately avoiding any separate S-R-compatibility
  confound layered on top of the choice-count manipulation itself). Reports
  average RT per block size plus the actual outcome measure this paradigm
  exists to surface: the Hick-Steigung (slope) in ms/Bit = (RT@8 - RT@2) /
  (log2(8) - log2(2)) - tracking the LOWEST slope per `hickPrefs.length` as
  the best score (`HICK_BEST_KEY`, lower-is-better, same `<`-comparison
  shape as UFOV's threshold/Antizip's AE, since a flatter slope = more
  efficient information processing, the theoretically "better" direction
  here). Also researched as sport-relevant: sports-science literature
  explains elite athletes' fast in-game decisions partly via deliberate
  practice collapsing effective choice complexity (an ingrained "most
  likely" response lowers the informational load per Hick's own formula),
  and studies comparing athletes/non-athletes on simple vs. choice RT
  consistently find athletes faster particularly as alternatives increase -
  a direct fit for FWMC's "visuelle Entscheidungsgeschwindigkeit" focus,
  and genuinely distinct from every existing Test/NAT mechanic: none of the
  twelve exercises above systematically varies the NUMBER OF RESPONSE
  ALTERNATIVES itself as the independent variable (Go/No-Go is 1-vs-withhold,
  Flanker/Simon/Posner are always exactly 2 responses with a conflict/cue
  layered on top, Suchtest varies DISPLAY set size not response count) -
  this is the only exercise whose entire point is the RT-vs-choice-count
  relationship. `hickPrefs.length` (kurz/mittel/lang = 3/5/7 reps per
  position per block, so total trials = reps·(2+4+8) = reps·14, same
  "length setting, no natural difficulty dial" shape as Suchtest/UFOV, since
  the difficulty ladder IS the fixed 2→4→8 block structure, not something
  client-configurable). Self-paced per trial (tap ends it immediately, only
  a `HICK_TIMEOUT_MS` = 5000ms safety net advances an unanswered trial,
  same `scheduleSearchTimer`-style always-clear-pending-timer pattern as
  Suchtest, since - unlike Simon/Flanker/Posner's fixed full-duration
  response window - this can transition early). Boxes are generated
  dynamically per block (`renderHickGrid(n)`, a CSS grid with 2/4/4-col
  layouts for N=2/4/8) rather than fixed HTML markup like Posner's two
  static boxes, since N varies across the run. No Bei-Fehler/background
  colour/Zusatzaufgabe/Trainingsmodus - correctly skipped, same reasoning as
  every other fixed-trial RT exercise on this tab (nothing to configure
  beyond length). Pause/resume uses the same scheduleXTimer-remaining-delay
  trick as Suchtest/Simon/Posner. New CSS is `.hick-*` (fixed hex colours
  throughout, no `var(--...)`); correct/wrong feedback reuses the
  green/red-box convention from Posner/Simon. Test: `tests/hick_test.py`.
- **Blockspanne-Test (Corsi Block-Tapping Task)** (fourteenth autonomous
  entry, 2026-09-27): grounded in the Corsi block-tapping task (Corsi,
  1972) - nine identical blocks are scattered on a board; a subset lights
  up ONE AT A TIME in a specific order, then the client reproduces that
  exact order by tapping the same blocks back. Standardised administration/
  scoring cited in-code from Kessels et al. (2000, "The Corsi Block-Tapping
  Task: Standardization and Normative Data" - healthy adults averaged a
  block span of 6.2, SD 1.3). Genuinely distinct from every existing
  Test/NAT memory mechanic: N-Back is a continuous match-N-trials-back
  stream; Remember/Blitz-Raster show several positions SIMULTANEOUSLY and
  probe recall of WHICH ones (unordered for Blitz-Raster, positions only
  for Remember); Flash Speicher Test recalls a sequence of CHARACTER
  IDENTITIES in order, at positions that are visually irrelevant to the
  recall itself; Merkspanne-Test is a single global same/different feature
  judgment over a whole array shown at once - this is the only exercise
  where the client must reproduce an ORDERED SEQUENCE OF SPATIAL LOCATIONS,
  the Corsi task's defining feature (holding both "where" and "in what
  order" at once). **Since 2026-10-02 it follows Kessels' standard: two
  sequences per length, advance while at least one is right, stop when
  both fail (`corsiAfterAttempt()`, progress pill "Länge n · Versuch x/2").**
  Originally simplified to a single-trial-per-length adaptive climb
  (sequence length +1 after every correct recall, ends on the first wrong
  tap) rather than Kessels' own 2-trials-per-length stop rule - the same
  simplification several digital adaptations use (e.g. PsyToolkit's own
  Corsi implementation climbs the same way); flagged below since this means
  "Blockspanne erreicht" here is the longest sequence recalled in ONE
  climb, not the more forgiving lab-standard score. No client-set
  "level"/Bei-Fehler - like N-Back/Hick, the climb itself is the adaptive
  difficulty; `corsiPrefs.difficulty` (leicht/mittel/schwer) controls only
  the flash speed (lit/gap duration), tracking best span reached per
  difficulty via `CORSI_BEST_KEY` (higher is better, same shape as
  N-Back/Antizip's own best-hint). The board's 9 positions are scattered
  fresh per run (anti-overlap placement copy-adapted from Trail Making/
  Suchtest's own) but held FIXED for the whole game, unlike a per-trial
  reshuffle, since the client needs one stable board to actually build
  spatial memory of across the climb. A wrong tap reveals the block that
  was actually next in the sequence (green) alongside the wrong one (red) -
  same "show what it actually was" convention as Hick/MOT/UFOV. No
  background colour/Zusatzaufgabe/Trainingsmodus/backward-recall variant -
  correctly skipped per the "optional, skip what doesn't fit in an hour"
  guidance (backward Corsi is a real, well-known variant but explicitly a
  later extension, same "start with the forward version first" spirit as
  every other exercise here). Test: `tests/corsi_test.py`.
- **Reaktionsfeld-Test** (fifteenth autonomous entry, 2026-09-27): grounded
  in reaction-light-board training devices such as the Dynavision D2 (a
  64-light board across five concentric rings from centre to periphery,
  reaction time + hit-count recorded, used in sport-vision training and
  concussion/return-to-play research - e.g. a University of Cincinnati
  football-player preseason study measuring reaction time with it, cited
  in-code). A single light appears somewhere across the whole field - mostly
  central, sometimes far out toward the edge - the client taps it as fast as
  possible, then the next one appears elsewhere immediately, for a fixed
  duration (`reaktPrefs.length` kurz/mittel/lang = 30/60/90s, `REAKT_BEST_KEY`
  tracks Treffer/Min, deliberately length-independent so a 30s and a 90s run
  are directly comparable - unlike Corsi/N-Back's own single climb-based
  score, this needed a rate, not a raw count, to be comparable across the
  three duration settings). Two modes mirror the real device's own Mode
  A/Mode B exactly, both offered rather than picking one (same "don't force
  a single mode when the source paradigm defines several" spirit as MOT's
  speed/count/both): `"proaktiv"` (light stays lit until hit, untimed) and
  `"reaktiv"` (light times out after `REAKT_DIFFICULTIES[difficulty]
  .exposureMs` and moves on regardless, counted as "Verpasst"). Difficulty
  (leicht/mittel/schwer) sets both that exposure window AND
  `minJumpFrac` - how far (as a fraction of the stage's half-diagonal) the
  NEXT light must appear from the current one, in BOTH modes - so higher
  difficulty always means more ground to cover across the whole field, not
  just faster taps in one spot, matching the real device's own full-board-
  scanning emphasis. Every light's landing position is silently classified
  "zentral" vs. "peripher" (`REAKT_CENTRAL_RADIUS_FRAC = 0.4` of the stage's
  half-diagonal from centre - nothing is drawn to mark this boundary, same
  invisible-split convention as UFOV's own centre/peripheral categorisation)
  purely for reporting - the done-panel breaks out hit-rate/average RT per
  zone separately, mirroring the Dynavision literature's own central-vs-
  peripheral-ring hit-data breakdown, a direct fit for FWMC's "peripheres
  Sehen" focus specifically (not just reaction time in the abstract).
  Genuinely distinct from every existing Test/NAT mechanic: this is the only
  exercise whose stimulus can land ANYWHERE across a continuous field (not
  fixed grid cells like Blitz-Raster/N-Back/Corsi, not framed compass
  positions like UFOV/Posner) and whose whole point is raw speeded motor
  reaction to wherever it appears next, one at a time, for a sustained
  stretch of real time rather than a fixed trial count - UFOV measures a
  masked GLANCE under adaptive exposure with no motor race at all, Blitz-
  Raster shows several cells simultaneously then asks for delayed recall,
  MOT tracks objects that stay identical and keep moving continuously
  instead of appearing/disappearing at discrete points. No Bei-Fehler/
  background colour/Zusatzaufgabe/Trainingsmodus - correctly skipped per the
  "optional, skip what doesn't fit in an hour" guidance (a continuous
  reaction-rate test, nothing to configure beyond mode/difficulty/length).
  Pause/resume is a no-op beyond blocking input in "proaktiv" mode (no timer
  to shift, same shape as UFOV's own untimed response phases) and uses the
  usual scheduleXTimer-remaining-delay trick for "reaktiv" mode's exposure
  timeout. New CSS is `.reakt-*` (fixed hex colours throughout - a warm
  amber/gold light, `#f2a900`/`#ffe27a`, deliberately distinct from every
  other exercise's own stimulus colour on this tab, no `var(--...)`). Test:
  `tests/reakt_test.py`.

- **Regelwechsel-Test (Task-Switching)** (sixteenth autonomous entry,
  2026-09-27): grounded in the task-switching paradigm (Jersild, 1927;
  popularised by Rogers & Monsell, 1995's "alternating runs" design; the
  cued variant used here follows Meiran, 1996) - the same simple, ambiguous
  digit can be classified by one of two rules ("Zahl": gerade/ungerade, or
  "Größe": kleiner/größer als 5), and a cue names which rule applies THIS
  trial; the rule sometimes stays the same as the previous trial ("repeat")
  and sometimes changes ("switch"). Reports accuracy% plus average RT after
  a repeat vs. after a switch and their difference as the "Wechselkosten"
  (switch cost, ms) - the actual, endlessly-replicated outcome measure this
  paradigm exists to surface: even though the decision itself is equally
  simple either way, a switch trial is reliably slower (and often less
  accurate), because reconfiguring which rule is active costs real time,
  not the individual decision being harder. Bivalent bare-digit stimuli
  (every digit 1-4/6-9, excluding neutral 5, is a valid input to BOTH
  rules) copy the classic Rogers & Monsell/Meiran stimulus design directly.
  `tsPrefs.difficulty` (leicht/mittel/schwer) controls only the
  cue-stimulus interval (`csiMs`, the task-preparation time Meiran 1996
  showed actually shrinks the switch cost - generous on Leicht, almost none
  on Schwer) plus response window/ISI, tracking the LOWEST switch cost per
  difficulty as best (`TS_BEST_KEY`, lower-is-better, same shape as
  Hick/UFOV/Antizip). Also researched as sport-relevant: skilled/expert
  athletes show more flexible attentional-resource allocation and better
  task-switching accuracy than non-athletes under dual-task load (a 2024
  postural-control/cognitive-flexibility study), while task-switching
  accuracy specifically drops under mental fatigue in athletes (a 2026
  soccer-player ERP study) - a fit for FWMC's "visuelle
  Entscheidungsgeschwindigkeit" focus, this time the facet of adapting the
  decision RULE itself rather than filtering/inhibiting/timing an
  already-fixed one. Genuinely distinct from every existing Test/NAT
  mechanic: none of the fifteen exercises already on this tab ever changes
  WHICH RULE governs the same response mid-run - Simon/Flanker/Posner/
  Rotationstest all apply one constant rule to a changing stimulus, Hick
  varies the NUMBER of alternatives but never their meaning, Suchtest
  varies the target definition only across whole BLOCKS (feature vs.
  conjunction), never trial-by-trial with a real switch-vs-repeat contrast
  within one run. Fixed 44-trial run (`TS_TRIAL_COUNT`; trial 0 is an
  unclassified "warm-up" with no previous task to compare against, the
  other 43 split roughly evenly between switch/repeat via the same
  max-3-in-a-row-same-type guard used elsewhere). No Bei-Fehler/background
  colour/Zusatzaufgabe/Trainingsmodus/length setting - correctly skipped
  per the "optional, skip what doesn't fit in an hour" guidance, same
  reasoning as every other fixed-trial RT exercise here. Self-paced per
  trial with a safety-net timeout (`scheduleTsTimer`, same always-clear-
  pending-timer pattern as Hick/Suchtest) and the usual remaining-delay
  pause/resume. New CSS is `.ts-*` (fixed hex colours throughout, no
  `var(--...)`); correct/wrong is a plain solid background swap on the
  tapped response button (Flanker/Posner/Hick's convention) rather than
  Simon's colour-neutral ring, since these two buttons' LABELS themselves
  change every trial with the active rule - there's no fixed button colour
  meaning here that a solid swap could confuse. Test: `tests/ts_test.py`.
- **Gegenrichtungs-Test (Antisakkaden-Prinzip)** (seventeenth autonomous
  entry, 2026-09-27): grounded in the antisaccade task (Hallett, 1978) - a
  peripheral stimulus automatically pulls attention/gaze toward it (the
  "prosaccade" response); the antisaccade variant instead instructs
  responding AWAY from it, requiring active inhibition of that automatic
  pull. Real eye movements can't be measured on a phone screen, so this is
  built as the well-established MANUAL adaptation used throughout
  individual-differences and applied research when eye-tracking hardware
  isn't available - a dot appears left or right of a central fixation
  cross, and the client taps a fixed button either on the SAME side ("Pro"
  block - the automatic/compatible response, a baseline) or the OPPOSITE
  side ("Anti" block), directly following Kane, Bleckley, Conway & Engle
  (2001)'s manual antisaccade task for measuring individual differences in
  cognitive inhibition. Reports accuracy% plus average RT for the Pro vs.
  Anti block and their difference as "Hemm-Kosten" (inhibition cost, ms) -
  the actual outcome measure this paradigm exists to surface - tracking the
  LOWEST cost per `antiPrefs.difficulty` (leicht/mittel/schwer, controlling
  only the pre-stimulus foreperiod and a generous safety-net response
  timeout, self-paced like Regelwechsel-Test/Suchtest/Hick rather than a
  fixed full-duration response window, since direction errors - not raw
  speed - are the classic antisaccade DV and a tight fixed window would
  bias exactly the cost being measured) via `ANTI_BEST_KEY` (lower-is-
  better, same shape as Regelwechsel-Test/Hick/UFOV/Antizip). Also
  researched as sport-relevant: volleyball players showed a different
  interference pattern between saccadic and key-press reaction times than
  non-athletes on this exact manual/oculomotor contrast (Kokubu, Ando, Kida
  & Oda, 2006); more recent 2026 work links athletes' antisaccade
  performance to distinct microsaccade-preparation behaviour and shows
  prior high cognitive demand measurably lowers subsequent manual-
  antisaccade performance - a fit for FWMC's inhibitory-control/visuelle-
  Entscheidungsgeschwindigkeit focus. Genuinely distinct from every existing
  Test/NAT mechanic: Regelwechsel-Test mixes two classification RULES
  trial-by-trial on one ambiguous stimulus (one judgment, changing rule
  meaning every trial); Simon's location-vs-colour conflict is automatic
  and uninstructed, never a stated rule; Posner-Cueing's cue only predicts
  where a target MIGHT appear, never dictates the response mapping itself -
  this is the only exercise whose entire point is an EXPLICITLY INSTRUCTED,
  BLOCKED override of an automatic orienting response (Pro block always
  first as a baseline, then Anti - matching how the real paradigm is
  actually administered, a fixed, non-counterbalanced order same as
  Wahlreaktionstest's own 2→4→8 block order). Fixed 32-trial run
  (`ANTI_TRIALS_PER_BLOCK` = 16 per block, balanced left/right, shuffled
  with the same max-3-in-a-row-same-side guard used elsewhere). No
  Bei-Fehler/background colour/Zusatzaufgabe/Trainingsmodus - correctly
  skipped per the "optional, skip what doesn't fit in an hour" guidance,
  same reasoning as every other fixed-trial RT/cost exercise here. New CSS
  is `.anti-*` (fixed hex colours throughout, no `var(--...)`); reuses
  Simon's own fixed-position left/right slot layout idea
  (`.anti-slot`/`.anti-dot`) since both need a stimulus that can appear at
  one of two known locations near two fixed response targets, but with
  plain neutral dots/buttons (not colour-coded) since side, not colour, is
  the whole point here. Test: `tests/anti_test.py`.
- **Wortfarben-Test (Stroop-Aufgabe)** (eighteenth autonomous entry,
  2026-09-27): grounded in the classic Stroop colour-word task (Stroop,
  1935, "Studies of interference in serial verbal reactions", Journal of
  Experimental Psychology 18(6), 643-662) - a colour name ("ROT"/"BLAU"/
  "GRÜN"/"GELB") is printed in one of four ink colours, and the client
  must tap the colour PATCH matching the actual ink colour, ignoring the
  word's meaning entirely. Reading a familiar word is fast and automatic
  and keeps happening whether or not it's wanted, so when the word's
  meaning conflicts with its own ink colour ("inkongruent", e.g. "ROT"
  printed in blue) that automatic reading response competes with the
  instructed colour-naming response - correct answers come slower and
  less accurately than when word and ink agree ("kongruent"), the classic
  Stroop effect, one of the most replicated findings in cognitive
  psychology. Reports accuracy% plus average congruent/incongruent RT and
  their difference as the "Stroop-Effekt" (ms) - the actual outcome
  measure this paradigm exists to surface - tracking best accuracy% per
  `stroopPrefs.difficulty` (leicht/mittel/schwer, reusing
  SIMON_DIFFICULTIES/FLANKER_DIFFICULTIES' exact response-window/ISI
  numbers, a single-stimulus immediate-response task of comparable load)
  via `STROOP_BEST_KEY`. Also researched as sport-relevant: "Enhanced
  Cognitive Inhibition in Table Tennis Athletes: Insights from Color-Word
  and Spatial Stroop Tasks" (2024, PMC11117886) found table-tennis
  athletes showed a SMALLER Stroop effect (faster, more stable
  colour-naming despite the word conflict) than non-athletes on both the
  classic colour-word Stroop task and a spatial Stroop variant - a fit for
  FWMC's "visuelle Entscheidungsgeschwindigkeit" focus. Genuinely distinct
  from every existing Test/NAT mechanic: Simon's conflict comes from a
  stimulus's task-IRRELEVANT spatial location automatically priming a
  response side, with no verbal/reading component at all; Flanker's
  conflict comes from simultaneous DISTRACTOR stimuli surrounding an
  unambiguous central target; Regelwechsel-Test mixes two classification
  RULES on one ambiguous stimulus, but that stimulus (a bare digit) has no
  automatic reading response competing with anything - this is the only
  exercise whose interference arises WITHIN a single stimulus, between its
  automatically-read verbal identity and the separate perceptual dimension
  (colour) actually being judged. Fixed 48-trial run (24 congruent, 6 per
  colour + 24 incongruent, 2 reps of each of the 12 word≠ink combinations -
  a balanced 50/50 split with every colour equally often the correct
  answer), shuffled with the same same-correct-colour-max-3-in-a-row guard
  used elsewhere. No Bei-Fehler/background colour/Zusatzaufgabe/
  Trainingsmodus - all correctly skipped per the "optional, skip what
  doesn't fit in an hour" guidance, same reasoning as Simon/Flanker (a
  fixed-trial accuracy/RT test, nothing to configure beyond difficulty).
  Pause/resume uses the same scheduleXTimer-remaining-delay trick as
  Simon/Flanker/Posner. New CSS is `.stroop-*` (fixed hex colours
  throughout, no `var(--...)`); the four response buttons are plain colour
  swatches with NO text label - deliberately, unlike Simon's own labelled
  blue/orange buttons, since a text-labelled colour button here would
  itself need to be read, adding a second reading step on top of the exact
  word-vs-colour conflict this task exists to measure (the same "point to
  the colour patch" convention used in manual Stroop adaptations in
  individual-differences research). Test: `tests/stroop_test.py`.
  **Correction added after the fact (parent session, not the implementing
  run):** the implementing run's "genuinely distinct from every existing
  Test/NAT mechanic" claim above missed that Visual Training already has
  its own "Stroop · klassisch" exercise (`stroop-classic` in `EXERCISES`,
  app.js ~line 578 - "Sag laut die Schriftfarbe – nicht das Wort", plus a
  "Stroop · mit Hintergrund" variant) - the ground rule to also skim other
  sections' own exercise lists, not just the Test roster, wasn't followed
  here. The two aren't identical: VT's version is a spoken, unscored drill
  running for a fixed duration inside the generic timed-block engine (say
  it out loud, no input capture, no RT/accuracy at all), while this one is
  a self-contained, tap-scored trial-based test reporting accuracy/RT/the
  Stroop-effect number - closer in spirit to how Simon/Flanker turn a
  classic paradigm into a measured exercise than to VT's drill format. Real
  enough a difference that this wasn't reverted, but real enough an
  overlap (same paradigm, same "Stroop" name, adjacent on the same home
  screen) that it's flagged below in Offene Fragen for the client's own
  call rather than decided unilaterally.
- **Sofortmengen-Test (Subitizing-Aufgabe)** (nineteenth autonomous entry,
  2026-09-28): built from the "Recherche-Backlog: 20 Kandidaten" list above
  rather than fresh research this round (candidate #1 there was Iconic-
  Speicher/Partial-Report - not built - this is candidate #2, Sofortmengen/
  Subitizing). Grounded in Kaufman, Lord, Reese & Volkmann (1949), who
  coined "subitizing" - instant, accurate enumeration of up to ~4 items
  with flat reaction time, versus slower, roughly linearly-rising RT when
  serially counting beyond that - and Trick & Pylyshyn (1994), tying the
  small-number/large-number RT break to a limited-capacity preattentive
  individuation mechanism ("FINST," the same visual-indexing idea
  underlying this app's own MOT-Fähigkeit). A scatter of 1-9 identical
  dots (random positions, simple rejection-sampling min-spacing, adapted
  from `motPlaceObjects`' approach for static rather than moving points)
  flashes for `SUBITIZE_DIFFICULTIES[difficulty].flashMs`
  (leicht/mittel/schwer: 700/450/280ms), then the client taps the matching
  count on a 1-9 keypad (`.subitize-key`, styled like Flash's `.flash-key`/
  N-Back's `.nback-match-btn`). Fixed 27-trial run (`SUBITIZE_REPS_PER_
  COUNT = 3` × counts 1-9), shuffled avoiding identical consecutive counts.
  Genuinely distinct from every existing Test/NAT exercise: nothing else
  measures a QUANTITY judgment at all - Merkspanne-Test judges a colour
  CHANGE, Suchtest judges presence/absence of one target, Corsi/Remember/
  Blitz-Raster judge WHICH positions - this is the only one whose whole
  point is "how many." Reports accuracy% plus the actual outcome measure
  this paradigm exists to reveal: average RT for the "instant" range (≤4
  dots, `SUBITIZE_SUBITIZING_MAX`) versus the "counting" range (≥5 dots),
  and their difference. `SUBITIZE_BEST_KEY` tracks the lowest (fastest)
  subitizing-range RT per difficulty, gated to ≥80% accuracy so a
  fast-random-tap run can't fake a record. Unlike every RT exercise built
  so far, this task is deliberately self-paced with NO answer timeout (the
  literature doesn't force a response deadline here, and forcing one would
  conflate "how fast can you glance-count" with "how fast can you also
  physically tap in time") - trials only advance once tapped, so an idle
  run simply waits at the keypad rather than silently accumulating misses.
  No Bei-Fehler/background colour/Zusatzaufgabe/Trainingsmodus - all
  correctly skipped per the "optional, skip what doesn't fit in an hour"
  guidance; a tinted background would work against the plain-dot-on-plain-
  background contrast the count judgment itself depends on, unlike the
  conflict-paradigm exercises where a background tint is cosmetic. Pause/
  resume uses the same scheduleXTimer-remaining-delay trick as every other
  Test entry. Test: `tests/subitize_test.py`.
  **Process note**: this run's FIRST attempt independently built a
  Flanker-task exercise (Pfeil-Konflikttest) using the exact same Eriksen &
  Eriksen (1974) grounding already shipped as "Ablenkungstest (Flanker)"
  (fourth entry above, 2026-09-27) - a genuine duplicate, caught only after
  the full regression suite had already passed locally, when `git push`
  was rejected as non-fast-forward and a fetch revealed 32 commits had
  landed on `origin/main` from other concurrent sessions while this one
  was building (this repo now has multiple sessions racing on the same
  branch, not the single-session-at-a-time model this file's "Hard rule"
  section was written for). The duplicate work was never pushed - it was
  moved to a local-only `backup-duplicate-flanker-work` branch instead
  (not on `origin`, so a future session won't see or need it) - and
  `origin/main` was fetched fresh before picking a genuinely new idea from
  the (much longer than remembered) live roster and the research backlog
  above. Take-away for future runs: given how fast this roster now moves,
  re-fetch and re-read the roster (or the backlog above) immediately
  before committing to an idea, not just at the start of the session - and
  expect `git push` to occasionally need a rebase onto commits that landed
  mid-run.
- **Alarmierungs-Test (Alerting-Netzwerk)** (twentieth autonomous entry,
  2026-09-28): built from the "Recherche-Backlog: 20 Kandidaten" list
  (candidate #17) rather than fresh research this round. Grounded in the
  Attention Network Test framework (Fan, McCandliss, Sommer, Raz & Posner,
  2002, "Testing the efficiency and independence of attentional networks",
  Journal of Cognitive Neuroscience 14(3):340-347), building on Posner &
  Petersen's 1990 theory of three separable attentional networks -
  alerting, orienting, executive. This exercise isolates the ALERTING
  network: on half the trials the fixation cross itself briefly flashes (a
  plain, centred, non-directional warning - it carries no location
  information at all), then after a FIXED total foreperiod (identical
  whether cued or not, `ALARM_FOREPERIOD_MS = 500`) a target dot appears in
  a left or right box; the client taps that same box as fast as possible.
  Reports accuracy% plus average RT with/without the warning and their
  difference as the "Alarmierungs-Effekt" - how much a simple readiness cue
  speeds responding, the network's efficiency, the actual outcome measure
  this paradigm exists to surface. Genuinely distinct from the already-
  built Hinweisreiz-Test (Posner-Cueing) despite sharing the exact same
  two-box `.posner-*` CSS/layout (reused directly, not duplicated - only a
  new `.posner-fix.flash` modifier was added for the alerting flash itself):
  Posner's cue is spatially INFORMATIVE (predicts WHERE the target will
  appear, testing voluntarily shifting/re-orienting attention between two
  known locations); this cue carries ZERO location information and only
  tests WHETHER a generic warning speeds readiness at all - the ANT
  literature treats alerting and orienting as explicitly separable,
  independent networks, so this fills a real gap rather than duplicating
  Posner-Cueing. Fixed 32-trial run (`ALARM_TRIAL_COUNT`, balanced 16
  cued/16 uncued and 16 links/16 rechts), shuffled with a guard against
  more than 3 identical target sides OR more than 3 identical cued/uncued
  trials back to back (same shape as `buildPosnerTrials`/`buildFlankerTrials`,
  extended to cover both manipulated variables at once here). No Bei-
  Fehler/Zusatzaufgabe/Trainingsmodus - correctly skipped per the "optional,
  skip what doesn't fit in an hour" guidance, same reasoning as every other
  fixed-trial RT/effect exercise on this tab; background colour/intensity
  WAS included (`alarmPrefs.bgColorKey`/`bgIntensity`, `makeBgApplier`/
  `wireBgIntensityControl` on both the ready screen and the pause overlay) -
  basically free since it's the exact same three-line wiring as every
  sibling exercise, unlike Subitizing-Test where a tint would have worked
  against the task's own contrast requirement. `ALARM_BEST_KEY` tracks best
  accuracy% per `alarmPrefs.difficulty` (leicht/mittel/schwer - controlling
  only the response window and inter-trial gap, deliberately NOT the
  foreperiod itself, which stays constant across difficulty since it's the
  controlled scientific variable this task exists to isolate). Pause/resume
  uses the same scheduleXTimer-remaining-delay trick as Posner/Flanker/
  Go-No-Go. Test: `tests/alarm_test.py`.
- **Vorlaufzeit-Test (Foreperiod-Effekt)** (twenty-first autonomous entry,
  2026-09-28): built from the "Recherche-Backlog: 20 Kandidaten" list
  (candidate #18) rather than fresh research this round. Grounded in Niemi
  & Näätänen (1981, Psychological Bulletin, "Foreperiod and simple reaction
  time" - the "expectancy hypothesis": across a trial-to-trial VARYING
  wait, a person builds a moment-by-moment expectancy of when the stimulus
  will arrive, and RT typically drops as the foreperiod stretches on
  without the stimulus yet appearing, since the conditional probability of
  "it's about to happen NOW" keeps rising the longer the wait has already
  lasted). A single, always-present warning cue (the centre dot turning
  from a hollow outline to a steady "armed" border) is followed by the
  actual go signal (the dot filling in solid green) after a foreperiod that
  varies randomly trial-to-trial across five fixed steps spanning the
  classic 500-4000ms range (`VORLAUF_FOREPERIODS_MS = [500, 1000, 1750,
  2750, 4000]`); the client taps anywhere on the stage the instant the dot
  fills in - a single, plain reaction, no categorisation of any kind.
  Reports the mean RT per foreperiod bin plus the actual outcome measure
  this paradigm exists to surface: the "Erwartungseffekt" (Ø RT at the two
  shortest foreperiods minus Ø RT at the two longest), expected positive
  per the expectancy hypothesis - responses should get FASTER the longer
  the wait has already lasted, not slower. A tap during the "armed" wait
  itself (before the dot actually fills in) is the classic foreperiod
  anticipation/false-start error, tracked and excluded from the RT
  averages rather than scored as an implausibly fast hit.
  `vorlaufPrefs.length` (kurz/mittel/lang = 4/6/8 reps per foreperiod, so
  20/30/40 total trials) is the only client-facing setting, same "length,
  no natural difficulty dial" shape as Suchtest/UFOV/Hick, since the
  foreperiod range itself is the fixed scientific manipulation, not
  something to make easier/harder. `VORLAUF_BEST_KEY` tracks the LOWEST
  overall mean RT per length (lower-is-better, same shape as UFOV/Hick/
  Regelwechsel-Test/Gegenrichtungs-Test). Background colour/intensity WAS
  included (`vorlaufPrefs.bgColorKey`/`bgIntensity`, `makeBgApplier`/
  `wireBgIntensityControl` on both the ready screen and the pause overlay)
  - basically free, and unlike Subitizing-Test's plain-dot-count judgment,
  a background tint sitting behind this task's own colour-coded dot states
  doesn't compete with anything being judged. Genuinely distinct from the
  just-built Alarmierungs-Test despite both being foreperiod-based: Alarm's
  foreperiod is held FIXED (500ms) and the manipulated variable is whether
  a non-spatial warning cue occurs AT ALL (cued vs. uncued, isolating the
  alerting network's benefit); here the SAME warning cue is present on
  every single trial and the manipulated variable is instead the LENGTH of
  the wait itself, varied continuously across five steps - this is the
  only exercise on the whole tab whose independent variable is a
  continuously-varying TIME INTERVAL, reported as a mean-RT-per-interval
  curve rather than a single cued/uncued difference score (the same
  distinction already anticipated in this candidate's own backlog
  write-up). No Bei-Fehler/Zusatzaufgabe/Trainingsmodus - correctly
  skipped per the "optional, skip what doesn't fit in an hour" guidance,
  same reasoning as every other fixed-trial RT/effect exercise on this
  tab. Self-paced per trial (tap ends it immediately once the target
  appears) with a `VORLAUF_RESPONSE_TIMEOUT_MS = 2000` safety-net timeout
  for an unanswered trial, same shape as Suchtest/Hick/Regelwechsel-Test's
  own always-clear-pending-timer pattern; a real bug caught and fixed
  during testing (not shipped broken): the first draft advanced to the
  next trial SYNCHRONOUSLY on tap, which cleared the dot's just-set
  feedback class (`falsestart`/`missed`) in the very same tick before it
  could ever actually render - fixed with a `VORLAUF_FEEDBACK_MS = 400`
  pause before advancing, the same lesson Suchtest's own
  `SEARCH_FEEDBACK_MS` already encodes for exactly this class of
  self-paced-task bug. Pause/resume uses the same scheduleXTimer-
  remaining-delay trick as every other Test entry. New CSS is
  `.vorlauf-*` (fixed hex colours throughout, no `var(--...)`); a single
  circular dot with four visual states (base/armed/target/falsestart/
  missed) rather than Alarm/Posner/Simon's two-box layout, since there's
  only ever one response location here. Test: `tests/vorlauf_test.py`.
- **Stopp-Signal-Test** (twenty-second autonomous entry, 2026-09-29): built
  from the "Recherche-Backlog: 20 Kandidaten" list (candidate #6) rather
  than fresh research this round. Grounded in the stop-signal paradigm
  (Logan, Cowan & Davis, 1984, Journal of Experimental Psychology: Human
  Perception and Performance - the independent race-model method for
  estimating Stop-Signal Reaction Time, SSRT; Verbruggen & Logan, 2008,
  Trends in Cognitive Sciences, reviewing its use as a purer measure of
  response inhibition than simple go/no-go). Most trials show a single
  black arrow (left/right) - tap the matching `.stop-response-btn` as fast
  as possible. On `STOP_RATIO = 0.25` of trials (16 of `STOP_TRIAL_COUNT =
  64`, the classic stop-signal ratio), the arrow turns red after a short,
  adaptively-tracked delay (the Stop-Signal-Delay, SSD, starting at
  `STOP_SSD_START_MS = 250`) - the client must withhold the already-
  initiated tap. `STOP_SSD_STEP_MS = 50` staircases the SSD: a successful
  stop (no tap before the response window closes) lengthens SSD (harder to
  inhibit next time), a failed stop (any tap on a stop trial, whatever the
  direction or timing) shortens it (easier next time) - the standard
  design so the staircase converges toward ~50% stopping success and SSRT
  can be estimated via the race model. Reports Go-trial accuracy% plus
  average Go-RT, % of stop trials successfully withheld, and the actual
  outcome measure this paradigm exists to surface: SSRT ≈ mean Go-RT minus
  the converged SSD (averaged over the last 8 stop trials only, the same
  "let the staircase settle first" idea as UFOV's own last-10-trials
  threshold average) - tracking the LOWEST SSRT per `stopPrefs.difficulty`
  (leicht/mittel/schwer, controlling only the response window/ISI, same
  shape as every other fixed-trial RT exercise - the SSD staircase itself
  is the actual adaptive difficulty, deliberately not client-set) via
  `STOP_BEST_KEY` (lower-is-better, same shape as UFOV/Hick/Regelwechsel-
  Test/Gegenrichtungs-Test/Vorlaufzeit-Test). Genuinely distinct from
  Go/No-Go, already on this tab: Go/No-Go's stimulus signals "don't go"
  from the very first frame, before any motor programme starts; here
  EVERY trial begins as an identical Go arrow, and the stop signal - when
  it comes - typically arrives after the response has already begun,
  testing CANCELLING a response in flight rather than deciding not to
  start one, a distinct and (per the inhibition literature) more sensitive
  construct than Go/No-Go's simple accuracy%. Also distinct from every
  other Test-Bereich exercise: none of Flanker/Simon/Posner/Alarm/
  Vorlaufzeit-Test ever asks the client to withhold an already-cued
  response. Background colour/intensity WAS included (`stopPrefs.
  bgColorKey`/`bgIntensity`, `makeBgApplier`/`wireBgIntensityControl` on
  both the ready screen and the pause overlay) - basically free, and the
  single black/red arrow's own contrast is unaffected by a tint sitting
  behind it. No Bei-Fehler/Zusatzaufgabe/Trainingsmodus - correctly
  skipped per the "optional, skip what doesn't fit in an hour" guidance,
  same reasoning as every other fixed-trial RT/effect exercise on this
  tab (the SSD staircase already IS the adaptive mechanism, a second one
  would be redundant). Pause/resume uses the same scheduleXTimer-
  remaining-delay trick as every other Test entry - a stop trial's own
  two-step schedule (show arrow → arm the red signal at SSD → end at the
  remaining response time) still only ever has ONE timer pending at once,
  so the existing single-slot `timerFn`/`timerFiresAt` pause mechanism
  needed no changes. New CSS is `.stop-*` (fixed hex colours throughout,
  no `var(--...)`); a single centred arrow plus two response buttons,
  reusing Flanker's own left/right response-button layout idea but with
  just one (non-flanked) arrow, since only one stimulus is ever shown at
  once here. Test: `tests/stop_test.py`.
- **Zeichen-Zuordnungs-Test** (twenty-third autonomous entry, 2026-09-29):
  built from the "Recherche-Backlog: 20 Kandidaten" list (candidate #9)
  rather than fresh research this round. Grounded in the Digit Symbol
  Substitution Test (DSST, the "Coding" subtest of the Wechsler Adult
  Intelligence Scale) - a widely-used general processing-speed measure: a
  key maps each digit 1-9 to an abstract symbol, and the client converts
  as many digits to symbols as possible within a fixed time. A fresh,
  randomly-shuffled digit→symbol key (`DSST_SYMBOLS`, 9 simple geometric
  Unicode glyphs: △○□◇☆✚▽●✦) is generated at the START of every run and
  stays visible the whole time (`#dsstKeyRow`) - re-shuffled per run
  rather than one fixed standard key, deliberately, so repeat play trains
  genuine key-lookup speed rather than eventually memorising one fixed
  mapping (the real DSST's own repeat-testing use case, form A/B, made the
  same choice for the same reason). A single random digit 1-9 (a cheap
  "avoid immediate repeat" reroll, not a full shuffle-array, since the run
  length is open-ended rather than a fixed trial count) is shown large,
  and the client taps the matching symbol from a keypad (`#dsstKeypad`)
  built in the SAME left-to-right order as the key row, so the correct
  answer is always at the same visual column just looked up above. Runs
  continuously for a fixed duration (`dsstPrefs.length`, kurz/mittel/lang
  = 60/90/120s - same "length setting, no natural difficulty dial" shape
  as Suchtest/UFOV/Hick, since the real DSST has no difficulty knob
  either: one fixed key, one fixed digit range, raced against the clock)
  - self-paced per trial (a tap advances immediately after a brief
  `DSST_FEEDBACK_MS = 250` feedback pause, no per-item timeout, since the
  real test's whole point is throughput against the OVERALL time limit,
  not per-item speed) - `dsstNextTrial()` checks elapsed time itself and
  ends the run instead of showing a new digit once the duration is up, the
  same "duration-checked-at-spawn-time" shape Reaktionsfeld-Test already
  uses, so no second, competing timer is ever needed alongside the brief
  post-tap feedback timer (a real, deliberate design choice this time, not
  a bug found during testing - the Vorlaufzeit-Test/Suchtest lesson about
  needing SOME feedback delay before a self-paced advance was already
  known going in). Reports total correct substitutions (the DSST's own
  standard score, tracked as best via `DSST_BEST_KEY` per length, higher
  is better) plus accuracy% and a wrong-tap count. Background colour/
  intensity WAS included (`dsstPrefs.bgColorKey`/`bgIntensity`,
  `makeBgApplier`/`wireBgIntensityControl` on both the ready screen and
  the pause overlay) - basically free, and unlike Subitizing-Test's plain-
  dot-count judgment, a tint behind a fixed, known inventory of 9 shapes
  the client keeps re-checking against a legend doesn't compete with a
  subtle contrast judgment the way a pop-out/colour task would. No Bei-
  Fehler/Zusatzaufgabe/Trainingsmodus - correctly skipped per the
  "optional, skip what doesn't fit in an hour" guidance, same reasoning as
  every other fixed-duration/fixed-trial Test entry (nothing to configure
  beyond length, no natural "level" to progress). Genuinely distinct from
  every existing Test/NAT mechanic: Hick-Test varies the NUMBER of
  response alternatives with a spatially-compatible mapping (the lit box
  IS the tap target, no lookup needed); this instead demands constantly
  CONSULTING an arbitrary, freshly-learned key and re-mapping symbol
  identity every single trial - a genuinely different (coding/psychomotor
  translation) facet of processing speed nothing else on this tab touches.
  Pause/resume mirrors Reaktionsfeld-Test's own elapsed-time-based shape
  (shift `startTime` forward by the paused span on resume) rather than the
  usual single-pending-timer replay, since most of a self-paced run has NO
  pending timer at all (waiting on a tap) - same shape Suchtest/Subitizing
  already use for the same reason. New CSS is `.dsst-*` (fixed hex colours
  throughout, no `var(--...)`); the key row and keypad are both plain flex
  rows of 9 equal-width cells so their columns visually line up on a
  phone-width screen. Test: `tests/dsst_test.py`.
- **Kartensortier-Test** (twenty-fourth autonomous entry, 2026-09-29):
  built from the "Recherche-Backlog: 20 Kandidaten" list (candidate #7)
  rather than fresh research this round. Grounded in the Wisconsin Card
  Sorting Test (WCST; Grant & Berg, 1948; Milner, 1963, tying perseverative
  errors to dorsolateral-prefrontal damage). Four reference cards sit fixed
  on screen (1 red triangle, 2 green stars, 3 yellow squares, 4 blue
  circles - each unique on all three dimensions at once, the classic WCST
  reference-card design); a new stimulus card appears below and the client
  taps whichever reference card it "matches" - but the matching RULE
  (Farbe/Form/Anzahl) is never shown, only right/wrong feedback after each
  tap, and the client must infer it purely from that feedback. Once
  `WCST_STREAK_NEEDED` (6, simplified from the classic protocol's 10-in-a-
  row criterion - same "shorter for a quick training run" trade-off already
  made for Blockspanne-Test's single-trial-per-length simplification)
  consecutive correct matches accumulate under the current rule, it
  silently switches to the next one in the classic Farbe→Form→Anzahl cycle
  with no warning - the client has to notice their strategy stopped
  working and re-derive a new one. Genuinely distinct from every existing
  Test/NAT mechanic: Regelwechsel-Test explicitly CUES which of two known
  rules applies every single trial (a pure switch-cost paradigm); this is
  the only exercise where the rule is never told at all and must be
  discovered - and re-discovered after every silent switch - from feedback
  alone, testing rule LEARNING and perseveration (clinging to an outdated
  rule) rather than the cost of switching between two already-known rules.
  Stimulus cards are generated with all three dimension-indices pairwise
  distinct (`wcstRandomCard`, simple rejection sampling) so every card
  points unambiguously to three DIFFERENT reference cards depending on
  which rule is active - the same "unambiguous card" simplification
  several digital WCST adaptations use, since the real deck's occasional
  ambiguous cards (two or three dimensions pointing at the same reference
  card) are excluded from scoring in the standard protocol anyway. Reports
  categories completed (rule blocks fully solved, capped at
  `WCST_MAX_CATEGORIES = 6`, matching the real WCST's own stopping rule)
  and perseverative errors (a wrong tap that matches the PREVIOUS rule
  instead of the current one - the classic WCST error-type distinction)
  alongside plain accuracy%, tracking best categories-completed per
  `wcstPrefs.length` (kurz/mittel/lang = 32/48/64 cards, the only client-
  facing setting, same "length, no natural difficulty dial" shape as
  Suchtest/UFOV/Hick/DSST, since the real WCST has no difficulty knob
  either - one fixed deck, one fixed rule cycle) via `WCST_BEST_KEY`.
  **Deliberately no background-colour Feineinstellung**, unlike most other
  Test-Bereich exercises: colour identity of the four reference/stimulus
  colours IS literally one of the three sorting rules here, the same
  category of concern that kept Wortfarben-Test/Stroop excluded from the
  background-colour rollout entirely - a tinted stage risks competing with
  exactly the dimension being judged whenever "Farbe" is the active
  (hidden) rule, so this exercise was left out of that rollout rather than
  silently deciding it's fine; also correctly excluded from
  `MASTER_BG_TARGETS` (the Master-Einstellungen cascading-default-
  background registry another session built the same day) for the same
  reason - it has no `bgColorKey` field to seed. No Bei-Fehler/
  Zusatzaufgabe/Trainingsmodus - correctly skipped, same reasoning as every
  other fixed-trial Test entry. Feedback reuses Simon-Test's own "colour-
  neutral ring" idea (a `box-shadow` ring, not a solid fill swap) precisely
  because the tapped card's own colour is part of the signal being judged,
  not something feedback should repaint over. Pause/resume uses the same
  scheduleXTimer-remaining-delay trick as every other Test entry (a no-op
  beyond blocking input and cancelling/replaying the brief post-tap
  feedback timer, since there's no background/timing state to freeze
  otherwise). New CSS is `.wcst-*` (fixed hex colours throughout, no
  `var(--...)`); a real layout bug caught and fixed before shipping (not by
  the test, by a screenshot check during manual verification): the shared
  `.wcst-card` base rule originally carried `flex:1`, intended only for the
  four reference cards sitting side-by-side in `.wcst-ref-row` - but the
  stimulus card below reuses the same `.wcst-card` class and, as the sole
  non-`flex:1`-intended flex child of the column-direction `.wcst-stage`,
  inherited that `flex:1` too and ballooned to fill nearly the entire
  remaining stage height (confirmed via `getBoundingClientRect`/a
  screenshot, not guessed) - fixed by moving `flex:1;min-width:0` to a
  `.wcst-ref-row .wcst-card` scoped rule instead of the shared base class.
  Test: `tests/wcst_test.py` (since the active rule is deliberately never
  exposed in the DOM by design, the test drives many trials cycling
  through all four reference cards and asserts on mechanics that ARE
  observable - both correct and wrong feedback occur, progress advances,
  pause/resume freezes the stage, the done-panel reports categories/
  perseverative-errors/accuracy - rather than asserting the hidden rule
  logic itself, which was verified by reading the code).
- **Ganzheit-Detail-Test (Navon-Aufgabe)** (twenty-fifth autonomous entry,
  2026-09-30): built from the "Recherche-Backlog: 20 Kandidaten" list
  (candidate #20) rather than fresh research this round. Grounded in the
  Navon task (Navon, 1977, "Forest before the trees") - a large ("global")
  letter is itself built out of many small ("local") letters; a cue
  ("GROSS"/"KLEIN") names which level to judge THIS trial, and the client
  taps H or S for that level's identity, ignoring the other one. When both
  levels happen to be the same letter that's "kongruent" (fast, accurate);
  when they conflict that's "inkongruent" (slower, more error-prone) - and
  the classic, endlessly-replicated finding this paradigm exists to
  surface is an ASYMMETRY ("global precedence"): an incongruent LOCAL
  level typically slows GLOBAL responses less than an incongruent GLOBAL
  level slows LOCAL responses - the visual system processes the overall
  shape before it processes the fine detail inside it. The big letter
  renders as a 5x7 dot-matrix grid (`NAVON_SHAPES`, hand-encoded bitmaps
  for H and S) with small letter glyphs placed only at the "on" cells -
  every glyph inside one trial shares the SAME local identity (that's what
  makes it read as one coherent shape at a glance), so a trial is fully
  described by `{globalLetter, localLetter, cuedLevel}`. Genuinely
  distinct from every existing Test/NAT mechanic: Suchtest varies feature
  vs. conjunction search across SEPARATE items on a display; Regelwechsel-
  Test switches between two semantic classification RULES applied to one
  bivalent digit; this is the only exercise where a SINGLE object carries
  the SAME kind of information (a letter identity) at two different
  perceptual SCALES at once, and the question is which scale gets
  processed more automatically - a genuinely different "level of
  processing" construct, not a rule-switch or a search. Fixed 32-trial run
  (`NAVON_TRIAL_COUNT`, the full 2 levels x 2 letters x 2 congruency
  factorial x 4 reps), shuffled with a guard against more than 3 identical
  cued levels OR more than 3 identical correct answers in a row (same
  shape as `buildTsTaskSeq`/`buildFlankerTrials`, extended to cover both
  variables at once here). Reports accuracy% plus average RT for each of
  the four cells (global/lokal x kongruent/inkongruent) and both
  interference costs (inkongruent minus kongruent RT, per level) as
  "Interferenz gro&szlig;"/"Interferenz klein" - the actual outcome
  measures this paradigm exists to reveal - plus a one-line note on which
  one came out bigger this particular run, tracking best accuracy% per
  `navonPrefs.difficulty` (leicht/mittel/schwer, controlling only the
  cue-stimulus interval and response window, same "preparation time is
  what matters" shape as Regelwechsel-Test's own `csiMs`-as-difficulty
  design) via `NAVON_BEST_KEY`. Background colour/intensity WAS included
  (`navonPrefs.bgColorKey`/`bgIntensity`, `makeBgApplier`/
  `wireBgIntensityControl` on both the ready screen and the pause overlay,
  plus a new `MASTER_BG_TARGETS` registry entry so the Master-
  Einstellungen cascading default reaches this exercise too, and a
  `bg-master-status` element on the ready screen matching every other
  Test-Bereich exercise's now-current shape) - basically free, and unlike
  the immediately-preceding Kartensortier-Test (where colour identity IS
  one of the sorting rules), colour plays no role in the Navon task at
  all, so a background tint behind the plain dark letter grid doesn't
  compete with anything being judged. No Bei-Fehler/Zusatzaufgabe/
  Trainingsmodus - correctly skipped, same reasoning as every other
  fixed-trial Test entry. Self-paced per trial with a safety-net timeout
  (`scheduleNavonTimer`, same always-clear-pending-timer pattern as
  Regelwechsel-Test/Suchtest/Hick) and the usual remaining-delay pause/
  resume. New CSS is `.navon-*` (fixed hex colours throughout, no
  `var(--...)`); correct/wrong feedback is a plain solid background swap
  on the tapped H/S button (Flanker/Posner/Regelwechsel-Test's
  convention), since these two buttons have fixed, never-changing labels
  with no colour-coding of their own to protect (unlike Simon-Test/
  Kartensortier-Test's colour-neutral ring, needed there because the
  tapped element's OWN colour is part of the judged signal). Test:
  `tests/navon_test.py`.
- **Iconic-Speicher-Test (Partial-Report-Aufgabe)** (twenty-sixth
  autonomous entry, 2026-09-30): built from the "Recherche-Backlog: 20
  Kandidaten" list (candidate #1) rather than fresh research this round.
  Grounded in Sperling (1960) - the classic partial-report paradigm
  establishing iconic (sensory) visual memory: a grid of characters
  flashes for a very brief, near-subliminal duration, then after a
  variable post-stimulus delay a cue marks which portion to report; the
  hallmark finding is that partial-report accuracy at short delays is far
  higher than whole-report accuracy would predict, but decays sharply as
  the delay grows - revealing a large-capacity sensory store that fades
  within roughly a second. This exercise reproduces exactly that: a 3x3
  grid of digits (`ICONIC_GRID_ROWS`/`ICONIC_GRID_COLS`, a full 1-9
  permutation into the 9 cells so every recall is unambiguous) flashes for
  `ICONIC_DIFFICULTIES[difficulty].flashMs` (leicht/mittel/schwer =
  300/200/120ms - only the flash duration is difficulty-adjustable, since
  the post-stimulus delay itself is the fixed scientific manipulation,
  same "difficulty controls encoding, not the independent variable" shape
  as Vorlaufzeit-Test's own foreperiods), then blanks; after
  `ICONIC_DELAYS_MS = [0, 300, 700, 1000]` (Sperling's own tested range,
  stepped across trials, 6 reps each = 24 total, shuffled with a
  same-delay-max-3-in-a-row guard) one of the three rows gets a border
  outline, and the client taps that row's three digits (only, the other
  six are irrelevant) via a 9-key keypad + 3 answer boxes (mirroring
  Flash Speicher Test/DSST's own answer-box+keypad convention). Reports
  overall accuracy% plus, critically, accuracy BROKEN OUT PER DELAY in the
  done-panel (`finalizeIconicRun`'s `perDelayText`, e.g. "0ms: 82% ·
  300ms: 61% · 700ms: 45% · 1000ms: 38%") - the actual decay curve this
  paradigm exists to reveal, not a single average; scored per-trial as a
  SET match (how many of the 3 typed digits belong to the cued row's true
  3, order-independent, `hits/3` as a fraction averaged within each delay
  bin) rather than requiring exact left-right positional order, matching
  Sperling's own "number of items correctly reported" metric more closely
  than a strict-sequence convention would. `ICONIC_BEST_KEY` tracks best
  OVERALL accuracy% per difficulty (higher is better, standard shape).
  **One deliberate, disclosed adaptation from the original**: Sperling's
  own experiments cued the row with an auditory TONE (high/mid/low pitch)
  specifically so a second visual event never disturbs the fading icon;
  this version instead highlights the cued row's own on-screen border (a
  plain teal outline, `.iconic-row.cued`, no colour semantics involved) -
  a well-established modern-replication substitute for a tone in a
  quiet-audio-unfriendly coaching/gym setting, called out honestly in the
  client-facing ready-screen copy rather than silently claiming an
  auditory cue that isn't actually there. Genuinely distinct from every
  existing Test/NAT memory mechanic: Merkspanne-Test (Luck & Vogel
  change-detection) shows its array at NORMAL, non-subliminal speed and
  asks one global same/different judgment; Flash Speicher Test recalls a
  SEQUENTIAL stream of individually-flashed characters, one at a time;
  Blitz-Raster/Remember show several simultaneous positions with no time-
  pressure decay curve at all - this is the only exercise flashing a
  WHOLE array at once for a near-subliminal duration and probing raw
  sensory-store DECAY via a post-hoc partial cue, a genuinely earlier
  stage of visual memory (iconic/pre-attentive, decaying within ~1
  second) than anything else built so far, which all operate on working
  memory (holding items for many seconds to make a decision). Deliberately
  no background-colour Feineinstellung: the study flash is shown for as
  little as 120ms, the same "legibility during a brief flash matters more
  than usual" reasoning that already kept Sofortmengen-Test/Subitizing out
  of the background-colour rollout - a tint would work against the
  flash's own contrast exactly when it matters most. No Bei-Fehler/
  Zusatzaufgabe/Trainingsmodus - correctly skipped, same reasoning as
  every other fixed-trial Test entry. Self-paced answer phase (typing
  advances the instant 3 digits are entered) with a generous
  `ICONIC_ANSWER_TIMEOUT_MS = 7000` safety-net timeout for an unanswered
  trial, same always-clear-pending-timer pattern as every other self-paced
  Test entry; pause/resume uses the standard remaining-delay replay trick.
  New CSS is `.iconic-*` (fixed hex colours throughout, no `var(--...)`);
  the grid/answer-boxes/keypad are all built dynamically via JS
  (`iconicRenderGrid`/`iconicRenderAnswerBoxes`/`iconicRenderKeypad`)
  rather than static HTML, since which cells show digits and which row is
  outlined both change every phase of every trial. Test:
  `tests/iconic_test.py`.
- **Daueraufmerksamkeits-Test (Psychomotor Vigilance Task)** (twenty-
  seventh autonomous entry, 2026-09-30): built from the "Recherche-
  Backlog: 20 Kandidaten" list (candidate #14) rather than fresh research
  this round. Grounded in the Psychomotor Vigilance Task (PVT; Dinges &
  Powell, 1985) - the gold-standard sustained-attention/fatigue measure
  used throughout sleep-deprivation and vigilance research: a simple
  stimulus appears at pseudo-random 2-10s intervals with NO warning cue of
  any kind, over a sustained run; the client taps as fast as possible each
  time. "Lapses" (RT > 500ms, `PVT_LAPSE_THRESHOLD_MS`) accumulate
  measurably as time-on-task and fatigue build, and mean RT typically
  rises across the run (the "vigilance decrement") - famously sensitive to
  sleep loss, but also to plain sustained boredom/fatigue in an otherwise-
  rested person, which is the relevant read for a training-app context.
  The classic display is a millisecond counter that starts at the
  stimulus and counts up until stopped - reproduced exactly (`.pvt-
  display`, driven by `requestAnimationFrame`, not a colour change or
  shape), since the counting number itself is part of what makes the real
  PVT so simple and distraction-free. Durations offered (`PVT_LENGTHS`,
  kurz/mittel/lang = 3/5/10 Min) span the full classic 10-minute protocol
  down to genuinely validated ABBREVIATED versions - Basner, Mollicone &
  Dinges (2011, Acta Astronautica) validated 3- and 5-minute PVT-B forms
  against the full 10-minute original specifically for time-constrained/
  field use, so "Kurz"/"Mittel" aren't arbitrary shortenings, they're an
  established, cited protocol in their own right. Genuinely distinct from
  every existing Test/NAT mechanic: every other RT-based exercise here
  (Go/No-Go, Flanker, Posner, Simon, Rotationstest, Stopp-Signal-Test, ...)
  is a short, fixed-trial block (24-64 trials, a few minutes) measuring a
  momentary cognitive facet (inhibition/conflict/switching); this is the
  only one whose entire point is a SUSTAINED, MANY-MINUTE run measuring
  attentional DECAY over time-on-task itself - directly relevant to
  fatigue/overtraining monitoring in a coaching context, and a genuinely
  different construct (vigilance, not decision speed) from anything else
  on this tab. A tap during the "waiting" phase (before the counter
  starts) is a false start/anticipation, logged separately and never
  cancels the already-scheduled, genuinely random stimulus onset - a
  client "gaming" the wait can't shorten it. Reports overall mean RT,
  lapse count/rate, false-start count, and the actual outcome measure this
  paradigm exists to reveal: the "Vigilanz-Abfall" (mean RT of the second
  half of the run's trials minus the first half) - positive means
  responses genuinely slowed as the run went on, the classic decrement.
  `PVT_BEST_KEY` tracks the LOWEST overall mean RT per length (lower is
  better), but ONLY for a run that reached the FULL selected duration (not
  an early "Beenden") - a short stopped run could otherwise report an
  unrepresentatively fast mean RT and overwrite a genuinely earned record,
  the same class of concern already flagged for Reaktionsfeld-Test's own
  rate metric in Offene Fragen; this exercise avoids it outright by gating
  on a full finish rather than flagging it as a known gap. No Bei-Fehler/
  Zusatzaufgabe/Trainingsmodus/difficulty dial - correctly skipped, same
  reasoning as every other fixed-duration Test entry (the ISI range and
  lapse threshold are the fixed scientific protocol, not something to make
  easier/harder). Background colour/intensity WAS included (`pvtPrefs.
  bgColorKey`/`bgIntensity`, `makeBgApplier`/`wireBgIntensityControl` on
  both the ready screen and the pause overlay, plus a `MASTER_BG_TARGETS`
  registry entry) - basically free, and a tint behind the plain counting
  number doesn't compete with anything being judged (unlike Subitizing-
  Test/Iconic-Speicher-Test, where a near-subliminal flash's own contrast
  is what's at stake). Pause needs two different resume tricks depending
  on which phase was active, unlike every earlier self-paced Test entry:
  pausing during the "waiting" phase uses the usual `scheduleXTimer`-
  remaining-delay replay (there's a pending ISI timer); pausing during the
  "target" phase (the counter is actively running) additionally cancels
  the `raf` loop and shifts `targetShownAt` forward by the paused span on
  resume - the same "shift the timestamp, not the elapsed reading" trick
  used elsewhere in this app for a mid-flight measurement (MOT's physics
  tick, Periph's `session.startTime` shift) - so a pause mid-count never
  corrupts the eventual reaction time. Test: `tests/pvt_test.py` (the
  actual full-duration finish path and its best-score gate aren't
  exercised by real-time waiting - a 3/5/10-minute wait is impractical in
  a Playwright run, the same "verified by reading the logic" approach
  already used for UFOV's own staircase numerics - the test instead
  exercises every other mechanic: the counting display, the false-start
  handling, pause/resume across both phases, Beenden-doubles-as-finish,
  and length persistence).
- **Linienhalbierungs-Test (Line Bisection)** (twenty-eighth autonomous
  entry, 2026-10-01): built from the "Recherche-Backlog: 20 Kandidaten"
  list (candidate #3) rather than fresh research this round. Grounded in
  the line bisection test (Schenkenberg, Bradford & Ajax, 1980, Neurology
  - standardised neuropsychological scoring for the classic clinical
  task) and the "pseudoneglect" literature in healthy people (Bowers &
  Heilman, 1980, Neuropsychologia - normal, non-brain-damaged individuals
  reliably bisect slightly LEFT of true centre on average, attributed to
  right-hemisphere dominance for spatial attention; the bias is also
  known to be sensitive to attentional load and fatigue, not just a fixed
  trait). A plain horizontal line of varying length and varying screen
  position appears; the client taps where they judge its exact centre to
  be - no further instruction, no right/wrong feedback per trial (classic
  bisection tests never correct the client mid-session, since revealing
  the true centre would let them consciously override the very automatic/
  implicit bias being measured, destroying the point of a multi-trial
  average). Scored as the standard literature metric: deviation as a
  percentage of HALF the line's length, so trials of different lengths
  stay comparable - negative = tapped left of centre, positive = tapped
  right, a sign convention lifted directly from the bisection literature
  itself, not invented here. Genuinely distinct from every existing Test/
  NAT mechanic in two ways at once: (1) it is the ONLY exercise on this
  whole tab that collects NO reaction time at all - every other exercise's
  outcome is either an accuracy/correctness judgment or a speed
  measurement (occasionally both), this one is a pure spatial accuracy/
  bias measurement with the stimulus staying up indefinitely until
  tapped; and (2) its outcome is a SIGNED spatial bias (which direction a
  client tends to misjudge toward), not a reaction time, an accuracy%, or
  a recalled set - no other exercise reports a directional tendency like
  this. `BISECT_LENGTHS_PX = [140, 220, 300]` (three distinct lengths,
  matching the real test's own multi-length protocol) combined with a
  RANDOMISED horizontal start position every trial (not always centred on
  the screen) - a deliberate anti-strategy measure: if the line were
  always centred on the stage, "tap the middle of the screen" would
  trivially solve the task without the client ever needing to actually
  look at the line's two endpoints, which would make the whole
  measurement meaningless. `bisectPrefs.length` (kurz/mittel/lang =
  9/12/18 trials, 3/4/6 reps of each of the 3 line lengths) is the only
  client-facing setting, same "length, no natural difficulty dial" shape
  as Suchtest/UFOV/Hick/DSST - there's no sensible "harder" version of
  this task beyond a longer session for a more stable average. Reports
  the mean signed deviation% (the actual "Aufmerksamkeits-Tendenz" this
  paradigm exists to reveal, with a plain-language direction note: "eher
  nach links" / "eher nach rechts" / "sehr ausgeglichen" under a small
  ±2% dead zone) plus the mean ABSOLUTE deviation% as a measure of overall
  precision regardless of direction. `BISECT_BEST_KEY` tracks the LOWEST
  mean absolute deviation% per length (lower is better, i.e. "most
  balanced attempt so far" - phrased in the UI as exactly that, not as a
  skill score, since this is a bias measurement, not a trainable
  high-score game). No Bei-Fehler/Zusatzaufgabe/Trainingsmodus -
  correctly skipped, same reasoning as every other fixed-trial Test
  entry; there is also no "wrong answer" concept at all here for Bei-
  Fehler to apply to. Self-paced per trial with NO response timeout of
  any kind (unlike every other self-paced exercise on this tab) - the
  real bisection test never pressures the client to hurry, since rushing
  would itself introduce a confound into a task that's supposed to
  measure automatic spatial perception, not decision speed under
  pressure. Background colour/intensity WAS included (`bisectPrefs.
  bgColorKey`/`bgIntensity`, `makeBgApplier`/`wireBgIntensityControl` on
  both the ready screen and the pause overlay, plus a `MASTER_BG_TARGETS`
  registry entry) - basically free, and a tint behind a plain line
  doesn't compete with the purely positional judgment being made. The
  line/tap-mark render inside `.bisect-area`, a fixed-height
  `position:relative` sub-box (not a full-stage absolute overlay) - same
  "smaller sub-box, well clear of the top hint by construction"
  convention already used for Merkspanne's `.merk-field`, so
  `stageTopClearanceY()` doesn't apply here either, by the same
  reasoning. Test: `tests/bisect_test.py`.
- **Kippbild-Test (Necker-Würfel)** (twenty-ninth autonomous entry,
  2026-10-01): grounded in the classic multistable-perception paradigm
  around the Necker cube (Necker, L.A., 1832, "Observations on some
  remarkable phaenomena seen in Switzerland..." - the first documented
  description of a line drawing whose perceived 3D orientation
  spontaneously flips under completely unchanged visual input) and the
  broader bistable-perception literature studying how such reversals occur
  over time (e.g. Borsellino et al., 1972, finding reversal timing follows
  a roughly random process rather than a fixed rhythm). A plain wireframe
  cube - two offset squares connected by four diagonal edges, every line
  drawn identically, with no shading or occlusion cue favouring either
  interpretation - is shown continuously for the whole run; the image
  itself never changes at all. The client simply taps once every time
  their own perceived orientation of the cube flips. Two modes are offered
  (`kippbildPrefs.mode`): "Neutral beobachten" (just observe and tap) and
  "Bewusst verlangsamen" (deliberately try to slow the reversals down) -
  research following up on Necker's own observation that attention/
  intention can bias reversal rate to some degree (though never fully
  suppress it) treats voluntary control as a genuine, separate condition
  worth comparing against a neutral baseline, not just a label change.
  Genuinely distinct from every existing Test/NAT mechanic, in fact the
  single most distinct entry on this whole tab: this is the ONLY exercise
  whose physical stimulus never changes at all for the entire run - every
  other exercise's "event" is something appearing, moving, lighting up, or
  changing on screen; here the event being counted is a purely internal,
  spontaneous perceptual switch with no external trigger whatsoever.
  `kippbildPrefs.length` (kurz/mittel/lang = 45/60/90s) is the only other
  client-facing setting. Reports total reversals and reversals/minute (a
  rate, not a raw count, so different lengths stay comparable - same
  reasoning as Reaktionsfeld-Test's own Treffer/Min). **Deliberately NO
  best-score tracking, unlike every other Test exercise** - the featured
  card has no `.fc-meta` element at all: a reversal rate is a measure of
  an individual, largely involuntary perceptual trait, not a skill with a
  "better" direction, and a client could trivially "win" a tracked record
  with a flurry of fast meaningless taps while actually defeating the
  whole point of the measurement - the same concern Linienhalbierungs-
  Test's own Offene-Fragen entry already raised about forcing a best-score
  onto a trait measurement, resolved here by simply not building one
  rather than building one and then flagging doubt about it. No Bei-Fehler
  (there is no wrong answer - every tap is simply logged), no
  Zusatzaufgabe/Trainingsmodus - correctly skipped per the "optional, skip
  what doesn't fit in an hour" guidance. Background colour/intensity WAS
  included (`kippbildPrefs.bgColorKey`/`bgIntensity`, `makeBgApplier`/
  `wireBgIntensityControl` on both the ready screen and the pause overlay,
  plus a `MASTER_BG_TARGETS` registry entry) - basically free, and a tint
  behind the cube's own fixed-hex outline doesn't compete with anything
  being judged (the task is about perceived 3D orientation, not colour or
  contrast). Uses a single duration-based end timer (the same
  `scheduleXTimer`-remaining-delay pause/resume trick as every other Test
  entry) rather than per-trial scheduling, since there are no trials at
  all - just one continuous observation window; a live status line ("N
  Wechsel · Ms") updates 4x/second via a plain `setInterval` that simply
  skips its own update while paused, freezing the display for free with no
  extra pause-specific logic needed. "Beenden" doubles as Finish once at
  least `KIPPBILD_MIN_PLAYED_S` (8s) have actually elapsed - below that
  there usually hasn't been enough time to notice even one natural
  reversal, so an accidental immediate Beenden doesn't produce a
  misleadingly empty "0 Wechsel" result. **A real layout bug caught and
  fixed during manual verification, not by the test (the test was written
  afterward to cover it)**: at 390px width the player-bar's four items
  (Beenden/Pause/the status pill/Vollbild) don't fit on one row and wrap to
  two, the same class of bug this file already documents for MOT's own
  status pill - but unlike a brief per-trial instruction, this exercise's
  hint stays visible for the ENTIRE run, and `.remember-hint`'s fixed CSS
  `top:68px` offset (sized for a one-row bar) left it rendering partially
  underneath/behind the wrapped second row for the whole exercise, not
  just briefly. Fixed with `kippbildPositionHint()`, which reads the bar's
  own live `getBoundingClientRect().bottom` and sets the hint's inline
  `top` just below it - recomputed on every status tick (not just once at
  start), since the shrinking "remaining seconds" text can itself un-wrap
  the bar from two rows back to one as a run winds down toward single
  digits, and the hint needs to track that back upward too, not just move
  down once. `tests/kippbild_test.py` asserts the two elements' rendered
  rects never actually overlap, rather than trusting a fixed offset.
  Test: `tests/kippbild_test.py`.

- **Jedes Auge zählt (Farbbrille)** (2026-10-08, built on Fabian's request,
  not by the Routine): red-green anaglyph glasses; on a black stage dots
  appear one at a time in the calibrated red or green, so only one eye sees
  each; tap it; result per eye (found/shown, mean time) plus one neutral
  sentence. Needs the shared Farbbrille settings + mandatory calibration in
  the Grundeinstellungen (`fwmc-anaglyph-v1`, `#anaglyphCalib`,
  `anaglyphGate`/`anaglyphStart`) and shows the pre-start brightness/Night
  Shift/True Tone hint. Everything in docs/notes/30-farbbrille.md. Test:
  `tests/farbbrille_1008_test.py`.

- **Ton-Sequenz** (2026-10-08, built on Fabian's request, not by the
  Routine): a tool, not a scored test - tones on the left/right/both ears as
  a sequence of steps (frequency 20-2000 Hz, Sinus/Dreieck/Rechteck,
  Dauerton/Puls/Gleiten, Wechsel, pause 0-180 s, repeats, max 10 min),
  Kanal-Test, Frequenz-Suchlauf with "Merken", presets Referenz 500/100 Hz
  and Seitenvergleich L/R only, Vorher/Nachher note in the history, safety
  note "Training, keine Therapie". Grounded in the research file
  /mnt/project-files/app/recherche/ton-sequenzen-2026-10-08.md (VEMP
  reference frequencies; no effect claims). Everything in
  docs/notes/34-ton-sequenz.md. Test: `tests/ton_sequenz_1008_test.py`.

### Offene Fragen (uncertain items for the client to weigh in on)

- **Linienhalbierungs-Test: no "best" concept really fits a bias
  measurement, and the trial count is modest**: `BISECT_BEST_KEY` tracks
  the lowest mean ABSOLUTE deviation% as "ausgeglichenster Wert" - a
  reasonable "most balanced attempt" framing, but genuinely debatable
  whether a bias-measurement task should have a trackable "best" at all
  (a client could, in principle, learn to deliberately aim slightly off
  from their own natural bias to "beat" their own record, which would
  undermine the whole point of measuring an automatic tendency - the same
  category of worry the real clinical version avoids entirely by never
  gamifying it). Kept it anyway for consistency with every other Test
  entry's own best-score convention, and because a client curious about
  genuinely IMPROVING their spatial balance over time is a legitimate use
  case too, not just a diagnostic one-off. Separately, at 9/12/18 trials
  split across 3 line lengths, each length only gets 3-6 reps - enough for
  a readable OVERALL mean but not really enough to say anything reliable
  about whether the bias changes with line length specifically (not
  currently broken out per length in the done-panel at all). Not fixed -
  flagging rather than guessing: ask the client whether the "Bestleistung"
  framing should be dropped entirely in favour of just showing trend
  history, or whether a per-length breakdown would be worth adding.
- **Iconic-Speicher-Test: only 6 trials feed each delay bin**: 24 trials
  split across 4 delays (0/300/700/1000ms) means each reported per-delay
  accuracy% rests on just 6 trials - a genuinely small sample that can
  look noisy on any single run, the same category of caveat already
  flagged for Doppelziel-Test's per-lag sample size and Ganzheit-Detail-
  Test's per-cell sample size just above. Kept small deliberately so a run
  stays quick. Separately, unlike Sperling's own classic scoring, this
  version credits a typed digit as correct whenever it belongs to the
  cued row's set at all, regardless of which of the 3 positions it was
  typed into (a set match, not a left-right positional match) - a
  simplification chosen since order was never the point of THIS
  paradigm's classic finding (the decay curve), but worth flagging as a
  deliberate scoring choice rather than an oversight. Not fixed - flagging
  rather than guessing: ask the client whether the done-panel should note
  either of these ("kleine Stichprobe pro Wartezeit" / "Zahlen zählen auch
  bei anderer Reihenfolge"), or whether trial count should go up.
- **Daueraufmerksamkeits-Test: invented response-timeout + browser timing
  precision**: `PVT_RESPONSE_TIMEOUT_MS = 10000` (a stimulus that's never
  tapped within 10s counts as a "Verpasst" lapse and the run moves on) is
  this app's own safety net, not derived from the PVT literature - the
  real protocol's own convention for an extremely delayed/absent response
  is a "sleep episode" at the 30s mark, and doesn't otherwise force a move
  on. 10s was chosen so the exercise can never get stuck waiting forever
  on a distracted client, but it's an invented number, not a validated
  one - flagging rather than presenting it as protocol-accurate. Separately,
  like UFOV's own flagged timing-precision caveat, the counting display
  and the tap that stops it are both ordinary browser events
  (`requestAnimationFrame`/`click`), not calibrated lab hardware - real
  touchscreen input lag (commonly cited in the 50-100ms range depending on
  device) sits on top of every recorded RT here, so the ABSOLUTE numbers
  this exercise reports likely run a bit slower than a lab-grade PVT
  instrument would show for the same person; the RELATIVE pattern within
  one run (the vigilance decrement, lapses accumulating over time) should
  still be meaningful, since that same lag affects every trial equally.
  Not fixed - flagging rather than guessing: ask the client whether this
  matters for how the numbers get presented, or whether the response
  timeout should be lengthened toward the real protocol's 30s convention.
- **Ganzheit-Detail-Test: small per-cell sample size**: 32 trials split
  across 4 cells (global/lokal x kongruent/inkongruent) means only ~8
  trials feed each cell's average RT, so both interference-cost numbers
  (and the "which one is bigger" note) rest on a genuinely small sample
  and can look noisy - or even point the "wrong" direction by chance - on
  any single run, the same category of caveat already flagged for
  Doppelziel-Test's per-lag sample size. Kept small deliberately so a run
  stays quick, matching this app's "test, not a 20-minute lab session"
  shape. Not fixed - flagging rather than guessing: ask the client whether
  the done-panel should note this is "ein erster Hinweis, über mehrere
  Durchläufe stabiler" the same way Doppelziel-Test's own note already
  does, or whether the trial count should simply go up.
- **Kartensortier-Test: streak threshold and "unambiguous card" scoring
  are both simplifications versus the standardised WCST protocol**: the
  real test requires 10 consecutive correct matches per category (this
  version uses 6, so "Kategorien geschafft" here isn't directly comparable
  to a published WCST category count), and it deliberately never generates
  a card where two or three dimensions point at the same reference card
  (the real deck contains some of these; the standard protocol scores them
  too, just treats them as informative rather than diagnostic in a
  slightly different way) - both chosen to keep a run genuinely playable
  in a training-app session rather than the real test's much longer
  administration. Not fixed - flagging rather than guessing: ask the
  client whether the done-panel should note "vereinfachte Fassung, nicht
  direkt mit dem klinischen WCST vergleichbar", or whether a future pass
  should move closer to the standard 10-in-a-row criterion for a more
  directly comparable category count.
- **Wortfarben-Test overlaps with Visual Training's existing "Stroop ·
  klassisch"/"Stroop · mit Hintergrund"**: same core paradigm (colour-word
  Stroop interference), different mechanic (VT: spoken, unscored, timed
  drill; Test-Bereich: tapped, scored, trial-based test with an actual
  Stroop-effect-in-ms readout) - see the correction note just above this
  list. Worth asking directly: does a scored/quantified version add real
  value next to the existing spoken drill, or does having "Stroop" appear
  in two different places (Visual Training AND Test) read as redundant/
  confusing on the home screen? If the client would rather not keep both,
  this is the one entry in the whole Test-Bereich series to reconsider
  removing rather than any of the others. **Decided 2026-10-02: keep
  both.**

- **Regelwechsel-Test: congruency not separately analysed**: because the
  stimuli are deliberately bivalent (every digit is a valid input to both
  rules, the classic design), some trials are "congruent" (both rules
  would point to the same response side for that digit) and some
  "incongruent" (the two rules disagree) - real task-switching studies
  often find congruency effects layered on top of the pure switch cost,
  and an unbalanced sample of congruent vs. incongruent trials within
  switch/repeat could shift the reported "Wechselkosten" number somewhat
  either way on a given run. Not tracked or balanced here - a genuine
  simplification versus the full Rogers & Monsell/Meiran design, kept out
  to fit the build in an hour. Flagging rather than guessing: ask the
  client whether a future pass should track/report congruency separately,
  or whether the current single switch-cost number is good enough for a
  training tool (as opposed to a lab-grade measurement).

- **Blockspanne-Test single-trial-per-length scoring** (RESOLVED
  2026-10-02, Fabian: "wie Standard" - every length now has two sequences,
  the run goes on while at least one of them is correct and ends when both
  fail; the done panel also counts correct sequences; the text below is
  the original note): this version ends a
  run on the very first wrong tap at any given sequence length, so the
  reported "Blockspanne erreicht" is the longest sequence recalled in one
  unbroken climb - a simplification of Kessels et al. (2000)'s own
  standardised protocol, which gives 2 trials per length and only stops
  after BOTH fail (more forgiving of one unlucky mis-tap, and closer to a
  clinically comparable span score). Chosen to keep a run quick and the
  build within scope, matching a pattern some digital Corsi adaptations
  also use - but the number this app reports isn't directly comparable to
  a published Corsi-span norm (e.g. Kessels' own 6.2 average). Not fixed -
  flagging rather than guessing: ask the client whether the done-panel
  should note this ("dein Ergebnis aus einem einzigen Durchlauf, nicht der
  Standard-Testwert"), or whether a future pass should move to the
  2-trials-per-length stop rule for a more directly comparable number. A
  backward-recall variant (client reproduces the sequence in REVERSE
  order, the classic paired variant of this task, thought to load more on
  active manipulation than pure storage) was also not built - flagging as
  a natural next step if this exercise is well received, not built without
  being asked given the "one exercise per hour" pace this section runs at.

- **Suchtest safety-net timeout + "ms/Objekt" wording**: an unanswered
  trial only times out after 8 seconds (`SEARCH_TIMEOUT_MS`) - a rough,
  ungrounded safety net (not derived from any published visual-search
  protocol), chosen just so a genuinely self-paced "search until found"
  task never hard-blocks progress if the client gets stuck; on "schwer"
  Verbindungssuche at 18 items an honest search can plausibly take several
  seconds anyway, so this may still feel long or short in practice - not
  tuned against real client data yet. Separately, the done-panel reports
  a raw "ms/Objekt" slope number per search type, which is the technically
  correct outcome measure but may read as jargon to a non-technical
  client without a short explanatory line (something like "je niedriger,
  desto eher siehst du es auf einen Blick") - flagging rather than
  guessing at friendlier copy.
- **Merkspanne-Test study-exposure duration**: shown for 500ms per the
  implementing run's choice, a compromise versus the literature's much
  shorter (~100ms) flashes, chosen for `setTimeout` reliability on phones -
  same reasoning already documented below for UFOV's timing precision.
  Not fixed, just flagged.

- **UFOV timing precision on real devices**: the exposure-duration
  staircase steps in 33ms increments down to a 33ms floor, driven by plain
  `setTimeout`. On a loaded/low-end phone browser, actual paint timing can
  lag behind a `setTimeout` callback by a frame or more, so the shortest
  exposures may run a bit longer in practice than the number shown implies
  - the *relative* difficulty ordering (shorter requested duration = harder)
  should still hold, but the reported "Schwelle" in ms is likely somewhat
  optimistic versus a lab-grade, frame-locked UFOV implementation. Not
  fixable without moving the render loop onto `requestAnimationFrame`
  frame-counting (like MOT's physics tick) instead of `setTimeout` - felt
  like more than an hour's scope for a first version; flagging rather than
  silently shipping it as if it were precise. Ask the client whether this
  matters for how the score gets presented/interpreted, or whether a future
  pass should move it onto rAF frame-counting for real single-frame
  precision.
- **UFOV response order**: the real UFOV divided-attention subtest doesn't
  mandate an answer order between its two judgements; this version always
  asks "which shape" before "where was the target" (a fixed sequence, for a
  simpler one-thing-at-a-time phone UI). This shouldn't change what's being
  measured (both judgements are made from the same single glance, before
  either question appears), but flagging in case the client would rather
  see them combined into one screen, or the order reversed.
- **Posner-Cueing SOA range at "Leicht"**: `POSNER_DIFFICULTIES.leicht` uses
  a 450-650ms cue-target gap (SOA). Classic exogenous/peripheral-cueing
  literature (Posner & Cohen, 1984) reports that the cueing *benefit* can
  invert into inhibition-of-return (invalid trials becoming FASTER than
  valid ones) once cue-target SOA passes roughly 300ms for this kind of
  reflexive, box-brightening cue - so "Leicht" sits partly inside a range
  where the reported "Umlenkungs-Kosten" could theoretically come out
  negative instead of just smaller, which would read oddly in the done-
  panel summary. "Mittel" (250-400ms) and "Schwer" (100-200ms) stay
  comfortably inside the facilitation range where this doesn't apply. Not
  fixed - flagging rather than guessing at a resolution: ask the client
  whether "Leicht"'s SOA should be compressed to stay safely under ~300ms,
  or whether an occasional negative value is fine to leave as-is (a real,
  if initially surprising, part of how attention actually works) with just
  a clarifying note in the UI copy.
- **Doppelziel-Test per-lag sample size**: each lag (1/3/8) only gets 6
  T2-present trials per run, and the reported per-lag T2 accuracy is
  further restricted to the subset where T1 was also correctly identified
  - so a single run's per-lag percentages (and therefore the
  "Aufmerksamkeitslücke" difference) rest on a genuinely small, sometimes
  very small (occasionally 2-3, once in a while 0) number of trials, and
  can look noisy or even point the "wrong" direction by chance on any one
  run. Kept small deliberately so a full run stays quick, matching this
  app's "test, not a 20-minute lab session" shape - but not validated
  against repeated real-client runs to see how stable the numbers actually
  are in practice. Flagging rather than guessing at a fix: ask the client
  whether the done-panel should say something like "vorläufig, spielt es
  ein paar Mal für ein stabileres Bild" instead of presenting the numbers
  as if a single run were conclusive, or whether trial count should simply
  go up (at the cost of a longer session).
- **Reaktionsfeld-Test: three simplifications versus the real Dynavision
  D2 protocol**: (1) the real device places lights at 64 FIXED physical
  positions across 5 concentric rings with known, published radii; this
  phone version instead lets a light land at any continuous point and uses
  a single guessed threshold (`REAKT_CENTRAL_RADIUS_FRAC = 0.4` of the
  stage's half-diagonal) to call it "zentral" vs. "peripher" - not derived
  from the device's actual ring-size proportions, since that geometry wasn't
  looked up. (2) The "next light must land at least `minJumpFrac` away from
  the current one" rule is this app's own addition (to force genuine
  scanning across the whole field), not something the source literature
  describes the device itself enforcing - the real board just lights a
  random one of its 64 positions, which could occasionally repeat a nearby
  spot. Both are reasonable-seeming design choices but genuinely invented,
  not verified against the published device geometry - flagging rather than
  presenting either number as device-accurate. (3) The done-panel's
  "Treffer/Min" rate is computed from actual played time with only a 1-
  second floor (`Math.max(1000, ...)`), so a run stopped (Beenden) after
  just one or two very fast hits can show an inflated, unrepresentative
  rate (e.g. "60 Treffer/Min" from a single 1-second hit) that could
  overwrite a genuinely earned best score. Not fixed - flagging rather than
  guessing at a minimum-played-time gate: ask the client whether an early
  Beenden should require some minimum played time (e.g. 10s) before it's
  allowed to count toward the best score, or whether the done-panel should
  just avoid emphasising the rate number this prominently on a very short
  stopped run.
- **Wahlreaktionstest block order + slope sample size**: blocks always run
  ascending 2→4→8, never randomised/counterbalanced - real Hick's Law
  studies sometimes counterbalance block order across sessions to separate
  the choice-count effect from a plain practice/warm-up effect (RT often
  drops a little just from getting into rhythm, independent of N); this
  version can't distinguish "harder because more choices" from "harder
  because it's later in the run" within a single sitting. Separately, on
  "Kurz" (3 reps/position) the slope rests on only 6 correct RTs at N=2 and
  24 at N=8 - workable but not a lot, so an unlucky/lucky handful of trials
  can shift the reported ms/Bit number more than a longer "Lang" run would.
  Not fixed - flagging rather than guessing: ask the client whether block
  order should rotate across repeated sessions, or whether the done-panel
  should note the slope is "a first estimate, more stable over several
  runs" the same way Doppelziel-Test's per-lag note already does.
- **Gegenrichtungs-Test: fixed Pro-then-Anti block order**: the Pro block
  always runs first, then Anti, never counterbalanced - so a slower/less
  accurate Anti block can't be cleanly separated from a plain fatigue/
  practice-order effect within a single run (same limitation already
  flagged for Wahlreaktionstest's own fixed 2→4→8 order, and the reason
  real antisaccade studies sometimes counterbalance block order across
  sessions). Chosen because Pro-first also usefully doubles as a baseline/
  warm-up before the harder instruction, matching common manual-
  antisaccade administration - but the reported "Hemm-Kosten" number isn't
  perfectly clean of order effects on any single run. Not fixed - flagging
  rather than guessing: ask the client whether block order should
  alternate across repeated sessions (client-side, e.g. via a stored
  toggle), or whether the done-panel should simply note the number is "an
  estimate, most meaningful averaged over several runs" like several other
  exercises here already do.
