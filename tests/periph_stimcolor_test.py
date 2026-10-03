import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Three client asks for Periphere Wahrnehmung's "Farbe der Reize" picker
# that survived the "Transparenz" background-mode revert (that fourth ask
# turned out to be redundant with the pre-existing "Schwarz" colour at
# 100% intensity - a beamer physically can't project less light than
# black, and the Transparent toggle's actual on-screen result depended on
# the device's own light/dark-mode setting rather than being reliably
# black, so it added risk without a real benefit and was removed again):
# 1) "Alle Farben" select-all shortcut, generalized into
#    buildStimColorPicker itself (reaches Periph ready+pause, the
#    Zusatzaufgabe, and all 4 of MOT's colour pickers).
# 2) The picker is now also available on the pause overlay, sharing the
#    same state.periphColors backing store as the ready-screen one.
# 3) The "Blick auf die Mitte richten" caption is gone from every flash.

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

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)

        # ---- Ready screen: stimulus-colour picker gained "Alle Farben" ----
        stim_swatches = pg.locator("#periphColorPicker .color-swatch")
        print("periph colour swatch count (9 colours + Alle):", await stim_swatches.count() == 10)
        all_btn = pg.locator("#periphColorPicker .color-swatch").last
        print("'Alle Farben' label on the last swatch:", "Alle Farben" in await all_btn.inner_text())
        print("not active with only 'schwarz' selected:", "active" not in (await all_btn.get_attribute("class") or ""))
        await all_btn.click(); await pg.wait_for_timeout(80)
        print("'Alle Farben' selects every colour:", await pg.locator("#periphColorPicker .color-swatch[data-color].active").count() == 9)
        print("'Alle Farben' itself now active:", "active" in (await all_btn.get_attribute("class") or ""))
        await all_btn.click(); await pg.wait_for_timeout(80)
        print("toggling off leaves exactly 1 colour (never zero):", await pg.locator("#periphColorPicker .color-swatch[data-color].active").count() == 1)

        # ---- Run the exercise, confirm no "Blick auf die Mitte" caption ----
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.stimulusS = 3; raw.intervalMin = 0.5; raw.intervalMax = 0.5;
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#startBtn"); await pg.wait_for_timeout(4000)
        await pg.screenshot(path="screenshots/periph_no_caption.png")
        print("(see screenshot periph_no_caption.png - no 'Blick auf die Mitte' caption should be visible)")

        # ---- Pause overlay: stimulus-colour picker present, shares state ----
        print("pause button visible:", await pg.is_visible("#periphPauseBtn"))
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#periphPauseOverlay"))
        print("pause stimulus-colour picker present:", await pg.is_visible("#periphPauseColorPicker"))
        pause_stim_swatches = pg.locator("#periphPauseColorPicker .color-swatch")
        print("pause stimulus-colour picker also has 'Alle Farben' (9 + 1):", await pause_stim_swatches.count() == 10)
        print("pause picker reflects the same single colour as ready screen:",
              await pg.locator("#periphPauseColorPicker .color-swatch[data-color].active").count() == 1)

        # add 2 more colours via the pause overlay's own stimulus-colour
        # picker (the "toggling off" step above left exactly "rot" active,
        # STROOP_COLOR_LIB's first colour - pick two others on top of it)
        # and confirm the frozen frame redraws with a live background tweak
        # (the pre-existing bg picker) still working alongside it
        await pg.click('#periphPauseColorPicker .color-swatch[data-color="blau"]'); await pg.wait_for_timeout(60)
        await pg.click('#periphPauseColorPicker .color-swatch[data-color="gelb"]'); await pg.wait_for_timeout(60)
        print("ready-screen picker (hidden, still in DOM) reflects the pause picker's picks:",
              await pg.locator("#periphColorPicker .color-swatch[data-color].active").count() == 3)
        await pg.click('#periphPauseBgColorPicker .color-swatch[data-key="rot"]'); await pg.wait_for_timeout(60)
        print("pre-existing pause bg colour picker still works alongside the new stimulus one:",
              "active" in (await pg.get_attribute('#periphPauseBgColorPicker .color-swatch[data-key="rot"]', "class") or ""))

        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after Weiter:", await pg.is_hidden("#periphPauseOverlay"))

        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        print("beenden -> back at periph ready screen:", await pg.is_visible("#ready"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
