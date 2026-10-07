import sys, json, datetime
from playwright.sync_api import sync_playwright

# Small fixes of 2026-10-04 (Fabian's reports): history in every area,
# old exercise names renamed, "Ziel erreicht" instead of "11 von 3",
# logo has its size before it loads, dashboard follows light/dark.
BASE = "http://localhost:8845/"
results = []
def check(name, ok, extra=""):
    results.append(bool(ok)); print(f"{name}: {bool(ok)} {extra}".rstrip())

now = datetime.datetime.utcnow()
hist = [{"id": str(i), "ts": (now - datetime.timedelta(minutes=10 * i)).isoformat() + "Z", "kind": "remember",
         "title": "Remember · Feste Positionen" if i == 0 else "Workout", "seconds": 120, "rating": None} for i in range(5)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme="light")
    ctx.add_init_script("localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-tips-seen','true');"
                        f"localStorage.setItem('fwmc-history-v1', {json.dumps(json.dumps(hist))});"
                        "localStorage.setItem('fwmc-progress-v1', JSON.stringify({weekGoal:3, days:{}, seeded:false}));")
    pg = ctx.new_page(); errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    for area, sec in [("cardio", "#cardioHistorySection"), ("nat", "#natHistorySection"), ("test", "#testHistorySection"), ("workout", "#workoutHistorySection")]:
        pg.goto(BASE + "index.html?bereich=" + area); pg.wait_for_timeout(300)
        check(f"{area}: Gesamter Trainingsverlauf shown", pg.is_visible(sec))
    pg.click("#workoutHistoryMoreBtn"); pg.wait_for_timeout(100)
    check("Alle anzeigen expands", pg.locator("#workoutHistoryList li").count() == 5)
    check("old name shown as Positionen merken", "Positionen merken · Feste Positionen" in pg.inner_text("#workoutHistoryList") and "Remember" not in pg.inner_text("#workoutHistoryList"))
    pg.goto(BASE + "index.html?bereich=heute"); pg.wait_for_timeout(400)
    card = pg.inner_text("#todayProgressCard")
    # kp2 (Trainingsplanung 07.10.): the goal counts up to the goal, more is "zusätzlich"
    check("week goal reached is marked", "Wochenziel erreicht" in card and "3 von 3 ✓" in card and "2 zusätzlich" in card, card.replace("\n", " | ")[:80])
    check("Weitermachen shows the new name", "Remember" not in pg.inner_text("#todayMain"))
    w = pg.evaluate("document.querySelector('#todayHome .brand-logo').getAttribute('width')")
    check("logo carries its size before loading", w == "900")
    pg.goto(BASE + "dashboard.html"); pg.wait_for_timeout(300)
    light_bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    ctx2 = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark")
    pg2 = ctx2.new_page(); pg2.goto(BASE + "dashboard.html"); pg2.wait_for_timeout(300)
    dark_bg = pg2.evaluate("getComputedStyle(document.body).backgroundColor")
    check("dashboard light in light mode", light_bg == "rgb(246, 248, 249)", light_bg)
    check("dashboard dark in dark mode", dark_bg == "rgb(15, 17, 21)", dark_bg)
    check("no page errors", not errors, errors[:2])
    b.close()
print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
