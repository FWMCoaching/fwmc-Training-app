import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Picking a colour while intensity is 0% jumps it to 50% (0% would
# otherwise render plain white regardless of colour, looking "broken").
# Once intensity is already > 0, further colour picks must leave it alone.
# Applies everywhere wireBgIntensityControl is used (VT/Periph, Remember).

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
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.bgIntensity = 0; raw.bgColorKey = 'gruen';
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # --- VT/Periph ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("starts at 0%:", await pg.input_value("#bgIntensitySlider"))
        await pg.click('#bgColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(80)
        print("colour pick at 0% jumps to 50%:", await pg.input_value("#bgIntensitySlider"), await pg.inner_text("#bgIntensityValue"))

        # now manually set a different, non-zero intensity...
        await pg.fill("#bgIntensitySlider", "0.2")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        # ...picking another colour must NOT reset it back to 50%
        await pg.click('#bgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        print("colour pick at non-zero intensity (20%) leaves it alone:", await pg.input_value("#bgIntensitySlider"))

        # drop back to 0% and pick again - should jump to 50% again
        await pg.fill("#bgIntensitySlider", "0")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        await pg.click('#bgColorPicker .color-swatch[data-key="gelb"]'); await pg.wait_for_timeout(80)
        print("back at 0% -> colour pick jumps to 50% again:", await pg.input_value("#bgIntensitySlider"))

        # --- Remember (same shared helper, separate store) ---
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1') || '{}');
            raw.bgIntensity = 0; raw.bgColorKey = 'gruen';
            localStorage.setItem('fwmc-remember-prefs-v1', JSON.stringify(raw));
        }""")
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(100)
        print("Remember starts at 0%:", await pg.input_value("#rememberBgIntensitySlider"))
        await pg.click('#rememberBgColorPicker .color-swatch[data-key="pink"]'); await pg.wait_for_timeout(80)
        print("Remember colour pick at 0% jumps to 50%:", await pg.input_value("#rememberBgIntensitySlider"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
