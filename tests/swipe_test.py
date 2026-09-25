import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

async def swipe(pg, selector, dx, dy=0, start_x=300, start_y=400):
    await pg.eval_on_selector(selector, """(el, {dx, dy, startX, startY}) => {
        const mk = (x, y) => new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
        el.dispatchEvent(new TouchEvent('touchstart', { touches: [mk(startX, startY)], bubbles: true, cancelable: true }));
        const endX = startX + dx, endY = startY + dy;
        el.dispatchEvent(new TouchEvent('touchend', { changedTouches: [mk(endX, endY)], bubbles: true, cancelable: true }));
    }""", {"dx": dx, "dy": dy, "startX": start_x, "startY": start_y})

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", has_touch=True)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click("#filterMoreBtn"); await pg.wait_for_timeout(100)
        await pg.click('[data-filter-value="huetchen"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-exercise="cone-compass"]'); await pg.wait_for_timeout(150)
        await pg.click("#setupBtn"); await pg.wait_for_timeout(150)

        print("start counter:", await pg.inner_text("#setupCounter"))
        await swipe(pg, "#setupModal", -120)  # swipe left -> next
        await pg.wait_for_timeout(150)
        print("after swipe-left counter (expect 2/3):", await pg.inner_text("#setupCounter"))

        await swipe(pg, "#setupModal", -120)
        await pg.wait_for_timeout(150)
        print("after 2nd swipe-left (expect 3/3):", await pg.inner_text("#setupCounter"))

        await swipe(pg, "#setupModal", -120)  # already at last, should stay (button disabled)
        await pg.wait_for_timeout(150)
        print("swipe-left past end (should stay 3/3):", await pg.inner_text("#setupCounter"))

        await swipe(pg, "#setupModal", 120)  # swipe right -> prev
        await pg.wait_for_timeout(150)
        print("after swipe-right (expect 2/3):", await pg.inner_text("#setupCounter"))

        # a small, mostly-vertical drag should NOT trigger navigation (avoid conflict w/ scrolling / taps)
        await swipe(pg, "#setupModal", 10, dy=80)
        await pg.wait_for_timeout(150)
        print("after vertical drag (should stay 2/3):", await pg.inner_text("#setupCounter"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
