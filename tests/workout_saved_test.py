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

        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(200)
        print("workoutHome visible:", await pg.is_visible("#workoutHome"))
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        print("workoutTabataReady visible:", await pg.is_visible("#workoutTabataReady"))
        print("saved group hidden initially:", await pg.is_hidden("#workoutCircuitSavedGroup"))

        # Build a tiny 2-exercise circuit
        add_btns = pg.locator("#workoutCircuitAddGrid .combo-add-btn")
        await add_btns.nth(0).click(); await pg.wait_for_timeout(100)
        await add_btns.nth(1).click(); await pg.wait_for_timeout(100)
        print("circuit count text:", await pg.inner_text("#workoutCircuitCount"))
        print("start btn enabled:", not await pg.is_disabled("#workoutTabataStartBtn"))

        await pg.click("#workoutCircuitSaveBtn")
        await pg.fill("#workoutCircuitSaveNameInput", "Test Zirkel")
        await pg.click("#workoutCircuitSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("saved group visible after save:", await pg.is_visible("#workoutCircuitSavedGroup"))
        print("saved list has name:", "Test Zirkel" in await pg.inner_text("#workoutCircuitSavedList"))

        # tap to reuse -> should start the player directly
        await pg.click("#workoutCircuitSavedList .bundle-item"); await pg.wait_for_timeout(400)
        print("tap-to-reuse started workout player:", await pg.is_visible("#workoutPlayer"))
        if await pg.is_visible("#workoutBackBtn"):
            await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)

        # persistence across reload
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        print("preset persists after reload:", "Test Zirkel" in await pg.inner_text("#workoutCircuitSavedList"))

        # delete
        await pg.click("#workoutCircuitSavedList .combo-block-remove"); await pg.wait_for_timeout(200)
        print("saved group hidden after delete:", await pg.is_hidden("#workoutCircuitSavedGroup"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
