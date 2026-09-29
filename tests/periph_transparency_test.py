import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Four client asks for Periphere Wahrnehmung ("Blitzreize"), all bundled
# together since they touch the same ready/pause screens:
# 1) Transparent background mode (for a beamer/projector - no colored
#    rectangle on the wall), settable both on the ready screen and while
#    paused mid-session.
# 2) "Farbe der Reize" (stimulus colour) picker, previously ready-screen
#    only, now also available on the pause overlay.
# 3) "Alle Farben" select-all shortcut on that stimulus-colour picker
#    (mirrors the existing arrow/Stroop colour picker's own "Alle Farben").
# 4) The "Blick auf die Mitte richten" on-screen caption removed entirely
#    (distracting per the client, every flash used to show it).

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

        # ---- Ready screen: background "Transparent" mode ----
        print("bg mode row visible:", await pg.is_visible("#bgModeRow"))
        print("colour options visible by default (Farbe mode):", await pg.is_visible("#bgColorOptions"))
        print("transparent hint hidden by default:", await pg.is_hidden("#bgTransparentHint"))
        await pg.click('#bgModeRow [data-bg-mode="transparent"]'); await pg.wait_for_timeout(80)
        print("colour options hidden once Transparent is chosen:", await pg.is_hidden("#bgColorOptions"))
        print("transparent hint shown:", await pg.is_visible("#bgTransparentHint"))
        print("Transparent button marked active:", "active" in (await pg.get_attribute('#bgModeRow [data-bg-mode="transparent"]', "class") or ""))

        # reload to confirm the transparent choice persists
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click("#periphOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(100)
        print("transparent mode persisted after reload:", await pg.is_hidden("#bgColorOptions"))

        # ---- Run the exercise: canvas cleared (no fillRect) instead of
        # painted white/coloured, and .player itself has no opaque
        # background either (both needed for a beamer to show nothing) ----
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
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        print("player has the bg-transparent class while running:", "bg-transparent" in (await pg.get_attribute("#player", "class") or ""))
        canvas_alpha_zero = await pg.evaluate("""() => {
            const c = document.getElementById('stage');
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(2, 2, 1, 1).data; // corner pixel, never overdrawn by the stimulus itself
            return d[3] === 0;
        }""")
        print("canvas corner pixel is fully transparent (cleared, not filled):", canvas_alpha_zero)

        # ---- "Blick auf die Mitte richten" caption is gone ----
        await pg.wait_for_timeout(4000)  # let at least one stimulus flash
        canvas_text = await pg.evaluate("document.getElementById('stage').getAttribute('aria-label') || ''")  # canvas has no text nodes to check directly; screenshot instead
        await pg.screenshot(path="screenshots/periph_transparent_running.png")
        print("(see screenshot periph_transparent_running.png - no caption bar should be visible)")

        # ---- Pause overlay: bg mode toggle, stimulus-colour picker present ----
        print("pause button visible:", await pg.is_visible("#periphPauseBtn"))
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#periphPauseOverlay"))
        print("pause bg mode row shows Transparent active (matches ready screen state):",
              "active" in (await pg.get_attribute('#periphPauseBgModeRow [data-bg-mode="transparent"]', "class") or ""))
        print("pause bg colour options hidden (still in Transparent mode):", await pg.is_hidden("#periphPauseBgColorOptions"))
        print("pause stimulus-colour picker present:", await pg.is_visible("#periphPauseColorPicker"))
        pause_stim_swatches = pg.locator("#periphPauseColorPicker .color-swatch")
        print("pause stimulus-colour picker also has 'Alle Farben' (9 + 1):", await pause_stim_swatches.count() == 10)
        print("pause picker reflects the same single colour as ready screen:",
              await pg.locator("#periphPauseColorPicker .color-swatch[data-color].active").count() == 1)

        # switch back to Farbe mode from the pause overlay itself
        await pg.click('#periphPauseBgModeRow [data-bg-mode="color"]'); await pg.wait_for_timeout(150)
        print("pause: switching back to Farbe shows the colour picker again:", await pg.is_visible("#periphPauseBgColorOptions"))
        print("player's bg-transparent class removed after switching back to Farbe:",
              "bg-transparent" not in (await pg.get_attribute("#player", "class") or ""))
        canvas_alpha_zero_after = await pg.evaluate("""() => {
            const c = document.getElementById('stage');
            const ctx = c.getContext('2d');
            const d = ctx.getImageData(2, 2, 1, 1).data;
            return d[3] === 0;
        }""")
        print("canvas corner pixel painted again (not transparent) after switching back:", not canvas_alpha_zero_after)

        # add 2 more colours via the pause overlay's own stimulus-colour
        # picker (the "toggling off" step above left exactly "rot" active,
        # STROOP_COLOR_LIB's first colour - pick two others on top of it)
        await pg.click('#periphPauseColorPicker .color-swatch[data-color="blau"]'); await pg.wait_for_timeout(60)
        await pg.click('#periphPauseColorPicker .color-swatch[data-color="gelb"]'); await pg.wait_for_timeout(60)
        print("ready-screen picker (hidden, still in DOM) reflects the pause picker's picks:",
              await pg.locator("#periphColorPicker .color-swatch[data-color].active").count() == 3)

        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after Weiter:", await pg.is_hidden("#periphPauseOverlay"))

        await pg.click("#backBtn"); await pg.wait_for_timeout(150)
        print("beenden -> back at periph ready screen:", await pg.is_visible("#ready"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
