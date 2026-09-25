import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

async def check_no_overlap(pg, min_dist=82):
    boxes = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => e.getBoundingClientRect())")
    n = len(boxes)
    violations = []
    for i in range(n):
        for j in range(i + 1, n):
            cx1, cy1 = boxes[i]["x"] + boxes[i]["width"] / 2, boxes[i]["y"] + boxes[i]["height"] / 2
            cx2, cy2 = boxes[j]["x"] + boxes[j]["width"] / 2, boxes[j]["y"] + boxes[j]["height"] / 2
            dist = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
            if dist < min_dist - 1:  # 1px tolerance for rounding
                violations.append((i, j, round(dist, 1)))
    return n, violations

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

        # Use Training mode with schwer (fast timing) and skip forward a lot to test crowding
        await pg.click('[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.getElementById('rememberStartSlider').value = 12")
        await pg.eval_on_selector("#rememberStartSlider", "el => el.dispatchEvent(new Event('input'))")
        await pg.wait_for_timeout(100)
        await pg.click('#rememberTrainingDifficultyRow [data-remember-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(300)

        n, violations = await check_no_overlap(pg)
        print(f"level 12: {n} markers, overlap violations: {violations}")
        await pg.screenshot(path=OUT + "overlap_level12.png")

        # skip forward repeatedly to stress-test crowding
        for _ in range(8):
            await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(150)
        n, violations = await check_no_overlap(pg)
        print(f"level 20: {n} markers, overlap violations: {violations}")
        await pg.screenshot(path=OUT + "overlap_level20.png")

        for _ in range(10):
            await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(150)
        n, violations = await check_no_overlap(pg)
        print(f"level 30: {n} markers, overlap violations: {violations}")
        await pg.screenshot(path=OUT + "overlap_level30.png")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
