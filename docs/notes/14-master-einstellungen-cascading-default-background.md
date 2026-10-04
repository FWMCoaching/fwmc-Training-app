# Master-Einstellungen: cascading default background colour (added 2026-09-29)

The first half of the client's "go through everything independently"
follow-up (the other half is the contrast-safety warnings below): a
Master-level default background colour/intensity that seeds into every
exercise carrying its own background-colour Feineinstellung, so the
client doesn't have to set the same colour 25+ times by hand. Client's
own decision on how it should behave, asked explicitly since two designs
were both defensible (auto-seed-only vs one-click-transfer-only): **"Beides"**
- both at once:
- **Automatic seeding**: the very first time an exercise's own bg-colour
  prefs are read and it has genuinely never had its own colour chosen
  (`bgColorKey` absent from that exercise's own localStorage key, not
  merely falsy), it starts at the Master default instead of "keine
  Hintergrundfarbe". Once a client touches that exercise's own colour
  picker even once, it's "customised" forever after and the Master
  default never touches it again, even if the Master default later
  changes or the exercise is reopened - this direction (never silently
  override a real choice) mattered enough to the client to become its
  own explicit test assertion, not just an implementation detail.
- **One-click transfer button**: additionally, wherever the existing "Wie
  bei X" transfer row already lives (Visual/Remember/Blitz/Flash/MOT -
  see the pre-existing `wireBgIntensityControl`/`BG_SOURCES` mechanism
  documented under Kombi-Baukasten/earlier sessions), a same-styled "Wie
  in den Master-Einstellungen" button is appended, so the client can
  switch back to the Master colour at any time even after customising an
  exercise individually - not just once at first-open.
- **`MASTER_BG_TARGETS`**: a registry of factory functions
  (`() => ({ prefs, key, save })`, lazy for the TDZ reason below), one per
  exercise that has its own `bgColorKey`/`bgIntensity` fields - all 26:
  the 4 richer NAT domains (Remember/Blitz/Flash/MOT), Visual/`state`
  itself, and every Test-Bereich exercise (Go/No-Go, N-Back, Trail
  Making, Flanker, UFOV, Posner, Rotation, Merkspanne, Simon, Suchtest,
  Doppelziel, Antizipationstest, Hick, Corsi, Reaktionsfeld,
  Regelwechsel, Gegenrichtung, plus the newer autonomous Test-Bereich
  additions Vorlauf/Stopp-Signal/Zeichen-Zuordnung). New Test-Bereich
  exercises keep landing on `main` via the autonomous Routine while this
  feature was being built - `applyMasterBgDefaultEverywhere()` running
  again at every page load (not just once ever) is what keeps a freshly
  merged exercise's very first localStorage read already seeded, same as
  a never-touched pre-existing one. Stroop and any exercise where the
  background genuinely IS the stimulus were never given a `bgColorKey`
  field in the first place (pre-existing, unrelated to this feature) so
  they're correctly absent from the registry with no special-casing
  needed.
- **`applyMasterBgDefaultEverywhere()`**: reads each target's *raw*
  localStorage (not the already-loaded in-memory prefs object, which may
  already carry an in-memory-only default from an earlier code path) to
  distinguish "key genuinely never set" from "explicitly set", then writes
  + persists the Master default only into the former. Runs once at page
  load (right after `loadMasterPrefs()`, so it also covers any exercise
  added to the roster since the client last touched the Master default -
  relevant given the autonomous Test-Bereich Routine keeps adding new
  ones) and again every time the Master default itself changes (colour
  pick or intensity slider), so a client who sets the default AFTER
  already having explored a few exercises still gets it applied to
  whichever ones they hadn't customised yet.
- **`masterPrefs` gained two fields**: `defaultBgColorKey: null` (a
  `STROOP_COLOR_LIB` key or null = "kein Standard"),
  `defaultBgIntensity: 0` (0-1, jumps to 0.5 automatically on first colour
  pick, same "sensible non-zero starting point" behaviour the per-exercise
  pickers already have). Validated the same way as every other
  `masterPrefs` field in `loadMasterPrefs()` (unknown colour key or
  out-of-range intensity silently resets to the null/0 default rather than
  failing).
- **UI**: new "Feineinstellungen" group in `#masterSettingsSheet`, above
  the existing restrictions groups - a `buildSingleSelectPicker`/
  `syncSingleSelectPicker` swatch grid (`STROOP_COLOR_LIB`, the same
  generic picker every per-exercise bg-colour control already uses, not a
  new one), a "Keinen Standard vorgeben" text-link (hidden while no
  default is set), and an intensity slider row (hidden the same way).
  `syncMasterBgUI()` wired into `openMasterSettings()` alongside the
  other three `syncMaster*UI()` calls.
- **Real bug found and fixed along the way**: adding
  `masterPrefs.defaultBgColorKey` references inside
  `wireBgIntensityControl`'s `renderTransfer()` threw
  `"Cannot access 'masterPrefs' before initialization"` - `wireBgIntensityControl(state, {...})`
  is called for Visual's OWN bg picker very early in the file (~line 2935)
  and its `sync()`/`renderTransfer()` run *immediately* at module-init
  time, well before `masterPrefs` itself is declared (~line 4708). Fixed
  the same way the file's own pre-existing `BG_SOURCES` loop already
  handles this exact class of problem (its in-code comment: "a source
  whose own prefs object is declared later in the file... throws a TDZ
  error - skip it for now, it'll render fine once actually opened") - wrap
  the new block in `try/catch`. Confirmed fixed: the pageerror disappeared
  and the Master sheet + all seeding assertions passed on rerun.
- **Deliberately out of scope**: Test-Bereich exercises (Go/No-Go, Simon,
  etc.) do not get the one-click transfer button - a separate, earlier,
  pre-existing scope decision documented in-code ("no transfer/preset-save
  here, unlike those four [Remember/Blitz/Flash/MOT]") that this feature
  didn't reopen. They still get the automatic-seeding half in full; the
  one-click button is additive convenience on top for the four domains
  that already had a transfer row for other reasons.

Test: `tests/master_bg_default_test.py` - seeds Simon-Test with its own
explicit colour before the Master default is ever touched (proves
pre-existing customisation survives), sets a Master default and confirms
the intensity row/"Keinen Standard" link appear and the slider jumps to
50%, confirms a never-touched exercise (Go/No-Go) seeds correctly while
Simon-Test stays untouched, confirms Go/No-Go's own picker shows the
seeded colour as active and correctly has NO transfer row, confirms
Remember DOES offer the one-click button and that clicking it actually
switches Remember's own colour, and confirms clearing the Master default
afterwards does not retroactively undo anything already seeded.

