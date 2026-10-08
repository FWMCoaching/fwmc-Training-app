# 29 – Hütchen · Farbe + Zahl (Visuelles Training, 07.10.2026, Idee H)

Fabian approved 07.10. (Nacht 2). On the floor lie 3-6 numbered fields
(1..N), on each a coloured cup or cone. The screen shows a colour with a big
number (e.g. yellow + "2"): the client puts the yellow cup on field 2
(an occupied field = swap the two cups).

## Model
- EXERCISES `cone-number`, type `colornum`, `usesColors` (the shared VT
  colour picker / `state.colors`, COLOR_LIB). Card in `#home` right after
  Kompass-Aufbau, tag `huetchen`, pale icon badge (yellow disc + "2").
- `state.cnFields` (3-6, default 4) in the VT `state` (`fwmc-webapp-v3`),
  `cnNormalize()`; `#cnFieldsGroup` (choice row 3/4/5/6) on the VT ready
  screen, `syncCnUI()`.
- Colours: `colorModeLimits()` caps them at `cnFields` for this exercise (one
  cup per field); fewer fields than chosen colours trims the colour list.
  Note: the colour selection is shared with the other `usesColors` VT
  exercises, so up to 6 colours can carry over to e.g. Kompass-Aufbau.
- Schedule `buildColorNumSchedule`: random chosen colour + number 1..N,
  never the same pair twice in a row; tempo/duration/background are the
  usual VT ones (background tint allowed, it is not the stimulus).
- Drawing `drawColorNum` / `cnGeometry`: one disc below the floating player
  bar and inside the stage; number in Magra 700, ink white or #16232a
  (whichever has more contrast on that colour) with a fixed-hex outline of
  the other. Test hooks (automated browsers only): `window.__cnLast`,
  `window.__cnLastGeom`, `window.__cn.build(over, colorKeys)`.

## Wiring
Hilfsmittel note (`HILFSMITTEL["cone-number"]`), Kombi block carries `cn:
{cnFields}` (capture/edit/playback incl. `applyBlockToState`), VT presets
carry `cn`, Cardio guest `cone-number` (generic VT panel + "Anzahl Felder",
cfg `fields`, written into `state.cnFields` by `applyCardioGuestToState`),
Zusatzaufgabe automatic (shared VT canvas), Wochenplan/history via the VT
card (`visualExercises()`), dashboard `VISUAL_EX`. No "Größe" setting (the
disc always fills the free stage), not in CVD_* (no right/wrong feedback).

Tests: `tests/huetchen_farbe_zahl_1007_test.py`, `hint_overlap_all_test.py`
(`run_cn`), `text_wrap_audit_test.py` (visual/cone-number). Cardio guest
index shifts: the 14 VT guests come before periph-flash now (picker 20 types).

## Hilfsmittel für alle Hütchen-Übungen (Fabian 08.10.)
`HILFSMITTEL` also has `cone-compass` ("Hütchen oder Becher in den eingestellten
Farben und ein Kreuz oder einen Stern aus Klebeband") and `cone-tap` ("vier
Hütchen oder Becher in Rot, Gelb, Grün und Blau, nebeneinander vor dir");
same `.hilfsmittel-note` on the VT ready screen, link empty.
Test: `tests/hilfsmittel_texte_1008_test.py`.
