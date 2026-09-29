import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)

        # ==== Cycle-pattern (Box-Atmung) capture ====
        await pg.click('#breathHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        grid_text = await pg.inner_text("#comboAddGrid")
        print("all 4 patterns + Wim Hof present in add grid:",
              all(t in grid_text for t in ["Ruhige Atmung (Kohärenz)", "Box-Atmung", "4-7-8", "Eigenes Muster", "Kraftvolle Atmung"]))
        await pg.click('#comboAddGrid >> text="Box-Atmung"'); await pg.wait_for_timeout(300)
        print("capture opens breathReady:", await pg.is_visible("#breathReady"))
        print("title swapped to Baustein: Box-Atmung:", "Baustein: Box-Atmung" in await pg.inner_text("#breathReadyTitle"))
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#breathStartBtn"))
        # tweak the duration before committing
        await pg.click('[data-breath-dur="10"]'); await pg.wait_for_timeout(100)
        print("duration UI shows the tweak before commit:", "10 Min" in await pg.inner_text("#breathDurationValue"))
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("block list shows Box-Atmung:", "Box-Atmung" in await pg.inner_text("#comboBlockList"))
        print("block list shows the tweaked 10 Min duration:", "10 Min" in await pg.inner_text("#comboBlockList"))

        # ---- editing: tap the block again, should reopen with 10 Min ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens breathReady in capture mode:", "Baustein: Box-Atmung" in await pg.inner_text("#breathReadyTitle"))
        print("edit shows the previously-set 10 Min:", "10 Min" in await pg.inner_text("#breathDurationValue"))
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path must restore normal title/button ----
        await pg.click('#comboAddGrid >> text="Ruhige Atmung (Kohärenz)"'); await pg.wait_for_timeout(300)
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone open shows normal title/button again, own
        # duration untouched by the capture's 10-Min tweak (global durationMin
        # was restored on both commit-exit and cancel-exit above) ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(200)
        print("standalone open shows plain pattern title:", "Baustein:" not in await pg.inner_text("#breathReadyTitle"))
        print("standalone open shows normal start label:", "Atemtraining starten" in await pg.inner_text("#breathStartBtn"))
        print("standalone duration back to the original 5 Min (not the capture's 10):", "5 Min" in await pg.inner_text("#breathDurationValue"))
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(200)

        # ==== Wim Hof capture ====
        await pg.click('#breathHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text=Kraftvolle Atmung'); await pg.wait_for_timeout(300)
        print("Wim Hof capture opens wimhofReady:", await pg.is_visible("#wimhofReady"))
        print("start disabled before ack checked:", await pg.is_disabled("#wimhofStartBtn"))
        await pg.click("#wimhofAckCheck"); await pg.wait_for_timeout(100)
        print("start reads 'Baustein übernehmen' once acked:", "Baustein übernehmen" in await pg.inner_text("#wimhofStartBtn"))
        await pg.click("#wimhofStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        # re-entering the combo builder reset the unsaved draft (same as
        # every other unsaved builder in the app), so this is a fresh
        # one-block draft, not the earlier Box-Atmung block too.
        print("block list shows the Wim Hof block:", "Kraftvolle Atmung" in await pg.inner_text("#comboBlockList"))

        # ---- standalone Wim Hof entry still requires a fresh ack, normal label ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .fc-title", has_text="Kraftvolle Atmung").click(); await pg.wait_for_timeout(200)
        print("standalone Wim Hof ack unchecked again:", not await pg.is_checked("#wimhofAckCheck"))
        await pg.click("#wimhofAckCheck"); await pg.wait_for_timeout(100)
        print("standalone start label normal (not 'Baustein übernehmen'):", "Kraftvolle Atmung starten" in await pg.inner_text("#wimhofStartBtn"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
