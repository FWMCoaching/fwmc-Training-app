import asyncio, json
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Pause während des Trainings (Fabian, 2026-10-02): "Pause" freezes Tabata,
# Kraftplan, Cardio and the Kombi pause screen; the sheet edits the current
# pause (or the one after the current exercise), "Alle Pausen anzeigen"
# edits every pause still ahead, "Weiter" carries on where it stopped.

async def new_page(b, errors, seed=""):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');" + seed)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await pg.goto(URL); await pg.wait_for_timeout(300)
    return pg

async def sheet_values(pg):
    return [t.strip() for t in await pg.locator("#trainPauseOverlay [data-tpv]").all_inner_texts()]

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        quiet = "localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false}));"

        # ---------- Tabata ----------
        pg = await new_page(b, errors, quiet + "localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify({items:[{exercise:'kniebeuge',workS:20},{exercise:'liegestuetz',workS:20}],restS:10,sets:2,setRestS:30,defaultWorkS:20,prepS:6,cooldownS:0}))")
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#workoutPauseBtn"); await pg.wait_for_timeout(150)
        print("tabata: sheet open:", await pg.is_visible("#trainPauseOverlay"))
        cur = await pg.inner_text("#trainPauseCurrent")
        print("tabata: current = running start countdown:", "Diese Pause" in cur and "Bereit machen" in cur)
        c0 = await pg.inner_text("#tabataCountdown"); await pg.wait_for_timeout(1300)
        print("tabata: frozen while paused:", c0 == await pg.inner_text("#tabataCountdown"))
        await pg.click('#trainPauseCurrent [data-dir="1"]'); await pg.wait_for_timeout(80)
        print("tabata: current pause +5 snaps to 10 s:", (await sheet_values(pg))[0] == "10 s")
        print("tabata: list hidden until asked:", await pg.is_hidden("#trainPauseList"))
        await pg.click("#trainPauseOverviewBtn"); await pg.wait_for_timeout(80)
        vals = await sheet_values(pg)
        print("tabata: 3 later pauses (rest, setrest, rest):", vals[1:] == ["10 s", "30 s", "10 s"], vals)
        await pg.locator('#trainPauseList [data-dir="1"]').nth(1).click(); await pg.wait_for_timeout(80)
        print("tabata: Satzpause raised to 35 s:", (await sheet_values(pg))[2] == "35 s")
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(200)
        print("tabata: resumed at the edited countdown:", int(await pg.inner_text("#tabataCountdown")) in (9, 10))
        await pg.wait_for_timeout(1300)
        print("tabata: countdown runs again:", int(await pg.inner_text("#tabataCountdown")) <= 9)
        await pg.click("#workoutPauseBtn"); await pg.wait_for_timeout(100)
        await pg.click("#trainPauseOverviewBtn"); await pg.wait_for_timeout(80)
        print("tabata: edit kept on reopen:", "35 s" in await sheet_values(pg))
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)
        print("tabata: Beenden while paused closes it:", await pg.is_hidden("#trainPauseOverlay") and await pg.is_visible("#workoutTabataReady"))
        await pg.context.close()

        # ---------- Kraftplan ----------
        pg = await new_page(b, errors, quiet)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(60)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(60)
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#workoutPauseBtn"); await pg.wait_for_timeout(100)
        print("kraft: current = start countdown:", "Bereit machen" in await pg.inner_text("#trainPauseCurrent"))
        c0 = await pg.inner_text("#workoutRestCountdown"); await pg.wait_for_timeout(1300)
        print("kraft: frozen while paused:", c0 == await pg.inner_text("#workoutRestCountdown"))
        await pg.click("#trainPauseOverviewBtn"); await pg.wait_for_timeout(80)
        print("kraft: later pauses listed:", await pg.locator("#trainPauseList .train-pause-row").count() >= 2)
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(100)
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
        await pg.click("#workoutPauseBtn"); await pg.wait_for_timeout(100)
        cur = await pg.inner_text("#trainPauseCurrent")
        print("kraft: during a set = pause after this set:", "Pause nach diesem Satz" in cur)
        before = (await sheet_values(pg))[0]
        await pg.click('#trainPauseCurrent [data-dir="1"]'); await pg.wait_for_timeout(80)
        after = (await sheet_values(pg))[0]
        print("kraft: +5 on that pause:", int(after.split()[0]) - int(before.split()[0]) == 5 if "min" not in after else True, before, after)
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(100)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        shown = int(await pg.inner_text("#workoutRestCountdown"))
        expect = int(after.split()[0]) if "min" not in after else None
        print("kraft: next rest uses the edited value:", expect is None or shown == expect, shown, after)
        await pg.click("#workoutPauseBtn"); await pg.wait_for_timeout(100)
        await pg.click('#trainPauseCurrent [data-dir="-1"]'); await pg.wait_for_timeout(80)
        v = (await sheet_values(pg))[0]
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(150)
        print("kraft: running rest shortened live:", abs(int(await pg.inner_text("#workoutRestCountdown")) - int(v.split()[0])) <= 1 if "min" not in v else True, v)
        await pg.context.close()

        # ---------- Cardio ----------
        pg = await new_page(b, errors)
        await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
        for n in ["Joggen", "Walking", "Rad fahren"]:
            await pg.click(f'#cardioAddGrid >> text="{n}"'); await pg.wait_for_timeout(60)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioPauseBtn"); await pg.wait_for_timeout(100)
        cur = await pg.inner_text("#trainPauseCurrent")
        print("cardio: pause after this activity:", "Pause nach dieser Aktivität" in cur and "Joggen" in cur)
        c0 = await pg.inner_text("#cardioCountdown"); await pg.wait_for_timeout(1300)
        print("cardio: frozen while paused:", c0 == await pg.inner_text("#cardioCountdown"))
        v0 = (await sheet_values(pg))[0]
        await pg.click('#trainPauseCurrent [data-dir="1"]'); await pg.wait_for_timeout(80)
        print("cardio: +5:", int((await sheet_values(pg))[0].split()[0]) == int(v0.split()[0]) + 5)
        await pg.click("#trainPauseOverviewBtn"); await pg.wait_for_timeout(80)
        print("cardio: 1 later pause (Walking -> Rad):", await pg.locator("#trainPauseList .train-pause-row").count() == 1 and "Walking" in await pg.inner_text("#trainPauseList"))
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(1300)
        print("cardio: runs again:", c0 != await pg.inner_text("#cardioCountdown"))
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(200)
        print("cardio: skip lands on next activity:", "Walking" in await pg.inner_text("#cardioActivityTitle"))
        await pg.context.close()

        # ---------- Kombi pause screen ----------
        pg = await new_page(b, errors)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        for _ in range(3):
            await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
            await pg.fill("#rememberComboDurationSlider", "15")
            await pg.dispatch_event("#rememberComboDurationSlider", "input")
            await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(16500)
        print("kombi: on pause screen:", await pg.is_visible("#comboTransition"))
        await pg.click("#comboTransitionPauseBtn"); await pg.wait_for_timeout(100)
        print("kombi: sheet open:", await pg.is_visible("#trainPauseOverlay"))
        c0 = await pg.inner_text("#comboTransitionCountdown"); await pg.wait_for_timeout(1300)
        print("kombi: frozen while paused:", c0 == await pg.inner_text("#comboTransitionCountdown"))
        await pg.click("#trainPauseOverviewBtn"); await pg.wait_for_timeout(80)
        print("kombi: next Kombi pause listed:", await pg.locator("#trainPauseList .train-pause-row").count() == 1 and "Kombi" in await pg.inner_text("#trainPauseList"))
        await pg.click('#trainPauseCurrent [data-dir="-1"]'); await pg.wait_for_timeout(50)
        for _ in range(6):
            await pg.click('#trainPauseCurrent [data-dir="-1"]'); await pg.wait_for_timeout(30)
        print("kombi: current pause down to 0:", (await sheet_values(pg))[0] == "0 s")
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(400)
        print("kombi: 0 s continues straight to the next block:", await pg.is_hidden("#comboTransition") and await pg.is_visible("#rememberPlayer"))
        await pg.context.close()

        print("no page errors:", errors == [], errors[:3])
        await b.close()

asyncio.run(main())
