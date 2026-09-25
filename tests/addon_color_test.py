import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# "Farbe der Reize": the peripheral characters (Periphere Wahrnehmung's own,
# and the Zusatzaufgabe's "eigene Feineinstellung" bundle) now have their own
# colour picker under Feineinstellungen, independent of any exercise's own
# arrow/Stroop colour picker. More than one selected colour is "gemischt" -
# each flash rolls its own colour. Whichever colour is picked also has to
# situationally avoid the background colour in effect at that exact moment
# (pickPeriphColor()/colorsClash() - no DOM hook to inspect directly, so this
# suite covers the picker UI/persistence and leans on the runtime smoke tests
# to confirm the new frameBgHex()/pointInPolygon() code paths don't crash
# across a real run of a background-varying exercise (VRW) and an
# arrow-drawing one).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def open_card(exercise_id):
            if await pg.is_visible("#backToHome"):
                await pg.click("#backToHome"); await pg.wait_for_timeout(100)
            await pg.click('.section-tab[data-section="visual"]:visible'); await pg.wait_for_timeout(150)
            await pg.click(f'.excard[data-exercise="{exercise_id}"]'); await pg.wait_for_timeout(150)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # --- Periphere Wahrnehmung's own "Farbe der Reize", under Feineinstellungen ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("colour group visible for Periph under Feineinstellungen:", await pg.is_visible("#periphColorGroup"))
        print("default: schwarz selected:", "active" in (await pg.get_attribute('#periphColorPicker [data-color="schwarz"]', "class") or ""))
        print("single-colour hint shown by default:", "Nur eine Farbe" in (await pg.inner_text("#periphColorHint")))

        # can't deselect the only selected colour
        await pg.click('#periphColorPicker [data-color="schwarz"]'); await pg.wait_for_timeout(60)
        print("can't drop to zero colours:", "active" in (await pg.get_attribute('#periphColorPicker [data-color="schwarz"]', "class") or ""))

        # select a second colour -> "gemischt" hint
        await pg.click('#periphColorPicker [data-color="rot"]'); await pg.wait_for_timeout(60)
        print("gemischt hint once 2+ colours are selected:", "Gemischt" in (await pg.inner_text("#periphColorHint")))
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')||'{}').periphColors")
        print("both colours persisted to prefs:", set(prefs) == {"schwarz", "rot"})

        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("selection survives reload:",
              "active" in (await pg.get_attribute('#periphColorPicker [data-color="schwarz"]', "class") or "") and
              "active" in (await pg.get_attribute('#periphColorPicker [data-color="rot"]', "class") or ""))

        # --- Zusatzaufgabe's own "Farbe der Reize" (eigen mode), independent per exercise ---
        await open_card("4-straight")
        await pg.click('#addonPhaseRow [data-addon-phase="reiz"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-addon-mode="eigen"]'); await pg.wait_for_timeout(60)
        print("addon colour picker visible in eigen mode:", await pg.is_visible("#addonColorPicker"))
        print("addon colour default: schwarz:", "active" in (await pg.get_attribute('#addonColorPicker [data-color="schwarz"]', "class") or ""))
        await pg.click('#addonColorPicker [data-color="blau"]'); await pg.wait_for_timeout(60)
        await pg.click('#addonColorPicker [data-color="gelb"]'); await pg.wait_for_timeout(60)
        store = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-addon-v1')||'{}')")
        print("addon colours stored per-exercise:", set(store.get("4-straight", {}).get("own", {}).get("colors", [])) == {"schwarz", "blau", "gelb"})

        await open_card("4-diag")
        await pg.click('#addonPhaseRow [data-addon-phase="reiz"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-addon-mode="eigen"]'); await pg.wait_for_timeout(60)
        print("a different exercise's addon colours start at the default (schwarz only):",
              "active" in (await pg.get_attribute('#addonColorPicker [data-color="schwarz"]', "class") or "") and
              "active" not in (await pg.get_attribute('#addonColorPicker [data-color="blau"]', "class") or ""))

        # --- runtime smoke tests: the new frameBgHex()/pointInPolygon() logic
        # runs across a real session without crashing, for both a
        # background-varying exercise (VRW) and an arrow-drawing one. ---
        await open_card("vrw-original")
        await pg.click('#addonPhaseRow [data-addon-phase="pause"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-addon-phase="reiz"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-addon-mode="eigen"]'); await pg.wait_for_timeout(60)
        for key in ["rot", "gruen", "gelb", "orange", "lila", "pink", "weiss"]:
            await pg.click(f'#addonColorPicker [data-color="{key}"]'); await pg.wait_for_timeout(20)
        await pg.fill("#addonStimulusSlider", "0.4"); await pg.dispatch_event("#addonStimulusSlider", "input")
        await pg.fill("#addonIntervalMinSlider", "0.5"); await pg.dispatch_event("#addonIntervalMinSlider", "input")
        await pg.fill("#addonIntervalMaxSlider", "1.5"); await pg.dispatch_event("#addonIntervalMaxSlider", "input")
        await pg.click("#startBtn"); await pg.wait_for_timeout(3500)
        print("VRW (background-varying) runs with a busy add-on, no crash:", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await open_card("4-straight")
        await pg.click("#startBtn"); await pg.wait_for_timeout(3000)
        print("arrow exercise runs with its own eigen add-on config, no crash:", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
