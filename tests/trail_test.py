import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Verbindungstest (Trail Making): the third exercise added under the
# autonomous "Test" section. Grounded in the Trail Making Test (Reitan
# 1958, Halstead-Reitan battery) - scattered circles tapped in ascending
# order (Teil A: 1,2,3…; Teil B: alternating number/letter 1,A,2,B…),
# scored by completion time + error count, no artificial "level"/Bei-
# Fehler reset - a wrong tap is just counted, same as an examiner
# redirecting a participant without stopping the clock. Fresh random
# scatter layout every run (the paper test uses one fixed printed sheet
# per part) so repeat play trains genuine visual search, not layout
# memorisation.

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

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("Trail card visible:", await pg.is_visible("#trailOpenBtn"))
        print("other two Test cards still visible (no collision):", await pg.is_visible("#gngOpenBtn") and await pg.is_visible("#testNbackOpenBtn"))
        await pg.click("#trailOpenBtn"); await pg.wait_for_timeout(150)
        print("trailReady visible:", await pg.is_visible("#trailReady"))

        # --- Teil A, full completion in correct order ---
        await pg.click('#trailTeilRow [data-trail-teil="a"]'); await pg.wait_for_timeout(60)
        await pg.click('#trailDifficultyRow [data-trail-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.click("#trailReadyStartBtn"); await pg.wait_for_timeout(300)
        print("trailPlayer visible:", await pg.is_visible("#trailPlayer"))
        print("15 markers rendered (Leicht):", await pg.locator("#trailMarkersLayer .trail-marker").count() == 15)

        for i in range(1, 16):
            await pg.locator(f'#trailMarkersLayer .trail-marker:text-is("{i}")').click()
            await pg.wait_for_timeout(30)
        await pg.wait_for_timeout(300)
        print("all 15 markers marked done in ascending order:", await pg.locator("#trailMarkersLayer .trail-marker.done").count() == 15)
        print("connecting lines drawn between taps:", await pg.locator("#trailLinesSvg .trail-line").count() == 14)
        print("done panel shown on full completion:", await pg.is_visible("#trailDonePanel"))
        summary = await pg.inner_text("#trailDoneSummary")
        print("done summary mentions the exercise:", "Verbindungstest" in summary or "Trail" in summary)
        await pg.click("#trailDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- Teil B: alternating number/letter sequence ---
        await pg.click("#trailOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#trailTeilRow [data-trail-teil="b"]'); await pg.wait_for_timeout(60)
        await pg.click("#trailReadyStartBtn"); await pg.wait_for_timeout(300)
        print("Teil B: both numbers and letters present:", await pg.locator('#trailMarkersLayer .trail-marker:text-is("A")').count() == 1 and await pg.locator('#trailMarkersLayer .trail-marker:text-is("1")').count() == 1)
        await pg.click("#trailBackBtn"); await pg.wait_for_timeout(150)

        # --- wrong-tap handling: counted as error, doesn't advance or reset ---
        await pg.click("#trailOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#trailTeilRow [data-trail-teil="a"]'); await pg.wait_for_timeout(60)
        await pg.click("#trailReadyStartBtn"); await pg.wait_for_timeout(300)
        wrong_marker = pg.locator('#trailMarkersLayer .trail-marker:not(:text-is("1"))').first
        await wrong_marker.click(); await pg.wait_for_timeout(300)
        print("wrong tap doesn't mark anything done:", await pg.locator("#trailMarkersLayer .trail-marker.done").count() == 0)
        print("progress still at 0/15 after a wrong tap (no reset, no advance):", "0/15" in (await pg.inner_text("#trailProgressEl")))
        # the correct next target still works right after a wrong tap
        await pg.locator('#trailMarkersLayer .trail-marker:text-is("1")').click(); await pg.wait_for_timeout(150)
        print("correct tap right after a wrong one still advances:", "1/15" in (await pg.inner_text("#trailProgressEl")))

        # --- pause/resume freezes the elapsed-time readout ---
        await pg.click("#trailPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#trailPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#trailPauseBtn"))
        txt1 = await pg.inner_text("#trailProgressEl")
        await pg.wait_for_timeout(700)
        txt2 = await pg.inner_text("#trailProgressEl")
        print("elapsed-time readout frozen while paused:", txt1 == txt2)
        await pg.click("#trailResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#trailPauseOverlay"))

        # --- Beenden mid-run (partial progress) skips the done panel ---
        await pg.click("#trailBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden mid-run returns to testHome with no done panel:", await pg.is_visible("#testHome") and await pg.is_hidden("#trailDonePanel"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
