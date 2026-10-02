import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Flash-Speicher-Test's Kombi-Baukasten capture mode - same shape as
# Remember (3 modes share a ready screen, "training" has its own), plus
# the endless/progressive duration-cutoff Blitz-Raster just got.

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
        grid_text = await pg.inner_text("#comboAddGrid")
        print("Flash Konstant entry present:", "Flash-Speicher-Test · Konstant" in grid_text)
        print("Flash climb entry present:", "Flash-Speicher-Test · Steigend, direkt" in grid_text)
        print("Flash climbRepeat entry present:", "Flash-Speicher-Test · Steigend, mit Wiederholung" in grid_text)
        print("Flash training entry present:", "Flash-Speicher-Test · Trainingsmodus" in grid_text)

        await pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Konstant"'); await pg.wait_for_timeout(300)
        print("capture mode opens flashReady:", await pg.is_visible("#flashReady"))
        print("title swapped to capture mode:", "Baustein: Flash-Speicher-Test · Konstant" in await pg.inner_text("#flashReadyTitle"))
        print("duration slider visible only in capture mode:", await pg.is_visible("#flashComboDurationGroup"))
        print("duration defaults to 60s:", await pg.input_value("#flashComboDurationSlider") == "60")
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#flashReadyStartBtn"))

        await pg.fill("#flashComboDurationSlider", "100")
        await pg.dispatch_event("#flashComboDurationSlider", "input")
        await pg.wait_for_timeout(100)
        print("duration value label updates:", "100" in await pg.inner_text("#flashComboDurationValue"))

        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        block_text = await pg.inner_text("#comboBlockList")
        print("block list shows Flash Konstant:", "Konstant" in block_text)

        # ---- editing: tap the block again, duration should carry over ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens flash capture:", await pg.is_visible("#flashReady"))
        print("duration carried over into edit:", await pg.input_value("#flashComboDurationSlider") == "100")
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path ----
        await pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Konstant"'); await pg.wait_for_timeout(300)
        await pg.click("#flashReadyBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone entry shows normal title/button again, duration
        # slider hidden ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(200)
        print("standalone open shows normal title again:", await pg.inner_text("#flashReadyTitle") == "Konstant")
        print("standalone open shows normal start label again:", "Training starten" in await pg.inner_text("#flashReadyStartBtn"))
        print("duration slider hidden again standalone:", await pg.is_hidden("#flashComboDurationGroup"))
        await pg.click("#flashReadyBackToHome"); await pg.wait_for_timeout(200)

        # ==== training mode: separate screen, separate duration slider ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Trainingsmodus"'); await pg.wait_for_timeout(300)
        print("training capture opens flashTrainingReady:", await pg.is_visible("#flashTrainingReady"))
        print("training duration slider visible:", await pg.is_visible("#flashTrainingComboDurationGroup"))
        print("training start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#flashTrainingStartBtn"))
        await pg.click("#flashTrainingStartBtn"); await pg.wait_for_timeout(300)
        print("training block committed:", "Trainingsmodus" in await pg.inner_text("#comboBlockList"))

        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenTraining"); await pg.wait_for_timeout(200)
        print("standalone training start label normal:", "Training starten" in await pg.inner_text("#flashTrainingStartBtn"))
        print("standalone training duration slider hidden:", await pg.is_hidden("#flashTrainingComboDurationGroup"))
        await pg.click("#flashTrainingBackToHome"); await pg.wait_for_timeout(200)

        # ==== run a fresh combo end-to-end with a short duration ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Steigend, direkt"'); await pg.wait_for_timeout(300)
        await pg.fill("#flashComboDurationSlider", "15")
        await pg.dispatch_event("#flashComboDurationSlider", "input")
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: flashPlayer shows the block:", await pg.is_visible("#flashPlayer"))
        await pg.wait_for_timeout(16000)
        print("combo auto-advances/finishes after the short duration:", await pg.is_visible("#comboDonePanel") or await pg.is_visible("#natHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
