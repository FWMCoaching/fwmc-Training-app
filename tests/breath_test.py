import asyncio
from playwright.async_api import async_playwright
OUT = "screenshots/breath_"
URL = "http://localhost:8845/index.html"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # switch to Atemtraining
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)
        print("breathHome visible:", await pg.is_visible("#breathHome"), "home hidden:", not await pg.is_visible("#home"))
        await pg.screenshot(path=OUT + "01_home.png", full_page=True)

        # tips sheet
        await pg.click("#breathTipsBtn"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=OUT + "02_tips.png")
        await pg.click("#breathTipsCloseBtn"); await pg.wait_for_timeout(150)

        # open box pattern
        cards = pg.locator("#patternGrid .featured-card")
        print("pattern count:", await cards.count())
        await cards.nth(1).click(); await pg.wait_for_timeout(200)  # box
        print("ready title:", await pg.inner_text("#breathReadyTitle"))
        print("phase in value:", await pg.input_value("#phaseInSlider"), "hold1:", await pg.input_value("#phaseHold1Slider"))
        await pg.screenshot(path=OUT + "03_ready_box.png", full_page=True)

        # tweak a slider, verify chip breakdown updates
        await pg.fill("#phaseHold1Slider", "6")
        await pg.eval_on_selector("#phaseHold1Slider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("breakdown after tweak:", await pg.inner_text("#patternBreakdown"))

        # go back and reopen box -> should reset to default 4 (not persisted, since not custom)
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(150)
        await cards.nth(1).click(); await pg.wait_for_timeout(150)
        print("hold1 after reopen (should be 4):", await pg.input_value("#phaseHold1Slider"))

        # custom pattern persistence
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(150)
        await cards.nth(3).click(); await pg.wait_for_timeout(150)  # custom
        print("custom title:", await pg.inner_text("#breathReadyTitle"), "in default:", await pg.input_value("#phaseInSlider"))
        await pg.fill("#phaseInSlider", "3")
        await pg.eval_on_selector("#phaseInSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(150)
        await cards.nth(3).click(); await pg.wait_for_timeout(150)
        print("custom 'in' persisted (should be 3):", await pg.input_value("#phaseInSlider"))

        # all-zero validation
        for sid in ["#phaseInSlider", "#phaseHold1Slider", "#phaseOutSlider", "#phaseHold2Slider"]:
            await pg.fill(sid, "0")
            await pg.eval_on_selector(sid, "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("start disabled at all-zero:", await pg.get_attribute("#breathStartBtn", "disabled") is not None, "help visible:", await pg.is_visible("#phaseHelp"))

        # set a short session: in=1 out=1 (2s cycle), override duration slider min for a fast test
        await pg.fill("#phaseInSlider", "1"); await pg.eval_on_selector("#phaseInSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.fill("#phaseOutSlider", "1"); await pg.eval_on_selector("#phaseOutSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.eval_on_selector("#breathDurationSlider", "el => el.min = '0.05'")
        await pg.fill("#breathDurationSlider", "0.05")
        await pg.eval_on_selector("#breathDurationSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        await pg.screenshot(path=OUT + "04_ready_custom_short.png", full_page=True)

        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(700)
        print("player visible:", await pg.is_visible("#breathPlayer"))
        await pg.screenshot(path=OUT + "05_player.png")
        label1 = await pg.inner_text("#breathPhaseLabel")
        await pg.wait_for_timeout(1100)
        label2 = await pg.inner_text("#breathPhaseLabel")
        print("phase label changed:", label1, "->", label2)
        await pg.screenshot(path=OUT + "06_player_phase2.png")

        # wait for auto-finish (plannedTotal = round(3/2)*2 = 2s already elapsed ~1.8s, should finish soon)
        await pg.wait_for_function("() => !document.getElementById('breathDonePanel').hidden", timeout=8000)
        print("done panel summary:", await pg.inner_text("#breathDoneSummary"))
        await pg.screenshot(path=OUT + "07_done.png")
        await pg.click('#breathRating [data-rate="5"]'); await pg.wait_for_timeout(100)
        await pg.click("#breathDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at breathHome:", await pg.is_visible("#breathHome"))
        await pg.screenshot(path=OUT + "08_home_after.png", full_page=True)

        # abort mid-session test
        await pg.click("#patternGrid .featured-card >> nth=0"); await pg.wait_for_timeout(150)  # coherent
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(150)
        print("aborted -> back at breathReady:", await pg.is_visible("#breathReady"), "player hidden:", not await pg.is_visible("#breathPlayer"))

        # switch back to Visual Training still works
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(100)
        await pg.click('#breathHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
        print("visual home visible:", await pg.is_visible("#home"))
        await pg.click('[data-exercise="vt-color"]'); await pg.wait_for_timeout(150)
        print("visual ready screen still works:", await pg.is_visible("#ready"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
