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

        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(200)

        # deselect the only initially-selected color -> should reach 0, not block
        active_swatch = pg.locator("#colorPicker .color-swatch.active[data-color]")
        await active_swatch.first.click(); await pg.wait_for_timeout(100)
        print("count at zero:", await pg.inner_text("#colorCount"))
        print("hint at zero:", await pg.inner_text("#colorHint"))
        print("hint has warn class:", "warn" in (await pg.get_attribute("#colorHint", "class") or ""))
        print("start button disabled:", await pg.is_disabled("#startBtn"))
        print("save-preset button disabled:", await pg.is_disabled("#vtSaveBtn"))
        await pg.screenshot(path=OUT + "arrow_colors_zero.png")

        # click start while disabled - nothing should happen (still on ready screen)
        await pg.click("#startBtn", force=True); await pg.wait_for_timeout(200)
        print("still on ready screen (native disabled blocks click):", await pg.is_visible("#ready"))

        # pick one color again -> hint/back button should recover
        await pg.locator("#colorPicker .color-swatch[data-color]").nth(0).click(); await pg.wait_for_timeout(100)
        print("count after picking one:", await pg.inner_text("#colorCount"))
        print("hint back to normal:", await pg.inner_text("#colorHint"))
        print("start enabled again:", not await pg.is_disabled("#startBtn"))

        # select all 7 via the Alle button itself, then click it again -> should go to zero
        await pg.click("#colorPicker .color-swatch:not([data-color])"); await pg.wait_for_timeout(100)
        print("count before toggle-off (should be 7):", await pg.inner_text("#colorCount"))
        await pg.click("#colorPicker .color-swatch:not([data-color])"); await pg.wait_for_timeout(100)
        print("count after re-clicking Alle while all selected:", await pg.inner_text("#colorCount"))
        print("hint after Alle toggle-off:", await pg.inner_text("#colorHint"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
