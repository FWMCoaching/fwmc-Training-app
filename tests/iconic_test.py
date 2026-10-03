import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Iconic-Speicher-Test: twenty-sixth exercise added under the autonomous
# "Test" section, picked from the Recherche-Backlog (candidate #1, the
# Sperling 1960 partial-report paradigm). A 3x3 digit grid flashes for a
# near-subliminal duration, then after a variable delay (0/300/700/1000ms)
# one row is highlighted (a border, standing in for the original's tone
# cue) - only that row's three digits are tapped back via a keypad.
# Reports per-delay accuracy, the actual decay curve this paradigm exists
# to reveal.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("testHome visible:", await pg.is_visible("#testHome"))
        print("Iconic card visible:", await pg.is_visible("#iconicOpenBtn"))
        await pg.click("#iconicOpenBtn"); await pg.wait_for_timeout(150)
        print("iconicReady visible:", await pg.is_visible("#iconicReady"))

        # "leicht" = longest flash, easiest to reliably read in a screenshot/test
        await pg.click('#iconicDifficultyRow [data-iconic-diff="leicht"]'); await pg.wait_for_timeout(60)
        print("leicht marked active:", "active" in (await pg.get_attribute('#iconicDifficultyRow [data-iconic-diff="leicht"]', "class") or ""))
        await pg.click("#iconicReadyStartBtn"); await pg.wait_for_timeout(200)
        print("iconicPlayer visible:", await pg.is_visible("#iconicPlayer"))
        print("progress starts at 0/24:", "0/24" in (await pg.inner_text("#iconicProgressEl")))
        print("grid has 9 cells (3x3):", await pg.locator(".iconic-cell").count() == 9)

        async def wait_for_flash(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                filled = await pg.locator(".iconic-cell:not(:empty)").count()
                if filled == 9:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_cue(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".iconic-row.cued").count() > 0:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: flash shows all 9 digits, then blanks, then one row is cued ---
        print("all 9 digits shown during the flash:", await wait_for_flash())
        blanked = False
        for _ in range(40):
            if await pg.locator(".iconic-cell:not(:empty)").count() == 0:
                blanked = True
                break
            await pg.wait_for_timeout(20)
        print("grid blanks after the flash (before the cue):", blanked)
        print("exactly one row gets the cued outline:", await wait_for_cue() and await pg.locator(".iconic-row.cued").count() == 1)
        print("answer boxes + keypad appear once cued:", await pg.is_visible("#iconicAnswerRow") and await pg.is_visible("#iconicKeypad"))
        print("keypad has 9 keys:", await pg.locator(".iconic-key").count() == 9)

        # tap 3 digits - auto-checks once 3 are entered
        for i in range(3):
            await pg.click(".iconic-key >> nth=0")
        await pg.wait_for_timeout(150)
        print("answer boxes show feedback classes after 3 taps:", await pg.locator(".iconic-answer-box.correct, .iconic-answer-box.wrong").count() == 3)
        print("hint reveals what the correct row was:", "Richtig war" in (await pg.inner_text("#iconicHint")))

        # --- run through several more trials to clear the min-resolved gate ---
        for _ in range(4):
            await wait_for_flash()
            await wait_for_cue()
            for i in range(3):
                await pg.click(".iconic-key >> nth=0")
            await pg.wait_for_timeout(1050)  # feedback + ISI before next trial

        progress_after = await pg.inner_text("#iconicProgressEl")
        print("progress advanced past the first several trials:", "0/24" not in progress_after)

        # --- pause/resume freezes the stage ---
        await wait_for_cue()
        await pg.click("#iconicPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#iconicPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#iconicPauseBtn"))
        progress_paused1 = await pg.inner_text("#iconicProgressEl")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#iconicProgressEl")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click("#iconicResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#iconicPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel ---
        await pg.click("#iconicBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#iconicDonePanel"))
        summary = await pg.inner_text("#iconicDoneSummary")
        print("done summary mentions Iconic-Speicher-Test and richtig:", "Iconic-Speicher-Test" in summary and "richtig" in summary)
        await pg.click("#iconicDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#iconicOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#iconicReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#iconicPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#iconicPauseBtn"))
        await pg.click("#iconicBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#iconicDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#iconicOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#iconicDifficultyRow [data-iconic-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#iconicOpenBtn"); await pg.wait_for_timeout(150)
        print("'schwer' selection survives reload:", "active" in (await pg.get_attribute('#iconicDifficultyRow [data-iconic-diff="schwer"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
