# 37 – Neuro-Aktivierung (hidden area, Idee 68, 2026-10-08)

Fabian 08.10. approved Idee 68, name "Neuro-Aktivierung": guided activations
with equipment (Vibrationsgerät, Massageball) that only clients see whose
trainer unlocked them, plus single exercises a trainer can hand out inside a
Kombi code ("Spezialübung von deinem Trainer") without unlocking the area.

## Unlock
- Code type `neuro-unlock`: `{type:"neuro-unlock", name, lock?}` through the
  normal code flow (`lookupProgram` / `CODE_API`, the Worker stores configs
  generically, no Worker change). `codeDefProblem` accepts it,
  `rememberTrainerProgram` skips it. `openProgramIntro` → `applyNeuroUnlockCode`:
  sets `fwmc-neuro-unlocked-v1` = true and opens `#neuroHome` with the notice
  "Neu für dich freigeschaltet: Neuro-Aktivierung."; `lock:true` removes the
  key again (area hidden, back to Training). Works from every code box.
- `neuroUnlocked()` = the key, or `fwmc-test-neuro` in automated browsers only.
- Hidden = no hub tile, `?bereich=neuro|neuro-aktivierung` falls back to
  Heute, `showScreen("neuroHome"|"neuroReady")` redirects to Heute, no Kombi
  group (`COMBO_CAPTURE_ENTRIES.neuro` returns []), not in `PLAN_AREAS`
  (Wochenplan areas, tray "Bereiche"/"Übungen", Heute tiles), no gear cards
  (`GEAR_ITEMS[].neuro`). `syncNeuroArea()` adds/removes `NEURO_AREA` in
  `PLAN_AREAS` at start-up and on (un)lock; `AREA_BY_KEY.neuro` always exists
  so old entries keep label/colour.
- Backup: the key starts with `fwmc-`, so a restored backup keeps the unlock.

## Area frame (same "new area needs" list as Aktivierung, docs/notes/31)
- Key `neuro`, label "Neuro-Aktivierung", short "Neuro", colour `#8a4b2a`
  (`--area-neuro`, ink light `#8a4b2a` / dark `#d39a78`), icon = vibration waves.
- Training hub: own row "Für dich freigeschaltet" / "Von deinem Trainer, nur
  mit Code." directly under the four core tiles (never takes a core place,
  `HUB_CORE` unchanged), tile in the `.hub-extra` look, no badge (Prüfer
  08.10.: the unlock is said once, in the row heading; tile text "Geführt
  mit Vibration oder Massageball."). Heute area tiles follow `PLAN_AREAS`.
  `#neuroHome` hero: "Geführte Aktivierungen, meist mit Hilfsmitteln wie
  Vibrationsgerät oder Massageball.", tiles under "Übungen" (Gelenke
  kreisen needs nothing). "Z‑Vibe" uses U+2011 (no break at the hyphen).
- `#neuroHome`: logo bar + ‹ (AREA_HOME_IDS), old tab row without an active
  tab (`neuroAreaActive`, like Eigenes Training/Aktivierung), Kombi link,
  hero, unlock notice, `.code-card` (`NEURO_CODE_CTX`), tiles `#neuroGrid`
  (rendered once from `NEURO_EXERCISES`, `.nat-tile` look, badge in the area
  colour), "Gesamter Trainingsverlauf" (`HISTORY_PREFIXES` "neuro"), footer.
  SCREENS, HOME_SCREENS, AREA_HOME_IDS, AREA_TO_SECTION, currentHomeScreen
  know it. Long press on a tile (`LP_SEL`, `data-neuro-ex`): Öffnen /
  Starten / Planen / Kombi.

## Templates (`NEURO_EXERCISES` in app.js)
`{ id: { title, tag, desc, intro, need, safety, gear, defaults, icon, steps } }`,
step `{ t, side, dirs?, icon? }` with side
`lr` (links + rechts one after the other, order = Feineinstellung "Seite zuerst"),
`dir` (two directions from `dirs`), `beide`, `wechsel` (abwechselnd: the side
pill flips every `altS` and the new side is spoken), `none`.
- **Vibration links / rechts** (Vibrationsgerät wie Z-Vibe): Wange, Kiefergelenk,
  Nacken seitlich, Handinnenfläche, Fußsohle, je links/rechts. 20 s, Umsetzen 5 s.
- **Massageball: Fußsohlen**: Ferse→Zehen, Fußballen kreisen, Fußgewölbe
  Druck halten/lösen (je Seite), beide Füße Zehen spreizen. 30 s, Umsetzen 5 s.
- **Massageball: Hände**: zwischen den Handflächen (beide), drücken/lösen,
  Handrücken, Fingerspitzen (je Seite), von Hand zu Hand (abwechselnd). 30 s.
- **Gelenke kreisen** (kein Hilfsmittel): Kopf im Halbkreis, Schultern
  (nach hinten/vorne), Ellbogen (L/R), Handgelenke (außen/innen), Hüfte und
  Knie (rechts/links herum), Fußgelenke (L/R); one stick figure per step
  (`NEURO_ICONS`, STRETCH_ICONS style: figure + dashed ring at the joint). 20 s.
- A new template = one `NEURO_EXERCISES` entry (+ HILFSMITTEL/GEAR entries if it
  needs equipment, + the dashboard copy `NEURO_EX`).

## Settings, presets
- Prefs per template in `fwmc-neuro-prefs-v1` (`{ [id]: {stepS, reps, order,
  altS, moveS, takt, bpm} }`, `normalizeNeuroPrefs` clamps: stepS 10-120 in 5,
  reps (Durchgänge) 1-3, order lr|rl, altS 2-15, moveS (Umsetzen) 0-30 in 5,
  bpm 30-120 in 5).
- Ready `#neuroReady`: Hilfsmittel note (`.hilfsmittel-note` + "Alle
  Hilfsmittel"), Dauer pro Schritt (20/30/45 s + slider), Durchgänge (1-3 +
  total), Feineinstellungen (Seite zuerst, Seitenwechsel, Umsetzen, Takt +
  tempo), Ablauf (step list with icons), Sicherheitshinweis (closed details,
  template sentence + general sentence + "nicht auf Wunden …, Herzschrittmacher,
  Schwangerschaft … ärztlich abklären"), presets `fwmc-neuro-saved-v1`
  (`{id,name,ex,prefs}`, listed per template; tap = apply + start, in capture
  only fills the draft), "Training starten" (`LEADIN_START_IDS` → 3-2-1).
  Controls use `data-nr-f/-v` (choices), `data-nr-r` (sliders), `data-nr-out`,
  `data-nr-show`, bound by `neuroBind`/`neuroSyncControls` (ready + pause sheet).

## Player `#neuroPlayer`
- `.player.calm-dk` (dark in dark mode), reuses the Eigenes-Training stage
  (`.free-stage`): "Schritt n von N · Durchgang", title, Spezialübung tag,
  stick figure, instruction (`.free-run-item`), side pill `.neuro-side`
  (Links / Rechts / Beide Seiten / Abwechselnd · Links / direction; grey
  "Umsetzen · …" during the move phase), countdown, "Als Nächstes: …",
  « ↻ » (`stepCtx`, swipe), bar `neuroBackBtn` "✕ Beenden", `neuroPauseBtn`
  "Pause", `neuroFsBtn` (`wireFullscreen`).
- Ton: every step start is spoken via `cueSay` ("Fußsohle. links", move phase
  "Umsetzen. Gleich: …"), side flips in "abwechselnd" are spoken, beeps in the
  last 3 s + long beep at the end (`playWorkoutBeep`), Takt = `playCueTickTone`
  at `bpm` during work phases (not in the last 3 s), all through `cueVolume()`.
  First Takt run on iPhone shows the silent-switch hint (`silentSwitchHint`).
- Pause sheet `#neuroPauseOverlay` (own sheet like Optodrum): Takt an/aus +
  tempo, Dauer pro Schritt (from the next step on: each phase keeps its
  `curDur`), Seitenwechsel; standalone saves to the own prefs, Kombi = this run.
- End: natural end = done ("Geschafft!", rating, Nochmal, Zur Übersicht);
  "»" past the last step = aborted (`setDonePanelAborted`, "Abgebrochen · …");
  "✕ Beenden" = back to the ready screen without an entry (like Eigenes
  Training). History `{kind:"neuro", title:"Neuro-Aktivierung · …", neuroEx,
  seconds, note}` → `historyAreaOf` = neuro; "Weitermachen aus dem Verlauf"
  (continueFromHistory) reopens the template.
- Test hooks (automated browsers): `window.__neuro()`, `window.__neuroSkipTime(s)`,
  `window.__neuroLog`, `window.__neuroTicks`.

## Kombi + Wochenplan (unlocked clients)
- Kombi group "Neuro-Aktivierung" (`COMBO_DOMAIN_ORDER` last), block
  `{domain:"neuro", ex, prefs}` (own copy), capture/edit on `#neuroReady`
  ("Baustein: …" / "Baustein übernehmen", `comboNeuroCapture`, own prefs never
  touched), `COMBO_EDIT_OPENERS.neuro`, label/meta/seconds, playback in
  `startComboBlock` → `startNeuroRun(ex, prefs, {special})`; first Baustein gets
  the 3-2-1 (calm). Beenden in a Kombi quits the Kombi, the end goes on.
- Wochenplan: area `neuro` (only in `PLAN_AREAS` while unlocked), select and
  tray "Übungen" list `neuro:<id>` (`whatOptions`, `entryTitle`, `startEntry`).
  A planned entry whose area was locked again opens Heute.

## Spezialübung von deinem Trainer (not unlocked)
- A trainer `combo-program` (or a programme of a `combo-bundle`) may contain
  neuro blocks. `startComboBlock` plays them regardless of the unlock;
  `neuroBlockIsSpecial(block)` (= neuro block and area locked) shows
  "Spezialübung von deinem Trainer" in the run (`#neuroRunSpecial`), above
  the title of the Kombi pause (`#comboTransitionSpecial`), in the programme
  list of a combo-bundle (`.special-tag`), and as block result
  (`blockResultPush` → "Eben: …" in the next pause, closing panel and the
  combo history note "Vibration links / rechts: Spezialübung von deinem
  Trainer · 2:30"). No own history entry (the Kombi is the entry).
  Prüfer 08.10.: the "Eben: …" line reads only "erledigt · 2:30" (the tag
  already stands above the pause title); the history note keeps the tag via
  `blockResultPush(run, label, text, note)` (optional 4th arg). One tag
  style everywhere: teal outline; in the player fixed hex (#007094 light,
  #39a7cc on #16262b in the dark `.calm-dk` player). Durchgänge chips read
  "1×/2×/3×"; Dauer pro Schritt is the slider only. The pause sheet says
  one sentence: "Der Takt gilt sofort, die Dauer ab dem nächsten Schritt.
  Beides bleibt gespeichert, wie auf der Übungsseite." (own run) or "Nur
  für diesen Durchgang." (Kombi/code).
- It can't leave the code: `neuroStripBlocks` removes neuro blocks when a
  locked client inserts a trainer programme ("einfügen") or adapts one into an
  own Kombi (`openComboScreen(seed)`); a trainer programme made only of neuro
  blocks is not offered at all. The area stays hidden.
- Not covered: neuro blocks in plain VT `bundle`/programme codes (different
  engine; a Kombi code is the way to hand them out).

## Hilfsmittel
- `HILFSMITTEL["neuro-vibration" | "neuro-ball-fuss" | "neuro-ball-hand"]`
  (gear ids) + `GEAR_EX_OPEN` openers; the ready screen itself shows
  `NEURO_EXERCISES[..].need`.
- `GEAR_ITEMS` `vibration` (Vibrationsgerät), `massageball` (Massageball oder
  Massagepilz) and `bonephones` (Knochenschall-Kopfhörer, prepared, no
  exercise yet) carry `neuro: true` = only shown with the area unlocked.

## Trainer-Dashboard
- Baukasten Bereich "Neuro-Aktivierung" (`#neuroBuilder`) with two modes:
  "Spezialübung (Kombi-Code)" = catalog copy `NEURO_EX` (id, title, default
  seconds) → blocks with Sek. pro Schritt, Durchgänge, Takt + tempo, Pause
  danach (0-180) → `{type:"combo-program", blocks:[{domain:"neuro", ex,
  prefs, pauseAfterS}]}`; "Bereich freischalten" → `{type:"neuro-unlock"}`.
  Both reopen in the builder (`configToBuilder`); mixed Kombis stay JSON.
  The codes table marks them with a "Spezialübung" / "Neuro freischalten" pill;
  the JSON hint documents both shapes. Not in the plan builder's `AREAS` on
  purpose (a plan entry would point clients without the unlock at a hidden area).

## Stays in the Test-Bereich for now
Ton-Sequenz (docs/notes/34) and Farbbrille (docs/notes/30) stay in the
Test-Bereich until Fabian has tested them himself; they move into
Neuro-Aktivierung afterwards (then: one `NEURO_EXERCISES`-style tile or an
`ACTIVATION_LINKS`-like link entry each, never a copied engine; the
Knochenschall card then gets its exercise chip).

## Not wired on purpose
Cardio-Zusatzaufgabe (not a VT/NAT stimulus), CVD (no right/wrong),
MASTER_BG_TARGETS / Größe+Farbe (no stage objects), Sanfte Reize (no fast
light changes), Weitermachen (short single runs; a Kombi resumes as usual).

## Texte von Fabian prüfen
All client-facing texts are neutral (no efficacy or therapy claims) and need
Fabian's review before the area is handed to clients:
- Hero: "Gezielt aktivieren, Schritt für Schritt." / "Geführte Aktivierungen
  mit Hilfsmitteln wie Vibrationsgerät oder Massageball. Dein Trainer hat
  diesen Bereich für dich freigeschaltet."
- Hub row "Für dich freigeschaltet" / "Von deinem Trainer, nur mit Code.",
  tile text "Geführt mit Hilfsmitteln, für dich freigeschaltet."
- Tag "Spezialübung von deinem Trainer".
- Every template's `desc`, `intro`, `need`, `safety` and all step texts
  (list above), especially the Vibration places (Wange, Kiefergelenk, Nacken
  seitlich) and the Kopf step of "Gelenke kreisen".
- Sicherheitshinweis: "… Arbeite nur so lange und mit so viel Druck, wie es
  angenehm ist. Bei Schmerzen, Taubheit, Schwindel oder Unwohlsein sofort
  aufhören." + "Nicht auf Wunden, Entzündungen, frischen Verletzungen oder
  Krampfadern. Mit einem Herzschrittmacher, in der Schwangerschaft oder bei
  einer bekannten Erkrankung kläre die Übung vorher ärztlich ab."
- Gear cards Vibrationsgerät ("z. B. ein Z-Vibe" - brand name, Fabian decides
  whether it stays), Massageball oder Massagepilz, Knochenschall-Kopfhörer.
- Defaults (20/30 s per step, 5 s Umsetzen, Seitenwechsel alle 4 s).

## Privacy
Nothing new leaves the device: the unlock is the existing code lookup; state,
prefs, presets and history stay in localStorage.

Test: `tests/neuro_aktivierung_1008_test.py` (screenshots `tests/screenshots/neuro/`);
also `tests/text_wrap_audit_test.py` (area "neuro", every ready screen),
`tests/hint_overlap_all_test.py` (`run_neuro`), `tests/exercise_coverage_test.py`
(`--neuro` = unlocked run; without it the area must stay off the hub).
