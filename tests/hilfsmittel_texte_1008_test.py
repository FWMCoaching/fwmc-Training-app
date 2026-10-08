"""Paket A kleine Punkte (Fabian 08.10.2026):
- Hilfsmittel-Hinweis on every Hütchen exercise (Kompass-Aufbau, Hütchen
  sortieren, Farbe + Zahl), same .hilfsmittel-note look as Farbfelder.
- Nichtraucher-Pause info text in Du-Form (no "wir"/"uns").
- Datenschutz sheet: Kürzel sentence for the trainer's server storage.
- Trainer-Dashboard catalog: area Aktivierung (+ Optodrum), overview lists
  Farbe + Zahl, Farbfelder, Optodrum, Jedes Auge zählt.
Run from tests/ with a dev server on :8845."""
import asyncio, os, re
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');"
SHOTS = "screenshots/hilfsmittel_texte"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        await ctx.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, content_type="application/json", body="{}"))
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await pg.goto(BASE + "index.html?bereich=visual"); await pg.wait_for_timeout(400)

        expect = {"cone-compass": ["Hütchen oder Becher", "eingestellten Farben", "Klebeband"],
                  "cone-tap": ["vier Hütchen oder Becher", "Rot, Gelb, Grün und Blau"],
                  "cone-number": ["nummerierte Felder"],
                  "farbfelder": ["Farbmatte"]}
        boxes = {}
        for ex, words in expect.items():
            await pg.click(f'.excard[data-exercise="{ex}"]'); await pg.wait_for_timeout(250)
            vis = await pg.is_visible("#hilfsmittelNote")
            txt = await pg.inner_text("#hilfsmittelNote") if vis else ""
            check(f"{ex}: Hilfsmittel note shown with its text", vis and all(w in txt for w in words) and txt.upper().startswith("HILFSMITTEL"), txt)
            check(f"{ex}: no empty shop link", not await pg.is_visible("#hilfsmittelLink"))
            boxes[ex] = await pg.evaluate("() => { const s = getComputedStyle(document.getElementById('hilfsmittelNote')); return [s.borderRadius, s.backgroundColor, s.fontSize]; }")
            if ex in ("cone-compass", "cone-tap"):
                for scheme in ("light", "dark"):
                    await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
                    await pg.locator("#hilfsmittelNote").scroll_into_view_if_needed()
                    await pg.screenshot(path=f"{SHOTS}/{ex}_{scheme}.png")
                await pg.emulate_media(color_scheme="light")
            await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        check("same look on every exercise", len({tuple(v) for v in boxes.values()}) == 1, boxes)
        # Another VT exercise has none
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        check("vt-color: no Hilfsmittel note", not await pg.is_visible("#hilfsmittelNote"))

        # ---- Nichtraucher-Pause info ----
        await pg.goto(BASE + "index.html?bereich=heute"); await pg.wait_for_timeout(400)
        await pg.click("#todayBreakInfoBtn"); await pg.wait_for_timeout(200)
        txt = await pg.inner_text("#breakInfoSheet")
        check("Nichtraucher info: Du-Form, no wir/uns", not re.search(r"\b(wir|uns|unser\w*)\b", txt, re.I) and "kannst du dir" in txt, txt)
        check("Nichtraucher info: meaning kept, no 'Gift'", "ohne Zigarette" in txt and "Auszeit" in txt and "Gift" not in txt)
        await pg.screenshot(path=f"{SHOTS}/nichtraucher_info.png")
        await pg.click("#breakInfoCloseBtn"); await pg.wait_for_timeout(200)

        # ---- Datenschutz ----
        await pg.evaluate("() => document.querySelector('.privacy-open-btn').click()"); await pg.wait_for_timeout(200)
        body = await pg.evaluate("() => document.getElementById('privacySheet').textContent")
        check("privacy: Kürzel sentence", "unter einem Kürzel" in body and "FWMC-Server" in body and "nie unter deinem Namen" in body)
        await pg.evaluate("() => { const d = [...document.querySelectorAll('#privacySheet details')].find(x => x.textContent.includes('Kürzel')); d.open = true; d.scrollIntoView(); }")
        await pg.wait_for_timeout(150)
        await pg.screenshot(path=f"{SHOTS}/datenschutz.png")

        # ---- Dashboard ----
        await pg.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await pg.goto(BASE + "dashboard.html"); await pg.wait_for_timeout(600)
        opts = await pg.evaluate("() => [...document.querySelectorAll('#enArea option')].map(o => o.value)")
        check("dashboard: area Aktivierung offered", "activation" in opts, opts)
        ov = await pg.evaluate("() => document.getElementById('overviewBody') ? document.getElementById('overviewBody').textContent : ''")
        for w in ("Optodrum", "Farbfelder", "Hütchen · Farbe + Zahl", "Jedes Auge zählt", "Aktivierung"):
            check(f"dashboard overview lists {w}", w in ov)
        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
