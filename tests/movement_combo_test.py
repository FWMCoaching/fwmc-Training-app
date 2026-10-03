import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(200)

        # ==== Build a combo with a Movement block ====
        await pg.click('#movementHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        print("Movement group present in add grid:", "Ganzkörper-Reaktion" in await pg.inner_text("#comboAddGrid"))
        await pg.click('#comboAddGrid >> text="Ganzkörper-Reaktion"'); await pg.wait_for_timeout(300)
        print("capture mode opens movementReady:", await pg.is_visible("#movementReady"))
        print("title swapped to Baustein: Movement:", "Baustein: Movement" in await pg.inner_text("#movementReadyTitle"))
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#movementStartBtn"))

        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list shows the Movement block:", "Ganzkörper-Reaktion" in await pg.inner_text("#comboBlockList"))

        # ---- editing: tap the Movement block again ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens movement capture:", await pg.is_visible("#movementReady"))
        print("title still shows capture mode on re-edit:", "Baustein: Movement" in await pg.inner_text("#movementReadyTitle"))
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path (back-link) must restore normal title/button ----
        await pg.click('#comboAddGrid >> text="Ganzkörper-Reaktion"'); await pg.wait_for_timeout(300)
        await pg.click("#movementBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone entry (movementReady, opened fresh) shows normal
        # title/button again, not stuck in capture mode ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        print("standalone open shows normal title again:", "Ganzkörper-Reaktion" in await pg.inner_text("#movementReadyTitle"))
        print("standalone open shows normal start label again:", "Training starten" in await pg.inner_text("#movementStartBtn"))
        await pg.click("#movementBackToHome"); await pg.wait_for_timeout(200)

        # ==== Run the combo end-to-end. Re-entering the combo builder
        # resets the unsaved draft (same as every other unsaved builder in
        # the app), so build a fresh one-block combo here. ====
        await pg.click('#movementHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Ganzkörper-Reaktion"'); await pg.wait_for_timeout(300)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: movementPlayer shows the block:", await pg.is_visible("#movementPlayer"))
        print("combo run: no movement done panel mid-combo:", not await pg.is_visible("#movementDonePanel"))
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(400)
        print("abort mid-combo-movement lands back on movementHome:", await pg.is_visible("#movementHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
