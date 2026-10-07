# 28 – Farbfelder (Visuelles Training, 07.10.2026)

Fabian 07.10. 21:30 approved (concept: /mnt/project-files/app/konzept-farbfelder.md).
A 2x2 colour grid that mirrors the client's 4-colour floor mat.

## Model
- EXERCISES `farbfelder`, type `farbfelder`, `bgIsStimulus` (no background
  picker, no centre dot). Shared VT canvas engine: `buildFarbfelderSchedule`,
  drawScene kind `farbfelder`; "blank" frames of this exercise draw the
  resting (faded) grid instead of the fixation point.
- Settings live in the VT `state` (`fwmc-webapp-v3`): `ffLayout` (4 COLOR_LIB
  keys: oben links, oben rechts, unten links, unten rechts; default rot, blau,
  gelb, grün), `ffMode` (leuchten / regeln / leer / abfolge), `ffLevel` 1-4,
  `ffSeqStart` 2|3, `ffFoot` (aus / wechsel / zufall), `ffHands`,
  `ffHandRules` ({colourKey: keine|hoch|seitlich|klatschen}, default rot = hoch).
  `ffNormalize()` validates, `ffStateSnapshot()` copies them.
- Rule (pure, `ffTarget(symbol, field)`): Viereck = same field, Dreieck =
  `3 - f` (diagonal), Strich = `f ^ 1` (same row), Herz = `f ^ 2` (same column).
  Stufe n uses the first n symbols. Test hook `window.__ff` (automated browsers only).

## Modes
- Leuchten: one field full colour + white ring + badge (L/R if Fuß-Vorgabe),
  others faded; never the same field twice in a row.
- Regeln: all fields full colour, one symbol on one field; the target follows
  the rule; legend of the active symbols in the caption band at the bottom.
- Das leere Feld: one of kreis/viereck/dreieck/herz on 3 fields, target = 4th.
- Abfolge merken (Simon): intro "Schau zu" 0.8 s, each step lit
  `clamp(stimulusS*0.7, 0.5, 1.5)` s + 0.3 s gap, then "Jetzt du · N Felder"
  for `N * max(1.2, stimulusS)` s (spoken "Jetzt du"), then the normal pause;
  the same sequence + 1 step next round, capped at 12. Purely time-based.
  A live tempo change keeps the reached length (`ffSeqResume`).
- Fuß-Vorgabe: L/R badge on the lit field (Leuchten/Abfolge) or at the grid
  centre (Regeln/Leer). Im Wechsel starts with L.
- Hände: shown in the caption and spoken (cueVolume) for Leuchten and Abfolge
  only; for Regeln/Leer the client applies the rule from memory (showing it
  would give away the target colour) - stated on the ready screen.

## Layout
`ffGeometry()` keeps the square grid below the floating player bar and above
a reserved caption band (barCaption height), so captions/legend never touch a
field. Grid size follows the stage; no "Größe" setting (the grid always fills
the stage, symbols scale with the field).

## Wiring
Kombi block carries `ff` (capture/edit/playback, coach-programme blocks may
carry `ff` too), saved settings carry `ff`, Cardio guest `farbfelder`
(mode/tempo/Stufe/Startlänge/Fuß/Hände; layout + hand rules from the client's
own settings), Zusatzaufgabe works as on every VT exercise, Wochenplan/history
via the VT card. Not in CVD_* (no right/wrong feedback), not in
MASTER_BG_TARGETS beyond the shared VT state (bg is the stimulus).

## Hilfsmittel note (generic)
`HILFSMITTEL` in app.js: `{ exId: { text, link } }`, rendered by
`renderHilfsmittel()` on the VT ready screen as `.hilfsmittel-note`; the link
shows only when `link` is set (empty for now - Fabian names a product later).

Test: `tests/farbfelder_1007_test.py`; screenshots `tests/screenshots/farbfelder/`.
