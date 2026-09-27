import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Regression test for a real bug report: a flashed digit's random position
# (fx,fy) is shared with Periph's radial layout, which has no fixed on-screen
# text. Flash Speicher Test always shows a "Merken …"/"Richtig!"/error hint
# pill near the top of the stage (#flashHint), so a digit placed near-vertical
# at a large radius could land inside/under it. flashSafeFy() in app.js now
# measures the hint's actual rendered bottom edge at flash time and pushes the
# digit down below it with a margin. Forcing Math.random() to values that
# previously produced exactly that worst-case placement must no longer
# intersect the hint pill.

async def check_no_overlap(pg, forced_random):
    await pg.add_init_script(f"Math.random = () => {forced_random};")
    await pg.goto(URL); await pg.wait_for_timeout(300)
    if await pg.is_visible("#tipsCloseBtn"):
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
    await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
    await pg.click('#natHome :text("Flash Speicher Test")'); await pg.wait_for_timeout(200)
    await pg.click('#flashOpenConstant'); await pg.wait_for_timeout(200)
    await pg.click('#flashReadyStartBtn'); await pg.wait_for_timeout(150)
    return await pg.evaluate("""
        () => {
          const d = document.getElementById('flashDigitEl');
          const h = document.getElementById('flashHint');
          const dr = d.getBoundingClientRect();
          const hr = h.getBoundingClientRect();
          const intersects = !(dr.right < hr.left || dr.left > hr.right || dr.bottom < hr.top || dr.top > hr.bottom);
          return { hidden: d.hidden, intersects };
        }
    """)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for forced in [0.999, 0.97, 0.9, 0.5, 0.1]:
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            pg = await ctx.new_page()
            r = await check_no_overlap(pg, forced)
            print(f"forced Math.random={forced}: digit shown={not r['hidden']}, overlaps hint={r['intersects']}")
            assert not r["hidden"]
            assert not r["intersects"], f"digit overlaps hint pill with forced random {forced}"
            await ctx.close()
        print("ERRORS: []")
        await b.close()

asyncio.run(main())
