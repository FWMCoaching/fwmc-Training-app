# QR-Übergabe (Idee 69, 2026-10-08)

Fabian approved variant A (time range + checkboxes) plus "Kunden-Training
starten". Design draft: the five steps below. A client trains on the
trainer's phone; the trainer hands the runs over with a QR code, the
client's app takes them into its own history. **No server is involved.**

## Trainer side
- Fortschritt (`#progressScreen`) now also has the usual "Gesamter
  Trainingsverlauf" section (prefix `progress` in `HISTORY_PREFIXES`) and
  below it the group `#handoverGroup` "Training beim Trainer":
  "An Kunden übergeben" (`#handoverOpenBtn`), "Kunden-Training starten"
  (`#clientRunStartBtn`), "Übergabe-Code einfügen" (`#handoverPasteOpenBtn`).
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
`hoLoadQrLib()` only on the QR screen; precached in sw.js (CACHE v8).
**Artifact publish must include `qrcode.js` in `files`.**

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

## iPhone: Safari vs. home-screen app
A link from the iPhone camera opens in Safari, whose storage is separate
from the home-screen app. In iOS Safari outside standalone (`isIOS &&
!standalone`; tests: `fwmc-test-ios-browser`) the sheet explains this and
offers "Code kopieren" (copies `1.1.code.<data>`, clipboard API with
execCommand fallback) next to "Hier in Safari übernehmen". In the
home-screen app: Fortschritt › "Übergabe-Code einfügen" (`#handoverPasteSheet`)
runs the same import (whitespace in the pasted text is ignored; a whole
`…#import=…` URL works too).

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
`pip install opencv-python-headless`); wrap audit area "fortschritt".

Open / for Fabian to check on his iPhone: camera scan of a dense code
(150 entries = several codes), Safari tab per scan collecting parts,
"Code kopieren" → paste in the home-screen app, the strip under the notch.
