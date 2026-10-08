"""Haken & Kreuz (Fabian 07.10.2026): off by default, switchable in the pause
sheet, and a one-time question at the start when the background makes
green/red weak. Run from tests/ with a dev server on :8845."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-natmodes','1');"
        "localStorage.setItem('fwmc-test-fbhint','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(400)
        check("off by default", not await pg.evaluate("() => document.body.classList.contains('fbs-remember')"))

        # weak background: dark blue at full intensity
        await pg.evaluate("() => { const p = JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1') || '{}'); p.bgColorKey = 'blau'; p.bgIntensity = 1; localStorage.setItem('fwmc-remember-prefs-v1', JSON.stringify(p)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('.nat-tile[data-nat-ex="remember"]') if await pg.locator('.nat-tile[data-nat-ex="remember"]').count() else await pg.evaluate("() => document.getElementById('rememberOpenFixed').click()")
        await pg.wait_for_timeout(300)
        await pg.evaluate("() => document.getElementById('rememberReadyStartBtn').click()"); await pg.wait_for_timeout(300)
        sheet = await pg.is_visible("#confirmSheet")
        check("weak contrast: question at start", sheet and "Kontrast" in await pg.inner_text("#confirmTitle"), await pg.inner_text("#confirmSheet") if sheet else "")
        if sheet:
            await pg.screenshot(path="screenshots/fb_hint_sheet.png")
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(400)
            check("yes: tick on + run starts", await pg.evaluate("() => document.body.classList.contains('fbs-remember')") and await pg.is_visible("#rememberPlayer"))
        # pause toggle
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(200)
        off = '#rememberPauseOverlay [data-cvd-ex="remember"][data-cvd-val="0"]'
        check("pause sheet has Haken & Kreuz", await pg.is_visible(off))
        await pg.click(off); await pg.wait_for_timeout(100)
        check("pause: switched off", not await pg.evaluate("() => document.body.classList.contains('fbs-remember')"))
        await pg.screenshot(path="screenshots/fb_pause_toggle.png")
        await pg.click("#rememberResumeBtn"); await pg.wait_for_timeout(100)
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)

        # same combination again: no second question
        await pg.evaluate("() => document.getElementById('rememberReadyStartBtn').click()"); await pg.wait_for_timeout(300)
        check("asked only once per combination", not await pg.is_visible("#confirmSheet"))
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
