# Established patterns worth reusing

- **`stageTopClearanceY()` - shared top-clearance for full-stage exercises
  (added 2026-09-27)**: real bug report (screenshot: Trail Making's
  instruction text clipped off both edges of an iPhone screen, with
  markers rendered right up against the top bar). Every exercise whose
  stage fills the WHOLE player from y=0 (`.remember-stage/.trail-stage/
  .search-stage/.corsi-stage/.reakt-stage/.mot-objects{inset:0}`, all
  `flex:1;position:relative`, as opposed to Merkspanne's/Blitz-Raster's/
  Anti's smaller normal-flow sub-box that's centred well clear of the top
  by construction) has the instruction hint (`.remember-hint`) and the
  player-bar floating on top via z-index - their own `*StageBounds()`
  functions each had a hardcoded pixel `minY` that couldn't account for
  wrapped-hint height (varies with instruction length) or safe-area notch
  size (varies per device). Fixed with a shared helper, `stageTopClearanceY
  (stageRect, hintEl, barEl, fallbackMinY, halfSizePx, marginPx=16)`
  (defined near `focusFirstIn`/`trapTabKey`): measures the hint's AND
  bar's actual live `getBoundingClientRect().bottom`, adds the marker's own
  `halfSizePx` (it's centred via `translate(-50%,-50%)`, so its rendered
  top edge sits `halfSizePx` above whatever "centre" constraint you clamp
  to - **forgetting this `halfSizePx` term was the bug's second, sneakier
  half**: markers still visually overlapped the hint by exactly
  `halfSizePx - marginPx` even after switching to live measurement, and
  since it only happens for markers whose random draw lands near that
  boundary, a single Playwright run easily missed it - caught only by
  re-running the same test many times) plus a safety margin, and returns
  that as the exercise's `minY`. Applied to `rememberStageBounds`,
  `trailStageBounds`, `searchStageBounds`, `corsiStageBounds`,
  `reaktStageBounds` (all now one-liners: `stageTopClearanceY(rect, els.X
  Hint, els.XPlayerBar, oldFallbackConstant, half)`), and to MOT's
  continuous bounce physics (`motState.topMinY` - objects there drift for
  the WHOLE tracking phase via `requestAnimationFrame`, not just at
  initial placement, so both the edge-bounce clamp in `motMoveObjects()`
  AND the separate post-separation clamp in `motSeparateObjects()` had to
  use `topMinY` - the second one still used the plain `radius` and was a
  **third** bug, silently undoing the fix whenever two objects got pushed
  apart near the top edge). **A fourth bug, also real and also only
  visible under repeated runs**: `motStartRound()`/`startRememberLevel()`
  originally computed bounds/built the layout BEFORE setting that round's
  hint/level text - `getBoundingClientRect()` only reflects whatever text
  is in the DOM at the exact call moment, so measuring first captured the
  PREVIOUS round's (often shorter, sometimes empty on the very first
  round) text and produced a `minY` too small for the text about to be
  shown. **Any new exercise added to this scatter-layout family must set
  its hint/status text before calling its `*StageBounds()`/layout-builder,
  not after.** New exercise built the same "full-stage scatter" way should
  call this helper from day one rather than inventing a hardcoded minY.
  Flash Speicher Test predates this helper and has its own equivalent,
  `flashSafeFy()` (see its NAT entry below) - not worth merging, since it
  clamps a single already-computed `fy` fraction rather than being a whole
  bounds function.
- **Hard rule: nothing on a stage may ever sit under the hint or a
  player-bar button (client, 2026-10-01, after an iPad screenshot of
  Linienhalbierungs-Test drawing its line right next to "Tippe auf die
  Mitte der Linie")**: applies to every exercise, present and future, in
  every section. Fixed then: `bisectRenderLine()` and `renderSubitizeDots()`
  now clamp their top edge via `stageTopClearanceY()`, and `.ufov-stage`
  got a top padding clearing hint + bar. `tests/hint_overlap_all_test.py`
  starts every Test-Bereich and NAT exercise at 390px and 1000px width,
  samples the stage repeatedly and fails on any visible element
  overlapping the hint or a bar item (plus a `Math.random=()=>0`
  worst-case run for Linienhalbierung). **Any new exercise must be added to
  that test's `TEST`/`NAT` lists in the same commit**, and must place its
  content below the measured hint/bar, never at a hardcoded y.
- **`.player-bar` can also overflow off-screen on a narrow phone (fixed
  2026-09-27, found while investigating the above)**: the bar's 4 items
  (Beenden/Pause/status pill/Vollbild) are `display:flex;justify-content:
  space-between` with no wrap - MOT's status label ("8 Objekte · 4 Ziele ·
  Tempo-Stufe 3") is long enough that on a 390px-wide viewport the row
  doesn't fit, and since there was no wrap, "Vollbild" got pushed
  completely off the right edge of the screen - present but unreachable,
  not just visually cramped. Fixed with `.player-bar{flex-wrap:wrap}` and
  `.player-status{white-space:normal;max-width:78vw}` (was `nowrap`) -
  `stageTopClearanceY()` above already measures the bar live, so a
  now-2-line bar is automatically accounted for with no further change.
- **Multi-select with a "select all" shortcut**: individual toggle
  buttons plus one convenience button that (a) selects/deselects
  everything at once and (b) shows itself as "active" automatically
  whenever every individual option happens to be selected by hand, never
  storing that "all" state separately. Toggling the shortcut off drops to
  **zero** selected (not an arbitrary fallback), paired with a warning
  hint and a disabled Start button while empty. Used for VT's arrow
  colours, Stroop's colour palette, and Periphere Wahrnehmung's
  Horizontal/Vertikal/Diagonal "Bereich" picker. Don't reinvent this per
  feature — generalise the existing `colorMode`/`colorModeArray()`-style
  functions instead.
- **Preset + Feineinstellungen**: named presets (e.g. Leicht/Mittel/
  Schwer) set several underlying numeric fields together; an advanced
  "Feineinstellungen" `<details>` exposes the same fields as raw sliders;
  a preset row shows "individuell eingestellt" when the live values don't
  match any preset within a small floating-point tolerance.
- **Named local presets**: `makePresetStore` / `renderPresetList` /
  `wirePresetSaveForm` — reusable save-under-a-name / tap-to-reuse pattern
  used across VT, Breath, Movement, Workout, Kombi and (2026-10-07, Idee 54)
  all NAT ready screens: one store `fwmc-nat-saved-v1` `[{id, name, ex,
  mode, prefs}]` (whole prefs object of the exercise), list/save form per
  screen `<screenId>SavedGroup/SavedList/SaveBtn/SaveForm` in _body.html,
  wired in the `NAT_SAVED` block after the MOT capture code (re-rendered from
  `showScreen`). Tap = apply + start (mode switches along via
  `openNatMode`); in Kombi capture only the captured mode's presets show and
  a tap only fills the draft. `renderPresetList(..., {confirmDelete:true})`
  asks via `confirmDialog()` before "✕" (NAT only so far; VT/Atem/Reaktion/
  Kraft still delete at once - proposal to Fabian to switch them too).
  Periphere Wahrnehmung (VT ready screen) carries `periph` (all periph* +
  background) in its VT preset; Hütchen · Farbe + Zahl carries `cn`.
- **Kombi (cross-section combo) blocks**: adding a new domain to the
  Kombi builder means adding branches to `comboBlockLabel`,
  `comboBlockMeta`, `comboBlockSeconds`, a `COMBO_PRESETS.<domain>` array,
  a `COMBO_DOMAIN_TITLE` entry, and a dispatch branch in
  `startComboBlock()`. A domain whose exercise has no natural end (like
  Remember) needs its own duration-timeout that calls
  `advanceComboProgram(playedS)` when time is up, and its own "Beenden"
  handler must check `comboProgram` first and call `abortComboProgram()`
  instead of its normal single-exercise exit.
- **FAQ accordion** (added 2026-09-27, relocated to a shared footer modal
  the same day after user feedback that it should be reachable from
  everywhere, not just Home): a single `<div class="sheet" id="faqSheet">`
  reusing the exact `.sheet`/`.sheet-inner` + focus-trap/backdrop-click/
  Escape pattern already used by `#tipsSheet`, opened by a
  `<button class="faq-open-btn">` ("Häufige Fragen") placed as the first
  child of all 6 `<footer class="site-footer">` blocks (home, breath,
  movement, workout, nat, test) - so the same overlay opens from any
  section. Items are plain native `<details class="faq-item">`/`<summary>`/
  `<div class="faq-body">`, styled with the app's own theme tokens
  (`var(--line)`/`var(--surface)`/`var(--ink)`/`var(--brand)`) - this is
  general app UI read during normal light/dark browsing, NOT a player/stage
  element, so it correctly uses `var(--...)` rather than the Test-Bereich/
  exercise convention of fixed hex colours. Content is grounded only in
  things actually true of the app (no login, local-only history, what a
  Trainings-Code is, add-to-homescreen, what each section/the Test-Bereich
  is) - extend this list rather than adding a second FAQ pattern if more
  questions come up. Test: `tests/faq_test.py`.
- **Fixation point + background customisation**: `drawFixationPoint()`
  and `currentBgFill()` in `app.js` apply to nearly every exercise that
  uses the shared canvas `drawScene()` pipeline. An exercise whose
  background *is* the trained signal (VT · Farbe & Seite, VRW, Hütchen-
  Kompass-Aufbau, Stroop mit Hintergrund) must set `bgIsStimulus: true` in
  its `EXERCISES` entry to opt out of background tinting; only "Hütchen
  sortieren" (`type: "color-tap"`) opts out of the fixation point
  entirely, since it doesn't use this render path at all.
- **Swipe navigation**: `wireSwipeNav(el, {onLeft, onRight})` — a generic
  helper that calls an existing prev/next button's `.click()` on a
  horizontal swipe, so disabled-state handling is inherited for free.
  Add it wherever a screen already has prev/next buttons for browsing a
  fixed sequence; don't add it to a screen with scattered tap-targets a
  swipe could conflict with (e.g. Remember's training-mode markers).
- **Gesten (Fabian, 2026-10-05, block "Gesten" in app.js, test
  `tests/gestures_1005_test.py`)** - same style as "Zurück per Wischen"
  and "Fenster nach unten wegziehen" (touch/pointer listeners, passive
  where possible, reduced motion = no slide, harmless on desktop):
  - *Aktiven Tab erneut tippen* (`navTabRetap` in the bottom bar block):
    scrolled -> smooth to the top; at the top on a page below the tab ->
    the tab's own page (`NAV_ROOT`); at the top of that page -> nothing.
  - *Kalender wischen*: horizontal swipe > 50 px (|dx| >= 1.5 |dy|) on
    `#todayWeekStrip` clicks `#todayWeekPrev/Next`, on `#calExpand` the
    `[data-cal-step]` / `[data-year-step]` button (quarter view scrolls
    natively), then a 0.32 s slide (`cal-slide-next/prev`). Touches from
    x <= 28 px are left to the edge back swipe; the click that may follow
    a swipe is swallowed. `touch-action: pan-y` keeps vertical scrolling
    native. (Own variant of `wireSwipeNav` because of those two extras.)
  - *Ziehen zum Sortieren*: `wireDragReorder(list, {row, hide, onMove})` +
    `dragHandleEl()` (≡, 44 px, `touch-action:none`). Pointer events
    (touch + mouse), the row lifts (`.drag-lifted`, fixed), a dashed
    `.drag-placeholder` shows the drop slot, auto-scroll near the edges;
    the drop calls `onMove(from, to)`, which must be the SAME function the
    ↑/↓ buttons call (`moveComboBlock`, `freeMoveItem`). `hide` rows (Kombi
    "Pause danach") are hidden while dragging; they live on the block, so
    they travel along. Keep ↑/↓ for accessibility (the handle is
    `aria-hidden`). A new sortable list = one `wireDragReorder` call.
  - *Lange drücken* (500 ms, > 10 px movement cancels): `LP_SEL` (area
    tiles in `#hubAreaGrid`/`#todayAreaGrid`, `#home .excard`, NAT
    `.nat-tile`, Eigenes-Training cards) opens `#tileActionSheet` with only
    the actions that work for the item (`lpActions`): "Direkt starten"
    (opens the ready screen and clicks its visible "Training starten") or
    "Öffnen", "In den Wochenplan" (`openPlanEntry` with `pickDay` +
    `preset`: weekday select in the sheet, current phase or a new one),
    "Zum Kombi-Programm" (fresh Kombi + that item's capture; an area with
    several capture entries opens the Kombi screen at its group),
    "Abbrechen" (page scroll position restored). The click after a long
    press is swallowed, tiles have `user-select:none` and
    `-webkit-touch-callout:none`; right click / Android context menu opens
    the same sheet. A new kind of tile: add it to `LP_SEL` and `lpActions`.
  - *Wischen in Listen* (Fabian 2026-10-05: "nach links wischen, dann
    erscheinen 'Bearbeiten' und 'Löschen', so wie beim Löschen einer Mail am
    iPhone"; block "Wischen in Listen" after the long press, test
    `tests/list_swipe_1005_test.py`): one document-level touch listener and
    a table `SWIPE_ROWS = [{sel, acts(row) -> [{label, del?, run}]}]`. Rows:
    Heute `#dayEvents .event-item` (Termin: `openEventSheet` /
    `askDeleteEvent`), `#dayPanelBody .day-item:not(.compact)` (one-off
    training: `openPlanEntry({kind:"extra", date, id})` now edits in place /
    `dayAction(..., "remove")`; weekly training: `openPlanEntry({kind:"plan",
    pi, di, id, fromToday:true})` / `removePlanEntry` after a confirm that
    says it leaves the Wochenplan for that weekday, "Heute auslassen" stays
    for one day), `#planPhaseList .plan-item` (clicks the row's own ✎ / ✕
    after a confirm), `#freeOwnGrid` cards (`openFreeEditor(b,"edit")` /
    `askDeleteFree`), `#freeTrainerGrid` cards (only Löschen =
    `askRemoveTrainerTemplate`), every `renderPresetList` row
    (`.bundle-item-wrap` with a `.combo-block-remove[title=Löschen]`: saved
    settings and saved Kombi-Programme; only Löschen, since no edit exists;
    the ✕ itself still deletes at once as before). The Stunden view's
    compact blocks are left out (too narrow). Mechanics: direction decided
    after 10 px (vertical = native scroll, rows have `touch-action:pan-y`;
    the listeners are passive), the row follows the finger with a rubber band
    past the buttons, snaps open past half the width or on a fast flick
    (0.3 s ease, reduced motion = no slide). The buttons are a
    `.swipe-actions` panel laid absolutely under the row in its parent (the
    row is never moved in the DOM; parent gets `position:relative` and,
    while open, a horizontal `clip-path` so the row slides out of its list,
    not over the panel border). 84 px wide buttons, full row height (≥ 44),
    radius of the row; Bearbeiten `var(--brand)`, Löschen `var(--warn)`,
    text `var(--bg)` (white in light, dark in dark mode like `.start-btn`).
    One row open; a tap on the open row or anywhere else closes it and that
    tap is swallowed (iOS behaviour); scrolling or a screen change closes it
    too. Touches from x ≤ 28 px stay with the edge back swipe, except on an
    open row (`.swipe-open` is excluded in `wireEdgeSwipeBack`). Long press
    (cancels at > 10 px) and drag handles (`[data-drag-handle]` ignored)
    keep working. A new list with edit/delete: one `SWIPE_ROWS` entry with
    the list's existing functions + its selector in the `touch-action:pan-y`
    rule in styles.css.
  - Known, not changed: every open sheet resets the page scroll to the top
    (the `html:has(.sheet:not([hidden]))` overflow lock); the long-press
    sheet restores it itself.
- **Single-select swatch picker**: `buildSingleSelectPicker(container, lib,
  onPick)` / `syncSingleSelectPicker(container, currentKey)` build and sync
  a "pick exactly one colour" swatch grid (as opposed to the multi-select
  pattern above). Used for the fixation-point colour and background colour
  pickers, each of which now has two live instances (the ready screen and
  the Periph pause overlay) that must always show the same selection.
- **Mid-exercise pause with live adjustment** (Periphere Wahrnehmung,
  Remember): `#periphPauseBtn` stops `raf`, records `periphPausedAt =
  performance.now()`, and shows `#periphPauseOverlay`; `#periphResumeBtn`
  shifts `session.startTime` forward by the paused duration (same
  timestamp-shift trick as the `visibilitychange` backgrounding handler)
  and restarts `raf` — the stimulus schedule never notices the gap. While
  paused, the overlay's four controls (background intensity/colour,
  fixation colour/size) mutate `state` directly and call
  `redrawFrozenFrame()` to repaint the current frame immediately, without
  resuming. Gated to `ex.type === "periph"` in `runSession()`.
  Remember has no rAF schedule to shift - it drives its reveal/cover cycle
  with plain `setTimeout`s - so its pause (`pauseRemember`/
  `resumeRemember`) instead cancels the pending timer and replays it with
  its *remaining* delay on resume, via `scheduleRememberTimer(fn, delayMs)`
  (records `timerFn`/`timerFiresAt` on `rememberState` so any of the three
  places that schedule a transition can be paused generically); the Kombi
  `comboDurationTimer` gets the same treatment. Only background colour/
  intensity is exposed for Remember, not a fixation point - Remember has
  no such on-screen element (there's nothing to stare at a fixed centre
  for), so that part of the Periph pattern just doesn't apply there.
  Shared across both: `buildSingleSelectPicker`/`syncSingleSelectPicker`
  for the swatch grids, and `wireBgIntensityControl(store, refs, onChange,
  transferSelfId)` - a generic "colour + intensity, N synced UI instances"
  wirer, used because Remember needed a *third* near-identical bg-picker
  instance (fixed/shuffle ready screen + Trainingsmodus ready screen +
  pause overlay, all sharing one `rememberPrefs` object) where a fourth
  copy of the original inline Periph/VT pattern stopped being worth it.
  Periph/VT's own bg code has since been migrated onto this same helper
  too (`transferSelfId: "vt"`), once the transfer feature below needed
  wiring on both sides anyway. Picking a colour while intensity is at 0%
  jumps it to 50% (0% always renders plain white regardless of colour, so
  the pick would otherwise look like it did nothing - a real client
  confusion this surfaced); once intensity is already > 0 a colour pick
  leaves it alone. Applies everywhere this helper is used, by construction.
- **"Bestehende Farbgestaltung übernehmen"**: `wireBgIntensityControl`'s
  optional `refs.transfer` (array of `{sourceRow, presetGroup, presetList,
  saveBtn, form, nameInput, cancelBtn, confirmBtn}`, one per UI instance
  that should offer it - typically just the ready screen, not a pause
  overlay) plus the `transferSelfId` argument. Renders two things into
  `sourceRow`: a button per *other* entry in `BG_SOURCES` (each exercise
  domain that has its own background setting - `"vt"` for the whole shared
  VT/NAT canvas setting, `"remember"` for `rememberPrefs`; excludes
  `transferSelfId` so a domain never offers to copy its own live value),
  showing that domain's CURRENT colour and applying it on click exactly
  like a swatch pick (a source's `.get()` is wrapped in try/catch since the
  VT instance renders before `rememberPrefs` exists yet at page-load time -
  it just skips that source until the screen is actually opened, by which
  point every top-level `const` has run); and, via `renderPresetList` into
  `presetGroup`/`presetList`, every named preset the client saved from
  *any* domain (`bgPresetStore`, not domain-scoped - a saved combo is
  meant to be reusable everywhere). `wirePresetSaveForm` wires the save
  button/name-input/confirm the same way every other "gespeicherte
  Einstellungen" screen in this app does. Adding a third domain (Flash
  Speicher Test) means: give it its own `bgColorKey`/`bgIntensity` store,
  add one `BG_SOURCES` entry for it, and wire its own Hintergrund group
  through `wireBgIntensityControl` with a `transfer` config - the
  source-list and presets both pick up the new domain automatically.
- **Background colour/intensity extended to the Test-Bereich (2026-09-27)**:
  the client asked that every Test-Bereich exercise get the same background-
  colour Feineinstellungen NAT's Remember/Blitz/Flash/MOT already have,
  "alle bisherigen und alle neuen übergreifend, überall wo es Sinn macht" -
  audited per-exercise first for whether background colour could interfere
  with the exercise's own signal (several use colour AS the stimulus - Simon,
  Stroop ink colour, Go/No-Go's green/red, etc. - none of those are
  disqualifying since the background tint sits behind the coloured stimulus,
  not on it, except **Wortfarben-Test/Stroop**, excluded on colour-naming-
  validity grounds). First batch: **Go/No-Go**, **Positions-Gedächtnis
  (N-Back)**, **Verbindungstest (Trail Making)** - `gngPrefs`/
  `testNbackPrefs`/`trailPrefs` each gained `bgColorKey`/`bgIntensity`,
  `applyGngBg()`/`applyTestNbackBg()`/`applyTrailBg()` tint `#gngStage`/
  `#testNbackStage`/`#trailStage` (called once when the game starts and
  again on every live edit, exactly like `applyRememberBg()`), and each got
  a `wireBgIntensityControl` call covering both its ready-screen
  Feineinstellungen (a new `<details class="advanced">` - none of these
  three had one before) and its pause overlay (a new picker+slider there
  too, copy-adapted from Flash's `flashPauseBgColorPicker`/
  `flashPauseBgSlider`). **Deliberately DOES NOT** add these three to
  `BG_SOURCES` or wire a `transfer`/preset-save config - extending
  `BG_SOURCES` to 8 domains (and eventually all ~18 Test-Bereich exercises)
  would make the "Bestehende Farbgestaltung übernehmen" source-button row
  absurdly long on every single exercise's Feineinstellungen, a real UX
  regression the client didn't ask for; the ask was the background-colour
  control itself everywhere, not literally the whole preset/transfer
  subsystem too. This is a deliberate, reversible scope narrowing versus
  Remember/Blitz/Flash/MOT's own Feineinstellungen - if the client later
  wants full parity (transfer + named presets) for Test-Bereich exercises
  too, add them to `BG_SOURCES` then. Remaining Test-Bereich exercises get
  the same treatment (minus Wortfarben-Test) in further batches - see the
  Roster below for which already have it vs. not yet. Tests extended:
  `tests/gng_test.py`, `tests/nback_test.py`, `tests/trail_test.py` (swatch
  count, ready-screen colour+intensity changing the stage's rendered
  background, and the pause overlay's own picker live-updating the same
  background while paused). **Second batch**: **Ablenkungstest (Flanker)**,
  **Blickfeld-Test (UFOV)**, **Hinweisreiz-Test (Posner-Cueing)** -
  `flankerPrefs`/`ufovPrefs`/`posnerPrefs` each gained the same
  `bgColorKey`/`bgIntensity` pair, `applyFlankerBg()`/`applyUfovBg()`/
  `applyPosnerBg()` tint `#flankerStage`/`#ufovStage`/`#posnerStage`, and
  each got its own `wireBgIntensityControl` call (ready-screen
  `#flankerAdvanced`/`#ufovAdvanced`/`#posnerAdvanced` + pause overlay
  picker+slider), same scope narrowing as the first batch (no `BG_SOURCES`/
  transfer/preset-save for these three either). Tests extended:
  `tests/flanker_test.py`, `tests/ufov_test.py`, `tests/posner_test.py`.
  **Third batch**: **Rotationstest (Mentale Rotation)**, **Merkspanne-Test
  (Change Detection)**, **Farbkonflikt-Test (Simon-Aufgabe)** -
  `rotationPrefs`/`merkPrefs`/`simonPrefs` each gained the same
  `bgColorKey`/`bgIntensity` pair, `applyRotationBg()`/`applyMerkBg()`/
  `applySimonBg()` tint `#rotationStage`/`#merkStage`/`#simonStage`, and each
  got its own `wireBgIntensityControl` call (ready-screen `#rotationAdvanced`/
  `#merkAdvanced`/`#simonAdvanced` + pause overlay picker+slider), same scope
  narrowing as the first two batches (no `BG_SOURCES`/transfer/preset-save
  for these three either). Merkspanne's tint goes on the outer `#merkStage`
  (which also holds the hint and response row), deliberately NOT on
  `#merkField` - the smaller sub-box where the coloured memoranda themselves
  render - so the background never competes with the colour-change signal
  being tested; Merkspanne also doesn't use `stageTopClearanceY()` at all
  (confirmed by reading the code, not assumed), since its memoranda scatter
  inside that fixed `.merk-field` sub-box rather than the full stage.
  Simon's own stimulus colour (`.simon-dot-blue`/`.simon-dot-orange`) lives
  inside its own neutral, fixed-background `.simon-slot` box, so the stage
  tint sits behind that box and never touches the response-mapped colour
  signal itself - the same "background sits behind the coloured stimulus,
  not on it" reasoning as Simon's own entry in the audit above. Rotation
  is a fixed-centre rotated character, also no `stageTopClearanceY()` use.
  Tests extended: `tests/rotation_test.py`, `tests/merk_test.py`,
  `tests/simon_test.py`. **Fourth batch**: **Suchtest (Visuelle Suche)**,
  **Doppelziel-Test (Attentional Blink)**, **Antizipationstest
  (Coincidence-Anticipation Timing)** - `searchPrefs`/`abPrefs`/
  `antizipPrefs` each gained the same `bgColorKey`/`bgIntensity` pair,
  `applySearchBg()`/`applyAbBg()`/`applyAntizipBg()` tint `#searchStage`/
  `#abStage`/`#antizipStage`, and each got its own `wireBgIntensityControl`
  call (ready-screen `#searchAdvanced`/`#abAdvanced`/`#antizipAdvanced` +
  pause overlay picker+slider), same scope narrowing as every earlier batch
  (no `BG_SOURCES`/transfer/preset-save for these three either). Two of
  these three were flagged during the per-exercise colour-clash audit as
  having their trained signal sit DIRECTLY on the raw stage with no neutral
  box around it - Suchtest's target/distractor items
  (`SEARCH_COLOR_TARGET`/`SEARCH_COLOR_DISTRACTOR`, red vs grey) and
  Doppelziel-Test's T1 accent colour (`#007094` teal vs `#16232a` dark navy
  distractors) - and approved anyway, since this app's background tint is
  always mixed toward white (`mixHex("#ffffff", colorHex, intensity)`, never
  full saturation), which keeps contrast usable regardless. Antizipationstest's
  target zone (`#ffe0b2`/`#e65100` dashed border) lives in its own
  fixed-colour `.antizip-track` sub-element instead, so it's lower-risk by
  construction (same reasoning as Merkspanne's `.merk-field`).
  `stageTopClearanceY()` applies to Suchtest's own `searchStageBounds()`
  (full-stage scatter, like Trail Making/Corsi/Reaktionsfeld) - already
  correctly called after that round's hint text is set, so no change needed
  there; Doppelziel-Test/Antizipationstest are centred normal-flow content,
  not full-stage scatter, so `stageTopClearanceY()` doesn't apply to them at
  all. Tests extended: `tests/search_test.py`, `tests/ab_test.py`,
  `tests/antizip_test.py`. **Fifth batch**: **Wahlreaktionstest (Hick's
  Law)**, **Blockspanne-Test (Corsi)**, **Reaktionsfeld-Test** -
  `hickPrefs`/`corsiPrefs`/`reaktPrefs` each gained the same
  `bgColorKey`/`bgIntensity` pair, `applyHickBg()`/`applyCorsiBg()`/
  `applyReaktBg()` tint `#hickStage`/`#corsiStage`/`#reaktStage`, and each
  got its own `wireBgIntensityControl` call (ready-screen `#hickAdvanced`/
  `#corsiAdvanced`/`#reaktAdvanced` + pause overlay picker+slider), same
  scope narrowing as every earlier batch (no `BG_SOURCES`/transfer/
  preset-save for these three either). Hick's boxes grid renders directly on
  `#hickStage` with no neutral box around it either, approved for the same
  reason as Suchtest/Doppelziel above (tint always mixed toward white, never
  full saturation). Of these three, Corsi and Reaktionsfeld are full-stage
  scatter and use `stageTopClearanceY()` (`corsiStageBounds`/
  `reaktStageBounds`); Hick is a fixed boxes-grid layout (`renderHickGrid`),
  not a scatter, so it doesn't call `stageTopClearanceY()` at all. Checking
  the load-bearing hint-before-measurement order the task called out as a
  known bug class (see `stageTopClearanceY()`'s own entry above): confirmed
  **Reaktionsfeld is correct** - `reaktSpawnLight()` sets `els.reaktHint.
  textContent = ""` before calling `reaktStageBounds()` a line later, same
  order as Trail Making/Suchtest's own reference implementations. Confirmed
  **Corsi has a pre-existing instance of the bug, NOT introduced here and
  deliberately left unfixed per this batch's scope** - `startCorsiGame()`
  calls `renderCorsiBoard(buildCorsiBoard())` (which calls
  `corsiStageBounds()` -> `stageTopClearanceY(rect, els.corsiHint, ...)`,
  measuring `#corsiHint`'s live rendered height) BEFORE the very next line
  sets `els.corsiHint.textContent = "Gleich geht's los …"` - so the initial
  board layout is computed against whatever hint text (usually empty, or
  stale text left over from a previous run) happened to be in `#corsiHint`
  at that moment, not the text about to be shown. This can only under- or
  over-estimate the top clearance by one hint-line's worth of height on the
  very first board layout of a run, not a crash or a hard failure, and every
  subsequent board is rebuilt fresh each "Nochmal", so it is easy to miss in
  normal play; a real fix would reorder those two lines (set the hint text,
  *then* build the board) but that's out of scope for a background-colour
  batch - flagging it here rather than silently fixing unrelated code, for
  whoever picks up Corsi next. Tests extended: `tests/hick_test.py`,
  `tests/corsi_test.py`, `tests/reakt_test.py`. **Sixth batch (final)**:
  **Regelwechsel-Test (Task-Switching)**, **Gegenrichtungs-Test
  (Antisakkaden-Prinzip)** - `tsPrefs`/`antiPrefs` each gained the same
  `bgColorKey`/`bgIntensity` pair, `applyTsBg()`/`applyAntiBg()` tint
  `#tsStage`/`#antiStage`, and each got its own `wireBgIntensityControl`
  call (ready-screen `#tsAdvanced`/`#antiAdvanced` + pause overlay
  picker+slider), same scope narrowing as every earlier batch (no
  `BG_SOURCES`/transfer/preset-save for either). Regelwechsel-Test's own
  design comment previously claimed "no background colour" was in scope
  for this exercise (a leftover from before this rollout existed) - updated
  to stop contradicting the code. Neither exercise uses
  `stageTopClearanceY()` at all (confirmed by reading the code, not
  assumed): Regelwechsel-Test is a fixed-centre cue/digit/response-row
  layout, Gegenrichtungs-Test a fixed left/right dot-slot layout - neither
  is a full-stage scatter, so the hint-before-measurement bug class the
  task called out doesn't apply to either. Tests extended: `tests/ts_test.py`,
  `tests/anti_test.py`. Exercises with a background now: Go/No-Go, N-Back,
  Trail Making, Flanker, UFOV, Posner-Cueing, Rotationstest, Merkspanne-Test,
  Farbkonflikt-Test, Suchtest, Doppelziel-Test, Antizipationstest,
  Wahlreaktionstest (Hick), Blockspanne-Test (Corsi), Reaktionsfeld-Test,
  Regelwechsel-Test, Gegenrichtungs-Test - that's all 17 planned non-Stroop
  Test-Bereich exercises (Wortfarben-Test/Stroop remains the sole,
  deliberate exclusion). The background-colour/intensity rollout across
  the Test-Bereich is now complete.
- **`makeBgApplier(stageEl, prefs)` factory (cleanup, 2026-09-28)**: every
  exercise's own `applyXBg()` from the rollout above - all 21 of them,
  Remember/Blitz/Flash/MOT plus the 17 Test-Bereich ones - had become the
  exact same four lines, copy-pasted, differing only in which stage element
  and which prefs object they closed over. Replaced every
  `function applyXBg() { ... }` with `const applyXBg = makeBgApplier(els.
  xStage, xPrefs);` - pure mechanical dedup (a Python regex over the whole
  file, verified all 21 matches first), zero behaviour change, full
  regression suite confirmed clean after. One shared place to change the
  tinting formula itself from now on, instead of 21.
- **Multi-tab nav bars (`.section-switch`/`.sub-switch`) need headroom for
  their longest label, not just "however many tabs currently exist"**: both
  are a `display:flex` row of `flex:1` tabs capped at a `max-width` - a
  flex item's default `min-width:auto` means it can't actually shrink below
  its content's natural min-content width, so adding one more tab (MOT-
  Fähigkeit as NAT's 5th sub-tab, "Test" as the 6th top-level tab) was
  enough to make the row wider than a phone's viewport in portrait, with
  the rightmost tab clipped off-screen - the client caught this from a real
  device. Fixed with `min-width:0` (lets a tab actually shrink and wrap on
  whole words) + `overflow-wrap:break-word` (a defensive net for one
  unbreakable long word, e.g. "Atemtraining", at a width where it's shrunk
  below that word but there's no space to wrap at) + a wider `max-width`
  (580px/560px - enough for the longest label to fit on one line at any
  width the flex row is actually used at) for normal/wide viewports, and a
  `@media (max-width:480px)` switch to a `display:grid;
  grid-template-columns:repeat(3,1fr)` 3-per-row layout for phones in
  portrait, where a single row of 5-6 German-length labels genuinely
  doesn't fit no matter how much the font shrinks. Adding a 6th/7th tab to
  either bar in the future should re-check this the same way (screenshot at
  ~375-430px AND ~768px+, not just one or the other) rather than assuming
  the existing headroom still holds. Test: `tests/nav_overflow_test.py`.


- **No overlaps in settings UI either (client, 2026-10-02, after "Intensität"
  was covered by its slider in Master-Einstellungen)**: the no-overlap rule
  for stages applies to every settings screen too. `.slider-label` had a
  fixed `width:30px`, so any label longer than "Min"/"Max" ran under the
  range input; it is now `min-width:30px;white-space:nowrap`. Never give a
  text label a fixed width. `tests/no_overlap_settings_test.py` clones every
  `.slider-row` into a 280px box and checks the Master sheet and several
  ready screens live (all `<details>` open), measuring the TEXT extent
  (a Range rect), not just the element box - overflowing text doesn't grow
  the box, which is why a plain rect check missed this bug.

