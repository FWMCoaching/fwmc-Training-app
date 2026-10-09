"""Heute neu (Fabian 10.10.2026, Vorschau freigegeben): Begrüßung in einer Zeile
mit kurzem Datum, Zuletzt mit Streifen in der Bereichsfarbe, Atempause + Ring
(ein Segment je geplantem Training der Woche), ruhige Kalender-Zeichen D1
(rund = Training, eckig = Termin, keine Bereichsfarben, max. 3 + "+"), der Tag
als Zeitleiste T1 (Zeit, Linie, Karten, Lücken, Kombi-Symbol mit Bausteinen),
ab 900 px Monat links / Tag rechts. Hell und dunkel, ohne Seitenfehler.
Run from tests/ with the dev server on :8845."""
import json, datetime
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT = "screenshots/heute_neu/"
NOW = datetime.datetime(2026, 10, 9, 20, 30)  # Freitag
MON = datetime.date(2026, 10, 5)
ok = True

def check(name, cond, info=""):
    global ok
    print(f"{name}: {bool(cond)} {info if not cond else ''}")
    ok = ok and bool(cond)

def d(n):
    return (MON + datetime.timedelta(days=n)).isoformat()

def ts(day, h=18):
    return f"{day}T{h:02d}:10:00+02:00"

HIST = [
    {"id": "h1", "ts": ts(d(0), 7), "kind": "breath", "title": "Box-Atmung", "seconds": 600},
    {"id": "h2", "ts": ts(d(1)), "kind": "exercise", "exId": "vt-color", "title": "Farbe & Seite", "seconds": 900},
    {"id": "h3", "ts": ts(d(2)), "kind": "remember", "title": "Positionen merken · Optodrum", "seconds": 700},
]
HIST.sort(key=lambda h: h["ts"], reverse=True)

def entry(i, area, time, mins, what=""):
    return {"id": i, "area": area, "what": what, "code": "", "time": time, "minutes": mins}

PLAN = {"startDate": d(-7), "phases": [{"id": "p1", "name": "Grundphase", "weeks": 0, "days": [
    [entry("a", "breath", "07:30", 10)], [entry("b", "visual", "18:00", 15)], [entry("c", "nat", "18:00", 12)], [],
    [entry("k", "combo", "18:00", 25, "combo:k1")], [], []]}],
    "extras": {}, "skips": {}, "done": {}, "source": {"code": "TESTPLAN", "version": 1, "at": "2026-10-01T10:00:00Z", "baseTimes": {}}}
COMBO = [{"id": "k1", "name": "Kombi-Programm", "blocks": [
    {"domain": "visual", "exercise": "vt-color", "duration": 480},
    {"domain": "nat", "mode": "classic", "duration": 600},
    {"domain": "breath", "pattern": "box", "durationMin": 7}]}]
EVENTS = [
    {"id": "e1", "date": d(4), "time": "12:15", "title": "Physio", "kind": "erholung"},
    {"id": "e2", "date": d(3), "time": "19:00", "title": "Vereinstraining", "kind": "training", "repeat": "weekly"},
] + [{"id": f"m{i}", "date": d(12), "time": f"1{i}:00", "title": f"Termin {i}", "kind": "sonstiges"} for i in range(5)]

def store(with_hist=True, with_plan=True, name="Fabian", mood=True):
    st = {"fwmc-test-bottomnav": "1", "fwmc-onboarding-v1": "1", "fwmc-tips-seen": "true",
          "fwmc-master-v1": json.dumps({"startCountdown": False}), "fwmc-start-v1": json.dumps({"who": "trainer"})}
    if with_hist: st["fwmc-history-v1"] = json.dumps(HIST)
    if with_plan:
        st["fwmc-plan-v1"] = json.dumps(PLAN); st["fwmc-combo-saved-v1"] = json.dumps(COMBO); st["fwmc-events-v1"] = json.dumps(EVENTS)
    if name: st["fwmc-name-v1"] = name
    if mood: st["fwmc-mood-v1"] = json.dumps({"2026-10-09": {"v": 3, "at": 0}})
    return st

def open_page(b, st, w=390, h=844, scheme="light"):
    ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, timezone_id="Europe/Berlin", locale="de-DE", service_workers="block")
    ctx.clock.install(time=NOW.strftime("%Y-%m-%dT%H:%M:00+02:00"))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)});" for k, v in st.items())
    pg.add_init_script(f"if(!sessionStorage.getItem('s')){{{js}sessionStorage.setItem('s','1');}}")
    pg.goto(URL + "?bereich=heute"); pg.wait_for_timeout(900)
    return ctx, pg, errs

def box(pg, sel):
    return pg.locator(sel).first.bounding_box()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])

    # ---- 1. Happy path, iPhone, hell ----
    ctx, pg, errs = open_page(b, store())
    g = pg.inner_text("#todayGreeting").strip()
    check("Begrüßung mit Name", g == "Guten Abend, Fabian", g)
    check("kurzes Datum rechts", pg.inner_text("#todayDate").strip() == "Fr, 9. Okt.", pg.inner_text("#todayDate"))
    bg, bd = box(pg, "#todayGreeting"), box(pg, "#todayDate")
    check("Begrüßung und Datum in einer Zeile", abs((bg["y"] + bg["height"]) - (bd["y"] + bd["height"])) < 10 and bd["x"] > bg["x"] + bg["width"] - 2, (bg, bd))
    check("Datum vorgelesen lang", pg.get_attribute("#todayDate", "aria-label") == "Freitag, 9. Oktober")
    # Pair
    t1, t2 = box(pg, "#todayBreak"), box(pg, "#todayNewTile")
    check("Atempause + Ring nebeneinander, gleich hoch", abs(t1["y"] - t2["y"]) < 2 and abs(t1["height"] - t2["height"]) < 2, (t1, t2))
    check("Atempause-Kicker", pg.inner_text("#todayBreak .today-break-kicker").strip().upper() == "ATEMPAUSE")
    check("Atempause-Kreis 96 px", abs(box(pg, "#todayBreak .today-tile-circle")["width"] - 96) < 1)
    check("Ring 96 px", abs(box(pg, "#todayNewTile .today-ring")["width"] - 96) < 1)
    segs = pg.locator("#todayNewTile .today-ring circle").count()
    done = pg.locator("#todayNewTile .today-ring .ring-done").count()
    summ = pg.evaluate("(() => { const el = document.querySelector('#todayNewTile .today-ring-num'); return el.textContent; })()")
    check("Ring: ein Segment je geplantem Training (4), 3 erledigt", segs == 4 and done == 3, (segs, done))
    check("Ring-Mitte 3/4", summ.replace(" ", "") == "3/4", summ)
    prog = pg.inner_text("#todayProgress")
    check("Ring passt zur Wochenzeile", "3 von 4" in prog, prog)
    check("ehrliche Zeile unter dem Ring", "Noch 1" in pg.inner_text("#todayNewTile"), pg.inner_text("#todayNewTile"))
    check("Ring vorgelesen", "3 von 4" in (pg.get_attribute("#todayNewTile .today-ring", "aria-label") or ""))
    # D1 Woche
    wk = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#todayWeekStrip [data-date]')].map(b => [b.dataset.date,
        [...b.querySelectorAll('.d1-dot, .d1-sq, .d1-more')].map(i => i.className.replace(/\\b(d1-dot|d1-sq|event-mark)\\b/g, '').trim())]))""")
    check("Mo/Di/Mi erledigt (gefüllt)", all(wk[d(i)] == ["is-done"] for i in range(3)), wk)
    check("Do: Termin-Serie (hohles Quadrat)", wk[d(3)] == ["is-series"], wk[d(3)])
    check("Fr heute: geplant hohl + Termin gefüllt", wk[d(4)] == ["is-plan", "is-single"], wk[d(4)])
    check("keine Bereichsfarben in den Zeichen", pg.locator("#todayWeekStrip .area-dot").count() == 0)
    on = pg.evaluate("getComputedStyle(document.querySelector('#todayWeekStrip .week-day.selected .d1-sq')).backgroundColor")
    check("heute: Zeichen hell auf Markenfläche", on in ("rgb(255, 255, 255)",), on)
    # Monat
    pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
    mo = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#calExpand .cal-cell[data-date]')].map(c => [c.dataset.date,
        [...c.querySelectorAll('.d1-dot, .d1-sq, .d1-more')].map(i => i.className.replace(/\\b(d1-dot|d1-sq|event-mark)\\b/g, '').trim())]))""")
    check("Monat = Woche für jeden Tag", all(mo[k] == v for k, v in wk.items()), [(k, mo.get(k), v) for k, v in wk.items() if mo.get(k) != v])
    check("vergangener Plan-Tag ohne Training: blass (nicht gemacht)", mo[d(-3)] == ["is-missed"], mo.get(d(-3)))
    check("künftiger Plan-Tag: hohl", mo[d(7)] == ["is-plan"], mo.get(d(7)))
    check("mehr als 3 Zeichen: 3 + '+'", len(mo[d(12)]) == 4 and mo[d(12)][-1] == "d1-more", mo.get(d(12)))
    check("Legende unter dem Monat", "Termin-Serie" in pg.inner_text("#calExpand .d1-legend") and "nicht gemacht" in pg.inner_text("#calExpand .d1-legend"))
    check("Monat: Woche hinterlegt", pg.locator("#calExpand .cal-cell.in-week").count() == 7)
    pg.screenshot(path=OUT + "390_hell.png", full_page=True)
    # T1
    tl = pg.evaluate("""() => [...document.querySelectorAll('#dayTimeline .t1-row')].map(r => ({t: r.querySelector('.t1-time').textContent, y: r.getBoundingClientRect().top,
        title: r.querySelector('.day-item-title').textContent}))""")
    tl.sort(key=lambda r: r["y"])
    check("Zeitleiste: Physio 12:15 vor Kombi 18:00", [r["t"] for r in tl] == ["12:15", "18:00"], tl)
    gap = pg.locator("#dayTimeline .day-gap").first
    check("Lücke '5 Std. 45 Min. dazwischen' zwischen den Einträgen", "5 Std. 45 Min. dazwischen" in gap.inner_text() and tl[0]["y"] < gap.bounding_box()["y"] < tl[1]["y"])
    check("Kopfzeile '1 Training · 1 Termin'", pg.inner_text("#dayPanelSub").strip() == "1 Training · 1 Termin", pg.inner_text("#dayPanelSub"))
    k = "#dayPanelBody .day-item[data-occ='k']"
    sq = pg.evaluate(f"[...document.querySelectorAll(\"{k} .combo-ico i\")].map(i => i.getAttribute('style') || '')")
    check("Kombi-Symbol: 4 Quadrate, 3 in Bausteinfarben, 1 neutral", len(sq) == 4 and sum(1 for s in sq if "var(--area-" in s) == 3, sq)
    li = pg.locator(f"{k} .t1-blocks li")
    check("Kombi listet 3 Bausteine mit Minuten", li.count() == 3 and all("Min." in li.nth(i).inner_text() for i in range(3)))
    check("Kombi: Chip 'offen'", pg.inner_text(f"{k} .t1-chip").strip() == "offen")
    check("Plan vom Trainer markiert", "von deinem Trainer" in pg.inner_text(f"{k} .day-item-title") and "jede Woche (Plan von deinem Trainer)" in pg.inner_text(f"{k} .t1-repeat"))
    check("'Training starten' in der Karte", pg.inner_text(f"{k} .t1-start").strip() == "Training starten")
    check("Termin als Karte mit Kalender-Symbol", pg.locator("#dayEvents .event-item .t1-ico.is-ev svg").count() == 1 and pg.locator("#dayEvents .t1-node.is-ev").count() == 1)
    ex = pg.evaluate("document.documentElement.scrollWidth")
    check("kein seitliches Scrollen", ex <= 390, ex)
    small = pg.evaluate("""() => [...document.querySelectorAll('#dayTimeline button')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect().height).filter(h => h < 44)""")
    check("Tasten im Tag ≥ 44 px", not small, small)
    # Abhaken still works
    pg.click(f"{k} [data-act='done']"); pg.wait_for_timeout(200)
    check("Abhaken: Karte erledigt", pg.locator(f"{k}.done").count() == 1 and pg.inner_text(f"{k} .t1-chip").strip() == "erledigt")
    check("Abhaken: Ring 4/4", pg.locator("#todayNewTile .today-ring .ring-done").count() == 4)
    pg.click(f"{k} [data-act='done']"); pg.wait_for_timeout(200)
    # future and past day
    pg.click("#todayWeekNext"); pg.wait_for_timeout(200)
    pg.click(f"#todayWeekStrip [data-date='{d(7)}']"); pg.wait_for_timeout(200)
    body = pg.inner_text("#dayPanelBody")
    check("kommender Tag: Chip 'geplant', kein Abhaken", "geplant" in body and "Abhaken" not in body and "offen" not in body, body[:120])
    check("kommender Tag: hohler Knoten", pg.locator("#dayPanelBody .t1-node.is-plan").count() == 1)
    pg.click("#todayWeekPrev"); pg.wait_for_timeout(150); pg.click("#todayWeekPrev"); pg.wait_for_timeout(200)
    pg.click(f"#todayWeekStrip [data-date='{d(-3)}']"); pg.wait_for_timeout(200)
    body = pg.inner_text("#dayPanelBody")
    check("vergangener Tag: 'nicht gemacht'", "nicht gemacht" in body and " offen" not in body, body[:120])
    check("keine Seitenfehler (hell)", not errs, errs[:3])
    ctx.close()

    # ---- 2. Dunkel ----
    ctx, pg, errs = open_page(b, store(), scheme="dark")
    bgc = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    card = pg.evaluate("getComputedStyle(document.querySelector('#todayBreak')).backgroundColor")
    check("dunkel: dunkler Grund, Karten heben sich ab", bgc == "rgb(12, 27, 32)" and card != bgc, (bgc, card))
    ring_open = pg.evaluate("getComputedStyle(document.querySelector('#todayNewTile .ring-open')).stroke")
    check("dunkel: offenes Segment dunkelgrau", ring_open == "rgb(42, 73, 80)", ring_open)
    pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
    pg.screenshot(path=OUT + "390_dunkel.png", full_page=True)
    check("keine Seitenfehler (dunkel)", not errs, errs[:3])
    ctx.close()

    # ---- 3. Zuletzt-Streifen (heute nichts geplant) ----
    st = store(with_plan=False)
    ctx, pg, errs = open_page(b, st)
    check("Zuletzt als flache Karte", pg.locator("#todayMain.is-flat .today-last").count() == 1)
    check("Kicker 'Zuletzt · Mittwoch'", pg.inner_text("#todayMain .today-main-kicker").strip().upper() == "ZULETZT · MITTWOCH", pg.inner_text("#todayMain .today-main-kicker"))
    ac = pg.evaluate("getComputedStyle(document.getElementById('todayMain')).getPropertyValue('--ac').trim()")
    stripe = pg.evaluate("getComputedStyle(document.getElementById('todayMain'), '::before').backgroundColor")
    check("Streifen in NAT-Farbe", ac.lower() == "#3a7d2c" and stripe == "rgb(58, 125, 44)", (ac, stripe))
    check("Nochmal-Taste", pg.inner_text("#todayContinueBtn").strip() == "Nochmal")
    check("keine Seitenfehler (Zuletzt)", not errs, errs[:3])
    ctx.close()

    # ---- 4. ohne Namen, ohne Verlauf ----
    ctx, pg, errs = open_page(b, store(with_hist=False, with_plan=False, name="", mood=False))
    check("ohne Namen: Begrüßung ohne Komma", pg.inner_text("#todayGreeting").strip() == "Guten Abend")
    check("ohne Namen: 'Wie heißt du?'", pg.is_visible("#helloNameBtn"))
    check("leerer Verlauf: keine Zeichen in der Woche", pg.locator("#todayWeekStrip .d1-dot, #todayWeekStrip .d1-sq").count() == 0)
    check("leerer Verlauf: Atempause sichtbar", pg.is_visible("#todayBreak"))
    check("keine Seitenfehler (leer)", not errs, errs[:3])
    ctx.close()

    # ---- 5. iPad quer 1024: Karten oben nebeneinander, Monat links, Tag rechts ----
    for scheme in ("light", "dark"):
        ctx, pg, errs = open_page(b, store(), w=1024, h=1366, scheme=scheme)
        pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
        hello, pair = box(pg, ".today-top-main"), box(pg, "#todayPair")
        check(f"iPad {scheme}: Karten rechts neben Begrüßung", pair["x"] > hello["x"] + hello["width"] - 1 and abs(pair["y"] - hello["y"]) < 40, (hello, pair))
        cal, day = box(pg, ".today-week-cal"), box(pg, "#todayDayPanel")
        check(f"iPad {scheme}: Monat links, Tag rechts", day["x"] >= cal["x"] + cal["width"] and abs(day["y"] - cal["y"]) < 30, (cal, day))
        check(f"iPad {scheme}: kein seitliches Scrollen", pg.evaluate("document.documentElement.scrollWidth") <= 1024)
        pg.screenshot(path=OUT + f"1024_{scheme}.png", full_page=True)
        check(f"iPad {scheme}: keine Seitenfehler", not errs, errs[:3])
        ctx.close()

    # ---- 6. iPhone: Reihenfolge wie bisher (eine Spalte) ----
    ctx, pg, errs = open_page(b, store())
    y = [box(pg, s)["y"] for s in ("#todayGreeting", "#todayMain", "#todayPair", ".today-week-cal", "#todayDayPanel")]
    check("iPhone: eine Spalte, Reihenfolge Begrüßung > Karte > Paar > Woche > Tag", y == sorted(y), y)
    ctx.close()
    b.close()

print("ALLE OK" if ok else "FAILED")
