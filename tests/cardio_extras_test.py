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
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)

        # ---- combo-entry-link now present on cardioHome ----
        print("combo-entry-link visible on cardioHome:", await pg.is_visible('#cardioHome .combo-entry-link'))
        await pg.click('#cardioHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("opens comboScreen:", await pg.is_visible("#comboScreen"))
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        print("back returns to cardioHome:", await pg.is_visible("#cardioHome"))

        # ---- Tabata-style count badge on the activity add-grid ----
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        print("no badge before adding:", "in der Einheit" not in await pg.inner_text("#cardioAddGrid"))
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(150)
        print("badge shows 1x after first add:", "1× in der Einheit" in await pg.inner_text("#cardioAddGrid"))
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(150)
        print("badge shows 2x after second add:", "2× in der Einheit" in await pg.inner_text("#cardioAddGrid"))
        print("2 rows in the list:", await pg.locator("#cardioList .circuit-item-row").count() == 2)
        # remove one -> badge drops back to 1x
        await pg.locator("#cardioList .combo-block-remove").first.click(); await pg.wait_for_timeout(150)
        print("badge back to 1x after removing one:", "1× in der Einheit" in await pg.inner_text("#cardioAddGrid"))
        print("still no 2x text lingering:", "2× in der Einheit" not in await pg.inner_text("#cardioAddGrid"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
