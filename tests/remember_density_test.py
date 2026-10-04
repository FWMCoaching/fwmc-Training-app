import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Positionen merken at the maximum of 24 markers: no two markers may ever be
# closer than the minimum (marker size + 10 px; markers shrink to 52 px on a
# small screen so 24 still fit above the control bar) (was a known open item - ~2 of 3 layouts had
# an overlap). Repeated runs, both position modes, two phone sizes.


async def violations(pg):
    min_dist = await pg.eval_on_selector(".remember-marker", "e => e.getBoundingClientRect().width + 10")
    pts = await pg.eval_on_selector_all(".remember-marker", "els => els.map(e => { const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })")
    bad = 0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if ((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2) ** 0.5 < min_dist - 1:
                bad += 1
    return len(pts), bad


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for vw, vh in ((390, 844), (375, 667)):
            ctx = await b.new_context(viewport={"width": vw, "height": vh}, service_workers="block")
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
            await pg.goto(URL); await pg.wait_for_timeout(400)
            if await pg.is_visible("#tipsCloseBtn"):
                await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
            for mode in ("shuffle", "fixed"):
                worst, counts = 0, set()
                for run in range(5):
                    await pg.click('.section-tab[data-section="nat"] >> visible=true'); await pg.wait_for_timeout(150)
                    await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(100)
                    await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(150)
                    await pg.evaluate("document.getElementById('rememberStartSlider').value = 16")
                    await pg.eval_on_selector("#rememberStartSlider", "el => el.dispatchEvent(new Event('input'))")
                    await pg.click(f'#rememberTrainingPositionRow [data-remember-position="{mode}"]')
                    await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(250)
                    for _ in range(8):
                        await pg.click("#rememberNavNextBtn"); await pg.wait_for_timeout(80)
                    n, bad = await violations(pg)
                    counts.add(n); worst = max(worst, bad)
                    await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
                    if await pg.is_visible("#confirmSheet"):
                        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
                    for sel in ("#rememberDoneBackBtn", "#rememberTrainingBackToHome"):
                        if await pg.is_visible(sel):
                            await pg.click(sel); await pg.wait_for_timeout(150)
                print(f"{vw}x{vh} {mode}: 24 markers shown:", counts == {24}, counts)
                print(f"{vw}x{vh} {mode}: no overlap in 5 runs:", worst == 0, worst)
            await ctx.close()
        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
