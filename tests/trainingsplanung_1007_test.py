"""Trainingsplanung (Fabian 06./07.10.2026, konzept-trainingsplanung.md):
Wochen im Wechsel + mehrere Tage (kp1), Wochenziel folgt dem Plan (kp2),
Ablage/Kopieren/Rückgängig (kp3), "Wofür gilt das?" (kp4), Pause (kp7),
Woche wiederholen/überspringen/verschieben (kp8), Sondertraining/-woche
(kp10), Wettkampf-Empfehlung ohne Automatik (kp11), Plan per Code (kp13),
Mein Plan (kp15). Nothing changes minutes by itself (Fabian 07.10. 21:17).
Run from tests/ with a dev server on :8845."""
import asyncio, json, datetime, urllib.parse
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-bottomnav','1');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
D = lambda d: d.isoformat()
def E(i, area="breath", minutes=15, **kw):
    return {"id": i, "area": area, "what": "", "code": "", "time": "", "minutes": minutes, **kw}

async def seed(pg, plan, extra=None):
    await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(150)
    await pg.evaluate("""([p, x]) => { const keep = ['fwmc-tips-seen','fwmc-test-bottomnav','fwmc-master-v1'];
      Object.keys(localStorage).filter(k => !keep.includes(k)).forEach(k => localStorage.removeItem(k));
      if (p) localStorage.setItem('fwmc-plan-v1', JSON.stringify(p));
      Object.entries(x || {}).forEach(([k, v]) => localStorage.setItem(k, JSON.stringify(v))); }""", [plan, extra or {}])
    await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)

async def day_titles(pg, date):
    await pg.evaluate("(d) => { const b = document.querySelector(`#todayWeekStrip [data-date='${d}']`); if (b) b.click(); }", date)
    await pg.wait_for_timeout(150)
    return await pg.inner_text("#dayPanelBody")

async def myplan_rows(pg):
    await pg.click("#todayMyPlanBtn"); await pg.wait_for_timeout(300)
    return await pg.evaluate("() => [...document.querySelectorAll('#myPlanList .myplan-week')].map(r => r.dataset.week + '|' + r.querySelector('.myplan-text').textContent)")

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        served = {}
        async def api(route):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query)
            code = (q.get("code") or [""])[0].lower()
            if code in served: await route.fulfill(status=200, content_type="application/json", body=json.dumps(served[code]))
            else: await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
        await ctx.route("https://online-training.fwmc.workers.dev/**", api)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

        # ---- kp1: Wochen im Wechsel ----
        start = monday - datetime.timedelta(days=7)  # this week = plan week 2 = B
        plan = {"startDate": D(start), "phases": [{"id": "p1", "name": "Grundlage", "weeks": 0,
                 "days": [[E("a1", "breath")], [], [], [], [], [], []],
                 "alt": [[[E("b1", "workout")], [], [], [], [], [], []]]}]}
        await seed(pg, plan)
        t = await day_titles(pg, D(monday))
        check("kp1: this week is Woche B (Krafttraining)", "Krafttraining" in t and "Atemtraining" not in t, t[:80])
        await pg.click("#todayWeekNext"); await pg.wait_for_timeout(200)
        t = await day_titles(pg, D(monday + datetime.timedelta(days=7)))
        check("kp1: next week is Woche A (Atemtraining)", "Atemtraining" in t, t[:80])
        await pg.click("#todayWeekPrev"); await pg.wait_for_timeout(200)
        line = await pg.inner_text("#todayPlanLine")
        check("kp15: plan line names phase + week", "Grundlage" in line and "(B)" in line, line)

        # multi-day entry from the editor
        await pg.click("#todayPlanBtn"); await pg.wait_for_timeout(200)
        await pg.click('[data-vsel="0:0"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-add="0/0:2"]'); await pg.wait_for_timeout(200)
        check("kp1: day picker shown for a new weekly entry", await pg.is_visible("#planEntryDays"))
        await pg.click('#planEntryDays [data-pick="all"]'); await pg.click("#planEntrySaveBtn"); await pg.wait_for_timeout(200)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp1: 'Jeden Tag' fills all 7 days of week A", all(len(d) >= 1 for d in pl["phases"][0]["days"]), str([len(d) for d in pl["phases"][0]["days"]]))
        # kp3: undo
        await pg.click("#planUndoBtn"); await pg.wait_for_timeout(200)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp3: Rückgängig restores the plan", [len(d) for d in pl["phases"][0]["days"]] == [1, 0, 0, 0, 0, 0, 0], str([len(d) for d in pl["phases"][0]["days"]]))
        # kp3: tray tap onto a day
        await pg.click('[data-tray-tab="area"]'); await pg.click('#planTrayItems [data-tray="0"]'); await pg.wait_for_timeout(100)
        check("kp3: tray armed (sticky) after choosing", await pg.evaluate("() => document.getElementById('planTray').classList.contains('armed')"))
        await pg.click('[data-add="0/0:3"]'); await pg.wait_for_timeout(200)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp3: tray item lands on Thursday", any(e["area"] == "visual" for e in pl["phases"][0]["days"][3]))
        # copy day
        await pg.click('#planTrayItems [data-tray="0"]')  # disarm
        await pg.click('[data-copyday="0/0:0"]'); await pg.click('[data-add="0/0:5"]'); await pg.wait_for_timeout(200)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp3: Tag kopieren copies Monday to Saturday", len(pl["phases"][0]["days"][5]) == 1 and pl["phases"][0]["days"][5][0]["id"] != "a1")
        check("no Entlastung switch (Fabian 07.10.)", await pg.locator("[data-phase-deload]").count() == 0)
        await pg.screenshot(path="screenshots/planung_editor.png", full_page=True)

        # ---- kp7: shifting pause moves the plan ----
        start = monday
        plan = {"startDate": D(start), "phases": [{"id": "p1", "name": "Aufbau", "weeks": 2, "days": [[E("x1")]] + [[]] * 6},
                                                  {"id": "p2", "name": "Spezial", "weeks": 2, "days": [[E("y1", "workout")]] + [[]] * 6}],
                "pauses": [{"id": "z", "from": D(monday + datetime.timedelta(days=7)), "to": D(monday + datetime.timedelta(days=13)), "reason": "urlaub", "shift": True}]}
        await seed(pg, plan)
        rows = await myplan_rows(pg)
        check("kp7: week 2 is the pause", "Pause" in rows[1], rows[1])
        check("kp7: plan resumes after the pause with Aufbau week 2", "Aufbau · Woche 2" in rows[2], rows[2])
        check("kp7: Spezial starts one week later", "Spezial" in rows[3], rows[3])
        await pg.screenshot(path="screenshots/planung_meinplan.png", full_page=True)
        # kp8: repeat week 1
        await pg.click(f'#myPlanList [data-week="{D(monday)}"]'); await pg.wait_for_timeout(200)
        await pg.click('#choiceList .choice-sheet-btn:has-text("Diese Woche wiederholen")'); await pg.wait_for_timeout(300)
        rows = await myplan_rows(pg) if not await pg.is_visible("#myPlanList") else await pg.evaluate("() => [...document.querySelectorAll('#myPlanList .myplan-week')].map(r => r.dataset.week + '|' + r.querySelector('.myplan-text').textContent)")
        check("kp8: repeat waits for the pause, then Aufbau week 1 again", "Woche 1" in rows[2] and "wiederholt" in rows[2], rows[2])
        # non-shifting pause: days empty, no plan move
        plan["pauses"][0]["shift"] = False
        plan["pauses"][0]["from"] = D(today); plan["pauses"][0]["to"] = D(today)
        plan["phases"][0]["days"] = [[E("x%d" % i)] for i in range(7)]
        await seed(pg, plan)
        t = await day_titles(pg, D(today))
        check("kp7: a day in a pause shows the pause, no training", "Pause" in t and "Atemtraining" not in t, t[:80])

        # ---- kp4: change only today ----
        plan = {"startDate": D(monday), "phases": [{"id": "p1", "name": "Basis", "weeks": 0, "days": [[E("w%d" % i, minutes=20)] for i in range(7)]}]}
        await seed(pg, plan)
        await day_titles(pg, D(today))
        await pg.click('#dayPanelBody .day-act[data-act="change"]'); await pg.wait_for_timeout(200)
        check("kp4: asks what the change applies to", await pg.is_visible("#choiceSheet") and "Wofür gilt das" in await pg.inner_text("#choiceTitle"))
        await pg.click('#choiceList .choice-sheet-btn:has-text("Nur an diesem Tag")'); await pg.wait_for_timeout(200)
        await pg.select_option("#planEntryMinutes", "45"); await pg.click("#planEntrySaveBtn"); await pg.wait_for_timeout(300)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp4: only today changed", pl["dayOv"].get(D(today), [{}])[0].get("minutes") == 45 and pl["phases"][0]["days"][today.weekday()][0]["minutes"] == 20)

        # ---- kp10: Sondertraining + Sonderwoche ----
        plan = {"startDate": D(monday), "phases": [{"id": "p1", "name": "Basis", "weeks": 0, "days": [[E("q1")]] + [[]] * 6}],
                "extras": {D(today): [E("s1", "visual", special="Sondertraining")]},
                "inserts": [{"id": "i1", "at": D(monday + datetime.timedelta(days=7)), "name": "Trainingslager", "days": [[E("c1", "cardio")]] + [[]] * 6}]}
        await seed(pg, plan)
        t = await day_titles(pg, D(today))
        check("kp10: special training with star", "★" in t and "Sondertraining" in t, t[:100])
        rows = await myplan_rows(pg)
        check("kp10: Sonderwoche in Mein Plan", "Trainingslager" in rows[1], rows[1])
        check("kp10: plan moves one week back", "Basis · Woche 2" in rows[2], rows[2])

        # ---- kp11: Wettkampf = recommendation only, minutes unchanged ----
        race = monday + datetime.timedelta(days=14 + 5)
        plan = {"startDate": D(monday), "phases": [{"id": "p1", "name": "Basis", "weeks": 0, "days": [[E("r%d" % i, minutes=30)] for i in range(7)]}]}
        await seed(pg, plan, {"fwmc-events-v1": [{"id": "ev", "date": D(race), "time": "", "title": "Stadtlauf", "kind": "wettkampf", "goal": True}]})
        rows = await myplan_rows(pg)
        check("kp11: week before shows a recommendation", any("Woche vor „Stadtlauf“" in r for r in rows), str(rows[:4]))
        await pg.click(".bar-back-btn:visible"); await pg.wait_for_timeout(200)
        await pg.click("#todayWeekNext"); await pg.wait_for_timeout(200)
        t = await day_titles(pg, D(monday + datetime.timedelta(days=7)))
        check("kp11: minutes stay as planned", "30 Min." in t, t[:80])

        # ---- kp2: week goal follows the plan, extras split ----
        plan = {"startDate": D(monday), "phases": [{"id": "p1", "name": "Basis", "weeks": 0, "days": [[E("g1")], [E("g2")], [], [], [], [], []]}]}
        ts = datetime.datetime.combine(monday, datetime.time(9)).isoformat()
        hist = [{"id": "h1", "ts": ts, "kind": "breath", "title": "Box-Atmung", "seconds": 300}, {"id": "h2", "ts": ts, "kind": "workout", "title": "Kraft", "seconds": 300}]
        await seed(pg, plan, {"fwmc-history-v1": hist})
        card = await pg.inner_text("#todayProgressCard") if await pg.locator("#todayProgressCard").count() else ""
        check("kp2: Heute goal = planned (1 von 2), extra counted", "1 von 2" in card and "1 zusätzlich" in card, card[:120])
        await pg.goto(BASE + "?bereich=fortschritt"); await pg.wait_for_timeout(400)
        wt = await pg.inner_text("#progressWeekText")
        check("kp2: Fortschritt text names the plan goal", "1 von 2 geplanten" in wt, wt)

        # ---- kp13: plan per code ----
        served["plan-tina"] = {"type": "training-plan", "version": 1, "plan": {"phases": [{"id": "t1", "name": "Grundlage vom Trainer", "weeks": 4, "days": [[{"id": "e1", "area": "nat", "what": "nat:remember", "minutes": 10, "time": "07:00"}]] + [[]] * 6}]}}
        await seed(pg, None, {"fwmc-progress-v1": {"weekGoal": 3, "days": {}}})
        await pg.click(".today-code .code-toggle") if await pg.locator(".today-code .code-toggle").count() else None
        await pg.fill("#todayCodeInput", "plan-tina"); await pg.click("#todayCodeGoBtn"); await pg.wait_for_timeout(600)
        check("kp13: asks before taking over", await pg.is_visible("#confirmSheet") and "Trainer" in await pg.inner_text("#confirmTitle"), await pg.inner_text("#confirmSheet") if await pg.is_visible("#confirmSheet") else "")
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(400)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp13: plan taken over with source", pl and pl["phases"][0]["name"] == "Grundlage vom Trainer" and pl["source"]["code"] == "plan-tina")
        # client changes the time, trainer publishes v2: own time survives
        pl["phases"][0]["days"][0][0]["time"] = "18:30"
        await pg.evaluate("(p) => localStorage.setItem('fwmc-plan-v1', JSON.stringify(p))", pl)
        served["plan-tina"]["version"] = 2
        served["plan-tina"]["plan"]["phases"][0]["days"][1] = [{"id": "e2", "area": "breath", "minutes": 5}]
        await pg.evaluate("() => localStorage.removeItem('fwmc-plan-check-v1')")
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(3500)
        check("kp21: Heute offers the new version", await pg.is_visible("#todayPlanUpdate"))
        await pg.click("#planUpdateTakeBtn"); await pg.wait_for_timeout(600)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(400)
        pl = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("kp21: version 2 taken, own time kept", pl["source"]["version"] == 2 and pl["phases"][0]["days"][0][0]["time"] == "18:30" and len(pl["phases"][0]["days"][1]) == 1, json.dumps(pl["phases"][0]["days"][:2]))

        # layout: no sideways scroll, buttons >= 44 px on the new screens
        for scr in ["#todayPlanBtn", "#todayMyPlanBtn"]:
            await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(300)
            await pg.click(scr); await pg.wait_for_timeout(300)
            over = await pg.evaluate("() => document.documentElement.scrollWidth > innerWidth")
            small = await pg.evaluate("() => [...document.querySelectorAll('.screen:not([hidden]) button')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44 && !b.classList.contains('text-link') && !b.classList.contains('plan-item-btn')).map(b => b.textContent.trim()).slice(0, 5)")
            check(f"{scr}: no sideways scroll", not over)
            check(f"{scr}: buttons >= 44 px", not small, str(small))
        await pg.emulate_media(color_scheme="dark")
        await pg.screenshot(path="screenshots/planung_meinplan_dark.png", full_page=True)
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
