# Startseite "Heute", Kalender, Wochenplan (2026-10-03)

Fabian picked these from the concept doc
(https://claude.ai/code/artifact/599024ac-0579-46e5-a8ea-3b8889c678e2).
The app now **always opens on `#todayHome`**. "Heute" is the first tab
(`data-section="today"`) in every section bar, and `#home` (Visual
Training) is no longer the default.
- **`?bereich=` start parameter** (`initStartScreen()`): accepted values
  are `visual|breath|movement|workout|cardio|nat|test|heute` (+ `atempause`, 2026-10-07). `test` works
  only when unlocked, otherwise it falls back to visual. An unknown value
  opens Heute. **Every test that expects to land on Visual Training loads
  `index.html?bereich=visual`.** All existing tests were switched over;
  new tests must do the same, or test Heute itself.
- **Heute content**:
  - greeting by time of day, then the date (no name);
  - the `#todayMain` card: the next open training of the day, or
    "Weitermachen" with the last history entry, plus Fabian's hint text
    pointing to "deinem Trainer" (wording stays neutral, never "Fabian");
  - progress line "x von y geplanten Einheiten";
  - week strip Mo–So with ‹ › navigation;
  - calendar switches Monat (+ "nächsten Monat dazu"), Quartal (a
    horizontal scroller of months -3..+12) and Jahr (12 mini months, with
    a hint to use an iPad/laptop). There is no 4-week limit;
  - the day panel, as a list with "x dazwischen" gaps of 15 min or more,
    or as an hour grid. Overlapping entries go side by side in columns,
    based on the drawn height (`BLOCK_PX`), so nothing overlaps;
  - plan button, code line (`TODAY_CODE_CTX`, errors stay on Heute; the
    code boxes in every area remain), 6 area tiles.
- **Plan model** (`fwmc-plan-v1`): `{startDate (a Monday), phases:[{id,
  name, weeks (0 = unbegrenzt), days[7][entries]}], extras:{date:[entries]},
  skips:{date:[ids]}, done:{date:[ids]}}`. An entry is `{id, area, what
  ("ex:<exerciseId>" | "nat:<sub>" | "free:<freeBlockId>" | ""), code, time, minutes}`
  (`free:` = one Freier Baustein, see docs/notes/25-freier-baustein.md). Phases
  follow each other. An unlimited phase that is not the last one gets a
  warning, because the phases after it would never start.
  `occurrencesOn(date)` computes a day: phase entries + extras − skips. An
  entry counts as done when it was ticked manually, or when the history
  holds a non-aborted run of the same area that day (`historyAreaOf`;
  exercise history entries now carry `exId`).
- **Starting an entry** (`startEntry`):
  - a code opens `openProgramIntro`;
  - a visual exercise clicks its `.excard`;
  - a NAT sub-tab clicks that sub-tab;
  - anything else opens the area's home.
  The day actions are Starten / Abhaken / Heute auslassen (plan entries)
  or Löschen (extras), plus "Nur an diesem Tag etwas eintragen".
- **Plan editor** `#planScreen` + `#planEntrySheet`: per phase a name,
  a duration (1–52 weeks or unbegrenzt), seven days of entries, ↑ / copy /
  delete. "Ganzen Plan löschen" goes through `confirmDialog`.
- **A new area or exercise** needs a `PLAN_AREAS` entry (or for NAT a
  `NAT_SUBS` entry) and a `historyAreaOf` mapping, so it can be planned
  and auto-ticked.
- Not built yet: Tagesform, pausing/inserting/recovery week, plan codes
  from the trainer, calendar export (.ics), trainer dashboard view.
Test: `tests/today_test.py`.

## Eigene Termine + Countdown (2026-10-05)
Fabian: Wettkampf, Spiel, Vereinstraining, Massage, Ruhetag sollen in den
Kalender, ein großes Ziel als Motivations-Countdown auf Heute.
- Storage `fwmc-events-v1`: `[{id, date, time, title, kind, goal}]`, kind
  one of `EVENT_KINDS` (wettkampf/training/erholung/sonstiges, fixed colours).
- Day panel: `#dayEvents` above the trainings (cards with "Bearbeiten"),
  `#dayEventAddBtn` opens `#eventSheet` (title, kind, date, time, goal
  toggle; delete via `confirmDialog`). Week strip and month cells get a
  diamond `.event-mark` (bigger for a goal) and "1 Termin" in the label.
- `#todayCountdown` (a `.today-main` card) shows the nearest goal from today
  on: "Noch n Tage" / "Morgen…" / "Heute ist es so weit"; past goals vanish.
- Events do NOT steer training yet (open question to Fabian, see
  /mnt/project-files/app/ideen-liste.md: .ics export/import, which events
  should affect Trainingssteuerung).
Test: `tests/events_countdown_1005_test.py`.

### Termine wiederholen (Serien, 2026-10-08)
- Termin sheet: "Wiederholen" `#eventRepeatRow` Nie / Jede Woche / Alle 2
  Wochen (default Nie); field `repeat: "weekly"|"biweekly"`, missing = once
  (old events). No end date (Fabian: unlimited + deleting). With a series the
  date label reads "Erster Termin" and `#eventRepeatHint` says it repeats
  without end / that editing changes all dates of the series.
- `eventOccursOn(e, date)`, `eventNextDate(e, from)`; `eventsOn()` returns one
  copy per day with `date` = that day (`seriesDate` = first date), so week
  strip, month/quarter/year cells and the day panel need nothing extra. Day
  rows carry `data-event-date` for the swipe actions.
- Delete (sheet "Termin löschen" or list swipe) of a series: `confirmDialog`
  with "Nur diesen Termin" (date into `skip[]`) / "Alle Termine dieser Serie" /
  "Abbrechen". New `confirmDialog` option `cancel`: shows `#confirmCancelBtn`
  and makes tapping beside the sheet / Escape cancel instead of running onNo.
- Trainer events (`fromTrainer`, def.plan.events) never repeat; their sheet
  hides `#eventRepeatGroup`. Editing keeps unknown fields (e.g. fromTrainer).
- `nextGoalEvent` counts a repeating goal down to its next date.
  Trainingsplanung (`focusWeekOf`, Mein Plan goals/markers, plan length,
  `goalOverrun`) uses `loadSingleEvents()` only, so a weekly game does not
  mark every week as Wettkampfwoche. Reminders only cover plan entries, events
  were never part of them.
Test: `tests/termin_serien_1008_test.py`.


## Weitermachen nach Unterbrechung (2026-10-06)

Fabian: "Weitermachen nach Unterbrechung mit rein." Multi-block runs write
`fwmc-resume-v1` = `{type, def, code, key, title, idx, pos, total, played, ts}`
whenever a block starts (`resumeNote`), types `combo` / `workout` / `breath` /
`program` (Trainer-Programm: `pos` counts exercises, `idx` is the chapter
step). Every finish… (natural end, skip past the end) calls `resumeClear()`;
"Beenden" mid-run leaves it. `resumeGet()` offers it only from block 2 on
(pos > 0, pos < total) and for 3 days. Heute: without an open planned
training the main card becomes "Weitermachen" (title, "Übung 2 von 3 ·
unterbrochen vor 10 Min.", Fortsetzen / Von vorne / Verwerfen with
confirmDialog); with one, a single "Unterbrochen: … Fortsetzen" line under
it. `resumeRun()` rebuilds the runner (origin bundles reset, return screen
Heute). Not covered: Cardio-Einheit (one timeline, no blocks) and single
exercises. Test: `tests/resume_install_1006_test.py`.


## Weitermachen für einzelne Übungen + Wochenabschluss (2026-10-06)

- Single runs (Atem, Reaktionstraining) write `fwmc-resume-single-v1`
  (`resumeSingleNote(kind)`) on pause, abort and when the app goes to the
  background; only runs of ≥ 180 s with ≥ 30 s played and ≥ 60 s left.
  Finishing clears it (`resumeSingleClear`). Continuing starts a run of the
  remaining time with the stored settings (client prefs restored right
  after start); `resumeSingleBase` keeps the original total so a second
  break records the right rest. `resumeGet()` returns the more recent of the
  program and single records; "Verwerfen" (`resumeDrop`) removes only that one.
- The resume card shows "Fortsetzen ist noch bis … möglich." (`resumeUntil`).
- Wochenabschluss: on Sundays `renderWeekReview()` lists the week's planned
  entries with check/circle, one sentence (`weekReviewSentence`) and an
  optional "Mein Vorsatz für nächste Woche" (120 chars) saved under next
  Monday's date in `fwmc-week-intent-v1` (entries older than 21 days are
  pruned). Mon-Sat the Vorsatz shows with "Ausblenden".


## Nichtraucher-Pause (2026-10-07)
Card `#todayBreak` between the main cards (install hint) and the week: a short
calm breathing pause (1/2/3 Min.) with an ⓘ sheet. `?bereich=atempause` opens
Heute scrolled to it (push "Zeit für eine Atempause"). Details: docs/notes/20
(Atemtraining) and 26 (reminder).

## Vorname in der Begrüßung (2026-10-08, Fabian approved)
- `.today-hello`: `renderHello()` (called by `renderToday()`) writes
  `greetingFor(hour)` and, with a name, ", " + `span.today-greeting-name`
  (textContent only, never innerHTML). Names over 12 chars get
  `.has-long-name` (24 px instead of 28 px).
- Storage: `fwmc-name-v1`, plain string, `cleanName()` = whitespace
  collapsed, trimmed, max 30 chars (`NAME_MAX`); empty = key removed. Only on
  the device; in backups through the fwmc- prefix (not in `BACKUP_EXCLUDE`).
  Never read by the reminder payload (`computeReminders`) or any Worker call.
- Without a name: `#helloNameBtn` "+ Wie dürfen wir dich nennen?" (text-link
  small, 44 px) opens `#helloNameForm` inline (`.plan-input`
  autocomplete=given-name + `.start-btn.secondary` "Speichern", Enter saves,
  "Abbrechen"/Escape closes). Empty/whitespace saves nothing. Once saved the
  button is gone; clearing the name in Grundeinstellungen brings it back.
- Grundeinstellungen "Dein Name": docs/notes/03. Privacy sheet: the first
  name is listed under "Was wird auf deinem Gerät gespeichert?".
Test: `tests/vorname_heute_1008_test.py`; the wrap audit covers the open form
and a 30-char name on Heute.

## Auswahl vs. heute, ungeplante Trainings (2026-10-09, Fabian)
- Ausgewählter Tag = gefüllt in `--brand` (Text `--on-brand-fill`, hell weiß / dunkel #0c1b20), heute = Rahmen + Zahl in Markenfarbe. Gilt für Wochenleiste und Monatskalender (iOS-Kalender-Logik).
- Punkte ohne Plan-Eintrag (`extraAreasOn`) erklären sich im Tagesfeld: `extraEntriesOn` + `extraDayHtml` listen sie unter „Zusätzlich trainiert (nicht geplant)“ mit Uhrzeit, Dauer, Bereich. Test `tests/kalender_auswahl_0910_test.py`.

## Heute Entwurf E (2026-10-09, Fabian „Okay, wir nehmen E“)
- No plan for today: `#todayMain.is-flat` is one row „Zuletzt · <Tag>“ + name + pill „Nochmal“ (`lastDayWord`). Planned training / Weitermachen / all done keep their big card; newcomers keep the starter ask.
- `#todayPair`: half tile `#todayBreak` („Nichtraucher-Pause“ in quotes, „Gönn dir einmal durchatmen.“, „N Min. starten →“; 1/2/3 Min. now in `#breakInfoSheet`) + `#todayNewTile` „Neu für dich · <Bereich>“ (`newTilePick`: never-done STARTER from the first three of the goal's order, by day) or, when all are tried, „Bestleistung“ (`bestTilePick`, Positionen merken/Blitz/Flash/MOT, „Heute die 8?“). Newcomers: tile hidden, pause full width (`.single`).
- `#todayAsk`: „Trainierst du mit einem Trainer?“ as one slim line until answered (only own mode, not for newcomers who get it in the main card).
- `hasTrainerCode()`: a code-history entry whose `type` (recorded by `recordCodeUsage` since 09.10.) is not `feature-unlock`/`neuro-unlock`, or a QR-imported run (`trainer: 1`). Old entries without type count. `starterStage` uses it.
- `#todayGoal` under the week: „Für dein Ziel: <Ziel> ›“ (tap = goal chips), swipe row without the tile's exercise, never-done first, rotating by day; compact with a trainer; hint „Für dein persönliches Training sprich mit deinem Trainer.“ / „Noch keinen Trainer?“ (`PLAN_REQUEST_URL`). `fwmc-start-v1` gains `goalAt`; after 42 days „Passt dein Ziel noch?“ (Ja renews the date). Mehr › „Dein Ziel“ (`openGoalPicker`). Nothing is written in Kunden-/Test-Modus (`starterSave`). FAQ „Woher kommen die Vorschläge auf Heute?“. Test: `tests/heute_e_0910_test.py`.
