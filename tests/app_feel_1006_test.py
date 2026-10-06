import asyncio
from playwright.async_api import async_playwright

# Fabian 2026-10-06, A/B/C: "Training starten" stays visible on long exercise
# pages (A), › / ↗ on the Mehr list (B), every Heute calendar button >= 44 px
# with ‹ › in their own row and the week range (C).
BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for w in (375, 1024):
            ctx = await b.new_context(viewport={"width": w, "height": 700}, service_workers="block")
            await ctx.add_init_script(INIT)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
            sizes = await pg.evaluate("""() => [...document.querySelectorAll('.today-week button')].filter(b => b.getClientRects().length)
              .map(b => { const r = b.getBoundingClientRect(); return [b.id || b.className, r.width, r.height]; })""")
            small = [s for s in sizes if s[1] < 44 or s[2] < 44]
            check(f"[{w}] all calendar buttons >= 44 px", not small, small[:3])
            check(f"[{w}] week range shown", "Oktober" in await pg.inner_text("#todayWeekRange") or len((await pg.inner_text("#todayWeekRange")).strip()) > 4, await pg.inner_text("#todayWeekRange"))
            await pg.click("#todayWeekNext"); await pg.wait_for_timeout(150)
            r2 = await pg.inner_text("#todayWeekRange")
            await pg.click("#todayWeekPrev"); await pg.wait_for_timeout(150)
            check(f"[{w}] range follows ‹ ›", r2 != await pg.inner_text("#todayWeekRange"), r2)
            await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(200)
            marks = await pg.evaluate("""() => [...document.querySelectorAll('#moreScreen .more-list .featured-card')].map(c => getComputedStyle(c, '::after').content)""")
            check(f"[{w}] Mehr: › inside the app, ↗ for links out", marks[:4] == ['"›"'] * 4 and all(m == '"↗"' for m in marks[4:]), marks)
            await pg.goto(BASE + "index.html?bereich=movement"); await pg.wait_for_timeout(300)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
            for y in (0, 400):
                await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(150)
                st = await pg.evaluate("""() => { const b = document.getElementById('movementStartBtn').getBoundingClientRect();
                  const n = document.getElementById('bottomNav').getBoundingClientRect(); return [b.top, b.bottom, n.top, innerHeight]; }""")
                check(f"[{w}] start button visible above the bottom bar (scroll {y})", st[0] >= 0 and st[1] <= st[2] + 1, st)
            await pg.click("#movementStartBtn"); await pg.wait_for_timeout(600)
            check(f"[{w}] sticky start button still starts", await pg.evaluate("!!document.querySelector('.player:not([hidden])')"))
            cnt = await pg.evaluate("document.querySelectorAll('.screen > .start-btn.start-sticky').length")
            check(f"[{w}] every exercise page start button is sticky", cnt >= 40, cnt)
            await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "FAILED")

asyncio.run(main())
