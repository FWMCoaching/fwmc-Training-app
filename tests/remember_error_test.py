import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

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

        # ---- Training: startzahl up to 16, position mode toggle ----
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        max_attr = await pg.get_attribute("#rememberStartSlider", "max")
        print("training start slider max:", max_attr)
        await pg.evaluate("document.getElementById('rememberStartSlider').value = 16")
        await pg.eval_on_selector("#rememberStartSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        print("start value shows 16:", await pg.inner_text("#rememberStartValue"))
        print("position row exists:", await pg.locator("#rememberTrainingPositionRow").count())
        await pg.click('[data-remember-position="fixed"]'); await pg.wait_for_timeout(100)
        print("fixed active:", "active" in (await pg.get_attribute('[data-remember-position="fixed"]', "class") or ""))
        await pg.click('#rememberTrainingDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-remember-progress="1"]'); await pg.wait_for_timeout(100)

        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(1600)  # schwer @ level16 reveal ~0.7+14*0.15=2.8s, wait a bit more below
        await pg.wait_for_timeout(1500)
        markers = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => ({num: e.dataset.num, left: e.style.left, top: e.style.top}))")
        pos_map = {m["num"]: (m["left"], m["top"]) for m in markers}
        print("training level-16 marker count:", len(markers))

        # skip forward to 17 -> numbers 1-16 should KEEP their exact position (fixed mode)
        await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(2500)
        markers2 = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => ({num: e.dataset.num, left: e.style.left, top: e.style.top}))")
        pos_map2 = {m["num"]: (m["left"], m["top"]) for m in markers2}
        kept = all(pos_map.get(k) == pos_map2.get(k) for k in pos_map)
        print("FIXED training mode: positions 1-16 kept exactly after skip-forward:", kept, "count now:", len(markers2))

        # skip back down to 16, then to configured start (16) - clamp check, positions should match original cache too
        await pg.click("#rememberNavPrevBtn"); await pg.wait_for_timeout(2500)
        markers3 = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => ({num: e.dataset.num, left: e.style.left, top: e.style.top}))")
        pos_map3 = {m["num"]: (m["left"], m["top"]) for m in markers3}
        kept_back = all(pos_map.get(k) == pos_map3.get(k) for k in pos_map)
        print("FIXED training mode: positions still match after skip back down:", kept_back)

        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)
        print("debug: donePanel visible:", await pg.is_visible("#rememberDonePanel"),
              "trainingReady visible:", await pg.is_visible("#rememberTrainingReady"),
              "natHome visible:", await pg.is_visible("#natHome"))
        if await pg.is_visible("#rememberDonePanel"):
            await pg.click("#rememberDoneBackBtn"); await pg.wait_for_timeout(150)
        elif await pg.is_visible("#rememberTrainingReady"):
            await pg.click("#rememberTrainingBackToHome"); await pg.wait_for_timeout(150)

        # ---- Fixed/Shuffle: "Bei Fehler" options ----
        if not await pg.is_visible("#natHome"):
            await pg.click('[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        print("error row exists:", await pg.locator("#rememberErrorRow").count())
        print("default error mode active (reset2):", "active" in (await pg.get_attribute('[data-remember-error="reset2"]', "class") or ""))

        # set "Eine Zahl zurück" (backOne), schwer for speed
        await pg.click('[data-remember-error="backOne"]'); await pg.wait_for_timeout(100)
        await pg.click('#rememberDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(900)  # level2 reveal ~0.7s -> covered
        await click_num(pg, "1"); await pg.wait_for_timeout(150)
        await click_num(pg, "2"); await pg.wait_for_timeout(150)
        await pg.wait_for_timeout(900 + 1100)  # success + level3 reveal (~0.7+0.15=0.85s)
        # now at level 3, click wrong on purpose
        markers = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => e.dataset.num)")
        print("at level:", await pg.inner_text("#rememberLevelEl"))
        # nextExpected is always 1 at the start of a fresh level, so clicking
        # anything else is guaranteed wrong.
        wrong_target = next(n for n in markers if n != "1")
        await click_num(pg, wrong_target); await pg.wait_for_timeout(150)
        print("hint on backOne wrong click:", await pg.inner_text("#rememberHint"))
        await pg.wait_for_timeout(1400 + 1000)
        print("level after backOne reset (should be 2 Zahlen, was at 3):", await pg.inner_text("#rememberLevelEl"))

        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
