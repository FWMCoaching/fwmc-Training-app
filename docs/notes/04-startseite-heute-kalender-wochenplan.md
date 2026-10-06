# Startseite "Heute", Kalender, Wochenplan (2026-10-03)

Fabian picked these from the concept doc
(https://claude.ai/code/artifact/599024ac-0579-46e5-a8ea-3b8889c678e2).
The app now **always opens on `#todayHome`**. "Heute" is the first tab
(`data-section="today"`) in every section bar, and `#home` (Visual
Training) is no longer the default.
- **`?bereich=` start parameter** (`initStartScreen()`): accepted values
  are `visual|breath|movement|workout|cardio|nat|test|heute`. `test` works
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
