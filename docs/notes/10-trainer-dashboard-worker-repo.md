# Trainer-Dashboard (formerly Coach-Dashboard) & Worker-Repo (2026-09-28)

Client's ask: a way to programme Trainings-Codes and see which client
(Kürzel only) got which code and when, without needing me in the loop every
time, plus concerns that (a) code creation so far only ever happened "mit
mir zusammen, testweise" with no tool of its own, (b) no repo existed for
whatever serves the codes, and (c) a client-history log should live
somewhere more professional than just one browser's localStorage.

Investigated via the Cloudflare MCP connector (this session has read/D1
access to the client's Cloudflare account) and found the actual live setup
the app's `CODE_API` (`app.js`, `lookupProgram()`) has been calling all
along: a Worker named `online-training` (serves
`online-training.fwmc.workers.dev`, exactly the URL baked into `app.js`)
backed by a D1 database `fwmc-training-codes` with one table, `programs`
(`code`, `active`, `config` JSON, `created_at`, `updated_at`). It already
held the three real codes in production use (`dig01`, `dig02`, `xppbsp-1`)
- these were inserted by hand via direct D1 queries in earlier sessions,
confirming there was genuinely no write endpoint and no repo, exactly as
the client suspected. The `config` JSON shape already matches the app's own
local `PROGRAMS`/bundle format (a `blocks` array of
`{exercise,palette,duration,stimulusS,intervalMin,intervalMax,sequence}`,
or `{type:"bundle",programs:[...]}` for a programme overview) - no new
schema was invented, the dashboard just authors the same shape by hand.

Built, in `worker/` (the Worker's source now lives in this repo -
`worker/README.md` has full first-time-deploy steps) and `dashboard.html`
(a new, separate static page, not part of `build.sh`'s pipeline):

- **`worker/src/index.js`**: keeps the existing public `GET /program`
  lookup unchanged (still no auth - the client app itself calls it), and
  adds an admin API gated by `Authorization: Bearer <ADMIN_TOKEN>` (a
  secret set once via `wrangler secret put ADMIN_TOKEN`, never committed):
  `GET/POST /admin/programs` (list all codes incl. full config, or upsert
  one), `GET/POST /admin/client-history` (list, optionally filtered by
  `?client=`, or log a new `{clientCode, programCode, note}` entry).
- **New D1 table `client_history`** (`id`, `client_code`, `program_code`,
  `note`, `created_at`), added directly to the *same* production database
  the app already depends on - this is the "somewhere more professional"
  the client asked for: shared and device-independent, not
  localStorage-only (that already exists separately as the *client-side*
  Trainings-Code-Verlauf in Master-Einstellungen, which is a different,
  intentionally-local thing: what codes *this browser* has opened, not
  what the coach assigned to which Kürzel).
- **`dashboard.html`**: a small standalone page (dark theme, no build step,
  deliberately not wired into `build.sh`/`index.html` - it's a separate
  coach-only tool, not part of the client-facing app). Gate screen asks for
  the admin token once (stored in this browser's localStorage only,
  exactly like every other preference in the app); once past it: a
  Kunden-Verlauf panel (Kürzel + Code + optional Notiz → logs to
  `client_history`, with a filter-by-Kürzel table beneath) and a
  Trainings-Codes panel (table of existing codes with an active/inactive
  toggle, click a row to load its config into an editable JSON textarea,
  paste/edit and save to create or update a code). Deliberately a JSON
  textarea rather than a full visual block-builder for v1 - the config
  shape is exactly what `dig01`/`dig02`/`xppbsp-1` already use, so copying
  and adapting one is realistic, and a guided form can follow later once
  this baseline is confirmed useful. Tested end-to-end against a fully
  mocked Worker API (Playwright route interception standing in for the
  live endpoints, since deploying the new Worker code needs a step outside
  this session - see below) - auth gate, wrong-token rejection, listing,
  logging, filtering, edit-existing-code, toggle active/inactive,
  create-new-code, invalid-JSON handling, logout, and reload-with-
  stored-token all verified.

**Live since 2026-09-28**: this session's own Cloudflare access (via MCP)
can read Workers and read/write D1 directly, but cannot deploy Worker
*code* - there's no deploy tool exposed here. The client added a
`CLOUDFLARE_API_TOKEN` to a separate Claude Code session's environment
secrets (walked through interactively, iPad → Cloudflare dashboard for the
token itself, then the environment's own settings; had to switch that
environment's network access from "Vertraut" to "Voll" since `wrangler`
needs `api.cloudflare.com`, blocked in this repo's own environment's
network policy is a separate, unrelated setting) - that session ran
`wrangler deploy` and `wrangler secret put ADMIN_TOKEN`, then live-verified
all three routes (public lookup still works, admin without token 401s,
admin with token returns real data) before reporting the `ADMIN_TOKEN`
value back. Its one incidental commit (ignoring `worker/.wrangler/`'s local
cache) landed on a side branch, fast-forwarded into `main` from here.
`dashboard.html` needs no deploy step of its own - it's served by GitHub
Pages like the rest of the repo, just not linked from the client-facing
app's own navigation. The client still needs to enter the `ADMIN_TOKEN`
once into `dashboard.html`'s gate screen (treated like a password - it
grants full read/write on every training code and the client-history log).

**Baukasten (visual block-builder, added 2026-09-28)**: the client tried
the dashboard live, found the JSON textarea confusing ("wo kann ich denn
da jetzt die Übungen zusammenklicken?") and asked for a real click-together
UI. Added as a `dashboard.html`-only feature (no Worker/API changes needed
- it just constructs the same JSON the API already accepted):
- Two tabs, `#tabBuilderBtn`/`#tabJsonBtn`, toggled by `switchTab()`.
  Switching FROM json TO builder re-parses whatever's in the JSON textarea
  first (`configToBuilder(JSON.parse(...))`, silently keeping prior builder
  state on invalid JSON) so manual JSON edits aren't lost if the coach
  flips tabs; switching the other way serializes the current builder state
  into the textarea - either tab can be the one that's actually saved.
- Deliberately covers only the 8 canvas-timed exercise types dig01/dig02/
  xppbsp-1's blocks already use (`EXERCISE_CATALOG`: vt-color, vrw-original,
  4-straight, 4-diag, 8-solo, 8-vrw, stroop-classic, stroop-bg) - all share
  the exact same block shape. Colour choice uses `colors: [...]` (a
  multi-select of the app's own 7-colour `COLOR_BY_KEY` library, min 2 -
  `blockColors()`'s "free selection" path in app.js) rather than the
  legacy 3-letter `palette` codes (`"ORL"` etc.) - functionally identical,
  far more legible for a coach than memorising palette codes.
- `configToBuilder(config)` decides per-edit whether the builder can
  represent a code's saved config: only a plain `blocks` array (no
  `type:"bundle"`) whose every `exercise` id is in `EXERCISE_CATALOG`
  "fits". A code that doesn't (a bundle like `xppbsp-1`, or any future
  exercise type outside the 8) disables the Baukasten tab and shows
  `#builderFallbackHint` explaining why, falling back to the JSON tab -
  note this hint element lives as a sibling of both tab panels, NOT inside
  `#builderView`, specifically because `switchTab` hides that whole
  container when the JSON tab is active and the hint needs to stay visible
  exactly then; got this wrong once (nested inside `#builderView`, so the
  explanation was invisible right when it mattered) and caught it via the
  Playwright mock test before it shipped.
- A block's `palette`-only legacy shape (no `colors` array, e.g. editing
  `dig01` itself) falls back to a sensible default 3-colour set on load -
  close to but not byte-identical to the exact ORL hex shades, acceptable
  since editing and re-saving in the builder naturally normalises it to the
  `colors` shape going forward.
- "Neuer Code" button (`resetBuilder()`) clears the whole form for a fresh
  code, since there was previously no explicit way to back out of editing
  an existing one.
- Tested against a mocked Worker API: adding/reordering/removing blocks,
  the colour-count floor, tab round-tripping (builder → JSON → builder
  preserves state), saving posts the right `config` shape, editing a
  simple existing code populates the builder, editing a bundle correctly
  falls back to JSON-only with the hint visible, "Neuer Code" resets
  everything.
- **Other areas in the Baukasten (2026-10-02, Fabian "E. Ja")**: a
  "Bereich" row (Visual Training / Movement / Cardio / Workout) switches
  the builder. Movement writes a `movement-plan` (movements ≥2, bpm,
  durationMin, preview 1-4, mirror, showLabel), Cardio a `cardio-plan`
  (activities with minutes, label, optional interval), Workout a
  `workout-plan` of `reps`/`tabata` blocks. `configToBuilder` opens those
  types in the builder; circuit/strength/range blocks, bundles and Kombi
  stay JSON-only (fallback hint). The dashboard keeps its own copies of
  MOVEMENTS/CARDIO_ACTIVITIES/WORKOUT_EXERCISES - **add a new catalog entry
  there too** (and in the "Alle Übungen im Überblick" list). Test:
  `tests/dashboard_builder_test.py` (mocked Worker; the saved configs are
  fed to the real app to prove they open).
- **Eigenes Training (2026-10-05, Trainer-Vorlagen per Code)**: 5th
  "Bereich" button "Eigenes Training" (`#freeBuilder`): "+ Training
  hinzufügen", per training Art (Abhaken / Mit Zeit / Checkliste), Titel,
  Notiz, Dauer 1-60 Min. (Mit Zeit) or points with text + seconds 0-600
  (Checkliste, "+ Punkt", ✕), ↑/↓/✕ per training. Writes `{type:
  "free-template", name, description, trainings:[…]}` (save checks: at
  least one training, every training a title, a checklist at least one
  point). `configToBuilder` opens such codes in the builder. The kind row is
  now `auto-fit` (2-3 per row on a phone). The Worker stores configs
  generically (only code/active/config, dates and seats are read), so this
  type needed **no Worker change and no deploy**. App side: notes/25.
  Test: `tests/trainer_template_1005_test.py` (+ the kind count in
  `tests/dashboard_builder_test.py`).
- **Not built**: multi-program bundles (`xppbsp-1`'s shape) in the
  builder - still JSON-only; the other 4 `EXERCISES` types (`cross-modal`,
  `cone-tap`, `cone-compass`, `periph-flash`) aren't offered in the picker,
  since their config shape isn't confirmed to match the simple block form
  used here; drag-and-drop reordering (up/down buttons only).

**Trainingsplanung im Dashboard (2026-10-07, konzept-trainingsplanung kp17-kp22)**:
two new panels `#planPanel` (Trainingsplanung) and `#yearPanel`
(Jahresübersicht) above Kunden-Verlauf, a pill nav `.dash-nav`, and one
extra `<script>` block at the end of dashboard.html (an IIFE using the
first script's `api`, `token`, `programsCache`, `switchTab`,
`randomCodeSuffix`). Decided after the concept: no phase types, no
Entlastungswoche, nothing changes training by itself; a Wettkampf only shows
"Empfehlung: in der Woche davor etwas leichter, mit dem Kunden abstimmen.";
phases can be "aus der Wertung" (`noScore`).
- **Bausätze (kp17)**: kinds `kombi` ({items:[{area,what,minutes}], asOne,
  code}), `week` ({days[7]}), `phase` ({name, weeks, days, alt?}); each with
  tags (Einsteiger, Fortgeschritten, Sportler, Führungskraft, Regeneration,
  Wettkampf), note "Wofür, für wen", `version` (+1 per edit) and `used`
  (+1 per placement). Starts empty (no invented plans). Filter by kind and
  tags (AND). "Als Bausatz speichern" on a phase, a week, and via ⋯ on a day
  (Kombi-Paket). A Kombi-Paket goes in as one `area:"combo"` entry (optional
  Kombi-Programm code, minutes = sum) or one entry per exercise.
- **Plan-Baukasten (kp18)**: Bausätze left, plan right (from 1200 px; a phone
  stacks Bausätze, plan, preview). HTML5 drag & drop (phase anywhere on the
  plan = appended, week onto a week row = replaced, Kombi onto a day) or
  "Einsetzen" + tap on the highlighted target (touch). Entry sheet (Bereich,
  Übung = the app's `what` values `ex:`/`nat:`, Minuten 5-240, Uhrzeit,
  Code, Sondertraining), day menu ⋯ (kopieren / einfügen = replaces the day /
  leeren / als Kombi-Paket), Rückgängig + Ctrl/Cmd+Z (50 steps, in memory),
  Wochen im Wechsel A-D (new week = copy of A), Wettkämpfe per client.
  The dashboard keeps its own copy of `PLAN_AREAS`, the visual exercise ids
  and `NAT_SUBS` (`AREAS`, `VISUAL_EX`, `NAT_SUBS` in the planning script):
  **add a new area/exercise there too**.
- **Nacht 2 (2026-10-07)**: a Kombi-Paket placed "als ein Eintrag" gets
  `entry.title` = the Bausatz name (dashboard `cleanEntry` keeps `title`,
  max 60); the client's Wettkämpfe (`p.comps`) go out as
  `plan.events: [{date, title, kind:"wettkampf"}]` (app side: notes/27).
- **Ausgabe (kp13/kp21)**: "Als Plan-Code ausgeben" builds
  `{type:"training-plan", name, version, plan:{startDate, phases:[{id, name,
  weeks, days, alt?, noScore?}], events?}}` and saves it with the existing
  `POST /admin/program` (active) plus a `client-history` line (Kürzel,
  "Trainingsplan Version n"). Same code again = `version` = max(local
  issued, server config.version) + 1; entry ids stay stable so the client's
  own times survive (`applyTrainerPlan`). A code already used for another
  type is refused. Without a token ("Ohne Token: nur Trainingsplanung
  (lokal)" on the gate, `body.local-only` hides the server panels) the def is
  shown as JSON to copy; the old JSON tab stays the emergency exit ("Im
  JSON-Feld der Trainings-Codes öffnen"). Only the last phase may have
  `weeks: 0` (open end).
- **Jahresübersicht (kp19)**: 12 months (‹ › shift 3 months), one row per
  Kürzel/Gruppe, phase bars in two neutral brand tones (open end fades,
  noScore hatched), ◆ Wettkampf, red today line, "Plan endet in n Wochen"
  (≤ 3 weeks) / "Plan ist beendet"; tapping a bar opens that plan. Grid
  scrolls inside `.table-scroll` on a phone.
- **So sieht es dein Kunde (kp22)**: `.pv-phone` 390x700 mock with the app's
  tokens (light/dark): Heute date, week strip with rings, "Geplant für
  heute", "Mein Plan" (phase, Woche n von m, A-D), source line; switch
  Diese Woche / In 3 Wochen / Wettkampf. Simplified, not the real app.
- **Speichern (kp20)**: local keys `fwmc-dash-bausaetze-v1`,
  `fwmc-dash-plans-v1` (by Kürzel; no names or health data, the UI says so),
  `fwmc-dash-plan-versions-v1` (Stände: per "Stand speichern" and per Ausgabe,
  last 30, "Stand TT.MM., HH:MM", Zurückholen keeps the issue history),
  `fwmc-dash-current-v1`. "Alles als Datei sichern" (JSON,
  `app:"fwmc-trainer-dashboard"`) / "Aus Datei laden" (merge, asks before
  replacing) stay. **Server-backed since 2026-10-08** (next section).
Test: `tests/dashboard_planung_1007_test.py` (mocked Worker; the issued def
is entered in the real app and shows "Plan von deinem Trainer übernehmen?").

**Dashboard auf dem Server (kp20, 2026-10-08, Fabian approved)**: with an
admin token the planning data is the same on every device.
- **Worker**: table `trainer_items(kind, id, data JSON, updated_at INTEGER ms,
  PRIMARY KEY(kind,id))` (`worker/migrations/0002_trainer_items.sql`; the
  Worker also creates it on first use). Routes in `worker/src/items.js`,
  behind the same `withAuth` (Bearer `ADMIN_TOKEN`, constant-time) and admin
  CORS (`ADMIN_ORIGINS`, methods now incl. PUT/DELETE) as every admin route:
  `GET /admin/items?kind=` (list; without kind = all), `PUT
  /admin/items/<kind>/<id>` body `{data, updatedAt?}` (upsert; kind whitelist
  `bausaetze|plans|plan-versions|current`, id `[letters digits . _ -]{1,80}`,
  `current` only as id `current`, data must be object/array, 256 KB per item
  → 413, 2000 items per kind → 409; `updatedAt` = the dashboard's clock,
  absurd values become server time), `DELETE /admin/items/<kind>/<id>`.
  Kürzel only, never names (as before). Tests: `worker/test/items.mjs` (real
  SQLite via `node:sqlite`, Node ≥ 22.5), part of `npm test`.
- **Dashboard** (sync block in the planning IIFE, "Server-Speicher (kp20)"):
  one server item per Bausatz (`bausaetze/<id>`), per client plan and per
  client's Stände (`plans/<Kürzel>`, `plan-versions/<Kürzel>`) and the
  selected client (`current/current`). `fwmc-dash-sync-v1` keeps per item a
  hash of the synced state, its time, "was on the server" and "still has to
  go up", plus pending deletes. On open (token, not local-only): load all 4
  kinds, newer `updated_at` wins, local-only items go up unless they were on
  the server before (then they were deleted on another device and go here
  too); items first seen locally get their own time (plan `updatedAt`,
  Bausatz `updatedAt`, last Stand), never "now", so old local data never
  beats newer server data. Every `wj()` of the four keys schedules a
  write-through (0.8 s debounce; pagehide/hidden sends at once). Offline or
  5xx: everything stays local, status line `#plSyncLine` "Nur auf diesem
  Gerät gespeichert – wird übertragen, sobald der Server erreichbar ist",
  retry every 30 s and on `online`; reopening after > 2 min hidden re-loads.
  First run (server empty, local data, never synced): `confirmSheet`
  "Deine Dashboard-Daten auf den Server übernehmen?" Ja / Später (Später or
  closing = nothing goes up this session, line + "Jetzt auf den Server
  übernehmen"; asked again next open). A Stände item over 250 KB drops its
  oldest Stände on the server copy only. 401 = back to the gate. Local-only
  mode (no token) never calls the server and hides the line.
  `confirmSheet(title, text, yes, onYes, {no, onNo, safe})` gained the
  optional second label / non-red Ja.
- **Open for Fabian**: the app's Datenschutz sheet should get one sentence
  that the trainer keeps plans under a Kürzel on his own server (concept
  kp20: "Datenschutztext vorher kurz ergänzen") - not changed here.
Test: `tests/dashboard_server_1008_test.py` (mocked `/admin/items`: first-run
question Ja/Später, write-through + debounce, second device in a fresh
context, newer wins, delete across devices, offline line + upload when back,
390 px light/dark, local-only, wrong token). `tests/dashboard_planung_1007_test.py`
and `tests/dashboard_builder_test.py` mock `/admin/items` too.

**Deploy kp20 (not done yet - tonight, after the full suite)**. From a session
with `CLOUDFLARE_API_TOKEN` and network "Voll" (see above):
```sh
cd worker
npm install
npm test                                   # every line True
npx wrangler deploy --dry-run              # bundles, lists DB + limiters + vars
# 1. table (0001 was once applied by hand with d1 execute; migrations apply
#    runs it again - harmless, IF NOT EXISTS - and records both)
npx wrangler d1 migrations apply fwmc-training-codes --remote
npx wrangler d1 execute fwmc-training-codes --remote --command "SELECT name FROM sqlite_master WHERE name='trainer_items'"
# 2. Worker
npx wrangler deploy
```
Smoke checks (`T` = the ADMIN_TOKEN, `O="Origin: https://fwmcoaching.github.io"`,
`B=https://online-training.fwmc.workers.dev`):
```sh
curl -s -o /dev/null -w "%{http_code}\n" "$B/program?code=dig01"                  # 200 (public lookup unchanged)
curl -s -o /dev/null -w "%{http_code}\n" -X OPTIONS "$B/reminders"                 # 204
curl -s -o /dev/null -w "%{http_code}\n" -H "$O" "$B/admin/items?kind=plans"       # 401 without token
curl -s -o /dev/null -w "%{http_code}\n" -H "$O" -H "Authorization: Bearer wrong" "$B/admin/items?kind=plans"  # 401
curl -s -H "$O" -H "Authorization: Bearer $T" "$B/admin/items?kind=plans"          # 200 {"items":[...]}
curl -s -H "$O" -H "Authorization: Bearer $T" -H "Content-Type: application/json" -X PUT \
  --data '{"data":{"smoke":1}}' "$B/admin/items/bausaetze/smoke-test"              # 200 {"ok":true,...}
curl -s -H "$O" -H "Authorization: Bearer $T" -X DELETE "$B/admin/items/bausaetze/smoke-test"  # {"ok":true,"deleted":true}
curl -s -D - -o /dev/null -X OPTIONS -H "$O" "$B/admin/items/plans/x" | grep -i allow-methods  # ... PUT, DELETE ...
curl -s -o /dev/null -w "%{http_code}\n" -H "$O" -H "Authorization: Bearer $T" "$B/admin/programs"  # 200 (old admin route)
```
Then open the live dashboard with the token: on the device that has the
data, the question appears once - Fabian answers "Ja"; on a second device
the plans show up. Verified before commit (2026-10-08): `npm test`, `wrangler
deploy --dry-run` (wrangler 4.148), `d1 migrations apply --local` and the
smoke checks above against `wrangler dev --local` (all as expected).

**Bausteine-Bibliothek + "Alle Übungen im Überblick" (added 2026-09-28)**:
client tried the dashboard live and pushed back hard on my first
"reuse-the-app-itself" architecture idea for keeping the dashboard
auto-synced with new exercises - not because it was wrong, but because
the dashboard needs things the app itself has no concept of at all
(named reusable cross-client building blocks, video links, an
at-a-glance overview) - so a live-auto-synced-with-the-app approach
wasn't actually the right fit regardless of the sync question. Agreed
instead: separate dashboard stays, sync happens in periodic (roughly
weekly) manual reviews, not automatically - a real, deliberate scope
narrowing from what "Not yet built" implied before, not a stopgap.
- **"Alle Übungen im Überblick"**: a collapsed-by-default `<details>`
  panel, `OVERVIEW` - a hand-maintained array grouped by domain (Visual
  Training, NAT, Atemtraining, Movement, Workout, Test-Bereich), each
  exercise tagged `full` (Baukasten-fähig) / `json` (JSON-Tab only) /
  `none` (only in the app, not in the dashboard at all yet) rendered as
  coloured pills. Carries an explicit "Stand: <date>" note - this is
  the load-bearing part, not decoration, since the whole point is that
  it's a manual snapshot, never claiming to be live. Update the date and
  the list itself at each periodic review; don't let it go stale silently.
- **Bausteine-Bibliothek**: the client's own insight (unprompted) was
  that "a library of reusable templates" and "copy from an existing
  client's code" are the same feature - a `<details>` inside the
  Baukasten tab lets the coach pick ANY existing code from a dropdown
  (`renderLibSourceSelect()`, repopulated whenever `loadPrograms()`
  runs) and see its blocks (`renderLibBlockList()`); each block with a
  known `exercise` id gets an "Übernehmen" button. No separate "is this a
  template" flag exists or is needed - a code the coach deliberately
  keeps around under a clear name (e.g. `vorlage-warmup`) just IS a
  reusable template by virtue of being a normal code someone can browse
  and copy from; a real client's code works exactly the same way.
  **Deep-copy correctness was an explicit client requirement** ("ohne
  dass es im alten Code... automatisch gespeichert wird") - the copy
  button does `JSON.parse(JSON.stringify(block))` before pushing into
  `builderBlocks`, never pushes the source object by reference, so
  editing the copy in the new draft can never mutate `programsCache`'s
  copy of the source code (verified in the Playwright test: copy a
  block, edit its duration in the new draft, re-open the source in the
  library and confirm its own duration is unchanged). A source whose
  config isn't a plain `blocks` array (a bundle, or anything the
  builder doesn't understand) shows a `.lib-unavailable` message instead
  of a block list, same "don't guess, say what's missing" pattern as the
  Baukasten-vs-JSON fallback.

**Not built, explicitly out of scope for this pass**: client history
beyond Kürzel/code/note/date (e.g. richer client records - the client only
asked for "welches Kürzel hat was bekommen", not names or other PII, and
D1 access is already client-only via the admin token, but nothing here
does more than that minimum); any auth beyond a single shared bearer token
(fine for a single coach, would need real per-user auth if ever shared
with others).

**Home-screen icon + colour refresh (2026-09-28)**: the client uses
`dashboard.html` "add to home screen" style, and its icon fell back to
an auto-generated letter (`dashboard.html` had no `apple-touch-icon` at
all) - hard to tell apart from the trainings-app's own icon in a
folder. Fixed by giving the dashboard its own icon pair
(`dashboard-icon-192.png`/`dashboard-icon-512.png`, plain full-bleed
squares - iOS applies its own rounding, don't pre-round the corners,
same convention as the main app's `icon-192.png`/`icon-512.png`) plus a
small `dashboard-manifest.json` and the matching `<head>` tags
(`apple-touch-icon`, `manifest`, `theme-color`), mirroring exactly what
`build.sh`'s template already does for `index.html`. Four icon concepts
and three colour-scheme options were mocked up first as a throwaway
Artifact (icons rendered as real PNGs via a tiny Playwright-rendered
HTML page, not hand-drawn) so the client could pick without guessing -
client picked icon "A" (solid brand teal `#007094`, three white
rounded bars - a deliberately different glyph from the trainings-app's
signature-scribble icon, same colour family so the two read as related
apps) and colour option "1" (flat brand teal, no gradient).
That same colour choice also replaced the dashboard's top-bar/button
accent, which had been an invented teal→green gradient with no real
tie to the brand. `--accent2` is gone; `--accent` is now the true brand
teal (`#007094`, the same value as the main app's `theme-color` and
icon background - no longer the lighter `#39a7cc`). The old
`--accent2` uses were genuinely semantic (the "aktiv" pill, success
messages, "kopiert" button feedback, the Overview's "full support"
dot) rather than brand colour, so they moved to a new `--good` token
(`#3cc27a`, same value as before) instead of just being deleted -
keeping semantic status colour separate from the brand accent, so a
future brand-colour change doesn't have to relitigate what counts as
"success green".

**iOS dark/tinted home-screen icon quirk (found while testing the
above)**: on-device, the new teal icon showed up solid black instead
of teal once added to the home screen. Ruled out a file bug first (the
PNG is opaque RGB, confirmed teal at every pixel checked). Root cause,
confirmed by the client A/B-testing both icons live against the
Darstellung (Hell/Dunkel/Getönt/Automatisch) toggle: iOS recolours a
web-clip icon that reads as a simple two-tone "template" (flat solid
background + a few solid geometric shapes - exactly what icon "A"'s
three bars are) when the device's icon appearance is Dunkel/Getönt,
but leaves an icon with organic, hand-drawn linework (the trainings-
app's signature scribble) untouched in every mode. This is Apple's
call, not something a `<meta>` tag can opt out of. **Client's decision:
leave icon "A" as-is** - do not silently swap it to the signature-style
"C" variant that was offered as the fix (organic linework instead of
solid bars, matching what proved immune) unless asked again.

**Roadmap: video support**
- Step 2 (done): simple video-link URL fields in the dashboard
  Baukasten (no upload) - `introVideo`/`endVideo` at the programme
  level and `videoAfter` per block, all plain URL strings. See the
  Baukasten section above.
- Step 3 (done): app-side (app.js) rendering of those videos during a
  coach-authored programme run. A programme's runtime steps are no
  longer just `def.blocks` - `buildProgramSteps(def)` interleaves an
  `{type:"exercise"}` step per block with an `{type:"video"}` step
  wherever `videoAfter`/`endVideo` is set, and `program.chapterIndex`
  now indexes this `program.steps` array instead of `def.blocks`
  directly (every call site - `tick()`, `playChapter()`, `startPause()`,
  the pause-screen buttons, `finishSession()` - was updated together;
  search "program.chapterIndex indexes program.steps" if touching any
  of them again). `introVideo` itself was untouched - it still shows on
  the pre-start intro screen with native controls, was never part of
  this ask, and needs no chapter-nav treatment since nothing gates
  moving past it.
  Video steps play in a new `#programVideoPlayer` screen
  (`playProgramVideo()`), a real `<video controls>` (native seek both
  directions, no custom scrubber needed) with its own small nav ("«"
  restart/prev, "Weiter »", a skip checkbox) - **not** the existing
  `videoModal`/`openVideoModal()`, which is the older, separate
  "explainer video" feature (an on-demand how-to clip opened from the
  intro screen's chapter list, dismiss-and-return, no programme-flow
  role at all - the two must stay distinct).
  One structural trap worth remembering if another screen ever nests
  inside `#player` the way `#pauseScreen` already did: `#player` closes
  its own `<div>` *after* `#pauseScreen` and `#programVideoPlayer` in
  `_body.html`, so both are DOM children of `#player`, not siblings of
  it. `playProgramVideo()` first called the generic `hideAllPlayers()`
  (which sets `#player.hidden = true`) and the video silently rendered
  at 0x0 - `hidden` was correctly `false` on the video panel itself,
  but its own now-hidden ancestor collapsed it. Fixed by following
  `startPause()`'s existing pattern instead: hide `#player`'s *sibling
  panels* (stageWrap/progressTrack/playerBar/liveNav), never `#player`
  itself, while a step nested inside it is showing.
  Client requirements, all covered: end early (the "Weiter" button/the
  video's own `ended` event calls `advanceProgramStep()`); seek both
  directions (native `<video controls>`); return to a watched/skipped
  video via the same chapter navigation used for exercises (any direct
  `playChapter(idx)` call - chapter list, prev/next, restart - always
  lands exactly on the requested step, video or not, regardless of its
  skip flag; only the *automatic* forward path, `advanceProgramStep()`,
  auto-skips a flagged video); persistent-but-reversible per-video skip
  flag (`fwmc-program-video-skip-v1` in localStorage, keyed by program
  code + a stable `videoId` like `after-2`/`end` - ticking/unticking
  the checkbox on the video's own screen sets/clears it immediately).
  One semantic decision worth remembering: on the pause screen between
  exercises, "previous"/"restart" always act on the exercise that
  actually just ran, **never** on a video that got silently auto-skipped
  right before it - otherwise "restart" would force-replay a video the
  client deliberately chose to skip. A skipped video is still reachable
  once the *next* exercise is reached, through its own previous-chapter
  navigation (confirmed in `tests/program_video_steps_test.py`).
- Step 4 (later, explicitly separate, not started): video upload from a
  file/photo library AND in-browser camera recording (`getUserMedia`/
  `MediaRecorder`) directly from the dashboard, once R2 storage exists.
  Requires a new R2 bucket, a new Worker upload/serve endpoint, and
  another `wrangler deploy` cycle. Client confirmed reusing the same
  `CLOUDFLARE_API_TOKEN`/session setup is fine for this, no new token
  needed.


**Katalog-Stand 08.10.2026**: plan `AREAS` gained `activation` (Aktivierung,
`#3b4fa8`, what `act:optodrum` from `ACT_EX` = the app's
`ACTIVATION_EXERCISES`); "Alle Übungen im Überblick" (Stand 08.10.2026) lists
Hütchen · Farbe + Zahl and Farbfelder (JSON), Aktivierung · Optodrum and
Test-Bereich "Jedes Auge zählt (Farbbrille)" (not in the dashboard). The app's
privacy sheet says the trainer may keep the plan under a Kürzel on the FWMC
server (kp20). Test: `tests/hilfsmittel_texte_1008_test.py`.

**Freischaltung + QR-Code zeigen (08.10.2026, details docs/notes/36)**:
kind "Freischaltung" (`data-kind="unlock"`, `#unlockBuilder`) builds its
checkboxes from dashboard.html's `FEATURE_UNLOCKS` copy (label + hint; a
new feature = one entry there + one in app.js) plus "Sperr-Code" (`lock`);
saves `{"type":"feature-unlock","features":[…]}`, `configToBuilder`
recognises it, the codes table marks it "Freischaltung"/"Freischaltung
sperren". Every row of the codes table has "QR-Code zeigen" (`data-qr`,
does not open the editor), and after "Speichern" `#pQrBtn` appears:
`#codeQrSheet` shows a big QR (`qrcode.js` from the app folder, loaded in
`<head>`) for `<app url>#code=<CODE>`, the code as text and the hint for the
client. App URL = the dashboard's own folder on github.io /
fabian-westermann.de / localhost, else the Pages URL. Test:
`tests/pruefer_fixes_1008_test.py` (decodes the canvas with jsQR).
