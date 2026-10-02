import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Kraftplan v4 (2026-10-02, Fabian): "Maximal" as an Art, and per exercise,
# folded under "Mehr Optionen": Seite (beidseitig / links-rechts / nur eine
# Seite), Tempo, Aufwärmsätze (feste Wdh. oder frei) and Dropsätze.

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
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        add = lambda name: pg.click(f'#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("{name}") .ca-plus-btn')
        for n in ["Ausfallschritte", "Kniebeugen", "Plank"]:
            await add(n); await pg.wait_for_timeout(80)
        rows = pg.locator("#workoutRepsList .strength-item-row")
        r0 = rows.nth(0)
        print("Mehr Optionen folded by default:", await r0.locator(".strength-more").get_attribute("open") is None)
        print("summary names the options:", "Seite" in await r0.locator(".strength-more summary").inner_text())
        print("last item also has Mehr Optionen:", await rows.nth(2).locator(".strength-more").count() == 1)
        print("hold item has no tempo / drop fields:", await rows.nth(2).locator(".strength-tempo").count() == 0 and await rows.nth(2).locator('[data-sfield="dropSets"]').count() == 0)

        await r0.locator(".strength-more summary").click(); await pg.wait_for_timeout(60)
        await r0.locator(".strength-side-select").select_option("lr"); await pg.wait_for_timeout(80)
        print("stays open after change, side gap shown:", await r0.locator(".strength-more").get_attribute("open") is not None and await r0.locator('[data-sfield="sideGapS"]').count() == 2)
        await r0.locator(".strength-tempo").fill("3-1-1-0"); await r0.locator(".strength-tempo").press("Tab"); await pg.wait_for_timeout(80)
        await r0.locator('[data-sfield="warmupSets"][data-dir="1"]').click(); await pg.wait_for_timeout(60)
        print("warm-up reps default frei:", (await r0.locator('[data-svalue="warmupReps"]').inner_text()).strip() == "frei")
        await r0.locator('[data-sfield="dropSets"][data-dir="1"]').click(); await pg.wait_for_timeout(60)
        for _ in range(2):
            await r0.locator('[data-sfield="sets"][data-dir="-1"]').click(); await pg.wait_for_timeout(30)
        summ = await r0.locator(".strength-more summary").inner_text()
        print("summary lists extras:", all(t in summ for t in ["links, dann rechts", "Tempo 3-1-1-0", "1 Aufwärmsatz", "1 Dropsatz"]), summ)
        print("item line shows je Seite:", "je Seite" in await r0.locator(".info").inner_text())
        # Kniebeugen: Maximal, 2 sets
        r1 = rows.nth(1)
        await r1.locator(".strength-mode-select").select_option("amrap"); await pg.wait_for_timeout(60)
        await r1.locator('[data-sfield="sets"][data-dir="-1"]').click(); await pg.wait_for_timeout(60)
        print("amrap line 2× maximal:", "2× maximal" in await r1.inner_text())
        # Plank removed to keep the run short
        await rows.nth(2).locator(".combo-block-remove").click(); await pg.wait_for_timeout(80)

        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("persisted:", "links, dann rechts" in await rows.nth(0).locator(".strength-more summary").inner_text() and await rows.nth(1).locator(".strength-mode-select").input_value() == "amrap")

        # ---- run ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        async def st():
            return ((await pg.inner_text("#workoutSetInfo")).upper(), await pg.inner_text("#workoutRepsBig"), await pg.inner_text("#workoutNote"))
        info, big, note = await st()
        print("warm-up left, free reps:", "AUFWÄRMSATZ 1 VON 1" in info and "LINKS" in info and "nach Gefühl" in big, info, big)
        print("no reps logging in warm-up:", await pg.is_hidden("#workoutRepsInputRow"))
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("side switch pause:", "SEITENWECHSEL" in (await pg.inner_text("#workoutRestLabel")).upper() and "rechts" in await pg.inner_text("#workoutRestNext"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        info, big, note = await st()
        print("warm-up right:", "AUFWÄRMSATZ" in info and "RECHTS" in info)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("pause after warm-up previews working set:", "links" in await pg.inner_text("#workoutRestNext"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        info, big, note = await st()
        print("work set left with tempo:", "SATZ 1 VON 1" in info and "LINKS" in info and "Tempo 3-1-1-0" in note, info, note)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        info, big, note = await st()
        print("drop set follows straight away:", "DROPSATZ" in info and "LINKS" in info and "reduzieren" in big and await pg.is_hidden("#workoutRestBox"))
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("side switch after drop:", "SEITENWECHSEL" in (await pg.inner_text("#workoutRestLabel")).upper())
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        info, *_ = await st(); print("work set right:", "SATZ 1 VON 1" in info and "RECHTS" in info)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        info, *_ = await st(); print("drop right:", "DROPSATZ" in info and "RECHTS" in info)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("exercise change pause:", "Kniebeugen" in await pg.inner_text("#workoutRestNext"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        info, big, note = await st()
        print("amrap: So viele wie möglich, input 10:", "So viele wie möglich" in big and (await pg.inner_text("#workoutRepsInputValue")).strip() == "10")
        await pg.click("#workoutRepsInputPlus"); await pg.click("#workoutRepsInputPlus"); await pg.wait_for_timeout(50)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        print("amrap set 2 starts at last result 12:", (await pg.inner_text("#workoutRepsInputValue")).strip() == "12")
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(300)
        print("done panel shown:", await pg.is_visible("#workoutDonePanel"))

        # ---- Kombi round trip keeps the extras ----
        data = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-workout-reps-builder-v1')).items[0]")
        print("stored item has extras:", data["side"] == "lr" and data["tempo"] == "3-1-1-0" and data["warmupSets"] == 1 and data["dropSets"] == 1)
        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
