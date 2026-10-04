# Contrast-safety warnings on every background-colour picker (added 2026-09-29)

The second half of the same client ask ("Bei Kontrasten der Einstellungen
und vorallem Main Einstellungen auf nicht vorhandene und schlechte achten.
Bei schlechten Kontrasten jeweils ein Hinweis Feld in den Einstellungen
vorher und während der Übung [...] Wer das Risiko dann eingehen will oder
bewusst trainieren will dass es so knapp ist, ok" - never block, just
warn, both before starting and live while adjusting mid-session).

**Turned out to be mostly already built.** An audit before writing anything
found `wireBgIntensityControl`'s `sync()` already computed a contrast
check on every edit (`relLuma(mixHex("#ffffff", chosenHex, intensity)) <
0.45`) and already wrote a hint into `refs.hintEls` - a real, working,
pre-existing feature (`e6e90c4`/`0d88051`, long before this session),
already reaching all 25 exercises with their own bg-colour Feineinstellung
via each one's own `XBgContrastHint` element on the ready screen. The
0.45 threshold and its message ("weißer Text/eine weiße Form oft besser
lesbar als Schwarz") were left exactly as they were - re-litigating that
number wasn't what the client asked for tonight, and it already does the
one thing that matters: it fires on genuinely dark, high-intensity
backgrounds and stays silent otherwise. Never blocks anything - no start
button, no picker, no slider is ever disabled by it; it is purely a
`hidden`/text toggle on a `.group-help` div, so "ok, wer das Risiko
eingehen will" was already respected by construction.

**The actual, real gap, found by tracing where `refs.hintEls` was pointed
for every domain**: every one of those 25 exercises' `wireBgIntensityControl`
call also wires a SECOND (sometimes third) live picker for the mid-session
pause overlay (`refs.pickers: [readyPicker, pausePicker]`, sometimes a
third "Trainingsmodus" picker for Remember/Flash/MOT) - the client can
already change the background colour while paused, and it already applies
live to the stage. But `refs.hintEls` only ever listed the READY screen's
own hint element, never one living in the pause overlay's own markup - so
`sync()` genuinely did compute and set the correct warning text every
time, it just wrote it into a DOM node that's part of the (currently
hidden) ready/settings screen, invisible while actually paused. This is
the literal, precise gap the client's wording points at: "während der
Übung (bei Anpassung einbauen)" - during the exercise, when adjusting.
Confirmed by reading `_body.html`: e.g. Go/No-Go's pause overlay had
`gngPauseBgColorPicker` and `gngPauseBgSlider` but no matching hint
element at all next to them.

**Fix, applied uniformly to all 26 domains** (VT/Periph, Remember, Blitz,
Flash, MOT, and all 21 Test-Bereich exercises incl. the newly-merged DSST):
- A new `<div class="group-help" id="{x}PauseBgContrastHint" hidden></div>`
  added to `_body.html` right next to every existing `{x}PauseBgColorPicker`
  (mechanical, done via a small Python script rather than 26 hand-edits,
  each insertion asserted to match exactly once before writing - the kind
  of repetitive-but-precision-critical change a script verifies more
  reliably than eyeballing 26 near-identical diffs).
- A matching `els.{x}PauseBgContrastHint` mapping added next to the
  existing `els.{x}PauseBgColorPicker` entry.
- Every `hintEls: [...]` array in `app.js` extended with the new element -
  Remember/Flash/MOT (which already had 2: ready + "Trainingsmodus") now
  have 3; everyone else (which had 1) now has 2.
- **Shared the exact same contrast-check logic** rather than duplicating
  the threshold: extracted `bgContrastHintText(colorKey, intensity)` (next
  to `relLuma`/`mixHex`, the two helpers it composes) out of
  `wireBgIntensityControl`'s `sync()`, which now just calls it.
- **Master-Einstellungen's own "Standard-Hintergrundfarbe" picker** - the
  "vorallem Main Einstellungen" part of the client's own wording - did not
  go through `wireBgIntensityControl` at all (it has its own bespoke
  `syncMasterBgUI()`, see the task above), so it had no contrast hint of
  any kind before tonight. Now calls the same `bgContrastHintText()`
  helper and shows/hides a new `#masterBgContrastHint` element the same
  way every other picker does - one consistent mechanism, one message,
  everywhere a background colour can be picked in the whole app.

Test: `tests/contrast_hint_test.py` - Go/No-Go: light colour keeps the
ready hint hidden, switching to black at 100% intensity shows it with the
expected text while leaving "Training starten" enabled (never blocks);
starting and pausing carries the same warning state into the pause
overlay (previously showed nothing there at all); switching colours from
inside the pause overlay itself toggles the hint live, in both
directions, without leaving the overlay. Then Master-Einstellungen: hint
hidden with no default set, appears for a dark default at full intensity,
hides again for a light one, and hides once more after clearing the
default entirely.

