import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Suchtest (Visuelle Suche): tenth exercise added under the autonomous "Test"
# section. Classic visual-search paradigm / Treisman & Gelade's Feature
# Integration Theory (1980) - a single target hides among distractors; in
# "Merkmalssuche" (feature search) the target is the only item that differs
# by ONE feature (a red circle among grey circles) and pops out instantly; in
# "Verbindungssuche" (conjunction search) the target is a red SQUARE among
# red circles + grey squares - no single feature is unique, so it takes
# longer to find, especially as the set size grows. Unlike every other
# fixed-response-window Test exercise (Simon/Flanker/Posner), this task is
# SELF-PACED: a trial ends the moment the client taps something (correct or
# wrong), not after a fixed timer - only an 8s safety-net timeout advances an
# unanswered trial. Reports accuracy% plus average RT and the RT-by-set-size
# SLOPE (ms/object) per search type - the actual outcome measure this
# paradigm exists to surface (near-flat for feature search, clearly positive
# for conjunction search).
# Background colour/intensity (added later, fourth batch of the same
# Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/Rotation/
# Merkspanne/Simon - see CLAUDE.md's Established patterns for the scope
# decision, minus their transfer/preset-save machinery) tints the outer
# #searchStage - the target/distractor items sit directly on it with no
# neutral box around them (audited and approved: the tint is always mixed
# toward white, never full saturation, keeping contrast usable). Both the
# ready screen and the pause overlay have their own live picker+slider
# sharing the same searchPrefs.

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
        print("Suchtest card visible:", await pg.is_visible("#searchOpenBtn"))
        await pg.click("#searchOpenBtn"); await pg.wait_for_timeout(150)
        print("searchReady visible:", await pg.is_visible("#searchReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#searchAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#searchBgColorPicker .color-swatch").count())
        await pg.click('#searchBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#searchBgIntensitySlider", "0.6"); await pg.dispatch_event("#searchBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#searchBgIntensityValue")))

        # "kurz" = 12 trials, fast enough for a short test run.
        await pg.click('#searchLengthRow [data-search-length="kurz"]'); await pg.wait_for_timeout(60)
        await pg.click("#searchReadyStartBtn"); await pg.wait_for_timeout(200)
        print("searchPlayer visible:", await pg.is_visible("#searchPlayer"))
        progress = await pg.inner_text("#searchProgressEl")
        print("progress starts at 0/12:", "0/12" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('searchStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_progress_change(prev, max_ms=9500, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#searchProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_array(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                n = await pg.locator("#searchItemsLayer .search-item").count()
                if n > 0:
                    return n
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return 0

        async def wait_for_hint_contains(text, max_ms=9500, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#searchHint")
                if text in cur:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: cue text names the target, array appears, tap the TARGET ---
        progress = await wait_for_progress_change(progress)
        hint1 = await pg.inner_text("#searchHint")
        print("trial 1's cue names a target ('Ziel: ...'):", hint1.startswith("Ziel:"))
        n1 = await wait_for_array()
        print("trial 1's search array rendered with >=6 items:", n1 >= 6)
        shape_expected = "circle" if "Kreis" in hint1 else "square"
        target_loc = pg.locator('#searchItemsLayer .search-item[data-target="1"]')
        print("exactly one target item on stage:", await target_loc.count() == 1)
        print("the target item's shape matches the cue:", shape_expected in (await target_loc.get_attribute("class") or ""))
        await target_loc.click(); await pg.wait_for_timeout(80)
        print("tapping the target marks it 'correct':", "correct" in (await target_loc.get_attribute("class") or ""))

        # --- trial 2: deliberately tap a DISTRACTOR ---
        progress = await wait_for_progress_change(progress)
        await wait_for_array()
        distractor_loc = pg.locator('#searchItemsLayer .search-item[data-target="0"]').first
        await distractor_loc.click(); await pg.wait_for_timeout(80)
        print("tapping a distractor marks it 'wrong':", "wrong" in (await distractor_loc.get_attribute("class") or ""))
        print("a wrong tap reveals the true target:", await pg.locator('#searchItemsLayer .search-item.reveal').count() == 1)
        print("a wrong tap shows the 'Daneben!' hint:", "Daneben" in (await pg.inner_text("#searchHint")))

        # --- trial 3: let the 8s safety-net timeout elapse without tapping ---
        # (the timeout hint is only visible during the brief feedback window
        # right before the next trial's cue overwrites it, so it must be
        # checked BEFORE waiting for the progress counter to advance, not after)
        progress = await wait_for_progress_change(progress)
        await wait_for_array()
        timed_out_hint_shown = await wait_for_hint_contains("abgelaufen")
        print("a timed-out trial shows the 'Zeit abgelaufen!' hint:", timed_out_hint_shown)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances on its own:", progress4 != progress)
        progress = progress4

        # --- pause/resume freezes the stage mid-search ---
        await wait_for_array()
        await pg.click("#searchPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#searchPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#searchPauseBtn"))
        html_paused1 = await pg.inner_html("#searchItemsLayer")
        progress_paused1 = await pg.inner_text("#searchProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#searchItemsLayer")
        progress_paused2 = await pg.inner_text("#searchProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#searchPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('searchStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#searchResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#searchPauseOverlay"))
        # tapping the target should still work correctly right after a resume
        await wait_for_array()
        tgt = pg.locator('#searchItemsLayer .search-item[data-target="1"]')
        if await tgt.count() == 1:
            await tgt.click(); await pg.wait_for_timeout(80)
            print("tap after resume still resolves the trial:", "correct" in (await tgt.get_attribute("class") or ""))
        else:
            print("tap after resume still resolves the trial:", False)

        # --- Beenden mid-run with progress -> done panel with accuracy% + slope ---
        await pg.click("#searchBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#searchDonePanel"))
        summary = await pg.inner_text("#searchDoneSummary")
        print("done summary mentions Suchtest and % richtig:", "Suchtest" in summary and "%" in summary)
        await pg.click("#searchDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#searchOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#searchReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#searchPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#searchPauseBtn"))
        await pg.click("#searchBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#searchDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#searchOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#searchLengthRow [data-search-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#searchOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#searchLengthRow [data-search-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
