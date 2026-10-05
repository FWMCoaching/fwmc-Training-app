import asyncio
from playwright.async_api import async_playwright

# Fenster nach unten wegziehen (Fabian, 2026-10-05): every bottom sheet has a
# grab bar; at the top of its content a long/fast pull down closes it, a short
# one snaps back, and a pull while scrolled down only scrolls.
BASE = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def drag(cdp, x, y0, y1, steps=8, pause=0.012):
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y0}]})
    for i in range(1, steps + 1):
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y0 + (y1 - y0) * i / steps}]})
        await asyncio.sleep(pause)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        cdp = await ctx.new_cdp_session(pg)
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        n = await pg.evaluate("[...document.querySelectorAll('.sheet > .sheet-inner')].filter(i => i.firstElementChild && i.firstElementChild.classList.contains('sheet-grab')).length")
        total = await pg.evaluate("document.querySelectorAll('.sheet > .sheet-inner').length")
        check("every sheet has a grab bar", n == total and total >= 8, (n, total))

        async def open_master():
            await pg.evaluate("document.querySelector('#home .master-settings-btn').click()"); await pg.wait_for_timeout(300)
        async def top_of(sel):
            r = await pg.evaluate(f"(() => {{ const r = document.querySelector('{sel} .sheet-inner').getBoundingClientRect(); return [r.left + r.width / 2, r.top]; }})()")
            return r
        await open_master()
        check("Grundeinstellungen open", await pg.is_visible("#masterSettingsSheet"))
        x, top = await top_of("#masterSettingsSheet")
        await drag(cdp, x, top + 30, top + 60); await pg.wait_for_timeout(350)
        check("short pull snaps back", await pg.is_visible("#masterSettingsSheet"))
        await drag(cdp, x, top + 30, top + 330, steps=10); await pg.wait_for_timeout(400)
        check("long pull closes Grundeinstellungen", not await pg.is_visible("#masterSettingsSheet"))
        check("page scroll lock released", await pg.evaluate("getComputedStyle(document.body).overflowY") != "hidden")
        await open_master()
        await pg.evaluate("document.querySelector('#masterSettingsSheet .sheet-inner').scrollTop = 300"); await pg.wait_for_timeout(100)
        x, top = await top_of("#masterSettingsSheet")
        await drag(cdp, x, top + 200, top + 400, steps=10); await pg.wait_for_timeout(400)
        check("pull while scrolled down does not close", await pg.is_visible("#masterSettingsSheet"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
        # a sheet with its own close path (FAQ), fast flick
        await pg.evaluate("document.querySelector('.faq-open-btn').click()"); await pg.wait_for_timeout(300)
        check("FAQ open", await pg.is_visible("#faqSheet"))
        x, top = await top_of("#faqSheet")
        await drag(cdp, x, top + 20, top + 110, steps=4, pause=0.01); await pg.wait_for_timeout(400)
        check("fast flick closes FAQ", not await pg.is_visible("#faqSheet"))
        await pg.screenshot(path="sheet_swipe_after.png")
        # opening a sheet keeps the page where it was (no jump to the top)
        await pg.evaluate("window.scrollTo(0, 600)"); await pg.wait_for_timeout(150)
        y0 = await pg.evaluate("window.scrollY")
        ref = await pg.evaluate("document.querySelector('#home .master-settings-btn').closest('.screen').getBoundingClientRect().top")
        await pg.evaluate("document.querySelector('.faq-open-btn').click()"); await pg.wait_for_timeout(300)
        ref2 = await pg.evaluate("document.querySelector('#home .master-settings-btn').closest('.screen').getBoundingClientRect().top")
        check("page behind an open sheet does not jump", y0 > 100 and abs(ref - ref2) < 2, (y0, ref, ref2))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        check("scroll position back after closing", abs(await pg.evaluate("window.scrollY") - y0) < 2)
        # 1024 px: sheets are centred dialogs, no grab bar
        await pg.set_viewport_size({"width": 1024, "height": 768}); await pg.wait_for_timeout(200)
        await open_master()
        check("no grab bar on wide screens", not await pg.is_visible("#masterSettingsSheet .sheet-grab"))
        await ctx.close(); await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
