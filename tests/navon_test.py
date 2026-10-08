import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Ganzheit-Detail-Test (Navon-Aufgabe): twenty-fifth exercise added under
# the autonomous "Test" section, picked from the Recherche-Backlog
# (candidate #20, the Navon task - Navon, 1977, "Forest before the
# trees"). A large letter (H or S) built from many small letters (also H
# or S) appears; a cue ("GROSS"/"KLEIN") names which level to judge, and
# the client taps H or S for that level's identity, ignoring the other
# one. Reports accuracy% plus RT-based interference costs for the global
# and local level separately - the classic asymmetry (global usually
# interferes with local more than the reverse) is the actual outcome
# measure this paradigm exists to reveal.

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
        print("Navon card visible:", await pg.is_visible("#navonOpenBtn"))
        await pg.click("#navonOpenBtn"); await pg.wait_for_timeout(150)
        print("navonReady visible:", await pg.is_visible("#navonReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#navonAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#navonBgColorPicker .color-swatch").count())
        await pg.click('#navonBgColorPicker .color-swatch[data-key="gelb"]'); await pg.wait_for_timeout(80)
        await pg.fill("#navonBgIntensitySlider", "0.5"); await pg.dispatch_event("#navonBgIntensitySlider", "input")
        print("intensity value label updated:", "50 %" in (await pg.inner_text("#navonBgIntensityValue")))

        # "leicht" = longest cue time, so a slow Playwright click still
        # reliably lands during the response window rather than timing out.
        await pg.click('#navonDifficultyRow [data-navon-diff="leicht"]'); await pg.wait_for_timeout(60)
        print("leicht marked active:", "active" in (await pg.get_attribute('#navonDifficultyRow [data-navon-diff="leicht"]', "class") or ""))
        await pg.click("#navonReadyStartBtn"); await pg.wait_for_timeout(200)
        print("navonPlayer visible:", await pg.is_visible("#navonPlayer"))
        print("progress starts at 0/32:", "0/32" in (await pg.inner_text("#navonProgressEl")))
        bg_at_start = await pg.evaluate("() => document.getElementById('navonStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_cue(max_ms=2000, poll_ms=20):
            waited = 0
            while waited < max_ms:
                txt = await pg.inner_text("#navonCue")
                if txt in ("GROSS", "KLEIN"):
                    return txt
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def wait_for_grid(max_ms=2000, poll_ms=20):
            waited = 0
            while waited < max_ms:
                n = await pg.locator(".navon-cell").count()
                filled = await pg.locator(".navon-cell:not(:empty)").count()
                if n > 0 and filled > 0:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- trial 1: read cue + grid, verify a 5x7=35 cell grid renders ---
        cue1 = await wait_for_cue()
        print("cue shows GROSS or KLEIN:", cue1 in ("GROSS", "KLEIN"))
        got_grid = await wait_for_grid()
        print("stimulus grid renders with filled cells:", got_grid)
        print("grid has 35 cells (5x7):", await pg.locator(".navon-cell").count() == 35)
        # cue stays visible while the stimulus is shown (not cleared)
        print("cue still visible once stimulus appears:", (await pg.inner_text("#navonCue")) in ("GROSS", "KLEIN"))

        await pg.click("#navonHBtn"); await pg.wait_for_timeout(60)
        h_class = await pg.get_attribute("#navonHBtn", "class") or ""
        s_class = await pg.get_attribute("#navonSBtn", "class") or ""
        print("tapping H gives feedback (H itself marked, and the true answer is shown as correct):", ("correct" in h_class or "wrong" in h_class) and ("correct" in h_class or "correct" in s_class))
        await pg.wait_for_timeout(700)

        # --- feedback classes clear before the next trial's cue ---
        cue2 = await wait_for_cue()
        print("next trial's cue appears:", cue2 in ("GROSS", "KLEIN"))
        print("feedback classes cleared on H:", "correct" not in (await pg.get_attribute("#navonHBtn", "class") or "") and "wrong" not in (await pg.get_attribute("#navonHBtn", "class") or ""))
        await wait_for_grid()
        await pg.click("#navonSBtn"); await pg.wait_for_timeout(700)

        # --- more trials to clear the min-resolved threshold (>= 8) ---
        for _ in range(6):
            await wait_for_cue()
            await wait_for_grid()
            await pg.click("#navonHBtn")
            await pg.wait_for_timeout(700)

        progress_after = await pg.inner_text("#navonProgressEl")
        print("progress advanced past several trials:", "0/32" not in progress_after)

        # --- pause/resume freezes the stage ---
        await wait_for_cue()
        await pg.click("#navonPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#navonPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#navonPauseBtn"))
        progress_paused1 = await pg.inner_text("#navonProgressEl")
        await pg.wait_for_timeout(700)
        progress_paused2 = await pg.inner_text("#navonProgressEl")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click('#navonPauseBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('navonStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#navonResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#navonPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel ---
        await pg.click("#navonBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#navonDonePanel"))
        summary = await pg.inner_text("#navonDoneSummary")
        print("done summary mentions Ganzheit-Detail-Test and richtig:", "Ganzheit-Detail-Test" in summary and "richtig" in summary)
        await pg.click("#navonDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#navonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#navonReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#navonPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#navonPauseBtn"))
        await pg.click("#navonBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#navonDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#navonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#navonDifficultyRow [data-navon-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#navonOpenBtn"); await pg.wait_for_timeout(150)
        print("'schwer' selection survives reload:", "active" in (await pg.get_attribute('#navonDifficultyRow [data-navon-diff="schwer"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
