import asyncio
from playwright.async_api import async_playwright
OUT = "screenshots/mv2_"
URL = "http://localhost:8845/index.html?bereich=visual"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click("[data-mv-layout=band]")  # these checks cover the strip (Band); Zeilen/Feld: reaktion_anzeige_1007_test.py
        print("no sound row present:", await pg.locator("#movementSoundRow").count() == 0)
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(150)
        await pg.screenshot(path=OUT + "01_ready_full.png", full_page=True)

        # exact BPM slider
        await pg.fill("#movementBpmSlider", "95")
        await pg.eval_on_selector("#movementBpmSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("bpm value text:", await pg.inner_text("#movementBpmValue"))
        print("preset active after custom bpm:", await pg.eval_on_selector_all("[data-mv-bpm].active", "els => els.length"))

        # pictogram close-ups from picker
        chip_html = await pg.eval_on_selector_all(".movement-chip", "els => els.map(e => ({svg: e.querySelector('svg').outerHTML, label: e.querySelector('span').textContent}))")
        await pg.set_viewport_size({"width": 900, "height": 300})
        await pg.evaluate("""(items) => {
          document.body.innerHTML = ''; document.body.style.cssText = 'background:#fff;margin:0';
          const wrap = document.createElement('div'); wrap.style.cssText = 'display:flex;gap:14px;padding:20px';
          items.forEach(({svg, label}) => {
            const box = document.createElement('div'); box.style.cssText = 'display:flex;flex-direction:column;align-items:center;width:100px';
            box.innerHTML = svg + '<span style="font-size:10px;margin-top:4px;text-align:center">' + label + '</span>';
            box.querySelector('svg').style.cssText = 'width:70px;height:70px';
            wrap.appendChild(box);
          });
          document.body.appendChild(wrap);
        }""", chip_html)
        await pg.screenshot(path=OUT + "02_pictograms.png")
        await pg.set_viewport_size({"width": 390, "height": 844})

        # ---- Windowed lane mode (fast run) ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn")
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click("[data-mv-layout=band]")  # these checks cover the strip (Band); Zeilen/Feld: reaktion_anzeige_1007_test.py
        await pg.click('[data-mv-bpm="80"]')
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(100)
        await pg.evaluate("() => { document.querySelector('[data-mv-dur=\"1\"]').dataset.mvDur = '0.08'; }")
        await pg.click('[data-mv-dur="0.08"]')
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(200)
        print("lane class (windowed):", await pg.get_attribute("#movementLane", "class"))
        await pg.screenshot(path=OUT + "03_window_lane.png")
        await pg.wait_for_function("() => !document.getElementById('movementFinishBadge').hidden", timeout=6000)
        print("finish badge shown, lane still has tiles:", await pg.eval_on_selector_all(".movement-tile", "els => els.length") > 0)
        await pg.screenshot(path=OUT + "04_finish_badge.png")
        await pg.wait_for_function("() => !document.getElementById('movementDonePanel').hidden", timeout=4000)
        print("done summary:", await pg.inner_text("#movementDoneSummary"))
        await pg.click("#movementDoneBackBtn"); await pg.wait_for_timeout(150)

        # ---- Grid ("ganzes Programm") mode ----
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click("[data-mv-layout=band]")  # these checks cover the strip (Band); Zeilen/Feld: reaktion_anzeige_1007_test.py
        await pg.click('[data-mv-preview="all"]')
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(100)
        await pg.evaluate("() => { document.querySelector('[data-mv-dur=\"2\"]').dataset.mvDur = '0.1'; }")
        await pg.click('[data-mv-dur="0.1"]')
        await pg.click('[data-mv-bpm="80"]')
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(200)
        print("lane class (grid):", await pg.get_attribute("#movementLane", "class"))
        tile_count = await pg.eval_on_selector_all(".movement-lane.grid .movement-tile", "els => els.length")
        print("grid tile count:", tile_count)
        await pg.screenshot(path=OUT + "05_grid_start.png", full_page=True)
        await pg.wait_for_timeout(900)
        active_idx = await pg.evaluate("() => Array.from(document.querySelectorAll('.movement-tile')).findIndex(t => t.classList.contains('active'))")
        done_count = await pg.eval_on_selector_all(".movement-tile.done", "els => els.length")
        print("active idx after ~1 beat:", active_idx, "done count:", done_count)
        await pg.screenshot(path=OUT + "06_grid_progress.png", full_page=True)
        await pg.wait_for_function("() => !document.getElementById('movementFinishBadge').hidden", timeout=6000)
        await pg.screenshot(path=OUT + "07_grid_finish.png", full_page=True)
        await pg.wait_for_function("() => !document.getElementById('movementDonePanel').hidden", timeout=4000)
        print("grid mode done ok")
        await pg.click("#movementDoneBackBtn"); await pg.wait_for_timeout(150)

        # abort during finishing grace period should not crash
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click("[data-mv-layout=band]")  # these checks cover the strip (Band); Zeilen/Feld: reaktion_anzeige_1007_test.py
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(150)
        print("abort ok, back at ready:", await pg.is_visible("#movementReady"))

        # ---- Darstellung: "Figur" (real stick figure) vs "Abstrakt" (2x2
        # symbol grid) - replaced the old single four-spoke-hub pictogram,
        # which read as neither a clear figure nor a clean abstract symbol.
        # Both must render a genuinely different SVG shape, both in the
        # picker chips (live re-render on toggle) and in the lane during
        # play, and the choice must persist.
        print("still at movementReady after abort:", await pg.is_visible("#movementReady"))
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(100)
        # default is "Vier Felder" since 07.10. (Fabian took over the preview page); Figur stays selectable
        print("default style is Vier Felder:", "active" in (await pg.get_attribute('[data-mv-figure="felder"]', "class") or ""))
        await pg.click('[data-mv-figure="figur"]'); await pg.wait_for_timeout(100)
        figur_svg = await pg.eval_on_selector(".movement-chip svg", "el => el.outerHTML")
        print("Figur style has a head circle:", "circle" in figur_svg and 'r="10"' in figur_svg)

        await pg.click('[data-mv-figure="abstrakt"]'); await pg.wait_for_timeout(100)
        abstrakt_svg = await pg.eval_on_selector(".movement-chip svg", "el => el.outerHTML")
        print("Abstrakt style is a different shape (grid of circles):", abstrakt_svg != figur_svg and abstrakt_svg.count("<circle") >= 4)

        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        lane_svg = await pg.eval_on_selector(".movement-tile svg", "el => el.outerHTML")
        print("lane reflects Abstrakt style too:", lane_svg.count("<circle") >= 4 and "polygon" in lane_svg)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(150)

        await pg.reload(); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click("[data-mv-layout=band]")  # these checks cover the strip (Band); Zeilen/Feld: reaktion_anzeige_1007_test.py
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(100)
        print("Abstrakt choice persisted after reload:", "active" in (await pg.get_attribute('[data-mv-figure="abstrakt"]', "class") or ""))

        # ---- Laufrichtung: window mode now shows a couple of faded "done"
        # tiles behind the active one too (not just upcoming), and the whole
        # lane's flex-direction switches per client choice - "rechts" (row,
        # default), "links" (row-reverse), "oben"/"unten" (vertical column,
        # reversed or not) - so new tiles visibly enter from whichever edge
        # was picked instead of always from the right.
        print("default direction is rechts:", "active" in (await pg.get_attribute('[data-mv-direction="rechts"]', "class") or ""))
        await pg.click('[data-mv-preview="3"]'); await pg.wait_for_timeout(80)  # back out of "Ganz"/grid mode from the earlier test block
        for direction in ["rechts", "links", "oben", "unten"]:
            await pg.click(f'[data-mv-direction="{direction}"]'); await pg.wait_for_timeout(80)
            await pg.click("#movementStartBtn"); await pg.wait_for_timeout(1200)
            lane_class = await pg.get_attribute("#movementLane", "class")
            tiles = await pg.eval_on_selector_all(
                ".movement-tile",
                "els => els.map(e => ({done: e.classList.contains('done'), active: e.classList.contains('active'), next: e.classList.contains('next')}))"
            )
            has_done = any(t["done"] for t in tiles)
            has_active = sum(1 for t in tiles if t["active"]) == 1
            print(f"direction {direction}: lane class has dir-{direction}:", lane_class == f"movement-lane dir-{direction}",
                  "| a 'done' tile is shown behind active:", has_done, "| exactly one active tile:", has_active)
            await pg.click("#movementBackBtn"); await pg.wait_for_timeout(150)
            if not await pg.is_visible('[data-mv-direction="rechts"]'):
                await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(100)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
