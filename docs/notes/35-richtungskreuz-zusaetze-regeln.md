# 35 – Richtungskreuz, Zusätze für oben, ⓘ Regeln + Meine Notiz (08.10.2026 abends)

Fabian approved Ideen 70, 71, 72 on 08.10. Built together because they share
the VT ready screen, presets and Kombi blocks.

## Idee 70 – Richtungskreuz (Visuelles Training)
Four directions around the client: vorne (towards the screen), hinten, links,
rechts. Each has a colour (`state.rkColors`, default vorne Rot, rechts Gelb,
hinten Blau, links Grün - all four always differ, picking a used colour swaps)
and a number (`state.rkNums`, default vorne 4, hinten 1, links 2, rechts 3,
1-9, swap on duplicates). The app shows a sign, the client steps there and
back to the middle.

- EXERCISES `richtungskreuz`, type `richtungskreuz`, `bgIsStimulus` (no bg
  picker, no fixpoint). Card in `#home` after Farbfelder. Sibling of
  Farbfelder on the shared VT canvas engine: `ffGeometry` (square below the
  bar, caption band), `barCaption`, `seqTiming()` (Abfolge timing now shared
  by both), `capVtSchedule`, `pushCountdown`, Zusatzaufgabe, Sanfte Reize
  (`vtShowS`, cross-fade) - no copied engine. Builder `buildRkSchedule`,
  drawing `drawRk`/`rkDrawSign`, drawScene kind `rk` (resting frames = empty
  stage with a grey centre point).
- State (VT state, `rkNormalize` from `loadPrefs`): `rkMode` zeigen|abfolge,
  `rkSigns` farben|zahlen|beide, `rkGear` matte|huetchen|keine (only changes
  the help text; "Ohne" = "Richtungen merken"), `rkSeqStart` 2|3, `rkRuleOn`,
  `rkRules` {colourKey: normal|gegen|stehen|kreis}, `rkSpeak` (speakWord of
  the sign through cueVolume). Snapshot `rkStateSnapshot()` = `block.rk` /
  preset `rk`.
- Start: after the 3-2-1 the cross overview (`RK_ORIENT_S` = 3 s, "So liegen
  deine Richtungen", like Farbfelder · Einblenden). A live tempo change skips
  it (`rkSkipOrient`) and Abfolge keeps its length (`rkSeqResume`).
- Farbregel (pure `rkTarget(dir, colour, rules, on)`): normal = shown
  direction, gegen = opposite, stehen = no step, kreis = no step, change the
  ball's circling direction (meant for the Zusatz "Ball um den Körper
  kreisen"). Switching it on with nothing set gives Blau = Gegenrichtung.
  Decisions: only in "Zeichen zeigen" and not with "Zahlen" (no visible
  colour). With "Farbe + Zahl" the colour is drawn independently of the
  number: the number names the direction, the colour what to do (otherwise
  the rule would only be a fixed remap). With "Farben" colour = direction and
  meaning.
- Hilfsmittel: `HILFSMITTEL.richtungskreuz` with `optional: true` (kicker
  "Hilfsmittel (optional)", gear page chip "Richtungskreuz (optional)"),
  gear mat + cups.
- Kombi block `rk` (+ label "Richtungskreuz · <Modus>"), preset meta, history
  note "Zeichen zeigen · Farben · mit Farbregel", Wochenplan via the excard,
  dashboard `VISUAL_EX`. Cardio guest `richtungskreuz` appended LAST to
  `CARDIO_GUEST_TYPES` (22 types): Modus, Dauer/Tempo, Zeichen, Startlänge,
  Farbregel an/aus, Ansage; colours/numbers/meanings come from the client's
  own settings (same cross on the floor). Not in CVD_* (no right/wrong), not
  in MASTER_BG_TARGETS (sign is the stimulus).
- Test hooks: `window.__rk` (target, build, snapshot), `window.__rkLastDrawn`.

## Idee 71 – Zusätze für oben
ONE list `ZUSAETZE` in app.js (`id, title, short, text, signal?`). A new
Zusatz = one entry; sheet cards, chips, ready-screen note, Regeln sheet,
presets, Kombi blocks and trainer codes follow.
- Exercises (`ZUS_EXERCISES`, decided 08.10.): vt-color, vrw-original,
  4-straight, 4-diag, 8-solo, 8-vrw, cross-modal, cone-compass, cone-path,
  farbfelder, richtungskreuz. Not: Stroop (spoken answer), Periphere
  Wahrnehmung (fixation), Hütchen sortieren and Farbe + Zahl (the hands move
  the cups), NAT engines. Not as Cardio guest (treadmill).
- Storage: `state.zusOben[exId] = {ids, sigMin, sigMax, trainerIds}` (VT
  state, so Kombi capture's state backup covers it). Presets/blocks carry
  `zus` (always written, even empty); blocks without `zus` = none; presets
  saved before 08.10. leave the current choice alone.
- UI: Feineinstellungen first row `#zusGroup` ("Zusatz für oben:" chips with
  ✕ + "+ Zusatz"; Laufweg: moved into `#lwAdvanced`). `#zusatzSheet`
  (grab bar from the shared sheet code) with `.zus-card`s, any number; from
  the 2nd: "Prüfe, ob sich deine Zusätze gegenseitig ausschließen oder
  aufheben." (sheet + row). Ready screen `#zusNote` lists the instructions
  (Begleit-Zusätze are never checked).
- Signal "Kreisrichtung wechseln auf Signal": `zusSignalStart("player")` in
  runSession/startLaufweg, `zusSignalStop()` in hideAllPlayers. A 200 ms
  interval counts only running time (not during a pause overlay, the Regeln
  sheet, done/pause screens, the VT 3-2-1, a hidden page); at a random time
  between sigMin and sigMax (sliders in the sheet, 3-60 s, default 6-15 s)
  a double tone (`playCueTone` 1175 + 880 Hz, cueVolume) and `#zusSigCue`
  "↻ Kreisrichtung wechseln" for 1.6 s at the bottom of the stage.
  Test hook `window.__zusSig`.
- Trainer: a code block's `zus` gets `trainerIds` = its ids (chips/cards and
  rules show "Von deinem Trainer"). Dashboard: JSON-only (hint text in the
  JSON tab), the Baukasten has no field for it yet.
- History note appends "Zusatz: …".

## Idee 72 – ⓘ Regeln + Meine Notiz
Registry `REGELN_EXERCISES` (app.js): `"@vt"` (every VT catalog exercise incl.
Periphere Wahrnehmung and Laufweg) and the NAT exercises Positionen merken,
Blitz-Raster, Flash, MOT, Gleichgewicht. Per entry: ready screens + anchor,
player bar id, pause overlay ids, Kombi domain, (NAT) description element.
JS injects: `.regeln-btn` "ⓘ Regeln" (+ `.regeln-preview` "Meine Notiz: …")
on the ready screen, a round 44 px `.regeln-bar-btn` in the player bar
before Vollbild, `.regeln-pause-btn` "Regeln und Notiz" in the pause sheet,
and an ⓘ per Baustein in the Kombi overview (`.combo-block-info`, dot when
the block has a note).
- Sheet `#regelnSheet`: "So geht's gerade" (VT: `vtRuleLines(exId)` from the
  current settings - arrows Grün/Rot, VRW, Stroop, Farbfelder mode/symbols/
  Umkehr/foot/hands/mat, Richtungskreuz mapping + Farbregel, Laufweg variant,
  …; NAT: sentences of the ready screen description), "Zusätze für oben",
  "Notiz von deinem Trainer" (read-only, only when a code block carries
  `trainerNote` - or `note` in a code block), "Meine Notiz" (textarea, 300).
- During a run the bar ⓘ clicks the visible `…PauseBtn` (same convention as
  auto-pause), opens the sheet with "Weiter"; "Weiter"/Escape/pull-down
  closes and clicks the overlay's `…ResumeBtn`. From the pause sheet the
  button reads "Fertig" and the run stays paused. In fullscreen the sheet
  moves into the fullscreen element. The VT ⓘ is hidden for Cardio guests.
  Decision: the ⓘ stays in the bar during the run (small, like Vollbild);
  the rules themselves are only shown on tap. With five chips the bar packs
  tighter below 400 px so it stays one row from 360 px.
- Notes: VT in `state.exNotes[exId]` (presets carry `note`, Kombi capture
  writes into the block via the state backup), NAT in `fwmc-notes-v1`
  (`nat:<key>`). During a run only the note is written (`notePersist` reads
  the stored prefs and replaces `exNotes`), never the block's other values.
  Own Kombi run: edits go into the running block (and into the saved
  programme `local:<id>`); trainer runs: the client's own note per exercise.
  Notes stay on the device (in backups via the fwmc- keys).
- Test hook `window.__regeln` (lines, vtLines, note, ctx, startCombo).

Tests: `tests/richtungskreuz_1008_test.py`, `tests/zusaetze_oben_1008_test.py`,
`tests/regeln_notiz_1008_test.py`; hint/bar in `hint_overlap_all_test.py`
(`run_rk`), ready screens + sheets in `text_wrap_audit_test.py`. Screenshots
`tests/screenshots/paket_d/`.

## Open / for Fabian
- NAT Kombi blocks: ⓘ in the overview edits `block.note`, but NAT block
  rules come from the ready-screen description (not the block's own mode).
- Dashboard Baukasten fields for `trainerNote`/`zus` (JSON only for now).
- A "Ball" card on the Hilfsmittel page for the Zusätze (not built).
