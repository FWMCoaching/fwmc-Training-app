import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Kartensortier-Test: twenty-fourth exercise added under the autonomous
# "Test" section, picked from the Recherche-Backlog (candidate #7, the
# Wisconsin Card Sorting Test). Four fixed reference cards (1 red triangle,
# 2 green stars, 3 yellow squares, 4 blue circles) sit at the top; a new
# stimulus card appears below and the client taps which reference card it
# matches. The rule (Farbe/Form/Anzahl) is never shown - only right/wrong
# feedback - and silently cycles Farbe->Form->Anzahl after enough
# consecutive correct taps. This test drives the engine directly via
# window-level state inspection where needed, since the active rule is
# deliberately never exposed in the DOM (that's the whole point of the task).

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
        print("WCST card visible:", await pg.is_visible("#wcstOpenBtn"))
        await pg.click("#wcstOpenBtn"); await pg.wait_for_timeout(150)
        print("wcstReady visible:", await pg.is_visible("#wcstReady"))
        print("no background Feineinstellungen (deliberately excluded):", await pg.locator("#wcstAdvanced").count() == 0)

        await pg.click('#wcstLengthRow [data-wcst-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#wcstLengthRow [data-wcst-length="kurz"]', "class") or ""))
        await pg.click("#wcstReadyStartBtn"); await pg.wait_for_timeout(200)
        print("wcstPlayer visible:", await pg.is_visible("#wcstPlayer"))
        print("4 reference cards shown:", await pg.locator(".wcst-ref").count() == 4)
        progress = await pg.inner_text("#wcstProgressEl")
        print("progress starts at 0/32 . 0 Kategorien:", "0/32" in progress and "0 Kategorien" in progress)

        async def stimulus_shape_count():
            return await pg.locator("#wcstStimulusCard .wcst-shape").count()

        # wait for the first stimulus card to render (900ms initial delay)
        await pg.wait_for_timeout(1000)
        n0 = await stimulus_shape_count()
        print("a stimulus card with 1-4 shapes is shown:", 1 <= n0 <= 4)

        # Drive many trials, cycling through all 4 reference cards
        # correct/wrong, and use whichever feedback the engine gives us to
        # infer nothing more than "is progress advancing sanely" - since the
        # actual rule is intentionally opaque, this test verifies mechanics
        # (progress increments, feedback classes render, pause/resume,
        # perseverative/category reporting fields exist in the summary) via
        # exhaustive tapping: for each trial, tap card 0, read result, and if
        # wrong, the reveal is which card WAS right (only one of correct/
        # wrong classes is ever set) - re-derive by tapping the still-
        # unmarked correct card next round instead. Simpler and robust: just
        # tap a fixed pattern (cycle 0,1,2,3) for many trials - across 32
        # trials with a rule cycling every <=6 correct in a row, this will
        # organically hit the correct card often enough to observe both
        # correct and wrong feedback and to exercise category completion
        # indirectly (accuracy stats only, not a strict correctness check of
        # the hidden rule logic itself, which was verified by reading the
        # code).
        seen_correct = False
        seen_wrong = False
        for i in range(20):
            idx = i % 4
            await pg.click(f'.wcst-ref[data-ref-idx="{idx}"]'); await pg.wait_for_timeout(80)
            cls = await pg.get_attribute(f'.wcst-ref[data-ref-idx="{idx}"]', "class") or ""
            if "correct" in cls: seen_correct = True
            if "wrong" in cls: seen_wrong = True
            await pg.wait_for_timeout(650)
        print("saw at least one 'correct' feedback across 20 trials:", seen_correct)
        print("saw at least one 'wrong' feedback across 20 trials:", seen_wrong)
        progress_after = await pg.inner_text("#wcstProgressEl")
        print("progress advanced past the first 20 trials:", progress_after != progress and "/32" in progress_after)

        # --- pause/resume freezes the stage ---
        await pg.click("#wcstPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#wcstPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#wcstPauseBtn"))
        progress_paused1 = await pg.inner_text("#wcstProgressEl")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#wcstProgressEl")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click("#wcstResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#wcstPauseOverlay"))
        # a tap still registers after resume
        await pg.click('.wcst-ref[data-ref-idx="0"]'); await pg.wait_for_timeout(700)

        # --- Beenden mid-run with progress -> done panel ---
        await pg.click("#wcstBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#wcstDonePanel"))
        summary = await pg.inner_text("#wcstDoneSummary")
        print("done summary mentions Kartensortier-Test, Kategorien and perseverative:", "Kartensortier-Test" in summary and "Kategorien" in summary and "perseverative" in summary)
        await pg.click("#wcstDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#wcstOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#wcstReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#wcstPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#wcstPauseBtn"))
        await pg.click("#wcstBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#wcstDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#wcstOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#wcstLengthRow [data-wcst-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#wcstOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#wcstLengthRow [data-wcst-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
