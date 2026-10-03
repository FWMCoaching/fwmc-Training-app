import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Blickfeld-Test (UFOV): fifth exercise added under the autonomous "Test"
# section. Grounded in the Useful Field of View test (Ball & Owsley,
# 1987/1993) - a divided-attention/processing-speed paradigm: a central
# shape (circle/square) and a peripheral target (a diamond among dot
# distractors, at one of 8 compass positions around a ring) flash
# simultaneously, are then backward-masked, and the client reports first
# the central shape, then the peripheral position. The exposure duration is
# the dependent variable, adapted trial-by-trial via a 3-down/1-up
# staircase (three consecutive fully-correct trials shorten it, any error
# lengthens it) - no internal hook exposes the exact numeric staircase
# state, so this test verifies the OBSERVABLE behaviour (correct/wrong
# feedback classes, the true-answer reveal on a miss, pause/resume freezing
# the stage, Beenden-doubles-as-finish, persistence) rather than the exact
# duration progression, the same "verified by reading + behavioural
# checks" approach used for the addon colour/position logic elsewhere in
# this suite. Background colour/intensity (added later, so every
# Test-Bereich exercise gets the same Feineinstellungen control NAT's
# Remember/Blitz/Flash/MOT already have - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints #ufovStage; both the ready screen and the pause overlay
# have their own live picker+slider sharing the same ufovPrefs.

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
        print("UFOV card visible:", await pg.is_visible("#ufovOpenBtn"))
        await pg.click("#ufovOpenBtn"); await pg.wait_for_timeout(150)
        print("ufovReady visible:", await pg.is_visible("#ufovReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#ufovAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#ufovBgColorPicker .color-swatch").count())
        await pg.click('#ufovBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#ufovBgIntensitySlider", "0.6"); await pg.dispatch_event("#ufovBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#ufovBgIntensityValue")))

        # "kurz" = 20 trials, enough to exercise the staircase without a long test run.
        await pg.click('#ufovLengthRow [data-ufov-length="kurz"]'); await pg.wait_for_timeout(60)
        await pg.click("#ufovReadyStartBtn"); await pg.wait_for_timeout(200)
        print("ufovPlayer visible:", await pg.is_visible("#ufovPlayer"))
        progress = await pg.inner_text("#ufovProgressEl")
        print("progress starts at 0/20:", "0/20" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('ufovStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=4000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#ufovProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        # Reads the trial's true answer straight off the stage DURING the
        # brief "stim" phase (before it gets masked/cleared) - the same
        # trick flanker_test.py uses on `.flanker-target`'s text.
        async def read_trial_shape_and_pos(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                cls = await pg.get_attribute("#ufovCenterEl", "class") or ""
                if "shape-circle" in cls or "shape-square" in cls:
                    shape = "circle" if "shape-circle" in cls else "square"
                    target = await pg.query_selector(".ufov-ring-pos.target")
                    pos_id = (await target.get_attribute("id")) if target else None
                    return shape, pos_id
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None, None

        # --- trial 1: answer BOTH sub-tasks correctly ---
        progress = await wait_for_progress_change(progress)
        shape1, posid1 = await read_trial_shape_and_pos()
        print("trial 1 stimulus detected (central shape + peripheral target):", shape1 is not None and posid1 is not None)
        shape_btn = "#ufovShapeCircleBtn" if shape1 == "circle" else "#ufovShapeSquareBtn"
        await pg.wait_for_selector("#ufovShapeBtns:not([hidden])", timeout=3000)
        await pg.click(shape_btn); await pg.wait_for_timeout(80)
        print("correct shape tap marks that button 'correct':", "correct" in (await pg.get_attribute(shape_btn, "class") or ""))
        await pg.wait_for_selector("#ufovRingBtns:not([hidden])", timeout=3000)
        pos_index1 = posid1.replace("ufovRing", "")
        pos_btn = f'#ufovRingBtnField [data-ufov-pos="{pos_index1}"]'
        await pg.click(pos_btn); await pg.wait_for_timeout(80)
        print("correct position tap marks that button 'correct':", "correct" in (await pg.get_attribute(pos_btn, "class") or ""))

        # --- trial 2: answer BOTH sub-tasks wrong on purpose ---
        progress = await wait_for_progress_change(progress)
        shape2, posid2 = await read_trial_shape_and_pos()
        print("trial 2 stimulus detected:", shape2 is not None and posid2 is not None)
        wrong_shape_btn = "#ufovShapeSquareBtn" if shape2 == "circle" else "#ufovShapeCircleBtn"
        correct_shape_btn = "#ufovShapeCircleBtn" if shape2 == "circle" else "#ufovShapeSquareBtn"
        await pg.wait_for_selector("#ufovShapeBtns:not([hidden])", timeout=3000)
        await pg.click(wrong_shape_btn); await pg.wait_for_timeout(80)
        print("wrong shape tap marks that button 'wrong':", "wrong" in (await pg.get_attribute(wrong_shape_btn, "class") or ""))
        print("...and reveals the true shape as 'correct':", "correct" in (await pg.get_attribute(correct_shape_btn, "class") or ""))
        await pg.wait_for_selector("#ufovRingBtns:not([hidden])", timeout=3000)
        pos_index2 = int(posid2.replace("ufovRing", ""))
        wrong_index2 = (pos_index2 + 1) % 8
        wrong_pos_btn = f'#ufovRingBtnField [data-ufov-pos="{wrong_index2}"]'
        correct_pos_btn = f'#ufovRingBtnField [data-ufov-pos="{pos_index2}"]'
        await pg.click(wrong_pos_btn); await pg.wait_for_timeout(80)
        print("wrong position tap marks that button 'wrong':", "wrong" in (await pg.get_attribute(wrong_pos_btn, "class") or ""))
        print("...and reveals the true position as 'correct':", "correct" in (await pg.get_attribute(correct_pos_btn, "class") or ""))

        # --- pause/resume freezes the stage ---
        progress = await wait_for_progress_change(progress)
        await pg.wait_for_timeout(120)
        await pg.click("#ufovPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#ufovPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#ufovPauseBtn"))
        progress_paused1 = await pg.inner_text("#ufovProgressEl")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#ufovProgressEl")
        print("progress frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click('#ufovPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('ufovStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#ufovResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#ufovPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with threshold + accuracy% ---
        # A few more quick (arbitrary-answer) trials so durations.length is
        # comfortably >= 4 by the time Beenden is pressed.
        for _ in range(3):
            await pg.wait_for_selector("#ufovShapeBtns:not([hidden])", timeout=4000)
            await pg.click("#ufovShapeCircleBtn"); await pg.wait_for_timeout(650)
            await pg.wait_for_selector("#ufovRingBtns:not([hidden])", timeout=4000)
            await pg.click('#ufovRingBtnField [data-ufov-pos="0"]'); await pg.wait_for_timeout(650)
        await pg.click("#ufovBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#ufovDonePanel"))
        summary = await pg.inner_text("#ufovDoneSummary")
        print("done summary mentions Blickfeld-Test, Schwelle (ms) and % richtig:",
              "Blickfeld-Test" in summary and "Schwelle" in summary and "ms" in summary and "%" in summary)
        await pg.click("#ufovDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as the others) ---
        await pg.click("#ufovOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#ufovReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#ufovPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#ufovPauseBtn"))
        await pg.click("#ufovBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#ufovDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#ufovOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#ufovLengthRow [data-ufov-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#ufovOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#ufovLengthRow [data-ufov-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
