import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Two fixes: (1) the shared VT-canvas fixation point (Periphere Wahrnehmung
# and every other VT exercise via drawFixationPoint()) could be recoloured/
# resized but never fully switched off - now has the same "Anzeigen"/
# "Ausblenden" toggle Flash Speicher Test already had (state.periphFixEnabled,
# one shared setting, so switching it off applies "übergreifend" to every
# exercise that shows the dot). (2) Flash Speicher Test's own fixpoint sat
# absolutely centred on the whole stage, which - once the answer panel
# (boxes + keypad) filled that space - landed right on top of a keypad key;
# it must now always be hidden while that panel is open, regardless of the
# Anzeigen/Ausblenden setting.

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

        # --- Periph/VT-canvas fixpoint: on by default, fully removable ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("fixpoint toggle defaults to Anzeigen:", "active" in (await pg.get_attribute('#periphFixToggleRow [data-periph-fix="1"]', "class") or ""))
        print("fixpoint options visible by default:", await pg.is_visible("#periphFixOptions"))

        await pg.click('#periphFixToggleRow [data-periph-fix="0"]'); await pg.wait_for_timeout(80)
        print("options collapse when disabled:", await pg.is_hidden("#periphFixOptions"))
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')||'{}').periphFixEnabled")
        print("disabled state persisted:", prefs is False)

        await pg.click("#startBtn"); await pg.wait_for_timeout(600)
        canvas_has_dot = await pg.evaluate("""() => {
            const c = document.getElementById('stage');
            const ctx = c.getContext('2d');
            const cx = Math.round(c.width/2), cy = Math.round(c.height/2);
            const d = ctx.getImageData(cx, cy, 1, 1).data;
            // The centre pixel should just be background (near-white/neutral),
            // not the grey dot (#8fa2a8 = 143,162,168) or any fixpoint colour.
            return `${d[0]},${d[1]},${d[2]}`;
        }""")
        print("centre pixel isn't the fixpoint dot's grey once disabled:", canvas_has_dot != "143,162,168")
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        # --- re-enable, applies to a DIFFERENT VT exercise too (shared setting) ---
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)
        await pg.click('.section-tab[data-section="visual"]:visible'); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(150)
        if not await pg.is_visible("#periphFixOptions") and not await pg.is_visible('#periphFixToggleRow [data-periph-fix="1"]'):
            await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("a different VT exercise shows the same disabled state (shared, not per-exercise):",
              "active" in (await pg.get_attribute('#periphFixToggleRow [data-periph-fix="0"]', "class") or ""))
        await pg.click('#periphFixToggleRow [data-periph-fix="1"]'); await pg.wait_for_timeout(80)
        print("re-enabled:", "active" in (await pg.get_attribute('#periphFixToggleRow [data-periph-fix="1"]', "class") or ""))
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)

        # --- Flash Speicher Test: fixpoint always hidden once the answer panel opens ---
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)
        await pg.click("#flashAdvanced summary"); await pg.wait_for_timeout(100)
        print("Flash fixpoint Anzeigen active by default:", "active" in (await pg.get_attribute('#flashFixToggleRow [data-flash-fix="1"]', "class") or ""))
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fixpoint visible while a number flashes:", await pg.is_hidden("#flashFixpointEl") == False)
        for _ in range(150):
            if await pg.is_visible("#flashInputPanel"):
                break
            await pg.wait_for_timeout(40)
        print("fixpoint hidden once the answer panel (boxes+keypad) is open:", await pg.is_hidden("#flashFixpointEl"))
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
