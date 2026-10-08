import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Daueraufmerksamkeits-Test: twenty-seventh exercise added under the
# autonomous "Test" section, picked from the Recherche-Backlog (candidate
# #14, Psychomotor Vigilance Task / PVT - Dinges & Powell 1985). A simple
# counting-number stimulus appears at random 2-10s intervals with no
# warning cue; the client taps as fast as possible each time. Tapping
# before the stimulus appears is a false start (logged, does not cancel
# the already-scheduled stimulus). Reports mean RT, lapse count/rate
# (RT > 500ms), false starts, and the vigilance decrement (second-half
# mean RT minus first-half mean RT) over a chosen duration (3/5/10 Min).

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
        print("PVT card visible:", await pg.is_visible("#pvtOpenBtn"))
        await pg.click("#pvtOpenBtn"); await pg.wait_for_timeout(150)
        print("pvtReady visible:", await pg.is_visible("#pvtReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#pvtAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#pvtBgColorPicker .color-swatch").count())
        await pg.click('#pvtBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        await pg.fill("#pvtBgIntensitySlider", "0.5"); await pg.dispatch_event("#pvtBgIntensitySlider", "input")
        print("intensity value label updated:", "50 %" in (await pg.inner_text("#pvtBgIntensityValue")))

        await pg.click('#pvtLengthRow [data-pvt-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#pvtLengthRow [data-pvt-length="kurz"]', "class") or ""))
        await pg.click("#pvtReadyStartBtn"); await pg.wait_for_timeout(200)
        print("pvtPlayer visible:", await pg.is_visible("#pvtPlayer"))
        print("progress starts at 0 Reaktionen:", "0 Reaktionen · Kurz" in (await pg.inner_text("#pvtProgressEl")))
        bg_at_start = await pg.evaluate("() => document.getElementById('pvtStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        # --- false start: tapping during the waiting phase never cancels the
        # already-scheduled stimulus, only logs a false start ---
        await pg.click("#pvtStage"); await pg.wait_for_timeout(100)
        print("false start shows the expected hint:", "Zu früh" in (await pg.inner_text("#pvtHint")))
        print("false start briefly flags the display:", "falsestart" in (await pg.get_attribute("#pvtDisplay", "class") or ""))
        await pg.wait_for_timeout(350)
        print("false-start flag clears again:", "falsestart" not in (await pg.get_attribute("#pvtDisplay", "class") or ""))

        async def wait_for_target(max_ms=11000, poll_ms=40):
            waited = 0
            while waited < max_ms:
                cls = await pg.get_attribute("#pvtDisplay", "class") or ""
                if "active" in cls:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: the classic PVT display is a live counting number ---
        print("target eventually appears with no earlier warning:", await wait_for_target())
        await pg.wait_for_timeout(120)
        digit_text = (await pg.inner_text("#pvtDisplay")).strip()
        print("counter shows a live increasing millisecond number:", digit_text.isdigit() and int(digit_text) > 0)
        await pg.click("#pvtStage"); await pg.wait_for_timeout(60)
        feedback_cls = await pg.get_attribute("#pvtDisplay", "class") or ""
        print("tapping the target gives fast/lapse feedback:", ("fast" in feedback_cls) or ("lapse" in feedback_cls))
        print("progress advances to 1 Reaktion (singular):", "1 Reaktion ·" in (await pg.inner_text("#pvtProgressEl")))
        await pg.wait_for_timeout(750)  # let the feedback pause elapse before the next trial

        # --- four more trials to clear the min-resolved(5) gate ---
        for _ in range(4):
            await wait_for_target()
            await pg.wait_for_timeout(80)
            await pg.click("#pvtStage")
            await pg.wait_for_timeout(750)

        progress_after = await pg.inner_text("#pvtProgressEl")
        print("progress reached 5 reactions:", "5 Reaktionen" in progress_after)

        # --- pause/resume freezes the stage, even mid-wait ---
        progress_before_pause = await pg.inner_text("#pvtProgressEl")
        await pg.click("#pvtPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#pvtPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#pvtPauseBtn"))
        await pg.wait_for_timeout(900)
        print("progress genuinely frozen while paused:", (await pg.inner_text("#pvtProgressEl")) == progress_before_pause)
        await pg.click('#pvtPauseBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('pvtStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#pvtResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#pvtPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel ---
        await pg.click("#pvtBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#pvtDonePanel"))
        summary = await pg.inner_text("#pvtDoneSummary")
        print("done summary mentions the test name and reaction/lapse wording:", "Daueraufmerksamkeits-Test" in summary and "Ausfall" in summary)
        await pg.click("#pvtDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#pvtOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#pvtReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#pvtPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#pvtPauseBtn"))
        await pg.click("#pvtBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#pvtDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#pvtOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#pvtLengthRow [data-pvt-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#pvtOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#pvtLengthRow [data-pvt-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
