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

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)

        async def active(sel):
            return "active" in (await pg.get_attribute(sel, "class") or "")

        print("default: all 3 axes active:", all([await active('[data-periph-axis="horizontal"]'), await active('[data-periph-axis="vertikal"]'), await active('[data-periph-axis="diagonal"]')]))
        print("default: Überall active (all 3 selected):", await active("#periphAllBtn"))

        # deselect one axis -> Überall should turn off
        await pg.click('[data-periph-axis="vertikal"]'); await pg.wait_for_timeout(80)
        print("vertikal now off:", not await active('[data-periph-axis="vertikal"]'))
        print("Überall auto-deactivated:", not await active("#periphAllBtn"))

        # reselect vertikal by hand -> all 3 active again -> Überall auto-activates
        await pg.click('[data-periph-axis="vertikal"]'); await pg.wait_for_timeout(80)
        print("Überall auto-activated once all 3 picked by hand:", await active("#periphAllBtn"))

        # click Überall while all active -> toggles everything OFF
        await pg.click("#periphAllBtn"); await pg.wait_for_timeout(80)
        print("all 3 off after clicking Überall while active:", not any([await active('[data-periph-axis="horizontal"]'), await active('[data-periph-axis="vertikal"]'), await active('[data-periph-axis="diagonal"]')]))
        print("hint shown at zero:", await pg.inner_text("#periphFieldHint"))
        print("hint has warn class:", "warn" in (await pg.get_attribute("#periphFieldHint", "class") or ""))
        print("start button disabled at zero:", await pg.is_disabled("#startBtn"))

        # click Überall again -> all back on
        await pg.click("#periphAllBtn"); await pg.wait_for_timeout(80)
        print("all 3 back on after clicking Überall again:", all([await active('[data-periph-axis="horizontal"]'), await active('[data-periph-axis="vertikal"]'), await active('[data-periph-axis="diagonal"]')]))
        print("start button enabled again:", not await pg.is_disabled("#startBtn"))

        # Eigene Auswahl hides the axis row and shows the zone grid
        await pg.click("#periphZonesBtn"); await pg.wait_for_timeout(100)
        print("axis row hidden in zone mode:", await pg.is_hidden("#periphFieldRow"))
        print("zone grid visible:", await pg.is_visible("#periphZoneGrid"))
        print("start button enabled in zone mode:", not await pg.is_disabled("#startBtn"))

        # toggle back off
        await pg.click("#periphZonesBtn"); await pg.wait_for_timeout(100)
        print("axis row visible again:", await pg.is_visible("#periphFieldRow"))
        print("zone grid hidden again:", await pg.is_hidden("#periphZoneGrid"))

        # persistence across reload
        await pg.click('[data-periph-axis="vertikal"]'); await pg.wait_for_timeout(80)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        print("vertikal deselection persisted:", not await active('[data-periph-axis="vertikal"]'))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
