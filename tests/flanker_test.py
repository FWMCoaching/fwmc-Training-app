import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Ablenkungstest (Flanker): fourth exercise added under the autonomous "Test"
# section. Classic Eriksen flanker paradigm (Eriksen & Eriksen, 1974) - a
# central target arrow flanked by four distractor arrows that either point
# the same way ("congruent") or the opposite way ("incongruent"). The client
# must respond to the CENTRE arrow only and ignore the flankers. Fixed
# 32-trial run (FLANKER_TRIAL_COUNT), no "Bei Fehler"/level progression -
# this task reports accuracy % + average congruent/incongruent reaction time
# + the interference cost ("flanker effect") instead, the actual outcome
# measures for this paradigm. Background colour/intensity (added later, so
# every Test-Bereich exercise gets the same Feineinstellungen control NAT's
# Remember/Blitz/Flash/MOT already have - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints #flankerStage; both the ready screen and the pause
# overlay have their own live picker+slider sharing the same flankerPrefs.
#
# Timing note: the arrows stay on screen (feedback colour and all) for the
# FULL diff.responseMs window regardless of how fast the client answers -
# same rhythm as Go/No-Go leaving its stimulus's hit/wrong colour up for the
# rest of stimMs - so "a new trial started" is only reliably detected via
# the progress counter advancing, not via the arrow row simply being present.

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
        print("Flanker card visible:", await pg.is_visible("#flankerOpenBtn"))
        await pg.click("#flankerOpenBtn"); await pg.wait_for_timeout(150)
        print("flankerReady visible:", await pg.is_visible("#flankerReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#flankerAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#flankerBgColorPicker .color-swatch").count())
        await pg.click('#flankerBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#flankerBgIntensitySlider", "0.6"); await pg.dispatch_event("#flankerBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#flankerBgIntensityValue")))

        # "schwer" = shortest response window/ISI, so a short test window
        # still reliably samples several trials, including a timeout.
        await pg.click('#flankerDifficultyRow [data-flanker-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#flankerReadyStartBtn"); await pg.wait_for_timeout(200)
        print("flankerPlayer visible:", await pg.is_visible("#flankerPlayer"))
        progress = await pg.inner_text("#flankerProgressEl")
        print("progress starts at 0/32:", "0/32" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('flankerStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#flankerProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_arrows(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".flanker-arrow").count() == 5:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def target_dir():
            txt = await pg.inner_text(".flanker-target")
            return "left" if "←" in txt else "right"

        # --- trial 1: correct response ---
        progress = await wait_for_progress_change(progress)
        got_trial1 = await wait_for_arrows()
        print("trial 1's 5-arrow row appeared:", got_trial1)
        print("exactly one arrow is marked as the target:", await pg.locator(".flanker-target").count() == 1)
        d1 = await target_dir()
        btn1 = "#flankerLeftBtn" if d1 == "left" else "#flankerRightBtn"
        await pg.click(btn1); await pg.wait_for_timeout(80)
        print("tapping the correct direction marks that button 'correct':", "correct" in (await pg.get_attribute(btn1, "class") or ""))

        # --- trial 2: deliberately tap the opposite (wrong) button ---
        progress = await wait_for_progress_change(progress)
        got_trial2 = await wait_for_arrows()
        print("trial 2's row appeared after trial 1's full response window elapsed:", got_trial2)
        d2 = await target_dir()
        wrong_btn = "#flankerRightBtn" if d2 == "left" else "#flankerLeftBtn"
        await pg.click(wrong_btn); await pg.wait_for_timeout(80)
        print("tapping the wrong direction marks that button 'wrong':", "wrong" in (await pg.get_attribute(wrong_btn, "class") or ""))
        print("a wrong tap shows the 'Falsche Richtung!' hint:", "Falsche" in (await pg.inner_text("#flankerHint")))

        # --- trial 3: let its response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        got_trial3 = await wait_for_arrows()
        print("trial 3's row appeared:", got_trial3)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#flankerHint")))
        progress = progress4

        # --- pause/resume freezes the stage ---
        await wait_for_arrows()
        await pg.click("#flankerPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#flankerPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#flankerPauseBtn"))
        row_paused1 = await pg.inner_html("#flankerRow")
        progress_paused1 = await pg.inner_text("#flankerProgressEl")
        await pg.wait_for_timeout(700)
        row_paused2 = await pg.inner_html("#flankerRow")
        progress_paused2 = await pg.inner_text("#flankerProgressEl")
        print("stage genuinely frozen while paused:", row_paused1 == row_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#flankerPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('flankerStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#flankerResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#flankerPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy% ---
        # Let a couple more trials pass (unanswered, i.e. more timeouts) so
        # resolved count is comfortably >= 4 by the time Beenden is pressed.
        await pg.wait_for_timeout(2500)
        await pg.click("#flankerBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#flankerDonePanel"))
        summary = await pg.inner_text("#flankerDoneSummary")
        print("done summary mentions Ablenkungstest and % richtig:", "Ablenkungstest" in summary and "%" in summary)
        await pg.click("#flankerDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as Go/No-Go) ---
        await pg.click("#flankerOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#flankerReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#flankerPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#flankerPauseBtn"))
        await pg.click("#flankerBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#flankerDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#flankerOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#flankerDifficultyRow [data-flanker-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#flankerOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#flankerDifficultyRow [data-flanker-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
