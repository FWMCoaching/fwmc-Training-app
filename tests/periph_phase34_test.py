import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def open_advanced(pg):
    await pg.evaluate("document.getElementById('advanced').open = true")

async def open_filters(pg):
    await pg.evaluate("""() => {
        document.getElementById('filterExtra').hidden = false;
        document.getElementById('filterMoreBtn').textContent = 'Weniger Filter';
    }""")

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

        # vt-color: bg IS the stimulus -> bgGroup hidden, fixation allowed
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        await open_advanced(pg); await pg.wait_for_timeout(100)
        print("vt-color: bgGroup hidden:", await pg.is_hidden("#bgGroup"))
        print("vt-color: periphFixGroup visible:", await pg.is_visible("#periphFixGroup"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)

        # 8-solo: plain arrow, bg NOT the stimulus -> both allowed
        await open_filters(pg); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="pfeil"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="8-solo"]'); await pg.wait_for_timeout(150)
        await open_advanced(pg); await pg.wait_for_timeout(100)
        print("8-solo: bgGroup visible:", await pg.is_visible("#bgGroup"))
        print("8-solo: periphFixGroup visible:", await pg.is_visible("#periphFixGroup"))
        bg_swatch_count = await pg.locator("#bgColorPicker .color-swatch").count()
        print("bg swatch count (9):", bg_swatch_count)

        # set a custom fixation char + a dark background at high intensity
        await pg.fill("#periphFixCharInput", ":)")
        await pg.click('#bgColorPicker .color-swatch[data-bg-color="blau"]'); await pg.wait_for_timeout(80)
        await pg.fill("#bgIntensitySlider", "0.9")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        print("contrast hint visible at dark blue + high intensity:", await pg.is_visible("#bgContrastHint"))

        await pg.fill("#bgIntensitySlider", "0.1")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        print("contrast hint hidden at low intensity:", await pg.is_hidden("#bgContrastHint"))

        await pg.fill("#bgIntensitySlider", "0.9")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)

        # back to normal for a fast run: shrink duration + reveal via localStorage
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.stimulusS = 4; raw.intervalMin = 0.4; raw.intervalMax = 0.4;
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await open_filters(pg); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="pfeil"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="8-solo"]'); await pg.wait_for_timeout(150)
        await pg.click("#startBtn")
        await pg.wait_for_timeout(6500)
        await pg.screenshot(path=OUT + "phase34_arrows_bg.png")

        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)

        # vt-color must still show the real training colour as background,
        # unaffected by the blau/0.9 setting left over from 8-solo
        await pg.click('[data-filter-value="pfeil"]'); await pg.wait_for_timeout(100)  # toggle the earlier filter off
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        await pg.click("#startBtn")
        await pg.wait_for_timeout(6500)
        await pg.screenshot(path=OUT + "phase34_vtcolor_unaffected.png")

        # stroop-bg: bgGroup should stay hidden too
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await open_filters(pg); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="erweitert"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="stroop-bg"]'); await pg.wait_for_timeout(150)
        await open_advanced(pg); await pg.wait_for_timeout(100)
        print("stroop-bg: bgGroup hidden:", await pg.is_hidden("#bgGroup"))
        print("stroop-bg: periphFixGroup visible:", await pg.is_visible("#periphFixGroup"))

        # cone-tap: neither should show
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await open_filters(pg); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="huetchen"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="cone-tap"]'); await pg.wait_for_timeout(150)
        print("cone-tap: advanced hidden:", await pg.is_hidden("#advanced"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
