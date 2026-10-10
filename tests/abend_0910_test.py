"""Abendrunde 09.10.2026: Gleichgewicht Seite (Fuß vorne / Bein in der Luft), Tagesform-Zeilen mit Datum,
Mehr: "Mehr mit deinem Trainer"."""
import json, os
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/abend_0910"
ok = True
def check(name, cond, extra=""):
    global ok
    print(f"{name}: {bool(cond)} {extra}")
    ok = ok and bool(cond)

os.makedirs(SHOTS, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
        ctx.add_init_script("""localStorage.setItem('fwmc-tips-seen','true'); localStorage.setItem('fwmc-onboarding-v1','1');
          localStorage.setItem('fwmc-test-bottomnav','1'); localStorage.setItem('fwmc-test-natmodes','true'); localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));""")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        # --- Gleichgewicht Seite ---
        pg.goto(URL + "?bereich=nat"); pg.wait_for_timeout(300)
        pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); pg.wait_for_timeout(300)
        check(f"{scheme}: Gleichgewicht offen", pg.is_visible("#balanceReady"))
        pg.evaluate("document.getElementById('balanceStanceRow').closest('details')?.setAttribute('open','')")
        pg.click('#balanceStanceRow [data-bal-stance=normal]')
        check(f"{scheme}: Seite bei Normal verborgen", not pg.is_visible("#balanceSideBox"))
        pg.click('#balanceStanceRow [data-bal-stance=tandem]')
        check(f"{scheme}: Tandem fragt Fuß vorne", pg.is_visible("#balanceSideBox") and "Fuß ist vorne" in pg.inner_text("#balanceSideLabel"))
        pg.click('#balanceSideRow [data-bal-side=rechts]')
        pr = pg.evaluate("JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1') || 'null') || {}")
        keyname = [k for k in pg.evaluate("Object.keys(localStorage)") if "balance" in k]
        saved = any(json.loads(pg.evaluate(f"localStorage.getItem('{k}')") or "{}").get("stanceSide") == "rechts" for k in keyname)
        check(f"{scheme}: Seite gespeichert", saved, keyname)
        pg.click('#balanceStanceRow [data-bal-stance=einbein]')
        check(f"{scheme}: Einbein fragt Bein in der Luft", "Bein ist in der Luft" in pg.inner_text("#balanceSideLabel"))
        pg.locator("#balanceSideBox").scroll_into_view_if_needed()
        pg.screenshot(path=f"{SHOTS}/seite_{scheme}.png")
        lab = pg.evaluate("window.__balLabel ? 0 : 0")
        # Start und Stand-Hinweis lesen
        pg.click("#balanceReadyStartBtn"); pg.wait_for_timeout(700)
        hint = pg.evaluate("document.querySelector('.balance-stance')?.textContent || ''")
        check(f"{scheme}: Hinweis nennt rechtes Bein in der Luft", "rechtes Bein in der Luft" in hint, hint)
        pg.evaluate("document.getElementById('balanceBackBtn')?.click()"); pg.wait_for_timeout(300)
        # --- Tagesform ---
        pg.evaluate("""() => { const d = new Date(); const s = (x) => x.getFullYear() + '-' + String(x.getMonth()+1).padStart(2,'0') + '-' + String(x.getDate()).padStart(2,'0');
          const m = {}; for (let i = 0; i < 5; i++) { const x = new Date(d); x.setDate(d.getDate() - i); m[s(x)] = { v: 1 + (i % 3) }; }
          localStorage.setItem('fwmc-mood-v1', JSON.stringify(m)); }""")
        pg.goto(URL + "?bereich=fortschritt"); pg.wait_for_timeout(400)
        labels = pg.locator("#progressMood .mood-row-label").all_inner_texts()
        check(f"{scheme}: 4 Zeilen mit Datum, letzte 'jetzt'", len(labels) == 4 and labels[-1] == "jetzt" and labels[0].endswith("."), labels)
        leg = pg.inner_text("#progressMood .mood-legend")
        check(f"{scheme}: Legende 'mit Training', nicht 'trainiert'", "mit Training" in leg and "trainiert" not in leg, leg)
        w = pg.evaluate("document.querySelector('#progressMood .mood-grid').scrollWidth <= document.querySelector('#progressMood').clientWidth + 1")
        check(f"{scheme}: Raster passt in die Breite", w)
        pg.locator("#progressMood").scroll_into_view_if_needed()
        pg.screenshot(path=f"{SHOTS}/tagesform_{scheme}.png")
        # --- Mehr ---
        pg.goto(URL + "?bereich=mehr"); pg.wait_for_timeout(300)
        if not pg.is_visible("#moreScreen"):
            pg.evaluate("document.querySelector('#bottomNav [data-tab=more], #bottomNav button:last-child')?.click()"); pg.wait_for_timeout(300)
        check(f"{scheme}: Mehr-Karte sichtbar", pg.is_visible("#moreTrainerExtrasBtn"))
        pg.click("#moreTrainerExtrasBtn"); pg.wait_for_timeout(200)
        check(f"{scheme}: Fenster erklärt Möglichkeiten", pg.is_visible("#confirmSheet") and "persönlichen Trainingsplan" in pg.inner_text("#confirmText") and pg.inner_text("#confirmYesBtn") == "Trainer anfragen")
        pg.screenshot(path=f"{SHOTS}/mehr_{scheme}.png")
        pg.click("#confirmNoBtn"); pg.wait_for_timeout(150)
        check(f"{scheme}: Schließen schließt", not pg.is_visible("#confirmSheet"))
        check(f"{scheme}: keine Fehler", not errs, errs[:3])
        ctx.close()
    b.close()
print("ALL OK" if ok else "FAILED")
