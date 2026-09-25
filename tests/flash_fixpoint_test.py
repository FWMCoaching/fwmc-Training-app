import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

# Two fixes together: (1) the flashed digit was rendering in a dark-mode-
# following CSS colour (var(--ink)) while the player's own background is
# always hardcoded white, so on a system in dark mode the digit came out
# pale grey-on-white ("zu durchsichtig") - now hardcoded like every other
# player-scoped element. (2) a togglable, customisable fixation point in
# the middle, matching Periphere Wahrnehmung's Zeichen/Farbe/Größe pattern.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        # Force dark colour-scheme - this is exactly the condition that
        # exposed the low-contrast digit bug.
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme="dark")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)
        await pg.click("#flashAdvanced summary"); await pg.wait_for_timeout(100)

        print("fix group shown by default (Anzeigen active):", "active" in (await pg.get_attribute('#flashFixToggleRow [data-flash-fix="1"]', "class") or ""))
        print("fix options visible by default:", await pg.is_visible("#flashFixOptions"))
        print("fix colour swatch count:", await pg.locator("#flashFixColorPicker .color-swatch").count())

        # --- contrast fix: digit colour must stay dark even in dark mode ---
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        digit_color = await pg.evaluate("() => getComputedStyle(document.getElementById('flashDigitEl')).color")
        print("digit colour is dark navy even in OS dark mode:", digit_color == "rgb(22, 35, 42)")
        input_color = await pg.evaluate("() => getComputedStyle(document.getElementById('flashTypedInput')).color")
        print("input text colour also dark in dark mode:", input_color == "rgb(22, 35, 42)")

        # --- fixpoint on by default, plain grey dot ---
        print("fixpoint visible by default:", await pg.is_hidden("#flashFixpointEl") == False)
        fix_bg = await pg.evaluate("() => getComputedStyle(document.getElementById('flashFixpointEl')).backgroundColor")
        print("default fixpoint is the standard grey dot:", fix_bg == "rgb(143, 162, 168)")
        await pg.screenshot(path=OUT + "flash_fixpoint_default.png")
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)

        # --- toggle off -> hidden in player, options collapse in settings ---
        await pg.click('#flashFixToggleRow [data-flash-fix="0"]'); await pg.wait_for_timeout(80)
        print("fix options collapse when disabled:", await pg.is_hidden("#flashFixOptions"))
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fixpoint hidden in player when disabled:", await pg.is_hidden("#flashFixpointEl"))
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)

        # --- custom character + colour + size ---
        await pg.click('#flashFixToggleRow [data-flash-fix="1"]'); await pg.wait_for_timeout(80)
        await pg.fill("#flashFixCharInput", "X")
        await pg.click('#flashFixColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(80)
        await pg.fill("#flashFixSizeSlider", "1.8"); await pg.dispatch_event("#flashFixSizeSlider", "input")
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        print("custom fixpoint shows the chosen character:", await pg.inner_text("#flashFixpointEl") == "X")
        fix_color = await pg.evaluate("() => getComputedStyle(document.getElementById('flashFixpointEl')).color")
        print("custom fixpoint uses the chosen colour (rot):", fix_color == "rgb(211, 47, 47)")
        await pg.screenshot(path=OUT + "flash_fixpoint_custom.png")
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)

        # --- settings persist across reload, and the Trainingsmodus screen shares them ---
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenTraining"); await pg.wait_for_timeout(150)
        await pg.click("#flashTrainingAdvanced summary"); await pg.wait_for_timeout(100)
        print("Trainingsmodus shows the same saved char:", await pg.input_value("#flashTrainingFixCharInput") == "X")
        print("Trainingsmodus shows the same saved colour (rot active):", "active" in (await pg.get_attribute('#flashTrainingFixColorPicker .color-swatch[data-key="rot"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
