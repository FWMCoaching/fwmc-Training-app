import asyncio, json, urllib.parse
from playwright.async_api import async_playwright

DASH = "http://localhost:8845/dashboard.html"
APP = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# Persönliche Nachricht / Hausaufgabe im Code (Fabian, 2026-10-03):
# dashboard writes config.message for any code type, the app shows it once
# per text version when the code opens, and keeps it in the code history.

PROGRAMS = [
    {"code": "bundle-msg", "name": "Übersicht", "active": True, "updatedAt": "2026-10-01T10:00:00Z",
     "config": {"type": "bundle", "name": "Übersicht", "message": "Alte Nachricht",
                "programs": [{"label": "A", "blocks": [{"exercise": "vt-color", "duration": 30}]}]}},
]
DEFS = {
    "msg-1": {"name": "Programm mit Nachricht", "message": "Diese Woche 3x vor dem Schlafen.",
              "blocks": [{"exercise": "vt-color", "duration": 30}]},
    "msg-none": {"name": "Ohne Nachricht", "blocks": [{"exercise": "vt-color", "duration": 30}]},
    "msg-cardio": {"type": "cardio-plan", "name": "Cardio", "message": "Locker bleiben!",
                   "items": [{"activity": "joggen", "durationS": 60, "label": "", "interval": None}]},
}


async def main():
    errors, saved = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        # ---- Dashboard ----
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("dash pageerror: " + str(e)))

        async def api(route):
            req = route.request
            if "/admin/programs" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": PROGRAMS}))
            elif "/admin/program" in req.url and req.method == "POST":
                saved.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": True}))
            elif "/admin/client-history" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"history": []}))
            else:
                await route.fulfill(status=404, body="{}")
        await pg.route("https://online-training.fwmc.workers.dev/**", api)
        await pg.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await pg.goto(DASH); await pg.wait_for_timeout(500)

        print("message field visible:", await pg.is_visible("#pMessage"))
        await pg.fill("#pCode", "neu-msg"); await pg.fill("#pName", "Neu")
        await pg.fill("#pMessage", "  Bis Donnerstag bitte üben.  ")
        await pg.locator("#exGrid .ex-btn").first.click()
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        cfg = saved[-1]["config"] if saved else {}
        print("builder save carries message:", cfg.get("message") == "Bis Donnerstag bitte üben.", cfg.get("message"))

        # edit an existing bundle (JSON-only) -> field loads, change saves
        await pg.locator("#progTable tbody tr", has_text="bundle-msg").first.click(); await pg.wait_for_timeout(200)
        print("existing message loaded:", await pg.input_value("#pMessage") == "Alte Nachricht")
        await pg.fill("#pMessage", "Neue Nachricht")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        cfg = saved[-1]["config"]
        print("bundle save carries new message:", cfg.get("type") == "bundle" and cfg.get("message") == "Neue Nachricht")
        await pg.fill("#pMessage", "")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        print("empty field removes message:", "message" not in saved[-1]["config"])
        await pg.close()

        # ---- App ----
        app = await b.new_page(viewport={"width": 390, "height": 844})
        app.on("pageerror", lambda e: errors.append("app pageerror: " + str(e)))
        app.on("console", lambda m: errors.append("app console: " + m.text) if m.type == "error" else None)

        async def code_route(route):
            code = urllib.parse.unquote(route.request.url.split("code=")[-1].split("&")[0])
            d = DEFS.get(code)
            if d is None:
                await route.fulfill(status=404, body="not found")
            else:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(d))
        await app.route("**/program?code=*", code_route)
        await app.goto(APP); await app.wait_for_timeout(500)
        await app.click("#tipsCloseBtn"); await app.wait_for_timeout(150)

        async def open_code(code):
            await app.fill("#programCodeInput", code)
            await app.click("#programGoBtn"); await app.wait_for_timeout(500)

        await open_code("msg-1")
        print("sheet shown on first open:", await app.is_visible("#coachMessageSheet"))
        print("sheet text right:", await app.inner_text("#coachMessageText") == "Diese Woche 3x vor dem Schlafen.")
        print("trainer wording (no name):", "deinem Trainer" in await app.inner_text("#coachMessageTitle"))
        print("intro opened underneath:", await app.is_visible("#programIntro"))
        await app.click("#coachMessageOkBtn"); await app.wait_for_timeout(150)
        print("sheet closes:", await app.is_hidden("#coachMessageSheet"))

        await app.click("#programBackToHome"); await app.wait_for_timeout(200)
        await open_code("msg-1")
        print("not shown again for same text:", await app.is_hidden("#coachMessageSheet"))
        await app.click("#programBackToHome"); await app.wait_for_timeout(200)

        DEFS["msg-1"]["message"] = "Neue Aufgabe: 5 Minuten Box-Atmung."
        await open_code("msg-1")
        print("shown again after text change:", await app.is_visible("#coachMessageSheet") and "Box-Atmung" in await app.inner_text("#coachMessageText"))
        await app.keyboard.press("Escape"); await app.wait_for_timeout(150)
        print("Escape closes:", await app.is_hidden("#coachMessageSheet"))
        await app.click("#programBackToHome"); await app.wait_for_timeout(200)

        await open_code("msg-none")
        print("no sheet without message:", await app.is_hidden("#coachMessageSheet"))
        await app.click("#programBackToHome"); await app.wait_for_timeout(200)

        # other code type, entered from Cardio's own code box
        await app.click('#home .section-tab[data-section="cardio"]'); await app.wait_for_timeout(200)
        await app.fill("#cardioProgramCodeInput", "msg-cardio")
        await app.click("#cardioProgramGoBtn"); await app.wait_for_timeout(500)
        print("cardio code shows message:", await app.is_visible("#coachMessageSheet") and await app.inner_text("#coachMessageText") == "Locker bleiben!")
        await app.click("#coachMessageSheet", position={"x": 5, "y": 5}); await app.wait_for_timeout(150)
        print("backdrop click closes:", await app.is_hidden("#coachMessageSheet"))

        # code history keeps the latest text
        hist = await app.evaluate("JSON.parse(localStorage.getItem('fwmc-code-history-v1')||'[]')")
        h1 = next((h for h in hist if h["code"] == "msg-1"), {})
        hn = next((h for h in hist if h["code"] == "msg-none"), {})
        print("history stores latest message:", h1.get("message") == "Neue Aufgabe: 5 Minuten Box-Atmung." and "message" not in hn)
        await app.goto(APP); await app.wait_for_timeout(500)
        await app.locator(".master-settings-btn:visible").first.click(); await app.wait_for_timeout(200)
        txt = await app.inner_text("#masterCodeHistoryList")
        print("history shows message in Grundeinstellungen:", "Box-Atmung" in txt and "Locker bleiben!" in txt)

        print("no page errors:", not errors, errors)
        await b.close()

asyncio.run(main())
