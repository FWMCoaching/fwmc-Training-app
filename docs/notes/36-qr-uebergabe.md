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
