import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Objektverfolgung (MOT)'s Kombi-Baukasten capture mode - same shape as Remember/
# Flash (3 modes share a ready screen, "training" has its own), plus the
# endless/progressive duration-cutoff the other 3 NAT sub-exercises got.

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
        print("MOT speed entry present:", "Objektverfolgung (MOT) · Tempo steigt" in grid_text)
        print("MOT count entry present:", "Objektverfolgung (MOT) · Anzahl steigt" in grid_text)
        print("MOT both entry present:", "Objektverfolgung (MOT) · Beides steigt" in grid_text)
        print("MOT training entry present:", "Objektverfolgung (MOT) · Trainingsmodus" in grid_text)

        await pg.click('#comboAddGrid >> text="Objektverfolgung (MOT) · Tempo steigt"'); await pg.wait_for_timeout(300)
        print("capture mode opens motReady:", await pg.is_visible("#motReady"))
        print("title swapped to capture mode:", "Baustein: Objektverfolgung (MOT) · Tempo steigt" in await pg.inner_text("#motReadyTitle"))
        print("duration slider visible only in capture mode:", await pg.is_visible("#motComboDurationGroup"))
        print("duration defaults to 60s:", await pg.input_value("#motComboDurationSlider") == "60")
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#motReadyStartBtn"))

        await pg.fill("#motComboDurationSlider", "110")
        await pg.dispatch_event("#motComboDurationSlider", "input")
        await pg.wait_for_timeout(100)
        print("duration value label updates:", "110" in await pg.inner_text("#motComboDurationValue"))

        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        block_text = await pg.inner_text("#comboBlockList")
        print("block list shows MOT Tempo steigt:", "Tempo steigt" in block_text)

        # ---- editing: tap the block again, duration should carry over ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens mot capture:", await pg.is_visible("#motReady"))
        print("duration carried over into edit:", await pg.input_value("#motComboDurationSlider") == "110")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path ----
        await pg.click('#comboAddGrid >> text="Objektverfolgung (MOT) · Tempo steigt"'); await pg.wait_for_timeout(300)
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone entry shows normal title/button again, duration
        # slider hidden ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(200)
        print("standalone open shows normal title again:", await pg.inner_text("#motReadyTitle") == "Tempo steigt")
        print("standalone open shows normal start label again:", "Training starten" in await pg.inner_text("#motReadyStartBtn"))
        print("duration slider hidden again standalone:", await pg.is_hidden("#motComboDurationGroup"))
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(200)

        # ==== training mode: separate screen, separate duration slider ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Objektverfolgung (MOT) · Trainingsmodus"'); await pg.wait_for_timeout(300)
        print("training capture opens motTrainingReady:", await pg.is_visible("#motTrainingReady"))
        print("training duration slider visible:", await pg.is_visible("#motTrainingComboDurationGroup"))
        print("training start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#motTrainingStartBtn"))
        await pg.click("#motTrainingStartBtn"); await pg.wait_for_timeout(300)
        print("training block committed:", "Trainingsmodus" in await pg.inner_text("#comboBlockList"))

        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenTraining"); await pg.wait_for_timeout(200)
        print("standalone training start label normal:", "Training starten" in await pg.inner_text("#motTrainingStartBtn"))
        print("standalone training duration slider hidden:", await pg.is_hidden("#motTrainingComboDurationGroup"))
        await pg.click("#motTrainingBackToHome"); await pg.wait_for_timeout(200)

        # ==== run a fresh combo end-to-end with a short duration ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Objektverfolgung (MOT) · Anzahl steigt"'); await pg.wait_for_timeout(300)
        await pg.fill("#motComboDurationSlider", "15")
        await pg.dispatch_event("#motComboDurationSlider", "input")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: motPlayer shows the block:", await pg.is_visible("#motPlayer"))

        # ---- mid-block pause ----
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        print("pause overlay visible:", await pg.is_visible("#motPauseOverlay"))
        await pg.click("#motResumeBtn"); await pg.wait_for_timeout(150)

        await pg.wait_for_timeout(16000)
        print("combo auto-advances/finishes after the short duration:", await pg.is_visible("#comboDonePanel") or await pg.is_visible("#natHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
