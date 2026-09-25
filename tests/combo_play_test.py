import asyncio, json
from playwright.async_api import async_playwright
OUT = "screenshots/wc2_"
URL = "http://localhost:8845/index.html"

COMBO_PROGRAM = {"type": "combo-program", "name": "Gesamt-Session", "description": "Alle vier Bereiche.",
    "blocks": [
        {"domain": "breath", "pattern": "custom", "phases": {"in": 0.2, "hold1": 0, "out": 0.2, "hold2": 0}, "durationMin": 0.03},
        {"domain": "movement", "durationMin": 0.03, "bpm": 120},
        {"domain": "visual", "exercise": "vt-color", "duration": 2, "colors": ["orange", "rot", "lila"]},
        {"domain": "workout", "kind": "reps", "exercise": "kniebeuge", "sets": 1, "reps": 5, "restS": 1},
        {"domain": "wimhof", "breaths": 2, "rounds": 1, "breathPaceS": 0.2, "recoveryHoldS": 1},
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
            data = {"comboprog": COMBO_PROGRAM, "combobundle": COMBO_BUNDLE}.get(code)
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

        # ---- Full cross-domain chain via code: breath -> movement -> visual -> workout -> wimhof ----
        await pg.fill("#programCodeInput", "comboprog"); await pg.click("#programGoBtn"); await pg.wait_for_timeout(500)
        print("breath block running:", await pg.is_visible("#breathPlayer"))
        await pg.screenshot(path=OUT + "01_combo_breath.png")

        await pg.wait_for_function("() => !document.getElementById('movementPlayer').hidden", timeout=8000)
        print("advanced to movement block")
        await pg.screenshot(path=OUT + "02_combo_movement.png")

        await pg.wait_for_function("() => !document.getElementById('player').hidden", timeout=8000)
        print("advanced to visual block")
        await pg.screenshot(path=OUT + "03_combo_visual.png")

        await pg.wait_for_function("() => !document.getElementById('workoutPlayer').hidden", timeout=8000)
        print("advanced to workout block, reps view:", await pg.is_visible("#workoutRepsView"))
        await pg.screenshot(path=OUT + "04_combo_workout.png")
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(300)

        # wimhof block should require the safety screen, not auto-play
        await pg.wait_for_function("() => !document.getElementById('wimhofReady').hidden", timeout=6000)
        print("wimhof safety gate shown mid-combo:", await pg.is_visible("#wimhofReady"))
        print("start disabled before ack:", await pg.get_attribute("#wimhofStartBtn", "disabled") is not None)
        await pg.screenshot(path=OUT + "05_combo_wimhof_gate.png")
        await pg.check("#wimhofAckCheck")
        await pg.click("#wimhofStartBtn"); await pg.wait_for_timeout(300)
        print("wimhof running mid-combo:", await pg.is_visible("#wimhofPlayer"))
        await pg.wait_for_function("() => !document.getElementById('wimhofHoldDoneBtn').hidden", timeout=4000)
        await pg.click("#wimhofHoldDoneBtn"); await pg.wait_for_timeout(200)

        await pg.wait_for_function("() => !document.getElementById('comboDonePanel').hidden", timeout=6000)
        print("combo done summary:", await pg.inner_text("#comboDoneSummary"))
        await pg.screenshot(path=OUT + "06_combo_done.png")
        await pg.click('#comboRating [data-rate="5"]')
        print("done-back label:", await pg.inner_text("#comboDoneBackBtn"))
        await pg.click("#comboDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at home (visual, since code entered there):", await pg.is_visible("#home"))
        print("history has combo entry:", "Gesamt-Session" in (await pg.inner_text("#historyList")))

        # ---- Abort mid-combo ----
        await pg.fill("#programCodeInput", "comboprog"); await pg.click("#programGoBtn"); await pg.wait_for_timeout(500)
        await pg.click("#backBtn"); await pg.wait_for_timeout(200)  # visual's Beenden isn't first block though; use breath's
        # first block is breath; its Beenden id is breathBackBtn
        print("aborted -> home:", await pg.is_visible("#home"), "any player visible:", await pg.is_visible("#breathPlayer") or await pg.is_visible("#player"))

        # ---- Combo via bundle code ----
        await pg.fill("#programCodeInput", "combobundle"); await pg.click("#programGoBtn"); await pg.wait_for_timeout(400)
        print("combo bundle overview:", await pg.is_visible("#comboBundleOverview"))
        await pg.click(".bundle-item >> nth=0"); await pg.wait_for_timeout(300)
        print("single-block combo running (visual stroop):", await pg.is_visible("#player"))
        await pg.wait_for_function("() => !document.getElementById('comboDonePanel').hidden", timeout=6000)
        print("bundle combo done, back label:", await pg.inner_text("#comboDoneBackBtn"))
        await pg.click("#comboDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at combo bundle overview:", await pg.is_visible("#comboBundleOverview"))

        # ---- Start a saved local combo from the builder ----
        await pg.click("#comboBundleBackToHome"); await pg.wait_for_timeout(150)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        saved_count = await pg.locator("#comboSavedList .bundle-item").count()
        print("saved local combos available:", saved_count)
        if saved_count:
            await pg.click("#comboSavedList .bundle-item >> nth=0"); await pg.wait_for_timeout(400)
            print("local saved combo started, some player visible:",
                  await pg.is_visible("#breathPlayer") or await pg.is_visible("#movementPlayer") or await pg.is_visible("#player") or await pg.is_visible("#workoutPlayer"))
            await pg.click("body")  # no-op, just settle

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
