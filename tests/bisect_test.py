import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Linienhalbierungs-Test: twenty-eighth exercise added under the autonomous
# "Test" section, picked from the Recherche-Backlog (candidate #3, the Line
# Bisection Test / Schenkenberg, Bradford & Ajax 1980, plus the
# "pseudoneglect" literature - Bowers & Heilman 1980 - establishing that
# healthy people reliably show a small left/right bias when judging a
# line's centre). A horizontal line of varying length/position appears;
# the client taps where they judge the exact centre to be, no time limit,
# no per-trial feedback. Scored as deviation % of half the line's length
# (negative = left, positive = right), reporting the mean signed deviation
# (the "Aufmerksamkeits-Tendenz") and the mean absolute deviation.

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
        print("Linienhalbierungs-Test card visible:", await pg.is_visible("#bisectOpenBtn"))
        await pg.click("#bisectOpenBtn"); await pg.wait_for_timeout(150)
        print("bisectReady visible:", await pg.is_visible("#bisectReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#bisectAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#bisectBgColorPicker .color-swatch").count())
        await pg.click('#bisectBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        await pg.fill("#bisectBgIntensitySlider", "0.5"); await pg.dispatch_event("#bisectBgIntensitySlider", "input")
        print("intensity value label updated:", "50%" in (await pg.inner_text("#bisectBgIntensityValue")))

        await pg.click('#bisectLengthRow [data-bisect-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#bisectLengthRow [data-bisect-length="kurz"]', "class") or ""))
        await pg.click("#bisectReadyStartBtn"); await pg.wait_for_timeout(1100)
        print("bisectPlayer visible:", await pg.is_visible("#bisectPlayer"))
        print("progress starts at 1/9:", "1/9" in (await pg.inner_text("#bisectProgressEl")))
        print("hint asks for the centre:", "Mitte" in (await pg.inner_text("#bisectHint")))
        bg_at_start = await pg.evaluate("() => document.getElementById('bisectStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def line_box():
            return await pg.eval_on_selector("#bisectLine", "el => { const r = el.getBoundingClientRect(); return {left: r.left, width: r.width, top: r.top}; }")

        lb = await line_box()
        print("a line of plausible width is shown:", 100 < lb["width"] < 350)

        # --- trial 1: tap exactly at the true centre ---
        true_center_x = lb["left"] + lb["width"] / 2
        await pg.mouse.click(true_center_x, lb["top"] + 2)
        await pg.wait_for_timeout(100)
        print("tap mark appears immediately after tapping:", await pg.is_visible("#bisectMark"))
        print("hint clears once tapped (no per-trial feedback text):", (await pg.inner_text("#bisectHint")) == "")
        await pg.wait_for_timeout(900)
        print("progress advances to 2/9:", "2/9" in (await pg.inner_text("#bisectProgressEl")))
        print("line re-rendered for the next trial:", await pg.is_visible("#bisectLine"))

        # --- 3 more trials, each deliberately offset to the right, to
        # produce a clearly right-biased, non-trivial summary ---
        for _ in range(3):
            lb = await line_box()
            cx = lb["left"] + lb["width"] / 2 + lb["width"] * 0.3
            await pg.mouse.click(cx, lb["top"] + 2)
            await pg.wait_for_timeout(900)
        print("progress reached 5/9:", "5/9" in (await pg.inner_text("#bisectProgressEl")))

        # --- pause/resume freezes the stage ---
        progress_before_pause = await pg.inner_text("#bisectProgressEl")
        await pg.click("#bisectPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#bisectPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#bisectPauseBtn"))
        await pg.wait_for_timeout(700)
        print("progress genuinely frozen while paused:", (await pg.inner_text("#bisectProgressEl")) == progress_before_pause)
        await pg.click('#bisectPauseBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('bisectStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#bisectResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#bisectPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel reflects the
        # deliberate rightward bias just produced ---
        await pg.click("#bisectBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#bisectDonePanel"))
        summary = await pg.inner_text("#bisectDoneSummary")
        print("summary:", summary)
        print("summary names the test and a Tendenz:", "Linienhalbierungs-Test" in summary and "Tendenz" in summary)
        print("summary correctly reports a rightward tendency:", "rechts" in summary)
        await pg.click("#bisectDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#bisectOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#bisectReadyStartBtn"); await pg.wait_for_timeout(1100)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#bisectPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#bisectPauseBtn"))
        await pg.click("#bisectBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#bisectDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#bisectOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#bisectLengthRow [data-bisect-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#bisectOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#bisectLengthRow [data-bisect-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
