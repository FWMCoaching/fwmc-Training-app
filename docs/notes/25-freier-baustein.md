# Freie Bausteine (2026-10-05)

**Renamed (Fabian, 2026-10-05 evening): client-facing name is "Eigenes Training"** (area, Kombi group, plan area; one item = "Training", e.g. "+ Neues Training"; inside a Kombi it is still a Baustein). Code names (`free`, `fwmc-free-blocks-v1`) and the history below keep the old wording.

Client's ask: own activities outside the app (Dehnen, Eisbad,
Mobilisation, Journal ...) that can be planned, combined and logged.
Built as a 7th area "Freie Bausteine" (`PLAN_AREAS` key `free`, colour
#a0527a), reached via the Training hub tile and the Heute area tiles
(no tab in the old 8-tab grid on purpose: a 9th tab would break the
4-column grid; with the bottom bar the tab row is hidden anyway).
`?bereich=free` (or `frei`) opens it directly.

## Model
- Storage `fwmc-free-blocks-v1`: `[{id, kind, title, note, minutes, items:[{text, s}]}]`,
  normalised by `freeClean()` (title max 40, falls back to "Eigener
  Baustein"; note max 160; minutes 1-60; item seconds 0-600, 0 = tick yourself).
- Kinds (`FREE_KINDS`): `check` "Abhaken" (title + "✓ Erledigt"),
  `timer` "Mit Zeit" (slider 1-60 min in 1-min steps, countdown),
  `list` "Checkliste" (points one after another; a point with seconds
  shows a countdown and moves on by itself, a point without shows
  "✓ Erledigt"; "Als Nächstes: …" below).
- Templates `FREE_TEMPLATES` (read-only, id `tpl-…`): "Dehnen" =
  Checkliste with 8 generic stretches of 30 s (Waden, Oberschenkel vorne/
  hinten, Hüftbeuger, Gesäß, Brust, Schultern, Nacken). "Kopieren und
  anpassen" opens the editor with a copy; saving creates an own Baustein.

## Trainer-Vorlagen per Code (2026-10-05)
Fabian: "also so wie die eigenen Übungen die sie gestalten können? Dann ja".
- Code type `free-template`: `{type:"free-template", name, trainings:[{kind,
  title, note, minutes, items:[{text, s}]}, …]}` (1-30 trainings, the shape
  `freeClean` accepts; optional `id` per training for stable ids). Built in
  the Trainer-Dashboard (Bereich "Eigenes Training", see notes/10) or JSON.
- `codeDefProblem` → `freeTemplateDefProblem`: trainings must be a non-empty
  array of objects, `items` an array if present, a Checkliste needs at least
  one point with text; otherwise `showCodeError(…, "broken")`.
- `openProgramIntro` → `importTrainerTemplates(def, code)`: stores the
  cleaned trainings in `fwmc-free-trainer-v1` (`[{…training, id:
  "tr-<code>-<n|own id>", code}]`, code normalised), replacing all earlier
  templates of that code (= update, no duplicates; other codes stay), opens
  `#freeHome` and shows "Neu von deinem Trainer: …" / "Aktualisiert: …"
  (`#freeTrainerNotice`, gone on the next visit). Works from every code box
  (Training hub, area code cards, Heute), all funnel through openProgramIntro.
- `loadTrainerTemplates()` adds `template:true, trainer:true`;
  `freeAllBlocks()` = own + trainer + `FREE_TEMPLATES`, so ready screen,
  run, Kombi capture, Wochenplan select, history "Weitermachen" and long
  press all work unchanged. `#freeHome` section "Von deinem Trainer" (per
  Trainings-Code, hidden when empty) between own trainings and Vorlagen.
  Ready screen meta "… · von deinem Trainer", "Kopieren und anpassen" (copy
  becomes an own training) and "Vorlage entfernen" (confirmDialog; the code
  brings it back). Swipe on a trainer card offers only "Löschen".
- Ids are by position (`tr-<code>-1`, …) unless the training carries an
  `id`: if the trainer reorders trainings, a plan entry pointing at
  `free:tr-…` follows the position. Removed trainings leave stale plan
  entries that simply open the area.
- Test: `tests/trainer_template_1005_test.py` (CODE_API routed, incl. the
  dashboard builder writing a code the app opens).

## Screens
- `#freeHome`: same frame as Cardio (logo bar, tab row, Kombi link, hero,
  code card using the generic `openProgramIntro` like Mehr, "Deine
  Bausteine" `.featured-card`s + "+ Neuer Baustein", "Vorlagen", history
  prefix `free`, footer).
- `#freeReady`: title, meta, note, the checklist points, "Training starten"
  (`freeStartBtn`, in `LEADIN_START_IDS` = 3-2-1), "Bearbeiten" (own) or
  "Kopieren und anpassen" (template).
- `#freeEdit`: kind row, title, note (textarea), duration slider or the
  point editor (text, −/+ seconds: 0 → 10 s, 5-s steps to 1 min, then
  15 s; ↑ ↓ ✕, all 44 px), "Speichern"; "Baustein löschen" via
  `confirmDialog()` only when editing an own one.
- `#freePlayer` (`.player`, reuses the `.cardio-stage` classes, fixed hex):
  `freeBackBtn` "✕ Beenden", `freePauseBtn` "Pause" (shared "Pausiert"
  sheet via `openTrainPause`), « ↻ » via `stepCtx` (`freePrevBtn`/
  `freeRestartBtn`/`freeSkipBtn`), swipe nav, beeps in the last 3 s of a
  timed point (`playWorkoutBeep`, follows "Töne und Ansagen").
- Vollbild (Idee 52, 2026-10-07): `#freeFsBtn` + `#freeFsHint` via
  `wireFullscreen` like every player; a finished run leaves fullscreen.
- `#freeDonePanel`: "Geschafft!", rating, Nochmal, Zur Übersicht.

## Everywhere
- Verlauf: `addHistory({kind:"free", title, freeId, seconds, note})`,
  seconds = real elapsed time minus pauses. "»" on the last point =
  aborted (`note:"abgebrochen"`, `setDonePanelAborted`); "✕ Beenden"
  leaves no entry (like Cardio). "Weitermachen" on Heute reopens the same
  Baustein via `freeId`.
- Wochenplan: area `free`, the "Training" select lists every Baustein
  (`what: "free:<id>"`, templates included); `startEntry` opens that
  Baustein's ready screen. Auto-tick is per area (`historyAreaOf` →
  `free`), like every other area: any finished free run that day ticks
  one planned free entry.
- Kombi: group "Freier Baustein" in `COMBO_CAPTURE_ENTRIES.free` (own +
  templates + "Neuer freier Baustein"); each opens `#freeEdit` in capture
  mode ("Baustein übernehmen", edits apply to the block only). Block shape
  `{domain:"free", free:{kind,title,note,minutes,items}}` - its own copy,
  so later edits of the saved Baustein never change a captured Kombi.
  `COMBO_EDIT_OPENERS.free`, label/meta/seconds, `startComboBlock()` →
  `startFreeRun()`; finish → `advanceComboProgram()`, Beenden →
  `abortComboProgram()`. `currentHomeScreen()` knows the area
  (`freeAreaActive`), so a Kombi started here returns here.
- Not applicable (no stage objects/colours): Größe/Farbe, CVD,
  background colour (`MASTER_BG_TARGETS`), Cardio-Zusatzaufgabe.
- Not built / open for Fabian: own icons per Baustein, more templates (e.g. Mobilisation, Atemübung vor dem
  Schlafen), whether "Abhaken" should log a chosen duration instead of the
  (near zero) real time.

Test: `tests/free_block_1005_test.py`; also in `tests/text_wrap_audit_test.py`
(area + ready + editor) and `tests/bottom_nav_1005_test.py` (7 hub tiles).
