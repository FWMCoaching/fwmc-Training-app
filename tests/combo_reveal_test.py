import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/combo_reveal.png"

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

        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        add_btns = pg.locator(".combo-add-btn")
        await add_btns.nth(0).click(); await pg.wait_for_timeout(100)
        await add_btns.nth(1).click(); await pg.wait_for_timeout(100)

        # name form should be hidden before clicking save
        print("save form hidden before click:", await pg.is_hidden("#comboSaveForm"))
        print("save btn visible before click:", await pg.is_visible("#comboSaveBtn"))

        await pg.click("#comboSaveBtn")
        await pg.wait_for_timeout(150)
        print("save form visible after click:", await pg.is_visible("#comboSaveForm"))
        print("save btn hidden after click:", await pg.is_hidden("#comboSaveBtn"))
        is_focused = await pg.evaluate("() => document.activeElement && document.activeElement.id === 'comboNameInput'")
        print("name input focused after click:", is_focused)

        await pg.screenshot(path=OUT)

        await pg.fill("#comboNameInput", "Abendroutine")
        await pg.click("#comboSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("form hidden again after confirm:", await pg.is_hidden("#comboSaveForm"))
        print("save btn visible again after confirm:", await pg.is_visible("#comboSaveBtn"))
        print("saved group visible:", await pg.is_visible("#comboSavedGroup"))
        print("saved list has the name:", "Abendroutine" in await pg.inner_text("#comboSavedList"))
        print("draft cleared (empty hint shown):", await pg.is_visible("#comboEmptyHint"))

        # delete capability (new, via shared preset-list helper)
        has_delete_btn = await pg.locator("#comboSavedList .combo-block-remove").count() > 0
        print("saved combo has a delete button:", has_delete_btn)
        await pg.click("#comboSavedList .combo-block-remove"); await pg.wait_for_timeout(150)
        print("saved group hidden after delete:", await pg.is_hidden("#comboSavedGroup"))

        # cancel flow
        await add_btns.nth(0).click(); await pg.wait_for_timeout(100)
        await pg.click("#comboSaveBtn"); await pg.wait_for_timeout(100)
        await pg.click("#comboSaveCancelBtn"); await pg.wait_for_timeout(100)
        print("form hidden after cancel:", await pg.is_hidden("#comboSaveForm"))
        print("save btn visible after cancel:", await pg.is_visible("#comboSaveBtn"))
        print("block still in draft after cancel (not lost):", "1 Baustein" in await pg.inner_text("#comboBlockCount"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
