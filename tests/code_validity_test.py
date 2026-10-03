import asyncio, json, urllib.parse
from playwright.async_api import async_playwright

DASH = "http://localhost:8845/dashboard.html"
APP = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# Codes mit Laufzeit (Fabian, 2026-10-03): personal and group codes, an
# optional validity window, seats per group code counted by device id.
# Dashboard writes validFrom/validUntil/codeKind/seats; the app sends a
# device id, shows clear messages for expired / not yet valid / full codes,
# checks validUntil itself too (works with an older Worker), and shows
# "gültig bis" in the code history.

PROGRAMS = [
    {"code": "grp-a", "active": True, "name": "Gruppe A", "createdAt": "2026-10-01T10:00:00Z", "updatedAt": "2026-10-02T10:00:00Z",
     "seatsUsed": 3, "config": {"name": "Gruppe A", "codeKind": "gruppe", "seats": 12, "validUntil": "2026-12-31",
                                "blocks": [{"exercise": "vt-color", "duration": 30}]}},
    {"code": "pers-b", "active": True, "name": "Person B", "createdAt": "2026-10-01T10:00:00Z", "updatedAt": "2026-10-01T10:00:00Z",
     "seatsUsed": 0, "config": {"name": "Person B", "blocks": [{"exercise": "vt-color", "duration": 30}]}},
]

DEFS = {
    "gut": {"name": "Gültig", "validUntil": "2099-12-31", "blocks": [{"exercise": "vt-color", "duration": 30}]},
    "lokal-alt": {"name": "Alt", "validUntil": "2020-01-01", "blocks": [{"exercise": "vt-color", "duration": 30}]},
}
STATUS = {
    "alt": (410, {"error": "expired", "validUntil": "2026-09-30"}),
    "spaeter": (403, {"error": "not_yet", "validFrom": "2099-01-01"}),
    "voll": (403, {"error": "full"}),
}

results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


async def main():
    errors, saved, resets, lookups = [], [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        # ---- Dashboard ----
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("dash pageerror: " + str(e)))
        pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))

        async def api(route):
            req = route.request
            if "/admin/programs" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": PROGRAMS}))
            elif "/admin/code-seats-reset" in req.url:
                resets.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
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

        table = await pg.inner_text("#progTable")
        check("table shows run time + seats", "bis 31.12.2026" in table and "3/12 Plätze" in table)
        check("table shows unbegrenzt", "unbegrenzt" in table)
        check("seats row hidden for personal code", await pg.is_hidden("#pSeatsRow"))

        # new group code with window
        await pg.fill("#pCode", "neu-grp"); await pg.fill("#pName", "Neu")
        await pg.locator("#exGrid .ex-btn").first.click()
        await pg.check("#pKindGruppe")
        check("seats row shows for group", await pg.is_visible("#pSeatsRow"))
        await pg.fill("#pSeats", "8")
        await pg.fill("#pValidFrom", "2026-10-05"); await pg.fill("#pValidUntil", "2026-11-30")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        cfg = saved[-1]["config"] if saved else {}
        check("save carries group + seats + window", cfg.get("codeKind") == "gruppe" and cfg.get("seats") == 8
              and cfg.get("validFrom") == "2026-10-05" and cfg.get("validUntil") == "2026-11-30", cfg)

        # from after until -> refused
        n = len(saved)
        await pg.fill("#pValidFrom", "2026-12-05")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        check("from after until refused", len(saved) == n and "liegt nach" in await pg.inner_text("#pMsg"))
        await pg.fill("#pValidFrom", "")

        # edit existing group code: fields load, reset button frees seats
        await pg.locator("#progTable tbody tr", has_text="grp-a").first.click(); await pg.wait_for_timeout(200)
        check("existing group loads", await pg.is_checked("#pKindGruppe") and await pg.input_value("#pSeats") == "12"
              and await pg.input_value("#pValidUntil") == "2026-12-31")
        check("seat info shown", "3 von 12" in await pg.inner_text("#pSeatsInfo"))
        check("reset button visible", await pg.is_visible("#pSeatsResetBtn"))
        await pg.click("#pSeatsResetBtn"); await pg.wait_for_timeout(300)
        check("reset posts code", resets and resets[-1].get("code") == "grp-a")

        # switch to personal: group fields removed on save
        await pg.check("#pKindPerson"); await pg.fill("#pValidUntil", "")
        await pg.click("#pSaveBtn"); await pg.wait_for_timeout(200)
        cfg = saved[-1]["config"]
        check("personal save drops seats + date", "seats" not in cfg and "codeKind" not in cfg and "validUntil" not in cfg)
        await pg.locator("#progTable tbody tr", has_text="pers-b").first.click(); await pg.wait_for_timeout(200)
        check("personal code loads empty fields", await pg.is_checked("#pKindPerson") and await pg.input_value("#pValidUntil") == "")
        await pg.close()

        # ---- App ----
        app = await b.new_page(viewport={"width": 390, "height": 844})
        app.on("pageerror", lambda e: errors.append("app pageerror: " + str(e)))
        app.on("console", lambda m: errors.append("app console: " + m.text)
               if m.type == "error" and "Failed to load resource" not in m.text else None)

        async def code_route(route):
            url = route.request.url
            lookups.append(url)
            code = urllib.parse.unquote(url.split("code=")[-1].split("&")[0])
            if code in STATUS:
                st, body = STATUS[code]
                await route.fulfill(status=st, content_type="application/json", body=json.dumps(body))
            elif code in DEFS:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(DEFS[code]))
            else:
                await route.fulfill(status=404, body="{}")
        await app.route("**/program?code=*", code_route)
        await app.add_init_script("try{localStorage.setItem('fwmc-tips-seen','true')}catch(e){}")
        await app.goto(APP); await app.wait_for_timeout(500)

        async def open_code(code):
            await app.fill("#programCodeInput", code)
            await app.click("#programGoBtn"); await app.wait_for_timeout(500)

        await open_code("alt")
        err = await app.inner_text("#programError")
        check("expired message with date", "bis 30.09.2026 gültig" in err and "Trainer" in err, err)
        check("stays on home", await app.is_visible("#home"))
        await open_code("spaeter")
        err = await app.inner_text("#programError")
        check("not yet message with date", "erst ab 01.01.2099" in err, err)
        await open_code("voll")
        err = await app.inner_text("#programError")
        check("full message", "Plätze" in err and "Trainer" in err, err)
        await open_code("lokal-alt")
        err = await app.inner_text("#programError")
        check("app checks validUntil itself (old Worker)", "bis 01.01.2020 gültig" in err and await app.is_visible("#home"), err)

        dev = await app.evaluate("localStorage.getItem('fwmc-device-id')")
        check("device id created", bool(dev) and len(dev) == 20, dev)
        check("device id sent with lookup", any(("device=" + str(dev)) in u for u in lookups))

        await open_code("gut")
        check("valid code opens intro", await app.is_visible("#programIntro"))
        await app.click("#programBackToHome"); await app.wait_for_timeout(200)

        await app.reload(); await app.wait_for_timeout(500)
        check("device id stays the same after reload", await app.evaluate("localStorage.getItem('fwmc-device-id')") == dev)

        await app.click("#home .master-settings-btn"); await app.wait_for_timeout(200)
        hist = await app.inner_text("#masterCodeHistoryList")
        check("history shows gültig bis", "gültig bis 31.12.2099" in hist, hist)

        check("no page errors", not errors, errors[:3])
        await b.close()
    bad = [n for n, ok in results if not ok]
    print("FAILED:", bad if bad else "none")


asyncio.run(main())
