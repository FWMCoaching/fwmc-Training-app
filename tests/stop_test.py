import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Stopp-Signal-Test: twenty-second exercise added under the autonomous
# "Test" section, picked from the Recherche-Backlog (candidate #6, the
# stop-signal paradigm - Logan, Cowan & Davis, 1984; Verbruggen & Logan,
# 2008). Most trials are a simple choice-RT task (tap left/right matching
# a shown arrow); on ~25% of trials the arrow turns red shortly after
# appearing (the Stop-Signal-Delay, SSD) and the client must withhold the
# already-initiated tap. SSD rises after a successful stop, falls after a
# failed one, staircasing toward ~50% success so SSRT can be estimated
# (mean Go-RT minus the converged SSD). Distinct from Go/No-Go: here every
# trial starts as an identical Go arrow, the stop signal (when present)
# arrives AFTER the response has typically already begun, testing
# cancelling a response in flight rather than deciding not to start one.

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
        print("Stop card visible:", await pg.is_visible("#stopOpenBtn"))
        await pg.click("#stopOpenBtn"); await pg.wait_for_timeout(150)
        print("stopReady visible:", await pg.is_visible("#stopReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#stopAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#stopBgColorPicker .color-swatch").count())
        await pg.click('#stopBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        await pg.fill("#stopBgIntensitySlider", "0.6"); await pg.dispatch_event("#stopBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#stopBgIntensityValue")))

        # "leicht" = longest response window, so a slow Playwright click
        # still reliably lands as a normal Go tap rather than a timeout.
        await pg.click('#stopDifficultyRow [data-stop-diff="leicht"]'); await pg.wait_for_timeout(60)
        print("leicht marked active:", "active" in (await pg.get_attribute('#stopDifficultyRow [data-stop-diff="leicht"]', "class") or ""))
        await pg.click("#stopReadyStartBtn"); await pg.wait_for_timeout(200)
        print("stopPlayer visible:", await pg.is_visible("#stopPlayer"))
        progress = await pg.inner_text("#stopProgressEl")
        print("progress starts at 0/64:", "0/64" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('stopStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=8000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#stopProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_arrow(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                txt = await pg.inner_text("#stopArrow")
                if txt in ("←", "→"):
                    return txt
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def wait_for_signal(max_ms=2000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if "stop-signal" in (await pg.get_attribute("#stopArrow", "class") or ""):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- watch several trials, tapping the correct direction every time,
        # unless a stop signal (red arrow) appears - then withhold ---
        n_go_correct = 0
        n_stop_seen = 0
        n_stop_withheld = 0
        for _ in range(10):
            progress = await wait_for_progress_change(progress)
            arrow = await wait_for_arrow()
            if arrow is None:
                continue
            btn = "#stopLeftBtn" if arrow == "←" else "#stopRightBtn"
            became_red = await wait_for_signal(max_ms=250)
            if became_red:
                n_stop_seen += 1
                # withhold - just wait out the trial without tapping
                await pg.wait_for_timeout(1300)
                n_stop_withheld += 1
            else:
                await pg.click(btn); await pg.wait_for_timeout(60)
                n_go_correct += 1
        print("saw at least one stop-signal (red arrow) trial within 10 trials:", n_stop_seen >= 1)
        print("go trials answered with correct-direction taps:", n_go_correct >= 5)

        # --- deliberately tap during a stop trial to trigger a failed stop ---
        got_stop_trial = False
        for _ in range(15):
            progress = await wait_for_progress_change(progress)
            arrow = await wait_for_arrow()
            if arrow is None:
                continue
            became_red = await wait_for_signal(max_ms=250)
            if became_red:
                btn = "#stopLeftBtn" if arrow == "←" else "#stopRightBtn"
                await pg.click(btn); await pg.wait_for_timeout(80)
                got_stop_trial = True
                break
            else:
                btn = "#stopLeftBtn" if arrow == "←" else "#stopRightBtn"
                await pg.click(btn); await pg.wait_for_timeout(60)
        print("found and tapped during a stop-signal trial:", got_stop_trial)
        if got_stop_trial:
            print("tapping during a stop signal marks the button 'wrong':", "wrong" in (await pg.get_attribute("#stopLeftBtn", "class") or "") or "wrong" in (await pg.get_attribute("#stopRightBtn", "class") or ""))
            print("a failed stop shows the 'Nicht tippen bei Rot!' hint:", "Rot" in (await pg.inner_text("#stopHint")))

        # --- let one go trial fully time out (no tap) ---
        for _ in range(6):
            progress = await wait_for_progress_change(progress)
            arrow = await wait_for_arrow()
            if arrow is None:
                continue
            became_red = await wait_for_signal(max_ms=250)
            if not became_red:
                break
        progress_after_timeout = await wait_for_progress_change(progress, max_ms=3000)
        print("an unanswered go trial times out and advances progress on its own:", progress_after_timeout != progress)
        progress = progress_after_timeout

        # --- pause/resume freezes the stage ---
        await wait_for_arrow()
        await pg.click("#stopPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#stopPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#stopPauseBtn"))
        progress_paused1 = await pg.inner_text("#stopProgressEl")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#stopProgressEl")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click('#stopPauseBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('stopStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#stopResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#stopPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with SSRT/accuracy ---
        await pg.click("#stopBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#stopDonePanel"))
        summary = await pg.inner_text("#stopDoneSummary")
        print("done summary mentions Stopp-Signal-Test and Go-Genauigkeit:", "Stopp-Signal-Test" in summary and "Go-Genauigkeit" in summary)
        await pg.click("#stopDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#stopOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#stopReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#stopPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#stopPauseBtn"))
        await pg.click("#stopBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#stopDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#stopOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#stopDifficultyRow [data-stop-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#stopOpenBtn"); await pg.wait_for_timeout(150)
        print("'schwer' selection survives reload:", "active" in (await pg.get_attribute('#stopDifficultyRow [data-stop-diff="schwer"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
