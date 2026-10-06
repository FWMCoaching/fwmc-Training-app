import asyncio
from playwright.async_api import async_playwright

# Fabian 2026-10-06: "Zurückwischen vom linken Rand geht nicht" (Safari).
# In Safari iOS owns the edge swipe and goes back in the browser history,
# so every deeper page gets a history entry and popstate taps the visible ‹.
# Also covers Android's back gesture and the browser back button.
BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

VIS = "() => [...document.querySelectorAll('.screen')].filter(e => !e.hidden && e.getClientRects().length).map(e => e.id).join('+')"
DEPTH = "() => (history.state && history.state.fwmc) || 0"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        start_len = await pg.evaluate("history.length")
        check("Heute: no extra entry", await pg.evaluate(DEPTH) == 0)
        await pg.click('#bottomNav [data-nav="training"]'); await pg.wait_for_timeout(200)
        check("bottom bar switch adds no entry", await pg.evaluate("history.length") == start_len)
        await pg.click('#trainingHub [data-area="movement"], #trainingHub .hub-tile >> nth=0'); await pg.wait_for_timeout(200)
        area = await pg.evaluate(VIS)
        check("area page adds one entry", await pg.evaluate(DEPTH) == 1, area)
        await pg.click(f"#{area} .bar-back-btn"); await pg.wait_for_timeout(200)
        check("in-app ‹ goes back and drops the entry", await pg.evaluate(VIS) == "trainingHub" and await pg.evaluate(DEPTH) == 0)

        await pg.goto(BASE + "index.html?bereich=movement"); await pg.wait_for_timeout(300)
        check("opened on an area: one entry back to Training", await pg.evaluate(DEPTH) == 1)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        check("deeper page: depth 2", await pg.evaluate(DEPTH) == 2 and await pg.evaluate(VIS) == "movementReady")
        await pg.go_back(); await pg.wait_for_timeout(300)
        check("browser back (= Safari edge swipe) goes back one page", await pg.evaluate(VIS) == "movementHome", await pg.evaluate(VIS))
        await pg.go_back(); await pg.wait_for_timeout(300)
        check("second back lands on Training, still in the app", await pg.evaluate(VIS) == "trainingHub" and "localhost" in pg.url, await pg.evaluate(VIS))
        # back with a sheet open does not change the page under it
        await pg.goto(BASE + "index.html?bereich=movement"); await pg.wait_for_timeout(300)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#movementReady .master-settings-btn"); await pg.wait_for_timeout(200)
        sheet = await pg.evaluate("!!document.querySelector('.sheet:not([hidden])')")
        await pg.go_back(); await pg.wait_for_timeout(300)
        check("back with a sheet open keeps the page", sheet and await pg.evaluate(VIS) == "movementReady", str(sheet))
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "FAILED")

asyncio.run(main())
