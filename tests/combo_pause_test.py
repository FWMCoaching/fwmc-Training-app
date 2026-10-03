import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Pause markers between Kombi-Baukasten blocks - client's ask: a Master
# default, adjustable per block (different exercises need different
# transition time for changing equipment/position), always skippable.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- Master default pause ----
        await pg.click(".master-settings-btn"); await pg.wait_for_timeout(200)
        print("master pause slider default 20s:", await pg.input_value("#masterPauseSlider") == "20")
        await pg.fill("#masterPauseSlider", "10")
        await pg.dispatch_event("#masterPauseSlider", "input")
        await pg.wait_for_timeout(100)
        print("master pause value updates:", "10" in await pg.inner_text("#masterPauseValue"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- build a 2-block combo (2x Remember, each with a short 15s
        # comboDurationS so block 1 finishes ON ITS OWN - manually quitting
        # mid-block via "Beenden" aborts the whole Kombi instead of
        # advancing, so a natural finish is needed to reach the pause) ----
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
        await pg.fill("#rememberComboDurationSlider", "15")
        await pg.dispatch_event("#rememberComboDurationSlider", "input")
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Positionen merken · Bewegte Positionen"'); await pg.wait_for_timeout(300)
        await pg.fill("#rememberComboDurationSlider", "15")
        await pg.dispatch_event("#rememberComboDurationSlider", "input")
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        print("2 blocks in draft:", await pg.locator("#comboBlockList .chapter-row").count() == 2)

        # ---- pause row present after block 1, not after block 2 (last) ----
        pause_rows = pg.locator("#comboBlockList .combo-pause-row")
        print("exactly 1 pause row (between the 2 blocks, none after the last):", await pause_rows.count() == 1)
        print("pause row defaults to the Master value (10s):", "10" in await pause_rows.first.inner_text())

        # ---- adjust that pause to 6s (short, for a fast test run) ----
        await pg.fill("#comboBlockList .combo-pause-slider", "5")
        await pg.dispatch_event("#comboBlockList .combo-pause-slider", "input")
        await pg.wait_for_timeout(100)
        print("pause value label updates after drag:", "5" in await pause_rows.first.inner_text())

        # ---- run the combo: block 1 finishes on its own (15s cutoff) ->
        # pause with visible countdown -> skip -> block 2 ----
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
        print("remember player visible (block 1):", await pg.is_visible("#rememberPlayer"))
        await pg.wait_for_timeout(16000)
        print("transition screen shown after block 1 finishes on its own:", await pg.is_visible("#comboTransition"))
        print("countdown shows a number:", (await pg.inner_text("#comboTransitionCountdown")).strip() != "")
        print("skip button reads 'Überspringen':", "Überspringen" in await pg.inner_text("#comboTransitionBtn"))
        await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(300)
        print("transition screen hidden after skip:", await pg.is_hidden("#comboTransition"))
        print("remember player visible again (block 2, skip worked instantly):", await pg.is_visible("#rememberPlayer"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
