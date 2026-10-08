# Hütchen · Laufweg "Folge der Karte" (VT, 2026-10-08)

A map of the client's cone grid with a hand-drawn path; the client walks it
(map in hand, or from memory). No scoring, tap-paced.

## Architecture (why)
A regular VT catalog entry (`EXERCISES["cone-path"]`, type `laufweg`), like
Hütchen sortieren (`color-tap`) - the closest sibling: it gets the VT ready
screen, presets (`fwmc-vt-saved-v1`), Kombi capture/edit/playback,
Wochenplan (`visualExercises()` reads the #home excards), history and the
lead-in for free. The run itself is its own DOM/SVG stage (`#lwStage`
inside `#player`) instead of the canvas schedule, because there is no
stimulus timing and nothing to score.

Deliberately NOT wired: Cardio guest (you can't walk a cone course on a
treadmill), Zusatzaufgabe (no Reiz/Pause frames), background colour and CVD
(no right/wrong feedback), Sanfte Reize (`softApplies` excludes laufweg -
nothing flashes).

## Settings (`state.lw*`, normalized by `lwNormalize` from `loadPrefs`)
- Variante: "Karte in der Hand" (path stays; "Nächster Weg") / "Weg merken"
  (path shown 3-20 s, then hidden; "Weg zeigen" / "Weg ausblenden").
- Weglänge Kurz / Mittel / Lang = 3 / 5 / 7 cones (`LW_LENGTHS`).
- Aufbau Reihen × Spalten 2-4 × 2-4 (default 3 × 3) with preview.
- Reihenfarben (Feineinstellungen `#lwAdvanced`): one colour per row,
  default hinten gelb / Mitte blau / vorne rot.
  `#lwAdvanced` sits in `#ready` BEFORE the shared `#advanced`, so code that
  looks for "the" Feineinstellungen of `#ready` must name `#advanced`
  (`cvdControlsHost` does since 08.10.; before, Farbschwäche/Signalfarbe/
  Sanfte Reize of every VT exercise vanished into the hidden Laufweg block).
- Ende: nach Wegen (rounds slider) or nach Zeit (2/3/5/10 Min).
- Hilfsmittel note: "Du brauchst Hütchen in den eingestellten Farben"
  (`HILFSMITTEL["cone-path"]`).

## Path (`lwMakePath(rows, cols, length, rng)`)
Start below the front row, end outside the field. Lattice routing along the
gap lines with small lane offsets, an arc around the current cone before
leaving via a corner, a full loop or half wrap around each target, long
straight runs densified (avoids Catmull-Rom bulges into cones), jitter
0.05. `LW_RHO = 0.36` loop radius. Min distance from the drawn path to any
cone ≥ 0.25 grid units (tested on many seeds). Drawn by `lwMapSvg`: white
card, "hinten" label, cones in row colours, white underlay + #16232a path,
small direction triangles (`.lw-chevron`) every ~1.1 units, end arrow,
start circle #007094 "Start". New random path every round.

## Run
`startLaufweg` / `lwTick` / `lwComplete`; pause via `#lwPauseBtn` +
`#lwPauseOverlay`. Caption "Weg n von N" (+ "merk dir den Weg · noch X s",
"lauf ihn aus dem Kopf", "so war der Weg"). History note e.g. "Karte in der
Hand · 3×3 Hütchen · Mittel · 2 Wege". `lwStop()` from `leavePlayer` and
`hideAllPlayers`. Kombi blocks carry `block.lw` (duration estimate
`lwEstimateS()`). Dashboard `VISUAL_EX` has the entry.

Tests: `tests/huetchen_laufweg_1008_test.py`; hint/bar overlap in
`tests/hint_overlap_all_test.py` (`run_lw`), ready screen in
`tests/text_wrap_audit_test.py`.
