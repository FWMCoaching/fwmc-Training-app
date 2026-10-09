"""Tippen auf einen Kalendertag auf Heute springt zur Tagesansicht (Fabian 09.10.2026)."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ok = True
def check(name, cond):
    global ok
    print(f"{name}: {cond}")
    ok = ok and bool(cond)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.add_init_script("localStorage.setItem('fwmc-test-bottomnav','1');localStorage.setItem('fwmc-onboarding-v1','1');localStorage.setItem('fwmc-tips-seen','1')")
    pg.goto(URL)
    pg.wait_for_timeout(800)
    panel_top = lambda: pg.evaluate("document.getElementById('todayDayPanel').getBoundingClientRect().top")
    # Wochenleiste: Tag antippen -> Tagesansicht rueckt nach oben ins Bild
    before = panel_top()
    pg.locator("#todayWeekStrip [data-date]").nth(2).click()
    pg.wait_for_timeout(900)
    after = panel_top()
    check("Woche: Tagesansicht im oberen Bildteil", after <= 844 * 0.6)
    check("Woche: Wochenleiste bleibt sichtbar", pg.evaluate("document.getElementById('todayWeekStrip').getBoundingClientRect().top") >= 40)
    # Monat aufklappen, nach oben, Tag tippen
    pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(200)
    pg.locator("#calExpand [data-date]").nth(20).click()
    pg.wait_for_timeout(900)
    t = panel_top()
    bar = pg.evaluate("Math.max(0,...[...document.querySelectorAll('.brandbar,.app-bar')].map(e=>{const r=e.getBoundingClientRect();return r.height>0&&r.top<=1?r.bottom:0}))")
    at_end = pg.evaluate("Math.abs(scrollY + innerHeight - document.documentElement.scrollHeight) < 3")
    check("Monat: Tagesansicht unter der Kopfleiste (oder Seitenende)", bar - 2 <= t <= bar + 40 or (at_end and t <= 844 * 0.5))
    # Schon gut im Bild: Wochenleiste antippen bewegt nichts
    pg.click("#calMonthBtn"); pg.wait_for_timeout(300)
    pg.locator("#todayWeekStrip [data-date]").nth(3).click(); pg.wait_for_timeout(700)
    y0 = pg.evaluate("scrollY")
    pg.locator("#todayWeekStrip [data-date]").nth(4).click(); pg.wait_for_timeout(700)
    check("kein zweiter Sprung", abs(pg.evaluate("scrollY") - y0) < 3)
    check("kein Fehler", not errs)
    print("ERRS", errs[:3])
    b.close()
print("ALL OK" if ok else "FAILED")
