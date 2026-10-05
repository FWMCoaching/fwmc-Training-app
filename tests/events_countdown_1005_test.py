import asyncio, datetime, json
from playwright.async_api import async_playwright

# Eigene Termine + Countdown (Fabian, 2026-10-05): Wettkampf, Spiel,
# Vereinstraining, Massage, Ruhetag in den Kalender; ein Termin als
# "großes Ziel" zeigt auf Heute einen Countdown.
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

today = datetime.date.today()
in10 = (today + datetime.timedelta(days=10)).isoformat()
in3 = (today + datetime.timedelta(days=3)).isoformat()

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for vw, vh, scheme in [(390, 844, "light"), (1024, 768, "dark")]:
            t = f"[{vw} {scheme}] "
            ctx = await b.new_context(viewport={"width": vw, "height": vh}, color_scheme=scheme, service_workers="block")
            await ctx.add_init_script(INIT)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            await pg.goto(BASE); await pg.wait_for_timeout(300)
            check(t + "no countdown without a goal", not await pg.is_visible("#todayCountdown"))
            check(t + "Termin button on the day panel", await pg.is_visible("#dayEventAddBtn"))
            # empty title -> error, nothing saved
            await pg.click("#dayEventAddBtn"); await pg.wait_for_timeout(150)
            check(t + "sheet opens", await pg.is_visible("#eventSheet"))
            check(t + "date defaults to the selected day", await pg.input_value("#eventDateInput") == today.isoformat())
            check(t + "four kinds", await pg.locator("#eventKindRow .choice").count() == 4)
            await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(100)
            check(t + "empty title shows an error", await pg.is_visible("#eventError"))
            check(t + "nothing saved", await pg.evaluate("localStorage.getItem('fwmc-events-v1')") is None)
            # goal event in 10 days
            await pg.fill("#eventTitleInput", "Halbmarathon Paderborn")
            await pg.fill("#eventDateInput", in10)
            await pg.fill("#eventTimeInput", "09:30")
            await pg.check("#eventGoalToggle")
            await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(200)
            check(t + "sheet closes", not await pg.is_visible("#eventSheet"))
            ev = json.loads(await pg.evaluate("localStorage.getItem('fwmc-events-v1')"))
            check(t + "saved with kind and goal", len(ev) == 1 and ev[0]["kind"] == "wettkampf" and ev[0]["goal"] and ev[0]["time"] == "09:30", ev)
            check(t + "day panel jumps to the event day and lists it", "Halbmarathon" in await pg.inner_text("#dayEvents"))
            await pg.reload(); await pg.wait_for_timeout(300)
            check(t + "countdown shows after reload", await pg.is_visible("#todayCountdown"))
            txt = await pg.inner_text("#todayCountdown")
            check(t + "countdown says 10 days", "Noch 10 Tage" in txt and "Halbmarathon Paderborn" in txt, txt)
            # a second, nearer non-goal event does not replace the countdown
            await pg.click("#dayEventAddBtn"); await pg.wait_for_timeout(100)
            await pg.fill("#eventTitleInput", "Massage")
            await pg.fill("#eventDateInput", in3)
            await pg.click('#eventKindRow [data-kind="erholung"]')
            await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(200)
            check(t + "countdown keeps the goal", "Halbmarathon" in await pg.inner_text("#todayCountdown"))
            # week strip / calendar marker
            await pg.click("#calMonthBtn"); await pg.wait_for_timeout(150)
            marks = await pg.locator(f'#calExpand .cal-cell[data-date="{in3}"] .event-mark').count()
            check(t + "calendar marks the event day", marks == 1)
            lbl = await pg.get_attribute(f'#calExpand .cal-cell[data-date="{in3}"]', "aria-label")
            check(t + "calendar label names the event", "1 Termin" in (lbl or ""), lbl)
            # edit -> becomes goal and nearer -> countdown switches
            await pg.click(f'#calExpand .cal-cell[data-date="{in3}"]'); await pg.wait_for_timeout(150)
            await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
            check(t + "edit mode", (await pg.inner_text("#eventSheetTitle")) == "Termin bearbeiten" and await pg.input_value("#eventTitleInput") == "Massage")
            check(t + "kind kept", await pg.get_attribute('#eventKindRow [data-kind="erholung"]', "aria-pressed") == "true")
            await pg.check("#eventGoalToggle"); await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(200)
            check(t + "nearest goal wins", "Massage" in await pg.inner_text("#todayCountdown") and "Noch 3 Tage" in await pg.inner_text("#todayCountdown"))
            check(t + "still two events", len(json.loads(await pg.evaluate("localStorage.getItem('fwmc-events-v1')"))) == 2)
            # countdown button jumps to the day
            await pg.click("#countdownShowBtn"); await pg.wait_for_timeout(200)
            check(t + "Im Kalender zeigen selects the day", "Massage" in await pg.inner_text("#dayEvents"))
            # delete with confirmation
            await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
            await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
            check(t + "delete asks first", await pg.is_visible("#confirmSheet"))
            await pg.click("#confirmYesBtn") if await pg.locator("#confirmYesBtn").count() else await pg.click("#confirmOkBtn")
            await pg.wait_for_timeout(200)
            check(t + "deleted", len(json.loads(await pg.evaluate("localStorage.getItem('fwmc-events-v1')"))) == 1)
            check(t + "countdown falls back to the other goal", "Halbmarathon" in await pg.inner_text("#todayCountdown"))
            # today goal
            await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', JSON.stringify([{{id:'x',date:'{today.isoformat()}',time:'',title:'Spiel',kind:'wettkampf',goal:true}}]))")
            await pg.reload(); await pg.wait_for_timeout(300)
            check(t + "today: so weit", "Heute ist es so weit" in await pg.inner_text("#todayCountdown"))
            check(t + "week strip marks today", await pg.locator(f'#todayWeekStrip [data-date="{today.isoformat()}"] .event-mark').count() == 1)
            # a past goal disappears
            past = (today - datetime.timedelta(days=1)).isoformat()
            await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', JSON.stringify([{{id:'x',date:'{past}',time:'',title:'Alt',kind:'wettkampf',goal:true}}]))")
            await pg.reload(); await pg.wait_for_timeout(300)
            check(t + "past goal: no countdown", not await pg.is_visible("#todayCountdown"))
            # broken storage never throws
            await pg.evaluate("localStorage.setItem('fwmc-events-v1', '{\"bad\":1}')")
            await pg.reload(); await pg.wait_for_timeout(300)
            check(t + "broken storage: page still renders", await pg.is_visible("#todayMain"))
            # tap sizes in the sheet
            await pg.click("#dayEventAddBtn"); await pg.wait_for_timeout(150)
            small = await pg.evaluate("""() => [...document.querySelectorAll('#eventSheet button, #eventSheet input')].filter(e => e.offsetParent && e.type !== 'checkbox').map(e => [e.id || e.textContent.trim(), Math.round(e.getBoundingClientRect().height)]).filter(x => x[1] < 44)""")
            check(t + "sheet tap targets >= 44 px", not small, small)
            await pg.screenshot(path=f"events_sheet_{vw}_{scheme}.png")
            await ctx.close()
        await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
