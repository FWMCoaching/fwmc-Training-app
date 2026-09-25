import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def get_markers(pg):
    return await pg.eval_on_selector_all(".remember-marker", """els => els.map(e => ({
        num: e.dataset.num, left: e.style.left, top: e.style.top, covered: e.classList.contains('covered')
    }))""")

async def click_num(pg, n):
    await pg.click(f'.remember-marker[data-num="{n}"]')

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        print("remember panel visible:", await pg.is_visible("#natRememberPanel"))
        print("3 cards present:", await pg.locator("#natRememberPanel .featured-card").count())
        print("best fixed text initially empty:", (await pg.inner_text("#rememberBestFixed")) == "")

        # ---- open FIXED ready screen, pick Schwer for fast timing ----
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        print("rememberReady visible:", await pg.is_visible("#rememberReady"))
        print("ready title:", await pg.inner_text("#rememberReadyTitle"))
        await pg.click('#rememberDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        print("schwer active:", "active" in (await pg.get_attribute('#rememberDifficultyRow [data-remember-diff="schwer"]', "class") or ""))
        print("custom hint hidden after picking a preset:", await pg.is_hidden("#rememberDiffCustom"))

        # move a slider -> should now show "custom", value should update, no scroll-to-top navigation bug
        await pg.evaluate("document.getElementById('rememberRevealSlider').value = 2.0")
        await pg.eval_on_selector("#rememberRevealSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("custom hint visible after moving a slider:", await pg.is_visible("#rememberDiffCustom"))
        print("still on rememberReady (no unwanted re-navigation):", await pg.is_visible("#rememberReady"))

        # go back to Mittel for a clean run, then start
        await pg.click('#rememberDifficultyRow [data-remember-diff="mittel"]'); await pg.wait_for_timeout(100)
        await pg.click("#rememberReadyStartBtn")
        print("player visible:", await pg.is_visible("#rememberPlayer"))
        print("nav hidden for fixed/shuffle mode:", await pg.is_hidden("#rememberNav"))
        await pg.wait_for_timeout(1300)  # mittel level-2 reveal ~1.1s
        markers = await get_markers(pg)
        print("markers covered:", all(m["covered"] for m in markers), "count:", len(markers))
        pos_before = {m["num"]: (m["left"], m["top"]) for m in markers}

        await click_num(pg, "1"); await pg.wait_for_timeout(150)
        await click_num(pg, "2"); await pg.wait_for_timeout(150)
        await pg.wait_for_timeout(900 + 1700)  # success pause + level-3 reveal (~1.4s)
        markers = await get_markers(pg)
        pos_after = {m["num"]: (m["left"], m["top"]) for m in markers}
        print("FIXED: numbers 1/2 kept position after advancing:", pos_before.get("1") == pos_after.get("1") and pos_before.get("2") == pos_after.get("2"))

        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
        print("done panel visible:", await pg.is_visible("#rememberDonePanel"))
        print("done summary:", await pg.inner_text("#rememberDoneSummary"))
        await pg.click("#rememberDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at natHome:", await pg.is_visible("#natHome"))
        print("card best now shows a score:", "Bestleistung" in await pg.inner_text("#rememberBestFixed"))

        # differentiated best: switch to Leicht, should show "noch keine Bestleistung" there
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click('#rememberDifficultyRow [data-remember-diff="leicht"]'); await pg.wait_for_timeout(100)
        print("best hint at Leicht (should say none yet):", await pg.inner_text("#rememberReadyBestHint"))
        await pg.click('#rememberDifficultyRow [data-remember-diff="mittel"]'); await pg.wait_for_timeout(100)
        print("best hint back at Mittel (should show the score):", await pg.inner_text("#rememberReadyBestHint"))

        # quit-without-progress -> back to rememberReady, not natHome
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(150)
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
        print("quit w/o progress -> back at rememberReady (not natHome):", await pg.is_visible("#rememberReady"))

        # ---- Trainingsmodus ----
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        print("trainingReady visible:", await pg.is_visible("#rememberTrainingReady"))
        await pg.evaluate("document.getElementById('rememberStartSlider').value = 6")
        await pg.eval_on_selector("#rememberStartSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("start value shows 6:", await pg.inner_text("#rememberStartValue"))
        await pg.click('[data-remember-progress="0"]'); await pg.wait_for_timeout(100)
        print("'bei dieser Zahl bleiben' active:", "active" in (await pg.get_attribute('[data-remember-progress="0"]', "class") or ""))
        await pg.click('#rememberTrainingDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(150)
        print("player visible (training):", await pg.is_visible("#rememberPlayer"))
        print("nav visible for training mode:", await pg.is_visible("#rememberNav"))
        print("level label shows 6 Zahlen:", await pg.inner_text("#rememberLevelEl"))

        await pg.wait_for_timeout(900)  # schwer level-6 reveal: 0.7+4*0.15=1.3s -> not fully done yet, still covering soon
        await pg.wait_for_timeout(500)
        markers = await get_markers(pg)
        print("training: marker count at start level 6:", len(markers))
        for n in range(1, 7):
            await click_num(pg, str(n)); await pg.wait_for_timeout(120)
        await pg.wait_for_timeout(900 + 300)
        print("stayed at 6 after success (bei dieser Zahl bleiben):", await pg.inner_text("#rememberLevelEl"))

        # manual skip forward to 8, then back down
        await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(100)
        print("after skip-forward once:", await pg.inner_text("#rememberLevelEl"))
        await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(100)
        print("after skip-forward twice (should be 8):", await pg.inner_text("#rememberLevelEl"))
        await pg.click("#rememberNavPrevBtn"); await pg.wait_for_timeout(100)
        print("after skip-back once (should be 7):", await pg.inner_text("#rememberLevelEl"))
        # try to go below the configured start (6) - should clamp at 6
        await pg.click("#rememberNavPrevBtn"); await pg.wait_for_timeout(100)
        await pg.click("#rememberNavPrevBtn"); await pg.wait_for_timeout(100)
        await pg.click("#rememberNavPrevBtn"); await pg.wait_for_timeout(100)
        print("clamped at configured start (should be 6, not below):", await pg.inner_text("#rememberLevelEl"))

        # wrong click should reset to the configured start (6), not 2
        await pg.wait_for_timeout(1600)  # let it cover
        markers = await get_markers(pg)
        wrong_num = markers[0]["num"]
        # click a definitely-wrong one (not "1") if possible
        target = "2" if wrong_num != "2" else "1"
        await click_num(pg, target); await pg.wait_for_timeout(1600)
        print("after wrong click, reset to configured start (6, not 2):", await pg.inner_text("#rememberLevelEl"))

        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
        print("training run finished without crashing")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
