import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Client-facing "Kraft-/Wiederholungstraining" builder, v2 (2026-10-02):
# a whole Kraftplan of several exercises (like the Tabata Zirkel), each
# with its own rep range / sets / set rest, plus a rest between exercises
# and a start countdown. Also covers the live set stopwatch, the
# "geschafft" reps input, the double-progression suggestion (done screen
# and next visit), saved plans, migration of an old single-exercise save,
# and "Beenden" returning to this screen.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(150)
        print("reps start card visible on workoutHome:", await pg.is_visible("#workoutRepsStartCard"))
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("reps ready screen open:", await pg.is_visible("#workoutRepsReady"))
        print("start button disabled with an empty plan:", await pg.get_attribute("#workoutRepsStartBtn", "disabled") is not None)
        print("empty-plan hint shown:", await pg.is_visible("#workoutRepsEmptyHint"))

        # ---- defaults for new exercises live in Feineinstellungen ----
        await pg.click("#workoutRepsAdvanced summary"); await pg.wait_for_timeout(100)
        print("default range preset is Muskelaufbau:", "active" in (await pg.get_attribute('[data-reps-range="muskelaufbau"]', "class") or ""))
        print("hint mentions the %1RM range:", "65" in await pg.inner_text("#workoutRepsRangeHint"))
        await pg.click('[data-reps-range="kraft"]'); await pg.wait_for_timeout(80)
        print("Kraft hint mentions Maximalkraft:", "Maximalkraft" in await pg.inner_text("#workoutRepsRangeHint"))
        await pg.click('[data-reps-range="custom"]'); await pg.wait_for_timeout(80)
        print("custom range sliders visible:", await pg.is_visible("#workoutRepsCustomRangeRow"))
        await pg.fill("#workoutRepsCustomMinSlider", "5"); await pg.dispatch_event("#workoutRepsCustomMinSlider", "input")
        await pg.fill("#workoutRepsCustomMaxSlider", "8"); await pg.dispatch_event("#workoutRepsCustomMaxSlider", "input")
        await pg.wait_for_timeout(80)
        print("custom range value updates:", "5–8" in await pg.inner_text("#workoutRepsCustomRangeValue"))
        await pg.click('[data-reps-range="muskelaufbau"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-reps-sets="2"]'); await pg.wait_for_timeout(60)
        await pg.fill("#workoutRepsRestSlider", "15"); await pg.dispatch_event("#workoutRepsRestSlider", "input")
        await pg.wait_for_timeout(60)
        print("set rest default shows 15 s:", "15" in await pg.inner_text("#workoutRepsRestValue"))
        print("prep countdown slider present (default 10 s):", "10" in await pg.inner_text("#workoutRepsPrepValue"))

        # ---- stack three exercises (one twice-capable, like Tabata) ----
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Plank") .ca-plus-btn'); await pg.wait_for_timeout(80)
        rows = pg.locator("#workoutRepsList .strength-item-row")
        print("three exercises in the plan:", await rows.count() == 3)
        print("count badge in add grid (1× im Plan):", "1× im Plan" in await pg.inner_text('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen")'))
        print("new items took the defaults (2×6–12):", "2×6–12" in await rows.nth(0).inner_text())
        print("start button enabled with items:", await pg.get_attribute("#workoutRepsStartBtn", "disabled") is None)

        # per-item settings: give Liegestütze the Kraft range + 3 sets
        await rows.nth(1).locator(".strength-range-select").select_option("kraft"); await pg.wait_for_timeout(80)
        await rows.nth(1).locator('[data-sfield="sets"][data-dir="1"]').click(); await pg.wait_for_timeout(80)
        print("item 2 now 3×1–6 independently:", "3×1–6" in await rows.nth(1).inner_text() and "2×6–12" in await rows.nth(0).inner_text())
        # Plank starts as a timed hold; switch it to reps, then a custom range
        print("Plank starts as 'Halten auf Zeit':", "halten" in await rows.nth(2).inner_text())
        await rows.nth(2).locator(".strength-mode-select").select_option("range"); await pg.wait_for_timeout(80)
        await rows.nth(2).locator(".strength-range-select").select_option("custom"); await pg.wait_for_timeout(80)
        print("custom range steppers appear for item 3:", await rows.nth(2).locator('[data-sfield="customMin"]').count() == 2)
        await rows.nth(2).locator('[data-sfield="customMax"][data-dir="-1"]').click(); await pg.wait_for_timeout(80)
        print("item 3 custom range edited (6–11):", "6–11" in await rows.nth(2).inner_text())
        # move item 3 up and remove it again
        await rows.nth(2).locator(".strength-move").click(); await pg.wait_for_timeout(80)
        print("reorder moved Plank to position 2:", "Plank" in await rows.nth(1).inner_text())
        await rows.nth(1).locator(".combo-block-remove").click(); await pg.wait_for_timeout(80)
        print("remove leaves 2 items:", await rows.count() == 2)

        # exercise-change rest
        await pg.fill("#workoutRepsExerciseRestSlider", "30"); await pg.dispatch_event("#workoutRepsExerciseRestSlider", "input")
        await pg.wait_for_timeout(60)
        print("exercise rest shows 30 s:", "30" in await pg.inner_text("#workoutRepsExerciseRestValue"))
        print("no progression hint yet:", await pg.is_hidden("#workoutRepsSuggestionHint"))

        # persistence across reload
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("plan persisted across reload:", await rows.count() == 2 and "3×1–6" in await rows.nth(1).inner_text())

        # ---- save the plan ----
        await pg.click("#workoutRepsSaveBtn"); await pg.wait_for_timeout(60)
        await pg.fill("#workoutRepsSaveNameInput", "Testplan")
        await pg.click("#workoutRepsSaveConfirmBtn"); await pg.wait_for_timeout(100)
        print("saved plan listed:", "Testplan" in await pg.inner_text("#workoutRepsSavedList"))

        # ---- run: prep countdown -> Kniebeugen 2 sets -> change rest -> Liegestütze 3 sets ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        print("prep countdown shown first:", await pg.is_visible("#workoutRestBox") and "BEREIT" in (await pg.inner_text("#workoutRestLabel")).upper())
        print("prep names first exercise:", "Kniebeugen" in await pg.inner_text("#workoutRestNext"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(200)
        print("set info shows Übung 1 von 2 · Satz 1 von 2:", "ÜBUNG 1 VON 2" in (await pg.inner_text("#workoutSetInfo")).upper())
        print("range shown (6–12):", "6–12" in await pg.inner_text("#workoutRepsBig"))
        print("live set timer visible:", await pg.is_visible("#workoutSetTimer"))
        print("reps input defaults to top of range (12):", await pg.inner_text("#workoutRepsInputValue") == "12")
        await pg.wait_for_timeout(1200)
        print("timer advancing:", (await pg.inner_text("#workoutSetTimer")) not in ("0:00", ""))
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        print("set rest shown (plain 'Pause'):", await pg.is_visible("#workoutRestBox") and (await pg.inner_text("#workoutRestLabel")).strip().upper() == "PAUSE")
        print("set rest counts the item's own 15 s:", (await pg.inner_text("#workoutRestCountdown")).strip() in ("15", "14"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(200)
        print("set 2 of 2:", "SATZ 2 VON 2" in (await pg.inner_text("#workoutSetInfo")).upper())
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        print("exercise-change rest shown:", "ÜBUNGSWECHSEL" in (await pg.inner_text("#workoutRestLabel")).upper())
        print("change rest previews next exercise:", "Liegestütze" in await pg.inner_text("#workoutRestNext") and "1–6" in await pg.inner_text("#workoutRestNext"))
        print("change rest counts 30 s:", (await pg.inner_text("#workoutRestCountdown")).strip() in ("30", "29"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(200)
        print("now Liegestütze, Übung 2 von 2, Satz 1 von 3:", await pg.inner_text("#workoutExerciseName") == "Liegestütze" and "ÜBUNG 2 VON 2 · SATZ 1 VON 3" in (await pg.inner_text("#workoutSetInfo")).upper())
        print("item 2 range (1–6), input defaults to 6:", "1–6" in await pg.inner_text("#workoutRepsBig") and await pg.inner_text("#workoutRepsInputValue") == "6")
        for k in range(3):
            await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
            if k < 2:
                await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        await pg.wait_for_timeout(200)
        print("done panel shown:", await pg.is_visible("#workoutDonePanel"))
        print("done summary names the Kraftplan:", "Kraftplan" in await pg.inner_text("#workoutDoneSummary"))
        sug = await pg.inner_text("#workoutDoneSuggestion")
        print("suggestion names both exercises:", "Kniebeugen" in sug and "Liegestütze" in sug)
        await pg.click("#workoutDoneBackBtn"); await pg.wait_for_timeout(200)

        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("progression hint on next visit:", await pg.is_visible("#workoutRepsSuggestionHint") and "Kniebeugen" in await pg.inner_text("#workoutRepsSuggestionHint"))

        # ---- Beenden mid-set returns here ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)
        print("Beenden returns to workoutRepsReady:", await pg.is_visible("#workoutRepsReady"))

        # ---- prep 0 = start straight into set 1 ----
        await pg.click("#workoutRepsAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.fill("#workoutRepsPrepSlider", "0"); await pg.dispatch_event("#workoutRepsPrepSlider", "input")
        await pg.wait_for_timeout(60)
        print("prep shows Aus at 0:", (await pg.inner_text("#workoutRepsPrepValue")).strip() == "Aus")
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        print("prep 0 skips countdown:", await pg.is_hidden("#workoutRestBox") and await pg.is_visible("#workoutSetDoneBtn"))
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)

        # ---- loading the saved plan starts it ----
        await pg.click('#workoutRepsSavedList .bundle-item:has-text("Testplan")'); await pg.wait_for_timeout(300)
        print("saved plan starts a run:", await pg.is_visible("#workoutRepsView"))
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)

        # ---- migration: an old single-exercise save becomes a 1-item plan ----
        await pg.evaluate("""() => localStorage.setItem('fwmc-workout-reps-builder-v1', JSON.stringify({exercise:'kniebeuge', rangeKey:'kraft', customMin:8, customMax:12, sets:4, restS:90}))""")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("old single-exercise save migrated to a 1-item plan (4×1–6):", await rows.count() == 1 and "4×1–6" in await rows.nth(0).inner_text())
        print("reps-input row hidden with no active session:", await pg.is_hidden("#workoutRepsInputRow"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
