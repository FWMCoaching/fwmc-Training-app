# 31 – Aktivierung (8th area) + Optodrum (2026-10-08)

Fabian 08.10. ("Ja so"): a new area for short activations (30 s - 2 min),
done on their own, as a Kombi-Baustein before/between exercises, and
plannable on Heute/Wochenplan. First own exercise: Optodrum (optokinetic
drum, "da muss natürlich dann wirklich alles fein einstellbar sein, auch
die Geschwindigkeit ... vor und auch während der Übung wieder in der Pause").

## Area
- `PLAN_AREAS` key `activation`, label/short "Aktivierung", colour `#3b4fa8`
  (token `--area-activation`, ink `--area-activation-ink` light/dark),
  icon lightning bolt. Training hub: lower "Dazu" group (`HUB_TEXT`
  "Kurz und knackig, z. B. vor dem Training."), Heute area tiles too.
- `#activationHome`: same frame as `#freeHome` (logo bar + ‹, old tab row
  with no active tab - no tab of its own, like Eigenes Training, flag
  `activationAreaActive` in `activateSectionTab`/`currentHomeScreen`), Kombi
  link, hero (kicker "Aktivierung", "Kurz aktivieren, dann loslegen.", intro
  "Kurze Aktivierungen für zwischendurch: allein, vor einer Übung oder als
  Baustein im Kombi-Programm."), `.code-card` (generic `openProgramIntro`,
  `ACTIVATION_CODE_CTX`), "Aktivierungen" tiles (`#activationGrid`, `.nat-tile`
  look, badge in the area colour), "Gesamter Trainingsverlauf"
  (`HISTORY_PREFIXES` "activation"), footer.
- `?bereich=aktivierung` (or `activation`). `AREA_HOME_IDS`, `HOME_SCREENS`,
  `AREA_TO_SECTION` know it. Long press on a tile (`LP_SEL`, `data-act-ex`
  branch in `lpActions`): Öffnen / Starten / Planen / Kombi.
- `ACTIVATION_EXERCISES` = own exercises `{ id: { title, open } }` (used by
  plan `what: "act:<id>"`, `entryTitle`, tray "Übungen", `startEntry`).
- **Link cards later**: `ACTIVATION_LINKS` (empty) - one entry per existing
  exercise of another area with a short preset, e.g. `{ title: "Gleichgewicht
  kurz", desc, area: "nat", icon: "<svg …>", open: () => …(30 s preset) }`;
  `renderActivationHome()` appends it as the same tile with the tag "aus
  <Bereich>". Exercises are built once; a link never copies an engine.
- Not applicable to the area: Cardio-Zusatzaufgabe (not VT/NAT), restriction
  filters (no sound/limbs/colour judgement), Weitermachen (runs are short).

## Optodrum
- Prefs `fwmc-optodrum-prefs-v1` (`normalizeOptoPrefs` clamps everything):
  `pattern` streifen|punkte|schach, `dir` links|rechts|hoch|runter|schraeg|
  wechsel, `diag` ro|ru|lu|lo (for schräg), `axis` h|v (for Wechsel),
  `swapS` 5-30, `speed` 1-10 (Leicht 3 / Mittel 5 / Schwer 8), `size`
  10-160 px (Streifenbreite / Punktgröße / Feldgröße), `gap` 10-200 px (not
  for Schachbrett), `fg`/`bg` colour keys of `OPTO_COLORS` (default
  schwarz/weiss), `fix` (Fixierpunkt, default aus), `durationS` 10-300 in
  10 s (choices 30 s / 1 Min / 2 Min + slider), `noLimit` (Ohne Zeitlimit).
- Tempo unit for the client: "Stufe 5 von 10 · etwa 1,5 Streifen pro
  Sekunde" (`OPTO_SPEEDS` px/s per Stufe: 30…450; per second = px/s ÷ period).
- Ready screen `#optoReady` and the pause sheet share one markup with data
  attributes (`data-opto-f/-v` choices, `data-opto-r` sliders, `data-opto-c`
  colour pickers, `data-opto-out`, `data-opto-lbl`, `data-opto-show`), wired
  by `optoBind(root, set)` and drawn by `optoSyncControls(root, prefs)`.
  Feineinstellungen: Tempo genau, Breite, Abstand, Musterfarbe,
  Hintergrundfarbe (+ contrast tip), Fixierpunkt, Sanfte Reize je Übung.
  Sicherheitshinweis (closed `details`, Gleichgewicht pattern): photosensitive
  epilepsy, dizziness, when to stop - the general note stays in Tipps/FAQ
  (docs/notes/22).
- Presets `fwmc-optodrum-saved-v1` (`makePresetStore`, tap = apply + start;
  in Kombi capture only fills the draft; ✕ asks first).
- Player `#optoPlayer` (`.player`, `optoBackBtn` "✕ Beenden", `optoPauseBtn`
  "Pause", status "← 0:45", `optoFsBtn` via `wireFullscreen`, 3-2-1 via
  `LEADIN_START_IDS`). One canvas fills the stage behind the floating player
  bar (nothing to read there; `optoCanvas` is exempt in
  `tests/hint_overlap_all_test.py`, the Fertig chip and the fixation point
  are checked). DPR-aware, `ResizeObserver` + resize: motion is kept in CSS
  px (`s` along the direction for stripes, `dx/dy` for raster/checkerboard),
  so a resize never jumps. Stripes are drawn rotated across the direction of
  travel; raster/checkerboard stay axis-aligned and drift. Fixation point:
  red dot with white + dark ring (visible on any colour). Fixed hex only.
- Wechsel: base direction links (axis h) / hoch (axis v); every `swapS` the
  sign flips with a 0.35 s ramp through zero (no hard jump), status arrow
  follows. A live change of direction/axis/interval restarts the count.
- Pause sheet: every setting above except duration, live; standalone run
  saves to the own prefs ("Gilt sofort und bleibt gespeichert …"), Kombi run
  only this run ("Gilt sofort, nur für diesen Durchgang.").
- End: time up = done; "Beenden" before = aborted ("Optodrum beendet",
  `aborted:true`, < 5 s = back to the ready screen without entry); Ohne
  Zeitlimit: "Fertig" chip (bottom centre) or Beenden = done. History kind
  `optodrum` (title "Optodrum · Streifen", note direction + Stufe) →
  `historyAreaOf` = activation (auto-tick, Fortschritt). Done panel inside the
  player, "Nochmal" / "Zur Übersicht" (→ `#activationHome`).
- Sanfte Reize: `SOFT_EXERCISES.optodrum` (+ `softApplies`): tempo capped at
  Stufe 4 (`OPTO_SOFT_MAX`, shown as "Sanfte Reize: höchstens Stufe 4"), the
  pattern colour is mixed 45 % toward the background (less contrast). Note
  on the ready screen, per-exercise switch, live switch in the pause sheet.
- Kombi: group "Aktivierung" (`COMBO_CAPTURE_ENTRIES.activation`), block
  `{domain:"optodrum", prefs}` (own copy), capture/edit on `#optoReady`
  ("Baustein: Optodrum" / "Baustein übernehmen", own prefs restored on exit),
  `COMBO_EDIT_OPENERS.optodrum`, playback `startOptoRun(optoBlockPrefs(block))`
  (`own:false`). Beenden in a Kombi quits the Kombi, Fertig/time up goes on.
- Not wired on purpose: `MASTER_BG_TARGETS` (the background colour is part of
  the stimulus, like Farbfelder), CVD (no right/wrong), Cardio-Zusatzaufgabe,
  Weitermachen, pinch-to-resize (slider in the pause sheet instead).
- Dashboard catalog (dashboard.html, 08.10.): `AREAS` has `activation`
  (plan entries "Aktivierung", what `act:optodrum` via `ACT_EX`), the
  overview lists "Aktivierung · Optodrum" (no code type yet).
- Test hook `window.__opto()` (automated browsers only).

Test: `tests/aktivierung_optodrum_1008_test.py` (screenshots
`tests/screenshots/aktivierung/`); also in `tests/text_wrap_audit_test.py`
(AREAS "aktivierung" + Optodrum ready screen), `tests/hint_overlap_all_test.py`
(`run_opto`), `tests/exercise_coverage_test.py` (activation tiles vs Kombi),
`tests/bottom_nav_1005_test.py` / `tests/today_test.py` (8 area tiles).

## Shared renderer + Bewegter Hintergrund (Fabian 08.10.)
- `optoPaint(ctx, W, H, m, fg, bg)` draws streifen/punkte/schach from a motion object
  `m = {pattern, size, gap, s, dx, dy, a}`; `optoAdvance(m, v, a, dt)` moves it (CSS px,
  wraps the numbers). Optodrum's `optoDraw`/`optoTick` use both; nothing is duplicated.
- **Bewegter Hintergrund** (`==== Bewegter Hintergrund` in app.js, after Optodrum): the same
  pattern as a layer behind Gleichgewicht, Positionen merken, Flash-Speicher-Test and
  Objektverfolgung (MOT, added 08.10. evening: `.mot-stage` isolates, the balls are DOM nodes in
  `#motObjectsLayer` above the canvas and keep their own `onGameTap` targets; default pattern
  grey 35 % keeps black balls >= 4.5:1, yellow targets differ by hue).
  `MOVING_BG` = one entry per exercise (`stage`, `overlay`, `state`, `prefs`, `save`, `own`,
  `readies`). Each exercise's prefs hold `mbg` (`MBG_DEFAULTS`: pattern aus|streifen|punkte,
  dir links|rechts|hoch|runter|schraeg + diag, speed 1-10, size 10-160, gap 10-200, fg/bg
  `OPTO_COLORS` keys, fgInt/bgInt 10-100 %; `normalizeMbg`). Colours: bg = white mixed toward
  the bg colour by bgInt, pattern = bg mixed toward the pattern colour by fgInt (`mbgColors`).
- Controls: `MBG_CONTROLS_HTML` (data-opto-* attributes, so `optoBind`/`optoSyncControls` work;
  `data-opto-lbl` switches Streifenbreite/Punktgröße and the gap/colour labels) is inserted by JS
  into each ready screen's Feineinstellungen right after "Hintergrund" (`.mbg-group`) and into
  the pause sheet as a closed `details.mbg-pause` before "Weiter". Ready edits replace
  `prefs.mbg` with a new object (Kombi capture backups are shallow copies). Pause edits change
  the run's copy `st.mbg` and, for standalone runs (`L.own()`), save to prefs.
- Run: `mbg: mbgCopy(p.mbg)` in the run state + `mbgStart(kind)` in the start function. The
  canvas (`canvas.mbg-canvas`, first child of the stage, `z-index:-1`, `pointer-events:none`,
  stages have `isolation:isolate`) never covers or blocks content; one rAF per exercise, frozen
  while the pause sheet is open, stops itself when the player hides or the state ends.
  Sanfte Reize: `mbgEffSpeed` caps at `OPTO_SOFT_MAX`, pattern 45 % softer. Contrast tip in the
  group (pattern vs. background, or pattern intensity > 60 %), epilepsy/dizziness sentence.
  Cardio guests start without (their cfg has no mbg). Test hook `window.__mbg(kind)`.
- A new exercise = one `MOVING_BG` entry + `mbg` in its run state + `mbgStart(kind)`.
Test: `tests/bewegter_hintergrund_1008_test.py` (screenshots `tests/screenshots/bewegter_hintergrund/`),
`tests/bewegter_hintergrund_mot_1008_test.py` (MOT: off by default, moves, real-pointer tap
selection with the pattern on, pause live, Sanfte Reize, Kombi isolation; screenshots `mot_*`),
`tests/hint_overlap_all_test.py` (balance words+mbg, flash mbg, mot mbg), `tests/text_wrap_audit_test.py` (nat/mot-mbg).

## Gesten in der Übung (Fabian 09.10.)
- Wischen auf `#optoStage` (≥ 40 px, < 0,9 s, nicht vom linken Rand ≤ 28 px) setzt die Laufrichtung
  (8 Sektoren: links/rechts/hoch/runter, schräg = `dir:"schraeg"` + `diag`), zwei Finger
  (oder Strg+Mausrad) die Breite `size` 10-160 px. Kurzer Text in der Mitte (`.opto-toast`).
- Gilt sofort für den Lauf; `#optoLiveSaveBtn` „Speichern" (unten rechts) erscheint, sobald
  Richtung/Breite von den gespeicherten Optodrum-Einstellungen abweichen, nur bei eigenen Läufen
  (nie im Kombi), verschwindet in der Pause (die Pause zeigt die Live-Werte und speichert ihr
  Feld wie bisher sofort). Die ersten 3 eigenen Läufe zeigen kurz den Gesten-Hinweis
  (`fwmc-opto-gesture-hint-v1`; Tests: `fwmc-test-optohint`). Test: `tests/optodrum_gesten_0910_test.py`.
- Client-facing name of the background layer: „Optodrum (bewegter Hintergrund)" (Fabian 09.10.).
- Shared helpers (10.10., used by Optodrum and the switch below): `makeStageToast(stage)`,
  `makeLiveSaveBtn(parent, {id, unsaved, save, visible})`, `wireSwipePinch(el, {live, skip, size,
  onSize, onDir})` (+ `optoGestureDir`), `gestureHintDue(key, testFlag)` (3 times).

## Ebenen-Umschalter „Übung | Hintergrund" (Fabian 10.10., 👍 on the proposal)
- Every `MOVING_BG` exercise (Gleichgewicht, Positionen merken, Flash-Speicher-Test, MOT,
  Schulte-Tabelle) gets, generically (`mbgEbene` setup loop after the MOVING_BG wiring), a
  segmented switch `.mbg-ebene-bar` at the bottom of the stage (z 5, chips 44 px, fixed hex).
  Shown only while the pattern runs (`mbgEbeneOn` from `mbgStart`, `mbgEbeneOff` from
  `mbgStop`), hidden while paused / pause sheet open / done panel (`mbgEbeneSync` per frame in
  `mbgTick`). Every new run state starts on „Übung" (`mbgStart` compares `E.st`).
- „Hintergrund": a transparent `.mbg-gesture` layer (z 4) covers the stage, so no answer
  (`onGameTap`/FAST_TAP), stick drag or balance control below ever sees a touch;
  `wirePinchSize` (LIVE_LOOK) ignores the stage while it has `.mbg-bg-mode`. Swipe = `dir`/`diag`,
  two fingers / ctrl+wheel = `size` 10-160 (same `wireSwipePinch` as Optodrum), toast in the
  middle. `#<kind>MbgSaveBtn` „Speichern" next to the switch, only in „Hintergrund", only when
  `L.own()` and dir/diag/size differ from the exercise's prefs; writes those three into
  `prefs.mbg`. Kombi / trainer programme / Cardio guest: no Speichern, this run only. The pause
  sheet shows the live values (its observer reads `st.mbg`).
- Room for the switch: the stage gets `.has-mbg-switch` (`--mbg-inset: 66px`, JS `mbgInset(stage)`).
  Remember: `rememberStageBounds` / `rememberLiveSize` keep markers above it (percentages stay of
  the full height); Flash: `flashSafeFy` + stage padding-bottom (keypad centred above);
  MOT: `.mot-objects{bottom:inset}` (physics bounds from the layer); Schulte: `fitSchulteBoard`
  + padding (entry `relayout`); Gleichgewicht: `.balance-live` moves up, `balanceArea` follows
  (entry `relayout`). A new MOVING_BG exercise gets the switch for free; its engine only has to
  keep content above `mbgInset(stage)` (optional `relayout` when the inset toggles).
- Hint: the first 3 switches to „Hintergrund" (not at the start, so it never covers numbers while
  answering) show „Wischen ändert die Richtung, zwei Finger die Breite. Tippen zählt so lange
  nicht." (`fwmc-mbg-ebene-hint-v1`, seen-hints keep group; tests: `fwmc-test-mbghint`).
- Explained in the Feineinstellungen group (`data-mbg-gesture-help`) and the Optodrum gestures FAQ.
- Test: `tests/optodrum_ebene_1010_test.py` (screenshots `tests/screenshots/optodrum_ebene/`).
