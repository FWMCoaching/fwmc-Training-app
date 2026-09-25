import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/workout_save_position.png"

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

        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)

        # saved-circuits list should now be at the TOP, before "Übung hinzufügen"
        order_ok = await pg.evaluate("""() => {
            const savedGroup = document.getElementById('workoutCircuitSavedGroup');
            const addGrid = document.getElementById('workoutCircuitAddGrid');
            return savedGroup.compareDocumentPosition(addGrid) === Node.DOCUMENT_POSITION_FOLLOWING;
        }""")
        print("saved-circuits group now sits before 'Übung hinzufügen':", order_ok)

        # save button + form should now sit inside the "Dein Zirkel" group, right after the list
        same_group = await pg.evaluate("""() => {
            const list = document.getElementById('workoutCircuitList');
            const saveBtn = document.getElementById('workoutCircuitSaveBtn');
            return list.parentElement === saveBtn.parentElement;
        }""")
        print("save button shares the 'Dein Zirkel' group with the list:", same_group)

        add_btns = pg.locator("#workoutCircuitAddGrid .combo-add-btn")
        await add_btns.nth(0).click(); await pg.wait_for_timeout(100)
        await add_btns.nth(1).click(); await pg.wait_for_timeout(100)
        await pg.click("#workoutCircuitSaveBtn")
        await pg.fill("#workoutCircuitSaveNameInput", "Oberkörper kurz")
        await pg.locator("#workoutCircuitList").scroll_into_view_if_needed()
        await pg.screenshot(path=OUT)

        await pg.click("#workoutCircuitSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("saved list has the name:", "Oberkörper kurz" in await pg.inner_text("#workoutCircuitSavedList"))
        print("saved group now visible near top:", await pg.is_visible("#workoutCircuitSavedGroup"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
