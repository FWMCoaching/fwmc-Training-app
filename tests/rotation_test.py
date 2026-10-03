import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Rotationstest (Mentale Rotation): seventh exercise added under the
# autonomous "Test" section. Classic mental-rotation/character-rotation
# chronometric paradigm (Cooper & Shepard, 1973) - a letter or digit is
# shown rotated out of upright, either in its normal form or mirror-
# reversed; the client judges "Normal" or "Gespiegelt" as fast as possible.
# 32-trial fixed run (8 angles x normal/mirrored x 2 repeats), no "Bei
# Fehler"/level progression - reports accuracy% + average RT near vs. far
# from upright + their difference ("Rotations-Kosten", the actual angular-
# disparity effect this paradigm exists to surface). Background colour/
# intensity (added later, third batch of the same Test-Bereich effort as
# Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints #rotationStage; both the ready screen and the pause
# overlay have their own live picker+slider sharing the same rotationPrefs.
#
# Timing note: like Flanker/Posner, the feedback colour on the tapped
# button stays up for the rest of diff.responseMs, so "a new trial
# started" is only reliably detected via the progress counter advancing,
# not via the character simply reappearing.

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
        print("Rotation card visible:", await pg.is_visible("#rotationOpenBtn"))
        await pg.click("#rotationOpenBtn"); await pg.wait_for_timeout(150)
        print("rotationReady visible:", await pg.is_visible("#rotationReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#rotationAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#rotationBgColorPicker .color-swatch").count())
        await pg.click('#rotationBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#rotationBgIntensitySlider", "0.6"); await pg.dispatch_event("#rotationBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#rotationBgIntensityValue")))

        # "schwer" = shortest response window, so a short test window still
        # reliably samples several trials, including a timeout.
        await pg.click('#rotationDifficultyRow [data-rotation-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#rotationReadyStartBtn"); await pg.wait_for_timeout(200)
        print("rotationPlayer visible:", await pg.is_visible("#rotationPlayer"))
        progress = await pg.inner_text("#rotationProgressEl")
        print("progress starts at 0/32:", "0/32" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('rotationStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#rotationProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_char(max_ms=2500, poll_ms=15):
            waited = 0
            while waited < max_ms:
                txt = await pg.inner_text("#rotationCharEl")
                if txt.strip():
                    return txt
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        # --- trial 1: character appears, then a tap (correct or not, doesn't matter here) advances ---
        char1 = await wait_for_char()
        print("first character appeared:", bool(char1))
        transform1 = await pg.get_attribute("#rotationCharEl", "style")
        print("character has a rotate() transform applied:", "rotate(" in (transform1 or ""))
        await pg.click("#rotationNormalBtn"); await pg.wait_for_timeout(80)
        has_feedback = ("correct" in (await pg.get_attribute("#rotationNormalBtn", "class") or "")) or \
                       ("wrong" in (await pg.get_attribute("#rotationNormalBtn", "class") or ""))
        print("tapped button shows correct/wrong feedback immediately:", has_feedback)
        progress = await wait_for_progress_change(progress)
        print("progress advanced after trial 1:", "1/32" in progress)

        # --- trial 2: a timeout (no tap) still advances and counts as incorrect ---
        char2 = await wait_for_char()
        print("second character appeared:", bool(char2))
        progress = await wait_for_progress_change(progress, max_ms=3000)
        print("progress advanced after a timeout (no tap):", "2/32" in progress)

        # --- pause/resume freezes the stage, no character stays visible mid-pause ---
        await pg.click("#rotationPauseBtn"); await pg.wait_for_timeout(120)
        print("pause overlay visible:", await pg.is_visible("#rotationPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#rotationPauseBtn"))
        progress_frozen_1 = await pg.inner_text("#rotationProgressEl")
        await pg.wait_for_timeout(700)
        progress_frozen_2 = await pg.inner_text("#rotationProgressEl")
        print("progress frozen while paused:", progress_frozen_1 == progress_frozen_2)
        await pg.click('#rotationPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('rotationStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#rotationResumeBtn"); await pg.wait_for_timeout(120)
        print("pause overlay hidden after resume:", await pg.is_hidden("#rotationPauseOverlay"))

        # --- Beenden with only a couple of resolved trials skips the done panel (< 4 threshold) ---
        await pg.click("#rotationBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with too few resolved trials returns to testHome, no done panel:", await pg.is_visible("#testHome") and await pg.is_hidden("#rotationDonePanel"))

        # --- full run to the done panel ---
        await pg.click("#rotationOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#rotationDifficultyRow [data-rotation-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#rotationReadyStartBtn"); await pg.wait_for_timeout(200)

        async def wait_for_done_panel(max_ms=4000, poll_ms=30):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible("#rotationDonePanel"):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        progress = "0/32"
        for i in range(32):
            await wait_for_char()
            # alternate guesses so we don't rely on always being right
            btn = "#rotationNormalBtn" if i % 2 == 0 else "#rotationMirroredBtn"
            await pg.click(btn)
            if i < 31:
                # progress text advances to the NEXT trial's "n/32" while it
                # is shown - true for every trial except the very last one,
                # where the index rolls over into rotationFinish() instead
                # of a new progress line (nothing to wait for there but the
                # done panel itself, checked right after this loop).
                progress = await wait_for_progress_change(progress, max_ms=3000)
        await wait_for_done_panel()
        print("done panel shown after all 32 trials:", await pg.is_visible("#rotationDonePanel"))
        summary = await pg.inner_text("#rotationDoneSummary")
        print("done summary mentions Rotationstest:", "Rotationstest" in summary)
        print("done summary reports an accuracy percentage:", "%" in summary)
        await pg.click("#rotationDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome after done panel:", await pg.is_visible("#testHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
