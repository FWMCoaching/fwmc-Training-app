import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 900}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # Open "8 Pfeile" (8-solo) - should now show the color group
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(200)
        print("colorGroup visible for 8-solo:", await pg.is_visible("#colorGroup"))
        swatch_count = await pg.locator("#colorPicker .color-swatch").count()
        print("swatch count (7 colors + Alle):", swatch_count)
        print("hint text (should say 1 bis 7):", await pg.inner_text("#colorHint"))
        print("initial selected count:", await pg.inner_text("#colorCount"))

        # single color should be deselectable-blocked (min 1): try deselecting the only selected one
        active_swatch = pg.locator("#colorPicker .color-swatch.active[data-color]")
        print("initially exactly 1 active:", await active_swatch.count())
        await active_swatch.first.click(); await pg.wait_for_timeout(150)
        print("hint after trying to deselect last color:", await pg.inner_text("#colorHint"))
        print("still 1 selected:", await pg.inner_text("#colorCount"))

        # select a second and third color
        swatches = pg.locator("#colorPicker .color-swatch[data-color]")
        await swatches.nth(1).click(); await pg.wait_for_timeout(80)
        await swatches.nth(2).click(); await pg.wait_for_timeout(80)
        print("count after selecting 2 more:", await pg.inner_text("#colorCount"))
        print("'Alle' active with only 3 selected:", "active" in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))

        # click "Alle Farben"
        await pg.click("#colorPicker .color-swatch:not([data-color])"); await pg.wait_for_timeout(150)
        print("count after clicking Alle:", await pg.inner_text("#colorCount"))
        print("'Alle' now active:", "active" in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))
        await pg.screenshot(path=OUT + "arrow_colors_all.png")

        # deselect one color -> "Alle" should un-mark itself
        await swatches.nth(0).click(); await pg.wait_for_timeout(150)
        print("count after deselecting one from all-7:", await pg.inner_text("#colorCount"))
        print("'Alle' no longer active:", "active" in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))

        # Verify VT (vt-color) still has its own 2-4 range, unaffected
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        print("VT hint (should say 2 bis 4):", await pg.inner_text("#colorHint"))
        print("VT swatch count (7 colors, no Alle):", await pg.locator("#colorPicker .color-swatch").count())
        print("Alle button hidden for VT:", await pg.is_hidden("#colorPicker .color-swatch:not([data-color])"))

        # Actually run 8-solo briefly to confirm no crash and arrow colors get used
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(600)
        print("player visible after starting 8-solo:", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
