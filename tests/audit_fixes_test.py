# Covers the clear bugs fixed after the full app audit (2026-10-02):
# wake lock comes back after backgrounding, admin token never in a backup,
# full storage shows a warning, offline/broken training codes get their own
# message, Movement presets keep Laufrichtung/Darstellung, the stage hint
# moves below a wrapped player bar, sheets open scrolled to the top, the
# nav never breaks a word mid-way, NAT Kombi blocks keep their own settings.
import json
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(label, ok):
    results.append(ok)
    print(f"{label}: {ok}")


def new_page(b, w=390, h=844, init=""):
    pg = b.new_page(viewport={"width": w, "height": h})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');" + init)
    pg.goto(URL)
    pg.wait_for_timeout(300)
    return pg, errors


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    # 1. Wake lock: a released lock is requested again on return.
    mock = """
      window.__wl = 0;
      Object.defineProperty(navigator, 'wakeLock', { configurable: true, value: { request: async () => {
        window.__wl++;
        const t = new EventTarget(); t.release = async () => {}; window.__lastLock = t; return t; } } });
    """
    pg, errors = new_page(b, init=mock)
    pg.evaluate("document.querySelector('.excard[data-exercise]').click()")
    pg.wait_for_timeout(200)
    pg.click("#startBtn")
    pg.wait_for_timeout(500)
    first = pg.evaluate("window.__wl")
    pg.evaluate("window.__lastLock.dispatchEvent(new Event('release'))")
    pg.evaluate("""() => {
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    pg.wait_for_timeout(300)
    check("wake lock requested again after the browser released it", first >= 1 and pg.evaluate("window.__wl") == first + 1)
    check("no page errors (wake lock)", not errors)
    pg.close()

    # 2. Backup never contains the coach dashboard's admin token.
    pg, errors = new_page(b, init="localStorage.setItem('fwmc-admin-token','geheim');")
    pg.evaluate("document.querySelector('.master-settings-btn').click()")
    with pg.expect_download() as dl:
        pg.click("#masterBackupExportBtn")
    data = json.loads(open(dl.value.path()).read())["data"]
    check("backup export leaves out fwmc-admin-token", "fwmc-admin-token" not in data and len(data) > 0)
    pg.close()

    # 3. Full storage shows a visible warning instead of failing silently.
    pg, errors = new_page(b)
    pg.evaluate("""() => {
      const orig = Storage.prototype.setItem;
      Storage.prototype.setItem = function () { const e = new Error('full'); e.name = 'QuotaExceededError'; throw e; };
      document.querySelector('.master-settings-btn').click();
      document.querySelector('[data-master-cvd]').click();
      Storage.prototype.setItem = orig;
    }""")
    pg.wait_for_timeout(200)
    check("storage-full warning visible", pg.is_visible("#storageWarning"))
    pg.click("#storageWarning button")
    check("storage-full warning can be closed", pg.locator("#storageWarning").count() == 0)
    pg.close()

    # 4. Training codes: offline, broken config, unknown code.
    pg, errors = new_page(b)

    def try_code(code):
        pg.fill("#programCodeInput", code)
        pg.click("#programGoBtn")
        pg.wait_for_timeout(600)
        return pg.inner_text("#programError") if pg.is_visible("#programError") else ""

    pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.abort())
    t = try_code("offline-test")
    check("offline code lookup says 'Keine Verbindung'", "Keine Verbindung" in t)
    pg.unroute("**/online-training.fwmc.workers.dev/**")
    pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"name": "x", "blocks": [{"exercise": "gibt-es-nicht", "duration": 30}]})))
    t = try_code("kaputt-test")
    check("broken coach config shows a message, no crash", "nicht geöffnet" in t)
    pg.unroute("**/online-training.fwmc.workers.dev/**")
    pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    t = try_code("unbekannt-test")
    check("unknown code still says 'kein Training gefunden'", "kein Training gefunden" in t)
    check("still on the home screen", pg.is_visible("#home"))
    check("no page errors (codes)", not errors)
    pg.close()

    # 5. Movement presets keep Laufrichtung and Darstellung.
    pg, errors = new_page(b)
    pg.evaluate("document.querySelector('.section-tab[data-section=\"movement\"]').click()")
    pg.evaluate("document.getElementById('movementStartCard').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('[data-mv-direction=\"oben\"]').click(); document.querySelector('[data-mv-figure=\"abstrakt\"]').click()")
    pg.evaluate("document.getElementById('movementSaveBtn').click()")
    pg.fill("#movementSaveNameInput", "Oben")
    pg.click("#movementSaveConfirmBtn")
    saved = pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-saved-v1'))")
    check("movement preset stores direction + figure style", saved[-1].get("direction") == "oben" and saved[-1].get("figureStyle") == "abstrakt")
    pg.close()

    # 6. Stage hint sits below the (two-row) player bar on a phone.
    pg, errors = new_page(b, 375, 667)
    pg.evaluate("document.querySelector('.section-tab[data-section=\"nat\"]').click()")
    pg.evaluate("document.getElementById('motOpenSpeed').click()")
    pg.wait_for_timeout(200)
    pg.click("#motReadyStartBtn")
    pg.wait_for_timeout(700)
    bar = pg.evaluate("document.getElementById('motPlayerBar').getBoundingClientRect().bottom")
    hint = pg.evaluate("document.getElementById('motHint').getBoundingClientRect().top")
    check(f"MOT hint top {round(hint)} below bar bottom {round(bar)}", hint >= bar)
    check("no page errors (MOT)", not errors)
    pg.close()

    # 7. First-visit tips sheet opens at the top.
    pg = b.new_page(viewport={"width": 375, "height": 667})
    pg.goto(URL)
    pg.wait_for_timeout(500)
    st = pg.evaluate("Math.max(document.getElementById('tipsSheet').scrollTop, ...[...document.querySelectorAll('#tipsSheet .sheet-inner')].map(e => e.scrollTop))")
    check("tips sheet opens scrolled to the top", pg.is_visible("#tipsSheet") and st == 0)
    pg.close()

    # 8. Nav labels never break mid-word between phone and tablet widths.
    for unlocked in (False, True):
        for w in (481, 560, 600, 667, 700, 760):
            pg, _ = new_page(b, w, 800, "localStorage.setItem('fwmc-test-unlocked','true');" if unlocked else "")
            broken = pg.evaluate("""() => [...document.querySelectorAll('#home .section-tab:not([hidden])')].filter(t => {
              const r = document.createRange(); r.selectNodeContents(t);
              return r.getClientRects().length > t.textContent.trim().split(/\\s+/).length; }).map(t => t.textContent.trim())""")
            check(f"nav no mid-word break at {w}px (Test {'an' if unlocked else 'aus'})", broken == [])
            pg.close()

    # 9. A Remember Kombi block keeps its own settings, own prefs untouched.
    pg, errors = new_page(b)
    pg.evaluate("document.querySelector('.section-tab[data-section=\"nat\"]').click()")
    pg.evaluate("document.querySelector('#rememberReady [data-remember-diff=\"mittel\"]').click()")
    before = pg.evaluate("JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')).revealBaseS")
    pg.evaluate("document.querySelector('[data-open-combo]').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("[...document.querySelectorAll('#comboScreen .combo-add-btn')].find(b => b.textContent.includes('Positionen merken')).click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#rememberReady [data-remember-diff=\"schwer\"]').click()")
    pg.evaluate("document.getElementById('rememberReadyStartBtn').click()")
    pg.wait_for_timeout(200)
    after = pg.evaluate("JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')).revealBaseS")
    check("own Remember settings unchanged by capture", before == after)
    check("Kombi screen back after capture", pg.is_visible("#comboScreen"))
    check("no page errors (Kombi)", not errors)
    pg.close()

    # 10. A Kombi block's Movement settings don't stay in the client's own setup.
    pg, errors = new_page(b)
    pg.evaluate("document.querySelector('.section-tab[data-section=\"movement\"]').click()")
    pg.evaluate("document.getElementById('movementStartCard').click()")
    pg.wait_for_timeout(200)
    pg.click('[data-mv-bpm="40"]')
    pg.click("#movementBackToHome") if pg.is_visible("#movementBackToHome") else None
    pg.evaluate("document.querySelector('#movementHome .combo-entry-link').click()")
    pg.wait_for_timeout(200)
    pg.click('#comboAddGrid >> text="Ganzkörper-Reaktion"')
    pg.wait_for_timeout(200)
    pg.click('[data-mv-bpm="80"]')
    pg.click("#movementStartBtn")
    pg.wait_for_timeout(200)
    pg.click("#comboStartBtn")
    pg.wait_for_timeout(400)
    pg.click("#movementBackBtn")
    pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('movementStartCard').click()")
    pg.wait_for_timeout(200)
    active = pg.evaluate("document.querySelector('[data-mv-bpm].active')?.dataset.mvBpm")
    check(f"own Movement tempo back to 40 after a Kombi with 80 (shows {active})", active == "40")
    check("no page errors (Kombi restore)", not errors)
    pg.close()

    # 11. Workout: info sheet closes with Escape, Kraft card has its own heading,
    # Kraftplan player has no visible empty pill and centred reps text.
    pg, errors = new_page(b)
    pg.evaluate("document.querySelector('.section-tab[data-section=\"workout\"]').click()")
    head = pg.evaluate("document.getElementById('workoutRepsStartCard').closest('section').querySelector('h2').textContent")
    check(f"Kraft card under its own heading ({head})", head == "Krafttraining")
    pg.click("#workoutRepsStartCard")
    pg.wait_for_timeout(200)
    pg.locator("#workoutRepsExerciseGrid .combo-add-btn").first.click()
    pg.wait_for_timeout(150)
    check("info sheet open", pg.is_visible("#workoutExerciseInfoSheet"))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(150)
    check("Escape closes the exercise info sheet", not pg.is_visible("#workoutExerciseInfoSheet"))
    pg.locator("#workoutRepsExerciseGrid .ca-plus-btn").first.click()
    pg.click("#workoutRepsStartBtn")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#workoutRestSkipBtn').forEach(b => b.click())")
    pg.wait_for_timeout(300)
    pill = pg.evaluate("(() => { const e = document.getElementById('workoutTimeEl'); return [e.textContent, getComputedStyle(e).visibility]; })()")
    check(f"empty status pill not drawn ({pill})", pill[0] != "" or pill[1] == "hidden")
    big = pg.evaluate("(() => { const e = document.getElementById('workoutRepsBig'); const r = e.getBoundingClientRect(); return [getComputedStyle(e).textAlign, r.right, e.textContent]; })()")
    check(f"reps text centred and inside the screen ({big})", big[0] == "center" and big[1] <= 390)
    check("no page errors (Workout)", not errors)
    pg.close()

    # 12. Colour-vision help text names no hidden Test exercises.
    pg, errors = new_page(b)
    txt = pg.inner_text("#masterSettingsSheet", timeout=2000) if False else pg.evaluate("document.getElementById('masterSettingsSheet').textContent")
    check("colour-vision help without Test-Bereich names", "Wortfarben-Test" not in txt and "Suchtest" not in txt)
    pg.close()

    b.close()

print("ALL OK" if all(results) else "FAILURES")
sys.exit(0 if all(results) else 1)
