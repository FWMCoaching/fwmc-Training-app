import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# FAQ: one shared overlay (#faqSheet), opened from a "Häufige Fragen" link
# in EVERY section's site-footer (".faq-open-btn", six instances - home,
# breath, movement, workout, nat, test) so it's reachable from anywhere in
# the app, not just the main home screen. Reuses the exact .sheet/
# .sheet-inner + focus-trap/backdrop-click/Escape pattern already used by
# #tipsSheet - no custom modal logic of its own.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        print("faq-open-btn count across the app (one per footer):", await pg.locator(".faq-open-btn").count())
        print("faqSheet hidden initially:", await pg.is_hidden("#faqSheet"))

        # open from the home screen's footer
        await pg.locator("#home .faq-open-btn").click(); await pg.wait_for_timeout(150)
        print("faqSheet visible after opening from home:", await pg.is_visible("#faqSheet"))
        items = pg.locator("#faqSheet .faq-item")
        print("has several FAQ items:", await items.count() >= 6)
        first = items.first
        await first.locator("summary").click(); await pg.wait_for_timeout(100)
        print("first item opens:", (await first.get_attribute("open")) is not None)
        body_text = await first.locator(".faq-body").inner_text()
        print("opened item shows real body text:", len(body_text) > 20)

        # Escape closes it
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
        print("Escape closes the sheet:", await pg.is_hidden("#faqSheet"))

        # switch to a different section (Test) and confirm the same FAQ opens from there too
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.locator("#testHome .faq-open-btn").click(); await pg.wait_for_timeout(150)
        print("faqSheet also opens from the Test section's footer:", await pg.is_visible("#faqSheet"))
        await pg.click("#faqCloseBtn"); await pg.wait_for_timeout(150)
        print("Schließen-Button closes it, back on testHome:", await pg.is_hidden("#faqSheet") and await pg.is_visible("#testHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
