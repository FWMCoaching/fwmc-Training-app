# Reset-Buttons + "Master aktiv"-Hinweis für Hintergrundfarben (added 2026-09-29)

Client's follow-up to the Master-Einstellungen background-colour cascade
(task above): a way to deliberately go back to following the Master
default after customizing an exercise (not just the existing one-way
"Wie in den Master-Einstellungen" copy), a bulk version of that for every
exercise at once, and a visible indicator when an exercise's colour is
currently coming from the Master default rather than its own choice -
explicitly the "simple version" (no separate opt-out toggle, no full
"Werkseinstellungen" wipe of every setting) after discussing scope.

- **`bgCustom` (new boolean field, alongside `bgColorKey`/`bgIntensity`
  on every one of the 26 background-colour domains)** replaces "does raw
  storage have an explicit `bgColorKey`" as the signal for "has the
  client customized this exercise" - that raw-storage check
  (`applyMasterBgDefaultEverywhere()`'s original approach, still exactly
  right for the seed-once feature it was built for) stops being usable
  the moment ANY value is ever written for a target, since a seeded
  value and a hand-picked one look identical in storage afterwards.
  `true` = explicit customization (a colour pick, an intensity drag, a
  "Wie bei X" transfer from another exercise, loading a saved bg-colour
  preset); `false` = still following Master (never touched, or
  explicitly reset). `wireBgIntensityControl`'s `apply(colorKey,
  intensity, custom)` now takes this as a third argument, defaulting to
  `true` (every pre-existing call site was already a genuine
  customization) - only the "Wie in den Master-Einstellungen" button
  passes `false`, since tapping it means "sync me to Master", not "copy
  this value once and go independent again".
- **Migration**: a save from before `bgCustom` existed is treated as
  customized if it already had an explicit colour in raw storage
  (preserves the established "never silently override a real choice"
  guarantee), otherwise as still-following - done once per target,
  inside `applyMasterBgDefaultEverywhere()` itself, since it already
  iterates every target via `MASTER_BG_TARGETS`.
- **Real bug found and fixed**: the very first call to
  `applyMasterBgDefaultEverywhere()` (right after `loadMasterPrefs()`,
  the only one guaranteed to run on every page load with nothing else
  needed first) silently skipped every domain declared later in the file
  - which is most of them, Test-Bereich/Blitz/Flash/MOT included - via
  the pre-existing `try { target = factory() } catch { return }` TDZ
  guard. That guard is correct and necessary (those domains' `const`s
  genuinely don't exist yet at that point in the file), but it meant
  their `bgCustom` migration silently never ran for an entire session
  unless something else (e.g. touching the Master default itself)
  happened to call the function again later - caught by seeding
  `fwmc-simon-prefs-v1` with its own explicit colour before ever loading
  the page once, matching exactly how a real pre-existing customization
  would look, then checking Simon's reset button showed up on the very
  first screen visit, no other interaction first. Fixed by wrapping only
  this one initial call in `setTimeout(applyMasterBgDefaultEverywhere, 0)`
  - deferred just long enough for every `const` later in the file to
  finish being declared (synchronous module-init always completes before
  any deferred callback runs), so this call now reaches every domain
  correctly on every load. The later, UI-triggered calls (clicking the
  Master colour picker, its intensity slider) stay synchronous, since
  those already run long after full module init.
- **Per-exercise UI**: one new `.bg-master-status` div per ready screen
  (29 of them - one per existing `XBgContrastHint`, i.e. every domain's
  primary settings screen, Remember/Flash/MOT/VT's own "Trainingsmodus"
  screens included, but deliberately NOT the pause overlays - resetting
  mid-exercise wasn't part of the ask), rendered by `sync()` into one of
  two mutually-exclusive states: `bgCustom` true → an "Auf Standard
  zurücksetzen" button; false and a Master default is set → "Master-
  Einstellungen aktiv" text with a "zu den Einstellungen" link
  (`openMasterSettings()`). Neither shown when nothing applies (no
  customization, no Master default set). Built via `createElement`/
  `textContent`, not `innerHTML` - a `<button>` with a value-less
  `data-*` attribute past certain preceding text tripped a genuine
  Chromium HTML-parser bug during testing (mangled the attribute into
  `data-foo"=""`, breaking the `querySelector` right after; reproduced
  even on a blank page with none of this app's code loaded), so building
  the nodes directly sidesteps that entirely rather than working around
  one specific string shape.
- **`resetToDefault()`** (per exercise, inside `wireBgIntensityControl`):
  sets `bgCustom = false` and `bgIntensity = 0` (no background - the
  shipped default for every exercise; client's own words, "auch wenn der
  Hintergrund meist weiß sein wird"), then calls
  `applyMasterBgDefaultEverywhere()` so a live Master default (if any) is
  adopted immediately, not just on the next reload.
- **`resetAllBgToMasterDefault()`** (Master-Einstellungen, "Alle eigenen
  Hintergrundfarben zurücksetzen", behind a `confirm()` same as
  `clearHistory()`'s "Verlauf löschen"): the same reset applied to every
  `MASTER_BG_TARGETS` entry at once.

Test: `tests/bg_reset_master_status_test.py` - Go/No-Go never touched
shows neither state until a Master default is set, then shows "Master
aktiv" with a working link back to Master-Einstellungen; customizing it
swaps in the reset button and persists the customization; resetting
swaps back to "Master aktiv" and persists that too; a pre-seeded
Simon-Test (simulating a save from before this feature existed) shows
the reset button on the very first visit, no prior interaction needed;
the global reset button reaches it too, clearing `bgCustom` and
re-adopting the Master colour, after which it also shows "Master aktiv".

