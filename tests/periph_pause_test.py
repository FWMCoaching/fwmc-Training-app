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

        # long stimulus/interval so the running screenshots/reads are stable
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.stimulusS = 4; raw.intervalMin = 0.5; raw.intervalMax = 0.5;
            raw.bgIntensity = 0; raw.bgColorKey = 'gruen';
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        print("pause button hidden on ready screen (not started yet):", await pg.is_hidden("#periphPauseBtn"))

        await pg.click("#startBtn"); await pg.wait_for_timeout(800)
        print("player visible:", await pg.is_visible("#player"))
        print("pause button visible once Periph is running:", await pg.is_visible("#periphPauseBtn"))
        print("pause overlay hidden while running:", await pg.is_hidden("#periphPauseOverlay"))

        # --- pause ---
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible after Pause:", await pg.is_visible("#periphPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#periphPauseBtn"))
        time_at_pause = await pg.inner_text("#timeEl")
        await pg.wait_for_timeout(1500)
        time_after_wait = await pg.inner_text("#timeEl")
        print("timer frozen while paused:", time_at_pause == time_after_wait, time_at_pause, time_after_wait)

        # --- live-adjust background to full red while paused ---
        await pg.fill("#periphPauseBgSlider", "1")
        await pg.dispatch_event("#periphPauseBgSlider", "input")
        await pg.wait_for_timeout(80)
        await pg.click('#periphPauseBgColorPicker .color-swatch[data-key="rot"]')
        await pg.wait_for_timeout(150)
        px = await pg.evaluate("""() => {
            const c = document.getElementById('stage');
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(5, 5, 1, 1).data;
            return [d[0], d[1], d[2]];
        }""")
        print("background pixel reflects live change to full red while frozen:", px, px[0] > 180 and px[1] < 90 and px[2] < 90)

        # fixation colour + size while paused
        await pg.click('#periphPauseFixColorPicker .color-swatch[data-key="blau"]')
        await pg.fill("#periphPauseFixSizeSlider", "1.8")
        await pg.dispatch_event("#periphPauseFixSizeSlider", "input")
        await pg.wait_for_timeout(150)
        print("pause fix size value text:", await pg.inner_text("#periphPauseFixSizeValue"))

        # ready-screen picker mirrors the same state (shared single-select helper)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}')")
        print("bgColorKey persisted as rot:", prefs.get("bgColorKey") == "rot")
        print("bgIntensity persisted as 1:", prefs.get("bgIntensity") == 1)
        print("periphFixColor persisted as blau:", prefs.get("periphFixColor") == "blau")
        print("periphFixSize persisted as 1.8:", prefs.get("periphFixSize") == 1.8)

        # --- resume ---
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after Weiter:", await pg.is_hidden("#periphPauseOverlay"))
        print("pause button visible again after resume:", await pg.is_visible("#periphPauseBtn"))
        time_after_resume = await pg.inner_text("#timeEl")
        await pg.wait_for_timeout(1200)
        time_running_again = await pg.inner_text("#timeEl")
        print("timer advancing again after resume:", time_after_resume != time_running_again, time_after_resume, time_running_again)
        await pg.screenshot(path=OUT + "periph_pause_resumed.png")

        # --- Beenden while paused should not leave the overlay stuck open ---
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        print("back at periph ready screen after Beenden-while-paused:", await pg.is_visible("#ready"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(500)
        print("pause overlay not stuck open on a fresh run:", await pg.is_hidden("#periphPauseOverlay"))
        print("pause button visible again on the fresh run:", await pg.is_visible("#periphPauseBtn"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        # --- a non-Periph exercise never shows the pause button ---
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('#natHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        await pg.click("#startBtn"); await pg.wait_for_timeout(500)
        print("pause button stays hidden for a non-Periph exercise:", await pg.is_hidden("#periphPauseBtn"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
