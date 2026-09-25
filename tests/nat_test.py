import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

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

        # NAT tab present on home, 5 tabs total
        tabs = await pg.locator("#home .section-tab").count()
        print("tabs on home:", tabs)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        print("natHome visible:", await pg.is_visible("#natHome"))
        print("home hidden:", await pg.is_hidden("#home"))
        print("NAT tab active on natHome:", await pg.get_attribute('#natHome .section-tab[data-section="nat"]', 'class'))

        # sub-nav default state
        print("peripher panel visible:", await pg.is_visible("#natPeripherPanel"))
        print("remember panel hidden:", await pg.is_hidden("#natRememberPanel"))
        print("flash panel hidden:", await pg.is_hidden("#natFlashPanel"))

        await pg.screenshot(path=OUT + "nat_light.png")

        # switch to Remember
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        print("after click remember -> remember visible:", await pg.is_visible("#natRememberPanel"))
        print("peripher now hidden:", await pg.is_hidden("#natPeripherPanel"))
        print("remember tab active:", "active" in (await pg.get_attribute('.sub-tab[data-nat-sub="remember"]', 'class') or ""))

        # switch to Flash
        await pg.click('.sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        print("flash visible:", await pg.is_visible("#natFlashPanel"))
        await pg.screenshot(path=OUT + "nat_flash.png")

        # navigate away and back - check NAT tab reflects correctly from other screens
        await pg.click('#natHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
        print("back at home:", await pg.is_visible("#home"))
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(150)
        print("workoutHome visible:", await pg.is_visible("#workoutHome"))
        print("workout tabs count:", await pg.locator("#workoutHome .section-tab").count())
        await pg.click('#workoutHome .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        print("natHome visible again:", await pg.is_visible("#natHome"))

        # combo entry link still works from NAT
        await pg.click('#natHome [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        print("combo screen visible from NAT:", await pg.is_visible("#comboScreen"))

        # dark mode screenshot
        await pg.emulate_media(color_scheme="dark")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=OUT + "nat_dark.png")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
