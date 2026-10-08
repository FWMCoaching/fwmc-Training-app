import asyncio, json, os, urllib.parse
from playwright.async_api import async_playwright

# Trainer code QR scanned with the iPhone camera app opens Safari, whose
# storage is not the home-screen app's (Fabian 08.10.2026): a #code= link in
# iOS Safari asks once ("Lieber in der App scannen"); elsewhere it runs at once.
# The trainer pre-check card and the dashboard hint say: scan in the app.
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = """try{localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-onboarding-v1','{"done":true}');}catch(e){}"""
SERVED = {"tools-an": {"type": "feature-unlock", "name": "Trainer-Werkzeuge", "features": ["trainer-tools"]}}
fails, errors = [], []

def check(name, ok, info=""):
    print(f"{name}: {ok}", info if not ok else "")
    if not ok: fails.append(name)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        async def api(route):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query)
            code = (q.get("code") or [""])[0].lower()
            if "/program" in route.request.url and code in SERVED:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(SERVED[code]))
            else:
                await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
        async def page(extra=""):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            await ctx.add_init_script(INIT + extra)
            await ctx.route("https://online-training.fwmc.workers.dev/**", api)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            return ctx, pg
        feats = "() => JSON.parse(localStorage.getItem('fwmc-features-v1') || '{}')['trainer-tools'] === true"

        # iOS Safari: asks first, Abbrechen stores nothing, "Hier in Safari öffnen" runs the code
        ctx, pg = await page("localStorage.setItem('fwmc-test-ios-browser','true');")
        await pg.goto(BASE + "#code=tools-an"); await pg.wait_for_timeout(900)
        sheet = await pg.evaluate("() => { const t = document.body.innerText; return t.includes('Lieber in der App scannen') && t.includes('Hier in Safari öffnen'); }")
        check("iOS Safari: #code= asks 'Lieber in der App scannen'", sheet)
        check("hash removed from the address", await pg.evaluate("() => !location.hash"))
        check("nothing unlocked before the answer", not await pg.evaluate(feats))
        await pg.get_by_role("button", name="Hier in Safari öffnen").click(); await pg.wait_for_timeout(900)
        check("'Hier in Safari öffnen' runs the code", await pg.evaluate(feats))
        await ctx.close()

        ctx, pg = await page("localStorage.setItem('fwmc-test-ios-browser','true');")
        await pg.goto(BASE + "#code=tools-an"); await pg.wait_for_timeout(900)
        await pg.get_by_role("button", name="Abbrechen").click(); await pg.wait_for_timeout(600)
        check("Abbrechen: nothing unlocked", not await pg.evaluate(feats))
        await ctx.close()

        # elsewhere (Android, desktop, home-screen app): runs at once
        ctx, pg = await page()
        await pg.goto(BASE + "#code=tools-an"); await pg.wait_for_timeout(900)
        check("not iOS Safari: no question", not await pg.evaluate("() => document.body.innerText.includes('Lieber in der App scannen')"))
        check("not iOS Safari: code runs at once", await pg.evaluate(feats))
        # trainer pre-check card names the camera-app pitfall
        txt = await pg.evaluate("() => document.getElementById('handoverPrecheck').textContent")
        check("pre-check card warns about the normal camera app", "normalen Kamera-App" in txt)
        await ctx.close()

        ctx, pg = await page()
        await pg.goto(f"http://localhost:{PORT}/dashboard.html"); await pg.wait_for_timeout(500)
        hint = await pg.evaluate("() => (document.getElementById('codeQrHint') || {}).textContent || ''")
        check("dashboard QR hint warns about the normal camera app", "normalen Kamera-App" in hint)
        await ctx.close()
        await b.close()
    check("no page/console errors", not errors, errors[:3])
    print("FAILS:", fails); print("ERRORS:", errors[:5])

asyncio.run(main())
