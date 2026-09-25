import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---------- Visual Training ----------
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        print("VT ready visible:", await pg.is_visible("#ready"))
        print("VT saved group hidden initially:", await pg.is_hidden("#vtSavedGroup"))
        await pg.click("#vtSaveBtn")
        await pg.fill("#vtSaveNameInput", "Test VT Preset")
        await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("VT saved group visible after save:", await pg.is_visible("#vtSavedGroup"))
        print("VT saved list text has name:", "Test VT Preset" in await pg.inner_text("#vtSavedList"))
        await pg.click("#vtSavedList .bundle-item"); await pg.wait_for_timeout(400)
        print("VT tap-to-reuse started player:", await pg.is_visible("#player"))
        if await pg.is_visible("#backBtn"):
            await pg.click("#backBtn"); await pg.wait_for_timeout(200)
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        print("VT preset persists after reload:", "Test VT Preset" in await pg.inner_text("#vtSavedList"))
        await pg.click("#vtSavedList .combo-block-remove"); await pg.wait_for_timeout(200)
        print("VT saved group hidden after delete:", await pg.is_hidden("#vtSavedGroup"))
        await pg.click("#backBtn" if await pg.is_visible("#backBtn") else "body")

        # ---------- Atemtraining ----------
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('[data-section="breath"]'); await pg.wait_for_timeout(200)
        print("breathHome visible:", await pg.is_visible("#breathHome"))
        await pg.click("#patternGrid .featured-card >> nth=0"); await pg.wait_for_timeout(200)
        print("breathReady visible:", await pg.is_visible("#breathReady"))
        print("breath saved group hidden initially:", await pg.is_hidden("#breathSavedGroup"))
        await pg.click("#breathSaveBtn")
        await pg.fill("#breathSaveNameInput", "Test Breath Preset")
        await pg.click("#breathSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("breath saved group visible after save:", await pg.is_visible("#breathSavedGroup"))
        print("breath saved list has name:", "Test Breath Preset" in await pg.inner_text("#breathSavedList"))
        await pg.click("#breathSavedList .bundle-item"); await pg.wait_for_timeout(400)
        print("breath tap-to-reuse started player:", await pg.is_visible("#breathPlayer"))
        if await pg.is_visible("#breathBackBtn"):
            await pg.click("#breathBackBtn"); await pg.wait_for_timeout(200)
        await pg.click("#breathSavedList .combo-block-remove"); await pg.wait_for_timeout(200)
        print("breath saved group hidden after delete:", await pg.is_hidden("#breathSavedGroup"))

        # ---------- Movement ----------
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('[data-section="movement"]'); await pg.wait_for_timeout(200)
        print("movementHome visible:", await pg.is_visible("#movementHome"))
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        print("movementReady visible:", await pg.is_visible("#movementReady"))
        print("movement saved group hidden initially:", await pg.is_hidden("#movementSavedGroup"))
        await pg.click("#movementSaveBtn")
        await pg.fill("#movementSaveNameInput", "Test Movement Preset")
        await pg.click("#movementSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("movement saved group visible after save:", await pg.is_visible("#movementSavedGroup"))
        print("movement saved list has name:", "Test Movement Preset" in await pg.inner_text("#movementSavedList"))
        await pg.click("#movementSavedList .bundle-item"); await pg.wait_for_timeout(400)
        print("movement tap-to-reuse started player:", await pg.is_visible("#movementPlayer"))
        if await pg.is_visible("#movementBackBtn"):
            await pg.click("#movementBackBtn"); await pg.wait_for_timeout(200)
        await pg.click("#movementSavedList .combo-block-remove"); await pg.wait_for_timeout(200)
        print("movement saved group hidden after delete:", await pg.is_hidden("#movementSavedGroup"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
