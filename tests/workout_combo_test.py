import asyncio, json
from playwright.async_api import async_playwright
OUT = "screenshots/wc_"
URL = "http://localhost:8845/index.html"

WORKOUT_BUNDLE = {"type": "workout-bundle", "name": "Test-Kundin · Pläne", "programs": [
    {"label": "Woche 1", "createdAt": "2026-09-10", "description": "Start", "blocks": [
        {"kind": "reps", "exercise": "kniebeuge", "sets": 1, "reps": 5, "restS": 1}]},
]}
COMBO_PROGRAM = {"type": "combo-program", "name": "Gesamt-Session", "description": "Alle vier Bereiche.",
    "blocks": [
        {"domain": "breath", "pattern": "custom", "phases": {"in": 0.2, "hold1": 0, "out": 0.2, "hold2": 0}, "durationMin": 0.03},
        {"domain": "movement", "durationMin": 0.03, "bpm": 120},
        {"domain": "visual", "exercise": "vt-color", "duration": 2, "colors": ["orange", "rot", "lila"]},
        {"domain": "workout", "kind": "reps", "exercise": "kniebeuge", "sets": 1, "reps": 5, "restS": 1},
    ]}
COMBO_BUNDLE = {"type": "combo-bundle", "name": "Kombi-Test", "programs": [
    {"label": "Mini", "createdAt": "2026-09-20", "description": "Kurz", "blocks": [
        {"domain": "visual", "exercise": "stroop-classic", "duration": 2}]},
]}

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        async def api(route):
            code = route.request.url.split("code=")[-1]
            data = {"workoutbundle": WORKOUT_BUNDLE, "comboprog": COMBO_PROGRAM, "combobundle": COMBO_BUNDLE}.get(code)
            if data:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
            else:
                await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
        await ctx.route("https://online-training.fwmc.workers.dev/**", api)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- Workout home ----
        await pg.click('.section-tab[data-section="workout"]'); await pg.wait_for_timeout(200)
        print("workoutHome visible:", await pg.is_visible("#workoutHome"))
        await pg.screenshot(path=OUT + "01_workout_home.png", full_page=True)

        # ---- Standalone Tabata (self-built circuit) ----
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.locator("#workoutCircuitAddGrid .combo-add-btn").nth(4).click(); await pg.wait_for_timeout(80)  # Hampelmann
        await pg.locator("#workoutCircuitAddGrid .combo-add-btn").nth(0).click(); await pg.wait_for_timeout(80)  # Kniebeugen
        await pg.click('[data-wo-rest="5"]')
        await pg.evaluate("""() => {
            const raw = localStorage.getItem('fwmc-workout-circuit-v1');
            const prefs = JSON.parse(raw);
            prefs.items = prefs.items.map(it => ({...it, workS: 1}));
            localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify(prefs));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('.section-tab[data-section="workout"]'); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(300)
        print("tabata player visible:", await pg.is_visible("#workoutPlayer"))
        print("phase label (prep expected):", await pg.inner_text("#tabataPhaseLabel"))
        await pg.screenshot(path=OUT + "02_tabata_prep.png")
        await pg.wait_for_function("() => document.getElementById('tabataPhaseLabel').textContent === 'Los!'", timeout=7000)
        await pg.screenshot(path=OUT + "03_tabata_work.png")
        await pg.wait_for_function("() => document.getElementById('tabataPhaseLabel').textContent === 'Pause'", timeout=4000)
        await pg.screenshot(path=OUT + "04_tabata_rest.png")
        await pg.wait_for_function("() => !document.getElementById('workoutDonePanel').hidden", timeout=8000)
        print("tabata done summary:", await pg.inner_text("#workoutDoneSummary"))
        await pg.click('#workoutRating [data-rate="4"]')
        await pg.click("#workoutDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at workoutHome:", await pg.is_visible("#workoutHome"))

        # ---- Coach-code workout plan (bundle) ----
        await pg.fill("#workoutProgramCodeInput", "workoutbundle"); await pg.click("#workoutProgramGoBtn"); await pg.wait_for_timeout(400)
        print("workout bundle overview:", await pg.is_visible("#workoutBundleOverview"))
        await pg.click(".bundle-item >> nth=0"); await pg.wait_for_timeout(200)
        print("plan intro:", await pg.is_visible("#workoutProgramIntro"), await pg.inner_text("#workoutProgramTitle"))
        await pg.click("#workoutProgramStartBtn"); await pg.wait_for_timeout(200)
        print("reps view visible:", await pg.is_visible("#workoutRepsView"), "overview visible:", await pg.is_visible("#workoutOverview"))
        print("set info:", await pg.inner_text("#workoutSetInfo"))
        await pg.screenshot(path=OUT + "05_reps_plan.png")
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        print("finished single-set block -> plan done panel:", await pg.is_visible("#workoutProgramDonePanel"))
        print("plan done summary:", await pg.inner_text("#workoutProgramDoneSummary"))
        print("done-back label (should offer bundle return):", await pg.inner_text("#workoutProgramDoneBackBtn"))
        await pg.click("#workoutProgramDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at bundle overview (expected, since opened from one):", await pg.is_visible("#workoutBundleOverview"))
        await pg.click("#workoutBundleBackToHome"); await pg.wait_for_timeout(200)
        print("now at workoutHome:", await pg.is_visible("#workoutHome"))
        print("history list html:", await pg.eval_on_selector("#workoutHistoryList", "el => el.innerHTML"))

        # ---- Combo builder: add + remove + save ----
        await pg.click('#workoutHome [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        print("combo screen visible:", await pg.is_visible("#comboScreen"))
        add_btns = pg.locator("#comboScreen .combo-add-btn")
        print("preset add buttons:", await add_btns.count())
        await add_btns.nth(0).click()  # breath box
        await add_btns.nth(4).click()  # movement
        await add_btns.nth(6).click()  # visual vt
        await add_btns.nth(9).click()  # workout reps
        await pg.wait_for_timeout(100)
        print("block count text:", await pg.inner_text("#comboBlockCount"))
        rows = await pg.eval_on_selector_all("#comboBlockList .chapter-main strong", "els => els.map(e => e.textContent)")
        print("blocks added:", rows)
        # remove last, re-add
        await pg.click("#comboScreen .combo-block-remove >> nth=3"); await pg.wait_for_timeout(100)
        print("after remove, count:", await pg.inner_text("#comboBlockCount"))
        await add_btns.nth(9).click(); await pg.wait_for_timeout(100)
        await pg.click("#comboSaveBtn"); await pg.wait_for_timeout(100)
        await pg.fill("#comboNameInput", "Testkombi")
        await pg.screenshot(path=OUT + "06_combo_builder.png", full_page=True)
        await pg.click("#comboSaveConfirmBtn"); await pg.wait_for_timeout(150)
        print("saved shows in list:", await pg.is_visible("#comboSavedGroup"), "draft cleared:", await pg.inner_text("#comboBlockCount") == "")
        await pg.screenshot(path=OUT + "07_combo_saved.png", full_page=True)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
