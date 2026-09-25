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

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # build a 2-block combo: NAT fixed + NAT shuffle, from NAT home this time
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome [data-open-combo="1"]'); await pg.wait_for_timeout(200)
        print("combo screen visible (from NAT):", await pg.is_visible("#comboScreen"))

        nat_btns = pg.locator('.combo-domain-group:has(.combo-domain-title:text-is("NAT")) .combo-add-btn')
        await nat_btns.nth(0).click(); await pg.wait_for_timeout(100)
        await nat_btns.nth(1).click(); await pg.wait_for_timeout(100)
        print("block count text (should be 2 Bausteine):", await pg.inner_text("#comboBlockCount"))

        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
        print("remember player visible after start:", await pg.is_visible("#rememberPlayer"))

        # mid-block "Beenden" should abort the WHOLE combo (2 blocks), not
        # just skip to the second NAT block
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)
        print("remember player hidden after Beenden:", await pg.is_hidden("#rememberPlayer"))
        print("combo done panel visible (should be False - aborted, not finished):", await pg.is_visible("#comboDonePanel"))
        print("back at natHome (comboReturnScreen):", await pg.is_visible("#natHome"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
