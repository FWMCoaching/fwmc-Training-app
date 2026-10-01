import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Batch A of the "genau so als wenn man die Übung einzeln machen würde"
# follow-up (cardio_addon_picker_full_settings_test.py covered the first,
# more modest pass - this one closes the remaining gap for the two periph-
# like guest types specifically): addon-flash's and periph-flash's own
# "Bereich" (axes/zones) and "Größe der Reize" controls, previously
# deliberately left out as a "keep the panel proportionate" simplification,
# now reinstated field-for-field. Periph-flash alone also gets the zone-
# dominance "Feineinstellungen" (addon-flash's own standalone panel never
# had this control either - see cardioGuestHasZoneWeights()), nested under
# its own collapsible per the client's explicit call on how deep this
# should go.

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

        # ---- pre-start Feineinstellungen panel: both periph-like types show
        # the new rows, zone-weighting only for periph-flash ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid input[data-pool="addon-flash"]'); await pg.wait_for_timeout(100)
        await pg.check('#cardioAddonPoolGrid input[data-pool="periph-flash"]'); await pg.wait_for_timeout(150)
        addon_panel = pg.locator('.cardio-guest-panel:has(input[data-type="addon-flash"])')
        periph_panel = pg.locator('.cardio-guest-panel:has(input[data-type="periph-flash"])')
        print("addon-flash: axis-row present pre-start:", await addon_panel.locator("[data-axis-row]").count() == 1)
        print("addon-flash: size-row present pre-start:", await addon_panel.locator("[data-size-row]").count() == 1)
        print("periph-flash: axis-row present pre-start:", await periph_panel.locator("[data-axis-row]").count() == 1)
        print("periph-flash: size-row present pre-start:", await periph_panel.locator("[data-size-row]").count() == 1)
        # both default to axes-mode (useZones false) so the zone grid/weights
        # aren't in the DOM yet either way at this point
        print("neither shows the zone grid yet (useZones off by default):",
              await addon_panel.locator("[data-zone-grid]").count() == 0 and await periph_panel.locator("[data-zone-grid]").count() == 0)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        detail = pg.locator("#cardioAddonPickerDetail")
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        # ==== addon-flash (index 0): axes/zones/size live, no weighting ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        print("addon-flash pre-selected by default:", "active" in (await pg.locator("#cardioAddonPickerTypeRow .choice").nth(0).get_attribute("class")))
        print("axis-row shows all 3 axes active by default (+ Überall):",
              await detail.locator('[data-axis="horizontal"].active').count() == 1 and
              await detail.locator('[data-axis="vertikal"].active').count() == 1 and
              await detail.locator('[data-axis="diagonal"].active').count() == 1 and
              await detail.locator('[data-axis-all].active').count() == 1)

        await detail.locator('[data-axis="horizontal"]').click(); await pg.wait_for_timeout(80)
        print("toggling one axis off deactivates it:", await detail.locator('[data-axis="horizontal"].active').count() == 0)
        print("'Überall' no longer active with only 2 of 3 on:", await detail.locator('[data-axis-all].active').count() == 0)
        # "Überall" from a PARTIAL state (2/3) goes to fully-on, same as the
        # standalone Ready screen's own periphAllBtn logic (allOn ? [] :
        # full) - it only reaches zero when clicked while ALREADY fully on
        await detail.locator('[data-axis-all]').click(); await pg.wait_for_timeout(80)
        print("'Überall' from a partial state (2/3) goes to fully-on instead:", await detail.locator('[data-axis].active').count() == 3)
        await detail.locator('[data-axis-all]').click(); await pg.wait_for_timeout(80)
        print("'Überall' clicked again while already fully-on reaches zero:",
              await detail.locator('[data-axis].active').count() == 0)
        print("zero-axes warning hint shown:", await detail.locator(".color-hint.warn").count() == 1)
        await detail.locator('[data-axis-all]').click(); await pg.wait_for_timeout(80)
        print("'Überall' once more restores all 3:", await detail.locator('[data-axis].active').count() == 3)

        await detail.locator('[data-zones-toggle]').click(); await pg.wait_for_timeout(80)
        print("switching to zone mode hides the axis-row:", await detail.locator("[data-axis-row]").count() == 0)
        print("zone grid shows 8 zone buttons, all active by default:", await detail.locator(".periph-zone[data-zone].active").count() == 8)
        print("addon-flash never shows zone-weighting (not on its own standalone panel either):",
              await detail.locator(".periph-zone-weights").count() == 0)

        zones = detail.locator(".periph-zone[data-zone]")
        for i in range(7):
            await zones.nth(i).click(); await pg.wait_for_timeout(30)
        print("zones can be narrowed down to just one:", await detail.locator(".periph-zone[data-zone].active").count() == 1)
        await detail.locator(".periph-zone[data-zone].active").click(); await pg.wait_for_timeout(80)
        print("the last remaining zone can't be deselected:", await detail.locator(".periph-zone[data-zone].active").count() == 1)

        await detail.locator('[data-zones-toggle]').click(); await pg.wait_for_timeout(80)
        print("toggling back brings the axis-row back:", await detail.locator("[data-axis-row]").count() == 1)

        print("size mode defaults to 'gleich':", await detail.locator('[data-sizemode="gleich"].active').count() == 1)
        await detail.locator('[data-sizemode="wachsend"]').click(); await pg.wait_for_timeout(80)
        print("size mode switches to 'wachsend':", await detail.locator('[data-sizemode="wachsend"].active').count() == 1 and await detail.locator('[data-sizemode="gleich"].active').count() == 0)

        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)

        # ==== periph-flash (index 12): same controls, PLUS zone-dominance
        # weighting collapsed under "Feineinstellungen" ====
        saved_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['periph-flash']")
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(12).click(); await pg.wait_for_timeout(80)
        await detail.locator('[data-zones-toggle]').click(); await pg.wait_for_timeout(80)
        print("periph-flash: zone grid shown with all 8 active by default:", await detail.locator(".periph-zone[data-zone].active").count() == 8)
        print("periph-flash: 'Feineinstellungen' collapsible present (8 zones selected):", await detail.locator("details.advanced").count() == 1)
        print("collapsed by default:", not await detail.locator("details.advanced").get_attribute("open"))

        await detail.locator("details.advanced summary").click(); await pg.wait_for_timeout(100)
        print("expands to show one dominance slider per selected zone (8):", await detail.locator('input[data-zoneweight]').count() == 8)

        first_weight = detail.locator('input[data-zoneweight]').first
        await first_weight.fill("3")
        await first_weight.dispatch_event("input")
        await pg.wait_for_timeout(80)
        print("dragging a zone's dominance slider updates its own label live:",
              "3×" in await detail.locator("[data-zoneweightvalue]").first.inner_text())

        # narrow down to a single zone -> the weighting section (meaningless
        # for just one zone) disappears
        zones2 = detail.locator(".periph-zone[data-zone]")
        for i in range(7):
            await zones2.nth(i).click(); await pg.wait_for_timeout(30)
        print("weighting section disappears once only one zone remains:", await detail.locator("details.advanced").count() == 0)

        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)
        saved_after_cancel = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['periph-flash']")
        print("cancelling leaves the saved default completely untouched (axes/zones/sizeMode/zoneWeights):",
              saved_after_cancel == saved_before)

        # ==== for real: live-edit axes/zones/size/weights, start, confirm
        # isolation even after actually running the burst ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(12).click(); await pg.wait_for_timeout(80)
        await detail.locator('[data-sizemode="wachsend"]').click(); await pg.wait_for_timeout(80)
        await detail.locator('[data-axis="horizontal"]').click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("periph-flash takes over full-screen:", await pg.is_visible("#player") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        print("returned to still-running cardioPlayer:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#player"))

        saved_after_run = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['periph-flash']")
        print("saved sizeMode/axes still untouched after actually running the live-edited burst:",
              saved_after_run["sizeMode"] == saved_before["sizeMode"] and saved_after_run["axes"] == saved_before["axes"])

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
