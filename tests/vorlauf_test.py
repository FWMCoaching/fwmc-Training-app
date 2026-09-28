import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Vorlaufzeit-Test: twenty-first exercise added under the autonomous "Test"
# section, picked from the Recherche-Backlog (candidate #18, Foreperiod-
# Effekt). Grounded in Niemi & Näätänen (1981) - a single always-present
# warning cue (the centre dot turning from hollow to a steady "armed"
# outline) precedes the actual go signal (the dot filling in) by a
# foreperiod that varies randomly trial-to-trial across five fixed steps
# (500-4000ms); the client taps anywhere on the stage the instant the dot
# fills in. Reports mean RT per foreperiod bin plus the "Erwartungseffekt"
# (Ø RT at the shortest two foreperiods minus Ø RT at the longest two) - the
# actual expectancy-curve outcome measure this paradigm exists to reveal.
# Distinct from the already-existing Alarmierungs-Test: that one holds the
# foreperiod FIXED and varies whether a cue occurs at all (cued vs.
# uncued); here the SAME cue is present every trial and the foreperiod
# LENGTH itself is the manipulated variable. A tap during the "armed" wait
# (before the dot fills in) is a false start, tracked separately.

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
        print("Vorlauf card visible:", await pg.is_visible("#vorlaufOpenBtn"))
        await pg.click("#vorlaufOpenBtn"); await pg.wait_for_timeout(150)
        print("vorlaufReady visible:", await pg.is_visible("#vorlaufReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#vorlaufAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#vorlaufBgColorPicker .color-swatch").count())
        await pg.click('#vorlaufBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#vorlaufBgIntensitySlider", "0.6"); await pg.dispatch_event("#vorlaufBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#vorlaufBgIntensityValue")))

        await pg.click('#vorlaufLengthRow [data-vorlauf-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#vorlaufLengthRow [data-vorlauf-length="kurz"]', "class") or ""))
        await pg.click("#vorlaufReadyStartBtn"); await pg.wait_for_timeout(200)
        print("vorlaufPlayer visible:", await pg.is_visible("#vorlaufPlayer"))
        progress = await pg.inner_text("#vorlaufProgressEl")
        print("progress starts at 0/20:", "0/20" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('vorlaufStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=8000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#vorlaufProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_armed(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                cls = await pg.get_attribute("#vorlaufDot", "class") or ""
                if "armed" in cls:
                    return True
                if "target" in cls:
                    return False
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def wait_for_target(max_ms=6000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                cls = await pg.get_attribute("#vorlaufDot", "class") or ""
                if "target" in cls:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: wait for the warning cue, then correct response on target ---
        progress = await wait_for_progress_change(progress)
        saw_armed = await wait_for_armed()
        print("trial 1 showed the 'armed' warning cue before the target:", saw_armed is True)
        got_target = await wait_for_target()
        print("trial 1's target (filled dot) appeared:", got_target)
        await pg.click("#vorlaufTapzone"); await pg.wait_for_timeout(80)

        # --- trial 2: deliberately tap during the 'armed' wait (false start) ---
        progress = await wait_for_progress_change(progress)
        await wait_for_armed()
        await pg.click("#vorlaufTapzone"); await pg.wait_for_timeout(80)
        print("tapping during the armed wait marks the dot 'falsestart':", "falsestart" in (await pg.get_attribute("#vorlaufDot", "class") or ""))
        print("a false start shows the 'Zu früh!' hint:", "früh" in (await pg.inner_text("#vorlaufHint")))

        # --- trial 3: let the response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        await wait_for_target()
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#vorlaufHint")))
        progress = progress4

        # --- trial 4: a normal, correct response (to clear the 4-resolved threshold) ---
        progress = await wait_for_progress_change(progress)
        await wait_for_armed()
        await wait_for_target()
        await pg.click("#vorlaufTapzone"); await pg.wait_for_timeout(80)

        # --- pause/resume freezes the stage ---
        await wait_for_progress_change(progress)
        await wait_for_armed()
        await pg.click("#vorlaufPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#vorlaufPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#vorlaufPauseBtn"))
        cls_paused1 = await pg.get_attribute("#vorlaufDot", "class")
        progress_paused1 = await pg.inner_text("#vorlaufProgressEl")
        await pg.wait_for_timeout(700)
        cls_paused2 = await pg.get_attribute("#vorlaufDot", "class")
        progress_paused2 = await pg.inner_text("#vorlaufProgressEl")
        print("stage genuinely frozen while paused:", cls_paused1 == cls_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#vorlaufPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('vorlaufStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#vorlaufResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#vorlaufPauseOverlay"))
        # a tap right after resume completes whatever trial phase we resumed into
        await wait_for_target()
        await pg.click("#vorlaufTapzone"); await pg.wait_for_timeout(120)

        # --- Beenden mid-run with progress -> done panel with Ø/Erwartungseffekt ---
        await pg.click("#vorlaufBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#vorlaufDonePanel"))
        summary = await pg.inner_text("#vorlaufDoneSummary")
        print("done summary mentions Vorlaufzeit-Test and Ø:", "Vorlaufzeit-Test" in summary and "Ø" in summary)
        await pg.click("#vorlaufDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#vorlaufOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#vorlaufReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#vorlaufPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#vorlaufPauseBtn"))
        await pg.click("#vorlaufBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#vorlaufDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#vorlaufOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#vorlaufLengthRow [data-vorlauf-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#vorlaufOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#vorlaufLengthRow [data-vorlauf-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
