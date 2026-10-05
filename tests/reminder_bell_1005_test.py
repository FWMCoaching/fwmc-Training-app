import asyncio, json, datetime
from playwright.async_api import async_playwright

# Glocke an Trainings mit Erinnerung (Fabian 2026-10-05): with reminders on,
# open upcoming trainings on Heute carry a small bell; off = no bell; done
# trainings and own appointments never get one.
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def main():
    errors = []
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    tomorrow = (today + datetime.timedelta(days=1)).isoformat()
    days = [[] for _ in range(7)]
    plan = {"startDate": monday.isoformat(), "phases": [{"id": "p1", "name": "Phase 1", "weeks": 0, "days": days}],
            "extras": {tomorrow: [{"id": "x1", "area": "breath", "what": "", "code": "", "time": "10:00", "minutes": 10}]},
            "skips": {}, "done": {}}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for on in [True, False]:
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            st = {"fwmc-tips-seen": "true", "fwmc-plan-v1": json.dumps(plan), "fwmc-test-reminder-key": json.dumps("BKEY"),
                  "fwmc-reminders-v1": json.dumps({"on": on, "lead": 10, "morning": "08:00"}),
                  "fwmc-events-v1": json.dumps([{"id": "e1", "date": tomorrow, "time": "12:00", "title": "Physio", "minutes": 30}])}
            await ctx.add_init_script("".join(f"localStorage.setItem({json.dumps(k)},{json.dumps(v)});" for k, v in st.items()))
            await ctx.route("**/reminders", lambda r: r.fulfill(status=200, body='{"ok":true,"count":1}', headers={"content-type": "application/json", "access-control-allow-origin": "*"}))
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            await pg.goto(BASE); await pg.wait_for_timeout(500)
            await pg.click(f'.week-day[data-date="{tomorrow}"]') if await pg.locator(f'.week-day[data-date="{tomorrow}"]').count() else await pg.click('[data-week-step="1"], #todayWeekNext')
            if not await pg.locator(f'.week-day[data-date="{tomorrow}"].selected').count():
                await pg.click(f'.week-day[data-date="{tomorrow}"]')
            await pg.wait_for_timeout(200)
            n = await pg.locator("#dayPanelBody .rem-bell, .day-panel .rem-bell").count()
            if on:
                check("bell on the planned training when reminders are on", n == 1, n)
                check("no bell on own appointments", await pg.evaluate("[...document.querySelectorAll('.rem-bell')].every(b => b.closest('.day-item'))"))
                await pg.locator(".rem-bell").first.evaluate("e => e.closest('.day-item').scrollIntoView({block:'center'})"); await pg.locator(".rem-bell").first.evaluate("e => 0"); await pg.locator(".day-item:has(.rem-bell)").first.screenshot(path="reminder_bell_on.png")
            else:
                check("no bell when reminders are off", n == 0, n)
            await ctx.close()
        await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
