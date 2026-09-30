import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Three follow-up fixes to the Cardio "+ Zusatzimpuls" system, all
# client-requested after trying the live picker (Tier 2, see
# cardio_addon_picker_test.py):
# 1. Background colour + intensity Feineinstellungen per guest type - was
#    completely missing before (applyCardioGuestToState() never touched
#    state.bgColorKey/bgIntensity), so a guest exercise's background was
#    just whatever was left over from the last standalone use of that
#    exercise. Skipped for vt-color (bgIsStimulus: true - its background
#    IS the trained colour, a tint on top would be meaningless).
# 2. An optional time window restricting the AUTOMATIC randomized-interval
#    trigger to a client-chosen sub-range of the session ("in diesem
#    Zeitraum sollen die gesetzt werden"). The manual picker is
#    unaffected - always available, any time, by design.
# 3. Title text settled as "Zusatzaufgabe · Ziffer/Buchstabe" - it went
#    through two names in one session: first "Zusatzaufgabe · Zahlen/
#    Buchstaben" (the client asked whether this was actually Periphere
#    Wahrnehmung's Blitzreiz exercise), briefly renamed to something that
#    implied it was NOT Blitzreiz (wrong - it IS the same drawPeriphChar()
#    mechanic, just running through the "Zusatzaufgabe" add-on system
#    standalone instead of layered on a host exercise), then corrected
#    back to "Zusatzaufgabe" - the name this exact mechanism already
#    carries everywhere else in the app, which is what "one consistent
#    name, wherever it shows up" actually calls for.

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

        # ==== 1. Naming, settled ====
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        print("pool grid uses the app-wide 'Zusatzaufgabe' name:", "Zusatzaufgabe · Ziffer/Buchstabe" in await pg.inner_text("#cardioAddonPoolGrid"))

        # ==== 2. Background colour + intensity per type ====
        await pg.check('#cardioAddonPoolGrid input[data-pool="addon-flash"]'); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid input[data-pool="vt-color"]'); await pg.wait_for_timeout(150)
        panels = pg.locator(".cardio-guest-panel")
        print("2 fine-tune panels open:", await panels.count() == 2)
        flash_panel = pg.locator('.cardio-guest-panel:has(input[data-type="addon-flash"])')
        vt_panel = pg.locator('.cardio-guest-panel:has(input[data-type="vt-color"])')
        print("bg controls offered for addon-flash:", await flash_panel.locator("[data-bgcolors]").count() == 1)
        print("bg controls skipped for vt-color (bgIsStimulus):", await vt_panel.locator("[data-bgcolors]").count() == 0)

        await flash_panel.locator('input[data-bgcolor="orange"]').check(); await pg.wait_for_timeout(100)
        await flash_panel.locator('input[data-bgintensity]').fill("0.4")
        await flash_panel.locator('input[data-bgintensity]').dispatch_event("input")
        await pg.wait_for_timeout(100)
        print("bg intensity value label updated:", "40%" in await flash_panel.locator("[data-bgintensityvalue]").inner_text())

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        flash_panel = pg.locator('.cardio-guest-panel:has(input[data-type="addon-flash"])')
        print("bg colour choice persisted after reload:", await flash_panel.locator('input[data-bgcolor="orange"]').is_checked())
        print("bg intensity persisted after reload:", (await flash_panel.locator('input[data-bgintensity]').input_value()) == "0.4")

        # ==== 3. Time window ====
        print("window body hidden by default:", await pg.is_hidden("#cardioAddonWindowBody"))
        await pg.click("#cardioAddonWindowToggle"); await pg.wait_for_timeout(150)
        print("window body visible once enabled:", await pg.is_visible("#cardioAddonWindowBody"))
        print("default window shown as 0 Min. - 10 Min.:",
              (await pg.inner_text("#cardioAddonWindowStartValue")) == "0 Min." and (await pg.inner_text("#cardioAddonWindowEndValue")) == "10 Min.")

        # lower "bis" below the max first - the default already sits at the
        # 10 Min. cap (single Joggen activity), leaving no room above it to
        # demonstrate "ab" dragging past "bis" without this step
        await pg.fill("#cardioAddonWindowEndSlider", "5")
        await pg.dispatch_event("#cardioAddonWindowEndSlider", "input")
        await pg.wait_for_timeout(150)

        # dragging "ab" past "bis" pulls "bis" along with it - capped at 8
        # rather than the old arbitrary 15, since the slider's reachable
        # range is now bounded by the single 10 Min. Joggen activity in this
        # session (see cardio_addon_window_bounds_test.py for that cap itself)
        await pg.fill("#cardioAddonWindowStartSlider", "8")
        await pg.dispatch_event("#cardioAddonWindowStartSlider", "input")
        await pg.wait_for_timeout(150)
        print("end clamped up to match a later start:",
              (await pg.inner_text("#cardioAddonWindowStartValue")) == "8 Min." and (await pg.inner_text("#cardioAddonWindowEndValue")) == "8 Min.")

        # reload, confirm persistence
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        print("window toggle persisted checked:", await pg.is_checked("#cardioAddonWindowToggle"))
        print("window bounds persisted (8/8 Min.):",
              (await pg.inner_text("#cardioAddonWindowStartValue")) == "8 Min." and (await pg.inner_text("#cardioAddonWindowEndValue")) == "8 Min.")

        # ---- functional: a window that has already closed blocks the
        # automatic trigger even though the interval is due ----
        await pg.fill("#cardioAddonWindowStartSlider", "0")
        await pg.dispatch_event("#cardioAddonWindowStartSlider", "input")
        await pg.wait_for_timeout(80)
        await pg.fill("#cardioAddonWindowEndSlider", "0")
        await pg.dispatch_event("#cardioAddonWindowEndSlider", "input")
        await pg.wait_for_timeout(80)
        await pg.check('#cardioAddonPoolGrid input[data-pool="vt-color"]'); await pg.wait_for_timeout(150)
        await pg.fill("#cardioAddonIntervalMinSlider", "20")
        await pg.dispatch_event("#cardioAddonIntervalMinSlider", "input")
        await pg.fill("#cardioAddonIntervalMaxSlider", "20")
        await pg.dispatch_event("#cardioAddonIntervalMaxSlider", "input")
        await pg.wait_for_timeout(150)

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.wait_for_timeout(24000)
        print("interval due (20s) but 0-0 Min. window already closed -> no automatic guest:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)

        # ---- functional: a window covering the due interval lets it
        # trigger normally (still on cardioReady, Feineinstellungen panel
        # already open from before the abort above - no need to reopen it) ----
        await pg.fill("#cardioAddonWindowEndSlider", "1")
        await pg.dispatch_event("#cardioAddonWindowEndSlider", "input")
        await pg.wait_for_timeout(150)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.wait_for_timeout(24000)
        print("interval due (20s) inside the 0-1 Min. window -> automatic guest fires:",
              await pg.is_visible("#player") and not await pg.is_visible("#cardioPlayer"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
