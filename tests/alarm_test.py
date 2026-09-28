import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Alarmierungs-Test: twentieth exercise added under the autonomous "Test"
# section, picked from the Recherche-Backlog (candidate #17, Alerting-
# Netzwerk). Grounded in the Attention Network Test framework (Fan,
# McCandliss, Sommer, Raz & Posner, 2002) isolating the ALERTING network -
# on half the trials the fixation cross briefly flashes (a non-spatial
# warning), then after a FIXED total foreperiod (identical whether cued or
# not) a target dot appears left or right; the client taps that same side.
# Reports accuracy%, average RT with/without the warning, and the
# "Alarmierungs-Effekt" (Ø ohne Warnung - Ø mit Warnung). Distinct from the
# already-existing Hinweisreiz-Test (Posner-Cueing): that cue is spatially
# informative (predicts WHERE), this cue carries no location information at
# all, purely a "get ready" signal. Background colour/intensity included
# (basically free, reusing wireBgIntensityControl/makeBgApplier exactly
# like Posner/Simon/Flanker) - tints #alarmStage.

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
        print("Alarm card visible:", await pg.is_visible("#alarmOpenBtn"))
        await pg.click("#alarmOpenBtn"); await pg.wait_for_timeout(150)
        print("alarmReady visible:", await pg.is_visible("#alarmReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#alarmAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#alarmBgColorPicker .color-swatch").count())
        await pg.click('#alarmBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#alarmBgIntensitySlider", "0.6"); await pg.dispatch_event("#alarmBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#alarmBgIntensityValue")))

        # "schwer" = shortest response window, so a short test window still
        # reliably samples several trials, including a timeout.
        await pg.click('#alarmDifficultyRow [data-alarm-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#alarmReadyStartBtn"); await pg.wait_for_timeout(200)
        print("alarmPlayer visible:", await pg.is_visible("#alarmPlayer"))
        progress = await pg.inner_text("#alarmProgressEl")
        print("progress starts at 0/32:", "0/32" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('alarmStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#alarmProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_target(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".posner-dot.show").count() == 1:
                    is_left = "show" in (await pg.get_attribute("#alarmLeftDot", "class") or "")
                    return "left" if is_left else "right"
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        # --- trial 1: target appears, correct response ---
        progress = await wait_for_progress_change(progress)
        d1 = await wait_for_target()
        print("trial 1's target dot appeared in exactly one box:", d1 is not None)
        btn1 = "#alarmLeftBtn" if d1 == "left" else "#alarmRightBtn"
        await pg.click(btn1); await pg.wait_for_timeout(80)
        print("tapping the box the dot actually appeared in marks it 'correct':", "correct" in (await pg.get_attribute(btn1, "class") or ""))

        # --- trial 2: deliberately tap the OTHER box (wrong side) ---
        progress = await wait_for_progress_change(progress)
        d2 = await wait_for_target()
        print("trial 2's target dot appeared:", d2 is not None)
        wrong_btn = "#alarmRightBtn" if d2 == "left" else "#alarmLeftBtn"
        await pg.click(wrong_btn); await pg.wait_for_timeout(80)
        print("tapping the wrong side marks that button 'wrong':", "wrong" in (await pg.get_attribute(wrong_btn, "class") or ""))
        print("a wrong tap shows the 'Falsche Seite!' hint:", "Falsche" in (await pg.inner_text("#alarmHint")))

        # --- trial 3: let its response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        d3 = await wait_for_target()
        print("trial 3's target dot appeared:", d3 is not None)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#alarmHint")))
        progress = progress4

        # --- watch enough trials to see at least one cue flash on the fixation cross ---
        async def wait_for_cue_flash(max_ms=4000, poll_ms=10):
            waited = 0
            while waited < max_ms:
                if "flash" in (await pg.get_attribute("#alarmFix", "class") or ""):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False
        saw_flash = await wait_for_cue_flash()
        print("saw the fixation cross flash (an alerting cue) within a few trials:", saw_flash)

        # --- pause/resume freezes the stage ---
        await wait_for_target()
        await pg.click("#alarmPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#alarmPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#alarmPauseBtn"))
        html_paused1 = await pg.inner_html("#alarmStage")
        progress_paused1 = await pg.inner_text("#alarmProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#alarmStage")
        progress_paused2 = await pg.inner_text("#alarmProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#alarmPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('alarmStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#alarmResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#alarmPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy%/effect ---
        await pg.wait_for_timeout(2500)
        await pg.click("#alarmBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#alarmDonePanel"))
        summary = await pg.inner_text("#alarmDoneSummary")
        print("done summary mentions Alarmierungs-Test and % richtig:", "Alarmierungs-Test" in summary and "%" in summary)
        await pg.click("#alarmDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#alarmOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#alarmReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#alarmPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#alarmPauseBtn"))
        await pg.click("#alarmBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#alarmDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#alarmOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#alarmDifficultyRow [data-alarm-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#alarmOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#alarmDifficultyRow [data-alarm-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
