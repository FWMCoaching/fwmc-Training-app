# Periphere Wahrnehmung: Reizfarbe-Pause, Alle-Button (added 2026-09-29)

Three client asks about Periphere Wahrnehmung ("Blitzreize"), all landing
together since they touch the same ready/pause screens (a fourth ask,
"Transparenter Hintergrund" for beamer/projector use, was built the same
day and then deliberately reverted - see the note at the end):

1. **"Farbe der Reize" im Pause-Overlay**: `buildStimColorPicker`/
   `syncPeriphColorUI()` now wire up a *second* picker instance
   (`#periphPauseColorPicker`), sharing the same `state.periphColors`
   backing store as the ready-screen one; its `onChange` additionally calls
   `redrawFrozenFrame()` so a colour picked mid-pause is visible the moment
   you resume, same pattern as the existing pause fixpoint-colour picker.
2. **"Alle Farben"** (`buildStimColorAllBtn`, generalized into
   `buildStimColorPicker` itself): a rainbow conic-gradient swatch, same
   idiom as the unrelated arrow/Stroop `buildColorAllBtn`, appended to
   *every* `buildStimColorPicker` call - so this reaches Periph's own
   picker (ready + pause), the Zusatzaufgabe's `addonColorPicker`, and all
   4 of MOT's colour pickers in one change, not just Periph's. Toggling
   "Alle" off drops to a single colour (`lib[0]`, i.e. "rot") rather than
   zero, since this picker (unlike the standard arrow/Stroop one) never
   allows an empty selection.
3. **"Blick auf die Mitte richten" entfernt**: the `barCaption(...)` call
   in `drawScene()`'s `"periph"` branch is gone - the client found it
   distracting, showing on every single flash.

Test: `tests/periph_stimcolor_test.py` - stimulus-colour picker has 10
swatches (9 colours + Alle) on both ready and pause instances, "Alle"
selects/deselects correctly (down to 1, never 0); a colour picked via the
pause overlay's picker shows up on the (hidden) ready-screen picker too,
confirming the shared backing store; the pre-existing pause bg-colour
picker still works alongside the new stimulus-colour one.

**"Transparenter Hintergrund" was built, then reverted the same day.**
The original idea: a "Farbe"/"Transparent" toggle that cleared the canvas
(`ctx.clearRect()` instead of `fillRect()`) and dropped `.player`'s own
opaque CSS background, so a beamer would show only the stimulus. On
review with the client this turned out to add risk without a real
benefit: a projector can only ever *add* light to the wall, never
subtract it - the physical floor is always "a dark colour", never
"nothing". The already-existing "Schwarz" colour at 100% intensity
already produces exactly that floor, reliably and device-independently.
"Transparent", by contrast, composited down to `body`'s own `--bg` colour
- light grey (`#f6f8f9`) in normal/light mode, near-black (`#0f1a1e`) only
if the client's device happened to be in OS Dark Mode - so it was
strictly *less* predictable than just picking "Schwarz" directly, for no
upside. Removed again in full: `state.bgTransparent`, `currentBgFill()`'s
`null`-return branch, `drawScene()`'s `paintBg()` helper (reverted to the
plain inline `fillStyle`/`fillRect()` it replaced), `bgTransparentActive()`/
`syncBgTransparentUI()`, the `#bgModeRow`/`#periphPauseBgModeRow` toggles
and their `#bgColorOptions`/`#periphPauseBgColorOptions` wrapper divs, and
the `.player.bg-transparent` CSS rule. `tests/periph_transparency_test.py`
(which covered it) was deleted; its still-relevant assertions (the "Alle
Farben" button, the pause stimulus-colour picker) live on in
`tests/periph_stimcolor_test.py` above.

The one *kept* side effect of that detour: while testing "Transparent",
a real, unrelated layout bug surfaced in the shared `.pause-overlay`/
`.pause-panel` CSS (used by ~30 domains' own pause screens, not just
Periph's) - a panel taller than the viewport had its own top edge
clipped/unreachable by CSS flexbox centering, intercepted by the fixed
player-bar above it. Fixed via `margin:auto` on `.pause-panel` (instead
of `align-items:center` on `.pause-overlay`) plus extra top padding to
clear the player-bar - see the CSS comment there. This fix stayed in
when the rest of the Transparent work was reverted, since it's a real,
generally-applicable bugfix unrelated to the beamer-transparency idea
that exposed it.

