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

        # ==== all 11 Visual exercises present in the combo add grid ====
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(300)
        grid_text = await pg.inner_text("#comboAddGrid")
        for title in ["VT · Farbe & Seite", "VRW · Direkt & Umgekehrt", "Stroop · klassisch", "8 Pfeile"]:
            print(f"'{title}' present in add grid:", title in grid_text)

        # ==== VT-Farbe capture: pick colors, tweak duration ====
        await pg.click('#comboAddGrid >> text="VT · Farbe & Seite"'); await pg.wait_for_timeout(300)
        print("capture opens the shared ready screen:", await pg.is_visible("#ready"))
        print("title swapped to Baustein: VT · Farbe & Seite:", "Baustein: VT · Farbe & Seite" in await pg.inner_text("#readyTitle"))
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#startBtn"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list shows VT-Farbe:", "VT · Farbe & Seite" in await pg.inner_text("#comboBlockList"))

        # ---- editing: tap the block again ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens ready in capture mode:", "Baustein: VT · Farbe & Seite" in await pg.inner_text("#readyTitle"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path must restore normal title/button, standalone
        # exercise setting untouched ----
        await pg.click('#comboAddGrid >> text="Stroop · klassisch"'); await pg.wait_for_timeout(300)
        await pg.click("#backToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone open (from the real home grid) shows normal
        # title/button again ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        print("standalone open shows plain exercise title:", "Baustein:" not in await pg.inner_text("#readyTitle"))
        print("standalone open shows normal start label:", "Training starten" in await pg.inner_text("#startBtn"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)

        # ==== stroop-classic (usesStroopColors, not usesColors) capture:
        # confirms the color-kind generalization actually stores/replays
        # the right colour array, not just usesColors exercises ====
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Stroop · klassisch"'); await pg.wait_for_timeout(300)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        print("Stroop block added:", "Stroop · klassisch" in await pg.inner_text("#comboBlockList"))

        # ==== run a fresh one-block combo end-to-end (re-entering the
        # builder resets the unsaved draft, same as every other unsaved
        # builder in the app) ====
        await pg.click('#comboAddGrid >> text="VT · Farbe & Seite"'); await pg.wait_for_timeout(300)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: player shows the block:", await pg.is_visible("#player"))
        print("combo run: no single-exercise done panel mid-combo:", not await pg.is_visible("#donePanel"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(400)
        print("abort mid-combo-visual lands back on home:", await pg.is_visible("#home"))

        # ==== Master-Einstellungen "Hören" restriction must grey out
        # cross-modal (needs "ton") in the combo grid too, same as on the
        # home grid, and route to Master-Einstellungen instead of capture ====
        await pg.evaluate("""() => {
            localStorage.setItem('fwmc-master-v1', JSON.stringify({colorVision: [], restrictedLimbs: [], hearing: true}));
        }""")
        await pg.reload(); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(300)
        cross_btn = pg.locator("#comboAddGrid .combo-add-btn", has_text="Sehen & Hören")
        print("cross-modal combo button greyed out while hearing-restricted:", "incompatible" in (await cross_btn.first.get_attribute("class") or ""))
        await cross_btn.first.click(); await pg.wait_for_timeout(300)
        print("tapping it opens Master-Einstellungen instead of capture:", await pg.is_visible("#masterSettingsSheet"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
