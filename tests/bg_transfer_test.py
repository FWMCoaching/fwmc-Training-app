import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Covers "Bestehende Farbgestaltung uebernehmen": named presets (saved once,
# usable from any domain with a background setting) plus quick copy of
# another domain's current live colour - both apply the same way a swatch
# click does. Two domains exist today: the shared VT/NAT canvas setting
# (state.bgColorKey/bgIntensity) and Remember's own (rememberPrefs).

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
        await pg.evaluate("() => localStorage.removeItem('fwmc-bg-presets-v1')")

        # --- VT/Periph ready screen: lists the other domain as a source ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("VT source row lists only Remember (not itself):", await pg.locator("#bgSourceRow button").all_inner_texts())
        print("preset group hidden with nothing saved yet:", await pg.is_hidden("#bgPresetGroup"))

        # set + save a named preset from the VT/Periph screen
        await pg.click('#bgColorPicker .color-swatch[data-key="gelb"]'); await pg.wait_for_timeout(80)
        await pg.fill("#bgIntensitySlider", "0.7")
        await pg.dispatch_event("#bgIntensitySlider", "input")
        await pg.wait_for_timeout(80)
        await pg.click("#bgSaveBtn"); await pg.wait_for_timeout(100)
        print("save form opens, save button hides:", await pg.is_visible("#bgSaveForm"), await pg.is_hidden("#bgSaveBtn"))
        await pg.fill("#bgSaveNameInput", "Warmes Gelb")
        await pg.click("#bgSaveConfirmBtn"); await pg.wait_for_timeout(150)
        print("save form closes again:", await pg.is_hidden("#bgSaveForm"))
        print("preset now listed:", await pg.locator("#bgPresetList .bundle-item").count())

        # change VT's live colour away from the saved preset, so the
        # "quick copy from VT" and "load the saved preset" cases diverge
        await pg.click('#bgColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(80)

        # --- Remember: sees both the other domain's LIVE colour and the SAME saved preset ---
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(100)
        print("Remember source row lists only VT/NAT:", await pg.locator("#rememberBgSourceRow button").all_inner_texts())
        print("Remember lists the VT-saved preset too (not domain-scoped):", await pg.locator("#rememberBgPresetList .bundle-item").all_inner_texts())

        await pg.click('#rememberBgSourceRow button:has-text("Visual Training")'); await pg.wait_for_timeout(100)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')||'{}')")
        print("quick-copy picked up VT's CURRENT colour (rot, not the saved preset):", prefs.get("bgColorKey") == "rot")

        await pg.click('#rememberBgPresetList .bundle-item:has-text("Warmes Gelb")'); await pg.wait_for_timeout(100)
        prefs2 = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')||'{}')")
        print("saved preset applied instead (gelb, 0.7):", prefs2.get("bgColorKey") == "gelb" and prefs2.get("bgIntensity") == 0.7)

        # ready-screen picker reflects the applied preset immediately
        print("rememberBgColorPicker shows gelb active:", "active" in (await pg.get_attribute('#rememberBgColorPicker .color-swatch[data-key="gelb"]', "class") or ""))

        # Trainingsmodus screen shares the same preset store
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        await pg.click("#rememberTrainingAdvanced summary"); await pg.wait_for_timeout(100)
        print("Trainingsmodus sees the same saved preset:", await pg.locator("#rememberTrainingBgPresetList .bundle-item").count())

        # delete from the training screen, confirm it's gone everywhere
        await pg.click('#rememberTrainingBgPresetList .bundle-item-wrap:has-text("Warmes Gelb") .combo-block-remove'); await pg.wait_for_timeout(100)
        print("preset group hides itself once empty (training):", await pg.is_hidden("#rememberTrainingBgPresetGroup"))
        await pg.click("#rememberTrainingBackToHome"); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(100)
        print("deletion is visible from the other screen too:", await pg.is_hidden("#rememberBgPresetGroup"))
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)
        # rememberReadyBackToHome already lands on natHome directly
        await pg.click('#natHome .sub-tab[data-nat-sub="peripher"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("deletion visible from VT/Periph screen too:", await pg.is_hidden("#bgPresetGroup"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
