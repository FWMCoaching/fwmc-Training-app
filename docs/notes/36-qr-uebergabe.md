# QR-Übergabe (Idee 69, 2026-10-08)

Fabian approved variant A (time range + checkboxes) plus "Kunden-Training
starten". Design draft: the five steps below. A client trains on the
trainer's phone; the trainer hands the runs over with a QR code, the
client's app takes them into its own history. **No server is involved.**

## Trainer side
- Fortschritt (`#progressScreen`) now also has the usual "Gesamter
  Trainingsverlauf" section (prefix `progress` in `HISTORY_PREFIXES`) and
  below it the group `#handoverGroup`: "An Kunden übergeben"
  (`#handoverOpenItem`/`#handoverOpenBtn`) and "Kunden-Training starten"
  (`#clientRunItem`) only with the feature `trainer-tools` (see
  "Freischaltungen" below); "Trainer-QR-Code scannen"
  (`#handoverScanOpenBtn`, quiet `.text-link`, 44 px) for everyone.
  A running Kunden-Training (or runs waiting) stays visible and endable
  after a lock code.
- The range screen has the pre-check card `#handoverPrecheck`
  (`.handover-precheck`, kicker style of the Hilfsmittel note) above the
  button: "Bevor dein Kunde scannt:" / "Hat er die App auf seinem Handy (am
  besten auf dem Startbildschirm)?" / "Er tippt in seiner App unter
  Fortschritt auf „Trainer-QR-Code scannen“." The line under the QR code
  uses the same wording.
- `#handoverScreen`: chips `seit <Zeit>` / 30 / 60 / 90 Min (`.choice-row
  .handover-range`). "seit" shows a time picker (`#handoverSinceInput`,
  5-min steps); default = earliest entry of the last 2 hours rounded down to
  5 min (`hoDefaultSince`, 60 min back without entries). A "seit" time later
  than now means yesterday. The list (`.history-list` + `.checkbox-row`)
  shows the entries in range, all checked; changing the range checks all
  again. Button "N Trainings übergeben", disabled at 0.
- `#handoverQrScreen` "Scannen lassen": one canvas QR (`#handoverQrCanvas`,
  white plate in both themes, ECC M, 4-module quiet zone, drawn at ~720 px
  and shown at min(76vw, 340px)). Large payloads: ‹ "Code 1 von N" ›.
  `data-url` on the canvas holds the encoded URL (tests read it).
- "Fertig": source history → `confirmDialog` title "Diese N Trainings auf
  deinem Gerät löschen?", text "Dein Kunde hat sie jetzt in seiner App.",
  "Löschen"/"Behalten". Löschen removes exactly those ids from
  `fwmc-history-v1` and subtracts them from `fwmc-progress-v1`
  (`hoDeleteFromHistory`). Source Kunden-Training → no question, the runs
  are dropped.

## Payload (what leaves the trainer's phone)
`{v:1, e:[[id, tsSeconds, kind, title, seconds, note, rating, aborted,
exId, progKey], …]}` per history entry, trailing empty fields dropped.
Nothing else: no name (`fwmc-name-v1`), no settings, plan, freeId,
device id or code (a Ton-Sequenz "Nachher" text travels inside `note`).
JSON → `deflate-raw` via CompressionStream ("z" prefix) or plain ("j") →
base64url. Token `"<i>.<n>.<group>.<chunk>"`; URL `<app URL>#import=<token>`.
App URL = current origin+path on github.io / fabian-westermann.de /
localhost, otherwise (Artifact preview) the Pages URL (`HO_APP_URL`).
One code while the whole URL is ≤ 1200 chars (`HO_SINGLE_MAX`), else the
data is split into equal chunks ≤ 1000 chars (`HO_PART_MAX`). About 20-30
entries fit one code.

QR generator: `qrcode.js` in the repo root = qrcode-generator 1.4.4
(Kazuhiko Arase, MIT, from npm, unchanged), loaded lazily by
`hoLoadQrLib()` only on the QR screen (the dashboard loads it with a
`<script src="qrcode.js">`); QR reader: `jsqr.js` = jsQR (cozmo,
Apache-2.0, `jsqr.LICENSE.txt`, one header line, otherwise unchanged),
loaded lazily by `hoLoadJsQr()` only when the scanner has no
BarcodeDetector. Both precached in sw.js (CACHE v9).
**Artifact publish must include `qrcode.js` and `jsqr.js` in `files`.**

## Client side (import)
- Start-up: `#import=` skips the code lookup (`openFromHash`), the slides
  and the tips; `hoCheckHash()` clears the fragment at once
  (`history.replaceState`), then decodes. Also on `hashchange`.
- Split codes: parts collect in localStorage `fwmc-import-parts-v1` (not
  sessionStorage: the iPhone camera opens each scan in a new Safari tab),
  30 min lifetime, excluded from backups. Missing part → sheet "Code 1 von 2
  gelesen / Scanne jetzt Code 2".
- `#handoverImportSheet`: "N Trainings von deinem Trainer übernehmen?" +
  list, "Übernehmen" / "Nicht jetzt". Übernehmen (`hoImport`) adds the
  entries with `trainer: 1`, `srcId`, original ts; dedupe by
  `srcId|tsSeconds` (and own `id|ts`), so a second scan adds nothing
  (toast "schon in deinem Verlauf"). They count for progress (progress is
  seeded first so nothing counts twice) and tick plan entries. History
  rows show `.h-tag` "bei deinem Trainer".
- Invalid data (format, base64, JSON shape, any field out of range, no
  DecompressionStream for a "z" code) → one message "Das hat nicht
  geklappt", nothing written.

## Trainer-QR-Code scannen (in-app scanner, 2026-10-08)
Fortschritt › "Trainer-QR-Code scannen" opens `#handoverScanSheet`
(`.scan-sheet`, full height on phones, grab bar from the shared sheet
code): `getUserMedia({video:{facingMode:{ideal:"environment"}},audio:false})`
into `<video playsinline muted>`, a frame overlay (`.scan-frame`), help
"Halte die Kamera auf den QR-Code deines Trainers.", status line, small
"Code von Hand einfügen" (opens `#handoverPasteSheet`) and "Abbrechen".
- Decoding: `BarcodeDetector` when it supports `qr_code`, else jsQR on a
  canvas downscaled to 720 px (`inversionAttempts: "dontInvert"`), every
  160 ms (`hoScanTick`).
- A handover token goes through `hoCollect` (parts: "Code 1 von 2 gelesen.
  Halte die Kamera jetzt auf Code 2."); the last part stops the camera,
  closes the sheet and calls `hoHandleData` (the same "übernehmen?" sheet,
  dedupe, `fromPaste` = no Safari hint).
- A trainer code (`<app url>#code=<CODE>` or the bare code text,
  `codeFromQrText`) stops the camera and runs `openCodeAsTyped(code)`:
  Training page, code into `#moreCodeInput`, `goMoreCode()` - exactly the
  code card's path (lookupProgram, codeDefProblem, showCodeError, success
  flow). Anything else: "Das ist kein Code deines Trainers…", scanning goes on.
- Errors: no secure context / no `mediaDevices` / NotFound /
  NotAllowed+Security / other → one calm sentence in `#handoverScanError`,
  the video hidden, the fallback link stays.
- The camera stops on Abbrechen, backdrop, Escape, pull-down (a
  MutationObserver on `hidden`) and when the page is hidden.
- Test hook `window.__hoScan()` = {open, running, detector, tracks}.
- Privacy sheet: "Beim Scannen des Trainer-QR-Codes nutzt die App die
  Kamera nur, um den Code auf deinem Gerät zu lesen. Kein Bild wird
  gespeichert oder verschickt."

## Trainer codes as QR (Fabian 08.10.)
- Dashboard: "QR-Code zeigen" in every row of the codes table and after
  "Speichern" (`#pQrBtn`) opens `#codeQrSheet`: big QR (qrcode.js, ECC M)
  for `<app url>#code=<CODE>` (app url = the dashboard's own folder on
  github.io/fabian-westermann.de/localhost, else the Pages URL), the code
  as text and "Dein Kunde scannt in seiner App unter Fortschritt mit
  „Trainer-QR-Code scannen“ oder tippt den Code ein." Details notes/10.
- App: `#code=<CODE>` at start-up or on `hashchange` (`openFromHash`)
  clears the fragment and runs `openCodeAsTyped` (no slides/tips on top);
  the old `#<code>` link keeps its Visual-Training path. The paste field
  also accepts a `…#code=…` link. An error on a collapsed (quiet) code card
  now opens the card (`showCodeError`), so the message is seen.

## Freischaltungen (code type `feature-unlock`, 2026-10-08)
`{"type":"feature-unlock","name":"…","features":["trainer-tools"]}`, with
`"lock":true` to switch off again; one code may carry several features.
Store `fwmc-features-v1` = `{feature: true}` (in backups via the fwmc-
prefix); tests: `fwmc-test-<feature>` (webdriver only). Not added to the
code history. Registry `FEATURE_UNLOCKS` in app.js, per entry: `label`,
`on`/`off` (toast, Du-form), `tab` + `screen` + `focus` shown after an
unlock, `apply()` re-renders what depends on it; every active feature sets
`body.feat-<key>` (applied at start-up and after a code), so CSS can show
or hide things without code. **A new feature = one `FEATURE_UNLOCKS`
entry in app.js + one entry in dashboard.html's copy** (the "Freischaltung"
kind builds its checkboxes from it; label + hint text). `codeDefProblem`
rejects unknown features. Worker: stores configs generically, no type
validation, so no Worker deploy is needed.
- `trainer-tools` (only entry so far): "An Kunden übergeben" + "Kunden-
  Training starten" on Fortschritt; toast "Trainer-Werkzeuge sind jetzt
  freigeschaltet. Du findest sie unter Fortschritt." / "… wieder
  ausgeblendet."

## iPhone: Safari vs. home-screen app
A link from the iPhone camera opens in Safari, whose storage is separate
from the home-screen app. In iOS Safari outside standalone (`isIOS &&
!standalone`; tests: `fwmc-test-ios-browser`) the sheet explains this and
offers "Code kopieren" (copies `1.1.code.<data>`, clipboard API with
execCommand fallback) next to "Hier in Safari übernehmen". In the
home-screen app: Fortschritt › "Trainer-QR-Code scannen" › "Code von Hand
einfügen" (`#handoverPasteSheet`) runs the same import (whitespace in the
pasted text is ignored; a whole `…#import=…` URL works too). Easier: scan
inside the home-screen app directly, then Safari is never involved.

## Kunden-Training
- `fwmc-client-session-v1` = `{start, snap}`. While set, `addHistory()`
  writes to `fwmc-client-runs-v1` (flag `client: <start>`) instead of the
  history: no `recordProgress`, no reminder resync. So stats, streaks,
  Wochenabschluss, plan ticks, calendar and "Weitermachen" from history
  never see them. `levelSuggestAfter` returns early. `rateHistory` and the
  Ton-Sequenz "Nachher" note patch the client run (`hoPatchClientRun`).
- On start the keys matching `HO_SNAP_RE` (every `fwmc-*-best-v1`,
  resume, level-suggest, ton/eyecount last) are snapshotted and put back
  on "Beenden", so a client's bests never become the trainer's.
- Strip `#clientRunStrip` (fixed, #007094, 48 px + safe area; the sub page
  bar sticks below it via `body.client-run-on`) "Kunden-Training · seit
  HH:MM · N Trainings" + "Beenden"; only while a `.screen` is visible.
- "Beenden" → straight to the QR screen with those runs; "Fertig" drops
  them. Left via ‹ instead: Fortschritt shows "N Trainings aus dem
  Kunden-Training sind noch nicht übergeben" with "QR-Code zeigen" /
  "Löschen" (confirmDialog).

Privacy sheet: one sentence under "Was wird auf deinem Gerät gespeichert?".
Test: `tests/qr_uebergabe_1008_test.py` (OpenCV decode when installed:
`pip install opencv-python-headless`), `tests/pruefer_fixes_1008_test.py`
(unlock/lock, scanner with a fake canvas camera + jsQR, BarcodeDetector
stub, permission denied, code QR, `#code=` link, dashboard QR decoded with
jsQR); wrap audit areas "fortschritt", "uebergabe", "scannen".

Open / for Fabian to check on his iPhone: in the home-screen app the
camera prompt (iOS asks once per app; after "Nicht erlauben" only
Settings › Safari/App brings it back), the rear camera is chosen, scan
speed on a dense code; camera scan of a dense code
(150 entries = several codes), Safari tab per scan collecting parts,
"Code kopieren" → paste in the home-screen app, the strip under the notch.


## Safari-Hinweis für #code= (2026-10-08 abends, Fabian)
On the iPhone the camera app opens Safari, whose storage is not the home-screen
app's. A `#code=` link in iOS Safari (`hoIosBrowser()`) therefore asks once via
`confirmDialog` ("Lieber in der App scannen": "Hier in Safari öffnen" / "Abbrechen")
before `openCodeAsTyped`; everywhere else it runs at once. The trainer pre-check
card and the dashboard QR hint both say: scan in the app, not with the camera app.
Test: `tests/safari_code_hinweis_1008_test.py`.

## Trainer-Menü (2026-10-08 abends, Fabian)

Everything the `trainer-tools` unlock gives lives in one sheet `#trainerMenuSheet`,
opened by the round `.trainer-mode-btn` in the free ‹ slot of the four main pages
(Heute, Training, Fortschritt, Mehr; never on area pages). Without the unlock
(and no mode running) the slot stays empty. Placement of the handover/scan items
next to the code cards: `HO_HOSTS` + `hoPlaceGroup()`; the trainer items
(`#handoverOpenItem`, `#tmStoreItem`, `#clientRunItem`) are moved into `#tmToolsHost`.

Modes (`tmSetMode`):
- **Mein Training** (`own`): everything counts. Button shows the icon.
- **Mit Kunde** (`client`): Kunden-Training (`fwmc-client-session-v1`), runs go to
  `fwmc-client-runs-v1` stamped `client: <session start>`; petrol `#007094` (Fabian 09.10., was orange),
  button word "Kunde". Ending it opens the selection with exactly this session ticked.
- **Ausprobieren** (`try`): nothing counts, runs go to `fwmc-try-runs-v1`
  (`tryRun: true`), bests snapshot/restore; violet `#5d4a8f`, button/tag word
  **"Test"** (was "Probe", Fabian found it odd). Starting it during a Kunden-
  Training pauses that session; the gap is never ticked.
- 3 h limit per mode, "… fortsetzen?" after 30 min in the background
  (`tmCheckReturn`, `fwmc-trainer-seen-v1`). In a player only a thin line (`.slim`).

Retention: client runs and test runs 14 days (`HO_KEEP_MS`, `TM_TRY_KEEP_MS`); own
history is kept as always, but only its last 14 days are listed for trainers.

Selection before every QR (`hoRenderPick`, `hoPick`):
- `range` ("An Kunden übergeben"): time window; own runs ticked, test runs unticked.
- `client` (after a Kunden-Training): its runs ticked; test, own (tag "eigenes")
  and earlier client leftovers ("früher") unticked, so a run done in the wrong
  mode can still go along.
- `store` (**Gespeicherte Trainings**, `#tmStoreBtn`): every kind of the last 14
  days, nothing ticked, filter chips Alle/Kunde/Test/Eigene (`hoKind`), button
  "Alle … löschen" for the filter shown (`#handoverClearBtn`), swipe left on a row
  = Löschen (`SWIPE_ROWS`, event `ho-del`).

Deleting vs sending (Fabian): whatever is **sent** is removed everywhere
(`hoDeleteEverywhere`, own runs also leave Fortschritt). **Deleting** client/test
runs removes them; deleting **own** runs only hides them from the trainer lists
(`fwmc-trainer-hidden-v1`), history and Fortschritt keep them (`hoAskDelete`).
Test: `tests/trainer_menu_1008_test.py`; readability of every button on every
main page, light/dark: `tests/knopf_lesbar_1008_test.py`.

### Absicherung (Prüfer-Runde 09.10.)
- Snapshot (`HO_SNAP_RE`) covers bests/resume/levels plus settings, plan, code list, unlocks, events, Eigenes Training, notes, Ton, gear, reminders. A restore that changes a settings key (`HO_PREFS_RE`) reloads once (`hoReloadIfNeeded`), `hoAfterReload` then opens the selection or shows the toast.
- Starting client/test mode puts "Weitermachen" aside (`hoClearResume`; it comes back with the snapshot).
- Test → Mit Kunde: restore first, then start the session from the restored state, one reload.
- Mode checks (`tmCheckReturn`) never run while a `.player` is open; a 60 s interval also enforces the 3 h limit while the app stays in front.
- Time-window selection includes client runs; if there are any, only the latest Kunden-Training is ticked, never own runs.
- Split QR: "Fertig" before the last part asks "Alle Teile gescannt?". More than 20 parts or 200 runs cannot be sent at once.
- `hoPack` trims title (120) and note (300), so a long Kombi note never breaks the whole import.
- Backup excludes the session/mode keys. The trainer button shows a dot while client runs wait for handover.
- Ton-Sequenz "Nachher" also lands on test runs; level suggestions are off in test mode too.

## Nachtrag 09.10. morgens (Fabian)
- 3-Stunden-Grenze ersetzt: `tmCheckReturn` fragt nach 3 h nur „Läuft … noch?“
  (`fwmc-trainer-asked-v1` = letzte Frage, erneut alle 3 h), beendet selbst erst
  am nächsten Tag (`tmNextDay`: anderes Datum ab 04:00 oder > 12 h). Nie während
  ein Player oder `#confirmSheet` offen ist. Unversendete Trainings bleiben 14 Tage.
- Wartende Kunden-Trainings: Punkt am Trainer-Knopf in jedem Modus (im Modus
  „Mit Kunde“ zählt die laufende Sitzung nicht), `#clientRunPending` steht oben im
  Trainer-Menü, `#handoverWaitNote` in der Übersicht und beim Übergeben (mit
  „Nur Kunden-Trainings zeigen“). Petrol-Strich links wie der Kunden-Modus.

## Bestwerte + Einstellungen vom Trainer (2026-10-09)
- Kunden-Training clears the four NAT best stores after the snapshot (`hoClearBests`), so each client run carries the client's own session bests `bs`, the settings `ps` (`HO_SETTINGS`: remember, blitz, flash, mot, balance; never volume/colours) and the device kind `dk` (`hoAttachExtras` in `hoAddClientRun`).
- Payload v1 gains optional `b` (bests merged per exercise), `s` (latest settings per exercise), `d` (phone|tablet), built by `hoExtrasFor`. Old apps ignore them. `hoCheckExtras` drops anything unknown or of the wrong type (the runs still import).
- Client: `hoMergeBests` (higher is better, own other values stay), then one `confirmDialog` per exercise „Mit den Einstellungen deines Trainers weitertrainieren?“ (`hoAskSettings`); size only with the same device kind, otherwise a note. Applied = `fwmc-trainer-settings-v1` + `.trainer-set-note` on the ready screen. FAQ „Was bekomme ich von meinem Trainer?“. Test: `tests/trainer_uebernahme_0910_test.py`. Schulte joins `HO_BEST_KEYS`/`HO_SETTINGS` when it is merged.

### Paket 09.10. nachmittags (Fabian's answers)
- **Verschickt** (`HO_SENT_KEY` = `fwmc-trainer-sent-v1`, 21 days by `sent`): "Fertig" after a QR copies the sent runs there (`hoMarkSent`) before `hoDeleteEverywhere` removes them as before (own runs still leave Verlauf/Fortschritt). Gespeicherte Trainings lists them last with a green "verschickt" tag and the send time; chip "Verschickt"; they can be ticked and shown as QR again (`hoEntriesFor` reads the archive); deleting removes the copy.
- **Ausgeblendete zeigen**: `#handoverHiddenBtn` in Gespeicherte Trainings (only with hidden own runs of the last 14 days, filter Alle/Eigene) toggles `hoShowHidden`; such rows get a dashed "ausgeblendet" tag and can be sent.
- **Kürzel pro Kunden-Training**: `#clientTagSheet` right after "Mit Kunde" starts (`hoAskTag`, max 4 chars, no spaces), stored in the session (`tag`) and on each client run; shown in the tags ("Kunde · MK", "früher · MK", "verschickt · MK"). Never in the QR payload. Automated browsers only with `fwmc-test-clienttag`.
- **QR sub field**: payload position 11 = `freeId` or `neuroEx` (≤ 60, `[\w.:-]`); the import sets it back, so a plan entry `free:<id>` / `neuro:<ex>` is ticked on the client's phone (see docs/notes/04).
Test: `tests/paket_0910_nachmittag_test.py`.
