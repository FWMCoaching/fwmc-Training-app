# 27 Trainingsplanung (2026-10-07)

Konzept: /mnt/project-files/app/konzept-trainingsplanung.md (kp1-kp24). Diese
Notiz beschreibt, was gebaut wurde: App-Teil kp1-4, 6-8, 10, 11, 13, 15 und kp21
auf App-Seite. Test: `tests/trainingsplanung_1007_test.py`.

## Grundsatz (Fabian 07.10., abends)
Nichts verändert das Training automatisch. Es gibt keine Phasen-Arten (kp5
entfällt), keinen Entlastungs-Schalter und keinen Faktor. Wettkampf- und
Ziel-Termine (`goal || kind==="wettkampf"`) erzeugen nur einen Empfehlungstext
(`focusWeekOf`). Ein Trainer stimmt so etwas mit dem Kunden ab.

## Datenmodell (`fwmc-plan-v1`, `loadPlan`/`emptyPlan`)
- `phases[]`:
  - `{name, weeks, days[7][entries], alt?[weeks B-D], noScore?, locked?}`.
  - `alt` = "Wochen im Wechsel" (A = days, B-D = alt[i]). `noScore` = aus der Wertung nehmen (kp11).
- Einträge:
  - `{id, area, what, code, time, minutes, special?, locked?}`.
  - `area:"combo"` + `what:"combo:<savedId>"` startet ein gespeichertes Kombi-Programm.
- `pauses[]`:
  - `{id, from, to, reason (urlaub|krank|verletzt|sonstiges), shift}`.
  - `shift` schiebt den Plan nach hinten, sobald die Woche mindestens 4 Pausentage hat.
  - Das Häkchen ist bei mehr als 3 Tagen vorausgewählt, der Kunde kann es abwählen.
- `weekOps[]`: `{id, at:Montag, op: repeat|skip|shift}`. Gilt ab der Kalenderwoche `at`.
- `inserts[]`: Sonderwochen `{id, at, name, days, noScore}`.
- `dayOv{date: entries}`: Änderung nur an einem Tag (kp4).
- `source`:
  - `{code, version, at, baseTimes}` bei einem Plan vom Trainer.
  - `baseTimes` merkt die Uhrzeiten des Trainers, damit eine neue Version die eigenen Zeiten des Kunden behält (kp21).

## Rechenweg
- `planWeekMap(cw)` ordnet Kalenderwochen den Planwochen zu (Typen insert, pause, blank, plan). Das Ergebnis ist gecacht; `savePlan` setzt den Cache zurück.
- Ein repeat oder skip, der auf eine Pause oder eine Sonderwoche fällt, wird mitgenommen (`pending`).
- `phaseFor(date)` liefert `{phase, index, weekInPhase, variant, focus, week, pw}`.
- `occurrencesOn(date)` geht in dieser Reihenfolge vor:
  1. Pause → leer.
  2. Sonderwoche.
  3. `dayOv`.
  4. Phasen-Variante.
  5. skip/extra.
- Flags an den Einträgen: `override`, `insert`, `noScore`.
- `weekGoalInfo` (kp2):
  - Das Wochenziel zählt nur geplante Einträge, die in der Wertung sind.
  - Pausen- und noScore-Wochen unterbrechen die Serie nicht.
  - Zusätzliche Trainings werden getrennt gezeigt (geteilte Balken `.pw-extra`).

## Oberfläche
- **Plan-Editor `#planScreen`**:
  - Zeile „Jede Woche gleich / Wochen im Wechsel“ mit Reitern A-D.
  - Ablage `#planTray`: antippen und platzieren oder ziehen.
  - Tag kopieren und einfügen.
  - Rückgängig `#planUndoBtn` (20 Schritte, nur im Speicher).
  - „+ Sonderwoche“ und der Haken „Aus der Wertung nehmen“.
  - Im Eintragsfenster gibt es eine Mehrtagesauswahl und „Jeden Tag“.
- **Mein Plan `#myPlanScreen`** (aus Heute und aus dem Editor):
  - Wochenzeilen „Name · Woche n von m (A)“. Ein Tipp darauf öffnet `choiceSheet`: wiederholen, überspringen, verschieben, rückgängig.
  - Pausenliste und Empfehlungen zu Wettkämpfen.
- **Pausenfenster `#pauseSheet`**: Grund, von/bis, Verschieben-Haken, Warnung ab 8 Tagen, „Ich bin wieder fit“.
- **Umfang beim Ändern (kp4)**: `askScope` fragt „Nur an diesem Tag / Ab jetzt immer / In der ganzen Phase“.
- **Heute**:
  - Planzeile `#todayPlanLine` mit den Links Mein Plan / Pause.
  - ★ für Sonder-Trainings, Ringe für geplante Einträge, kleine Punkte für zusätzliche.
  - Karte `#todayPlanUpdate`, wenn der Trainer eine neue Version ausgegeben hat.
- **Allgemeine Helfer**: `choiceSheet(title, text, options)` und `showToast(text)`. Für neue Auswahl- oder Hinweisfälle diese wiederverwenden.

## Plan-Code vom Trainer (kp13/kp21)
- Codetyp `training-plan`: `{plan:{phases, inserts?, startDate?}, version}`.
- `codeDefProblem` prüft ihn. `openProgramIntro` → `offerTrainerPlan` fragt „Plan von deinem Trainer übernehmen?“.
- `applyTrainerPlan` sperrt die Phasen (`locked`) und behält die eigenen Uhrzeiten des Kunden.
- Optional `entry.title` (Nacht 2, 07.10.): `cleanEntry` behält ihn (String, max. 60),
  `entryTitle` zeigt ihn vor allem anderen (Kombi-Paket aus dem Dashboard heißt dann
  wie im Dashboard statt „Kombi-Programm“). Ändert der Kunde im Eintragsfenster
  Bereich/Übung/Code, fällt der Titel weg; nur Uhrzeit/Dauer ändern behält ihn.
- Optional `def.plan.events` (Nacht 2): `[{date, title, kind:"wettkampf"}]`.
  `addTrainerEvents` trägt sie beim Übernehmen in die eigenen Termine
  (`fwmc-events-v1`, gleicher Speicher wie der Heute-Kalender) ein, mit
  `fromTrainer: <code>`; gleiches Datum + Titel schon da = übersprungen (neue
  Version doppelt nichts). `focusWeekOf` nimmt sie dann für die Empfehlungen mit.
- `checkTrainerPlanUpdate`:
  - Läuft einmal am Tag (`fwmc-plan-check-v1`), 2,5 s nach dem Start.
  - Bei höherer Version erscheint die Karte auf Heute.
  - Tests löschen den Schlüssel.
- Dashboard: siehe Notiz 10.
