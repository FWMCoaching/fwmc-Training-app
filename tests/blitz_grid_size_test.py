import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Blitz-Raster's Rastergröße was capped at 5x5 - the client asked for higher
# options ("8x8 oder so", "mindestens auf iPad macht das Sinn"). Added
# 6x6/7x7/8x8; blitzEligibleCells()/blitzMaxLevelForCurrentSettings() were
# already generic over gridSize (the 3x3 Bereich band math scales to any N),
# so this is mostly a new choice + validation + a narrower grid gap so the
# extra cells stay reasonable tap targets on a phone-width screen too.

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
        await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)

        print("6/7/8 offered alongside 3/4/5:", await pg.locator("#blitzGridSizeRow [data-blitz-grid]").count() == 6)

        await pg.click('#blitzGridSizeRow [data-blitz-grid="8"]'); await pg.wait_for_timeout(80)
        print("8x8 selectable and becomes active:", "active" in (await pg.get_attribute('#blitzGridSizeRow [data-blitz-grid="8"]', "class") or ""))
        print("Bereich still shown for 8x8 (only 3x3 hides it):", await pg.is_visible("#blitzZoneGroup"))
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-blitz-prefs-v1')||'{}').gridSize")
        print("8 persisted to prefs:", prefs == 8)

        await pg.click("#blitzAdvanced summary"); await pg.wait_for_timeout(100)
        max_start = int(await pg.get_attribute("#blitzStartSlider", "max"))
        print("start-count max scales up for the much bigger grid (all zones):", max_start > 16 or max_start == 16)

        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(200)
        cell_count = await pg.locator("#blitzGrid .blitz-cell").count()
        print("8x8 grid actually renders 64 cells:", cell_count == 64)
        gap = await pg.evaluate("() => getComputedStyle(document.getElementById('blitzGrid')).gap")
        print("gap narrowed for the 8x8 grid (not the 10px default):", gap != "10px")
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(150)

        # --- reload persistence + 8x8 still selectable after coming back ---
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)
        print("8x8 selection survives reload:", "active" in (await pg.get_attribute('#blitzGridSizeRow [data-blitz-grid="8"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
