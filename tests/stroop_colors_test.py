import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('[data-exercise="stroop-classic"]'); await pg.wait_for_timeout(150)
        print("colorGroup visible for stroop:", await pg.is_visible("#colorGroup"))
        swatch_count = await pg.locator("#colorPicker .color-swatch").count()
        print("swatch count (9 colours + Alle = 10):", swatch_count)
        print("initial selected count (default 5):", await pg.inner_text("#colorCount"))
        print("hint (should say 2 bis 9):", await pg.inner_text("#colorHint"))

        # deselect down past the old VT-style floor, all the way toward zero
        for _ in range(5):
            active = pg.locator("#colorPicker .color-swatch.active[data-color]")
            if await active.count() == 0:
                break
            await active.first.click(); await pg.wait_for_timeout(80)
        print("count after deselecting all individually:", await pg.inner_text("#colorCount"))
        print("hint at zero:", await pg.inner_text("#colorHint"))
        print("hint has warn class:", "warn" in (await pg.get_attribute("#colorHint", "class") or ""))
        print("start button disabled at zero:", await pg.is_disabled("#startBtn"))

        # pick Schwarz and Weiß specifically (only 2 colours - the minimum)
        await pg.click('#colorPicker .color-swatch[data-color="schwarz"]'); await pg.wait_for_timeout(80)
        await pg.click('#colorPicker .color-swatch[data-color="weiss"]'); await pg.wait_for_timeout(80)
        print("count after picking schwarz+weiss:", await pg.inner_text("#colorCount"))
        print("start button enabled again:", not await pg.is_disabled("#startBtn"))

        # the Weiß swatch's checkmark should not be an invisible white-on-white
        weiss_stroke = await pg.eval_on_selector('#colorPicker .color-swatch[data-color="weiss"] svg path', "el => el.getAttribute('stroke')")
        print("Weiß checkmark stroke colour (should be dark, not #fff):", weiss_stroke)

        # "Alle Farben" should now cover all 9, wedges should include black/white
        await pg.click('#colorPicker .color-swatch:not([data-color])'); await pg.wait_for_timeout(100)
        print("count after Alle Farben (should be 9):", await pg.inner_text("#colorCount"))
        wedge_bg = await pg.eval_on_selector('#colorPicker .color-swatch:not([data-color]) .swatch', "el => getComputedStyle(el).backgroundImage")
        print("Alle-Farben pie includes black:", "rgb(0, 0, 0)" in wedge_bg)
        print("Alle-Farben pie includes white:", "rgb(255, 255, 255)" in wedge_bg)

        # start with schwarz+weiss only (min case for stroop-bg's 3-way-distinct
        # fallback) and confirm it runs without crashing / rendering errors
        for _ in range(9):
            active = pg.locator("#colorPicker .color-swatch.active[data-color]")
            n = await active.count()
            if n <= 2:
                break
            await active.first.click(); await pg.wait_for_timeout(60)
        keys = await pg.eval_on_selector_all('#colorPicker .color-swatch.active[data-color]', "els => els.map(e => e.dataset.color)")
        print("final 2 colours before starting:", keys)
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        print("player visible after start:", await pg.is_visible("#player"))
        await pg.screenshot(path=OUT + "stroop_colors_running.png")

        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)

        # stroop-bg variant with the same 2-colour minimum (exercises the
        # bg-pick fallback when there's no 3rd colour to keep bg distinct)
        await pg.click('[data-exercise="stroop-bg"]'); await pg.wait_for_timeout(150)
        print("stroop-bg swatch count:", await pg.locator("#colorPicker .color-swatch").count())
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        print("player visible for stroop-bg:", await pg.is_visible("#player"))
        await pg.screenshot(path=OUT + "stroop_bg_running.png")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
