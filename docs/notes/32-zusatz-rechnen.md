# Zusatzaufgabe "Rechnen" (2026-10-08)

Fabian's request: a second kind of Zusatzaufgabe next to "Zeichen am Rand"
(Periphere Wahrnehmung). While a VT canvas exercise runs, an equation shows
up and the client decides whether it holds ("stimmt die Aufgabe?").

## Where it lives
- Ready screen `#addonGroup` (label "Zusatzaufgabe"): sub-label "Art der
  Zusatzaufgabe" (`.addon-task-label`, Prüfer 08.10.), then `#addonTaskRow`
  (`data-addon-task` periph / rechnen). The old periph controls are wrapped
  in `#addonPeriphBody`, the new ones are in `#addonMathBody`: Rechenart
  (`data-addon-mathlevel` plus10 / plus20 / mal), "So antwortest du"
  (`data-addon-mathanswer` doppelkreis / gonogo / laut), Anzeigedauer
  1,5-6 s, Pause dazwischen min/max 1-15 s.
- Store: the existing `fwmc-addon-v1` entry per exercise gets `task`
  ("periph" | "rechnen") and `math` `{level, answer, stimulusS,
  intervalMin, intervalMax}` (`addonMathNormalizeEntry`). Phases (Reiz /
  Pause / beide) are shared with the periph variant.
- app.js: one block `==== Zusatzaufgabe "Rechnen" ====` (right before
  "Redraws whatever frame is currently frozen"). Hooks outside it:
  `normalizeAddonEntry`, `syncAddonUI`, `buildAddonSchedule` (returns the
  math schedule when task = rechnen or the Cardio guest is `addon-math`),
  `runSession` (`session.addonMath`), `rebuildVtScheduleFrom`
  (`mathAbandon`), `drawAddonOverlay`, `finishSession` (score in summary and
  history note).

## Statements (`mathMakeStatement`)
- "a + b = c", "a − b > c", "a · b < c" ("−" and "·" glyphs). Results stay
  within 0..10 / 0..20; Mal: 60 % of statements are a multiplication 2-10 ×
  2-10, the rest plus/minus up to 20.
- Relation "=" 60 %, else ">" / "<". About 50 % are true; false ones are
  1-3 off (Mal 1-6). The truth flag is always recomputed from the numbers.

## Answer modes
- **Doppelkreis** (default): inner white disc = "stimmt", dark ring
  (#37474f, white text) = "stimmt nicht". R = clamp(0.3 × shorter stage
  side, 106, 150) css px, ring width max(46, 0.4 R) - both zones ≥ 44 px.
- **Nur bei „stimmt" antippen**: one disc, tap only when true; an untapped
  false statement counts as richtig.
- **Laut sagen**: no tap, no score (summary has no Rechnen line).
- Placement: below the player bar (`top` = bar bottom + 10), never over the
  arrow (`frameArrowPolygon`), the centre word/disc or the fixation dot;
  48 random candidates, then a grid scan (`mathPlace`).
- Taps: a capture-phase pointerdown on `els.stageWrap`; inside the circle it
  calls `stopImmediatePropagation`, so Farbfelder · Antippen and other
  canvas taps never see it. Counted on pointerdown.

## Scoring
`mathFinish` → "Rechnen: X richtig, Y falsch, Z verpasst" appended to the
done summary and history note (" · Rechnen: …"). An unanswered statement is
"verpasst" (go/no-go: unanswered false = richtig).

## Cardio
`CARDIO_GUEST_TYPES` last entry `{id:"addon-math", title:"Zusatzaufgabe ·
Rechnen", group:"extra"}` (`CARDIO_GUEST_GROUPS.extra` = "Weitere
Zusatzaufgaben"); runs on the `cardio-flash-host`
(`cardioGuestRealId`), its cfg travels in `cardioHostAddonId/Cfg`. Own
fields: Dauer, Anzeigedauer, Pause min/max, Rechenart, So antwortest du.
Appended last so older picker indices stay; picker tests now count 21.

## Open / later
- In Kombi and Trainer-Programm runs taps work, but the score is not shown
  per Baustein (could use `blockResultPush` once that lands on main).
- Not offered on Hütchen sortieren / Laufweg / NAT's own engines (same
  exclusions as the periph Zusatzaufgabe).

Test: `tests/zusatz_rechnen_1008_test.py`.
