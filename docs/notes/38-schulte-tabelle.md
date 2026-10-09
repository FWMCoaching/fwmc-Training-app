# 38 – Schulte-Tabelle (7th NAT exercise, 2026-10-09)

Numbers 1..N in a square grid, tapped in order against the clock. Closest
sibling: Blitz-Raster (stage, hint rule, cell look); Fixpunkt wiring like MOT.

## Modes and rules
- Grid 3×3, 4×4, 5×5, 6×6 (`SCHULTE_GRIDS`, default 5) on the ready screen
  (`#schulteGridRow [data-schulte-grid]`, `#schulteGridCount` names the count).
- Modes (`SCHULTE_MODES`, NAT_MODES row "Fest / Wechselnd / Aus der Erinnerung",
  cards `schulteOpenFest/Wechselnd/Erinnerung`, one screen `#schulteReady`):
  - **Fest**: numbers stay.
  - **Wechselnd**: after every correct tap the numbers not tapped yet are
    reshuffled over their cells (tapped ones stay put, greyed).
  - **Aus der Erinnerung**: all numbers visible until the first CORRECT tap
    (the 1), then every open cell is covered (`.covered`); tapped ones show.
- Fixpunkt: shared module (`FIX_ADAPTERS.schulte`, key `schulte:<mode>`,
  standard ON, groups `schulteFix*` on the ready screen and `schultePauseFix*`
  in the pause sheet). Odd grid + Fixpunkt = the middle cell is `.free` (no
  number, N-1 numbers, the point sits in it). Even grid = the point sits on
  the crossing of the four middle cells (kept small: ≤ 42 % of a cell).
- Wrong tap: cell `.wrong` red for 450 ms, counted (`errors`); correct = green
  350 ms. Haken & Kreuz via `CVD_EXERCISES.schulte` / `CVD_FB_SELECTORS`.
- Taps: `onGameTap` on every number cell, `.schulte-cell.tappable` in
  `GAME_TAP_SEL`; `.schulte-cell` in the touch-action list.

## Run, pause, result
- `startSchulteGame(mode, opts, prefsOverride)`; standalone = one table, then
  the done panel. `opts.comboDurationS` (Kombi block, Cardio-Zusatzaufgabe) =
  tables repeat (1.6 s "gleich kommt die nächste Tabelle") until time is up.
- Status pill: "k/N · 12,3 s" (100 ms ticker).
- Pause: clock stops, numbers are hidden (`.schulte-board.is-paused`, colour
  transparent) so a pause never helps the search. Live in the sheet:
  Hintergrund (intensity/colour), Fixpunkt (full group), Größe der Zahlen
  (`LIVE_LOOK`, also pinch), Haken & Kreuz, Sanfte Reize, Bewegter Hintergrund.
  Switching the Fixpunkt on/off on an odd grid restarts the current table
  (middle cell changes; its errors are dropped); the sheet says so.
- Result: "Schulte-Tabelle · Fest · 5×5 mit Fixpunkt · 23,4 s · 1 Fehler",
  `markBest(... "· ", time)` + "Neue Bestzeit!" (BEST_PHRASE knows "Bestzeit").
  History kind `schulte`, title "Schulte-Tabelle · <Modus>", `historyAreaOf` →
  `nat`, Wochenplan `nat:schulte` (`NAT_SUBS`).
- Beenden: a finished table still counts (short "Geschafft" moment), an
  unfinished one leaves no entry. Done "Zur Übersicht" goes to `#schulteReady`.
- Bests: `fwmc-schulte-best-v1` = `{ "<mode>:<grid>[f]": ms }`, lower is
  better; `f` = odd grid with a free middle (one number less, so its own best).
  Card meta `schulteBest*` lists the bests per grid, the ready screen
  (`#schulteReadyBestHint`) the one for the current grid/Fixpunkt.

## Settings and wiring
- Prefs `fwmc-schulte-prefs-v1` (`schultePrefs`: gridSize, numScale, numColor,
  bgColorKey/bgIntensity, mbg). LOOK_SPECS `schulte` (Größe der Zahlen 0.6-1.6,
  capped at 60 % of a cell; Farbe der Zahlen from FLASH_CHAR_COLOR_LIB, checked
  against the white cell). Background `makeBgApplier` + `MASTER_BG_TARGETS`.
- `SOFT_EXERCISES.schulte` (Sanfte Reize: swaps fade in, softer colour changes,
  `body.soft-schulte`), `MOVING_BG.schulte`, `REGELN_EXERCISES "nat:schulte"`,
  NAT presets (`NAT_SAVED` EX.schulte, ids `schulteReadySaved*`),
  `FB_HINT_STARTS` + `LEADIN_START_IDS` (shared 3-2-1), `wireFullscreen`.
- Stufen-Vorschlag: `LEVEL_SUGGEST_EX.schulte` walks the grid size
  (`def.order` g3 → g6, new in `levelSuggestAfter`). "Very good" =
  ≤ 1 Fehler and ≤ 1.2 s per number (Fest), 1.6 s (Wechselnd), 2.0 s
  (Erinnerung) - ASSUMPTIONS, see docs/notes/02.
- Kombi: three capture entries "Schulte-Tabelle · Fest/Wechselnd/Aus der
  Erinnerung", block `{domain:"schulte", mode, duration (s, default 120),
  prefs}` (prefs snapshot incl. Fixpunkt of that mode), edit via
  `COMBO_EDIT_OPENERS.schulte`, playback in `startComboBlock`, block result
  "N Tabellen · beste 12,3 s". Trainer can send it as JSON combo-program
  (dashboard hint); no dashboard builder (no NAT exercise has one).
- Cardio-Zusatzaufgabe: guest type `schulte` (appended last), cfg duration 45 s,
  mode, grid (default 4), Fixpunkt an/aus, look, background; the Fixpunkt's
  kind/colour/size comes from that mode's module setting.

## Open (for Fabian)
- Thresholds of the Stufen-Vorschlag (above).
- Erinnerung: numbers vanish on the first correct tap (alternative: after a
  fixed look time).
- Pause covers the numbers (fair timing); alternative: leave them visible.
