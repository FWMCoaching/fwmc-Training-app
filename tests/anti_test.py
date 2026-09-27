import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Gegenrichtungs-Test (Antisakkaden-Prinzip): seventeenth exercise added
# under the autonomous "Test" section. Grounded in the antisaccade task
# (Hallett, 1978) - a dot appears left or right of a central fixation
# cross; in Block 1 ("Pro") the client taps the SAME side (the automatic,
# compatible response), in Block 2 ("Anti") the OPPOSITE side, following
# the established MANUAL/keypress adaptation of the paradigm (Kane,
# Bleckley, Conway & Engle, 2001). Reports accuracy% plus average RT per
# block and their difference as "Hemm-Kosten" (inhibition cost, ms).
# Self-paced per trial (like Regelwechsel-Test/Suchtest/Hick), only a
# generous safety-net timeout advances an unanswered trial. 16 Pro + 16
# Anti = 32 trials total.
# Background colour/intensity (added later, sixth and final batch of the
# same Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/
# Rotation/Merkspanne/Simon/Suchtest/Doppelziel/Antizipationstest/Hick/
# Corsi/Reaktionsfeld/Regelwechsel-Test - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints the outer #antiStage. Both the ready screen and the
# pause overlay have their own live picker+slider sharing the same
# antiPrefs.

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
        print("Gegenrichtungs-Test card visible:", await pg.is_visible("#antiOpenBtn"))
        await pg.click("#antiOpenBtn"); await pg.wait_for_timeout(150)
        print("antiReady visible:", await pg.is_visible("#antiReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#antiAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#antiBgColorPicker .color-swatch").count())
        await pg.click('#antiBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#antiBgIntensitySlider", "0.6"); await pg.dispatch_event("#antiBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#antiBgIntensityValue")))

        # "schwer" = shortest ISI/timeout, fastest test run (block-intro
        # delay is fixed regardless of difficulty, see ANTI_BLOCK_INTRO_MS).
        await pg.click('#antiDifficultyRow [data-anti-diff="schwer"]'); await pg.wait_for_timeout(60)
        print("'schwer' selected:", "active" in (await pg.get_attribute('#antiDifficultyRow [data-anti-diff="schwer"]', "class") or ""))
        await pg.click("#antiReadyStartBtn"); await pg.wait_for_timeout(150)
        print("antiPlayer visible:", await pg.is_visible("#antiPlayer"))
        print("progress starts at 0/32:", "0/32" in (await pg.inner_text("#antiProgressEl")))
        bg_at_start = await pg.evaluate("() => document.getElementById('antiStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#antiProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_hint_contains(text, max_ms=5000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#antiHint")
                if text in cur:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_dot_side(max_ms=5000, poll_ms=20):
            waited = 0
            while waited < max_ms:
                left_show = "show" in (await pg.get_attribute("#antiDotLeft", "class") or "")
                right_show = "show" in (await pg.get_attribute("#antiDotRight", "class") or "")
                if left_show:
                    return "left"
                if right_show:
                    return "right"
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def read_trial_context():
            side = await wait_for_dot_side()
            rule = (await pg.inner_text("#antiRule")).strip()
            correct_side = None
            if side is not None:
                is_pro = "GLEICHE" in rule
                correct_side = side if is_pro else ("right" if side == "left" else "left")
            return side, rule, correct_side

        # Resolves whichever trial is CURRENTLY on screen, re-baselining
        # progress right at the point of action - same pattern (and same
        # reason) as Regelwechsel-Test's own test.
        async def resolve_trial(action):
            side, rule, correct_side = await read_trial_context()
            prev_progress = await pg.inner_text("#antiProgressEl")
            tapped_loc = correct_loc = None
            if action in ("correct", "wrong"):
                tap_side = correct_side if action == "correct" else ("right" if correct_side == "left" else "left")
                tapped_loc = pg.locator("#antiLeftBtn" if tap_side == "left" else "#antiRightBtn")
                correct_loc = pg.locator("#antiLeftBtn" if correct_side == "left" else "#antiRightBtn")
                await tapped_loc.click(); await pg.wait_for_timeout(60)
            return (side, rule, correct_side), tapped_loc, correct_loc, prev_progress

        # --- Block 1 intro shown before the very first trial (the initial
        # "Bereit? …" hint is only replaced once antiNextTrial actually
        # fires, 1000ms after start - wait for that transition first) ---
        await pg.wait_for_timeout(1200)
        block1_hint = await pg.inner_text("#antiHint")
        print("Block 1 intro mentions 'Block 1':", "Block 1" in block1_hint)
        print("rule banner shows 'GLEICHE SEITE' during Block 1:", "GLEICHE SEITE" in (await pg.inner_text("#antiRule")))

        # --- trial 1 (Block 1/Pro): tap CORRECT (same side as the dot) ---
        (side, rule, correct_side), tapped_loc, correct_loc, prev_progress = await resolve_trial("correct")
        print("a dot appears on a valid side:", side in ("left", "right"))
        print("Pro block: correct side == dot side:", correct_side == side)
        print("tapping the correct side marks it 'correct':", "correct" in (await tapped_loc.get_attribute("class") or ""))
        await wait_for_progress_change(prev_progress)

        # --- trial 2 (Block 1/Pro): deliberately tap the WRONG side ---
        _, tapped_loc, correct_loc, prev_progress = await resolve_trial("wrong")
        print("tapping the wrong side marks it 'wrong':", "wrong" in (await tapped_loc.get_attribute("class") or ""))
        print("a wrong tap also reveals the correct side:", "correct" in (await correct_loc.get_attribute("class") or ""))
        print("a wrong tap shows the 'Daneben!' hint:", "Daneben" in (await pg.inner_text("#antiHint")))
        await wait_for_progress_change(prev_progress)

        # --- trial 3: let the safety-net timeout elapse without tapping ---
        _, _, _, prev_progress = await resolve_trial("timeout")
        timed_out_hint_shown = await wait_for_hint_contains("Verpasst")
        print("a timed-out trial shows the 'Verpasst!' hint:", timed_out_hint_shown)
        after_timeout_progress = await wait_for_progress_change(prev_progress)
        print("an unanswered trial times out and advances on its own:", after_timeout_progress != prev_progress)

        # --- pause/resume freezes the stage mid-trial ---
        await wait_for_dot_side()
        await pg.click("#antiPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#antiPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#antiPauseBtn"))
        progress_paused1 = await pg.inner_text("#antiProgressEl")
        left_paused1 = await pg.get_attribute("#antiDotLeft", "class")
        right_paused1 = await pg.get_attribute("#antiDotRight", "class")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#antiProgressEl")
        left_paused2 = await pg.get_attribute("#antiDotLeft", "class")
        right_paused2 = await pg.get_attribute("#antiDotRight", "class")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2 and left_paused1 == left_paused2 and right_paused1 == right_paused2)
        await pg.click('#antiPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('antiStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#antiResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#antiPauseOverlay"))

        # answer this (already-visible, now-resumed) trial correctly
        _, tapped_loc, _, prev_progress = await resolve_trial("correct")
        print("tap after resume still resolves the trial:", "correct" in (await tapped_loc.get_attribute("class") or ""))
        await wait_for_progress_change(prev_progress)

        # --- answer through the rest of Block 1 (12 more trials, 16 total)
        # and into Block 2 (Anti) far enough to pick up a real Hemm-Kosten
        # number - resolve_trial() re-reads the rule banner every trial, so
        # it automatically flips its own "correct" definition the instant
        # Block 2 starts. ---
        for _ in range(12):
            _, tapped_loc, _, prev_progress = await resolve_trial("correct")
            await wait_for_progress_change(prev_progress)

        # --- Block 2 intro ---
        block2_hint = await pg.inner_text("#antiHint")
        print("Block 2 intro mentions 'Block 2':", "Block 2" in block2_hint)
        print("rule banner switches to 'GEGENTEIL' for Block 2:", "GEGENTEIL" in (await pg.inner_text("#antiRule")))

        (side2, rule2, correct_side2), tapped_loc, correct_loc, prev_progress = await resolve_trial("correct")
        print("Anti block: correct side is the OPPOSITE of the dot side:", correct_side2 != side2)
        print("tapping the (opposite) correct side marks it 'correct' in Block 2:", "correct" in (await tapped_loc.get_attribute("class") or ""))
        await wait_for_progress_change(prev_progress)

        for _ in range(8):
            _, tapped_loc, _, prev_progress = await resolve_trial("correct")
            await wait_for_progress_change(prev_progress)

        # --- Beenden mid-run with enough resolved trials (both blocks
        # represented) -> done panel with accuracy%, both RT averages and
        # a real Hemm-Kosten number ---
        await pg.click("#antiBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#antiDonePanel"))
        summary = await pg.inner_text("#antiDoneSummary")
        print("done summary mentions Gegenrichtungs-Test and % richtig:", "Gegenrichtungs-Test" in summary and "% richtig" in summary)
        print("done summary reports both RT averages:", "gleiche Seite" in summary and "Gegenteil" in summary)
        print("done summary reports Hemm-Kosten:", "Hemm-Kosten" in summary)
        print("first-ever run records a new best:", "Neue Bestleistung!" in summary)
        await pg.click("#antiDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- best-hint now shows on the ready screen ---
        await pg.click("#antiOpenBtn"); await pg.wait_for_timeout(150)
        best_hint = await pg.inner_text("#antiReadyBestHint")
        print("ready screen shows a best-hint after a completed run:", "Hemm-Kosten" in best_hint and "ms" in best_hint)

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#antiReadyStartBtn"); await pg.wait_for_timeout(150)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#antiPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#antiPauseBtn"))
        await pg.click("#antiBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#antiDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#antiOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#antiDifficultyRow [data-anti-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#antiOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#antiDifficultyRow [data-anti-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
