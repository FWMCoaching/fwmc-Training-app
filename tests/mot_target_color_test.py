import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# MOT-Fähigkeit's target highlight colour ("Farbe des Ziels") is now
# configurable too, same swatch-picker pattern as "Farbe der Objekte" -
# default "gelb" (#f2a900, the exact colour the CSS default used before
# this was configurable). Picked once per round via pickMotColor(), which
# avoids clashing with BOTH the background AND that round's own object
# colour (pickPeriphColor() itself only ever avoids one) - during the
# highlight phase both colours are on screen together and must read as
# clearly different at a glance.

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
        await pg.evaluate("() => localStorage.removeItem('fwmc-mot-prefs-v1')")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)

        print("Farbe des Ziels group visible:", await pg.is_visible("#motTargetColorPicker"))
        print("default target colour is gelb (matches the old fixed #f2a900):", "active" in (await pg.get_attribute('#motTargetColorPicker [data-color="gelb"]', "class") or ""))
        await pg.click('#motTargetColorPicker [data-color="blau"]'); await pg.wait_for_timeout(60)
        await pg.click('#motTargetColorPicker [data-color="gelb"]'); await pg.wait_for_timeout(60)
        pref = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')||'{}').targetColors")
        print("selection persisted (only blau now):", pref == ["blau"])

        # Training screen has its own DOM instance of the same shared prefs
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(100)
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(100)
        await pg.click("#motOpenTraining"); await pg.wait_for_timeout(150)
        print("Training screen shows the same selection (blau active):", "active" in (await pg.get_attribute('#motTrainingTargetColorPicker [data-color="blau"]', "class") or ""))
        await pg.click("#motTrainingBackToHome"); await pg.wait_for_timeout(100)

        # a round actually renders the chosen colour, not the old fixed one
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(100)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        await pg.click("#motAdvanced summary"); await pg.wait_for_timeout(100)
        await pg.fill("#motObjectsSlider", "4"); await pg.dispatch_event("#motObjectsSlider", "input")
        await pg.fill("#motTargetsSlider", "1"); await pg.dispatch_event("#motTargetsSlider", "input")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)

        target_bg = await pg.evaluate("""() => { const el = document.querySelector('#motObjectsLayer .mot-object.target'); return el ? el.style.background : null; }""")
        print("target renders the chosen colour (blau, #1565c0):", target_bg is not None and "21, 101, 192" in target_bg)
        normal_bg = await pg.evaluate("""() => { const el = [...document.querySelectorAll('#motObjectsLayer .mot-object')].find(e => !e.classList.contains('target')); return el ? el.style.background : null; }""")
        print("normal object colour is visually distinct from the target colour:", normal_bg != target_bg)
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)

        # 3D-Optik: target gets a gradient built from the chosen colour, not a hardcoded one
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(100)
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(100)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        await pg.click('#motStyleRow [data-mot-style="3d"]'); await pg.wait_for_timeout(60)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)
        target_bg_3d = await pg.evaluate("""() => { const el = document.querySelector('#motObjectsLayer .mot-object.target'); return el ? el.style.background : null; }""")
        print("3D-Optik target uses a gradient built from the chosen colour:", target_bg_3d is not None and "gradient" in target_bg_3d and "21, 101, 192" in target_bg_3d)
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
