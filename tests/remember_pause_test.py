import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

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

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)

        # --- Fixed/Bewegte ready screen: pre-set background ---
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(100)
        print("rememberBgColorPicker swatch count (9):", await pg.locator("#rememberBgColorPicker .color-swatch").count())
        await pg.click('#rememberBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        await pg.fill("#rememberBgIntensitySlider", "0.9")
        await pg.dispatch_event("#rememberBgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        print("contrast hint visible at dark blue + high intensity:", await pg.is_visible("#rememberBgContrastHint"))

        # Trainingsmodus screen shows the SAME shared prefs already applied
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        await pg.click("#rememberTrainingAdvanced summary"); await pg.wait_for_timeout(100)
        print("training bg colour mirrors fixed/shuffle (blau active):", "active" in (await pg.get_attribute('#rememberTrainingBgColorPicker .color-swatch[data-key="blau"]', "class") or ""))
        print("training bg intensity mirrors fixed/shuffle:", await pg.input_value("#rememberTrainingBgIntensitySlider"))

        # reload -> persistence
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1') || '{}')")
        print("bgColorKey persisted as blau:", prefs.get("bgColorKey") == "blau")
        print("bgIntensity persisted as 0.9:", prefs.get("bgIntensity") == 0.9)

        # --- Run Feste Positionen, check background applied, then pause ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(400)
        print("remember player visible:", await pg.is_visible("#rememberPlayer"))
        bg = await pg.evaluate("() => document.getElementById('rememberStage').style.background")
        print("stage background applied on start:", bg)

        print("pause button visible:", await pg.is_visible("#rememberPauseBtn"))
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#rememberPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#rememberPauseBtn"))

        # game must be frozen: clicking a covered marker (if any visible under
        # the overlay) must not register - wait past the reveal time and
        # confirm the hint text never changes to "richtig antippen" while paused
        hint_before = await pg.inner_text("#rememberHint")
        await pg.wait_for_timeout(2000)
        hint_after = await pg.inner_text("#rememberHint")
        print("game frozen while paused (hint unchanged):", hint_before == hint_after, hint_before, hint_after)

        # live-adjust to full red while paused
        await pg.click('#rememberPauseBgColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(80)
        await pg.fill("#rememberPauseBgSlider", "1")
        await pg.dispatch_event("#rememberPauseBgSlider", "input")
        await pg.wait_for_timeout(150)
        bg_paused = await pg.evaluate("() => document.getElementById('rememberStage').style.background")
        print("stage background updated live while paused:", bg_paused)
        ready_picker_synced = "active" in (await pg.get_attribute('#rememberBgColorPicker .color-swatch[data-key="rot"]', "class") or "")
        print("ready-screen picker would show the same colour (state shared):", ready_picker_synced)

        # --- resume: game continues ---
        await pg.click("#rememberResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after Weiter:", await pg.is_hidden("#rememberPauseOverlay"))
        print("pause button visible again:", await pg.is_visible("#rememberPauseBtn"))
        await pg.wait_for_timeout(3500)
        hint_running = await pg.inner_text("#rememberHint")
        print("game progressed after resume (phase changed):", hint_running != hint_before, hint_running)
        await pg.screenshot(path=OUT + "remember_pause_resumed.png")

        # --- Beenden while paused should not leave the overlay stuck open ---
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(150)
        print("back at a remember screen after Beenden-while-paused:", not (await pg.is_visible("#rememberPlayer")))
        print("pause overlay not left stuck open after Beenden:", await pg.is_hidden("#rememberPauseOverlay"))
        if await pg.is_visible("#rememberDonePanel"):
            await pg.click("#rememberDoneBackBtn"); await pg.wait_for_timeout(150)
        if await pg.is_visible("#rememberReady"):
            await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)

        # --- Trainingsmodus run also has the pause button + nav gating ---
        # rememberReadyBackToHome already lands on natHome directly.
        if not await pg.is_visible("#natHome"):
            await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(400)
        print("training pause button visible:", await pg.is_visible("#rememberPauseBtn"))
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(150)
        level_before = await pg.inner_text("#rememberLevelEl")
        # nav buttons sit behind the overlay - a forced click must not change level
        await pg.evaluate("document.getElementById('rememberNavNextBtn').click()")
        await pg.wait_for_timeout(150)
        level_after = await pg.inner_text("#rememberLevelEl")
        print("training nav ignored while paused:", level_before == level_after, level_before, level_after)
        await pg.click("#rememberResumeBtn"); await pg.wait_for_timeout(150)
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
