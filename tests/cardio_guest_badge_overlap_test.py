import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Client-reported, with screenshots: the floating "Cardio: noch M:SS" badge
# (fixed top-right, see .cardio-guest-badge) sat at a hardcoded top offset
# that assumed every guest player's own top-right "Vollbild" (fullscreen)
# button lived further down than it - true for most, but several guest
# players' own .player-bar actually occupies exactly that spot, so the
# badge visibly covered "Vollbild" (its text peeking out from underneath).
# cardioGuestBadgeTop() now measures whichever .player-bar is actually
# rendered (0-height for every hidden one) and sits just below its real
# bottom edge instead of guessing - this re-checks that across every
# domain a guest burst can take over.

async def check(pg, type_index, fs_selector, back_selector, label):
    await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
    await pg.locator("#cardioAddonPickerTypeRow .choice").nth(type_index).click(); await pg.wait_for_timeout(80)
    await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
    badge = await pg.eval_on_selector("#cardioGuestBadge", "el => el.getBoundingClientRect()")
    fs = await pg.eval_on_selector(fs_selector, "el => el.getBoundingClientRect()")
    overlap = not (badge["right"] < fs["left"] or badge["left"] > fs["right"] or badge["bottom"] < fs["top"] or badge["top"] > fs["bottom"])
    print(f"{label}: badge clears Vollbild (no overlap):", not overlap)
    await pg.click(back_selector); await pg.wait_for_timeout(300)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        # index 6 = 4-diag (generic runSession player, the client's own
        # screenshot - an arrow exercise), 11 = cone-tap (the client's other
        # screenshot - a plain grey dot), 13-16 = the four separate-engine
        # domains, each with their own .player-bar/Vollbild.
        await check(pg, 6, "#fsBtn", "#backBtn", "4-diag (generic player)")
        await check(pg, 11, "#fsBtn", "#backBtn", "cone-tap")
        await check(pg, 15, "#blitzFsBtn", "#blitzBackBtn", "blitz-raster")
        await check(pg, 16, "#rememberFsBtn", "#rememberBackBtn", "remember")
        await check(pg, 17, "#flashFsBtn", "#flashBackBtn", "flash")
        await check(pg, 18, "#motFsBtn", "#motBackBtn", "mot")

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
