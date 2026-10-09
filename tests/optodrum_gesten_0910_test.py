"""Optodrum: Wischen = Richtung, zwei Finger = Breite, "Speichern" in der Übung (Fabian 09.10.2026)."""
import os
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/optodrum_gesten"
ok = True
def check(name, cond, extra=""):
    global ok
    print(f"{name}: {bool(cond)} {extra}")
    ok = ok and bool(cond)

PINCH = """(f) => { const s = document.getElementById('optoStage'); const r = s.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const ev = (type, id, x, prim) => s.dispatchEvent(new PointerEvent(type, {pointerId: id, pointerType: 'touch', isPrimary: prim, clientX: x, clientY: cy, bubbles: true}));
  ev('pointerdown', 11, cx - 50, true); ev('pointerdown', 12, cx + 50, false);
  for (let k = 1; k <= 5; k++) { const d = 50 * (1 + (f - 1) * k / 5); ev('pointermove', 11, cx - d, true); ev('pointermove', 12, cx + d, false); }
  ev('pointerup', 12, cx + 50 * f, false); ev('pointerup', 11, cx - 50 * f, true); }"""

def prefs(pg):
    return pg.evaluate("JSON.parse(localStorage.getItem('fwmc-optodrum-prefs-v1') || '{}')")

os.makedirs(SHOTS, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
        ctx.add_init_script("""localStorage.setItem('fwmc-tips-seen','true'); localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));
          if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded','1');
            localStorage.setItem('fwmc-optodrum-prefs-v1', JSON.stringify({dir:'links', size:40, durationS:60}));
            localStorage.setItem('fwmc-test-optohint','1'); }""")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(URL + "?bereich=aktivierung"); pg.wait_for_timeout(300)
        pg.click("#optoOpenBtn"); pg.wait_for_timeout(200)
        check(f"{scheme}: Hilfe-Zeile auf der Übungsseite", "Wischen" in pg.inner_text("#optoGestureHelp"))
        pg.click("#optoStartBtn"); pg.wait_for_timeout(400)
        check(f"{scheme}: Gesten-Hinweis beim ersten Lauf", pg.is_visible(".opto-toast") and "Wischen" in pg.inner_text(".opto-toast"))
        pg.screenshot(path=f"{SHOTS}/hinweis_{scheme}.png")
        check(f"{scheme}: Speichern anfangs versteckt", not pg.is_visible("#optoLiveSaveBtn"))
        box = pg.locator("#optoStage").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        # Wischen nach rechts
        pg.mouse.move(cx - 80, cy); pg.mouse.down(); pg.mouse.move(cx + 80, cy, steps=5); pg.mouse.up()
        pg.wait_for_timeout(150)
        st = pg.evaluate("window.__opto()")
        check(f"{scheme}: Wischen rechts -> rechts", st["dir"] == "rechts", st["dir"])
        check(f"{scheme}: Toast zeigt Richtung", "nach rechts" in pg.inner_text(".opto-toast"))
        check(f"{scheme}: Speichern erscheint", pg.is_visible("#optoLiveSaveBtn"))
        check(f"{scheme}: noch nicht gespeichert", prefs(pg).get("dir") == "links")
        # schraeg nach rechts oben
        pg.mouse.move(cx - 60, cy + 60); pg.mouse.down(); pg.mouse.move(cx + 60, cy - 60, steps=5); pg.mouse.up(); pg.wait_for_timeout(100)
        check(f"{scheme}: Wischen schräg -> ro", pg.evaluate("window.__opto().dir") == "schraeg" and pg.evaluate("document.getElementById('optoStatusEl').textContent").startswith("↗"))
        # kurzer Tipp aendert nichts
        pg.mouse.click(cx, cy); pg.wait_for_timeout(100)
        check(f"{scheme}: Tipp ändert nichts", pg.evaluate("window.__opto().dir") == "schraeg")
        # Pinch -> breiter
        pg.evaluate(PINCH, 2.0); pg.wait_for_timeout(100)
        size = pg.evaluate("document.getElementById('optoStage') && window.__optoSize ? 0 : 0")
        pg.screenshot(path=f"{SHOTS}/nach_gesten_{scheme}.png")
        # Pause zeigt Live-Werte
        pg.click("#optoPauseBtn"); pg.wait_for_timeout(200)
        live = pg.evaluate("Number(document.querySelector('#optoPauseControls [data-opto-r=size]').value)")
        check(f"{scheme}: Pause zeigt Live-Breite (~80 px)", 70 <= live <= 90, live)
        check(f"{scheme}: Pause zeigt Live-Richtung", pg.locator('#optoPauseControls [data-opto-f=dir][data-opto-v=schraeg]').evaluate("b => b.classList.contains('active') || b.getAttribute('aria-pressed') === 'true'"))
        check(f"{scheme}: Speichern in der Pause verborgen", not pg.is_visible("#optoLiveSaveBtn"))
        pg.click("#optoResumeBtn"); pg.wait_for_timeout(150)
        check(f"{scheme}: Speichern nach Weiter wieder da", pg.is_visible("#optoLiveSaveBtn"))
        pg.screenshot(path=f"{SHOTS}/speichern_{scheme}.png")
        pg.click("#optoLiveSaveBtn"); pg.wait_for_timeout(150)
        pr = prefs(pg)
        check(f"{scheme}: gespeichert", pr.get("dir") == "schraeg" and pr.get("diag") == "ro" and 70 <= pr.get("size", 0) <= 90, pr)
        check(f"{scheme}: Knopf sagt Gespeichert", "Gespeichert" in pg.inner_text("#optoLiveSaveBtn"))
        pg.wait_for_timeout(1600)
        check(f"{scheme}: Knopf verschwindet danach", not pg.is_visible("#optoLiveSaveBtn"))
        # Taps auf Pause/Beenden bleiben normale Knoepfe
        pg.click("#optoBackBtn"); pg.wait_for_timeout(300)
        pg.reload(); pg.wait_for_timeout(300)
        pg.goto(URL + "?bereich=aktivierung"); pg.wait_for_timeout(300)
        pg.click("#optoOpenBtn"); pg.wait_for_timeout(200)
        check(f"{scheme}: Übungsseite zeigt gespeicherte Richtung", pg.locator('#optoReadyControls [data-opto-f=dir][data-opto-v=schraeg]').evaluate("b => b.classList.contains('active') || b.getAttribute('aria-pressed') === 'true'"))
        n = pg.evaluate("Number(localStorage.getItem('fwmc-opto-gesture-hint-v1'))")
        check(f"{scheme}: Hinweis-Zähler", n == 1, n)
        check(f"{scheme}: keine Fehler", not errs, errs[:3])
        ctx.close()
    b.close()
print("ALL OK" if ok else "FAILED")
