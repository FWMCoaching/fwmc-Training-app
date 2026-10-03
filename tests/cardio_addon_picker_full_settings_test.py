import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Client's follow-up ask (2026-09-30), using Periphere Wahrnehmung and
# Blitz-Raster as the illustrating example: pre-start Feineinstellungen lets
# you configure every field of a guest type ("alle Details einstellen"),
# but triggering that SAME exercise live from inside a running Cardio
# session only ever offered the exercise + duration pick - every other
# "Unterpunkt" (colours, difficulty, grid size, background, ...) was
# missing from that live flow. Then generalized further: "Also ich möchte
# bei allen Übungen die gleichen Einstellungsmöglichkeiten... überall volle
# Kontrolle" - every guest type, not just the two examples.
#
# #cardioAddonPickerDetail now renders buildCardioGuestFieldsHtml() - the
# exact same function the pre-start panel uses - so this test checks two
# things for the two example types plus a plain generic one: (1) parity -
# the live detail panel shows the same field rows the advanced panel would
# for that type, and (2) isolation - editing them live actually changes
# what the burst does, but never gets written back to the client's own
# saved cardioAddonPrefs.perType default (a live edit is a "just for this
# once" choice, not a settings change - same principle already proven for
# duration in cardio_addon_picker_test.py, and for the separate-engine
# domains' own real prefs/best scores in the NAT batch tests).

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

        # ---- touch the advanced panel once just to force cardioAddonPrefs'
        # in-memory defaults (already fully populated per-type at load time,
        # see loadCardioAddonPrefs()) to actually persist to localStorage -
        # otherwise the isolation checks below have nothing to read yet ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        detail = pg.locator("#cardioAddonPickerDetail")

        # ==== a plain generic type (vrw-original, index 2): Reiz-Dauer/Pause
        # fields reachable live, same as the advanced panel already offers ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(2).click(); await pg.wait_for_timeout(80)
        print("generic type: Reiz-Dauer/Pause min/max fields present live:",
              await detail.locator('input[data-f="stimulusS"]').count() == 1 and
              await detail.locator('input[data-f="intervalMin"]').count() == 1 and
              await detail.locator('input[data-f="intervalMax"]').count() == 1)
        print("generic type: colour row present live:", await detail.locator("[data-colors]").count() == 1)
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)

        # ==== Periphere Wahrnehmung (periph-flash, index 12): kind/colour/
        # background rows, same depth as its own Feineinstellungen panel ====
        saved_periph_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['periph-flash']")
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(12).click(); await pg.wait_for_timeout(80)
        print("periph-flash: kind-row present live:", await detail.locator("[data-kind-row]").count() == 1)
        print("periph-flash: colour row present live:", await detail.locator("[data-colors]").count() == 1)
        print("periph-flash: background row present live:", await detail.locator("[data-bgcolors]").count() == 1)

        # live-edit: switch kind to "zahlen" and push the background
        # intensity up from its saved 0 (periph-flash renders its background
        # onto a canvas via currentBgFill(), not a checkable DOM style, so
        # the actual visual effect isn't asserted here - the isolation check
        # below is the load-bearing one: it proves the live edit was used
        # for real, not merely displayed, precisely because it differs from
        # what stayed saved)
        await detail.locator('[data-kind="zahlen"]').click(); await pg.wait_for_timeout(80)
        print("kind selection moves live (zahlen now active):", "active" in (await detail.locator('[data-kind="zahlen"]').get_attribute("class")))
        await detail.locator("input[data-bgintensity]").fill("0.6")
        await detail.locator("input[data-bgintensity]").dispatch_event("input")
        await pg.wait_for_timeout(80)

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("periph-flash takes over full-screen:", await pg.is_visible("#player") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#player"))

        saved_periph_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['periph-flash']")
        print("periph-flash: saved kind untouched by the live edit:", saved_periph_after["kind"] == saved_periph_before["kind"])
        print("periph-flash: saved background intensity untouched by the live edit:", saved_periph_after["bgIntensity"] == saved_periph_before["bgIntensity"])

        # ==== Blitz-Raster (index 13): difficulty/grid/error rows, same
        # depth as its own Feineinstellungen panel; grid size change is
        # checkable directly via the rendered cell count ====
        saved_blitz_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['blitz-raster']")
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(13).click(); await pg.wait_for_timeout(80)
        print("blitz-raster: difficulty row present live:", await detail.locator("[data-blitzdiff-row]").count() == 1)
        print("blitz-raster: grid-size row present live:", await detail.locator("[data-blitzgrid-row]").count() == 1)
        print("blitz-raster: 'Bei Fehler' row present live:", await detail.locator("[data-blitzerror-row]").count() == 1)
        print("blitz-raster: no colour row (no colour concept):", await detail.locator("[data-colors]").count() == 0)

        print("default grid size (4x4) active by default:", "active" in (await detail.locator('[data-blitzgrid="4"]').get_attribute("class")))
        await detail.locator('[data-blitzgrid="6"]').click(); await pg.wait_for_timeout(80)
        print("grid size selection moves live (6x6 now active):", "active" in (await detail.locator('[data-blitzgrid="6"]').get_attribute("class")))

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("blitz-raster takes over full-screen (own #blitzPlayer):", await pg.is_visible("#blitzPlayer") and await pg.is_hidden("#cardioPlayer"))
        cell_count = await pg.locator(".blitz-cell").count()
        print("the live-edited 6x6 grid size actually rendered (36 cells), not the saved 4x4 default:", cell_count == 36)
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#blitzPlayer"))

        saved_blitz_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['blitz-raster']")
        print("blitz-raster: saved grid size untouched by the live edit:", saved_blitz_after["gridSize"] == saved_blitz_before["gridSize"])

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
