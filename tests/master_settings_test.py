import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Master-Einstellungen: a no-login "profile" (client's own framing) reachable
# via a gear button top-right of every section's brandbar - accessibility
# presets (colour vision, a physical/motor limitation, hearing) that would
# otherwise need re-setting in every exercise's own Feineinstellungen, plus a
# locally remembered history of Trainings-Codes. Explicitly local-only
# (localStorage), same as every other preference in this app - the sheet
# says so up top.
#
# 2026-09-28 redesign: everything under "Vorhandene Einschränkungen" - no
# "Normal"/"Keine" button anywhere (nothing selected already means no
# restriction), multi-select throughout (colour vision can have more than
# one type ticked, arm/leg restrictions share one multi-select list so any
# combination of the 4 extremities can be restricted at once), and Hören is
# a plain checkbox instead of a normal/gehörlos choice.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { localStorage.removeItem('fwmc-master-v1'); localStorage.removeItem('fwmc-code-history-v1'); localStorage.removeItem('fwmc-movement-v1'); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        print("gear button count (one per brandbar):", await pg.locator(".master-settings-btn").count())
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        print("sheet open:", await pg.is_visible("#masterSettingsSheet"))
        privacy_text = await pg.inner_text("#masterSettingsSheet .group-help >> nth=0")
        print("privacy note mentions local-only:", "Browser" in privacy_text and "Cloud" in privacy_text)
        print("umbrella heading present:", "Vorhandene Einschränkungen" in await pg.inner_text("#masterSettingsSheet"))
        print("no 'Normal' button anywhere in the sheet:", "Normal" not in await pg.inner_text("#masterSettingsSheet"))
        print("no 'Keine' button anywhere in the sheet:", "Keine" not in await pg.inner_text("#masterSettingsSheet"))
        print("code history hidden when empty:", await pg.is_hidden("#masterCodeHistoryGroup"))

        # ---- Farbsehen: 3 options now (rotgruen/blaugelb/voll), all unticked
        # by default, multi-select ----
        print("3 colour-vision options offered:", await pg.locator("#masterColorVisionRow [data-master-cvd]").count() == 3)
        print("none active by default:", await pg.locator("#masterColorVisionRow .choice.active").count() == 0)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngReadyStartBtn")
        async def wait_stimulus_phase(max_polls=60):
            for _ in range(max_polls):
                cls = await pg.get_attribute("#gngStimulus", "class") or ""
                if "go" in cls or "nogo" in cls:
                    return cls
                await pg.wait_for_timeout(80)
            return ""
        async def exit_gng():
            await pg.click("#gngBackBtn"); await pg.wait_for_timeout(150)
            if await pg.is_visible("#confirmYesBtn"):
                await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(150)
            if await pg.is_visible("#gngDoneBackBtn"):
                await pg.click("#gngDoneBackBtn"); await pg.wait_for_timeout(150)

        cls_before = await wait_stimulus_phase()
        bg_before = await pg.eval_on_selector("#gngStimulus", "el => getComputedStyle(el).backgroundColor")
        print("GNG stimulus phase reached, default colour captured:", bool(cls_before), bg_before)
        await exit_gng()

        # tick Rot-Grün-Schwäche (and, to prove multi-select, Blau-Gelb too)
        # and confirm GNG's colour actually changes
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click('[data-master-cvd="rotgruen"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-master-cvd="blaugelb"]'); await pg.wait_for_timeout(100)
        print("cvd rotgruen active:", "active" in (await pg.get_attribute('[data-master-cvd="rotgruen"]', "class") or ""))
        print("cvd blaugelb ALSO active (multi-select):", "active" in (await pg.get_attribute('[data-master-cvd="blaugelb"]', "class") or ""))
        stored = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-master-v1')||'{}').colorVision")
        print("both stored in colorVision array:", sorted(stored) == ["blaugelb", "rotgruen"])
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngReadyStartBtn")
        await wait_stimulus_phase()
        bg_after = await pg.eval_on_selector("#gngStimulus", "el => getComputedStyle(el).backgroundColor")
        print("GNG stimulus colour changed under Rot-Grün-Schwäche:", bg_after != bg_before, bg_after)
        await exit_gng()

        # untick both again for a clean slate before the limb test
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click('[data-master-cvd="rotgruen"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-master-cvd="blaugelb"]'); await pg.wait_for_timeout(100)
        print("both cvd options cleared:", await pg.locator("#masterColorVisionRow .choice.active").count() == 0)

        # ---- Bewegungseinschränkung: one shared multi-select set of 4
        # extremity tags, any combination can be ticked at once ----
        print("2 arm options, 2 leg options offered:", await pg.locator("#masterArmLimbRow [data-master-limb]").count() == 2 and await pg.locator("#masterLegLimbRow [data-master-limb]").count() == 2)
        await pg.click('[data-master-limb="armL"]'); await pg.wait_for_timeout(150)
        print("arm limb armL active:", "active" in (await pg.get_attribute('[data-master-limb="armL"]', "class") or ""))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.section-tab[data-section="movement"]:visible'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        chip_labels = await pg.locator("#movementPicker .movement-chip span").all_inner_texts()
        print("armL chips hidden under 'linker Arm eingeschränkt':", not any("Linker Arm" in t for t in chip_labels))
        print("armR/leg chips still present:", any("Rechter Arm" in t for t in chip_labels) and any("Bein" in t for t in chip_labels))
        print("total chip count now 6 (8 minus 2 armL ones):", len(chip_labels) == 6)

        # also restrict a leg -> combines with the arm restriction already set
        await pg.click("#movementBackToHome"); await pg.wait_for_timeout(150)
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click('[data-master-limb="legR"]'); await pg.wait_for_timeout(150)
        print("leg limb legR active:", "active" in (await pg.get_attribute('[data-master-limb="legR"]', "class") or ""))
        print("arm limb still armL (both restrictions coexist):", "active" in (await pg.get_attribute('[data-master-limb="armL"]', "class") or ""))
        stored_limbs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-master-v1')||'{}').restrictedLimbs")
        print("both stored together in restrictedLimbs:", sorted(stored_limbs) == ["armL", "legR"])
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="movement"]:visible'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        chip_labels_both = await pg.locator("#movementPicker .movement-chip span").all_inner_texts()
        print("armL AND legR chips both hidden now (combined restriction):", not any("Linker Arm" in t for t in chip_labels_both) and not any("Rechtes Bein" in t for t in chip_labels_both))
        print("total chip count now 4 (8 minus 2 armL minus 2 legR):", len(chip_labels_both) == 4)

        # untick both to reset
        await pg.click("#movementBackToHome"); await pg.wait_for_timeout(150)
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click('[data-master-limb="armL"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-master-limb="legR"]'); await pg.wait_for_timeout(150)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        chip_labels_after = await pg.locator("#movementPicker .movement-chip span").all_inner_texts()
        print("all 8 chips back once both limb restrictions cleared:", len(chip_labels_after) == 8)

        # ---- Trainings-Code-Verlauf: entering a code records it, shows up
        # in the sheet with first/last-used, and tapping it relaunches ----
        await pg.click('.section-tab[data-section="visual"]:visible'); await pg.wait_for_timeout(150)
        await pg.fill("#programCodeInput", "dig01")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(400)
        print("programme intro opened from a local code:", await pg.is_visible("#programIntro"))
        await pg.click("#programBackToHome"); await pg.wait_for_timeout(150)

        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        print("code history now visible:", await pg.is_visible("#masterCodeHistoryGroup"))
        history_text = await pg.inner_text("#masterCodeHistoryList")
        print("history shows the code with zuerst/zuletzt:", "dig01" in history_text and "zuerst" in history_text and "zuletzt" in history_text)

        # tap-to-relaunch from history
        await pg.click("#masterCodeHistoryList .bundle-item"); await pg.wait_for_timeout(400)
        print("tapping history item relaunched the programme intro:", await pg.is_visible("#programIntro"))
        print("sheet closed itself on relaunch:", await pg.is_hidden("#masterSettingsSheet"))
        await pg.click("#programBackToHome"); await pg.wait_for_timeout(150)

        # ---- Hören: a plain checkbox now (ticked = restriction present),
        # greys out (not hides) VT's "Sehen & Hören", the one exercise in
        # the app that's tagged data-tags="ton" and genuinely can't be
        # adapted (unlike Go/No-Go's colour, which just swaps instead of
        # blocking) - tapping the greyed card should open Settings again
        # rather than the exercise.
        await pg.click('.section-tab[data-section="visual"]:visible'); await pg.wait_for_timeout(150)
        cross_card = pg.locator('.excard[data-exercise="cross-modal"]')
        print("Sehen & Hören not incompatible by default:", "incompatible" not in (await cross_card.get_attribute("class") or ""))
        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        print("hearing checkbox unticked by default:", not await pg.is_checked("#masterHearingCheck"))
        await pg.check("#masterHearingCheck"); await pg.wait_for_timeout(100)
        print("hearing checkbox now ticked:", await pg.is_checked("#masterHearingCheck"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        print("Sehen & Hören now greyed:", "incompatible" in (await cross_card.get_attribute("class") or ""))
        print("blocked note references Einstellungen:", "Einstellungen" in await cross_card.locator(".excard-blocked-note").inner_text())
        other_card = pg.locator('.excard[data-exercise="vt-color"]')
        print("an unrelated card stays unaffected:", "incompatible" not in (await other_card.get_attribute("class") or ""))
        await cross_card.click(); await pg.wait_for_timeout(200)
        print("tapping the greyed card opens Settings, not the exercise:", await pg.is_visible("#masterSettingsSheet") and await pg.is_hidden("#ready"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        await other_card.click(); await pg.wait_for_timeout(150)
        print("an unaffected exercise still opens normally:", await pg.is_visible("#ready"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)

        await pg.locator(".master-settings-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.uncheck("#masterHearingCheck"); await pg.wait_for_timeout(100)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        print("Sehen & Hören usable again after unticking hearing:", "incompatible" not in (await cross_card.get_attribute("class") or ""))
        await cross_card.click(); await pg.wait_for_timeout(150)
        print("Sehen & Hören opens normally once reset:", await pg.is_visible("#ready"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
