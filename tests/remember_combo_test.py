import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Remember's Kombi-Baukasten capture mode - last item in the documented
# backlog for the Kombi-Baukasten rebuild. Unlike every other domain
# capture-fied so far, none of Remember's 3 modes (fixed/shuffle/
# training) has a natural end on its own, so the capture UI adds a
# duration slider that only exists in combo mode.

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

        # ==== fixed mode: capture, duration slider, commit ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(300)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        print("Remember fixed entry present:", "Positionen merken · Feste Positionen" in await pg.inner_text("#comboAddGrid"))
        print("Remember shuffle entry present:", "Positionen merken · Bewegte Positionen" in await pg.inner_text("#comboAddGrid"))
        print("Remember training entry present:", "Positionen merken · Trainingsmodus" in await pg.inner_text("#comboAddGrid"))

        await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
        print("capture mode opens rememberReady:", await pg.is_visible("#rememberReady"))
        print("title swapped to capture mode:", "Baustein: Positionen merken · Feste Positionen" in await pg.inner_text("#rememberReadyTitle"))
        print("duration slider visible only in capture mode:", await pg.is_visible("#rememberComboDurationGroup"))
        print("duration defaults to 60s:", await pg.input_value("#rememberComboDurationSlider") == "60")
        print("start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#rememberReadyStartBtn"))

        await pg.fill("#rememberComboDurationSlider", "120")
        await pg.dispatch_event("#rememberComboDurationSlider", "input")
        await pg.wait_for_timeout(100)
        print("duration value label updates:", "120" in await pg.inner_text("#rememberComboDurationValue"))

        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        print("commit returns to comboScreen:", await pg.is_visible("#comboScreen"))
        block_text = await pg.inner_text("#comboBlockList")
        print("block list shows Feste Positionen:", "Feste Positionen" in block_text)
        print("block list shows the 2-minute duration:", "2 Min" in block_text)

        # ---- editing: tap the block again, duration should carry over ----
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        print("edit reopens remember capture:", await pg.is_visible("#rememberReady"))
        print("duration carried over into edit:", await pg.input_value("#rememberComboDurationSlider") == "120")
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        print("still exactly 1 block after re-edit+commit:", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- cancel path (back-link) must restore normal title/button and
        # hide the duration slider again ----
        await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(300)
        print("cancel returns to comboScreen:", await pg.is_visible("#comboScreen"))
        print("still exactly 1 block (cancelled add discarded):", await pg.locator("#comboBlockList .chapter-row").count() == 1)

        # ---- standalone entry shows normal title/button again, duration
        # slider hidden, not stuck in capture mode ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(200)
        print("standalone open shows normal title again:", await pg.inner_text("#rememberReadyTitle") == "Feste Positionen")
        print("standalone open shows normal start label again:", "Training starten" in await pg.inner_text("#rememberReadyStartBtn"))
        print("duration slider hidden again standalone:", await pg.is_hidden("#rememberComboDurationGroup"))
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(200)

        # ==== training mode: separate screen, separate duration slider ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Positionen merken · Trainingsmodus"'); await pg.wait_for_timeout(300)
        print("training capture opens rememberTrainingReady:", await pg.is_visible("#rememberTrainingReady"))
        print("training duration slider visible:", await pg.is_visible("#rememberTrainingComboDurationGroup"))
        print("training start button reads 'Baustein übernehmen':", "Baustein übernehmen" in await pg.inner_text("#rememberTrainingStartBtn"))
        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(300)
        print("training block committed:", "Trainingsmodus" in await pg.inner_text("#comboBlockList"))

        # ---- standalone training entry unaffected ----
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(200)
        print("standalone training start label normal:", "Training starten" in await pg.inner_text("#rememberTrainingStartBtn"))
        print("standalone training duration slider hidden:", await pg.is_hidden("#rememberTrainingComboDurationGroup"))
        await pg.click("#rememberTrainingBackToHome"); await pg.wait_for_timeout(200)

        # ==== run a fresh combo end-to-end with a short duration ====
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Positionen merken · Bewegte Positionen"'); await pg.wait_for_timeout(300)
        await pg.fill("#rememberComboDurationSlider", "15")
        await pg.dispatch_event("#rememberComboDurationSlider", "input")
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        print("combo run: rememberPlayer shows the block:", await pg.is_visible("#rememberPlayer"))
        await pg.wait_for_timeout(16000)
        print("combo auto-advances/finishes after the short duration:", await pg.is_visible("#comboDonePanel") or await pg.is_visible("#natHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
