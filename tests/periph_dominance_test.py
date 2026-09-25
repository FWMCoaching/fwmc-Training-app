import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# "Dominanz": a 1x-3x weight slider per currently selected Bereich zone
# (Periphere Wahrnehmung only, for now), skewing how often that zone gets
# picked relative to the others instead of a flat equal split.

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
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("weights hidden in axis mode (default):", await pg.is_hidden("#periphZoneWeights"))

        await pg.click("#periphZonesBtn"); await pg.wait_for_timeout(100)
        print("weights visible with all 8 zones selected:", await pg.is_visible("#periphZoneWeights"))
        print("one row per zone:", await pg.locator("#periphZoneWeights .slider-row").count() == 8)

        # narrow to exactly two zones
        for z in ["tm", "tr", "ml", "mr", "bl", "bm"]:
            await pg.click(f'#periphZoneGrid [data-zone="{z}"]'); await pg.wait_for_timeout(40)
        print("two rows left (tl, br):", await pg.locator("#periphZoneWeights .slider-row").count() == 2)

        # exactly one zone selected -> weighting is meaningless, hide it
        await pg.click('#periphZoneGrid [data-zone="br"]'); await pg.wait_for_timeout(80)
        print("weights hidden with a single zone:", await pg.is_hidden("#periphZoneWeights"))
        await pg.click('#periphZoneGrid [data-zone="br"]'); await pg.wait_for_timeout(80)  # back to two

        # set tl to 3x, persists to prefs and survives reload
        await pg.fill('#periphZoneWeights [data-zone-weight="tl"]', "3")
        await pg.dispatch_event('#periphZoneWeights [data-zone-weight="tl"]', "input")
        await pg.wait_for_timeout(80)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')||'{}').periphZoneWeights")
        print("tl weight saved as 3:", prefs.get("tl") == 3)
        print("untouched zones default to 1:", prefs.get("tm") == 1 and prefs.get("mr") == 1)

        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        val = await pg.evaluate("""() => {
            const el = document.querySelector('#periphZoneWeights [data-zone-weight="tl"]');
            return el ? el.value : null;
        }""")
        print("tl weight persisted across reload:", val == "3")

        # switching back to axis mode hides the weight sliders again, and
        # doesn't lose the saved zone weights
        await pg.click("#periphZonesBtn"); await pg.wait_for_timeout(80)
        print("weights hidden back in axis mode:", await pg.is_hidden("#periphZoneWeights"))
        await pg.click("#periphZonesBtn"); await pg.wait_for_timeout(80)
        val2 = await pg.evaluate("""() => {
            const el = document.querySelector('#periphZoneWeights [data-zone-weight="tl"]');
            return el ? el.value : null;
        }""")
        print("tl weight still 3 after toggling zones mode off and on:", val2 == "3")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
