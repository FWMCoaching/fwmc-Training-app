import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- navigate to Cardio tab ----
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        print("cardioHome visible:", await pg.is_visible("#cardioHome"))
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        print("cardioReady visible:", await pg.is_visible("#cardioReady"))
        print("start button disabled with no items:", await pg.is_disabled("#cardioStartBtn"))

        # ---- add two activities ----
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Rad fahren"'); await pg.wait_for_timeout(100)
        print("2 blocks in list:", await pg.locator("#cardioList .circuit-item-row").count() == 2)
        print("start button enabled now:", not await pg.is_disabled("#cardioStartBtn"))
        print("default duration shown as 10 Min.:", "10 Min." in await pg.inner_text("#cardioList"))

        # ---- shorten duration via stepper (10 min -> 9 min) ----
        first_row = pg.locator("#cardioList .circuit-item-row").nth(0)
        await first_row.locator('.circuit-step[data-dir="-1"]').first.click(); await pg.wait_for_timeout(100)
        print("duration decreased by 1 min:", "9 Min." in await first_row.inner_text())

        # ---- set a label ----
        await first_row.locator(".circuit-item-note").fill("Warm-up"); await first_row.locator(".circuit-item-note").blur()
        await pg.wait_for_timeout(150)

        # ---- enable interval on second block ----
        second_row = pg.locator("#cardioList .circuit-item-row").nth(1)
        await second_row.locator(".cardio-interval-toggle input").check(); await pg.wait_for_timeout(150)
        print("interval fields appear:", await second_row.locator(".cardio-interval-fields").count() == 1)

        # ---- remove second block, re-add for a clean 2-block set ----
        # (leave as-is - both blocks stay for the sequencing test)

        # ---- save as preset ----
        await pg.click("#cardioSaveBtn"); await pg.wait_for_timeout(150)
        await pg.fill("#cardioSaveNameInput", "Test-Einheit")
        await pg.click("#cardioSaveConfirmBtn"); await pg.wait_for_timeout(200)
        print("saved preset appears:", "Test-Einheit" in await pg.inner_text("#cardioSavedList"))

        # ==== Dual-task settings ====
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        print("addon body visible after enabling:", await pg.is_visible("#cardioAddonBody"))
        await pg.check('#cardioAddonPoolGrid input[data-pool="vt-color"]'); await pg.wait_for_timeout(150)
        print("fine-tune panel appears for vt-color:", await pg.locator(".cardio-guest-panel").count() == 1)
        # set the interval window short (20s-20s) so the test can actually observe a trigger
        await pg.fill("#cardioAddonIntervalMinSlider", "20")
        await pg.dispatch_event("#cardioAddonIntervalMinSlider", "input")
        await pg.fill("#cardioAddonIntervalMaxSlider", "20")
        await pg.dispatch_event("#cardioAddonIntervalMaxSlider", "input")
        await pg.wait_for_timeout(150)
        print("interval min/max both show 20s:", "20s" in await pg.inner_text("#cardioAddonIntervalMinValue") and "20s" in await pg.inner_text("#cardioAddonIntervalMaxValue"))
        # set the guest window's own duration short too (5s) so it finishes fast on its own
        await pg.fill('.cardio-guest-panel input[data-f="duration"]', "5")
        await pg.dispatch_event('.cardio-guest-panel input[data-f="duration"]', "input")
        await pg.wait_for_timeout(150)

        # ---- reload the page and confirm settings persisted ----
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        print("addon toggle persisted checked after reload:", await pg.is_checked("#cardioAddonEnableToggle"))
        print("pool selection persisted after reload:", await pg.is_checked('#cardioAddonPoolGrid input[data-pool="vt-color"]'))
        print("blocks persisted after reload:", await pg.locator("#cardioList .circuit-item-row").count() == 2)
        print("label persisted after reload:", await pg.locator("#cardioList .circuit-item-note").nth(0).input_value() == "Warm-up")

        # ==== Run the sequence: skip through both blocks quickly ====
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("cardioPlayer visible after start:", await pg.is_visible("#cardioPlayer"))
        print("first activity name shown:", "Joggen" in await pg.inner_text("#cardioActivityTitle"))
        # .cardio-block-progress is CSS text-transform:uppercase, so
        # inner_text() (the rendered text) comes back upper-cased - compare
        # case-insensitively rather than assume the raw textContent's casing.
        print("block progress shows 1 von 2:", "1 von 2" in (await pg.inner_text("#cardioBlockProgress")).lower())
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(300)
        print("second activity name shown after skip:", "Rad fahren" in await pg.inner_text("#cardioActivityTitle"))
        print("block progress shows 2 von 2:", "2 von 2" in (await pg.inner_text("#cardioBlockProgress")).lower())
        print("interval phase label visible (Intensive/Leichtere Belastung):", await pg.is_visible("#cardioPhaseLabel"))

        # ==== Wait ~21s for the dual-task guest window to trigger ====
        await pg.wait_for_timeout(21000)
        guest_triggered = await pg.is_visible("#player") and not await pg.is_visible("#cardioPlayer")
        print("guest window (VT-Farbe) took over the screen:", guest_triggered)

        # let the 5s guest window finish on its own (VT-Farbe adds its own
        # lead-in countdown on top of the configured duration) -> should
        # return to cardio
        await pg.wait_for_timeout(10000)
        print("returned to cardioPlayer after guest window finished:", await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))

        # ==== finish the sequence via skip ====
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(400)
        print("done panel shown after last block:", await pg.is_visible("#cardioDonePanel"))
        print("done summary mentions 2 Übungen:", "2" in (await pg.inner_text("#cardioDoneSummary")))

        await pg.click("#cardioDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady:", await pg.is_visible("#cardioReady"))

        # ==== history entry recorded ==== (cardioReady has no nav bar of its
        # own, same as workoutTabataReady - go via cardioHome first)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('#cardioHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(200)
        history_text = await pg.inner_text("#historyList") if await pg.is_visible("#historySection") else ""
        print("cardio history entry recorded on home:", "Cardio" in history_text)

        # ==== Abort paths: cardioPlayer is a "player" overlay (like
        # workoutPlayer/els.player), not a SCREENS member - showScreen()
        # alone never hides it, so both abort routes need their own explicit
        # hide (caught a real bug here: abortCardio() originally forgot it). ====
        await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Schwimmen"'); await pg.wait_for_timeout(100)

        # abort mid-cardio, no guest active - cardioBackBtn -> abortCardio()
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)
        print("abort mid-cardio: back at cardioReady:", await pg.is_visible("#cardioReady"))
        print("abort mid-cardio: cardioPlayer hidden:", not await pg.is_visible("#cardioPlayer"))

        # abort DURING a guest window - shared player bar's Beenden button
        # now returns to the still-running Cardio session rather than
        # ending the whole thing (abortTraining()'s cardioGuestActive
        # branch calls returnFromCardioGuest(), not abortCardio() - a
        # reported bug fix, see cardio_addon_abort_test.py for full
        # coverage). Ending the whole session from here needs the normal
        # follow-up cardioBackBtn tap, same as any other point mid-Cardio.
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.wait_for_timeout(21000)
        print("guest window active before abort:", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(400)
        print("Beenden mid-guest returns to the still-running cardioPlayer, not cardioReady:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player") and not await pg.is_visible("#cardioReady"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)
        print("cardioBackBtn from there still ends the whole session as normal:", await pg.is_visible("#cardioReady"))

        # state is clean afterward - a fresh run starts normally
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("fresh cardio run starts cleanly after prior aborts:", await pg.is_visible("#cardioPlayer"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
