import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# FAQ section on the main home screen, below "Einzelne Übungen" and above
# the site footer - plain native <details>/<summary> accordion items (no
# custom JS), styled with the app's theme tokens like .advanced (general
# app UI read in normal light/dark browsing, unlike the fixed-hex player/
# stage rules used during a running exercise).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        print("FAQ section visible:", await pg.is_visible("#faqSection"))
        items = pg.locator("#faqSection .faq-item")
        count = await items.count()
        print("has several FAQ items:", count >= 6)

        first = items.first
        print("first item closed initially:", (await first.get_attribute("open")) is None)
        await first.locator("summary").click(); await pg.wait_for_timeout(100)
        print("first item open after click:", (await first.get_attribute("open")) is not None)
        body_text = await first.locator(".faq-body").inner_text()
        print("opened item shows real body text:", len(body_text) > 20)

        # each item toggles independently
        second = items.nth(1)
        print("second item still closed (independent toggle):", (await second.get_attribute("open")) is None)
        await first.locator("summary").click(); await pg.wait_for_timeout(100)
        print("first item closes again on second click:", (await first.get_attribute("open")) is None)

        # a link inside an FAQ body is a real, absolute, new-tab link (not a stray in-app handler)
        await second.locator("summary").click(); await pg.wait_for_timeout(100)
        link = second.locator(".faq-body a")
        if await link.count() > 0:
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            print("FAQ link is absolute https and opens in a new tab:", bool(href and href.startswith("https://")) and target == "_blank")

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
