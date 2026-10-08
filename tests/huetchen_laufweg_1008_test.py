"""Hütchen · Laufweg "Folge der Karte" (Fabian 08.10.2026): a cone grid
(2-4 x 2-4, colours per row) and a drawn path to walk; variants "Karte in der
Hand" and "Weg merken"; rounds or time. Checks the card + ready screen, the
path maker (never crosses a cone, loops, lengths), both variants, pause,
rounds end + history, presets, Kombi capture/edit/playback, Wochenplan
source, light/dark screenshots at 390 and 1024 px.
Run from tests/ with a dev server (FWMC_PORT, default 8845)."""
import asyncio, json, math, os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
URL = f"http://localhost:{PORT}/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/huetchen_laufweg"
CARD = '.excard[data-exercise="cone-path"]'
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def st(pg):
    return await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}')")

SAMPLE = """([rows, cols, length, seed]) => {
  const p = window.__lw.make(rows, cols, length, seed);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); const path = document.createElementNS(ns, 'path');
  path.setAttribute('d', p.d); svg.appendChild(path); document.body.appendChild(svg);
  const L = path.getTotalLength(); const pts = [];
  for (let i = 0; i <= 400; i++) { const q = path.getPointAtLength(L * i / 400); pts.push([q.x, q.y]); }
  svg.remove();
  let minD = 9;
  pts.forEach(([x, y]) => p.cones.forEach((k) => { minD = Math.min(minD, Math.hypot(k.c - x, k.r - y)); }));
  return { L, minD, targets: p.targets, start: p.start, end: p.end, n: p.cones.length };
}"""


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- card + ready screen ----
        order = await pg.evaluate("() => [...document.querySelectorAll('#home .excard')].map(e => e.dataset.exercise)")
        check("card on the VT home right after Farbe + Zahl", order.index("cone-path") == order.index("cone-number") + 1, str(order))
        await pg.click(CARD); await pg.wait_for_timeout(250)
        check("ready screen opens", (await pg.inner_text("#readyTitle")).strip() == "Hütchen · Laufweg")
        check("Hilfsmittel note", await pg.is_visible("#hilfsmittelNote") and "Du brauchst Hütchen in den eingestellten Farben." in await pg.inner_text("#hilfsmittelNote"))
        hidden = await pg.evaluate("() => ['tempoGroup','advanced','addonGroup','durationGroup','colorGroup','bgGroup'].filter(id => { const e = document.getElementById(id); return e && !e.hidden && e.offsetParent; })")
        check("no tempo/background/add-on/shared duration groups", hidden == [], str(hidden))
        check("own settings visible", await pg.is_visible("#lwSettings"))
        check("defaults: Karte in der Hand, 3x3, Mittel, 5 Wege",
              all(["active" in await pg.get_attribute(sel, "class") for sel in ['[data-lw-variant="karte"]', '[data-lw-rows="3"]', '[data-lw-cols="3"]', '[data-lw-length="mittel"]', '[data-lw-end="runden"]']])
              and (await pg.inner_text("#lwRoundsValue")).strip() == "5 Wege")
        fills = await pg.evaluate("() => [...document.querySelectorAll('#lwPreview .lw-cone > path:nth-of-type(1)')].map(e => e.getAttribute('fill'))")
        check("preview: 9 cones, back row yellow, middle blue, front red", fills == ["#f2a900"] * 3 + ["#1565c0"] * 3 + ["#d32f2f"] * 3, str(fills))
        await pg.click("#lwAdvanced summary"); await pg.wait_for_timeout(100)
        check("Feineinstellungen: one colour line per row", await pg.locator("#lwRowColors .lw-row-colors").count() == 3)
        sw = await pg.evaluate("() => { const r = document.querySelector('.lw-swatch').getBoundingClientRect(); return [r.width, r.height]; }")
        check("row colour buttons >= 44 px", min(sw) >= 44, str(sw))
        await pg.screenshot(path=f"{SHOTS}/ready_390_light.png", full_page=True)
        await pg.click('[data-lw-rows="4"]'); await pg.wait_for_timeout(80)
        check("4 rows: 4 colour lines, 4th defaults to green", await pg.locator("#lwRowColors .lw-row-colors").count() == 4 and (await st(pg))["lwRowColors"][3] == "gruen")
        await pg.click('[data-lw-row="0"][data-lw-color="orange"]'); await pg.wait_for_timeout(80)
        await pg.click('[data-lw-cols="2"]'); await pg.wait_for_timeout(80)
        await pg.reload(); await pg.wait_for_timeout(400)
        s = await st(pg)
        check("settings persist", s["lwRows"] == 4 and s["lwCols"] == 2 and s["lwRowColors"][0] == "orange", json.dumps({k: s[k] for k in s if k.startswith("lw")}))
        await pg.click(CARD); await pg.wait_for_timeout(250)
        check("preview follows: 8 cones", await pg.locator("#lwPreview .lw-cone").count() == 8)
        await pg.click('[data-lw-rows="3"]'); await pg.click('[data-lw-cols="3"]')
        await pg.click("#lwAdvanced summary"); await pg.click('[data-lw-row="0"][data-lw-color="gelb"]'); await pg.wait_for_timeout(80)

        # ---- path maker ----
        worst, lens, loops, ends_ok, n_ok = 9, {"kurz": [], "mittel": [], "lang": []}, set(), True, True
        for rows in (2, 3, 4):
            for cols in (2, 3, 4):
                for length in ("kurz", "mittel", "lang"):
                    for seed in (3, 11, 29, 47):
                        r = await pg.evaluate(SAMPLE, [rows, cols, length, seed])
                        worst = min(worst, r["minD"])
                        lens[length].append(r["L"])
                        loops |= {t["loop"] for t in r["targets"]}
                        n_ok &= len(r["targets"]) == {"kurz": 3, "mittel": 5, "lang": 7}[length] and r["n"] == rows * cols
                        ends_ok &= r["start"]["y"] > rows - 1 and (r["end"]["x"] < -0.5 or r["end"]["x"] > cols - 0.5 or r["end"]["y"] < -0.5)
        check("path never crosses a cone icon (min distance >= 0.25, icon half-width 0.19)", worst >= 0.25, f"{worst:.3f}")
        check("3 / 5 / 7 cones per path", n_ok)
        check("full loops and wraps both occur", loops == {"full", "half"}, str(loops))
        avg = {k: sum(v) / len(v) for k, v in lens.items()}
        check("Kurz < Mittel < Lang", avg["kurz"] < avg["mittel"] < avg["lang"], str({k: round(v, 1) for k, v in avg.items()}))
        check("start below the front row, arrow ends outside the field", ends_ok)
        same = await pg.evaluate("() => { const a = window.__lw.make(3,3,'mittel',5).d, b = window.__lw.make(3,3,'mittel',6).d; return a === b; }")
        check("different seeds give different paths", not same)

        # ---- Karte in der Hand, 2 Wege ----
        await pg.fill("#lwRoundsSlider", "2"); await pg.dispatch_event("#lwRoundsSlider", "input"); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("player shows the map with the path", await pg.is_visible("#lwStage") and await pg.locator("#lwMap [data-lw-path]").count() == 1)
        check("caption: Weg 1 von 2", (await pg.inner_text("#lwCaption")).strip() == "Weg 1 von 2")
        check("pause button follows the player convention", await pg.is_visible("#lwPauseBtn") and (await pg.inner_text("#lwPauseBtn")).strip() == "Pause")
        bar = await pg.evaluate("() => document.getElementById('playerBar').getBoundingClientRect().bottom")
        cap = await pg.evaluate("() => document.getElementById('lwCaption').getBoundingClientRect().top")
        check("caption below the player bar", cap >= bar, f"{cap} vs {bar}")
        nb = await pg.evaluate("() => { const r = document.getElementById('lwNextBtn').getBoundingClientRect(); return [r.height, r.bottom, innerHeight]; }")
        check("Nächster Weg >= 44 px and on screen", nb[0] >= 44 and nb[1] <= nb[2], str(nb))
        await pg.screenshot(path=f"{SHOTS}/run_karte_390_light.png")
        d1 = (await pg.evaluate("() => window.__lw.run()"))["d"]
        await pg.click("#lwPauseBtn"); await pg.wait_for_timeout(150)
        t1 = await pg.inner_text("#timeEl"); await pg.wait_for_timeout(1300); t2 = await pg.inner_text("#timeEl")
        check("pause: sheet open, clock stands", await pg.is_visible("#lwPauseOverlay") and t1 == t2, f"{t1} {t2}")
        await pg.click("#lwResumeBtn"); await pg.wait_for_timeout(150)
        await pg.click("#lwNextBtn"); await pg.wait_for_timeout(150)
        r = await pg.evaluate("() => window.__lw.run()")
        check("Nächster Weg: round 2, new path", r["round"] == 2 and r["d"] != d1)
        check("last round button reads Fertig", (await pg.inner_text("#lwNextBtn")).strip() == "Fertig")
        await pg.click("#lwNextBtn"); await pg.wait_for_timeout(300)
        summ = await pg.inner_text("#doneSummary")
        check("done summary: 2 Wege", summ.startswith("2 Wege"), summ)
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")
        notes = [h.get("note") or "" for h in hist] if isinstance(hist, list) else []
        check("history note names variant, size, length", any("Karte in der Hand · 3×3 Hütchen · Mittel · 2 Wege" in n for n in notes), str(notes[:3]))
        check("player stage gone after the end", not await pg.is_visible("#lwStage"))
        await pg.click("#doneBackBtn"); await pg.wait_for_timeout(250)

        # ---- Weg merken ----
        await pg.click(CARD); await pg.wait_for_timeout(250)
        await pg.click('[data-lw-variant="merken"]'); await pg.wait_for_timeout(60)
        check("Merkzeit slider shown for Weg merken", await pg.is_visible("#lwShowGroup"))
        await pg.fill("#lwShowSlider", "3"); await pg.dispatch_event("#lwShowSlider", "input"); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("() => window.__lw.run()")
        check("merken: path shown first, no Nächster Weg yet", r["phase"] == "show" and await pg.locator("#lwMap [data-lw-path]").count() == 1 and not await pg.is_visible("#lwNextBtn"))
        check("merken: countdown in the caption", "merk dir den Weg · noch" in await pg.inner_text("#lwCaption"))
        await pg.screenshot(path=f"{SHOTS}/run_merken_show_390_light.png")
        await pg.wait_for_timeout(3300)
        r = await pg.evaluate("() => window.__lw.run()")
        check("merken: path hidden after the time", r["phase"] == "walk" and await pg.locator("#lwMap [data-lw-path]").count() == 0 and await pg.locator("#lwMap .lw-cone").count() == 9)
        check("merken: Weg zeigen + Nächster Weg", await pg.is_visible("#lwRevealBtn") and await pg.is_visible("#lwNextBtn"))
        await pg.screenshot(path=f"{SHOTS}/run_merken_walk_390_light.png")
        await pg.click("#lwRevealBtn"); await pg.wait_for_timeout(100)
        check("Weg zeigen brings the path back", await pg.locator("#lwMap [data-lw-path]").count() == 1 and (await pg.inner_text("#lwRevealBtn")).strip() == "Weg ausblenden")
        await pg.click("#lwNextBtn"); await pg.wait_for_timeout(100)
        check("next path starts with the memorising phase again", (await pg.evaluate("() => window.__lw.run()"))["phase"] == "show")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        check("Beenden: back to the ready screen, stage gone", await pg.is_visible("#ready") and not await pg.is_visible("#lwStage"))

        # ---- Dauer ----
        await pg.click('[data-lw-end="dauer"]'); await pg.click('[data-lw-dur="120"]'); await pg.wait_for_timeout(60)
        check("Dauer choices shown, rounds slider hidden", await pg.is_visible("#lwDurRow") and not await pg.is_visible("#lwRoundsLine"))
        await pg.click('[data-lw-variant="karte"]')
        await pg.click("#startBtn"); await pg.wait_for_timeout(1200)
        t = (await pg.inner_text("#timeEl")).strip()
        check("Dauer: clock counts down from 2:00", t in ("1:59", "1:58", "2:00"), t)
        check("Dauer: caption without 'von'", (await pg.inner_text("#lwCaption")).strip() == "Weg 1")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # ---- preset ----
        await pg.click("#vtSaveBtn"); await pg.fill("#vtSaveNameInput", "Lauf 2 Min"); await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(150)
        vt = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1') || '[]')")
        check("preset stores the Laufweg settings", vt and vt[-1].get("lw", {}).get("lwEnd") == "dauer" and vt[-1]["lw"]["lwDurS"] == 120, json.dumps(vt[-1] if vt else None))
        check("preset meta names variant and size", "Karte in der Hand · 3×3" in await pg.inner_text("#vtSavedList"))
        await pg.click('[data-lw-end="runden"]'); await pg.click('[data-lw-length="kurz"]'); await pg.wait_for_timeout(60)
        await pg.click('#vtSavedList .bundle-item:has-text("Lauf 2 Min")'); await pg.wait_for_timeout(400)
        s = await st(pg)
        check("preset tap restores + starts", s["lwEnd"] == "dauer" and s["lwLength"] == "mittel" and await pg.is_visible("#lwStage"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        await pg.click('[data-lw-end="runden"]'); await pg.wait_for_timeout(60)

        # ---- Kombi capture/edit/playback ----
        before = {k: v for k, v in (await st(pg)).items() if k.startswith("lw")}
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Laufweg")'); await pg.wait_for_timeout(250)
        check("Kombi: capture opens the ready screen", "Baustein: Hütchen · Laufweg" in await pg.inner_text("#readyTitle") and (await pg.inner_text("#startBtn")).strip() == "Baustein übernehmen")
        await pg.click('[data-lw-variant="merken"]'); await pg.click('[data-lw-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("Kombi: block added", await pg.is_visible("#comboScreen") and "Laufweg" in await pg.inner_text("#comboBlockList"))
        after = {k: v for k, v in (await st(pg)).items() if k.startswith("lw")}
        check("Kombi: standalone settings unchanged", after == before, f"{after} vs {before}")
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-editable with its own settings", "active" in await pg.get_attribute('[data-lw-variant="merken"]', "class") and "active" in await pg.get_attribute('[data-lw-length="lang"]', "class"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("() => window.__lw.run()")
        check("Kombi: block plays the Laufweg with its settings", await pg.is_visible("#lwStage") and r and r["cfg"]["lwVariant"] == "merken" and r["cfg"]["lwLength"] == "lang", json.dumps(r)[:200] if r else "none")
        await pg.screenshot(path=f"{SHOTS}/kombi_run_390_light.png")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        after2 = {k: v for k, v in (await st(pg)).items() if k.startswith("lw")}
        check("Kombi run leaves standalone settings alone", after2 == before)
        check("stage hidden after leaving the Kombi", not await pg.is_visible("#lwStage"))

        # ---- Wochenplan source ----
        opts = await pg.evaluate("() => [...document.querySelectorAll('#home .excard[data-exercise]')].map(c => c.dataset.exercise)")
        check("Wochenplan source lists it", "cone-path" in opts)
        dash = open("../dashboard.html", encoding="utf-8").read()
        check("dashboard catalogue lists it", '["cone-path", "Hütchen · Laufweg"]' in dash)
        await ctx.close()

        # ---- screenshots: dark + 1024 ----
        for w, h, dark in ((390, 844, True), (1024, 768, False), (1024, 768, True)):
            c2 = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme="dark" if dark else "light")
            await c2.add_init_script(INIT)
            p2 = await c2.new_page()
            p2.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            await p2.goto(URL); await p2.wait_for_timeout(400)
            await p2.click(CARD); await p2.wait_for_timeout(250)
            tag = f"{w}_{'dark' if dark else 'light'}"
            await p2.screenshot(path=f"{SHOTS}/ready_{tag}.png")
            await p2.click("#startBtn"); await p2.wait_for_timeout(300)
            box = await p2.evaluate("() => { const r = document.querySelector('#lwMap svg').getBoundingClientRect(); return [r.width, r.height]; }")
            check(f"map fills the stage at {tag}", box[0] > w * 0.5 and box[1] > 200, str(box))
            await p2.screenshot(path=f"{SHOTS}/run_{tag}.png")
            await c2.close()
        await b.close()
    print("ERRORS:", errors)
    print(f"{sum(results)}/{len(results)} checks passed")
    if errors or not all(results):
        raise SystemExit(1)

asyncio.run(main())
