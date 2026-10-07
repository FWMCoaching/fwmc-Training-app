import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# NAT batch 2: Cardio "+ Zusatzimpuls" extended with the remaining three NAT
# exercises - Remember, Flash-Speicher-Test, Objektverfolgung (MOT). Each has several
# starting modes (training vs. fixed vs. shuffle vs. ...), so this batch adds
# the new sub-mode-picker step to the live picker (cardioGuestModeList()) on
# top of the prefsOverride/cardioGuestActive pattern proven in batch 1
# (Blitz-Raster). CARDIO_GUEST_TYPES is now 18 entries (Gleichgewicht added 2026-10-06).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- baseline: the client's own real Remember best score, before
        # touching Cardio at all ----
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        best_before = await pg.inner_text("#rememberBestFixed")

        await pg.click('#natHome .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)

        # ---- pool grid + fine-tune panels ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        print("pool grid now offers 19 types:", await pg.locator("#cardioAddonPoolGrid [data-pool]").count() == 19)
        for t in ("remember", "flash", "mot"):
            await pg.check(f'#cardioAddonPoolGrid input[data-pool="{t}"]')
        await pg.wait_for_timeout(200)

        remember_panel = pg.locator('.cardio-guest-panel:has(input[data-type="remember"])')
        print("remember: mode-row with 3 modes:", await remember_panel.locator("[data-mode-row] button").count() == 3)
        print("remember: difficulty row present:", await remember_panel.locator("[data-diff-row]").count() == 1)
        print("remember: 'Bei Fehler' row present:", await remember_panel.locator("[data-error-row]").count() == 1)
        print("remember: no colour row (no colour concept):", await remember_panel.locator("[data-colors]").count() == 0)
        print("remember: no generic stimulus/interval fields:", await remember_panel.locator('input[data-f="stimulusS"]').count() == 0)
        print("remember: background row present:", await remember_panel.locator("[data-bgcolors]").count() == 1)

        flash_panel = pg.locator('.cardio-guest-panel:has(input[data-type="flash"])')
        print("flash: mode-row with 4 modes:", await flash_panel.locator("[data-mode-row] button").count() == 4)
        print("flash: kind-row present (buchstaben/zahlen/gemischt):", await flash_panel.locator("[data-kind-row]").count() == 1)
        print("flash: difficulty row present:", await flash_panel.locator("[data-diff-row]").count() == 1)

        mot_panel = pg.locator('.cardio-guest-panel:has(input[data-type="mot"])')
        print("mot: mode-row with 4 modes:", await mot_panel.locator("[data-mode-row] button").count() == 4)
        print("mot: has a colour row (Objektfarbe):", await mot_panel.locator("[data-colors]").count() == 1)
        print("mot: difficulty row present:", await mot_panel.locator("[data-diff-row]").count() == 1)

        # ---- live picker: full detail panel (same field set as the pre-
        # start Feineinstellungen panel), sub-mode step appears only for
        # these 3 ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        print("no mode-row for the first (VT) type by default:", await pg.locator("#cardioAddonPickerDetail [data-mode-row]").count() == 0)
        print("picker offers 19 choices total:", await pg.locator("#cardioAddonPickerTypeRow .choice").count() == 19)

        # index 15 = remember (13 VT + periph-flash + blitz-raster + remember)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(15).click(); await pg.wait_for_timeout(80)
        print("mode-row appears once Remember is selected:", await pg.locator("#cardioAddonPickerDetail [data-mode-row]").count() == 1)
        print("3 mode choices shown for Remember:", await pg.locator("#cardioAddonPickerDetail [data-mode-row] .choice").count() == 3)
        print("Remember's difficulty/error rows also present live (same depth as pre-start):",
              await pg.locator("#cardioAddonPickerDetail [data-diff-row]").count() == 1 and await pg.locator("#cardioAddonPickerDetail [data-error-row]").count() == 1)
        await pg.locator("#cardioAddonPickerDetail [data-mode-row] .choice").nth(1).click(); await pg.wait_for_timeout(80)
        print("second mode ('Bewegte Positionen') now active:", "active" in (await pg.locator("#cardioAddonPickerDetail [data-mode-row] .choice").nth(1).get_attribute("class")))

        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("remember takes over full-screen (own #rememberPlayer):",
              await pg.is_visible("#rememberPlayer") and await pg.is_hidden("#cardioPlayer"))
        print("cardio badge visible on top of the Remember guest burst:", await pg.is_visible("#cardioGuestBadge"))
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)
        print("remember: early Beenden returns to still-running cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#rememberPlayer"))

        # index 16 = flash
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(16).click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("flash takes over full-screen:", await pg.is_visible("#flashPlayer") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(300)
        print("flash: Beenden returns to still-running cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#flashPlayer"))

        # index 17 = mot
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(17).click(); await pg.wait_for_timeout(80)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
        print("mot takes over full-screen:", await pg.is_visible("#motPlayer") and await pg.is_hidden("#cardioPlayer"))
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(300)
        print("mot: Beenden returns to still-running cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#motPlayer"))

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(200)

        # ---- the client's own real Remember best score is untouched by
        # any of the guest bursts above ----
        await pg.click('#cardioHome .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        best_after = await pg.inner_text("#rememberBestFixed")
        print("client's own Remember best score unaffected by the guest bursts:", best_before == best_after)

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
