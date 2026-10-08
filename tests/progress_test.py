"""Mein Fortschritt (Fabian, 2026-10-03): weekly goal, week streak,
milestones, 8-week chart and areas across the last 4 weeks. Seeded once
from the history, aborted runs never count, numbers survive the 200-entry
history cap, a finished run adds to it, the goal persists, no overlaps."""
import asyncio, json
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


def iso(d):
    return d.strftime("%Y-%m-%dT12:00:00.000Z")


now = datetime.now()
monday = (now - timedelta(days=now.weekday())).replace(hour=12, minute=0, second=0, microsecond=0)
hist = []
# this week: 2 visual + 1 breath (goal 3 -> reached), plus 1 aborted that must not count
for i, kind in enumerate(["exercise", "exercise", "breath"]):
    hist.append({"id": f"t{i}", "ts": iso(monday), "kind": kind, "exId": "vt-color", "title": "X", "seconds": 300})
hist.append({"id": "ab", "ts": iso(monday), "kind": "exercise", "exId": "vt-color", "title": "Abgebr.", "seconds": 60, "aborted": True})
# last week: 3 workout (reached), the week before: 3 cardio (reached), 3 weeks ago: 1 only (breaks streak)
for back, kind, n in [(1, "workout", 3), (2, "cardio-plan", 3), (3, "movement", 1)]:
    for i in range(n):
        hist.append({"id": f"w{back}{i}", "ts": iso(monday - timedelta(days=7 * back)), "kind": kind, "title": "Y", "seconds": 600})
TOTAL = 3 + 3 + 3 + 1  # 10, aborted excluded


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        seed = json.dumps(hist)
        await ctx.add_init_script(f"""if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded','1');
          localStorage.setItem('fwmc-tips-seen','true');
          localStorage.setItem('fwmc-history-v1', JSON.stringify({seed})); }}""")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text else None)
        await pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
        await pg.goto(BASE); await pg.wait_for_timeout(500)

        card = await pg.inner_text("#todayProgressCard")
        check("Heute card: week 3 of 3", "3 von 3" in card, card)
        check("Heute card: streak 3 weeks", "3 Wochen" in card)
        check("Heute card: total without aborted", str(TOTAL) in card)
        await pg.click("#todayProgressOpenBtn"); await pg.wait_for_timeout(200)
        check("progress screen opens", await pg.is_visible("#progressScreen") and await pg.is_hidden("#todayHome"))
        check("goal text", "3 Trainings pro Woche" in await pg.inner_text("#progressGoalValue"))
        check("goal reached text", "Ziel erreicht" in await pg.inner_text("#progressWeekText"))
        stats = await pg.inner_text("#progressStats")
        check("stats: streak + longest + total", stats.count("3 Wochen") == 2 and str(TOTAL) in stats, stats)
        check("8 week bars", await pg.locator("#progressWeeks .progress-week").count() == 8)
        check("3 weeks marked reached", await pg.locator("#progressWeeks .progress-week.reached").count() == 3)
        areas = await pg.inner_text("#progressAreas")
        check("areas list all trained areas", all(a in areas for a in ["Visuelles Training", "Atemtraining", "Krafttraining", "Ausdauertraining", "Reaktionstraining"]), areas)
        check("milestones 1/5/10 reached", await pg.locator(".progress-milestone.reached").count() == 3)
        check("next milestone text", "15 Trainings bis zum nächsten Meilenstein (25)" in await pg.inner_text("#progressNextText"))

        # goal up -> this week no longer reached, streak drops to 0 (old weeks had 3 < 4)
        await pg.click("#progressGoalPlus"); await pg.wait_for_timeout(150)
        check("goal up to 4", "4 Trainings" in await pg.inner_text("#progressGoalValue"))
        check("week not reached at goal 4", "Noch 1 bis zum Ziel" in await pg.inner_text("#progressWeekText"))
        check("streak 0 at goal 4", "0 Wochen" in await pg.inner_text("#progressStats"))
        for _ in range(20):
            if await pg.is_disabled("#progressGoalPlus"):
                break
            await pg.click("#progressGoalPlus")
        check("goal capped at 14", "14 Trainings" in await pg.inner_text("#progressGoalValue") and await pg.is_disabled("#progressGoalPlus"))
        for _ in range(20):
            if await pg.is_disabled("#progressGoalMinus"):
                break
            await pg.click("#progressGoalMinus")
        check("goal floor 1", "1 Training pro Woche" in await pg.inner_text("#progressGoalValue"))
        await pg.click("#progressGoalPlus"); await pg.click("#progressGoalPlus")  # back to 3

        # no horizontal scroll, no overlapping text in the chart/areas
        sw = await pg.evaluate("document.documentElement.scrollWidth")
        check("no horizontal scroll", sw <= 390)
        ov = await pg.evaluate("""() => {
          const els = [...document.querySelectorAll('#progressWeeks .progress-week-label, #progressAreas .progress-area-name, #progressAreas .progress-area-n, .progress-milestone')];
          const r = els.map(e => e.getBoundingClientRect());
          for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) {
            const a = r[i], c = r[j];
            if (a.left < c.right - 1 && c.left < a.right - 1 && a.top < c.bottom - 1 && c.top < a.bottom - 1) return true;
          }
          return false; }""")
        check("no overlapping labels", not ov)

        # history gets trimmed (cap) -> lifetime numbers stay
        await pg.evaluate("localStorage.setItem('fwmc-history-v1', '[]')")
        await pg.reload(); await pg.wait_for_timeout(400)
        check("goal persisted", "3 von 3" in await pg.inner_text("#todayProgressCard"))
        check("total survives a trimmed history", str(TOTAL) in await pg.inner_text("#todayProgressCard"))

        # a real finished run adds one (short coach programme, natural end)
        await pg.route("**/program?code=*", lambda r: r.fulfill(status=200, content_type="application/json",
                       body=json.dumps({"name": "Kurz", "blocks": [{"exercise": "vt-color", "duration": 15}]})))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.fill("#programCodeInput", "kurz-test")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(500)
        await pg.click("#programStartBtn"); await pg.wait_for_timeout(500)
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(500)
        check("programme finished", await pg.is_visible("#programDonePanel"))
        await pg.click("#programDoneBackBtn"); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="today"]'); await pg.wait_for_timeout(300)
        card = await pg.inner_text("#todayProgressCard")
        # Since 07.10. (Trainingsplanung, 87e61a4) the week shows at most the goal
        # ("3 von 3 ✓") and anything beyond it as "· 1 zusätzlich" (weekGoalInfo:
        # more is shown but never rewarded) - was "4 von 3". Updated 08.10.
        check("finished run counted", "3 von 3" in card and "1 zusätzlich" in card and str(TOTAL + 1) in card, card)

        await pg.click("#todayProgressOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#progressBackBtn"); await pg.wait_for_timeout(200)
        check("back to Heute", await pg.is_visible("#todayHome"))

        check("no page errors", not errors, errors[:3])
        await b.close()
    bad = [n for n, ok in results if not ok]
    print("FAILED:", bad if bad else "none")


asyncio.run(main())
