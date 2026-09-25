import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        # seed 12 fake history entries directly via localStorage
        await pg.evaluate("""() => {
            const list = [];
            for (let i = 0; i < 12; i++) {
                list.push({ id: String(i), ts: new Date(Date.now() - i * 3600000).toISOString(), kind: "exercise", title: "Test " + i, seconds: 60, rating: null });
            }
            localStorage.setItem("fwmc-history-v1", JSON.stringify(list));
        }""")
        await pg.reload(); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        print("collapsed row count (should be 3):", await pg.locator("#historyList li").count())
        print("more button text:", await pg.inner_text("#historyMoreBtn"))
        await pg.screenshot(path=OUT + "history_collapsed.png")

        await pg.click("#historyMoreBtn"); await pg.wait_for_timeout(200)
        print("expanded row count (should be 12):", await pg.locator("#historyList li").count())
        print("more button text after expand:", await pg.inner_text("#historyMoreBtn"))
        overflow = await pg.eval_on_selector("#historyList", "el => getComputedStyle(el).overflowY")
        max_h = await pg.eval_on_selector("#historyList", "el => getComputedStyle(el).maxHeight")
        scroll_h = await pg.eval_on_selector("#historyList", "el => el.scrollHeight")
        client_h = await pg.eval_on_selector("#historyList", "el => el.clientHeight")
        print("overflow-y:", overflow, "max-height:", max_h, "scrollHeight:", scroll_h, "clientHeight:", client_h, "-> scrollable:", scroll_h > client_h)
        await pg.screenshot(path=OUT + "history_expanded.png")

        await pg.click("#historyMoreBtn"); await pg.wait_for_timeout(200)
        print("collapsed again row count (should be 3):", await pg.locator("#historyList li").count())

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
