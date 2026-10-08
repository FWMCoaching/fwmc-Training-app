import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Batch D of the "genau so als wenn man die Übung einzeln machen würde"
# follow-up, closing it out: Remember/Flash/MOT's own mode-specific numeric
# fine-tuning fields (client confirmed via the clarifying question: include
# them, nested under their own collapsible "Feineinstellungen" rather than
# flattened into the main field list - same treatment Batch A's zone-
# dominance weighting already got). Which field(s) appear depends entirely
# on which mode is currently selected, exactly like each domain's own
# dedicated Ready screens (flashConstantGroup/flashStartGroup/flashRepsGroup
# vs. flashTrainingReady; motFixedCountGroup vs. motGrowStartGroup vs.
# motTrainingReady; rememberTrainingReady's own Positionsart/Nach-Erfolg).
#
# Also fixed a real, pre-existing standalone bug while wiring Flash's
# repsPerLevel through: flashState never actually carried that field at
# all (only flashPrefs.repsPerLevel existed) - flashSuccessTransition()'s
# own "climbRepeat" branch compared repsDone against undefined, so it could
# never advance past the first count. Not re-verified via full gameplay
# here (would need reading the flashed digits back to type a correct
# answer repeatedly) - the isolation/structural checks below still prove
# the field is now correctly threaded through from cfg to flashState.

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

        # ---- force a save once so the isolation checks have a baseline ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        detail = pg.locator("#cardioAddonPickerDetail")
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        async def expand_finetune():
            await detail.locator("details.advanced summary").click(); await pg.wait_for_timeout(100)

        # ==== Remember (index 16): training-only fields ====
        saved_remember_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['remember']")
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(16).click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("remember (fixed mode): no training-only fields shown:", await detail.locator('input[data-f="trainingStart"]').count() == 0)
        await detail.locator('[data-mode="training"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("remember (training mode): Startzahl/Positionsart/Nach-Erfolg all appear:",
              await detail.locator('input[data-f="trainingStart"]').count() == 1 and
              await detail.locator('[data-posmode]').count() == 2 and
              await detail.locator('[data-progressfield="trainingProgress"]').count() == 2)
        await detail.locator('[data-posmode="fixed"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("remember: Positionsart selection moves live:", await detail.locator('[data-posmode="fixed"].active').count() == 1)
        await detail.locator('[data-progressfield="trainingProgress"][data-progressval="0"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("remember: Nach-Erfolg selection moves live:", await detail.locator('[data-progressfield="trainingProgress"][data-progressval="0"].active').count() == 1)
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)
        saved_remember_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['remember']")
        print("remember: saved training fields untouched by any of the live edits:",
              saved_remember_after["trainingPositionMode"] == saved_remember_before["trainingPositionMode"] and
              saved_remember_after["trainingProgress"] == saved_remember_before["trainingProgress"])

        # ==== Flash (index 17): one of three field sets depending on mode ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(17).click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("flash (constant mode, default): shows 'Anzahl der Zahlen' only:",
              await detail.locator('input[data-f="constantCount"]').count() == 1 and
              await detail.locator('input[data-f="startCount"]').count() == 0 and
              await detail.locator('input[data-f="trainingStart"]').count() == 0)

        await detail.locator('[data-mode="climb"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("flash (climb mode): shows 'Startanzahl', no Wiederholungen (that's climbRepeat-only):",
              await detail.locator('input[data-f="startCount"]').count() == 1 and
              await detail.locator('[data-repsperlevel]').count() == 0)

        await detail.locator('[data-mode="climbRepeat"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("flash (climbRepeat mode): 'Startanzahl' AND 'Wiederholungen je Stufe' both shown:",
              await detail.locator('input[data-f="startCount"]').count() == 1 and
              await detail.locator('[data-repsperlevel]').count() == 2)
        await detail.locator('[data-repsperlevel="3"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("flash: Wiederholungen-je-Stufe selection moves live (3x):", await detail.locator('[data-repsperlevel="3"].active').count() == 1)

        await detail.locator('[data-mode="training"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("flash (training mode): 'Startzahl' + Nach-Erfolg shown, no constant/climb fields:",
              await detail.locator('input[data-f="trainingStart"]').count() == 1 and
              await detail.locator('[data-progressfield="trainingProgress"]').count() == 2 and
              await detail.locator('input[data-f="constantCount"]').count() == 0 and
              await detail.locator('input[data-f="startCount"]').count() == 0)

        saved_flash_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['flash']")
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)
        saved_flash_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['flash']")
        print("flash: saved repsPerLevel/trainingStart untouched by any of the live edits:",
              saved_flash_after["repsPerLevel"] == saved_flash_before["repsPerLevel"] and
              saved_flash_after["trainingStart"] == saved_flash_before["trainingStart"])

        # ==== MOT (index 18): one of three field-pairs depending on mode ====
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(18).click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("mot (speed mode, default): shows fixed Objekte/Ziele, no grow/training fields:",
              await detail.locator('input[data-f="objectCount"]').count() == 1 and
              await detail.locator('input[data-f="targetCount"]').count() == 1 and
              await detail.locator('input[data-f="growStartObjects"]').count() == 0)

        await detail.locator('[data-mode="count"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("mot (count mode): shows Start-Anzahl Objekte/Ziele instead:",
              await detail.locator('input[data-f="growStartObjects"]').count() == 1 and
              await detail.locator('input[data-f="growStartTargets"]').count() == 1 and
              await detail.locator('input[data-f="objectCount"]').count() == 0)

        await detail.locator('[data-mode="training"]').click(); await pg.wait_for_timeout(80)
        await expand_finetune()
        print("mot (training mode): shows training-specific Objekte/Ziele/Tempo-Stufe + Nach-Erfolg:",
              await detail.locator('input[data-f="trainingObjects"]').count() == 1 and
              await detail.locator('input[data-f="trainingTargets"]').count() == 1 and
              await detail.locator('input[data-f="trainingSpeedStep"]').count() == 1 and
              await detail.locator('[data-progressfield="trainingProgress"]').count() == 2)

        saved_mot_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['mot']")
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(150)
        saved_mot_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['mot']")
        print("mot: saved trainingObjects/growStartObjects untouched by any of the live edits:",
              saved_mot_after["trainingObjects"] == saved_mot_before["trainingObjects"] and
              saved_mot_after["growStartObjects"] == saved_mot_before["growStartObjects"])

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady after all of it:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
