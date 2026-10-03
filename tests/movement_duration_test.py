import asyncio, json
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
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#movementReady .advanced summary'); await pg.wait_for_timeout(150)
        print("slider max is 5:", await pg.get_attribute("#movementDurSlider", "max") == "5")
        await pg.fill("#movementDurSlider", "4.5")
        await pg.eval_on_selector("#movementDurSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("value label 4,5 Min:", (await pg.inner_text("#movementDurValue")) == "4,5 Min")
        print("no preset button active:", await pg.eval_on_selector_all("[data-mv-dur].active", "els => els.length") == 0)
        saved = json.loads(await pg.evaluate("localStorage.getItem('fwmc-movement-v1')"))
        print("persisted 4.5:", saved["durationMin"] == 4.5)
        await pg.click('[data-mv-dur="2"]'); await pg.wait_for_timeout(100)
        print("button syncs slider:", await pg.eval_on_selector("#movementDurSlider", "el => el.value") == "2")
        await pg.fill("#movementDurSlider", "5")
        await pg.eval_on_selector("#movementDurSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        await pg.reload(); await pg.wait_for_timeout(500)
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        print("reload keeps 5 Min:", (await pg.text_content("#movementDurValue")) == "5 Min")
        print("no errors:", errors == [] or errors)
        await b.close()

asyncio.run(main())
