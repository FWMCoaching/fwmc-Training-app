# "Wirklich beenden?" (Fabian, 2026-10-02): once a training has run for at
# least a minute, "✕ Beenden" asks first (in-app sheet, never confirm()).
# Shorter runs end straight away. Date.now is warped so the test needn't wait.
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(label, ok):
    results.append(ok)
    print(f"{label}: {ok}")


INIT = """
localStorage.setItem('fwmc-tips-seen','true');
(function(){ const real = Date.now; let off = 0; window.__warp = (ms) => { off += ms; }; Date.now = () => real() + off; })();
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: (errors.append("native dialog"), d.dismiss()))
    pg.add_init_script(INIT)
    pg.goto(URL)
    pg.wait_for_timeout(300)

    # Short run: no question.
    pg.click('.excard[data-exercise="vt-color"]'); pg.wait_for_timeout(200)
    pg.click("#startBtn"); pg.wait_for_timeout(1300)
    pg.click("#backBtn"); pg.wait_for_timeout(300)
    check("short run ends without asking", pg.is_hidden("#confirmSheet") and pg.is_hidden("#player"))

    # Long run (Beenden lands back on the ready screen): asks; Nein keeps
    # training, Ja ends it.
    pg.click("#startBtn"); pg.wait_for_timeout(1300)
    pg.evaluate("window.__warp(70000)")
    pg.click("#backBtn"); pg.wait_for_timeout(300)
    check("long run asks first", pg.is_visible("#confirmSheet"))
    check("question text", "wirklich beenden" in pg.inner_text("#confirmText"))
    check("player still running while asked", pg.is_visible("#player"))
    pg.click("#confirmNoBtn"); pg.wait_for_timeout(300)
    check("Nein keeps the training", pg.is_hidden("#confirmSheet") and pg.is_visible("#player"))
    pg.click("#backBtn"); pg.wait_for_timeout(300)
    pg.click("#confirmYesBtn"); pg.wait_for_timeout(400)
    check("Ja ends the training", pg.is_hidden("#player") and pg.is_hidden("#confirmSheet"))
    check("sheet back in body", pg.evaluate("document.getElementById('confirmSheet').parentNode === document.body"))

    # Clock resets for the next run.
    pg.click("#startBtn"); pg.wait_for_timeout(1300)
    pg.click("#backBtn"); pg.wait_for_timeout(300)
    check("new run starts its own clock", pg.is_hidden("#confirmSheet") and pg.is_hidden("#player"))

    # Another player (Positionen merken) asks too.
    pg.click("#backToHome"); pg.wait_for_timeout(200)
    pg.click('.section-tab[data-section="nat"]'); pg.wait_for_timeout(200)
    pg.click('[data-nat-sub="remember"]'); pg.wait_for_timeout(200)
    pg.click("#rememberOpenFixed"); pg.wait_for_timeout(200)
    pg.click("#rememberReadyStartBtn"); pg.wait_for_timeout(1300)
    pg.evaluate("window.__warp(70000)")
    pg.click("#rememberBackBtn"); pg.wait_for_timeout(300)
    check("Positionen merken asks after a minute", pg.is_visible("#confirmSheet"))
    pg.click("#confirmYesBtn"); pg.wait_for_timeout(400)
    check("Positionen merken ended after Ja", pg.is_hidden("#rememberPlayer"))

    check("no page errors / native dialogs", not errors)
    b.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
