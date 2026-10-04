# Master-Einstellungen (added 2026-09-27, client's own framing: "wie ein Profil, nur ohne Login")

A gear button (`.master-settings-btn`, one per screen's `.brandbar`, seven
total since Cardio added its own home screen - same "one shared overlay
reachable from everywhere" convention as the FAQ sheet) opens
`#masterSettingsSheet`, a cross-cutting settings sheet so the client
doesn't have to re-set the same preference in every exercise's own
Feineinstellungen. Everything lives in ONE localStorage key
(`fwmc-master-v1`) - the sheet's own first line states explicitly that
it's local-only (matches the FAQ's existing "wo werden meine
Trainingsdaten gespeichert" answer), since this is exactly the kind of
setting a client would reasonably wonder is synced somewhere.

**"Vorhandene Einschränkungen" redesign (2026-09-28)**: the whole sheet was
reworked around one explicit client concern - the original single-select
shape (`colorVision: "normal"/"rotgruen"`, `hearing: "normal"/"gehoerlos"`)
put a clickable **"Normal" button** next to each restriction, which reads
as "is having this need not normal" once you sit with the wording - the
client's own example was pointed: "sind Leute die rot-grün-schwäche haben
nicht normal?". Fixed by removing the concept entirely, not just the
label - there is no "Normal"/"Keine" value anywhere in the data model any
more, no matching UI ever rendered, in either language. Empty selection
(nothing ticked, `false`) already means "no restriction" on its own, with
no separate state or button needed to say so. Everything now lives under
one umbrella group-label, "Vorhandene Einschränkungen", with each category
below it. The client also asked explicitly for multi-select everywhere
more than one thing can genuinely apply at once ("genau so wie bei
mehreren Farbeinschränkungen" - i.e. once colour vision itself became a
list, extremities needed the same treatment):
- `masterPrefs = { colorVision: [], restrictedLimbs: [], hearing: false }`.
  `colorVision` and `restrictedLimbs` are arrays (any combination
  selected); `hearing` stays a plain boolean (see below for why it wasn't
  turned into a list too).
- **Farbsehen** (`colorVision`, `CVD_KEYS = ["rotgruen","blaugelb","voll"]`,
  `.choice` buttons, click toggles array membership): Rot-Grün-Schwäche
  already existed; Blau-Gelb-Schwäche (Tritanopie/Tritanomalie) and
  vollständige Farbenblindheit (Achromatopsie) were added after the client
  asked to research what else belongs in this category - these three are
  the standard clinically-recognised groupings; Protanopie/Deuteranomalie
  etc. are deliberately lumped into the one "Rot-Grün" checkbox since
  nothing in this app needs to tell protan/deutan apart. Still wired to
  exactly one exercise - Go/No-Go (`applyColorVisionMode()`, a
  `body.cvd-rotgruen` class, `styles.css`'s `.gng-stimulus.go`/`.nogo`
  override, reusing Simon's blue/orange pair) - the two new categories are
  honestly **collected but not wired to anything yet**, matching the
  sheet's own pre-existing "weitere Übungen folgen, sobald dort die
  Zielfarbe einstellbar ist" framing, which now literally applies to two
  more categories rather than zero.
  **Follow-up research surfaced a real backlog, not yet acted on**: a
  focused audit (asked "which exercises have a fixed, non-picker colour
  pair carrying their actual signal, beyond Go/No-Go") found five more -
  **Simon-Test** (fixed blue `#1565c0`/orange `#e65100` - notably the SAME
  pair Go/No-Go's own rotgruen-safe swap reuses, which would itself need a
  different swap if Blau-Gelb support is ever actually wired up, not just
  collected), **Stroop · klassisch** (fixed 4-colour set incl. a red/green
  AND a blue/yellow-ish pair, both the word ink and the 4 answer buttons -
  not user-configurable, unlike the VT/Zusatzaufgabe colour picker),
  **Merkspanne-Test** (a fixed 9-colour palette, change-detection is
  100% colour, any two of the 9 can pair as changed/unchanged by chance),
  **Suchtest** feature-search mode (red target vs grey distractors,
  colour-alone pop-out by design), and **Attentional-Blink-Test** (T1's
  only marker is brand-teal vs ink colour). Plus a systemic pattern
  spanning nearly every exercise: fixed green `#2e7d32`/red `#d32f2f`
  correct/wrong feedback after a response, colour-alone with no icon.
  None of this was touched tonight - it's a real, separately-scoped design
  problem (choosing genuinely safe replacement palettes across three CVD
  axes, six-plus exercises) that deserves its own pass, not a rushed
  addition on top of an already-large night; flagging it here so it isn't
  lost.
- **Bewegungseinschränkung** (`restrictedLimbs`, one SHARED multi-select
  array of `"armL"/"armR"/"legL"/"legR"` tags - was two independent
  single-select fields, `armLimb`/`legLimb`, before this redesign, itself a
  split of an even older single shared `limb` field covering only arms).
  The semantic direction flipped along with the data shape: the old
  `armLimb: "armL"` meant "only the left arm is usable" (indirect); the new
  `restrictedLimbs: ["armL"]` means "the left arm is restricted" directly -
  the client's ask ("Mehrfachauswahl muss auch bei den Extremitäten möglich
  sein") only makes sense under the direct framing, since "only usable"
  and "multi-select" contradict each other (you can't have two different
  arms be the ONE exclusively-usable one). Because `MOVEMENTS`' own
  `m.limb` tags already use exactly these four strings,
  `movementAllowedByLimb(m)` collapsed to one membership check
  (`!masterPrefs.restrictedLimbs.includes(m.limb)`) instead of four
  separate arm/leg comparisons - unifying the field turned out to simplify
  the filter, not just the settings UI. Still filters Movement's pool
  everywhere it's built from (picker + play pool), same as before.
- **Hören** (`hearing: false`, a single `.checkbox-row` checkbox, no longer
  a two-value choice): deliberately NOT turned into a multi-select list of
  hearing-restriction types the way colour vision was - the app's own
  behaviour never differentiated Schwerhörigkeit from Gehörlosigkeit, it
  only ever gates "this exercise needs sound" (`exerciseBlockedReason()`),
  so a list of types would be inert UI, not a real feature; one honest
  yes/no is what actually does something. Checkbox label deliberately
  spans both ("Gehörlosigkeit oder eingeschränktes Hören") so a client
  doesn't have to self-diagnose which exact category before ticking it.
- **Trainings-Code-Verlauf**: every successful code lookup
  (`openProgramIntro()`, regardless of which of the four programme/bundle
  types it resolves to) calls `recordCodeUsage(code)`, which upserts
  `{code, firstUsed, lastUsed}` into its own `fwmc-code-history-v1` list
  (capped at 20, most-recently-used first). Rendered in the sheet
  (`renderMasterCodeHistory()`) using the same `.bundle-item`/
  `.bundle-item-wrap` + circular action-button pattern the combo-builder's
  own remove buttons use - tapping the item relaunches that code via
  `openProgramIntro()` directly (closing the sheet first), a separate small
  button copies the code to the clipboard. Hidden entirely (not just empty)
  until at least one code has ever been entered.
- **Exercise compatibility - greyed out + marked, not hidden** (client's
  own follow-up: some restrictions ADAPT an exercise, like Farbsehen/
  Go-No-Go above, but others make one genuinely unusable, and those should
  stay visible-but-blocked with a note pointing back to Settings, not
  disappear or silently misbehave). `exerciseBlockedReason(card)` is the
  one general-purpose check, reusable for future exercises/restrictions:
  today it only fires for `masterPrefs.hearing` (now a plain boolean check,
  no string comparison) against any `.excard` whose EXISTING `data-tags`
  already includes `"ton"` - VT's own long-standing ton/ohne-ton filter
  tag, reused rather than a second parallel list, and it turns out only ONE
  exercise in the entire app ("Sehen & Hören"/cross-modal, VT) is tagged
  `ton` at all. `applyExerciseCompatibility()` toggles an `.incompatible`
  class (greys it out via CSS) and injects/removes a small
  `.excard-blocked-note` badge reusing the blocked reason as its text - runs
  once at load and again whenever `masterPrefs.hearing` changes. The
  `.excard` click handler checks `classList.contains("incompatible")` FIRST
  and opens Master-Einstellungen instead of the exercise when true - the
  card itself doubles as the "Verweis auf die Master-Einstellungen" the
  client asked for, rather than a separate link/tooltip. Currently only
  `.excard` (VT's home grid) is wired - Movement's own incompatibility
  (Bewegungseinschränkung) already handles itself by filtering its
  pool/picker instead of greying a whole exercise.
- **Migration**: `loadMasterPrefs()` reads every earlier saved shape
  (single-string `colorVision`/`hearing`, split `armLimb`/`legLimb`, or the
  oldest shared `limb` field) and converts each into the new arrays/
  boolean, then calls `saveMasterPrefs()` immediately at the end of load -
  a migrated shape lands on disk right away rather than silently staying
  in the old shape in storage until the client happens to touch some
  toggle (caught by a Playwright assertion checking `localStorage`
  directly after a fresh load with old-shape seed data, not by eye - the
  in-memory state and UI were already correct without this, only the
  persisted copy was stale).

Test: `tests/master_settings_test.py` (42 assertions: the no-"Normal"
wording check, multi-select colour vision incl. an actual GNG-colour-
change proof, the unified multi-select limb list including a combined
restriction, the hearing checkbox, code history, migration of all three
old shapes - the last one via a separate inline script, not the main test
file, since it needs to seed localStorage before the page's first load).

**Built 2026-10-02 (client approved both parts): Farbschwäche-Unterstützung.**
Any Farbsehen option ticked in Master now switches on, for every exercise
that has it, two independent aids (one shared block in app.js,
`CVD_EXERCISES`/`CVD_FB_SELECTORS`, next to `applyColorVisionMode()`):
- **Haken & Kreuz** (`fb`): a tick/cross badge on every right/wrong
  feedback state, so green/red no longer carries the meaning alone.
  Implemented as a generated stylesheet (`#cvdFeedbackStyles`, built from
  `CVD_FB_SELECTORS`) that adds an SVG `background-image` badge, centred at
  the top, scoped per exercise via `body.fbs-<ex>` - no positioning or
  layout change, so it's safe on absolutely-positioned markers and static
  buttons alike (a corner badge got clipped away on round buttons, hence
  centre-top). MOT's 3D look keeps its gradient under the badge (special
  rule). 26 exercises: Remember/Blitz/MOT plus every Test-Bereich exercise
  with right/wrong feedback.
- **Farbsichere Farben** (`pal`): `body.cvdp-<ex>` plus render-time reads
  (`cvdPalOn(ex)`) swap the fixed colours of Go/No-Go, Simon, Stopp-Signal,
  Doppelziel (T1), Suchtest, Wortfarben-Test, Kartensortier-Test and
  Merkspanne. Pairs are dark blue `#0b3d91` vs. amber `#f5a300` (apart by
  brightness, ~4.9:1, so they survive every CVD type incl. full colour
  blindness); 4-colour tasks use a brightness ladder Schwarz/Blau/Orange/
  Gelb (words and button labels change with it); Merkspanne uses
  Okabe-Ito + grey (9 colours, same count). Instruction texts that name a
  colour swap via `<span data-cvdp-ex data-cvdp-show="on|off">` pairs.
  Honest limit: for full colour blindness the 4-colour/9-colour tasks rest
  on brightness steps alone - better, not perfect.
Each exercise's Feineinstellungen gets a "Farbschwäche-Unterstützung" group
(injected by JS into every ready screen; a new `details.advanced` is
created where a screen had none) with An/Aus per aid. Pressing either
stores an override (`fwmc-cvd-overrides-v1`, `{ex:{fb,pal}}`) that wins
over Master in both directions; the status line offers "Wieder den
Master-Einstellungen folgen", and Master-Einstellungen has a global reset
(`#masterCvdResetBtn`, shown only while overrides exist). The old
`body.cvd-rotgruen` GNG-only swap is gone (replaced by `cvdp-gng`). VT's
Stroop exercises are untouched - they already have a free colour picker.
**Any new exercise with right/wrong feedback or a fixed colour pair must
be added to `CVD_EXERCISES`/`CVD_FB_SELECTORS` (and palette reads) in the
same commit.** Test: `tests/cvd_support_test.py`.

