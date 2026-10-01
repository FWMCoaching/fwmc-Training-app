import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# NAT batch 1: Cardio "+ Zusatzimpuls" extended with the first two NAT-domain
# exercises - "periph-flash" (Periphere Wahrnehmung, turns out to share the
# same runSession() engine as everything in Phase 1) and "blitz-raster"
# (Blitz-Raster, a genuinely separate engine - startBlitzGame() got a new
# prefsOverride parameter so a Cardio guest burst never reads or mutates the
# client's own saved blitzPrefs/best score). Also covers the new category
# grouping (Visual Training / Neuroathletik) in both the Feineinstellungen
# pool grid and the live picker. Remember/Flash/MOT are a later batch.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- baseline: note the client's own real Blitz-Raster best score
        # before touching Cardio at all, to later prove a guest burst never
        # changes it ----
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('.sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        best_before = await pg.inner_text("#blitzBestHint")

        await pg.click('#natHome .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)

        # ---- pool grid: grouped by category, both new types present ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        group_labels = await pg.locator("#cardioAddonPoolGrid .cardio-pool-group-label").all_inner_texts()
        print("pool grid grouped Visual Training then Neuroathletik:", group_labels == ["Visual Training", "Neuroathletik (NAT)"])
        print("periph-flash offered:", await pg.locator('#cardioAddonPoolGrid input[data-pool="periph-flash"]').count() == 1)
        print("blitz-raster offered:", await pg.locator('#cardioAddonPoolGrid input[data-pool="blitz-raster"]').count() == 1)

        await pg.check('#cardioAddonPoolGrid input[data-pool="periph-flash"]')
        await pg.check('#cardioAddonPoolGrid input[data-pool="blitz-raster"]')
        await pg.wait_for_timeout(200)

        # ---- periph-flash panel: kind-row, colours, background, standard
        # duration/stimulus/interval fields - same depth as addon-flash ----
        periph_panel = pg.locator('.cardio-guest-panel:has(input[data-type="periph-flash"])')
        print("periph-flash: kind-row present:", await periph_panel.locator("[data-kind-row]").count() == 1)
        print("periph-flash: colour row present:", await periph_panel.locator("[data-colors]").count() == 1)
        print("periph-flash: background row present:", await periph_panel.locator("[data-bgcolors]").count() == 1)
        print("periph-flash: stimulus/interval fields present:", await periph_panel.locator('input[data-f="stimulusS"]').count() == 1)

        # ---- blitz-raster panel: its own field set, no colour row, has bg ----
        blitz_panel = pg.locator('.cardio-guest-panel:has-text("Blitz-Raster")')
        print("blitz-raster: no colour row (no colour concept):", await blitz_panel.locator("[data-colors]").count() == 0)
        print("blitz-raster: no generic stimulus/interval fields:", await blitz_panel.locator('input[data-f="stimulusS"]').count() == 0)
        print("blitz-raster: Startanzahl field present:", await blitz_panel.locator('input[data-f="startCount"]').count() == 1)
        print("blitz-raster: difficulty choice-row present:", await blitz_panel.locator("[data-blitzdiff-row]").count() == 1)
        print("blitz-raster: grid-size choice-row present:", await blitz_panel.locator("[data-blitzgrid-row]").count() == 1)
        print("blitz-raster: 'Bei Fehler' choice-row present:", await blitz_panel.locator("[data-blitzerror-row]").count() == 1)
        print("blitz-raster: background row present:", await blitz_panel.locator("[data-bgcolors]").count() == 1)

        # ---- adjust a couple of blitz settings, short duration for a fast test ----
        await blitz_panel.locator('input[data-f="duration"]').fill("5")
        await blitz_panel.locator('input[data-f="duration"]').dispatch_event("input")
        await blitz_panel.locator('[data-blitzgrid="5"]').click(); await pg.wait_for_timeout(80)
        print("grid size 5x5 now active:", "active" in (await blitz_panel.locator('[data-blitzgrid="5"]').get_attribute("class")))

        # ---- live picker: grouped, both new types selectable ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        picker_groups = await pg.locator("#cardioAddonPickerTypeRow .cardio-addon-picker-group-label").all_inner_texts()
        print("picker grouped Visual Training then Neuroathletik:", picker_groups == ["Visual Training", "Neuroathletik (NAT)"])
        print("picker offers 17 choices total:", await pg.locator("#cardioAddonPickerTypeRow .choice").count() == 17)

        # index 12 = periph-flash (first NAT entry, right after the 12 VT ones)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(12).click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("periph-flash takes over full-screen:", await pg.is_visible("#player") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        print("periph-flash: Beenden returns to still-running cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))

        # index 13 = blitz-raster
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(13).click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("blitz-raster takes over full-screen (own #blitzPlayer):",
              await pg.is_visible("#blitzPlayer") and await pg.is_hidden("#cardioPlayer"))
        print("cardio badge visible on top of the Blitz-Raster guest burst:", await pg.is_visible("#cardioGuestBadge"))

        # ---- let it finish on its own -> back to cardio. The picker
        # clamps its own duration to a 15s floor (CARDIO_ADDON_PICKER_DURATION_MIN)
        # regardless of the Feineinstellungen's configured 5s default, so
        # the actual guest burst here runs 15s, not 5 - wait past that. ----
        await pg.wait_for_timeout(16000)
        print("blitz-raster guest burst auto-finished, back at cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#blitzPlayer"))

        # ---- early-abort path too: trigger again, tap Beenden mid-round ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(13).click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(300)
        print("blitz-raster early Beenden also returns to cardioPlayer (not blitzDonePanel):",
              await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#blitzPlayer") and await pg.is_hidden("#blitzDonePanel"))

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)

        # ---- the client's own real Blitz-Raster best score/settings were
        # never touched by any of the guest bursts above. cardioReady has
        # no section-tab nav of its own (only "← Zurück") - back to
        # cardioHome first. ----
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('#cardioHome .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('.sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        best_after = await pg.inner_text("#blitzBestHint")
        print("client's own Blitz-Raster best score unaffected by the guest bursts:", best_before == best_after)
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(200)
        print("client's own Blitz-Raster grid size still the real default (4x4), not the 5x5 set in Cardio's panel:",
              "active" in (await pg.locator('#blitzGridSizeRow [data-blitz-grid="4"]').get_attribute("class")))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
