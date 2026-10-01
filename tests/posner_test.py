import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Hinweisreiz-Test (Posner-Cueing): sixth exercise added under the autonomous
# "Test" section. Classic Posner cueing task (Posner, 1980) - a cue briefly
# highlights one of two side boxes, then a target dot appears in the cued box
# on most trials ("valid", 80%) or the other box on a minority ("invalid",
# 20%). The client must tap the box where the dot ACTUALLY appears, not the
# one that merely lit up as a cue. Fixed 40-trial run (POSNER_TRIAL_COUNT),
# no "Bei Fehler"/level progression - reports accuracy % + average valid/
# invalid reaction time + the "Umlenkungs-Kosten" (cueing/validity effect)
# instead, the actual outcome measure this paradigm exists to surface.
# Background colour/intensity (added later, so every Test-Bereich exercise
# gets the same Feineinstellungen control NAT's Remember/Blitz/Flash/MOT
# already have - see CLAUDE.md's Established patterns for the scope
# decision, minus their transfer/preset-save machinery) tints #posnerStage;
# both the ready screen and the pause overlay have their own live
# picker+slider sharing the same posnerPrefs.
#
# Timing note: like Flanker/Go-No-Go, the feedback colour on a tapped box
# stays up for the rest of diff.responseMs regardless of how fast the client
# answers, so "a new trial started" is only reliably detected via the
# progress counter advancing, not via the target dot simply reappearing.

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
        print("Posner card visible:", await pg.is_visible("#posnerOpenBtn"))
        await pg.click("#posnerOpenBtn"); await pg.wait_for_timeout(150)
        print("posnerReady visible:", await pg.is_visible("#posnerReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#posnerAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#posnerBgColorPicker .color-swatch").count())
        await pg.click('#posnerBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#posnerBgIntensitySlider", "0.6"); await pg.dispatch_event("#posnerBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#posnerBgIntensityValue")))

        # "schwer" = shortest cue/SOA/response window, so a short test window
        # still reliably samples several trials, including a timeout.
        await pg.click('#posnerDifficultyRow [data-posner-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#posnerReadyStartBtn"); await pg.wait_for_timeout(200)
        print("posnerPlayer visible:", await pg.is_visible("#posnerPlayer"))
        progress = await pg.inner_text("#posnerProgressEl")
        print("progress starts at 0/40:", "0/40" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('posnerStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#posnerProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_cue(max_ms=1500, poll_ms=10):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".posner-box.cued").count() == 1:
                    is_left = "cued" in (await pg.get_attribute("#posnerLeftBtn", "class") or "")
                    return "left" if is_left else "right"
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def wait_for_target(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".posner-dot.show").count() == 1:
                    is_left = "show" in (await pg.get_attribute("#posnerLeftDot", "class") or "")
                    return "left" if is_left else "right"
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        # --- trial 1: the cue itself appears, then the target, then a correct response ---
        progress = await wait_for_progress_change(progress)
        cue1 = await wait_for_cue()
        print("trial 1's cue lit up exactly one box:", cue1 is not None)
        d1 = await wait_for_target()
        print("trial 1's target dot appeared in exactly one box:", d1 is not None)
        btn1 = "#posnerLeftBtn" if d1 == "left" else "#posnerRightBtn"
        await pg.click(btn1); await pg.wait_for_timeout(80)
        print("tapping the box the dot actually appeared in marks it 'correct':", "correct" in (await pg.get_attribute(btn1, "class") or ""))

        # --- trial 2: deliberately tap the OTHER box (wrong side) ---
        progress = await wait_for_progress_change(progress)
        d2 = await wait_for_target()
        print("trial 2's target dot appeared:", d2 is not None)
        wrong_btn = "#posnerRightBtn" if d2 == "left" else "#posnerLeftBtn"
        await pg.click(wrong_btn); await pg.wait_for_timeout(80)
        print("tapping the wrong side marks that button 'wrong':", "wrong" in (await pg.get_attribute(wrong_btn, "class") or ""))
        print("a wrong tap shows the 'Falsche Seite!' hint:", "Falsche" in (await pg.inner_text("#posnerHint")))

        # --- trial 3: let its response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        d3 = await wait_for_target()
        print("trial 3's target dot appeared:", d3 is not None)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#posnerHint")))
        progress = progress4

        # --- pause/resume freezes the stage ---
        await wait_for_target()
        await pg.click("#posnerPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#posnerPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#posnerPauseBtn"))
        html_paused1 = await pg.inner_html("#posnerStage")
        progress_paused1 = await pg.inner_text("#posnerProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#posnerStage")
        progress_paused2 = await pg.inner_text("#posnerProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#posnerPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('posnerStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#posnerResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#posnerPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy% ---
        # Let a couple more trials pass (unanswered, i.e. more timeouts) so
        # resolved count is comfortably >= 4 by the time Beenden is pressed.
        await pg.wait_for_timeout(2500)
        await pg.click("#posnerBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#posnerDonePanel"))
        summary = await pg.inner_text("#posnerDoneSummary")
        print("done summary mentions Hinweisreiz-Test and % richtig:", "Hinweisreiz-Test" in summary and "%" in summary)
        await pg.click("#posnerDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as Flanker) ---
        await pg.click("#posnerOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#posnerReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#posnerPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#posnerPauseBtn"))
        await pg.click("#posnerBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#posnerDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#posnerOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#posnerDifficultyRow [data-posner-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#posnerOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#posnerDifficultyRow [data-posner-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
