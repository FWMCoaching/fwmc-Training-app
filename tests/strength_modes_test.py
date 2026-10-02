import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Kraftplan v3 (2026-10-02, Fabian): per exercise an "Art" (Wiederholungen /
# Pyramide / Halten auf Zeit), an own "Pause danach" deviating from the
# plan's standard pause, and a Supersatz with the next exercise (sets
# alternate A1 B1 A2 B2, own short switch pause, round pause after the pair).

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
        for n in ["Kniebeugen", "Liegestütze", "Ausfallschritte", "Plank"]:
            await add(n); await pg.wait_for_timeout(80)
        rows = pg.locator("#workoutRepsList .strength-item-row")
        print("4 items:", await rows.count() == 4)
        print("Plank defaults to a timed hold:", await rows.nth(3).locator(".strength-mode-select").input_value() == "time")
        print("last item has no pause/superset options:", await rows.nth(3).locator(".strength-options").count() == 0)

        # Item 1+2 as Supersatz with 5 s switch pause
        await rows.nth(0).locator(".strength-options summary").click(); await pg.wait_for_timeout(60)
        print("options show standard pause:", "Standard" in await rows.nth(0).locator(".strength-options summary").inner_text())
        await rows.nth(0).locator(".strength-superset").check(); await pg.wait_for_timeout(80)
        print("options stay open after a change:", await rows.nth(0).locator(".strength-options").get_attribute("open") is not None)
        await rows.nth(0).locator('[data-sfield="supersetGapS"][data-dir="1"]').click(); await pg.wait_for_timeout(60)
        print("summary names the Supersatz:", "Supersatz mit Übung 2" in await rows.nth(0).locator(".strength-options summary").inner_text())
        print("both rows marked as Supersatz:", "in-superset" in (await rows.nth(0).get_attribute("class")) and "in-superset" in (await rows.nth(1).get_attribute("class")))
        # Item 2 (end of the pair): own pause after = 0 s (straight on)
        await rows.nth(1).locator(".strength-options summary").click(); await pg.wait_for_timeout(60)
        await rows.nth(1).locator(".strength-rest-custom").click(); await pg.wait_for_timeout(60)
        for _ in range(14):
            await rows.nth(1).locator('[data-sfield="restAfterS"][data-dir="-1"]').click(); await pg.wait_for_timeout(20)
        print("own pause after shows 0 s:", "keine" in await rows.nth(1).locator(".strength-options summary").inner_text())
        # Item 3: pyramid 10 -> 6, 3 steps, and back
        await rows.nth(2).locator(".strength-mode-select").select_option("pyramid"); await pg.wait_for_timeout(60)
        for _ in range(2):
            await rows.nth(2).locator('[data-sfield="pyrFrom"][data-dir="-1"]').click(); await pg.wait_for_timeout(20)
        await rows.nth(2).locator(".strength-pyrback").check(); await pg.wait_for_timeout(60)
        print("pyramid summary 10–8–6–8–10:", "10–8–6–8–10" in await rows.nth(2).inner_text())
        # Plank: 1 set of 5 s
        for _ in range(5):
            await rows.nth(3).locator('[data-sfield="holdS"][data-dir="-1"]').click(); await pg.wait_for_timeout(20)
        for _ in range(3):
            await rows.nth(3).locator('[data-sfield="sets"][data-dir="-1"]').click(); await pg.wait_for_timeout(20)
        print("plank 1× 5 s halten:", "1× 5 s halten" in await rows.nth(3).inner_text())
        # Sets: Kniebeugen 2, Liegestütze 2 (defaults are 3; set both to 2)
        for i in (0, 1):
            await rows.nth(i).locator('[data-sfield="sets"][data-dir="-1"]').click(); await pg.wait_for_timeout(30)

        # Persisted across reload
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("settings persisted:", "in-superset" in (await rows.nth(0).get_attribute("class")) and "10–8–6–8–10" in await rows.nth(2).inner_text())

        # ---- run ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)  # prep
        async def info(): return (await pg.inner_text("#workoutExerciseName"), (await pg.inner_text("#workoutSetInfo")).upper())
        n, s = await info(); print("A1 Kniebeugen Satz 1 · Supersatz:", n == "Kniebeugen" and "SATZ 1 VON 2" in s and "SUPERSATZ" in s)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("switch pause labelled Supersatz:", "SUPERSATZ" in (await pg.inner_text("#workoutRestLabel")).upper() and (await pg.inner_text("#workoutRestCountdown")).strip() in ("5", "4"))
        print("switch pause previews Liegestütze:", "Liegestütze" in await pg.inner_text("#workoutRestNext"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        n, s = await info(); print("B1 Liegestütze Satz 1:", n == "Liegestütze" and "SATZ 1 VON 2" in s)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        print("round pause is a plain Pause:", (await pg.inner_text("#workoutRestLabel")).strip().upper() == "PAUSE")
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        n, s = await info(); print("A2 Kniebeugen Satz 2:", n == "Kniebeugen" and "SATZ 2 VON 2" in s)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        n, s = await info(); print("B2 Liegestütze Satz 2:", n == "Liegestütze" and "SATZ 2 VON 2" in s)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(150)
        n, s = await info()
        print("own 0 s pause after the pair: straight into the pyramid:", n == "Ausfallschritte" and await pg.is_hidden("#workoutRestBox"))
        print("pyramid set 1 of 5 targets 10:", "SATZ 1 VON 5" in s and "10 Wiederholungen" in await pg.inner_text("#workoutRepsBig") and await pg.inner_text("#workoutRepsInputValue") == "10")
        targets = []
        for k in range(5):
            targets.append((await pg.inner_text("#workoutRepsBig")).split()[0])
            await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(120)
            if k < 4:
                await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(120)
        print("pyramid targets 10,8,6,8,10:", targets == ["10", "8", "6", "8", "10"], targets)
        print("standard pause before Plank (Übungswechsel):", "ÜBUNGSWECHSEL" in (await pg.inner_text("#workoutRestLabel")).upper())
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        print("Plank shows 5 s halten, no reps input:", "5 s halten" in await pg.inner_text("#workoutRepsBig") and await pg.is_hidden("#workoutRepsInputRow"))
        print("button says Halten starten:", (await pg.inner_text("#workoutSetDoneBtn")).strip() == "Halten starten")
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(300)
        print("hold counting down, button now Fertig:", (await pg.inner_text("#workoutSetDoneBtn")).strip() == "Fertig" and "s" in await pg.inner_text("#workoutSetTimer"))
        await pg.wait_for_timeout(5300)
        print("hold completes itself -> done panel:", await pg.is_visible("#workoutDonePanel"))
        await pg.click("#workoutDoneBackBtn"); await pg.wait_for_timeout(150)

        # ---- Kombi round trip keeps Art / Supersatz / Pause danach ----
        await pg.click('#workoutHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        await pg.click('#comboAddGrid >> text="Kraft-/Wiederholungstraining"'); await pg.wait_for_timeout(200)
        for n in ["Kniebeugen", "Liegestütze", "Wandsitz"]:
            await add(n); await pg.wait_for_timeout(80)
        print("Wandsitz defaults to a timed hold:", await rows.nth(2).locator(".strength-mode-select").input_value() == "time")
        await rows.nth(0).locator(".strength-options summary").click(); await pg.wait_for_timeout(60)
        await rows.nth(0).locator(".strength-superset").check(); await pg.wait_for_timeout(60)
        await rows.nth(1).locator(".strength-mode-select").select_option("pyramid"); await pg.wait_for_timeout(60)
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(200)
        meta = await pg.locator("#comboBlockList .chapter-row >> nth=0 >> .info span").inner_text()
        print("Kombi block meta shows Supersatz, Pyramide, halten:", "Supersatz" in meta and "Pyramide" in meta and "halten" in meta, meta)
        await pg.click("#comboBlockList .chapter-row >> nth=0 >> .chapter-main"); await pg.wait_for_timeout(200)
        print("re-edit keeps superset/pyramid/hold:", "in-superset" in (await rows.nth(0).get_attribute("class"))
              and await rows.nth(1).locator(".strength-mode-select").input_value() == "pyramid"
              and await rows.nth(2).locator(".strength-mode-select").input_value() == "time")
        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
