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
        print("natPeripherPanel visible:", await pg.is_visible("#natPeripherPanel"))
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        print("ready screen visible:", await pg.is_visible("#ready"))
        print("ready title:", await pg.inner_text("#readyTitle"))
        print("colorGroup hidden:", await pg.is_hidden("#colorGroup"))
        print("periphKindGroup visible:", await pg.is_visible("#periphKindGroup"))
        print("durationGroup visible:", await pg.is_visible("#durationGroup"))
        print("tempoGroup visible:", await pg.is_visible("#tempoGroup"))
        rules_text = await pg.inner_text("#rulesBox")
        print("rulesBox mentions Pausen:", "Pausen" in rules_text)

        # Zeichentyp selection
        await pg.click('#periphKindRow [data-periph-kind="buchstaben"]'); await pg.wait_for_timeout(80)
        print("buchstaben active:", "active" in (await pg.get_attribute('#periphKindRow [data-periph-kind="buchstaben"]', "class") or ""))

        # open Feineinstellungen, set custom fixation point
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("periphFixGroup visible:", await pg.is_visible("#periphFixGroup"))
        fix_swatch_count = await pg.locator("#periphFixColorPicker .color-swatch").count()
        print("fix colour swatch count (grau + 9 = 10):", fix_swatch_count)
        await pg.fill("#periphFixCharInput", "X")
        await pg.click('#periphFixColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(80)
        await pg.fill("#periphFixSizeSlider", "1.6")
        await pg.dispatch_event("#periphFixSizeSlider", "input")
        await pg.wait_for_timeout(80)
        print("size value text:", await pg.inner_text("#periphFixSizeValue"))

        # reload to confirm persistence, then reopen
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        print("kind persisted (buchstaben):", "active" in (await pg.get_attribute('#periphKindRow [data-periph-kind="buchstaben"]', "class") or ""))
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("fix char persisted:", await pg.input_value("#periphFixCharInput"))
        print("fix colour persisted (rot active):", "active" in (await pg.get_attribute('#periphFixColorPicker .color-swatch[data-key="rot"]', "class") or ""))

        # "Zurück" should return to natHome, not the generic VT home
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        # sanity: a normal VT exercise still returns to "home", not natHome
        await pg.click('#natHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        print("VT exercise still returns to generic home:", await pg.is_visible("#home"))

        # now actually run Periph with a long stimulus to screenshot the render
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.stimulusS = 4; raw.intervalMin = 0.5; raw.intervalMax = 0.5;
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#startBtn")
        await pg.wait_for_timeout(6500)
        print("player visible during run:", await pg.is_visible("#player"))
        await pg.screenshot(path=OUT + "periph_running.png")

        # landscape check - rotate viewport, confirm still renders without error
        await pg.set_viewport_size({"width": 844, "height": 390})
        await pg.wait_for_timeout(600)
        await pg.screenshot(path=OUT + "periph_landscape.png")

        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        print("beenden -> back at periph ready screen:", await pg.is_visible("#ready"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
