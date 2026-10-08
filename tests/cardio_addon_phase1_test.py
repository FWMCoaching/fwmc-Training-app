import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Phase 1: Cardio "+ Zusatzimpuls" extended from the original 4 guest types
# to every remaining exercise in the shared EXERCISES catalog that already
# runs through runSession()/tick()/state.exercise - vrw-original, stroop-bg,
# 4-diag, 8-solo, 8-vrw, cross-modal, cone-compass, cone-tap (12 total now).
# Deliberately NOT periph-flash (its own much larger settings surface,
# separate follow-up) and NOT the ~25 NAT-domain exercises (each has its own
# dedicated player/prefs, not this shared engine at all - a much bigger,
# separate piece of work, contrary to an earlier too-optimistic estimate).
#
# CARDIO_GUEST_TYPES' fixed order (app.js) - used as picker-button indices
# below rather than text-matching, since "8 Pfeile" and "8 Pfeile · Rot/Grün"
# both render a plain "8 Pfeile" as their main label (only the <small>
# subtitle differs), which text-matching can't reliably disambiguate:
#  0 addon-flash, 1 vt-color, 2 vrw-original, 3 stroop-classic,
#  4 stroop-bg, 5 4-straight, 6 4-diag, 7 8-solo, 8 8-vrw, 9 cross-modal,
#  10 cone-compass, 11 cone-tap

NEW_TYPES = [
    (2, "vrw-original"), (4, "stroop-bg"), (6, "4-diag"), (7, "8-solo"),
    (8, "8-vrw"), (9, "cross-modal"), (10, "cone-compass"), (11, "cone-tap"),
]

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

        # ---- Feineinstellungen: pool grid + fine-tune gating ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        # 14 as of NAT batch 1 (2026-09-30): the 12 from this file's own
        # batch + periph-flash + blitz-raster (see cardio_addon_nat_batch1_test.py)
        print("pool grid now offers 22 types (incl. Rechnen, Richtungskreuz):", await pg.locator("#cardioAddonPoolGrid [data-pool]").count() == 22)
        for _, t in NEW_TYPES:
            await pg.check(f'#cardioAddonPoolGrid input[data-pool="{t}"]')
        await pg.wait_for_timeout(200)
        print("8 fine-tune panels open (only the newly-checked ones):", await pg.locator(".cardio-guest-panel").count() == 8)

        vrw_panel = pg.locator('.cardio-guest-panel:has(input[data-type="vrw-original"])')
        print("vrw-original: no background row (bgIsStimulus):", await vrw_panel.locator("[data-bgcolors]").count() == 0)
        print("vrw-original: has a colour row (usesColors):", await vrw_panel.locator("[data-colors]").count() == 1)

        crossmodal_panel = pg.locator('.cardio-guest-panel:has(input[data-type="cross-modal"])')
        print("cross-modal: has a background row:", await crossmodal_panel.locator("[data-bgcolors]").count() == 1)
        print("cross-modal: no colour row (no colour flags):", await crossmodal_panel.locator("[data-colors]").count() == 0)

        conetap_panel = pg.locator('.cardio-guest-panel:has(input[data-type="cone-tap"])')
        print("cone-tap: no background row (own hard-coded-white stage):", await conetap_panel.locator("[data-bgcolors]").count() == 0)
        print("cone-tap: no colour row:", await conetap_panel.locator("[data-colors]").count() == 0)
        print("cone-tap: only a Dauer field, no Reiz-Dauer/Pause fields:",
              await conetap_panel.locator('input[data-f="duration"]').count() == 1 and await conetap_panel.locator('input[data-f="stimulusS"]').count() == 0)

        # ---- live picker offers all 12 ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        print("picker offers all 22 types (incl. Rechnen, Richtungskreuz):", await pg.locator("#cardioAddonPickerTypeRow .choice").count() == 22)
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)

        # ---- each new type actually takes over and returns cleanly ----
        for idx, t in NEW_TYPES:
            await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
            await pg.locator("#cardioAddonPickerTypeRow .choice").nth(idx).click(); await pg.wait_for_timeout(80)
            await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(400)
            if t == "cone-tap":
                took_over = await pg.is_visible("#coneOrderStage") and await pg.is_visible("#player")
            else:
                took_over = await pg.is_visible("#player") and await pg.is_hidden("#coneOrderStage")
            print(f"{t}: takes over full-screen:", took_over and await pg.is_hidden("#cardioPlayer"))
            await pg.click("#backBtn"); await pg.wait_for_timeout(300)
            print(f"{t}: Beenden returns to still-running cardioPlayer:",
                  await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player") and not await pg.is_visible("#coneOrderStage"))

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
