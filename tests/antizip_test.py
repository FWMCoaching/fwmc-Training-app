import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Antizipationstest (Coincidence-Anticipation Timing): twelfth exercise added
# under the autonomous "Test" section. A ball moves at constant speed across
# a horizontal track toward a marked target zone; the client taps a single
# button at the moment they believe the ball arrives. Grounded in the
# classic Coincidence-Anticipation Timing paradigm from sport science
# (historically measured with the "Bassin Anticipation Timer"), scored via
# Absolute Error (AE)/Constant Error (CE)/Variable Error (VE) - the standard
# error decomposition for this paradigm (Schutz & Roy, 1973/1977). Unlike
# every RT-based exercise on this tab, correctness here depends on precise
# TIMING, not speed - tapping the instant the ball appears is always a large,
# unambiguous "Zu früh" (the ball's shortest possible arrival time, even on
# "schwer", is ~950ms away), which this test uses as a robust, non-flaky way
# to exercise the error-classification logic without needing to land inside
# a tight tolerance window under Playwright's own timing jitter.
# Background colour/intensity (added later, fourth batch of the same
# Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/Rotation/
# Merkspanne/Simon - see CLAUDE.md's Established patterns for the scope
# decision, minus their transfer/preset-save machinery) tints the outer
# #antizipStage - the target zone (#ffe0b2/#e65100 dashed border) lives in
# its own fixed-colour .antizip-track sub-element, not directly on the raw
# stage, so this is lower-risk by construction (same reasoning as
# Merkspanne's .merk-field). Both the ready screen and the pause overlay
# have their own live picker+slider sharing the same antizipPrefs.

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
        print("Antizip card visible:", await pg.is_visible("#antizipOpenBtn"))
        await pg.click("#antizipOpenBtn"); await pg.wait_for_timeout(150)
        print("antizipReady visible:", await pg.is_visible("#antizipReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#antizipAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#antizipBgColorPicker .color-swatch").count())
        await pg.click('#antizipBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#antizipBgIntensitySlider", "0.6"); await pg.dispatch_event("#antizipBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#antizipBgIntensityValue")))

        # "schwer" = shortest travel/tail time, so a short test window still
        # reliably samples several trials, including a timeout.
        await pg.click('#antizipDifficultyRow [data-antizip-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#antizipReadyStartBtn"); await pg.wait_for_timeout(200)
        print("antizipPlayer visible:", await pg.is_visible("#antizipPlayer"))
        progress = await pg.inner_text("#antizipProgressEl")
        print("progress starts at 0/20:", "0/20" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('antizipStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#antizipProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_ball_visible(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible("#antizipBall"):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_ball_hidden(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if await pg.is_hidden("#antizipBall"):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: tap the INSTANT the ball appears -> always a large,
        # unambiguous "Zu früh" regardless of any timing jitter in the test
        # itself (the shortest possible arrival is ~950ms away on "schwer"). ---
        progress = await wait_for_progress_change(progress)
        appeared1 = await wait_for_ball_visible()
        print("trial 1's ball appeared:", appeared1)
        await pg.click("#antizipTapBtn"); await pg.wait_for_timeout(60)
        fb1 = await pg.inner_text("#antizipFeedback")
        fb1_class = await pg.get_attribute("#antizipFeedback", "class") or ""
        print("tapping instantly is classified 'Zu früh':", "früh" in fb1 and "early" in fb1_class)
        print("ball hides again right after a tap:", await pg.is_hidden("#antizipBall"))

        # --- a second immediate tap before the next ball appears is ignored (still in the gap phase) ---
        fb_before = await pg.inner_text("#antizipFeedback")
        await pg.click("#antizipTapBtn"); await pg.wait_for_timeout(60)
        fb_after = await pg.inner_text("#antizipFeedback")
        print("a tap during the inter-trial gap does nothing:", fb_before == fb_after)

        # --- trial 2: let it run out fully unanswered -> a genuine timeout/miss,
        # checked the moment the ball itself hides again (BEFORE the 900ms
        # feedback-hold delay elapses and the next trial's own progress bump
        # and feedback reset happen). ---
        progress = await wait_for_progress_change(progress)
        appeared2 = await wait_for_ball_visible()
        print("trial 2's ball appeared:", appeared2)
        hid2 = await wait_for_ball_hidden()
        print("trial 2's ball disappears on its own (timeout) without a tap:", hid2)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#antizipFeedback")))
        progress = await wait_for_progress_change(progress)

        # --- two more quick "tap instantly" trials, purely to accumulate
        # enough resolved trials (>=4) for the Beenden-mid-run check below,
        # same >=4 threshold convention as Simon/Flanker/Posner. ---
        for _ in range(2):
            progress = await wait_for_progress_change(progress)
            await wait_for_ball_visible()
            await pg.click("#antizipTapBtn"); await pg.wait_for_timeout(60)

        # --- pause/resume freezes the stage (during the next trial's motion) ---
        progress = await wait_for_progress_change(progress)
        await wait_for_ball_visible()
        await pg.click("#antizipPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#antizipPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#antizipPauseBtn"))
        html_paused1 = await pg.inner_html("#antizipTrack")
        progress_paused1 = await pg.inner_text("#antizipProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#antizipTrack")
        progress_paused2 = await pg.inner_text("#antizipProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#antizipPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('antizipStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#antizipResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#antizipPauseOverlay"))

        # --- Beenden mid-run with >=4 resolved trials -> done panel with the AE/CE/VE-style summary ---
        await pg.click("#antizipBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with enough progress:", await pg.is_visible("#antizipDonePanel"))
        summary = await pg.inner_text("#antizipDoneSummary")
        print("done summary mentions Antizipationstest and Trefferquote %:", "Antizipationstest" in summary and "Trefferquote" in summary and "%" in summary)
        await pg.click("#antizipDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with barely any progress skips the done panel (same convention as Simon/Flanker) ---
        await pg.click("#antizipOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#antizipReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#antizipPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#antizipPauseBtn"))
        await pg.click("#antizipBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#antizipDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#antizipOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#antizipDifficultyRow [data-antizip-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#antizipOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#antizipDifficultyRow [data-antizip-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
