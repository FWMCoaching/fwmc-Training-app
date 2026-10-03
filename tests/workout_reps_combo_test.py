import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Kombi-Baukasten integration for the new Kraft-/Wiederholungstraining
# builder (workout_reps_builder_test.py covers the standalone screen
# itself). Client's exact ask: mix several Tabata blocks, several
# Wiederholungstraining blocks, and several Cardio blocks, in any order,
# interspersed with anything else - the combo draft is just a plain
# ordered list, so this was already possible for Tabata/circuit and
# Cardio; this test confirms the new reps builder now joins them the same
# way (both add-multiple-times and edit-in-place).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        print("comboScreen open:", await pg.is_visible("#comboScreen"))
        print("'Kraft-/Wiederholungstraining' entry present in add grid:",
              await pg.locator('#comboAddGrid >> text="Kraft-/Wiederholungstraining"').count() > 0)

        # ---- block 1: Zirkel (Tabata), short so it finishes fast below ----
        await pg.click('#comboAddGrid >> text="Eigener Zirkel"'); await pg.wait_for_timeout(200)
        await pg.click('#workoutCircuitAddGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(80)
        # shorten the item down to the 5s floor (two "-" clicks from the 15s
        # default) so the transition to block 2 below happens quickly
        await pg.click('#workoutCircuitList .circuit-step[data-dir="-1"]'); await pg.wait_for_timeout(60)
        await pg.click('#workoutCircuitList .circuit-step[data-dir="-1"]'); await pg.wait_for_timeout(60)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)
        print("block 1 (Zirkel) committed, back at comboScreen:", await pg.is_visible("#comboScreen"))

        # ---- block 2: a whole Kraftplan as ONE Baustein - Kniebeugen (Kraft,
        # 2 sets) + Liegestütze stacked in the same block ----
        await pg.click('#comboAddGrid >> text="Kraft-/Wiederholungstraining"'); await pg.wait_for_timeout(200)
        print("capture screen retitled for combo:", "Baustein" in await pg.inner_text("#workoutRepsReadyTitle"))
        print("capture starts with an empty plan:", await pg.locator("#workoutRepsList .strength-item-row").count() == 0)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(80)
        r0 = pg.locator("#workoutRepsList .strength-item-row").nth(0)
        await r0.locator(".strength-range-select").select_option("kraft"); await pg.wait_for_timeout(60)
        r0 = pg.locator("#workoutRepsList .strength-item-row").nth(0)
        await r0.locator('[data-sfield="sets"][data-dir="-1"]').click(); await pg.wait_for_timeout(60)
        print("two exercises stacked in one Baustein:", await pg.locator("#workoutRepsList .strength-item-row").count() == 2)
        print("start button reads 'Baustein übernehmen':", (await pg.inner_text("#workoutRepsStartBtn")).strip() == "Baustein übernehmen")
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(200)
        print("block 2 (Kraftplan) committed, back at comboScreen:", await pg.is_visible("#comboScreen"))
        print("title/hint reset after commit:", await pg.inner_text("#workoutRepsReadyTitle") == "Kraft-/Wiederholungstraining")
        print("standalone plan untouched by the capture (still empty):",
              await pg.evaluate("() => (JSON.parse(localStorage.getItem('fwmc-workout-reps-builder-v1')||'{}').items||[]).length") == 0)

        # ---- block 3: a second, different Zirkel ----
        await pg.click('#comboAddGrid >> text="Eigener Zirkel"'); await pg.wait_for_timeout(200)
        print("re-opening 'Eigener Zirkel' starts a fresh (empty) circuit, not block 1's leftover:",
              await pg.locator("#workoutCircuitList .circuit-item-row").count() == 0)
        await pg.click('#workoutCircuitAddGrid .custom-exercise-add-row:has-text("Burpees") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)

        # ---- block 4: Cardio ----
        await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid .combo-add-btn >> text="Joggen"'); await pg.wait_for_timeout(80)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(200)
        print("block 4 (Cardio) committed, back at comboScreen:", await pg.is_visible("#comboScreen"))

        # ---- block 5: a second Kraft-/Wiederholungstraining, Muskelaufbau, Liegestütze ----
        await pg.click('#comboAddGrid >> text="Kraft-/Wiederholungstraining"'); await pg.wait_for_timeout(200)
        print("re-opening reps builder starts fresh (nothing carried over from block 2):",
              await pg.locator("#workoutRepsList .strength-item-row").count() == 0)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(200)

        # ---- block 6: a second Cardio ----
        await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid .combo-add-btn >> text="Rad fahren"'); await pg.wait_for_timeout(80)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(200)

        count = await pg.locator("#comboBlockList .chapter-row").count()
        print("all 6 interspersed blocks present, in order (Zirkel/Kraft/Zirkel/Cardio/Kraft/Cardio):", count == 6)
        labels = await pg.locator("#comboBlockList .chapter-main .ca-title, #comboBlockList .chapter-main strong").all_inner_texts()
        print("block order:", labels)

        # ---- edit block 2 (index 1) in place - should reopen prefilled ----
        await pg.click("#comboBlockList .chapter-row >> nth=1 >> .chapter-main"); await pg.wait_for_timeout(200)
        print("editing block 2 reopens the reps builder:", await pg.is_visible("#workoutRepsReady"))
        rows = pg.locator("#workoutRepsList .strength-item-row")
        print("both exercises reopen prefilled on re-edit:", await rows.count() == 2 and "Kniebeugen" in await rows.nth(0).inner_text() and "Liegestütze" in await rows.nth(1).inner_text())
        print("Kraft range maps back to its preset (1×1–6... shown as 2×1–6):", "2×1–6" in await rows.nth(0).inner_text()
              and await rows.nth(0).locator(".strength-range-select").input_value() == "kraft")
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Plank") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await rows.nth(0).locator('[data-sfield="sets"][data-dir="1"]').click(); await pg.wait_for_timeout(60)
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(200)
        meta = await pg.locator("#comboBlockList .chapter-row >> nth=1 >> .info span").inner_text()
        print("edited block persisted (3 exercises, Kniebeugen now 3×1–6):", "3 Übungen" in await pg.locator("#comboBlockList .chapter-row >> nth=1 >> .info strong").inner_text() and "Kniebeugen 3×1–6" in meta)

        # ---- run the combo: block 1 (Zirkel) -> transition -> block 2
        # (Kraft/Wdh., now range-mode) plays correctly inside a combo ----
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
        print("workout player visible (block 1, Zirkel):", await pg.is_visible("#workoutPlayer"))
        await pg.wait_for_selector("#comboTransition:not([hidden])", timeout=15000)
        await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(300)
        print("reps view visible (block 2, Kraft/Wdh.):", await pg.is_visible("#workoutRepsView"))
        print("Kraftplan prep countdown shown inside the combo:", await pg.is_visible("#workoutRestBox"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(200)
        print("set info shows Übung 1 von 3:", "ÜBUNG 1 VON 3" in (await pg.inner_text("#workoutSetInfo")).upper())
        print("range shown correctly inside the combo run (1–6 Wiederholungen):", "1–6" in await pg.inner_text("#workoutRepsBig"))
        print("live set timer running inside the combo too:", await pg.is_visible("#workoutSetTimer"))
        print("reps-input defaults to top of range (6):", await pg.inner_text("#workoutRepsInputValue") == "6")

        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)
        print("aborting mid-combo (during the reps block) lands back at home:", await pg.is_visible("#home"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
