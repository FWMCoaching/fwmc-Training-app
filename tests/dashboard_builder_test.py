import asyncio, json, urllib.parse
from playwright.async_api import async_playwright

DASH = "http://localhost:8845/dashboard.html"
APP = "http://localhost:8845/index.html?bereich=visual"

# Dashboard Baukasten for Movement, Cardio and Workout codes (Fabian,
# 2026-10-02 "E. Ja"). Mocks the Worker API, builds one code per area,
# then feeds each saved config to the real app to prove it opens.

PROGRAMS = [
    {"code": "mv-alt", "name": "Alt Movement", "active": True, "updatedAt": "2026-10-01T10:00:00Z",
     "config": {"type": "movement-plan", "name": "Alt Movement", "movements": ["armL-heben", "legR-strecken"], "bpm": 80, "durationMin": 4, "preview": 2, "mirror": False, "showLabel": True}},
    {"code": "zirkel-alt", "name": "Zirkel", "active": True, "updatedAt": "2026-10-01T10:00:00Z",
     "config": {"type": "workout-plan", "name": "Zirkel", "blocks": [{"kind": "circuit", "items": [{"exercise": "kniebeuge", "workS": 20}], "restS": 10, "sets": 2, "setRestS": 30}]}},
]


async def main():
    errors = []
    saved = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "favicon" not in m.text else None)

        async def api(route):
            req = route.request
            url = req.url
            if "/admin/programs" in url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": PROGRAMS}))
            elif "/admin/program" in url and req.method == "POST":
                saved.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": True}))
            elif "/admin/client-history" in url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"history": []}))
            elif "/admin/items" in url:  # kp20 server storage: empty, accepts writes
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"items": [], "ok": True}))
            else:
                await route.fulfill(status=404, body="{}")
        await pg.route("https://online-training.fwmc.workers.dev/**", api)
        await pg.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await pg.goto(DASH); await pg.wait_for_timeout(500)

        # 08.10.: the Baukasten got a 6th kind "Neuro-Aktivierung" (data-kind="neuro").
        kinds = await pg.eval_on_selector_all("#kindRow [data-kind]", "els => els.map(e => e.dataset.kind)")
        print("kind row with 6 areas:", kinds == ["visual", "movement", "cardio", "workout", "free", "neuro"], kinds)
        print("visual builder shown by default:", await pg.is_visible("#visualBuilder") and await pg.is_hidden("#movementBuilder"))

        # ---- Movement ----
        await pg.fill("#pCode", "mv-neu"); await pg.fill("#pName", "Bewegung neu")
        await pg.click('#kindRow [data-kind="movement"]')
        print("movement builder shown:", await pg.is_visible("#movementBuilder") and await pg.is_hidden("#visualBuilder"))
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(100)
        print("needs 2 movements:", "zwei Bewegungen" in await pg.inner_text("#pMsg"))
        for mv in ("armL-heben", "armR-heben", "legL-strecken"):
            await pg.check(f'[data-mv="{mv}"]')
        await pg.fill("#mvBpm", "90"); await pg.fill("#mvDuration", "6")
        await pg.select_option("#mvPreview", "4"); await pg.uncheck("#mvMirror")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        mv = saved[-1]["config"]
        print("movement-plan saved:", mv["type"] == "movement-plan" and mv["movements"] == ["armL-heben", "armR-heben", "legL-strecken"] and mv["bpm"] == 90 and mv["durationMin"] == 6 and mv["preview"] == 4 and mv["mirror"] is False, mv)

        # ---- Cardio ----
        await pg.click("#pNewBtn")
        print("new code resets to Visual:", await pg.is_visible("#visualBuilder"))
        await pg.fill("#pCode", "cardio-neu"); await pg.fill("#pName", "Cardio neu")
        await pg.click('#kindRow [data-kind="cardio"]')
        await pg.click('#cardioGrid >> text="Joggen"'); await pg.click('#cardioGrid >> text="Rad fahren"')
        cards = pg.locator("#cardioList .block-card")
        print("two activities listed:", await cards.count() == 2)
        await cards.nth(0).locator('[data-c="min"]').fill("8")
        await cards.nth(0).locator('[data-c="label"]').fill("Warm-up")
        await cards.nth(1).locator('input[data-c="interval"]').check()
        await cards.nth(1).locator('[data-c="onS"]').fill("40")
        await cards.nth(1).locator('[data-act="up"]').click()
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        cd = saved[-1]["config"]
        print("cardio-plan saved in new order:", cd["type"] == "cardio-plan" and [i["activity"] for i in cd["items"]] == ["rad", "joggen"], cd)
        print("cardio interval + label kept:", cd["items"][0]["interval"] == {"onS": 40, "offS": 30} and cd["items"][1]["durationS"] == 480 and cd["items"][1]["label"] == "Warm-up")

        # ---- Workout ----
        await pg.click("#pNewBtn")
        await pg.fill("#pCode", "wo-neu"); await pg.fill("#pName", "Workout neu")
        await pg.click('#kindRow [data-kind="workout"]')
        await pg.click('#workoutGrid >> text="Kniebeugen"'); await pg.click('#workoutGrid >> text="Hampelmann"')
        wcards = pg.locator("#workoutList .block-card")
        await wcards.nth(0).locator('[data-w="reps"]').fill("15")
        await wcards.nth(1).locator('[data-w-kind="tabata"]').click()
        await wcards.nth(1).locator('[data-w="rounds"]').fill("6")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        wo = saved[-1]["config"]
        print("workout-plan saved:", wo["type"] == "workout-plan" and wo["blocks"][0] == {"kind": "reps", "exercise": "kniebeuge", "sets": 3, "reps": 15, "restS": 30} and wo["blocks"][1]["kind"] == "tabata" and wo["blocks"][1]["rounds"] == 6, wo)

        # ---- editing an existing movement code fills the builder ----
        await pg.click('#progTable tr:has-text("mv-alt")'); await pg.wait_for_timeout(200)
        print("existing movement code opens in the builder:", await pg.is_visible("#movementBuilder") and await pg.is_checked('[data-mv="legR-strecken"]') and await pg.input_value("#mvBpm") == "80")
        print("builder tab enabled:", await pg.is_enabled("#tabBuilderBtn"))
        # JSON round trip
        await pg.click("#tabJsonBtn")
        print("JSON tab shows movement-plan:", '"movement-plan"' in await pg.input_value("#pConfig"))
        await pg.click("#tabBuilderBtn")
        print("back to builder keeps movement:", await pg.is_visible("#movementBuilder"))
        # a circuit plan is still JSON-only
        await pg.click('#progTable tr:has-text("zirkel-alt")'); await pg.wait_for_timeout(200)
        print("circuit plan falls back to JSON:", await pg.is_visible("#jsonView") and await pg.is_visible("#builderFallbackHint"))

        # ---- the saved configs really open in the app ----
        defs = {"mv-neu": mv, "cardio-neu": cd, "wo-neu": wo}
        app = await b.new_page(viewport={"width": 390, "height": 844})
        app.on("pageerror", lambda e: errors.append("app pageerror: " + str(e)))

        async def code_route(route):
            code = urllib.parse.unquote(route.request.url.split("code=")[-1].split("&")[0])
            d = defs.get(code)
            if d is None:
                await route.fulfill(status=404, body="not found")
            else:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(d))
        await app.route("**/program?code=*", code_route)
        await app.goto(APP); await app.wait_for_timeout(400)
        if await app.is_visible("#tipsCloseBtn"):
            await app.click("#tipsCloseBtn"); await app.wait_for_timeout(150)
        await app.fill("#programCodeInput", "mv-neu"); await app.click("#programGoBtn"); await app.wait_for_timeout(500)
        print("app opens movement intro:", await app.is_visible("#movementProgramIntro") and "3 Bewegungen" in await app.inner_text("#movementProgramMeta"))
        await app.goto(APP); await app.wait_for_timeout(300)
        await app.fill("#programCodeInput", "cardio-neu"); await app.click("#programGoBtn"); await app.wait_for_timeout(500)
        print("app opens cardio intro:", await app.is_visible("#cardioProgramIntro"))
        await app.goto(APP); await app.wait_for_timeout(300)
        await app.fill("#programCodeInput", "wo-neu"); await app.click("#programGoBtn"); await app.wait_for_timeout(500)
        print("app opens workout intro:", await app.is_visible("#workoutOverview") or await app.is_visible("#workoutProgramIntro"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
