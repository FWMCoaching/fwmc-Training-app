import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Wahlreaktionstest (Hick's Law): thirteenth exercise added under the
# autonomous "Test" section. Grounded in Hick's Law (Hick, 1952) - choice
# reaction time rises linearly with log2(N), the number of possible
# stimulus-response alternatives. A block of N boxes is shown (N=2, then 4,
# then 8, always ascending); each trial one box lights up and the client
# taps that SAME box as fast as possible. Self-paced per trial (like
# Suchtest), only a 5s safety-net timeout advances an unanswered trial.
# Reports accuracy% plus average RT per block size and the Hick-Steigung
# (slope, ms/Bit) between the 2- and 8-choice blocks - the actual outcome
# measure this paradigm exists to surface.
# Background colour/intensity (added later, fifth batch of the same
# Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/Rotation/
# Merkspanne/Simon/Suchtest/Doppelziel/Antizip - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints the outer #hickStage. Both the ready screen and the pause
# overlay have their own live picker+slider sharing the same hickPrefs.

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
        print("Wahlreaktionstest card visible:", await pg.is_visible("#hickOpenBtn"))
        await pg.click("#hickOpenBtn"); await pg.wait_for_timeout(150)
        print("hickReady visible:", await pg.is_visible("#hickReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#hickAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#hickBgColorPicker .color-swatch").count())
        await pg.click('#hickBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#hickBgIntensitySlider", "0.6"); await pg.dispatch_event("#hickBgIntensitySlider", "input")
        print("intensity value label updated:", "60 %" in (await pg.inner_text("#hickBgIntensityValue")))

        # "kurz" = 3 reps * (2+4+8) = 42 trials, fast enough for a short test run.
        await pg.click('#hickLengthRow [data-hick-length="kurz"]'); await pg.wait_for_timeout(60)
        await pg.click("#hickReadyStartBtn"); await pg.wait_for_timeout(200)
        print("hickPlayer visible:", await pg.is_visible("#hickPlayer"))
        progress = await pg.inner_text("#hickProgressEl")
        print("progress starts at 0/42:", "0/42" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('hickStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=7000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#hickProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_hint_contains(text, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#hickHint")
                if text in cur:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_lit(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                idx = await pg.eval_on_selector_all("#hickBoxesGrid .hick-box", "(els) => els.findIndex(e => e.classList.contains('lit'))")
                if idx >= 0:
                    return idx
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return -1

        # --- block 1 intro shows before the first trial: "Block 1 von 3: 2 Möglichkeiten" ---
        block1_hint_shown = await wait_for_hint_contains("Block 1 von 3: 2")
        print("block 1 intro hint shown ('2 Möglichkeiten'):", block1_hint_shown)
        n_boxes_block1 = await pg.locator("#hickBoxesGrid .hick-box").count()
        print("block 1 renders exactly 2 boxes:", n_boxes_block1 == 2)

        # --- trial 1: tap the CORRECT (lit) box ---
        lit_idx = await wait_for_lit()
        print("a box lights up for trial 1:", lit_idx >= 0)
        lit_loc = pg.locator("#hickBoxesGrid .hick-box").nth(lit_idx)
        await lit_loc.click(); await pg.wait_for_timeout(60)
        print("tapping the lit box marks it 'correct':", "correct" in (await lit_loc.get_attribute("class") or ""))

        # --- trial 2: deliberately tap the WRONG box ---
        # (re-baseline "progress" to its REAL current value first - it was
        # last captured before trial 1's own advance, so comparing against
        # that stale value would return instantly instead of waiting)
        progress = await pg.inner_text("#hickProgressEl")
        progress = await wait_for_progress_change(progress)
        lit_idx2 = await wait_for_lit()
        wrong_idx = 1 - lit_idx2  # the only other box in a 2-choice block
        wrong_loc = pg.locator("#hickBoxesGrid .hick-box").nth(wrong_idx)
        correct_loc2 = pg.locator("#hickBoxesGrid .hick-box").nth(lit_idx2)
        await wrong_loc.click(); await pg.wait_for_timeout(60)
        print("tapping the wrong box marks it 'wrong':", "wrong" in (await wrong_loc.get_attribute("class") or ""))
        print("a wrong tap also reveals the correct box:", "correct" in (await correct_loc2.get_attribute("class") or ""))
        print("a wrong tap shows the 'Daneben!' hint:", "Daneben" in (await pg.inner_text("#hickHint")))

        # --- trial 3: let the 5s safety-net timeout elapse without tapping ---
        progress = await wait_for_progress_change(progress)
        await wait_for_lit()
        timed_out_hint_shown = await wait_for_hint_contains("Verpasst")
        print("a timed-out trial shows the 'Verpasst!' hint:", timed_out_hint_shown)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances on its own:", progress4 != progress)
        progress = progress4

        # --- pause/resume freezes the stage mid-run ---
        await wait_for_lit()
        await pg.click("#hickPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#hickPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#hickPauseBtn"))
        html_paused1 = await pg.inner_html("#hickBoxesGrid")
        progress_paused1 = await pg.inner_text("#hickProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#hickBoxesGrid")
        progress_paused2 = await pg.inner_text("#hickProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#hickPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('hickStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#hickResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#hickPauseOverlay"))
        lit_idx_r = await wait_for_lit()
        if lit_idx_r >= 0:
            r_loc = pg.locator("#hickBoxesGrid .hick-box").nth(lit_idx_r)
            await r_loc.click(); await pg.wait_for_timeout(60)
            print("tap after resume still resolves the trial:", "correct" in (await r_loc.get_attribute("class") or ""))
        else:
            print("tap after resume still resolves the trial:", False)
        progress = await wait_for_progress_change(progress)

        # --- fast-forward through the rest of block 1 (2-choice, 6 trials total, 4
        # already resolved above) into block 2 by letting the remaining 2 trials
        # time out on their own (each up to HICK_TIMEOUT_MS=5000ms + ISI + feedback,
        # so a generous window) - this also brings the resolved-trial count up to
        # HICK_MIN_RESOLVED (6) for the Beenden check right after ---
        block2_hint_shown = await wait_for_hint_contains("Block 2 von 3: 4", max_ms=16000)
        print("block 2 intro hint shown ('4 Möglichkeiten') after block 1 finishes:", block2_hint_shown)
        n_boxes_block2 = await pg.locator("#hickBoxesGrid .hick-box").count()
        print("block 2 renders exactly 4 boxes:", n_boxes_block2 == 4)

        # --- Beenden mid-run with progress -> done panel with accuracy% (no full slope yet, block 3/N=8 never reached) ---
        await pg.click("#hickBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#hickDonePanel"))
        summary = await pg.inner_text("#hickDoneSummary")
        print("done summary mentions Wahlreaktionstest and % richtig:", "Wahlreaktionstest" in summary and "%" in summary)
        print("done summary mentions the 2-choice block average:", "2 Möglichkeiten" in summary)
        await pg.click("#hickDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#hickOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#hickReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#hickPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#hickPauseBtn"))
        await pg.click("#hickBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#hickDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#hickOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#hickLengthRow [data-hick-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#hickOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#hickLengthRow [data-hick-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
