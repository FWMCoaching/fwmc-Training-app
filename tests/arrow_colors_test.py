import asyncio
import sys
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"
OUT = "screenshots/"

FAILS = []
def check(label, ok, detail=""):
    # 08.10.: turned the bare prints into checks - the suite log grep flagged
    # expected-False prints ("'Alle' active with only 3 selected: False") as
    # failures, and the "still 1 selected" label no longer matched the app.
    print(f"{label}: {bool(ok)}", detail)
    if not ok: FAILS.append(label)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 900}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # Open "8 Pfeile" (8-solo) - should now show the color group
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(200)
        check("colorGroup visible for 8-solo", await pg.is_visible("#colorGroup"))
        swatch_count = await pg.locator("#colorPicker .color-swatch").count()
        check("swatch count is 7 colors + Alle", swatch_count == 8, swatch_count)
        hint = await pg.inner_text("#colorHint")
        check("hint says 1 bis 7", "1 bis 7" in hint, hint)
        check("initially 1 gewählt", await pg.inner_text("#colorCount") == "1 gewählt")

        # single color should be deselectable-blocked (min 1): try deselecting the only selected one
        active_swatch = pg.locator("#colorPicker .color-swatch.active[data-color]")
        check("initially exactly 1 active", await active_swatch.count() == 1)
        await active_swatch.first.click(); await pg.wait_for_timeout(150)
        # The arrow/Stroop picker allows an empty selection on purpose (syncColorUI:
        # belowMin -> warning hint + disabled Start/Speichern), unlike the stimulus
        # colour picker which keeps at least one. The old label "still 1 selected"
        # printed "0 gewählt" for years; the check now states the real contract.
        hint = await pg.inner_text("#colorHint")
        check("deselecting the last colour warns", hint == "Wähle mindestens eine Farbe.", hint)
        check("0 gewählt then", await pg.inner_text("#colorCount") == "0 gewählt")
        check("start disabled with 0 colours", await pg.is_disabled("#startBtn"))

        # select a second and third color
        swatches = pg.locator("#colorPicker .color-swatch[data-color]")
        await swatches.nth(1).click(); await pg.wait_for_timeout(80)
        await swatches.nth(2).click(); await pg.wait_for_timeout(80)
        check("2 gewählt after selecting 2", await pg.inner_text("#colorCount") == "2 gewählt")
        check("start enabled again", not await pg.is_disabled("#startBtn"))
        check("'Alle' NOT active with only 2 selected", "active" not in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))

        # click "Alle Farben"
        await pg.click("#colorPicker .color-swatch:not([data-color])"); await pg.wait_for_timeout(150)
        check("7 gewählt after clicking Alle", await pg.inner_text("#colorCount") == "7 gewählt")
        check("'Alle' now active", "active" in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))
        await pg.screenshot(path=OUT + "arrow_colors_all.png")

        # deselect one color -> "Alle" should un-mark itself
        await swatches.nth(0).click(); await pg.wait_for_timeout(150)
        check("6 gewählt after deselecting one from all-7", await pg.inner_text("#colorCount") == "6 gewählt")
        check("'Alle' NOT active any more", "active" not in (await pg.get_attribute("#colorPicker .color-swatch:not([data-color])", "class") or ""))

        # Verify VT (vt-color) still has its own 2-4 range, unaffected
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        hint = await pg.inner_text("#colorHint")
        check("VT hint says 2 bis 4", "2 bis 4" in hint, hint)
        check("VT shows 7 colour swatches", await pg.locator("#colorPicker .color-swatch[data-color]:visible").count() == 7)
        check("Alle button hidden for VT", await pg.is_hidden("#colorPicker .color-swatch:not([data-color])"))

        # Actually run 8-solo briefly to confirm no crash and arrow colors get used
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(600)
        check("player visible after starting 8-solo", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)
    if errors: FAILS.append("errors")
    print("ALL OK" if not FAILS else "FAILED: " + str(FAILS))
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
