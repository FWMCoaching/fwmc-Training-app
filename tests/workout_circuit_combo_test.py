import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def add_exercise(label):
            await pg.click(f'#workoutCircuitAddGrid .ca-plus-btn[aria-label="{label} zum Zirkel hinzufügen"]')

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- seed a standalone Tabata circuit (distinct exercise), to
        # prove capture mode doesn't clobber it ----
        await pg.click('.section-tab[data-section="workout"]'); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        await add_exercise("Liegestütze"); await pg.wait_for_timeout(150)
        print("standalone setup has 1 item (Liegestütze) before combo work:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 1)
        await pg.click("#workoutTabataBackToHome"); await pg.wait_for_timeout(200)

        # ==== Build a combo with a Workout circuit block ====
        await pg.click('#workoutHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        print("'Eigener Zirkel' present in add grid:", "Eigener Zirkel" in await pg.inner_text("#comboAddGrid"))
        await pg.click('#comboAddGrid >> text="Eigener Zirkel"'); await pg.wait_for_timeout(300)
        print("capture opens workoutTabataReady:", await pg.is_visible("#workoutTabataReady"))
        print("title swapped to Baustein: Zirkel:", "Baustein: Zirkel" in await pg.inner_text("#workoutTabataReadyTitle"))
        print("capture starts blank (0 rows), not the standalone Liegestütze item:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 0)

        await add_exercise("Kniebeugen"); await pg.wait_for_timeout(150)
        await add_exercise("Hampelmann"); await pg.wait_for_timeout(150)
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#workoutTabataStartBtn"))
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list shows the circuit (2 Übungen):", "Zirkel · 2 Übungen" in await pg.inner_text("#comboBlockList"))

        # ---- editing: tap the block again, should reopen with its 2 items ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens capture with its 2 items:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 2)
        await add_exercise("Ausfallschritte"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(300)
        print("edited block now shows 3 Übungen:", "Zirkel · 3 Übungen" in await pg.inner_text("#comboBlockList"))

        # ---- cancel path must restore standalone state ----
        await pg.click('#comboAddGrid >> text="Eigener Zirkel"'); await pg.wait_for_timeout(300)
        await add_exercise("Burpees"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataBackToHome"); await pg.wait_for_timeout(300)
        print("cancel (back) returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list still shows only the earlier 3-Übungen block:", "Zirkel · 3 Übungen" in await pg.inner_text("#comboBlockList") and "Zirkel · 1 Übung" not in await pg.inner_text("#comboBlockList") and "Zirkel · 4 Übungen" not in await pg.inner_text("#comboBlockList"))

        # ---- standalone Tabata circuit (Liegestütze) must be untouched ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        print("standalone circuit still has Liegestütze, untouched by capture:", "Liegestütze" in await pg.inner_text("#workoutCircuitList"))
        print("standalone circuit still has exactly 1 item:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 1)
        print("standalone title/button back to normal:", "Baustein:" not in await pg.inner_text("#workoutTabataReadyTitle") and "Zirkel starten" in await pg.inner_text("#workoutTabataStartBtn"))
        await pg.click("#workoutTabataBackToHome"); await pg.wait_for_timeout(200)

        # ==== Run a fresh one-block combo end-to-end (re-entering the
        # builder resets the unsaved draft, same as every other unsaved
        # builder in the app) ====
        await pg.click('#workoutHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Eigener Zirkel"'); await pg.wait_for_timeout(200)
        await add_exercise("Kniebeugen"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(600)
        print("combo run: workoutPlayer shows the circuit:", await pg.is_visible("#workoutPlayer"))
        print("combo run: no workout done panel mid-combo:", not await pg.is_visible("#workoutDonePanel"))
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(400)
        print("abort mid-combo-workout lands back on workoutHome:", await pg.is_visible("#workoutHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
