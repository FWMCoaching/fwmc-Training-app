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

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # setupBtn should be hidden for a normal exercise (VT color)
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        print("setupBtn hidden for vt-color (expected True):", await pg.is_hidden("#setupBtn"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)

        # open cone-compass, use filter to reveal the huetchen card
        await pg.click("#filterMoreBtn"); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="huetchen"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="cone-compass"]'); await pg.wait_for_timeout(150)
        print("setupBtn visible for cone-compass:", await pg.is_visible("#setupBtn"))
        thumb_svg_count = await pg.locator("#setupThumb svg").count()
        print("thumbnail has an svg:", thumb_svg_count == 1)

        await pg.click("#setupBtn"); await pg.wait_for_timeout(150)
        print("setup modal visible:", await pg.is_visible("#setupModal"))
        print("slide 1 title:", await pg.inner_text("#setupSlideTitle"))
        print("slide 1 counter:", await pg.inner_text("#setupCounter"))
        print("prev disabled on slide 1:", await pg.is_disabled("#setupPrevBtn"))
        cone_count_1 = await pg.locator("#setupSlideArt circle").count()
        print("slide 1 circle count (center + 4 cones = 5):", cone_count_1)

        await pg.click("#setupNextBtn"); await pg.wait_for_timeout(100)
        print("slide 2 title:", await pg.inner_text("#setupSlideTitle"))
        cone_count_2 = await pg.locator("#setupSlideArt circle").count()
        print("slide 2 circle count (center + 8 cones = 9):", cone_count_2)

        await pg.click("#setupNextBtn"); await pg.wait_for_timeout(100)
        print("slide 3 title:", await pg.inner_text("#setupSlideTitle"))
        print("next disabled on slide 3 (last):", await pg.is_disabled("#setupNextBtn"))
        cone_count_3 = await pg.locator("#setupSlideArt circle").count()
        print("slide 3 circle count (center + 2+1+1=4 cones = 5):", cone_count_3)
        caption_3 = await pg.inner_text("#setupSlideCaption")
        print("slide 3 caption mentions 'häufiger':", "häufiger" in caption_3)

        await pg.screenshot(path=OUT + "setup_modal_slide3.png")

        # close via backdrop click
        await pg.click("#setupModal", position={"x": 5, "y": 5})
        await pg.wait_for_timeout(150)
        print("modal closed after backdrop click:", await pg.is_hidden("#setupModal"))

        # reopen, verify Escape closes it too
        await pg.click("#setupBtn"); await pg.wait_for_timeout(150)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
        print("modal closed after Escape:", await pg.is_hidden("#setupModal"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
