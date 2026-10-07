# Movement

Limb-cueing engine (`MOVEMENTS`/`figureSVG`/`resolveSlots`, near "==== Movement
(placeholder name) ====" in app.js): a beat-paced sequence of single-limb cues
(`{limb: armL/armR/legL/legR, type: heben/strecken}`), shown one at a time in
either a sliding "lane" window (`renderMovementLaneWindow`) or a full "grid"
(`buildMovementLaneGrid`), the client physically performs whichever one is
active.

**Pictogram style, replaced 2026-09-27**: the original design was a single
abstract four-spoke pictogram (no head/body outline at all, by deliberate
choice - see the code comment history) - in real use it read as neither a
proper figure nor a clean abstract symbol ("weit genug weg vom Original...
aber nichts halbes und nichts ganzes"). Replaced with **two full
alternatives**, chosen per client via `movementPrefs.figureStyle`
("figur"/"abstrakt", Feineinstellungen → "Darstellung"), each a complete
renderer (`figureSVGFigur`/`figureSVGAbstrakt`, dispatched by `figureSVG()`)
sharing the same `{armLeft, armRight, legLeft, legRight}` slot input:
- **"figur"** (default): an actual stick figure - head circle, torso line,
  four limbs anchored at shoulder/hip points, each swinging up for "heben" or
  extending outward for "strecken", the active one in `FIG_HIGHLIGHT` orange.
- **"abstrakt"**: a 2×2 grid of independent circular tiles (arms top row,
  legs bottom row) - neutral = outlined circle with a small dot, active =
  filled orange circle with a white arrow (up for "heben", outward for
  "strecken"). Deliberately NOT a body silhouette at all, so it can't land in
  the old design's same awkward middle ground.
Both renderers are used everywhere `figureSVG()` was already called (the
movement-picker chips AND the lane/grid tiles during play) - picking a style
live-regenerates the already-built picker chips too (`syncMvPickerUI()`), not
just future lane renders.

**Dauer (2026-10-03)**: besides the 1/2/3 Min buttons, Feineinstellungen
has "Exakte Dauer" (`#movementDurSlider`, 1-5 min in 0.5 steps, shown as
"2,5 Min"). Fabian: longer than 5 min = stack Movement twice in a Kombi.
A coach code can still set more (the slider then sits at its max). Test:
`tests/movement_duration_test.py`. Open feedback from Fabian, same day, not
yet decided: the lane "jumps" to the left/middle instead of letting you work
forward to the right, and the whole Movement look doesn't grab him yet -
he wants to think about it first (carry forward, don't build unasked).

**Laufrichtung (window/"lane" mode only), added 2026-09-27**: the client
described the lane as a flowing strip - new cues entering from one edge,
whatever's centred "on the beat" is the one that counts, done ones fading
out the other side - and wanted the entry edge configurable (`oben`/`unten`/
`links`/`rechts`), not always "from the right". Two changes made this real
rather than cosmetic:
1. `renderMovementLaneWindow()` now also renders `MOVEMENT_PAST_COUNT` (2)
   faded `.done` tiles BEFORE the active one, not just upcoming `.next`
   ones - without this the active tile sat at one end with nothing behind
   it, which doesn't read as "flowing past a centre" no matter which way
   the row faces.
2. `movementPrefs.direction` (`rechts` default/`links`/`oben`/`unten`,
   Feineinstellungen → "Laufrichtung") sets `.movement-lane`'s class to
   `dir-<direction>`, and `styles.css` maps each to a `flex-direction`
   (`rechts`→row, `links`→row-reverse, `unten`→column, `oben`→
   column-reverse) - with the DOM always built in the same
   done→active→next order, `flex-direction` alone is what changes which
   edge is "new" vs. "done": e.g. `column-reverse` puts the LAST dom child
   (the newest "next" tile) at the top, so `oben` genuinely means new cues
   enter from the top, not just a label.
Grid ("Ganzes Programm") mode is unaffected - a static full-programme
overview isn't a directional ticker, so `direction` only applies when
`buildMovementLaneWindow` (not `buildMovementLaneGrid`) is in play; a test
switching between grid and window modes must explicitly reset `preview` to
a number afterward; the direction buttons stay inert while stuck on "Ganz".
Diagonal directions and a "wechselnd" (periodically switching mid-session)
mode were also mentioned as maybes. Client's decision (2026-09-28): leave
both out for now, but keep them on the backlog - if picked up later, still
genuine open questions on exact behaviour (switch how often? random or
fixed rotation?), ask before building rather than guessing. Test:
`tests/movement_test2.py`.


**Reaktionstraining neu (2026-10-07)**: Fabian took over the preview page
(https://claude.ai/artifact/LrJwu5HzGoWCAFZDxzDyUi) "erstmal so". Ready
screen: "Anzeige" (Wandernde Zeilen = default / Ganzes Feld / Band),
"Felder pro Zeile" 3-5 (not for Band), "Symbole" moved out of
Feineinstellungen (Vier Felder = default, Vier Punkte, Nur Pfeil, Figur,
Kreise = the old "abstrakt"). Old saved prefs without `layout` are moved once
to zeilen/4/felder; old presets/Kombi blocks keep the strip. Rows engine:
`mvRowsSetup/mvRowsLayout/mvRowsDraw` (cells sized to fit the stage below the
player bar, max 170 px; zeilen shows 2.55 rows, scroll = max(0, t/N - 1);
labels only if a cell is >= 96 px). The pause sheet hides Vorschau for rows.
Symbols deliberately avoid a body silhouette and the original product's
triangle/square; the new display stays marked as Test (`.test-look`) until
Fabian has checked his Life-Kinetik licence (docs in STAND.md 07.10.).
Open for Fabian: Trainer-Dashboard movement-plan codes cannot set
layout/symbol yet (they play Band); live switch of Anzeige in the pause sheet.
