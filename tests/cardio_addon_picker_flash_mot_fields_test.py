import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Batch C of the "genau so als wenn man die Übung einzeln machen würde"
# follow-up: Flash-Speicher-Test's and Objektverfolgung (MOT)'s own remaining
# settings beyond kind/colour/difficulty/error-mode.
#
# Flash gets the exact same "Bereich" (axes/zones) mechanism as Periphere
# Wahrnehmung (Batch A) - same PERIPH_AXIS_KEYS/PERIPH_ZONE_KEYS, same
# generic data-axis/data-zone wiring, no dominance-weighting (flashPrefs
# never had that) - plus its own Fixpunkt (fixation point) controls and raw
# Einblenddauer/Pause sliders, both nested under its own "Feineinstellungen"
# same as its standalone Ready screen (#flashAdvanced).
#
# MOT gets "Darstellung" (flach/3D-Optik) and a second, independent colour
# picker "Farbe des Ziels" (targetColors, separate from the objects' own
# colour), plus raw Geschwindigkeit/Verfolgungsdauer/Markierdauer sliders
# under its own Feineinstellungen (#motAdvanced).
#
# Both batches also fixed real isolation leaks turned up while wiring this:
# startFlashGame() read axes/zones/useZones and renderFlashFixpoint() read
# fix* straight from the client's own real flashPrefs even under a
# prefsOverride; startMotGame() did the same for style/targetColors - all
# silently using the client's real saved values instead of the (until now
# nonexistent) Cardio panel's, the same class of bug Batch B's Blitz-zones
# fix turned up.

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

        # ---- pre-start Feineinstellungen panel shows all the new rows ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid input[data-pool="flash"]'); await pg.wait_for_timeout(100)
        await pg.check('#cardioAddonPoolGrid input[data-pool="mot"]'); await pg.wait_for_timeout(150)
        flash_panel = pg.locator('.cardio-guest-panel:has(input[data-type="flash"])')
        mot_panel = pg.locator('.cardio-guest-panel:has(input[data-type="mot"])')
        print("flash: axis-row present pre-start:", await flash_panel.locator("[data-axis-row]").count() == 1)
        print("flash: no size-row (no sizeMode concept, unlike periph-like):", await flash_panel.locator("[data-size-row]").count() == 0)
        print("flash: fixation toggle present pre-start:", await flash_panel.locator("[data-fixtoggle-row]").count() == 1)
        print("mot: style-row present pre-start:", await mot_panel.locator("[data-style-row]").count() == 1)
        print("mot: both colour pickers present pre-start (Objekte + Ziel):",
              await mot_panel.locator("[data-colors]").count() == 1 and await mot_panel.locator("[data-targetcolors]").count() == 1)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        detail = pg.locator("#cardioAddonPickerDetail")
        saved_flash_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['flash']")
        saved_mot_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['mot']")

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        # ==== Flash (index 17): axes/zones + fixation live ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(17).click(); await pg.wait_for_timeout(80)
        print("flash: all 3 axes active by default live:",
              await detail.locator('[data-axis].active').count() == 3)
        print("flash: fixation shown as enabled by default, text input + colours + size visible:",
              await detail.locator('input[data-fixchar]').count() == 1 and await detail.locator('[data-fixcolors]').count() == 1)

        # live-edit: disable the fixpoint entirely, and narrow "Bereich" to
        # a single zone - fixation lives inside the collapsed
        # "Feineinstellungen", so expand it first
        await detail.locator("details.advanced summary").click(); await pg.wait_for_timeout(100)
        await detail.locator('[data-fixtoggle="0"]').click(); await pg.wait_for_timeout(80)
        print("fixation options disappear once 'Ausblenden' is picked:", await detail.locator('input[data-fixchar]').count() == 0)
        await detail.locator('[data-zones-toggle]').click(); await pg.wait_for_timeout(80)
        zones = detail.locator(".periph-zone[data-zone]")
        for i in range(7):
            await zones.nth(i).click(); await pg.wait_for_timeout(30)
        print("flash: zones narrowed down to one live:", await detail.locator(".periph-zone[data-zone].active").count() == 1)

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("flash takes over full-screen:", await pg.is_visible("#flashPlayer") and await pg.is_hidden("#cardioPlayer"))
        print("live-disabled fixpoint is actually hidden in the running game (not the leftover real default):",
              await pg.is_hidden("#flashFixpointEl"))
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#flashPlayer"))

        saved_flash_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['flash']")
        print("flash: saved fixEnabled/zones untouched by the live edit, even after running it:",
              saved_flash_after["fixEnabled"] == saved_flash_before["fixEnabled"] and saved_flash_after["zones"] == saved_flash_before["zones"])

        # ==== MOT (index 18): Darstellung + Farbe des Ziels live ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(18).click(); await pg.wait_for_timeout(80)
        print("mot: 'Flach' active by default live:", await detail.locator('[data-motstyle="flach"].active').count() == 1)
        await detail.locator('[data-motstyle="3d"]').click(); await pg.wait_for_timeout(80)
        print("mot: style switches to 3D-Optik live:", await detail.locator('[data-motstyle="3d"].active').count() == 1)

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("mot takes over full-screen:", await pg.is_visible("#motPlayer") and await pg.is_hidden("#cardioPlayer"))
        print("the live-edited 3D style actually rendered (.style-3d on the objects):",
              await pg.locator(".mot-object.style-3d").count() > 0)
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#motPlayer"))

        saved_mot_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['mot']")
        print("mot: saved style/targetColors untouched by the live edit, even after running it:",
              saved_mot_after["style"] == saved_mot_before["style"] and saved_mot_after["targetColors"] == saved_mot_before["targetColors"])

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
