# Häppchen 13-15 (Fabian, 2026-10-02):
# 13 leaving the app mid-training auto-presses that player's "Pause"
#    (Cardio keeps running on purpose),
# 14 every footer shows "Stand: <Datum, Uhrzeit>",
# 15 Cardio has a Vollbild button like every other player.
import re, sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(label, ok):
    results.append(ok)
    print(f"{label}: {ok}")


INIT = """
localStorage.setItem('fwmc-tips-seen','true');
window.__vis = 'visible';
Object.defineProperty(document, 'visibilityState', { get: () => window.__vis, configurable: true });
Object.defineProperty(document, 'hidden', { get: () => window.__vis === 'hidden', configurable: true });
window.__leave = () => { window.__vis = 'hidden'; document.dispatchEvent(new Event('visibilitychange')); };
window.__back = () => { window.__vis = 'visible'; document.dispatchEvent(new Event('visibilitychange')); };
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.add_init_script(INIT)
    pg.goto(URL)
    pg.wait_for_timeout(300)

    # 14: version stamp
    stamps = pg.evaluate("[...document.querySelectorAll('.site-footer .app-version')].map(e=>e.textContent.trim())")
    check("every footer has a Stand line", len(stamps) == 11)
    check("Stand looks like a date and time", all(re.fullmatch(r"Stand: \d\d\.\d\d\.\d{4}, \d\d:\d\d", s) for s in stamps))
    check("version visible on home", pg.locator("#home .app-version").is_visible())

    # 13: Positionen merken pauses itself when leaving the app
    pg.click('.section-tab[data-section="nat"]'); pg.wait_for_timeout(200)
    pg.click('[data-nat-sub="remember"]'); pg.wait_for_timeout(200)
    pg.click("#rememberOpenFixed"); pg.wait_for_timeout(200)
    pg.click("#rememberReadyStartBtn"); pg.wait_for_timeout(800)
    pg.evaluate("window.__leave()"); pg.wait_for_timeout(200)
    pg.evaluate("window.__back()"); pg.wait_for_timeout(200)
    check("Positionen merken: pause screen after leaving", pg.is_visible("#rememberPauseOverlay"))
    # leaving again while paused must not toggle anything
    pg.evaluate("window.__leave()"); pg.evaluate("window.__back()"); pg.wait_for_timeout(200)
    check("still paused after leaving twice", pg.is_visible("#rememberPauseOverlay"))
    pg.click("#rememberResumeBtn"); pg.wait_for_timeout(200)
    check("resume works", pg.is_hidden("#rememberPauseOverlay"))
    pg.click("#rememberBackBtn"); pg.wait_for_timeout(300)

    # 13: Tabata-Zirkel pauses too (shared train-pause sheet)
    pg.goto(URL); pg.wait_for_timeout(300)
    pg.click('.section-tab[data-section="workout"]'); pg.wait_for_timeout(200)
    pg.click("#workoutTabataStartCard"); pg.wait_for_timeout(200)
    pg.locator("#workoutCircuitAddGrid .ca-plus-btn").nth(0).click(); pg.wait_for_timeout(100)
    pg.click("#workoutTabataStartBtn"); pg.wait_for_timeout(800)
    pg.evaluate("window.__leave()"); pg.wait_for_timeout(200)
    pg.evaluate("window.__back()"); pg.wait_for_timeout(200)
    check("Zirkel: pause sheet after leaving", pg.is_visible("#trainPauseOverlay"))

    # 13 (negative) + 15: Cardio keeps running, has a Vollbild button
    pg.goto(URL); pg.wait_for_timeout(300)
    pg.click('.section-tab[data-section="cardio"]'); pg.wait_for_timeout(200)
    pg.click("#cardioStartCard"); pg.wait_for_timeout(200)
    pg.click('#cardioAddGrid >> text="Joggen"'); pg.wait_for_timeout(100)
    pg.click("#cardioStartBtn"); pg.wait_for_timeout(500)
    check("Cardio: Vollbild button visible", pg.is_visible("#cardioFsBtn"))
    pg.evaluate("window.__leave()"); pg.wait_for_timeout(200)
    pg.evaluate("window.__back()"); pg.wait_for_timeout(200)
    check("Cardio: no pause after leaving", pg.is_hidden("#trainPauseOverlay"))
    t1 = pg.inner_text("#cardioCountdown"); pg.wait_for_timeout(1300)
    check("Cardio countdown still running", pg.inner_text("#cardioCountdown") != t1)
    pg.click("#cardioFsBtn"); pg.wait_for_timeout(400)
    fs = pg.evaluate("document.fullscreenElement && document.fullscreenElement.id")
    check("Vollbild: fullscreen or embedded-view hint", fs == "cardioPlayer" or pg.is_visible("#cardioFsHint"))
    if fs == "cardioPlayer":
        check("button reads Vollbild aus", pg.inner_text("#cardioFsBtn").strip() == "Vollbild aus")
        pg.click("#cardioBackBtn"); pg.wait_for_timeout(400)
        check("ending Cardio leaves fullscreen", pg.evaluate("document.fullscreenElement === null"))

    check("no page errors", not errors)
    b.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
