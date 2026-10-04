# Ziel-/Signalfarbe pro Übung + Stroop-Farbhäufigkeit (gebaut 2026-10-02)

Fabian: "A. Ja", "B. Ja".

**A - Signalfarbe** (`SIGNAL_DEFS` in app.js, next to the CVD block):
every Test exercise whose signal is a fixed colour has a "Signalfarbe"
group injected into its Feineinstellungen (same host helper as the CVD
toggles, `cvdControlsHost`): Go/No-Go (go/nogo), Farbkonflikt-Test
(left/right key), Suchtest (target/distractor), Doppelziel-Test (T1),
Stopp-Signal-Test (signal), Reaktionsfeld-Test (light), Antizipationstest
(ball), Blockspanne-Test (lit block). Palette = `FIX_COLOR_LIB` without
Weiß; store `fwmc-signal-colors-v1` = `{ex:{slot:key}}`; a missing entry
means "Standard" (each row has a "Standard" reset link).
- Effective colour (`sigEffective`): own pick > colour-safe palette
  (`cvdPalOn(ex)`, only where the slot has a `cvd` value) > default.
- Applied as a generated stylesheet `#signalColorStyles`, every rule
  prefixed `html body.sigc` so it outranks both base rules and
  `body.cvdp-<ex>` rules (`SIGNAL_CSS` holds one builder per slot). Suchtest
  reads `sigColor("search", ...)` at render time instead.
- Texts naming a colour are `<span data-sig="ex.slot" data-sig-form=...>`
  (forms: lower/upper/er/es/er-lower, e.g. "Roter Kreis", "blauer");
  they replaced the old `data-cvdp-ex` span pairs for gng/stop/search/ab
  (Wortfarben-Test keeps its pair). Simon's buttons are relabelled and
  get a readable text colour (`sigInk`).
- Never blocks: a warning under the group if the two colours are too close
  (`sigTooClose`: same brightness AND near in RGB - lila vs. rot is fine)
  or a colour barely shows on white.
- **A new Test exercise with a fixed signal colour gets a `SIGNAL_DEFS`
  entry, a `SIGNAL_CSS` builder and `data-sig` text spans in the same
  commit.** Merkspanne/Kartensortier/Wortfarben are palettes, not single
  signals - their colours stay with the CVD palette.
Test: `tests/signal_color_test.py`.

**B - Häufigkeit der Farben** (VT Stroop klassisch / mit Hintergrund):
`state.stroopWeights` (`{key: 2|3}`, missing = 1×) in the VT prefs; a
collapsible "Häufigkeit der Farben" under the colour picker
(`#stroopWeights`, shown only in Stroop colour mode) with one 1×-3× slider
per selected colour. `buildStroopSchedule` picks the INK colour (the
answer) with `weightedPick`, then the word from the other colours, so every
stimulus stays incongruent. Kombi Bausteine carry `stroopWeights` (capture,
edit, playback). The Test-Bereich Wortfarben-Test is a fixed balanced
design and was left alone. Test: `tests/stroop_weights_test.py`.

