import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- seed a standalone Cardio-Einheit first, to prove capture
        # mode doesn't clobber it ----
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Schwimmen"'); await pg.wait_for_timeout(150)
        print("standalone setup has 1 item (Schwimmen) before combo work:", await pg.locator("#cardioList .circuit-item-row").count() == 1)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(200)

        # ==== Build a combo with a Cardio block ====
        await pg.click('#cardioHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        print("Cardio group present in add grid:", "Cardio-Einheit" in await pg.inner_text("#comboAddGrid"))
        await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(300)
        print("capture mode opens cardioReady:", await pg.is_visible("#cardioReady"))
        print("title swapped to Baustein: Cardio:", "Baustein: Cardio" in await pg.inner_text("#cardioReadyTitle"))
        print("capture starts blank (0 rows), not the standalone Schwimmen item:", await pg.locator("#cardioList .circuit-item-row").count() == 0)

        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(150)
        await pg.click('#cardioAddGrid >> text="Rad fahren"'); await pg.wait_for_timeout(150)
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#cardioStartBtn"))
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list shows the Cardio block:", "Cardio · 2" in await pg.inner_text("#comboBlockList"))

        # ---- editing: tap the Cardio block again, should reopen with its
        # 2 items, not blank ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens capture with its 2 items:", await pg.locator("#cardioList .circuit-item-row").count() == 2)
        await pg.click('#cardioAddGrid >> text="Walking"'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)
        print("edited block now shows 3 activities:", "Cardio · 3" in await pg.inner_text("#comboBlockList"))

        # ---- cancel path (back-link) must also restore standalone state ----
        await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(300)
        await pg.click('#cardioAddGrid >> text="Treppensteigen"'); await pg.wait_for_timeout(150)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(300)
        print("cancel (back) returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list still shows only the earlier 3-activity block (cancelled add discarded):", "Cardio · 3" in await pg.inner_text("#comboBlockList") and "Cardio · 1" not in await pg.inner_text("#comboBlockList"))

        # ---- standalone Cardio-Einheit (Schwimmen) must be untouched ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        print("standalone setup still has Schwimmen, untouched by capture:", "Schwimmen" in await pg.inner_text("#cardioList"))
        print("standalone setup still has exactly 1 item:", await pg.locator("#cardioList .circuit-item-row").count() == 1)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(200)

        # ==== Run the combo end-to-end: Cardio block should play via the
        # normal cardioPlayer, then advance/finish through the combo, no
        # per-block done panel or history entry along the way. Re-entering
        # the combo builder resets the unsaved draft (same as every other
        # unsaved builder in the app), so build a fresh one-block combo
        # here rather than relying on the earlier (already-verified) draft. ====
        await pg.click('#cardioHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(300)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)
        print("fresh combo draft has 1 Cardio block:", "Cardio · 1" in await pg.inner_text("#comboBlockList"))
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: cardioPlayer shows the block:", await pg.is_visible("#cardioPlayer"))
        print("combo run: no cardio done panel mid-combo:", not await pg.is_visible("#cardioDonePanel"))
        # abort mid-combo via the shared player bar-equivalent (cardioBackBtn)
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(400)
        print("abort mid-combo-cardio returns to combo's own return screen, not cardioReady:", not await pg.is_visible("#cardioReady"))
        print("abort mid-combo-cardio lands back on cardioHome:", await pg.is_visible("#cardioHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
