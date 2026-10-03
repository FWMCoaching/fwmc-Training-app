import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Merkspanne-Test (Change Detection): eighth exercise added under the
# autonomous "Test" section. Classic visual working-memory change-detection
# paradigm (Phillips, 1974; popularised by Luck & Vogel, 1997) - a sample
# array of coloured squares is briefly shown, then after a blank retention
# interval the same positions are shown again, either identical or with
# exactly one square's colour changed. The client taps "Gleich"/"Veraendert"
# for the WHOLE display. Scored with Pashler's K (whole-display capacity
# estimate), not a "level" or accuracy alone. Fixed 20-trial run, difficulty
# = array size (4/6/8), no "Bei Fehler" (correctly skipped, same reasoning
# as Flanker/Posner/Rotation). Background colour/intensity (added later,
# third batch of the same Test-Bereich effort as Go/No-Go/N-Back/Trail/
# Flanker/UFOV/Posner/Rotation - see CLAUDE.md's Established patterns for
# the scope decision, minus their transfer/preset-save machinery) tints the
# OUTER #merkStage, not #merkField - the smaller sub-box where the coloured
# memoranda themselves render - so the background never competes with the
# colour-change signal being tested. Both the ready screen and the pause
# overlay have their own live picker+slider sharing the same merkPrefs.
#
# Each trial cycles through 4 phases in #merkField's child count:
#   gap (0 items, random ISI) -> study (N items, 500ms) -> retention
#   (0 items, 900ms) -> responding (N items again, untimed, waits on tap).
# A tap only counts during "responding" - tapping during "study" is
# silently ignored by design (same "ignore taps outside the response
# phase" convention as Flanker/Posner/Rotation), so this test always waits
# for a full 0 -> nonzero -> 0 -> nonzero cycle before tapping, to avoid
# racing a tap into the wrong phase.

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
        print("Merk card visible:", await pg.is_visible("#merkOpenBtn"))
        await pg.click("#merkOpenBtn"); await pg.wait_for_timeout(150)
        print("merkReady visible:", await pg.is_visible("#merkReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#merkAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#merkBgColorPicker .color-swatch").count())
        await pg.click('#merkBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#merkBgIntensitySlider", "0.6"); await pg.dispatch_event("#merkBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#merkBgIntensityValue")))

        async def field_count():
            return await pg.eval_on_selector("#merkField", "el => el.children.length")

        async def wait_for_count(predicate, max_ms=4000, poll_ms=20):
            waited = 0
            while waited < max_ms:
                n = await field_count()
                if predicate(n):
                    return n
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return await field_count()

        async def wait_for_progress_change(prev, max_ms=4000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#merkProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_responding_phase(max_ms=4000):
            # Right after a tap the field still holds the just-answered test
            # array for the rest of the feedback delay (deliberately, so the
            # tapped button's colour stays up against the display it was
            # answering) - so a naive "wait for nonzero" here would return
            # immediately on that stale leftover, then only walk as far as
            # the NEXT trial's study phase instead of its responding phase.
            # Confirming a zero baseline first (gap/retention) before
            # tracking nonzero->zero->nonzero (study->retention->responding)
            # is what actually lands on a fresh trial's responding phase.
            await wait_for_count(lambda n: n == 0, max_ms=max_ms)
            n1 = await wait_for_count(lambda n: n > 0, max_ms=max_ms)
            await wait_for_count(lambda n: n == 0, max_ms=max_ms)
            n2 = await wait_for_count(lambda n: n > 0, max_ms=max_ms)
            return n1, n2

        # --- "leicht" = 4 items, easiest to reason about in the test ---
        await pg.click('#merkDifficultyRow [data-merk-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.click("#merkReadyStartBtn"); await pg.wait_for_timeout(200)
        print("merkPlayer visible:", await pg.is_visible("#merkPlayer"))
        progress = await pg.inner_text("#merkProgressEl")
        print("progress starts at 0/20:", "0/20" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('merkStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        # --- trial 1: sample array shows exactly 4 items, then the same 4
        # positions reappear for the test array before we tap ---
        n_study, n_test = await wait_for_responding_phase()
        print("study array shows 4 items ('leicht'):", n_study == 4)
        print("test array also shows 4 items (same positions, feature-only change):", n_test == 4)
        await pg.click("#merkSameBtn"); await pg.wait_for_timeout(80)
        has_feedback = ("correct" in (await pg.get_attribute("#merkSameBtn", "class") or "")) or \
                       ("wrong" in (await pg.get_attribute("#merkSameBtn", "class") or ""))
        print("tapped button shows correct/wrong feedback immediately:", has_feedback)
        progress = await wait_for_progress_change(progress)
        print("progress advanced after trial 1:", "1/20" in progress)

        # --- pause immediately, before trial 2's items appear: progress and
        # field stay frozen, no items leak through while paused ---
        await pg.click("#merkPauseBtn"); await pg.wait_for_timeout(120)
        print("pause overlay visible:", await pg.is_visible("#merkPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#merkPauseBtn"))
        progress_frozen_1 = await pg.inner_text("#merkProgressEl")
        await pg.wait_for_timeout(700)
        progress_frozen_2 = await pg.inner_text("#merkProgressEl")
        print("progress frozen while paused:", progress_frozen_1 == progress_frozen_2)
        await pg.click('#merkPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('merkStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#merkResumeBtn"); await pg.wait_for_timeout(120)
        print("pause overlay hidden after resume:", await pg.is_hidden("#merkPauseOverlay"))

        # --- trial 2: tap "Veraendert" this time, still advances ---
        await wait_for_responding_phase()
        await pg.click("#merkChangedBtn"); await pg.wait_for_timeout(80)
        progress = await wait_for_progress_change(progress, max_ms=4000)
        print("progress advanced after trial 2:", "2/20" in progress)

        # --- Beenden with only 2 resolved trials skips the done panel (< 4 threshold) ---
        await pg.click("#merkBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with too few resolved trials returns to testHome, no done panel:",
              await pg.is_visible("#testHome") and await pg.is_hidden("#merkDonePanel"))

        # --- a fresh run with zero progress also skips the done panel ---
        await pg.click("#merkOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#merkReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#merkPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#merkPauseBtn"))
        await pg.click("#merkBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#merkDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#merkOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#merkDifficultyRow [data-merk-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#merkOpenBtn"); await pg.wait_for_timeout(150)
        print("'schwer' selection survives reload:", "active" in (await pg.get_attribute('#merkDifficultyRow [data-merk-diff="schwer"]', "class") or ""))
        # switch back to "leicht" for a fast, predictable full run below
        await pg.click('#merkDifficultyRow [data-merk-diff="leicht"]'); await pg.wait_for_timeout(60)

        # --- full run to the done panel ---
        await pg.click("#merkReadyStartBtn"); await pg.wait_for_timeout(200)
        progress = "0/20"
        for i in range(20):
            await wait_for_responding_phase()
            btn = "#merkSameBtn" if i % 2 == 0 else "#merkChangedBtn"
            await pg.click(btn)
            if i < 19:
                progress = await wait_for_progress_change(progress, max_ms=4000)

        async def wait_for_done_panel(max_ms=3000, poll_ms=30):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible("#merkDonePanel"):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        await wait_for_done_panel()
        print("done panel shown after all 20 trials:", await pg.is_visible("#merkDonePanel"))
        summary = await pg.inner_text("#merkDoneSummary")
        print("done summary mentions Merkspanne-Test:", "Merkspanne-Test" in summary)
        print("done summary reports an accuracy percentage:", "%" in summary)
        print("done summary reports a capacity (K):", "Kapazit" in summary and "(K)" in summary)
        await pg.click("#merkDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome after done panel:", await pg.is_visible("#testHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
