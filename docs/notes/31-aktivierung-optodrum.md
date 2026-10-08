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
- Dashboard catalog (dashboard.html): not added yet (another thread was
  working on dashboard.html) - add "Aktivierung"/Optodrum to its copies when
  trainer codes should carry it.
- Test hook `window.__opto()` (automated browsers only).

Test: `tests/aktivierung_optodrum_1008_test.py` (screenshots
`tests/screenshots/aktivierung/`); also in `tests/text_wrap_audit_test.py`
(AREAS "aktivierung" + Optodrum ready screen), `tests/hint_overlap_all_test.py`
(`run_opto`), `tests/exercise_coverage_test.py` (activation tiles vs Kombi),
`tests/bottom_nav_1005_test.py` / `tests/today_test.py` (8 area tiles).
