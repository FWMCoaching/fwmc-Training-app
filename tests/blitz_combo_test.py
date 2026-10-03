import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Blitz-Raster's Kombi-Baukasten capture mode - part of the extended
# backlog (Blitz/Flash/MOT all endless/progressive, needing the same
# comboDurationS cutoff Remember already got). Blitz has just one mode,
# so this is the simplest of the three.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("Blitz-Raster entry present:", "Blitz-Raster" in await pg.inner_text("#comboAddGrid"))

        await pg.click('#comboAddGrid >> text="Blitz-Raster"'); await pg.wait_for_timeout(300)
        print("capture mode opens blitzReady:", await pg.is_visible("#blitzReady"))
        print("title swapped to capture mode:", "Baustein: Blitz-Raster" in await pg.inner_text("#blitzReadyTitle"))
        print("duration slider visible only in capture mode:", await pg.is_visible("#blitzComboDurationGroup"))
        print("duration defaults to 60s:", await pg.input_value("#blitzComboDurationSlider") == "60")
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#blitzReadyStartBtn"))

        await pg.fill("#blitzComboDurationSlider", "90")
        await pg.dispatch_event("#blitzComboDurationSlider", "input")
        await pg.wait_for_timeout(100)
        print("duration value label updates:", "90" in await pg.inner_text("#blitzComboDurationValue"))

        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        block_text = await pg.inner_text("#comboBlockList")
        print("block list shows Blitz-Raster:", "Blitz-Raster" in block_text)
        print("block list shows the 1.5-minute duration:", "1:30" in block_text or "1,5 Min" in block_text or "90" in block_text)

        # ---- editing: tap the block again, duration should carry over ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens blitz capture:", await pg.is_visible("#blitzReady"))
        print("duration carried over into edit:", await pg.input_value("#blitzComboDurationSlider") == "90")
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path must restore normal title/button and hide the
        # duration slider again ----
        await pg.click('#comboAddGrid >> text="Blitz-Raster"'); await pg.wait_for_timeout(300)
        await pg.click("#blitzReadyBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone entry shows normal title/button again, duration
        # slider hidden, not stuck in capture mode ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(200)
        print("standalone open shows normal title again:", await pg.inner_text("#blitzReadyTitle") == "Blitz-Raster")
        print("standalone open shows normal start label again:", "Training starten" in await pg.inner_text("#blitzReadyStartBtn"))
        print("duration slider hidden again standalone:", await pg.is_hidden("#blitzComboDurationGroup"))
        await pg.click("#blitzReadyBackToHome"); await pg.wait_for_timeout(200)

        # ==== run a fresh combo end-to-end with a short duration ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Blitz-Raster"'); await pg.wait_for_timeout(300)
        await pg.fill("#blitzComboDurationSlider", "15")
        await pg.dispatch_event("#blitzComboDurationSlider", "input")
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: blitzPlayer shows the block:", await pg.is_visible("#blitzPlayer"))

        # ---- mid-block pause + live bg contrast hint stays alive there too ----
        await pg.click("#blitzPauseBtn"); await pg.wait_for_timeout(200)
        print("pause overlay visible:", await pg.is_visible("#blitzPauseOverlay"))
        await pg.click("#blitzResumeBtn"); await pg.wait_for_timeout(150)

        await pg.wait_for_timeout(16000)
        print("combo auto-advances/finishes after the short duration:", await pg.is_visible("#comboDonePanel") or await pg.is_visible("#natHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
