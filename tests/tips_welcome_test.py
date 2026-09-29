import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Task #21: a welcome/onboarding text inside the existing "So trainierst
# du richtig" sheet (tipsSheet) - dismissible but always recallable, per
# the client's own framing. The sheet itself already had this exact shape
# (auto-opens once on a genuinely first visit via TIPS_KEY/
# fwmc-tips-seen, reachable anytime after via the #tipsBtn link) - only
# the CONTENT was missing: how to start, that Master-Einstellungen (the
# gear icon) apply everywhere, that a Kombi-Baukasten exists, and a
# recommendation to book time with your coach if unsure.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await (await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")).new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- genuinely first visit: no fwmc-tips-seen key yet ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        print("tips sheet auto-opens on first visit:", await pg.is_visible("#tipsSheet"))
        print("welcome paragraph visible:", await pg.is_visible("#tipsWelcome"))
        welcome_text = await pg.inner_text("#tipsWelcome")
        print("welcome mentions starting without an account:", "Account" in welcome_text)
        print("welcome mentions the gear/Einstellungen:", "Einstellungen" in welcome_text)
        print("welcome mentions Kombi-Baukasten:", "Kombi-Baukasten" in welcome_text)
        print("coach hint visible:", await pg.is_visible("#tipsCoachHint"))
        coach_text = await pg.inner_text("#tipsCoachHint")
        print("coach hint mentions Coach:", "Coach" in coach_text)
        print("coach hint has a contact link:", await pg.locator('#tipsCoachHint a[href="https://www.fabian-westermann.de/"]').count() == 1)
        # existing practical tips list still intact, unchanged
        print("existing practical tips list still has 4 items:", await pg.locator("#tipsSheet .tips li").count() == 4)

        # ---- dismiss: marks fwmc-tips-seen, sheet closes ----
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        print("sheet closed after dismiss:", await pg.is_hidden("#tipsSheet"))
        seen = await pg.evaluate("() => localStorage.getItem('fwmc-tips-seen')")
        print("fwmc-tips-seen persisted:", seen == "true")

        # ---- reload: does NOT auto-open again (seen once) ----
        await pg.reload(); await pg.wait_for_timeout(400)
        print("does not auto-open again after being seen once:", await pg.is_hidden("#tipsSheet"))

        # ---- but stays recallable any time via the same link, with the
        # SAME welcome content still there ----
        await pg.click("#tipsBtn"); await pg.wait_for_timeout(150)
        print("recallable via tipsBtn:", await pg.is_visible("#tipsSheet"))
        print("welcome text still there when recalled:", await pg.is_visible("#tipsWelcome"))
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
