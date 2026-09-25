import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

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
        await pg.click("#rememberOpenShuffle"); await pg.wait_for_timeout(150)
        await pg.click('[data-remember-error="stay"]'); await pg.wait_for_timeout(100)
        await pg.click('#rememberDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(900)

        markers = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => e.dataset.num)")
        wrong_target = next(n for n in markers if n != "1")
        await click_num(pg, wrong_target); await pg.wait_for_timeout(150)
        print("hint on stay wrong click:", await pg.inner_text("#rememberHint"))
        await pg.wait_for_timeout(1400 + 1000)
        print("level after stay reset (should remain 2 Zahlen):", await pg.inner_text("#rememberLevelEl"))

        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
