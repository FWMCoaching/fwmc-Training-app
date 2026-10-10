"""Woche, Monat, Quartal und Jahr zeigen für jeden Tag dasselbe (Fabian 09.10.2026:
Trainings ohne Plan-Eintrag hatten Punkte in der Wochenleiste, aber nicht im Monat).
Allgemeine Prüfung: jede Kalender-Ansicht wird gegen die Wochenleiste abgeglichen.
Heute neu (10.10.): Trainings sind neutrale D1-Punkte (.d1-dot) statt Bereichsfarben/Haken."""
import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ok = True
def check(name, cond, info=""):
    global ok
    print(f"{name}: {bool(cond)} {info}")
    ok = ok and bool(cond)

NOW = datetime(2026, 10, 9, 20, 30)
monday = NOW - timedelta(days=NOW.weekday())
def ts(d, h=9):
    return (datetime(d.year, d.month, d.day, h, 0) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:00.000Z")
hist = [
    {"id": "a1", "ts": ts(monday + timedelta(days=1)), "kind": "exercise", "exId": "vrw", "title": "VRW", "seconds": 300},
    {"id": "a2", "ts": ts(monday + timedelta(days=1), 18), "kind": "remember", "title": "Positionen merken", "seconds": 200},
    {"id": "a3", "ts": ts(monday + timedelta(days=2)), "kind": "balance", "title": "Gleichgewicht", "seconds": 200},
    {"id": "a4", "ts": ts(NOW), "kind": "breath-box", "title": "Box-Atmung", "seconds": 240},
    {"id": "a5", "ts": ts(datetime(2026, 9, 28)), "kind": "optodrum", "title": "Optodrum", "seconds": 120},
]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Europe/Berlin", service_workers="block")
    ctx.clock.install(time=NOW.strftime("%Y-%m-%dT%H:%M:00+02:00"))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.add_init_script("""localStorage.setItem('fwmc-test-bottomnav','1');localStorage.setItem('fwmc-onboarding-v1','1');
      localStorage.setItem('fwmc-tips-seen','1');localStorage.setItem('fwmc-history-v1', %s)""" % json.dumps(json.dumps(hist)))
    pg.goto(URL)
    pg.wait_for_timeout(900)

    week = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#todayWeekStrip [data-date]')].map(b =>
        [b.dataset.date, b.querySelectorAll('.d1-dot').length]))""")
    marked = [d for d, n in week.items() if n]
    check("Wochenleiste zeigt die Trainings ohne Plan", len(marked) == 3, week)

    def month_cells():
        return pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#calExpand .cal-cell[data-date]')].map(c =>
            [c.dataset.date, {dots: c.querySelectorAll('.d1-dot').length, check: !!c.querySelector('.cal-check'),
             cls: c.className, label: c.getAttribute('aria-label'), num: getComputedStyle(c.querySelector('.cal-num')).fontWeight}]))""")

    pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
    m = month_cells()
    for d, n in week.items():
        cell = m.get(d)
        has = bool(cell and (cell["dots"] or cell["check"]))
        check(f"Monat {d} wie Woche ({'Punkte' if n else 'leer'})", has == bool(n), cell)
    check("Monat: vergangener Monat-Tag 28.9. nicht im Oktober-Raster", "2026-09-28" not in m)
    check("Monat: Vorlesetext nennt Training ohne Plan", "ohne Plan" in (m.get(marked[0]) or {}).get("label", ""), (m.get(marked[0]) or {}).get("label"))

    pg.click("#calQuarterBtn"); pg.wait_for_timeout(300)
    q = month_cells()
    for d in week:
        cell = q.get(d)
        hi = bool(cell) and int(cell["num"]) >= 800
        check(f"Quartal {d} hervorgehoben wie Woche", hi == bool(week[d]), cell and (cell["cls"], cell["num"]))
    sep = q.get("2026-09-28")
    check("Quartal: Training im September sichtbar", sep is None or int(sep["num"]) >= 800, sep)

    pg.click("#calYearBtn"); pg.wait_for_timeout(300)
    y = month_cells()
    check("Jahr: Trainingstag hervorgehoben", int(y[marked[0]]["num"]) >= 800, y.get(marked[0]))
    check("Jahr: leerer Tag nicht hervorgehoben", int(y["2026-10-08"]["num"]) < 800, y.get("2026-10-08"))

    check("keine Fehler auf der Seite", not errs, errs[:3])
    b.close()

print("ALLE OK" if ok else "FAILED")
