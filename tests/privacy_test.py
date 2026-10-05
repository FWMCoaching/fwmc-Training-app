import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Datenschutz in der App (Fabian, 2026-10-03): a sheet reachable from every
# footer and from the FAQ storage answer, plain words about what is stored
# where (device id for codes, IP only for rate limiting).


async def main():
    errors, fails = [], []
    def check(label, ok):
        print(label + ":", ok)
        if not ok: fails.append(label)

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for scheme in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme=scheme)
            await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
            await pg.goto(URL); await pg.wait_for_timeout(400)
            if scheme == "light":
                check("11 footer buttons", await pg.locator(".site-footer .privacy-open-btn").count() == 11)
                check("no footer link to an external Datenschutz page", await pg.locator('.site-footer a', has_text="Datenschutz").count() == 0)
            check("sheet hidden at start", await pg.is_hidden("#privacySheet"))
            await pg.locator("#home .site-footer .privacy-open-btn").click(); await pg.wait_for_timeout(200)
            check(scheme + ": opens from footer", await pg.is_visible("#privacySheet"))
            txt = await pg.evaluate("document.getElementById('privacySheet').textContent")
            check("mentions device id", "Geräte-Kennung" in txt)
            check("mentions IP address", "IP-Adresse" in txt)
            check("links website privacy policy", await pg.locator('#privacySheet a[href*="fabian-westermann.de"]').count() >= 1)
            check("never names Fabian", "Fabian" not in txt)
            await pg.screenshot(path=f"privacy_{scheme}.png")
            await pg.click("#privacyCloseBtn"); await pg.wait_for_timeout(150)
            check("close button closes", await pg.is_hidden("#privacySheet"))

            # From the FAQ: privacy stacks above the FAQ, Escape closes only privacy.
            await pg.locator("#home .site-footer .faq-open-btn").click(); await pg.wait_for_timeout(200)
            await pg.locator("#faqSheet summary", has_text="gespeichert").first.click(); await pg.wait_for_timeout(150)
            await pg.locator("#faqSheet .privacy-open-btn").click(); await pg.wait_for_timeout(200)
            check("opens from FAQ", await pg.is_visible("#privacySheet"))
            top = await pg.evaluate("""() => { const r = document.querySelector('#privacySheet .sheet-inner').getBoundingClientRect();
                const el = document.elementFromPoint(r.left + r.width/2, r.top + 30); return !!el.closest('#privacySheet'); }""")
            check("privacy sheet above FAQ", top)
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
            check("Escape closes privacy only", await pg.is_hidden("#privacySheet") and await pg.is_visible("#faqSheet"))
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
            check("second Escape closes FAQ", await pg.is_hidden("#faqSheet"))
            # Backdrop click closes.
            await pg.locator("#home .site-footer .privacy-open-btn").click(); await pg.wait_for_timeout(200)
            await pg.mouse.click(5, 5); await pg.wait_for_timeout(150)
            check("backdrop closes", await pg.is_hidden("#privacySheet"))
            await ctx.close()

        check("no page errors", not errors)
        if errors: print(errors)
        await b.close()
    if fails: print("FAILED:", fails)

asyncio.run(main())
