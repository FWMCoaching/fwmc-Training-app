import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Reaktionsfeld-Test: fifteenth autonomous entry under the Test section.
# Grounded in reaction-light-board training devices such as the Dynavision
# D2 (a 64-light board across five concentric rings, used in sport-vision
# training and concussion/return-to-play research) - a single light appears
# somewhere across the whole field, the client taps it as fast as possible,
# then the next one appears elsewhere immediately. Two modes mirror the real
# device's own Mode A/Mode B: "proaktiv" (light stays lit until hit) and
# "reaktiv" (light times out and moves on regardless).

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
        print("testHome visible:", await pg.is_visible("#testHome"))
        print("Reaktionsfeld-Test card visible:", await pg.is_visible("#reaktOpenBtn"))
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        print("reaktReady visible:", await pg.is_visible("#reaktReady"))

        # --- proaktiv mode, kurz length, schwer difficulty (fast, but light
        # never times out - only a real tap advances it) ---
        await pg.click('#reaktModeRow [data-reakt-mode="proaktiv"]'); await pg.wait_for_timeout(60)
        await pg.click('#reaktDifficultyRow [data-reakt-difficulty="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click('#reaktLengthRow [data-reakt-length="kurz"]'); await pg.wait_for_timeout(60)
        print("proaktiv mode selection is active:", "active" in (await pg.get_attribute('#reaktModeRow [data-reakt-mode="proaktiv"]', "class") or ""))

        await pg.click("#reaktReadyStartBtn"); await pg.wait_for_timeout(1100)
        print("reaktPlayer visible:", await pg.is_visible("#reaktPlayer"))
        print("a light renders after the lead-in:", await pg.locator("#reaktField .reakt-light").count() == 1)

        # tap the light several times, each time it must land at a genuinely
        # different position (min-jump-distance rule) and progress must
        # increment the Treffer count
        hit_count = 0
        for _ in range(5):
            if await pg.locator("#reaktField .reakt-light").count() == 0:
                await pg.wait_for_timeout(150)
                continue
            box_before = await pg.locator("#reaktField .reakt-light").bounding_box()
            await pg.locator("#reaktField .reakt-light").click()
            hit_count += 1
            await pg.wait_for_timeout(120)
            box_after = await pg.locator("#reaktField .reakt-light").bounding_box()
            if box_before and box_after:
                moved = (abs(box_before["x"] - box_after["x"]) > 5) or (abs(box_before["y"] - box_after["y"]) > 5)
                print(f"light moved to a new position on tap #{hit_count}:", moved)
        progress = await pg.inner_text("#reaktProgressEl")
        print("progress shows Treffer count after several hits:", f"Treffer: {hit_count}" in progress)
        print("proaktiv mode reports no 'Verpasst' (light never times out untapped):", "Verpasst" not in progress)

        # --- pause/resume freezes the field (no new light appears) ---
        await pg.click("#reaktPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#reaktPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#reaktPauseBtn"))
        html1 = await pg.inner_html("#reaktField")
        await pg.wait_for_timeout(700)
        html2 = await pg.inner_html("#reaktField")
        print("field genuinely frozen while paused:", html1 == html2)
        await pg.click("#reaktResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#reaktPauseOverlay"))

        # --- Beenden with real progress shows the done panel with zone breakdown ---
        await pg.click("#reaktBackBtn"); await pg.wait_for_timeout(200)
        print("done panel visible after Beenden with real progress:", await pg.is_visible("#reaktDonePanel"))
        summary = await pg.inner_text("#reaktDoneSummary")
        print("done summary mentions Reaktionsfeld-Test and Treffer:", "Reaktionsfeld-Test" in summary and "Treffer" in summary)
        print("done summary mentions Treffer/Min:", "Treffer/Min" in summary)
        print("done summary reports Zentral/Peripher breakdown:", "Zentral" in summary and "Peripher" in summary)
        await pg.click("#reaktDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run quit immediately (Beenden with zero progress) skips the done panel ---
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#reaktReadyStartBtn"); await pg.wait_for_timeout(150)
        await pg.click("#reaktBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#reaktDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- reaktiv mode: an unhit light eventually counts as 'Verpasst' ---
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#reaktModeRow [data-reakt-mode="reaktiv"]'); await pg.wait_for_timeout(60)
        await pg.click('#reaktDifficultyRow [data-reakt-difficulty="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#reaktReadyStartBtn"); await pg.wait_for_timeout(1100)
        # deliberately never tap - let a few lights time out
        await pg.wait_for_timeout(2500)
        progress2 = await pg.inner_text("#reaktProgressEl")
        print("reaktiv mode without any tap accumulates 'Verpasst':", "Verpasst" in progress2)
        await pg.click("#reaktBackBtn"); await pg.wait_for_timeout(200)
        summary2 = await pg.inner_text("#reaktDoneSummary")
        print("reaktiv-only-misses done summary still shown (misses count as progress):", await pg.is_visible("#reaktDonePanel") and "verpasst" in summary2)
        await pg.click("#reaktDoneBackBtn"); await pg.wait_for_timeout(150)

        # --- mode/difficulty/length selection persists across reload ---
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#reaktModeRow [data-reakt-mode="proaktiv"]'); await pg.wait_for_timeout(60)
        await pg.click('#reaktDifficultyRow [data-reakt-difficulty="leicht"]'); await pg.wait_for_timeout(60)
        await pg.click('#reaktLengthRow [data-reakt-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        print("'proaktiv' selection survives reload:", "active" in (await pg.get_attribute('#reaktModeRow [data-reakt-mode="proaktiv"]', "class") or ""))
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#reaktDifficultyRow [data-reakt-difficulty="leicht"]', "class") or ""))
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#reaktLengthRow [data-reakt-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
