"""Kein nackter Knopf (Fabian 07.10.2026: "Jetzt weiter" im Kraftplan wirkte
klein und wie ein Fremdkörper). Every text button inside a player, pause
sheet or done panel must carry real styling: no browser-default padding
(≈1 px), at least 36 px high when shown. Run from tests/ with a dev server."""
import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
# chips with a fixed height instead of padding
ALLOW = {"balanceClockBtn", "balanceFinishBtn", "balanceKnobBtn", "balanceMetroBtn", "liveEndBtn", "programVideoNextBtn"}


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
        pg.on("pageerror", lambda e: errors.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(500)
        bare = await pg.evaluate("""(allow) => { const out = [];
          document.querySelectorAll('.player button, .pause-overlay button, .done-panel button').forEach(bt => {
            if (allow.includes(bt.id) || bt.textContent.trim().length < 3 || bt.classList.contains('color-swatch')) return;
            const cs = getComputedStyle(bt);
            if (parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom) <= 4 && !(parseFloat(cs.minHeight) >= 36) && !(parseFloat(cs.height) >= 36))
              out.push((bt.id || bt.className) + ' "' + bt.textContent.trim().slice(0, 24) + '"'); });
          return out; }""", list(ALLOW))
        ok = not bare and not errors
        print("no bare buttons:", not bare, "; ".join(bare[:8]))
        print("no pageerror:", not errors)
        await b.close()
    print("ALL PASS" if ok else "SOME FAILED")

asyncio.run(main())
