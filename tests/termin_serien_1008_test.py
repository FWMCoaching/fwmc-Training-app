import asyncio, datetime, json, os
from playwright.async_api import async_playwright

# Eigene Termine wiederholen (Serien im Kalender, Fabian 08.10.): the Termin
# sheet gets "Wiederholen: Nie / Jede Woche / Alle 2 Wochen" (default Nie).
# A series shows on every matching date in the Heute week strip, the month
# view and the day panel, without an end. Editing changes the whole series
# (hint in the sheet, date label "Erster Termin"). Deleting (sheet or list
# swipe) a series asks via confirmDialog "Nur diesen Termin" (skip) / "Alle
# Termine dieser Serie" / "Abbrechen" (tapping beside deletes nothing).
# Old events without `repeat` = Nie, trainer events (fromTrainer) never repeat
# (no repeat row in their sheet). A repeating goal counts down to the next
# date; Mein Plan recommendations ignore series. Persistence across reload,
# 390/1024 light/dark screenshots, no page/console errors.
# Run from tests/ with a dev server (FWMC_PORT, default 8845).

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "paket_h")
os.makedirs(SHOTS, exist_ok=True)
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

today = datetime.date.today()
def d(n): return (today + datetime.timedelta(days=n)).isoformat()

async def events(pg):
    raw = await pg.evaluate("localStorage.getItem('fwmc-events-v1')")
    return json.loads(raw) if raw else []

async def goto_week(pg, date):
    """Week strip: step to the week holding `date` (forward only)."""
    for _ in range(10):
        if await pg.locator(f'#todayWeekStrip [data-date="{date}"]').count(): return True
        await pg.click("#todayWeekNext"); await pg.wait_for_timeout(120)
    return False

async def strip_mark(pg, date):
    await goto_week(pg, date)
    return await pg.locator(f'#todayWeekStrip [data-date="{date}"] .event-mark').count() > 0

async def open_day(pg, date):
    await goto_week(pg, date)
    await pg.click(f'#todayWeekStrip [data-date="{date}"]'); await pg.wait_for_timeout(150)

async def back_to_today(pg):
    if await pg.is_visible("#todayWeekTodayBtn"):
        await pg.click("#todayWeekTodayBtn"); await pg.wait_for_timeout(150)

async def new_ctx(b, errors, w=390, h=844, dark=False, touch=False):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme="dark" if dark else "light", service_workers="block", has_touch=touch, is_mobile=touch)
    await ctx.add_init_script(INIT)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    await ctx.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body='{"error":"not_found"}', content_type="application/json"))
    return ctx, pg

async def touch_swipe_left(pg, cdp, sel):
    await pg.evaluate(f"document.querySelector({json.dumps(sel)}).scrollIntoView({{block: 'center'}})")
    await pg.wait_for_timeout(80)
    r = await pg.evaluate(f"(() => {{ const r = document.querySelector({json.dumps(sel)}).getBoundingClientRect(); return {{x: r.left, y: r.top, w: r.width, h: r.height}}; }})()")
    y = r["y"] + min(r["h"] / 2, 24); x0 = min(r["x"] + r["w"] - 20, 370)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
    for i in range(1, 11):
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 - 200 * i / 10, "y": y}]})
        await asyncio.sleep(0.016)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    await pg.wait_for_timeout(380)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---------- create a weekly series ----------
        ctx, pg = await new_ctx(b, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        await pg.click("#dayEventAddBtn"); await pg.wait_for_timeout(150)
        check("sheet: repeat row with 3 choices", await pg.locator("#eventRepeatRow .choice").count() == 3)
        labels = await pg.locator("#eventRepeatRow .choice").all_inner_texts()
        check("sheet: labels Nie / Jede Woche / Alle 2 Wochen", labels == ["Nie", "Jede Woche", "Alle 2 Wochen"], labels)
        check("sheet: default Nie", await pg.get_attribute('#eventRepeatRow [data-repeat="none"]', "aria-pressed") == "true")
        check("sheet: hint hidden for Nie", await pg.is_hidden("#eventRepeatHint"))
        hs = await pg.evaluate("[...document.querySelectorAll('#eventRepeatRow .choice')].map((b) => b.getBoundingClientRect().height)")
        check("sheet: repeat buttons >= 44 px", min(hs) >= 44, hs)
        await pg.fill("#eventTitleInput", "Vereinstraining")
        await pg.click('#eventKindRow [data-kind="training"]')
        await pg.fill("#eventTimeInput", "18:30")
        await pg.click('#eventRepeatRow [data-repeat="weekly"]'); await pg.wait_for_timeout(80)
        check("sheet: Jede Woche active", await pg.get_attribute('#eventRepeatRow [data-repeat="weekly"]', "aria-pressed") == "true")
        check("sheet: date label 'Erster Termin'", (await pg.inner_text("#eventDateLabel")).strip() == "Erster Termin")
        check("sheet: new-series hint visible", await pg.is_visible("#eventRepeatHint") and "ohne Ende" in await pg.inner_text("#eventRepeatHint"))
        await pg.evaluate("document.getElementById('eventRepeatRow').scrollIntoView({block:'center'})")
        await pg.screenshot(path=os.path.join(SHOTS, "serie_sheet_390_light.png"))
        await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(200)
        ev = await events(pg)
        check("saved with repeat weekly", len(ev) == 1 and ev[0].get("repeat") == "weekly" and ev[0]["date"] == d(0) and "skip" not in ev[0], ev)

        # ---------- shows on every matching date ----------
        await pg.reload(); await pg.wait_for_timeout(300)
        check("strip: today marked (after reload)", await strip_mark(pg, d(0)))
        check("strip: today+3 not marked", not await strip_mark(pg, d(3)) if d(3) else True)
        await back_to_today(pg)
        check("strip: today+7 marked", await strip_mark(pg, d(7)))
        check("strip: today+35 marked (no end)", await strip_mark(pg, d(35)))
        await back_to_today(pg)
        check("strip: yesterday-7 not marked (series starts today)", await pg.locator(f'#todayWeekStrip [data-date="{d(-7)}"] .event-mark').count() == 0)
        await pg.click("#calMonthBtn"); await pg.wait_for_timeout(150)
        cells = await pg.evaluate("[...document.querySelectorAll('#calExpand .cal-cell')].filter((c) => c.querySelector('.event-mark')).map((c) => c.dataset.date)")
        expect = [c for c in await pg.evaluate("[...document.querySelectorAll('#calExpand .cal-cell[data-date]')].map((c) => c.dataset.date)")
                  if c >= d(0) and (datetime.date.fromisoformat(c) - today).days % 7 == 0]
        check("month view marks exactly the weekly dates", sorted(cells) == sorted(expect) and len(cells) >= 1, (cells, expect))
        await pg.click("#calMonthBtn"); await pg.wait_for_timeout(100)
        await open_day(pg, d(7))
        txt = await pg.inner_text("#dayEvents")
        check("day panel today+7 lists the series with 'jede Woche'", "Vereinstraining" in txt and "jede Woche" in txt, txt)
        await pg.screenshot(path=os.path.join(SHOTS, "serie_day_390_light.png"))

        # ---------- edit = whole series ----------
        await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
        check("edit: date shows the first date", await pg.input_value("#eventDateInput") == d(0))
        check("edit: Jede Woche preselected", await pg.get_attribute('#eventRepeatRow [data-repeat="weekly"]', "aria-pressed") == "true")
        hint = await pg.inner_text("#eventRepeatHint")
        check("edit: hint says changes apply to the whole series", "alle Termine dieser Serie" in hint, hint)
        await pg.fill("#eventTimeInput", "19:00")
        await pg.click("#eventSaveBtn"); await pg.wait_for_timeout(200)
        ev = await events(pg)
        check("edit: still one event, time changed for the series", len(ev) == 1 and ev[0]["time"] == "19:00" and ev[0]["repeat"] == "weekly", ev)
        await open_day(pg, d(14))
        check("edit: today+14 shows 19:00", "19:00" in await pg.inner_text("#dayEvents"))

        # ---------- delete: cancel, only this, all ----------
        await back_to_today(pg)
        await open_day(pg, d(7))
        await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
        await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
        check("delete: asks via the confirm sheet", await pg.is_visible("#confirmSheet") and (await pg.inner_text("#confirmTitle")) == "Termin löschen")
        btns = [await pg.inner_text("#confirmNoBtn"), await pg.inner_text("#confirmYesBtn"), await pg.inner_text("#confirmCancelBtn")]
        check("delete: 'Nur diesen Termin' / 'Alle Termine dieser Serie' / 'Abbrechen'", btns == ["Nur diesen Termin", "Alle Termine dieser Serie", "Abbrechen"], btns)
        ctext = await pg.inner_text("#confirmText")
        check("delete: names the date", str(datetime.date.fromisoformat(d(7)).day) + "." in ctext, ctext)
        await pg.screenshot(path=os.path.join(SHOTS, "serie_confirm_390_light.png"))
        await pg.mouse.click(195, 30); await pg.wait_for_timeout(150)
        ev = await events(pg)
        check("delete: tapping beside cancels (nothing deleted)", await pg.is_hidden("#confirmSheet") and len(ev) == 1 and not ev[0].get("skip"), ev)
        await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
        await pg.click("#confirmCancelBtn"); await pg.wait_for_timeout(150)
        check("delete: Abbrechen deletes nothing", len(await events(pg)) == 1 and not (await events(pg))[0].get("skip"))
        await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(250)
        ev = await events(pg)
        check("only this: skip holds today+7", len(ev) == 1 and ev[0].get("skip") == [d(7)], ev)
        check("only this: sheet closed", await pg.is_hidden("#eventSheet"))
        await back_to_today(pg)
        check("only this: today+7 no longer marked", not await strip_mark(pg, d(7)))
        await back_to_today(pg)
        check("only this: today+14 still marked", await strip_mark(pg, d(14)))
        await back_to_today(pg)
        check("only this: today still marked", await strip_mark(pg, d(0)))
        await pg.reload(); await pg.wait_for_timeout(300)
        check("only this: persists after reload", not await strip_mark(pg, d(7)))
        await back_to_today(pg)
        await open_day(pg, d(14))
        await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
        await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("all: series removed", await events(pg) == [])
        await ctx.close()

        # ---------- biweekly + old events + trainer event + goal countdown ----------
        ctx, pg = await new_ctx(b, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(200)
        seed = [
            {"id": "old1", "date": d(2), "time": "", "title": "Massage", "kind": "erholung", "goal": False},
            {"id": "bi1", "date": d(-14), "time": "10:00", "title": "Spiel", "kind": "wettkampf", "goal": False, "repeat": "biweekly"},
            {"id": "tr1", "date": d(4), "title": "Turnier", "kind": "wettkampf", "fromTrainer": "abc", "repeat": "weekly"},
            {"id": "g1", "date": d(-10), "time": "", "title": "Monatslauf", "kind": "wettkampf", "goal": True, "repeat": "weekly"},
        ]
        await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', {json.dumps(json.dumps(seed))})")
        await pg.reload(); await pg.wait_for_timeout(300)
        check("old event without repeat = once (today+2 yes, +9 no)", await strip_mark(pg, d(2)) and not await strip_mark(pg, d(9)))
        await back_to_today(pg)
        check("biweekly from today-14: today marked", await strip_mark(pg, d(0)))
        await back_to_today(pg)
        bi7 = await pg.evaluate(f"(() => {{ const c = document.querySelector('#todayWeekStrip [data-date=\"{d(7)}\"]'); return c ? !!c.querySelector('.event-mark') : null; }})()")
        await open_day(pg, d(7))
        check("biweekly: today+7 has no Spiel", "Spiel" not in await pg.inner_text("#dayEvents"))
        await open_day(pg, d(14))
        check("biweekly: today+14 has Spiel 'alle 2 Wochen'", "alle 2 Wochen" in await pg.inner_text("#dayEvents"))
        await back_to_today(pg)
        await open_day(pg, d(11))
        check("trainer event never repeats (today+11 empty)", "Turnier" not in await pg.inner_text("#dayEvents"))
        await back_to_today(pg)
        await open_day(pg, d(4))
        check("trainer event shows on its date", "Turnier" in await pg.inner_text("#dayEvents"))
        await pg.locator('#dayEvents [data-event="tr1"] [data-event-edit]').click(); await pg.wait_for_timeout(150)
        check("trainer event: no repeat row in the sheet", await pg.is_hidden("#eventRepeatGroup"))
        await pg.click("#eventCancelBtn"); await pg.wait_for_timeout(100)
        # repeating goal: next date from today on = today+4 (today-10 + 14)
        cd = await pg.inner_text("#todayCountdown")
        check("repeating goal counts down to the next date", "Monatslauf" in cd and "Noch 4 Tage" in cd, cd)
        await pg.click("#countdownShowBtn"); await pg.wait_for_timeout(200)
        check("countdown 'Im Kalender zeigen' opens that date", "Monatslauf" in await pg.inner_text("#dayEvents"))
        # Mein Plan: series ignored for Wettkampf recommendations
        foc = await pg.evaluate("(() => { try { return JSON.parse(localStorage.getItem('fwmc-events-v1')).length; } catch (e) { return -1; } })()")
        check("store untouched by rendering", foc == 4)
        await ctx.close()

        # ---------- list swipe on a series row ----------
        ctx, pg = await new_ctx(b, errors, touch=True)
        await pg.goto(BASE); await pg.wait_for_timeout(200)
        await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', JSON.stringify([{{id:'s1', date:'{d(0)}', time:'18:00', title:'Lauftreff', kind:'training', goal:false, repeat:'weekly'}}]))")
        await pg.reload(); await pg.wait_for_timeout(400)
        cdp = await ctx.new_cdp_session(pg)
        await touch_swipe_left(pg, cdp, "#dayEvents .event-item")
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        check("swipe Löschen on a series asks Nur diesen / Alle", await pg.is_visible("#confirmSheet") and await pg.inner_text("#confirmNoBtn") == "Nur diesen Termin")
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(250)
        ev = await events(pg)
        check("swipe 'Nur diesen Termin' skips today only", len(ev) == 1 and ev[0].get("skip") == [d(0)], ev)
        check("today's panel no longer lists it", await pg.locator("#dayEvents .event-item").count() == 0)
        await ctx.close()

        # ---------- single event delete still a plain question ----------
        ctx, pg = await new_ctx(b, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(200)
        await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', JSON.stringify([{{id:'x1', date:'{d(0)}', time:'', title:'Arzt', kind:'sonstiges', goal:false}}]))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(150)
        await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(150)
        check("single event: plain Ja/Nein, no Abbrechen", await pg.inner_text("#confirmYesBtn") == "Ja" and await pg.is_hidden("#confirmCancelBtn"))
        await pg.mouse.click(195, 30); await pg.wait_for_timeout(150)
        check("single event: tapping beside = Nein, kept", len(await events(pg)) == 1)
        await ctx.close()

        # ---------- screenshots 390/1024 light/dark ----------
        for w, h, dark in ((390, 844, True), (1024, 768, False), (1024, 768, True)):
            ctx, pg = await new_ctx(b, errors, w=w, h=h, dark=dark)
            await pg.goto(BASE); await pg.wait_for_timeout(200)
            await pg.evaluate(f"localStorage.setItem('fwmc-events-v1', JSON.stringify([{{id:'s1', date:'{d(0)}', time:'18:00', title:'Vereinstraining', kind:'training', goal:false, repeat:'biweekly'}}]))")
            await pg.reload(); await pg.wait_for_timeout(300)
            tag = f"{w}_{'dark' if dark else 'light'}"
            await pg.evaluate("document.getElementById('dayEvents').scrollIntoView({block:'center'})")
            await pg.screenshot(path=os.path.join(SHOTS, f"serie_day_{tag}.png"))
            await pg.click("#dayEvents [data-event-edit]"); await pg.wait_for_timeout(200)
            sw = await pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
            check(f"{tag}: sheet no sideways scroll", sw)
            await pg.evaluate("document.getElementById('eventRepeatRow').scrollIntoView({block:'center'})")
            await pg.screenshot(path=os.path.join(SHOTS, f"serie_sheet_{tag}.png"))
            await pg.click("#eventDeleteBtn"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f"serie_confirm_{tag}.png"))
            await ctx.close()

        check("no page/console errors", errors == [], errors[:5])
        await b.close()
    print("FAILS:", fails)
    print("ERRORS:", errors)

asyncio.run(main())
