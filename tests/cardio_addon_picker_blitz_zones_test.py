import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Batch B of the "genau so als wenn man die Übung einzeln machen würde"
# follow-up: Blitz-Raster's own "Bereich" (3x3-Zonen-Raster restricting
# which grid cells can light up) was previously hardcoded to all zones
# under a Cardio guest burst ("the Cardio Feineinstellungen panel doesn't
# offer a zones picker" - a simplification this batch undoes). Blitz's own
# zone mechanism is simpler than Periphere Wahrnehmung's (Batch A): no axes
# concept at all, no useZones toggle, no dominance weighting - the grid is
# always on, directly, same as the standalone Ready screen's own
# blitzZoneGroup/blitzZoneGrid/blitzZoneAllBtn.

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

        # ---- pre-start Feineinstellungen panel shows the new zone picker ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid input[data-pool="blitz-raster"]'); await pg.wait_for_timeout(150)
        blitz_panel = pg.locator('.cardio-guest-panel:has(input[data-type="blitz-raster"])')
        print("blitz-raster: zone grid present pre-start:", await blitz_panel.locator("[data-blitzzone-grid]").count() == 1)
        print("blitz-raster: 'Überall' present pre-start:", await blitz_panel.locator("[data-blitzzone-all]").count() == 1)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        detail = pg.locator("#cardioAddonPickerDetail")
        saved_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['blitz-raster']")

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(13).click(); await pg.wait_for_timeout(80)

        print("all 8 zones active by default:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 8)
        print("'Überall' active with all 8 selected:", await detail.locator("[data-blitzzone-all].active").count() == 1)

        zones = detail.locator(".periph-zone[data-blitzzone]")
        for i in range(7):
            await zones.nth(i).click(); await pg.wait_for_timeout(30)
        print("zones can be narrowed down to just one:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 1)
        await detail.locator(".periph-zone[data-blitzzone].active").click(); await pg.wait_for_timeout(80)
        print("the last remaining zone can't be deselected by hand:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 1)

        # "Überall" CAN reach zero from a fully-on state (same all-on/all-off
        # toggle as the standalone blitzZoneAllBtn) - first restore to full,
        # then toggle off
        await detail.locator("[data-blitzzone-all]").click(); await pg.wait_for_timeout(80)
        print("'Überall' from a partial state goes to fully-on:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 8)
        await detail.locator("[data-blitzzone-all]").click(); await pg.wait_for_timeout(80)
        print("'Überall' clicked again while fully-on reaches zero:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 0)
        print("zero-zones warning hint shown:", await detail.locator(".color-hint.warn").count() == 1)
        await detail.locator("[data-blitzzone-all]").click(); await pg.wait_for_timeout(80)
        print("'Überall' once more restores all 8:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 8)

        print("cancelling leaves the saved zones default untouched so far:",
              await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['blitz-raster'].zones") == saved_before["zones"])

        # ---- for real: live-narrow to a single zone, start, confirm the
        # saved default stays untouched even after actually running it ----
        await detail.locator(".periph-zone[data-blitzzone]").nth(0).click(); await pg.wait_for_timeout(30)
        for i in range(1, 8):
            await detail.locator(".periph-zone[data-blitzzone]").nth(i).click(); await pg.wait_for_timeout(30)
        print("live-narrowed down to a single zone:", await detail.locator(".periph-zone[data-blitzzone].active").count() == 1)

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("blitz-raster takes over full-screen:", await pg.is_visible("#blitzPlayer") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#blitzPlayer"))

        saved_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['blitz-raster'].zones")
        print("saved zones default (all 8) still untouched after actually running the live-narrowed burst:",
              saved_after == saved_before["zones"] and len(saved_after) == 8)

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
