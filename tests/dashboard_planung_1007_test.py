import asyncio, datetime, json, os, urllib.parse
from playwright.async_api import async_playwright

# Trainingsplanung im Trainer-Dashboard (2026-10-07, konzept-trainingsplanung
# kp17-kp22): Bausätze (Kombi-Paket, Wochen-Vorlage, Phasen-Vorlage) with
# tags/note/version/used count and filters; the plan builder (drag & drop
# with the mouse, "Einsetzen" + tap for touch), undo, copy/paste of a day,
# Wettkampf dates as a recommendation only; "Als Plan-Code ausgeben" writes a
# training-plan def through POST /admin/program, the same code again = version
# + 1; the real app accepts that def ("Plan von deinem Trainer übernehmen?");
# Jahresübersicht, Kunden-Vorschau, local Stände, file export/import, the
# local-only mode without token (JSON to copy), 390 px light/dark without
# sideways scroll and 44 px buttons. The live Worker is never used.
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
DASH = f"http://localhost:{PORT}/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "dashboard_planung")
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra if not ok else "")


async def ls(pg, key, default=None):
    return await pg.evaluate("(k) => JSON.parse(localStorage.getItem(k) || 'null')", key) or default


async def add_entry(pg, scope, ref, di, area, what, minutes):
    await pg.click(f'{scope} .pl-day[data-ref="{ref}"][data-di="{di}"] [data-act="add"]')
    await pg.wait_for_timeout(80)
    await pg.select_option("#enArea", area)
    await pg.select_option("#enWhat", what)
    await pg.fill("#enMinutes", str(minutes))
    await pg.click("#enSaveBtn"); await pg.wait_for_timeout(80)


async def tap_tag(pg, sel_box, tag):
    await pg.click(f'{sel_box} [data-tag="{tag}"], {sel_box} [data-tagf="{tag}"]'); await pg.wait_for_timeout(50)


async def drag(pg, src, dst):
    # bring both into view first: a scroll in the middle of a drag cancels it
    await pg.locator(dst).scroll_into_view_if_needed()
    await pg.locator(src).scroll_into_view_if_needed()
    await pg.drag_and_drop(src, dst, source_position={"x": 16, "y": 12})


async def bs_by_name(pg, name):
    return next((b for b in await ls(pg, "fwmc-dash-bausaetze-v1", []) if b["name"] == name), None)


async def layout_checks(pg, label):
    sw = await pg.evaluate("document.documentElement.scrollWidth")
    check(f"{label}: no sideways scroll", sw <= 390, sw)
    small = await pg.evaluate("""() => [...document.querySelectorAll('#planPanel button, #yearPanel button')]
      .filter(b => b.offsetParent && getComputedStyle(b).visibility !== 'hidden' && b.getBoundingClientRect().height < 44)
      .map(b => b.textContent.trim() || b.getAttribute('aria-label')).slice(0, 5)""")
    check(f"{label}: buttons >= 44 px", not small, small)
    over = await pg.evaluate("""() => [...document.querySelectorAll('#planPanel *')].filter(e => {
      if (!e.offsetParent || e.closest('.table-scroll') || e.closest('.pv-phone')) return false;
      const r = e.getBoundingClientRect(); return r.right > innerWidth + 1 || r.left < -1; }).map(e => e.className || e.tagName).slice(0, 5)""")
    check(f"{label}: nothing sticks out of the page", not over, over)


async def main():
    errors = []
    os.makedirs(SHOTS, exist_ok=True)
    server = {}      # code -> {code, name, active, config}
    posts, hist = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block", accept_downloads=True)
        await ctx.add_init_script("""localStorage.setItem('fwmc-tips-seen','true');
          localStorage.setItem('fwmc-test-bottomnav','true');
          localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));""")

        async def api(route):
            req = route.request; url = req.url
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if "/admin/programs" in url:
                body = {"programs": [{"code": c, "name": v["config"].get("name", ""), "active": v["active"], "config": v["config"], "updatedAt": "2026-10-07T10:00:00Z"} for c, v in server.items()]}
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
            elif "/admin/program" in url and req.method == "POST":
                d = json.loads(req.post_data); posts.append(d)
                created = d["code"] not in server
                server[d["code"]] = {"active": d["active"], "config": d["config"]}
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": created}))
            elif "/admin/client-history" in url:
                if req.method == "POST": hist.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"entries": []}))
            elif "/program" in url:
                code = (q.get("code") or [""])[0].lower()
                if code in server:
                    await route.fulfill(status=200, content_type="application/json", body=json.dumps(server[code]["config"]))
                else:
                    await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
            else:
                await route.fulfill(status=404, content_type="application/json", body="{}")
        await ctx.route("https://online-training.fwmc.workers.dev/**", api)

        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await pg.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await pg.goto(DASH); await pg.wait_for_timeout(500)
        check("planning panel shown", await pg.is_visible("#planPanel") and await pg.is_visible("#yearPanel"))
        check("library starts empty with a friendly hint", await pg.locator(".bs-card").count() == 0 and "Noch keine Bausätze" in await pg.inner_text("#bsEmpty"))
        check("no client yet: hint", await pg.is_visible("#plNoClient"))
        check("privacy hint names Kürzel only", "nie Namen oder Gesundheitsangaben" in await pg.inner_text("#planPanel"))

        # ---- client ----
        await pg.fill("#plNewKuerzel", "Tina Maria Schulz"); await pg.click("#plNewClientBtn"); await pg.wait_for_timeout(80)
        check("long name refused as Kürzel (max 12)", "12 Zeichen" in await pg.inner_text("#plClientMsg"))
        await pg.fill("#plNewKuerzel", "ts-07"); await pg.click("#plNewClientBtn"); await pg.wait_for_timeout(120)
        plans = await ls(pg, "fwmc-dash-plans-v1", {})
        check("client stored under Kürzel only", list(plans.keys()) == ["TS-07"] and await pg.is_visible("#plEditor"), list(plans.keys()))

        # ---- kp17: one Bausatz of each kind ----
        await pg.click("#bsNewBtn"); await pg.wait_for_timeout(100)
        await pg.click('#bsKindRow [data-bskind="kombi"]')
        await pg.fill("#bsName", "Kopf wach vor dem Spiel"); await pg.fill("#bsNote", "Vor dem Spiel, 15 Minuten")
        await tap_tag(pg, "#bsTags", "Sportler"); await tap_tag(pg, "#bsTags", "Wettkampf")
        await pg.select_option('#bsBody .bs-item[data-i="0"] [data-k="area"]', "nat"); await pg.wait_for_timeout(50)
        await pg.select_option('#bsBody .bs-item[data-i="0"] [data-k="what"]', "nat:remember")
        await pg.fill('#bsBody .bs-item[data-i="0"] [data-k="minutes"]', "10"); await pg.press('#bsBody .bs-item[data-i="0"] [data-k="minutes"]', "Tab")
        await pg.click("#bsAddItemBtn"); await pg.wait_for_timeout(50)
        await pg.select_option('#bsBody .bs-item[data-i="1"] [data-k="area"]', "breath"); await pg.wait_for_timeout(50)
        await pg.fill('#bsBody .bs-item[data-i="1"] [data-k="minutes"]', "5"); await pg.press('#bsBody .bs-item[data-i="1"] [data-k="minutes"]', "Tab")
        await pg.click("#bsSaveBtn"); await pg.wait_for_timeout(120)
        k = await bs_by_name(pg, "Kopf wach vor dem Spiel")
        check("kp17: Kombi-Paket saved", k and k["kind"] == "kombi" and k["version"] == 1 and k["used"] == 0 and k["tags"] == ["Sportler", "Wettkampf"]
              and [(i["area"], i["what"], i["minutes"]) for i in k["data"]["items"]] == [("nat", "nat:remember", 10), ("breath", "", 5)], k)

        await pg.click("#bsNewBtn"); await pg.wait_for_timeout(100)
        await pg.click('#bsKindRow [data-bskind="week"]'); await pg.wait_for_timeout(50)
        await pg.fill("#bsName", "3x Kopf"); await tap_tag(pg, "#bsTags", "Einsteiger")
        await pg.click("#bsSaveBtn"); await pg.wait_for_timeout(80)
        check("kp17: empty week is refused", "Mindestens ein Training" in await pg.inner_text("#bsMsg"))
        await add_entry(pg, "#bsBody", "d:0", 0, "nat", "nat:blitz", 10)
        await add_entry(pg, "#bsBody", "d:0", 2, "visual", "ex:stroop-classic", 10)
        await add_entry(pg, "#bsBody", "d:0", 4, "nat", "nat:flash", 10)
        await pg.click("#bsSaveBtn"); await pg.wait_for_timeout(120)
        w = await bs_by_name(pg, "3x Kopf")
        check("kp17: Wochen-Vorlage saved", w and w["kind"] == "week" and [len(d) for d in w["data"]["days"]] == [1, 0, 1, 0, 1, 0, 0], w and w["data"])

        await pg.click("#bsNewBtn"); await pg.wait_for_timeout(100)
        await pg.click('#bsKindRow [data-bskind="phase"]'); await pg.wait_for_timeout(50)
        await pg.fill("#bsName", "Grundlage 4 Wochen"); await pg.fill("#bsNote", "Einstieg für Sportler")
        await tap_tag(pg, "#bsTags", "Einsteiger"); await tap_tag(pg, "#bsTags", "Sportler")
        await pg.fill("#bsPhName", "Grundlage"); await pg.press("#bsPhName", "Tab")
        await pg.fill("#bsPhWeeks", "4"); await pg.press("#bsPhWeeks", "Tab")
        await add_entry(pg, "#bsBody", "d:0", 2, "breath", "", 10)
        await pg.select_option("#bsPhRot", "2"); await pg.wait_for_timeout(80)
        check("kp17: week B appears as a copy of A", await pg.locator('#bsBody .pl-week[data-ref="d:1"] .pl-chip').count() == 1)
        await add_entry(pg, "#bsBody", "d:1", 4, "cardio", "", 30)
        await pg.click("#bsSaveBtn"); await pg.wait_for_timeout(120)
        ph = await bs_by_name(pg, "Grundlage 4 Wochen")
        check("kp17: Phasen-Vorlage with A/B saved", ph and ph["kind"] == "phase" and ph["data"]["weeks"] == 4 and len(ph["data"].get("alt", [])) == 1
              and len(ph["data"]["alt"][0][4]) == 1 and len(ph["data"]["days"][4]) == 0, ph and ph["data"])
        check("kp17: library shows 3 cards with version + used count", await pg.locator(".bs-card").count() == 3 and "Version 1" in await pg.inner_text("#bsList") and "noch nicht eingesetzt" in await pg.inner_text("#bsList"))

        # filters
        async def names():
            return sorted(await pg.eval_on_selector_all(".bs-card .bs-name", "els => els.map(e => e.textContent)"))
        await tap_tag(pg, "#bsTagFilter", "Einsteiger")
        check("filter Einsteiger", await names() == ["3x Kopf", "Grundlage 4 Wochen"], await names())
        await tap_tag(pg, "#bsTagFilter", "Sportler")
        check("filter Einsteiger + Sportler", await names() == ["Grundlage 4 Wochen"], await names())
        await tap_tag(pg, "#bsTagFilter", "Regeneration")
        check("filter without match says so", await names() == [] and "passt zu diesem Filter" in await pg.inner_text("#bsEmpty"))
        for t in ["Einsteiger", "Sportler", "Regeneration"]:
            await tap_tag(pg, "#bsTagFilter", t)
        await pg.click('#bsKindFilter [data-bk="kombi"]'); await pg.wait_for_timeout(50)
        check("filter by kind Kombi", await names() == ["Kopf wach vor dem Spiel"], await names())
        await pg.click('#bsKindFilter [data-bk="all"]'); await pg.wait_for_timeout(50)

        # edit = version + 1
        await pg.click(f'.bs-card[data-bs="{k["id"]}"] [data-act="bs-edit"]'); await pg.wait_for_timeout(80)
        await pg.click("#bsAsOne"); await pg.fill("#bsCode", "kopfwach-abc"); await pg.press("#bsCode", "Tab")
        await pg.click("#bsSaveBtn"); await pg.wait_for_timeout(100)
        k = await bs_by_name(pg, "Kopf wach vor dem Spiel")
        check("kp17: editing raises the Bausatz version", k["version"] == 2 and k["data"]["asOne"] and k["data"]["code"] == "kopfwach-abc", k)

        # ---- kp18: build the plan ----
        await drag(pg, f'.bs-card[data-bs="{ph["id"]}"]', "#plPhaseEnd"); await pg.wait_for_timeout(150)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp18: phase template dragged in", len(plan["phases"]) == 1 and plan["phases"][0]["name"] == "Grundlage" and plan["phases"][0]["weeks"] == 4 and len(plan["phases"][0].get("alt", [])) == 1, plan["phases"])
        check("kp18: copies get fresh entry ids", plan["phases"][0]["days"][2][0]["id"] != ph["data"]["days"][2][0]["id"])
        # tap-to-place: Kombi on Tuesday of week A
        await pg.click(f'.bs-card[data-bs="{k["id"]}"] [data-act="bs-place"]'); await pg.wait_for_timeout(80)
        check("kp18: tap mode shows what to tap", await pg.is_visible("#plPlacing") and "tippe auf einen Tag" in await pg.inner_text("#plPlacing"))
        await pg.click('.pl-day[data-ref="p:0:0"][data-di="1"]', position={"x": 10, "y": 10}); await pg.wait_for_timeout(120)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        tue = plan["phases"][0]["days"][1]
        check("kp18: Kombi-Paket placed by tap as one combo entry", len(tue) == 1 and tue[0]["area"] == "combo" and tue[0]["code"] == "kopfwach-abc" and tue[0]["minutes"] == 15, tue)
        check("kp18: tap mode ends after placing", not await pg.is_visible("#plPlacing"))
        # week template dragged onto week B
        before_b = plan["phases"][0]["alt"][0]
        await drag(pg, f'.bs-card[data-bs="{w["id"]}"]', '.pl-week[data-ref="p:0:1"] .pl-week-head'); await pg.wait_for_timeout(150)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp18: week template replaces week B", [len(d) for d in plan["phases"][0]["alt"][0]] == [1, 0, 1, 0, 1, 0, 0] and plan["phases"][0]["alt"][0][0][0]["what"] == "nat:blitz")
        lib = await ls(pg, "fwmc-dash-bausaetze-v1", [])
        check("kp17: used count counts placements", {b2["name"]: b2["used"] for b2 in lib} == {"Kopf wach vor dem Spiel": 1, "3x Kopf": 1, "Grundlage 4 Wochen": 1}, {b2["name"]: b2["used"] for b2 in lib})
        # undo
        await pg.click("#plUndoBtn"); await pg.wait_for_timeout(120)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp18: Rückgängig restores week B", plan["phases"][0]["alt"][0] == before_b)
        await pg.click("body", position={"x": 5, "y": 5})
        await pg.keyboard.press("Control+z"); await pg.wait_for_timeout(120)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp18: Ctrl+Z undoes the Kombi placement", plan["phases"][0]["days"][1] == [])
        # place Kombi again by drag (as one entry), drag works on a day too
        await drag(pg, f'.bs-card[data-bs="{k["id"]}"]', '.pl-day[data-ref="p:0:0"][data-di="1"]'); await pg.wait_for_timeout(150)
        # edit an entry: time + minutes
        await pg.click('.pl-day[data-ref="p:0:0"][data-di="2"] .pl-chip'); await pg.wait_for_timeout(80)
        await pg.fill("#enTime", "07:30"); await pg.fill("#enMinutes", "20"); await pg.click("#enSaveBtn"); await pg.wait_for_timeout(100)
        # copy Tuesday, paste to Thursday
        await pg.click('.pl-day[data-ref="p:0:0"][data-di="1"] [data-act="daymenu"]'); await pg.wait_for_timeout(60)
        await pg.click('#dayMenuSheet [data-dm="copy"]'); await pg.wait_for_timeout(60)
        await pg.click('.pl-day[data-ref="p:0:0"][data-di="3"] [data-act="daymenu"]'); await pg.wait_for_timeout(60)
        await pg.click('#dayMenuSheet [data-dm="paste"]'); await pg.wait_for_timeout(100)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        a = plan["phases"][0]["days"]
        check("kp18: entry edited", a[2][0]["time"] == "07:30" and a[2][0]["minutes"] == 20, a[2])
        check("kp18: day copied and pasted with new ids", len(a[3]) == 1 and a[3][0]["area"] == "combo" and a[3][0]["id"] != a[1][0]["id"], a[3])
        # second phase: empty phase, by hand, 3 weeks, out of the score
        await pg.click("#plAddPhaseBtn"); await pg.wait_for_timeout(100)
        await pg.fill("#phName1", "Belastung"); await pg.press("#phName1", "Tab"); await pg.wait_for_timeout(60)
        await pg.fill("#phWeeks1", "3"); await pg.press("#phWeeks1", "Tab"); await pg.wait_for_timeout(60)
        await add_entry(pg, "#plPlan", "p:1:0", 0, "workout", "", 30)
        await pg.check('[data-pf="noScore"][data-pi="1"]'); await pg.wait_for_timeout(100)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp18: hand-made phase with noScore", len(plan["phases"]) == 2 and plan["phases"][1]["name"] == "Belastung" and plan["phases"][1]["weeks"] == 3 and plan["phases"][1].get("noScore") is True)
        # Wettkampf: in week 6 (phase 2)
        start = datetime.date.fromisoformat(plan["startDate"])
        comp = start + datetime.timedelta(days=7 * 5 + 5)
        await pg.fill("#plCompDate", comp.isoformat()); await pg.fill("#plCompTitle", "Turnier"); await pg.click("#plCompAddBtn"); await pg.wait_for_timeout(120)
        txt = await pg.inner_text("#plPhase1")
        check("Wettkampf: recommendation text only", "Turnier" in txt and "Empfehlung: in der Woche davor etwas leichter, mit dem Kunden abstimmen." in txt, txt[:300])
        plan2 = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("Wettkampf: training not changed", plan2["phases"] == plan["phases"] and plan2["comps"][0]["date"] == comp.isoformat())

        # ---- kp22 preview ----
        pv = await pg.inner_text("#pvPhone")
        check("kp22: preview shows Heute + Mein Plan + phase", "HEUTE" in pv.upper() and "MEIN PLAN" in pv.upper() and "Grundlage" in pv, pv[:200])
        box = await pg.locator("#pvPhone").bounding_box()
        check("kp22: phone-sized (about 390x700)", box and 360 <= box["width"] <= 392 and 690 <= box["height"] <= 710, box)
        await pg.click('#pvWhenRow [data-when="comp"]'); await pg.wait_for_timeout(80)
        pv = await pg.inner_text("#pvPhone")
        check("kp22: Wettkampfwoche shows phase 2 + recommendation", "Belastung" in pv and "Empfehlung" in pv and "zählt nicht fürs Wochenziel" in pv, pv[:300])
        await pg.click('#pvWhenRow [data-when="now"]')

        # ---- kp21 issue ----
        await pg.fill("#plName", "Grundlage Herbst"); await pg.press("#plName", "Tab")
        await pg.click("#plIssueBtn"); await pg.wait_for_timeout(100)
        check("issue needs a code", "Plan-Code" in await pg.inner_text("#plIssueMsg"))
        await pg.fill("#plCode", "TS07 Plan"); await pg.press("#plCode", "Tab"); await pg.wait_for_timeout(60)
        await pg.click("#plIssueBtn"); await pg.wait_for_timeout(400)
        check("kp21: saved via POST /admin/program", posts and posts[-1]["code"] == "ts07-plan" and posts[-1]["active"] is True, posts[-1:] and posts[-1]["code"])
        d1 = posts[-1]["config"]
        check("def shape: training-plan v1 with phases/alt/noScore",
              d1["type"] == "training-plan" and d1["version"] == 1 and d1["name"] == "Grundlage Herbst" and d1["plan"]["startDate"] == plan["startDate"]
              and len(d1["plan"]["phases"]) == 2 and len(d1["plan"]["phases"][0]["alt"]) == 1 and d1["plan"]["phases"][1]["noScore"] is True
              and all(len(ph2["days"]) == 7 for ph2 in d1["plan"]["phases"]), json.dumps(d1)[:300])
        e0 = d1["plan"]["phases"][0]["days"][2][0]
        check("def entry shape", set(e0.keys()) <= {"id", "area", "what", "code", "time", "minutes", "special", "title"} and e0["time"] == "07:30", e0)
        k0 = d1["plan"]["phases"][0]["days"][1][0]
        check("L1: Kombi-Paket entry carries its name as title", k0["area"] == "combo" and k0.get("title") == "Kopf wach vor dem Spiel", k0)
        check("L2: the client's Wettkampf dates go out as plan.events", d1["plan"].get("events") == [{"date": comp.isoformat(), "title": "Turnier", "kind": "wettkampf"}], d1["plan"].get("events"))
        check("kp21: client history logged with Kürzel", hist and hist[-1]["clientCode"] == "TS-07" and hist[-1]["programCode"] == "ts07-plan")
        st = await pg.inner_text("#plIssueState")
        check("kp21: 'Version 1, ausgegeben am …'", "Version 1, ausgegeben am" in st, st)
        await pg.wait_for_timeout(300)
        await add_entry(pg, "#plPlan", "p:0:0", 5, "breath", "", 5)
        await pg.click("#plIssueBtn"); await pg.wait_for_timeout(400)
        d2 = posts[-1]["config"]
        check("kp21: same code again = version 2", posts[-1]["code"] == "ts07-plan" and d2["version"] == 2 and len(d2["plan"]["phases"][0]["days"][5]) == 1)
        check("kp21: entry ids stay stable between versions", d2["plan"]["phases"][0]["days"][2][0]["id"] == e0["id"])
        st = await pg.inner_text("#plIssueState")
        check("kp21: state shows version 2", "Version 2, ausgegeben am" in st, st)
        check("JSON emergency exit shows the next version", json.loads(await pg.input_value("#plJson"))["version"] == 3)

        # ---- kp19 timeline ----
        check("kp19: timeline row with bars, diamond, today line", await pg.locator('#tlGrid .tl-bar[data-tl="TS-07"]').count() == 2
              and await pg.locator("#tlGrid .tl-diamond").count() == 1 and await pg.locator("#tlGrid .tl-today").count() >= 1)
        check("kp19: month header", "Okt" in await pg.inner_text("#tlGrid"))
        # a second client whose plan ends in 2 weeks
        await pg.fill("#plNewKuerzel", "MK-02"); await pg.check("#plNewGroup"); await pg.click("#plNewClientBtn"); await pg.wait_for_timeout(100)
        mon = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
        await pg.fill("#plStart", (mon - datetime.timedelta(days=7)).isoformat()); await pg.press("#plStart", "Tab"); await pg.wait_for_timeout(80)
        await pg.click("#plAddPhaseBtn"); await pg.wait_for_timeout(80)
        await pg.fill("#phWeeks0", "3"); await pg.press("#phWeeks0", "Tab"); await pg.wait_for_timeout(100)
        tl = await pg.inner_text("#tlGrid")
        check("kp19: 'Plan endet in 2 Wochen' + group", "Plan endet in 2 Wochen" in tl and "Gruppe" in tl, tl[-200:])
        await pg.click('#tlGrid .tl-bar[data-tl="TS-07"][data-pi="1"]'); await pg.wait_for_timeout(300)
        check("kp19: tapping a bar opens that plan", await pg.input_value("#plClientSelect") == "TS-07" and await pg.input_value("#phName1") == "Belastung")

        # ---- kp20 Stände + file ----
        opts = await pg.eval_on_selector_all("#plVersionSelect option", "els => els.map(e => e.textContent)")
        check("kp20: a Stand per issue ('Stand TT.MM., HH:MM')", len(opts) == 2 and all(o.startswith("Stand ") for o in opts) and "Version 2" in opts[0], opts)
        await pg.click('[data-act="ph-del"][data-pi="1"]'); await pg.wait_for_timeout(100)
        await pg.click("#plSaveVersionBtn"); await pg.wait_for_timeout(80)
        await pg.select_option("#plVersionSelect", index=1); await pg.click("#plRestoreBtn"); await pg.wait_for_timeout(120)
        plan = (await ls(pg, "fwmc-dash-plans-v1"))["TS-07"]
        check("kp20: old Stand restored (2 phases again), issue history kept", len(plan["phases"]) == 2 and len(plan["issued"]) == 2)
        async with pg.expect_download() as dl:
            await pg.click("#plExportBtn")
        path = await (await dl.value).path()
        data = json.load(open(path))
        check("kp20: export file has everything", data["app"] == "fwmc-trainer-dashboard" and len(data["bausaetze"]) == 3 and set(data["plans"]) == {"TS-07", "MK-02"} and len(data["versions"]["TS-07"]) == 3)
        keys = await pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('fwmc-dash-')).sort()")
        check("kp20: keys start with fwmc-dash-", keys == ["fwmc-dash-bausaetze-v1", "fwmc-dash-current-v1", "fwmc-dash-plan-versions-v1", "fwmc-dash-plans-v1"], keys)
        await pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('fwmc-dash-')).forEach(k => localStorage.removeItem(k))")
        await pg.reload(); await pg.wait_for_timeout(400)
        check("after wipe: empty", await pg.locator(".bs-card").count() == 0 and await pg.is_visible("#plNoClient"))
        await pg.set_input_files("#plImportFile", path); await pg.wait_for_timeout(300)
        check("kp20: import restores library + plans", await pg.locator(".bs-card").count() == 3 and sorted(await pg.eval_on_selector_all("#plClientSelect option", "e => e.map(x => x.value)")) == ["MK-02", "TS-07"])
        await pg.set_input_files("#plImportFile", path); await pg.wait_for_timeout(200)
        check("kp20: importing over existing asks first", await pg.is_visible("#plConfirmSheet"))
        await pg.click("#plConfirmYes"); await pg.wait_for_timeout(200)
        check("kp20: still 3 Bausätze (no duplicates)", await pg.locator(".bs-card").count() == 3)

        # ---- screenshots 390/1440 light/dark + layout ----
        await pg.select_option("#plClientSelect", "TS-07"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.getElementById('plToast').hidden = true")
        for scheme in ["light", "dark"]:
            await pg.emulate_media(color_scheme=scheme)
            await pg.set_viewport_size({"width": 1440, "height": 1000}); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f"1440_{scheme}.png"), full_page=True)
            await pg.set_viewport_size({"width": 390, "height": 844}); await pg.wait_for_timeout(250)
            await layout_checks(pg, f"390 {scheme}")
            await pg.screenshot(path=os.path.join(SHOTS, f"390_{scheme}.png"), full_page=True)
            await pg.click('.pl-day[data-ref="p:0:0"][data-di="1"] .pl-chip'); await pg.wait_for_timeout(100)
            await pg.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_entry.png"))
            await pg.click('#entrySheet [data-close="entrySheet"]')
            await pg.click(f'.bs-card [data-act="bs-edit"]'); await pg.wait_for_timeout(100)
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            check(f"390 {scheme}: Bausatz sheet fits", sw <= 390, sw)
            await pg.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_bausatz.png"))
            await pg.click('#bsSheet .pl-headrow [data-close="bsSheet"]'); await pg.wait_for_timeout(60)
        await pg.emulate_media(color_scheme="light")
        await pg.set_viewport_size({"width": 1440, "height": 1000})

        # ---- the app accepts the issued def ----
        app = await ctx.new_page()
        app.on("pageerror", lambda e: errors.append("app pageerror: " + str(e)))
        app.on("console", lambda m: errors.append("app console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await app.set_viewport_size({"width": 390, "height": 844})
        await app.goto(BASE + "?bereich=heute"); await app.wait_for_timeout(500)
        if await app.locator(".today-code .code-toggle").count():
            await app.click(".today-code .code-toggle")
        await app.fill("#todayCodeInput", "ts07-plan"); await app.click("#todayCodeGoBtn"); await app.wait_for_timeout(800)
        title = await app.inner_text("#confirmTitle") if await app.is_visible("#confirmSheet") else ""
        check("app: 'Plan von deinem Trainer übernehmen?' sheet", title == "Plan von deinem Trainer übernehmen?", title)
        if title:
            await app.click("#confirmYesBtn"); await app.wait_for_timeout(400)
            ap = await app.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
            check("app: plan taken over as version 2 with A/B + noScore", ap["source"]["code"] == "ts07-plan" and ap["source"]["version"] == 2
                  and len(ap["phases"]) == 2 and len(ap["phases"][0].get("alt", [])) == 1 and ap["phases"][1].get("noScore") is True
                  and ap["phases"][0]["days"][1][0]["area"] == "combo", json.dumps(ap)[:300])
            check("app L1: Kombi-Paket name kept", ap["phases"][0]["days"][1][0].get("title") == "Kopf wach vor dem Spiel", ap["phases"][0]["days"][1][0])
            aev = await app.evaluate("() => JSON.parse(localStorage.getItem('fwmc-events-v1') || '[]')")
            check("app L2: Wettkampf in the own calendar", len(aev) == 1 and aev[0]["title"] == "Turnier" and aev[0]["date"] == comp.isoformat() and aev[0]["fromTrainer"] == "ts07-plan", aev)
        await app.close()

        # ---- local-only mode, no token ----
        ctx2 = await b.new_context(viewport={"width": 390, "height": 844})
        async def no_worker(route):
            errors.append("local-only mode called the Worker: " + route.request.url)
            await route.abort()
        await ctx2.route("https://online-training.fwmc.workers.dev/**", no_worker)
        pg2 = await ctx2.new_page()
        pg2.on("pageerror", lambda e: errors.append("local pageerror: " + str(e)))
        pg2.on("console", lambda m: errors.append("local console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await pg2.goto(DASH); await pg2.wait_for_timeout(300)
        await pg2.click("#gateLocalBtn"); await pg2.wait_for_timeout(200)
        check("local-only: planning shown, server panels hidden", await pg2.is_visible("#planPanel") and not await pg2.is_visible("#codesPanel") and not await pg2.is_visible("#historyPanel"))
        await pg2.fill("#plNewKuerzel", "AB-1"); await pg2.click("#plNewClientBtn"); await pg2.wait_for_timeout(80)
        await pg2.click("#plAddPhaseBtn"); await pg2.wait_for_timeout(80)
        await add_entry(pg2, "#plPlan", "p:0:0", 0, "nat", "nat:mot", 15)
        await pg2.click("#plCodeRandomBtn"); await pg2.wait_for_timeout(60)
        code2 = await pg2.input_value("#plCode")
        check("random code from the Kürzel", code2.startswith("ab-1-") and len(code2) == 13, code2)
        await pg2.click("#plIssueBtn"); await pg2.wait_for_timeout(200)
        check("local-only: no token -> JSON to copy", "Ohne Admin-Token" in await pg2.inner_text("#plIssueMsg") and await pg2.evaluate("document.getElementById('plJsonDetails').open"))
        dj = json.loads(await pg2.input_value("#plJson"))
        check("local-only: JSON is a training-plan def", dj["type"] == "training-plan" and dj["plan"]["phases"][0]["days"][0][0]["what"] == "nat:mot")
        for scheme in ["light", "dark"]:
            await pg2.emulate_media(color_scheme=scheme); await pg2.wait_for_timeout(100)
            await layout_checks(pg2, f"local 390 {scheme}")
        await ctx2.close()
        await b.close()

    check("no page errors", not errors, errors)
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)
    print("ERRORS:", errors)


asyncio.run(main())
