# Farbbrille (Rot-Grün-Brille) + "Jedes Auge zählt" (2026-10-08)

Fabian has several red-green anaglyph glasses (fixed plastic, cardboard,
flip-able ones, so the red lens can sit left or right): "Wir sollten das
also flexibel bauen", calibrated once like a console ("bis man es nicht mehr
sieht"), not before every exercise. Built in the Test-Bereich only; whether
Farbbrille gets its own area is still open.

## Shared settings (one per device)
- Key `fwmc-anaglyph-v1` (in backups like every `fwmc-` key):
  `{left:"rot"|"gruen", red:"#rrggbb", green:"#rrggbb", calibrated, hintOff,
  redCal:{v,h}, greenCal:{v,h}, calibratedAt}`. Defaults: left rot, #ff0000,
  #00ff00, not calibrated. `v` = brightness 10-100 %, `h` = hue shift ±20°
  around red (0°) / green (120°), turned into hex by `anaglyphHex()` (HSV).
- Eye -> colour: the eye behind the red lens sees red dots (green is blocked
  and vanishes on black). `anaglyphLensOf(eye)`, `anaglyphColorForEye(eye)`
  follow `left`, so swapping the side flips the mapping everywhere.
- Grundeinstellungen group `#masterAnaglyphGroup` "Farbbrille" (class
  `.test-teaser`, i.e. only visible with the Test-Bereich unlocked - the same
  gate as the Test tab; when Farbbrille leaves Test, drop the class): "Welches
  Glas sitzt links?" Rot/Grün + "Brille umgedreht? Dann hier tauschen.",
  status line (abgeglichen am … / noch nicht), "Farbbrille abgleichen" / "Neu
  abgleichen", checkbox for the pre-start hint (= `!hintOff`).

## Abgleich `#anaglyphCalib`
Fixed full-screen layer (z-index 65, above sheets), black #000, fixed hex,
"✕ Schließen" + "Schritt n von 4". Works on a copy; "Fertig" saves
(`calibrated:true`), "Schließen" discards. Steps:
1. Brille aufsetzen: which lens is left (Links Rot / Links Grün).
2. Rot ausblenden: close the eye behind the red lens, look only through the
   green lens, tune Helligkeit/Farbton (44 px thumbs + −/+ buttons) until the
   red square vanishes; text names the eyes from the chosen side.
3. Grün ausblenden: the same the other way round.
4. Probe: "Links"/"Rechts" in each eye's colour; "Neu abgleichen" (back to
   step 2) / "Fertig".
Wake lock is held while it is open. Brightness/Night Shift/True Tone cannot be
set by a web app - the hint only asks for it.

## Lock + start (reusable for a later "Mit Farbbrille" switch)
- Calibration is mandatory (Fabian 08.10.): `anaglyphReady()`;
  `anaglyphGate(startBtn, lockEl)` registers a start button: until calibrated
  it gets `.is-locked` + `aria-disabled` and the lock box (`.anaglyph-lock`,
  "Erst die Farbbrille abgleichen" + "Jetzt abgleichen") shows; a tap opens
  the calibration, after "Fertig" you are back on the ready screen, unlocked.
- `anaglyphStart(go)`: locked -> calibration; else the sheet
  `#anaglyphHintSheet` ("Für die Farbbrille: Bildschirm ganz hell, Night Shift
  und True Tone aus …", "Erledigt" / "Nicht mehr anzeigen") unless `hintOff`,
  then the shared dark 3-2-1 (`runLeadIn`, if wanted), then `go`.
- Hilfsmittel: `HILFSMITTEL.farbbrille` ("Du brauchst eine Rot-Grün-Brille.",
  `link` empty - put a shop link there and it shows). Outside VT the note is
  `<div class="hilfsmittel-note" data-hilfsmittel="farbbrille">` (rendered by
  `renderHilfsmittelBox`), plus the "Farbbrille einstellen" link
  (`[data-anaglyph-calib]` opens the calibration).

## Jedes Auge zählt (Test-Bereich)
- `#eyecountOpenBtn` → `#eyecountReady` → `#eyecountPlayer`, prefs
  `fwmc-eyecount-prefs-v1` (Dauer 1/2/3 Min, Tempo leicht/mittel/schwer =
  2 s/1,4 s/0,9 s visible + 0,6-1,2/0,4-0,9/0,25-0,6 s gap, Verteilung
  Ausgewogen 5:5 / Linkes Auge 7:3 / Rechtes Auge 3:7 per shuffled deck of 10,
  Größe 28/40/56 px - a choice row, not LOOK_SPECS).
- Black stage, white fixation cross (both eyes see white), one dot at a time
  in the calibrated red or green, placed below `stageTopClearanceY()` and
  ≥ 44 px from the cross. Tap = own pointerdown on the stage with
  coordinates (hit radius max(r, 22) + 10 px, so the target is ≥ 44 px);
  other taps count as "Daneben getippt". Not in `FAST_TAP_SEL` (needs coordinates).
- Pause drops the dot on screen (not counted); dark player bar and step bar.
- Result: "Linkes Auge: 18 von 20 · Ø 0,62 s" per eye, then one neutral
  sentence: fewer dots (≥ 15 points apart) or slower (≥ 20 % and ≥ 80 ms) →
  "Dein rechtes Auge … Sprich das bei Bedarf mit deinem Trainer ab.", else
  "Beide Augen lagen ungefähr gleichauf." No diagnosis wording (Training,
  keine Augentherapie). Card meta "Zuletzt: linkes Auge x %, rechtes Auge y %"
  (`fwmc-eyecount-last-v1`), no best score.
- Beenden ≥ 10 s = aborted result ("Abgebrochen · …", history `aborted`,
  note "abgebrochen"); shorter = back to Test home. History kind `eyecount`
  (→ area test).
- Test: `tests/farbbrille_1008_test.py` (lock, calibration, hint, colours,
  side swap, per-eye scoring, bar clearance, 1024 px), screenshots in
  `tests/screenshots/farbbrille/`. Also in `tests/hint_overlap_all_test.py`.

## Open
- Own area "Farbbrille" or a "Mit Farbbrille" switch in other exercises
  (both can reuse `anaglyphGate`/`anaglyphStart`/`anaglyphColorForEye`).
- Shop link for the Hilfsmittel note.
- Real-glasses check on iPhone/iPad (Chromium cannot judge filter leakage).
