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

## Reize A-E (Fabian 07.10. 21:53, built the same night)
Four more entries in the same "Modus" row (8 modes, 2 per row) plus one option.
State: `ffGilt` (gesagt|gezeigt, default gesagt), `ffMix` (`FF_MIXES` key,
default ausgewogen), `ffFlip` (0|2|3, default 0) - in snapshot/normalize, so
presets, Kombi blocks and Cardio guests carry them. Pure rules (exposed on
`window.__ff`): `ffIsFlipped(n, every)`, `ffLeuchtenTarget`, `ffRegelnTarget`,
`ffAnsageTarget`, `ffFarbwortTarget`, `ffSehenHoerenTarget`, `ffPickFarbwort`.
- A **Ansage**: `speakWord(colour name)` (same helper as Sehen & Hören, so
  `cueVolume()`/🔊 apply); the stimulus frame shows all 4 fields at full colour,
  nothing marked (resting frames are faded as everywhere). Speaks the colour,
  not the field name (shorter, faster) - field names are a possible later option.
- B **Farbwort**: word (mat colour, upper case) in a different ink colour (also
  a mat colour) on a white plate on a random field; target = field of the INK.
  Word never equals ink (`ffPickFarbwort`). Light inks get a thin dark edge.
- C **Fuß und Hand**: footprint and hand silhouettes (white, dark outline, drawn
  as one merged shape) on two different fields; target = foot field,
  `handTarget` = hand field. The Hände group is hidden for this mode.
- D **Sehen und Hören**: per stimulus kind bild / ton / beides, weights from
  `FF_MIXES` (Ausgewogen 35/35/30, Mehr beides 20/20/60, Nur beides 0/0/100).
  With beides the said field always differs from the lit one; "Bei beidem gilt"
  decides. Caption band: "Bei beidem gilt: das Gesagte" (+ Umkehr).
- E **Rhythmus-Umkehr** (Leuchten, Regeln, Sehen und Hören): every 2nd/3rd
  stimulus flips. Leuchten: diagonal of the lit field; Regeln: diagonal of the
  normal target; Sehen und Hören: the other source - and here only "beides"
  stimuli are counted (single-source stimuli have no other source).
  **Not marked on screen** (decision: counting is the training); the static
  caption names the rule (Leuchten "Jedes 2. Mal schräg gegenüber"; Regeln keeps
  its symbol legend, the rule is on the ready screen). A live tempo change in
  the pause sheet restarts the count.
- Captions use the existing bottom caption band of `ffGeometry()` (reserved, so
  never on a field or under the bar); Farbwort "Die Schriftfarbe zählt", Fuß
  und Hand "Fuß: drauftreten · Hand: hinzeigen". With 🔊 off, Ansage and
  Sehen und Hören show "Ton ist aus – bitte einschalten" there.
- Foot badge (L/R): on the lit field when there is one, else at grid centre.
- History: Farbfelder runs store the mode (+ Umkehr) as `note`.
- Cardio guest: 8 modes; gilt/Mischung for Sehen und Hören, Umkehr row for the
  three flip modes (`data-balf` gilt/mix/flip).
Test: `tests/farbfelder_reize_1007_test.py`, screenshots `tests/screenshots/farbfelder_reize/`.
Not built (to be asked): "Die Übung kann man auch noch woanders einbringen, dann sieht man was angetippt wird".
