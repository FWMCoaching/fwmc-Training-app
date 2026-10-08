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
Every note also has "Alle Hilfsmittel" (`.hilfsmittel-all`), which opens the
Hilfsmittel page; its ‹ returns to the ready screen it came from.

### Hilfsmittel und Starterpaket (Mehr, Fabian 08.10. "Starterpaket Stufe 1")
Mehr row `#moreGearBtn` opens `#gearScreen` (tab Mehr stays active). Cards come
from ONE list `GEAR_ITEMS` in app.js (`id, name, desc, link, starter, test`):
`starter: true` = section "Starterpaket" (Hütchen/Becher in 4 Farben,
Farbmatte), the rest under "Für einzelne Übungen" (Nummerierte Felder 1-6,
Klebeband); `test: true` (Rot-Grün-Brille) shows only with the Test-Bereich
unlocked. The exercise chips are read from `HILFSMITTEL[key].gear` (list of
GEAR_ITEMS ids), so notes and page never drift apart. A VT key opens via its
`.excard` click (restrictions respected), then `readyReturnScreen =
"gearScreen"`; other keys need a `GEAR_EX_OPEN` entry (`farbbrille` -> Jedes
Auge zählt, `eyecountReturnScreen`).
Links: none set yet. Empty `link` = no shop button at all. With a link the card
shows "Ansehen" (new tab, `rel="noopener sponsored"`) + "Werbung · Partner-Link",
and `#gearPartnerNote` (Provision sentence, "dein Trainer") appears once any
link is set. Datenschutz "Videos und Links" names external shops. Note: the
privacy intro says "keine Werbung" - revisit that sentence when the first
partner link goes live. Test hook `window.__gear` (`items`, `render`).
A new Hilfsmittel = one HILFSMITTEL entry (with `gear`) + its GEAR_ITEMS card.
Test: `tests/hilfsmittel_liste_1008_test.py`, screenshots `tests/screenshots/hilfsmittel_liste/`.

### Meine Hilfsmittel (Idee 67, Fabian 08.10.)
The client ticks what they have; stored in `fwmc-gear-v1` (`{itemId: true}`,
in backups). Three places, always in sync (`gearSetOwned` -> `gearSyncAll`):
Grundeinstellungen group `#masterGearGroup` (checkboxes from GEAR_ITEMS, the
`test` item only with the Test-Bereich unlocked, + "Alle Hilfsmittel ansehen"),
a "Hab ich" checkbox on every `#gearScreen` card, and a "Hab ich" button in a
ready screen's `.hilfsmittel-note` (ticks every missing item in one tap; with
`anyOf` one button per option, "Hab ich: Farbmatte").
Rule (Fabian): nothing ticked = the client has nothing. HILFSMITTEL entries:
every `gear` id is needed; `anyOf: true` = one of them is enough (Farbfelder:
mat or cups); `optional: true` = works without, never greyed. Farbfelder in
"Antippen" needs nothing (note hidden, card/Kombi block not greyed).
Missing equipment: card `.gear-missing` (dimmed, still opens) + pill
`.excard-gear-note` "Braucht: Hütchen und Klebeband" (names = GEAR_ITEMS
`short`); cards are `.excard[data-exercise=key]` plus `GEAR_EX_OPEN[key].card`
(element id, e.g. Jedes Auge zählt). Ready screen: the start button (`#startBtn`
or the screen's `.start-btn[id$=StartBtn]`) reads "Braucht: …" in the
secondary look; a tap asks via `confirmDialog` "Du hast X noch nicht abgehakt.
Trotzdem starten?" (Trotzdem starten / Abbrechen), every tap once - a window
capture listener that runs before the lead-in/Haken listeners, then clicks the
button again as "Training starten". The label comes back whenever the screen is
shown (MutationObserver on `hidden`). Kombi capture mode ("Baustein
übernehmen") is never relabelled or asked. Kombi list: `.gear-need-tag`
"Braucht: …" per block (`gearKeyOfComboBlock`), playback never blocked. Trainer
code intro (`renderProgramIntro`): `#programGearNote` "Dafür brauchst du: …"
(full GEAR_ITEMS names, missing only), never blocked.
Area hint: every area home with an equipment card gets one `.gear-ask-card`
"Welche Hilfsmittel hast du?" (after the section head of that card's section;
"Hilfsmittel abhaken" opens the page, "Ausblenden" sets
`fwmc-gear-hint-dismissed`), only while nothing is ticked.
Automated browsers treat everything as owned unless localStorage
`fwmc-test-gear` is set (keeps the suite's start labels valid). Test hook
`window.__myGear` (`owned`, `set`, `missing`, `sync`, `hilfsmittel`).
A new Hilfsmittel exercise needs nothing extra: its HILFSMITTEL entry (`gear`,
optionally `anyOf`/`optional`) drives card, ready screen, Kombi tag and intro;
a non-VT one adds `card` to its GEAR_EX_OPEN entry.
Test: `tests/meine_hilfsmittel_1008_test.py`, screenshots `tests/screenshots/meine_hilfsmittel/`.

Test: `tests/farbfelder_1007_test.py`; screenshots `tests/screenshots/farbfelder/`.

## Reize A-E (Fabian 07.10. 21:53, built the same night)
Four more entries in the same "Modus" row (8 modes, 2 per row; 9 since Einblenden) plus one option.
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

## Laufzeit = gewählte Dauer (Prüfer 07.10. Nr. 4)

`buildScheduleFor` wraps every VT builder in `capVtSchedule`: nothing starts
after `state.duration`, a stimulus that would be cut becomes the closing
blank, a short schedule is padded with a blank; `total` is exactly the
chosen duration, so the clock starts at 1:00 for "1 Min". Abfolge merken
starts no round that would not finish. The raw builders (`__ff.build`,
`__cn.build`) are unchanged. Tests: farbfelder_1007 / huetchen_farbe_zahl_1007
("timer starts at the chosen 1:00").

## Antippen (Fabian 08.10., "dann sieht man was angetippt wird")
Ready screen group "So antwortest du" (`#ffAnswerRow`): Treten ("auf der Matte",
default, unchanged behaviour) / Antippen ("auf dem Bildschirm, mit Wertung").
State `ffAnswer` (treten|tippen) in DEFAULTS/snapshot/normalize, so presets and
Kombi blocks carry it; blocks/presets saved before 08.10. load as treten
(`Object.assign(state, { ffAnswer: "treten" }, ….ff)` at the 4 load sites).
Cardio guest always treads (`state.ffAnswer = "treten"` in the guest setup,
`ffTapMode()` is also false while `cardioGuestActive`); not offered there.
- Tippen texts: `FF_MODES[m].tapHelp/tapTask` (countdown task, mode help),
  `FF_MODE_SMALL` (mode buttons' small line), `FF_RULES_TAP` (rules box);
  Fuß und Hand caption "Tippe das Feld mit dem Fuß an" (only the foot counts).
  Hidden in tippen: Hilfsmittel note, Fuß-Vorgabe (`#ffFootGroup`, no L/R badge
  in the schedule), Hände (`ffHandFor` returns null). Layout label becomes
  "Anordnung der Felder", the mat sentence drops out of the help.
- Engine (`session.ffTap`, set in `runSession` when `ffTapMode()`): own
  pointerdown on `#stage` (needs coordinates, so not FAST_TAP_SEL; `#player.ff-tap
  #stage{touch-action:none}`), `ffFieldAt` maps canvas px via `ffGeometry`
  (gap → nearer field, outside the grid ignored). `ffTapEnter` on every frame
  change: a stimulus opens an answer window that lasts until the next stimulus
  (blank included); first tap counts, later ones ignored, none = missed.
  Abfolge: intro opens a round, show frames collect the sequence, "Jetzt du"
  opens input until the next intro; wrong tap ends the round's input.
  A live tempo change (`rebuildVtScheduleFrom`) drops an open, unanswered
  window/round (`ffTapAbandon`). Taps while paused or in the 3-2-1 are ignored.
- Feedback: Haken & Kreuz (`CVD_EXERCISES.farbfelder`, `screens: []`, drawn on
  the canvas by `ffDrawTapFlash`, fixed hex): off (default) = neutral white
  ring/flash 0.42 s on the tapped field; on = green #2e7d32 / red #d32f2f ring +
  white disc with dark tick/cross. An/Aus in `#ffFbRow` (ready, tippen only) and
  `#vtPauseFfFbGroup` (pause sheet, tap runs only). No FB_HINT_STARTS question:
  the badge is white/dark on every field, so contrast never depends on the colour.
- Score (`ffTapScore`): "18 von 22 richtig · Ø 0,84 s" (Ø over correct taps,
  stimulus start → tap) / Abfolge "5 von 7 Runden richtig · längste Folge 6".
  Single runs: done summary + history note (`Leuchten · Antippen · …`). In a
  Kombi or coach programme (Fabian 08.10.) the score goes through
  `blockResultPush(run, "Farbfelder · Leuchten", text)`: the next pause shows
  it once ("Eben: …", `#comboTransitionResult` / `#pauseResult`), the closing
  panel lists every scored block (`#comboDoneResults` / `#programDoneResults`,
  `.block-results`) and the combo/program history note keeps them
  ("Farbfelder · Leuchten: 18 von 22 richtig · Ø 0,84 s; …"). "Nochmal von
  vorne" starts with an empty list; Weitermachen does not carry earlier
  results. A new scored Kombi block = one `blockResultPush` call.
- Stufen-Vorschlag (Fabian 08.10.): `LEVEL_SUGGEST_EX.farbfelder` on the VT
  tempo (`VT_TEMPO_DIFFS`, `vtTempoBucket()`), streak per mode. Very good =
  ≥ 90 % right with ≥ 5 fields shown; Abfolge = every round right, ≥ 2
  rounds. Only single tap runs count (Treten, Kombi, Cardio never); accepting
  sets the shared VT tempo (all VT exercises), the text names "Tempo".
  No markBest (no obvious per-mode best yet).
- Test hooks (automated browsers): `window.__ffTap()` (current window/round/
  items/score), `window.__ffTapFinish()`, `window.__ffTapLastScore`, `__ff.snapshot()`.

## Matten-Anordnung: halten und ziehen (Fabian 08.10.)
Label "Anordnung deiner Matte" + `.tag` "veränderbar"; each cell shows a move
icon (`FF_GRIP_SVG`, cell ink colour). Help under the grid: "Halte ein Feld
gedrückt und zieh es auf ein anderes: Die beiden Farben tauschen den Platz. Eine
Farbe änderst du, indem du das Feld antippst und unten die Farbe wählst
(gewählt: …). Leg deine Matte genauso hin: Oben ist die Reihe näher am Bildschirm."
`wireFfLayoutDrag`: mouse drag after 6 px, touch/pen after a 250 ms long press
(moving > 10 px before = scroll, no drag; cells stay `touch-action:pan-y`,
touchmove is prevented only while dragging); a `.ff-ghost.drag-lifted` copy
follows the pointer, source `.ff-drag-src`, target `.ff-drop-target`, drop swaps
`state.ffLayout` (+ `.ff-swapped` pop), outside = cancel, a click right after a
drag is swallowed. Hand rules are keyed by colour and move with it. The edge
swipe back ignores touches that start on `.ff-layout-grid`.
Test: `tests/farbfelder_tippen_1008_test.py`, screenshots `tests/screenshots/farbfelder_tippen/`;
Kombi-Wertung + Stufen-Vorschlag: `tests/farbfelder_wertung_1008_test.py`
(`tests/screenshots/farbfelder_wertung/`).

## Einblenden (Fabian 08.10., "immer nur ein Feld angeblendet")
9th mode `einblenden` in the same "Modus" row, placed right after Leuchten
("Einblenden" / small "nur das Feld ist zu sehen"); with 9 tiles the last one
(Sehen und Hören) spans the row (`.ff-mode-row>.choice:last-child:nth-child(odd)`,
also on the Cardio guest mode row).
- Run: after the 3-2-1 the full grid shows for `FF_ORIENT_S` = 2 s with caption
  "So liegen deine Felder" (payload `phase: "orient"`); then the stage stays
  white (no faded grid, resting/blank frames draw nothing) and only the shown
  field(s) appear at their grid place in full colour (same rounded rect, no ring).
  A live tempo change does not repeat the orientation (`ffSkipOrient`).
- "Wie viele Felder" (`#ffCountGroup`, only for this mode), state `ffCount`
  (`FF_COUNTS`: eins "Nur eins" / wechsel "Im Wechsel" = default / phasen
  "Phasenweise") in DEFAULTS/snapshot/normalize, so presets, Kombi blocks and the
  Cardio guest (`count`, same row) carry it. `ffEinCount()`: Wechsel = 50/50,
  never more than `FF_COUNT_RUN_MAX` = 3 of one count in a row; Phasen = blocks of
  `FF_COUNT_PHASE` = 6 single, then 6 double, ... Two fields always differ; the
  exact previous set is never repeated.
- Payload `{ fields, count, target: fields[0], targets }`. L/R badge and Hände
  (caption + spoken) only on single fields; two fields = both feet, no badge.
  No Rhythmus-Umkehr (not in FF_FLIP_MODES).
- Tempo/Dauer/Feineinstellungen/Sanfte Reize: the shared VT ones (vtShowS,
  randInterval, cross-fade), nothing of its own.
- Antippen: orientation opens no window (taps ignored); one field as Leuchten;
  two fields (`cur.targets/got`): each shown field counts once, right when both
  came (rt = last needed tap), a tap on a field not shown = wrong, only one of
  two = missed. A tap on an empty spot gets a grey neutral ring (white would
  vanish on the white stage); Haken & Kreuz as before.
- History note `Einblenden · ein Feld | ein und zwei Felder im Wechsel | … phasenweise`
  (`FF_COUNT_NOTES`). Kombi block rows of Farbfelder now name the mode
  ("Farbfelder · Einblenden", for every mode).
- Test hook: `window.__ffLastDrawn` (mode, shown fields, phase / "rest").
Test: `tests/farbfelder_einblenden_1008_test.py`, screenshots
`tests/screenshots/farbfelder_einblenden/`.
