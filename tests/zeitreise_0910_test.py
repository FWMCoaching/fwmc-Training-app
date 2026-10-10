"""Zeitreise + Zahlwörter (Fabian 09.10.2026: "Ich will nicht mehr der sein, dem sowas auffällt").

Allgemeine Prüfung statt Einzelfall: die App läuft mit verstellter Uhr an festen Stichtagen
(Wochentage, Sonntag früh/spät, Montag 00:30, Silvester, Neujahr, Zeitumstellung) mit
festem Beispielverlauf. Regeln:
- Kalendertage nach heute: kein "erledigt"/"offen"/"Abhaken"/"Heute auslassen" (heißt "geplant").
- Kalendertage vor heute: kein "offen", kein "Heute auslassen", kein Eintragen, keine Vorschläge.
- Begrüßung passt zur Stunde.
- Kein Wochenabschluss, solange am Sonntag noch eine Einheit aussteht (vor 20 Uhr).
- "Noch N bis zum Ziel": N nie größer als die noch möglichen Einheiten.
- Nach Mitternacht (App im Speicher) zeigt Heute den neuen Tag.
- Auf jeder besuchten Seite: keine "1 Runden/Tage/…", kein "90s", kein "Min" ohne Punkt.
Lauf: aus tests/, Server auf :8845.
"""
import asyncio, datetime, json, re
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
DATES = ["2026-10-05T09:00", "2026-10-09T10:00", "2026-10-11T08:00", "2026-10-11T21:30", "2026-10-12T00:30",
         "2026-10-14T04:30", "2026-12-31T23:30", "2027-01-01T09:00", "2026-10-25T02:30", "2026-10-26T09:00"]
fails = []
def check(name, cond, extra=""):
    print(f"{name}: {bool(cond)} {extra if not cond else ''}")
    if not cond: fails.append(name)

def offset(t):  # Berlin: Sommerzeit bis 25.10.2026 03:00
    dt = datetime.datetime.fromisoformat(t)
    return "+02:00" if datetime.datetime(2026, 3, 29, 2) <= dt < datetime.datetime(2026, 10, 25, 3) else "+01:00"

def store_for(now):
    d = now.date(); mon = d - datetime.timedelta(days=d.weekday())
    hist = []
    for i, ago in enumerate([1, 2, 3, 6, 8, 15]):
        ts = (now - datetime.timedelta(days=ago)).replace(hour=16)
        hist.append({"id": "h%d" % i, "ts": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "seconds": 300, "kind": "breath", "title": "Box-Atmung"})
    extras = {}
    for k, area in [(0, "breath"), (2, "visual"), (4, "nat"), (6, "breath")]:
        extras[(mon + datetime.timedelta(days=k)).isoformat()] = [{"id": "x%d" % k, "area": area, "minutes": 10, "time": "18:00"}]
    mood = {(d - datetime.timedelta(days=j)).isoformat(): {"v": 1 + j % 3, "at": 0} for j in range(1, 12)}
    return {"fwmc-tips-seen": True, "fwmc-onboarding-v1": "1", "fwmc-test-bottomnav": "1", "fwmc-master-v1": {"startCountdown": False},
            "fwmc-history-v1": hist, "fwmc-plan-v1": {"extras": extras}, "fwmc-mood-v1": mood, "fwmc-name-v1": "Anna",
            "fwmc-start-v1": {"who": "allein", "goal": "ruhe", "goalAt": "2026-08-01"}}

ZAHL = re.compile(r"(?<![\d,.])1 (Runden|Sätze|Tage|Durchgänge|Trainings|Übungen|Minuten|Einheiten|Wochen|Bausteine|Stunden)\b")
FMT = [(re.compile(r"\b\d+s\b"), "Zahl+s ohne Leerzeichen"), (re.compile(r"\d Min(?![.\w])"), "Min ohne Punkt"), (re.compile(r"\d Sek(?![.\w])"), "Sek ohne Punkt")]
def scan_text(where, txt):
    m = ZAHL.search(txt)
    check(f"{where}: Einzahl/Mehrzahl", not m, m.group(0) if m else "")
    for rx, what in FMT:
        m = rx.search(txt)
        check(f"{where}: {what}", not m, m.group(0) if m else "")

def greet_ok(h, g):
    want = "Hallo" if h < 5 else "Guten Morgen" if h < 11 else "Guten Tag" if h < 17 else "Guten Abend"
    return g.startswith(want)

async def run_date(b, t):
    now = datetime.datetime.fromisoformat(t)
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Europe/Berlin", locale="de-DE", service_workers="block")
    await ctx.clock.install(time=datetime.datetime.fromisoformat(t + ":00" + offset(t)))
    st = store_for(now)
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v if isinstance(v, str) else json.dumps(v))});" for k, v in st.items())
    await ctx.add_init_script(f"if(!sessionStorage.getItem('s')){{{js}sessionStorage.setItem('s','1');}}")
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    await pg.goto(URL + "?bereich=heute"); await pg.wait_for_timeout(900)
    tag = t
    today = now.date().isoformat() if now.hour >= 0 else ""
    g = await pg.evaluate("(document.querySelector('#todayGreeting')||{}).innerText || ''")
    check(f"{tag}: Begrüßung passt zur Stunde", greet_ok(now.hour, g), g)
    scan_text(f"{tag} Heute", await pg.inner_text("#todayHome"))
    # jeden Tag der Woche anklicken
    days = await pg.evaluate("[...document.querySelectorAll('#todayWeekStrip [data-date]')].map(b => b.dataset.date)")
    for d in days:
        await pg.click(f'#todayWeekStrip [data-date="{d}"]'); await pg.wait_for_timeout(120)
        body = await pg.inner_text("#dayPanelBody")
        if d > today:
            bad = [w for w in ("erledigt", "offen", "Abhaken", "Heute auslassen", "nicht gemacht") if w in body]
            check(f"{tag} {d} (Zukunft): keine Vergangenheit/kein Abhaken", not bad, bad)
        elif d < today:
            bad = [w for w in (" offen", "Heute auslassen", "· geplant") if w in body]
            check(f"{tag} {d} (vorbei): kein 'offen'/'Heute auslassen'", not bad, bad)
            # Kundenblick 10.10.: a past day only shows what happened - no
            # "Noch kein Plan", no adding (would be missed at once), no suggestions.
            vis = await pg.evaluate("['dayAddBtn','dayEventAddBtn','todayGoal'].filter(id => { const e = document.getElementById(id); return e && !e.hidden && e.getClientRects().length; })")
            check(f"{tag} {d} (vorbei): nichts zum Eintragen, keine Vorschläge", not vis and "Noch kein Plan" not in body, vis)
            if not await pg.locator("#dayPanelBody .day-item, #dayPanelBody .extra-item, #dayEvents .event-item").count() and "Pause" not in body:
                check(f"{tag} {d} (vorbei, leer): 'An diesem Tag war nichts geplant.'", "An diesem Tag war nichts geplant." in body or "kein Training aus der App geplant" in body, body[:80])
        else:
            vis = await pg.evaluate("['dayAddBtn','dayEventAddBtn'].filter(id => { const e = document.getElementById(id); return e && !e.hidden && e.getClientRects().length; })")
            check(f"{tag} {d} (heute): Eintragen möglich", len(vis) == 2, vis)
    # Wochenabschluss am Sonntag erst, wenn der Sonntag durch ist
    if now.weekday() == 6:
        review = await pg.evaluate("(document.querySelector('#todayWeekReview')||{}).innerText || ''")
        if now.hour < 20:
            check(f"{tag}: kein Wochenabschluss vor der Sonntagseinheit", "wochenabschluss" not in review.lower(), review[:80])
        else:
            check(f"{tag}: Wochenabschluss am Sonntagabend", "wochenabschluss" in review.lower(), review[:80])
    # Fortschritt: "Noch N bis zum Ziel" nie mehr als noch möglich
    await pg.goto(URL + "?bereich=fortschritt"); await pg.wait_for_timeout(600)
    txt = await pg.inner_text("#progressScreen")
    scan_text(f"{tag} Fortschritt", txt)
    m = re.search(r"Noch (\d+) bis zum Ziel", txt)
    if m:
        ahead = sum(1 for k in (0, 2, 4, 6) if (now.date() - datetime.timedelta(days=now.weekday()) + datetime.timedelta(days=k)) >= now.date())
        check(f"{tag}: 'Noch {m.group(1)} bis zum Ziel' ≤ {ahead} noch mögliche", int(m.group(1)) <= ahead)
    check(f"{tag}: keine Seitenfehler", not errs, errs[:2])
    await ctx.close()

async def midnight(b):
    t = "2026-10-09T23:50"
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Europe/Berlin", locale="de-DE", service_workers="block")
    await ctx.clock.install(time=datetime.datetime.fromisoformat(t + ":00+02:00"))
    st = store_for(datetime.datetime.fromisoformat(t))
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v if isinstance(v, str) else json.dumps(v))});" for k, v in st.items())
    await ctx.add_init_script(f"if(!sessionStorage.getItem('s')){{{js}sessionStorage.setItem('s','1');}}")
    pg = await ctx.new_page()
    await pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    await pg.goto(URL + "?bereich=heute"); await pg.wait_for_timeout(900)
    await pg.clock.set_system_time(datetime.datetime.fromisoformat("2026-10-10T08:00:00+02:00"))
    await pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(400)
    title = await pg.inner_text("#dayPanelTitle")
    g = await pg.evaluate("(document.querySelector('#todayGreeting')||{}).innerText || ''")
    check("Mitternacht: Tagesansicht springt auf Samstag", "Samstag" in title or "10." in title, title)
    check("Mitternacht: Begrüßung neu (Guten Morgen)", g.startswith("Guten Morgen"), g)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for t in DATES:
            await run_date(b, t)
        await midnight(b)
        await b.close()
    print("ALL OK" if not fails else f"FAILED: {len(fails)}: {fails[:8]}")

asyncio.run(main())
