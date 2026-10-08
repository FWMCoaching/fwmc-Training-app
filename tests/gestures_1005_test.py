import asyncio, json, os
from playwright.async_api import async_playwright

# Gesten (Fabian, 2026-10-05): 1) tap the active bottom-bar tab again =
# scroll to top / back to the tab's own page, 2) swipe the Heute calendar
# sideways = ‹ / ›, 3) drag ≡ to reorder Kombi-Bausteine (pause travels
# along) and checklist points of "Eigenes Training", 4) long press on area
# tiles / exercise cards = action sheet (Direkt starten / Öffnen, In den
# Wochenplan, Zum Kombi-Programm, Abbrechen).
HOST = os.environ.get("FWMC_BASE", "http://localhost:8845")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
        "localStorage.setItem('fwmc-test-bottomnav','true');"
        "localStorage.setItem('fwmc-test-natmodes','true');")
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def touch_drag(cdp, x0, y0, x1, y1, steps=8, pause=0.015):
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / steps, "y": y0 + (y1 - y0) * i / steps}]})
        await asyncio.sleep(pause)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

async def press(cdp, x, y, ms, move=0):
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    if move:
        await asyncio.sleep(0.1)
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y + move}]})
    await asyncio.sleep(ms / 1000)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

async def center(pg, sel):
    return await pg.evaluate(f"(() => {{ const r = document.querySelector({json.dumps(sel)}).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }})()")

async def handle_at(pg, row_sel, i):
    return await pg.evaluate(f"(() => {{ const r = document.querySelectorAll({json.dumps(row_sel)})[{i}].querySelector('.drag-handle').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }})()")

async def visible_screen(pg):
    return await pg.evaluate("(document.querySelector('.screen:not([hidden])') || {}).id || null")

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        cdp = await ctx.new_cdp_session(pg)

        # ---------- 1) tap the active tab again ----------
        await pg.goto(HOST + "/index.html"); await pg.wait_for_timeout(500)
        tab = lambda t: f'#bottomNav [data-nav="{t}"]'
        await pg.click(tab("training")); await pg.wait_for_timeout(200)
        check("Training hub open", await visible_screen(pg) == "trainingHub")
        await pg.click('#hubAreaGrid .area-tile[data-area="visual"]'); await pg.wait_for_timeout(250)
        check("area home open (Visual Training)", await visible_screen(pg) == "home")
        await pg.evaluate("window.scrollTo(0, 700)"); await pg.wait_for_timeout(100)
        check("page scrolled", await pg.evaluate("window.scrollY") > 300)
        await pg.click(tab("training")); await pg.wait_for_timeout(900)
        check("re-tap while scrolled: back to the top", await pg.evaluate("window.scrollY") < 5)
        check("re-tap while scrolled: stays on the area home", await visible_screen(pg) == "home")
        await pg.click(tab("training")); await pg.wait_for_timeout(250)
        check("re-tap at the top: back to Training", await visible_screen(pg) == "trainingHub")
        await pg.click(tab("training")); await pg.wait_for_timeout(250)
        check("re-tap on the tab's own page: nothing happens", await visible_screen(pg) == "trainingHub")
        await pg.click(tab("today")); await pg.wait_for_timeout(250)
        await pg.click("#todayPlanBtn"); await pg.wait_for_timeout(250)
        check("Wochenplan open under Heute", await visible_screen(pg) == "planScreen")
        await pg.click(tab("today")); await pg.wait_for_timeout(250)
        check("re-tap Heute on the Wochenplan: back to Heute", await visible_screen(pg) == "todayHome")

        # ---------- 2) calendar swipe ----------
        first_date = lambda: pg.evaluate("document.querySelector('#todayWeekStrip [data-date]').dataset.date")
        d0 = await first_date()
        await pg.evaluate("document.querySelector('#todayWeekStrip').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, "#todayWeekStrip")
        await touch_drag(cdp, x + 70, y, x - 70, y + 8); await pg.wait_for_timeout(450)
        d1 = await first_date()
        check("swipe left on the week strip = next week", d1 != d0 and d1 > d0, (d0, d1))
        x, y = await center(pg, "#todayWeekStrip")
        await touch_drag(cdp, x - 70, y, x + 70, y - 8); await pg.wait_for_timeout(450)
        check("swipe right = previous week", await first_date() == d0)
        x, y = await center(pg, "#todayWeekStrip")
        await touch_drag(cdp, x, y, x + 15, y + 160); await pg.wait_for_timeout(300)
        check("vertical drag does not change the week", await first_date() == d0)
        x, y = await center(pg, "#todayWeekStrip")
        await touch_drag(cdp, x, y, x - 30, y); await pg.wait_for_timeout(300)
        check("short sideways move (< 50 px) does nothing", await first_date() == d0)
        # a short tap on a day still selects it
        day = '#todayWeekStrip [data-date]:nth-child(3)'
        dx, dy = await center(pg, day)
        await press(cdp, dx, dy, 60); await pg.wait_for_timeout(250)
        check("tap on a day still selects it", await pg.evaluate(f"document.querySelector({json.dumps(day)}).classList.contains('selected')"))
        # month view
        await pg.click("#calMonthBtn"); await pg.wait_for_timeout(250)
        title = lambda: pg.evaluate("document.querySelector('#calExpand .cal-month-title').textContent")
        m0 = await title()
        await pg.evaluate("document.querySelector('#calExpand .cal-grid').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, "#calExpand .cal-grid")
        await touch_drag(cdp, x + 80, y, x - 80, y); await pg.wait_for_timeout(450)
        m1 = await title()
        check("swipe left on the month = next month", m1 != m0, (m0, m1))
        x, y = await center(pg, "#calExpand .cal-grid")
        await touch_drag(cdp, x - 80, y, x + 80, y); await pg.wait_for_timeout(450)
        check("swipe right on the month = previous month", await title() == m0)
        x, y = await center(pg, "#calExpand .cal-grid")
        await touch_drag(cdp, 20, y, 200, y); await pg.wait_for_timeout(450)
        check("swipe from the left edge is left to Zurück-Wischen", await title() == m0)
        await pg.click("#calMonthBtn"); await pg.wait_for_timeout(200)

        # ---------- 4) long press ----------
        await pg.click(tab("training")); await pg.wait_for_timeout(250)
        tile = '#hubAreaGrid .area-tile[data-area="visual"]'
        check("tiles block text selection / callout", await pg.evaluate(f"getComputedStyle(document.querySelector({json.dumps(tile)})).userSelect") == "none")
        x, y = await center(pg, tile)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        check("long press opens the action sheet", await pg.is_visible("#tileActionSheet"))
        check("the tile's click was suppressed", await visible_screen(pg) == "trainingHub")
        acts = await pg.evaluate("[...document.querySelectorAll('#tileActionList button')].map(b => b.textContent)")
        check("area tile actions", acts == ["Öffnen", "In den Wochenplan", "Zum Kombi-Programm", "Abbrechen"], acts)
        check("sheet title is the area", (await pg.inner_text("#tileActionTitle")).strip() == "Visuelles Training")
        check("action buttons >= 44 px", await pg.evaluate("[...document.querySelectorAll('#tileActionList button')].every(b => b.getBoundingClientRect().height >= 44)"))
        await pg.screenshot(path="gestures_sheet.png")
        await pg.click('#tileActionList [data-tile-act="cancel"]'); await pg.wait_for_timeout(200)
        check("Abbrechen closes, nothing else happens", not await pg.is_visible("#tileActionSheet") and await visible_screen(pg) == "trainingHub")
        await press(cdp, x, y, 700, move=25); await pg.wait_for_timeout(300)
        check("press with movement (scroll) opens no sheet", not await pg.is_visible("#tileActionSheet"))
        await press(cdp, x, y, 70); await pg.wait_for_timeout(300)
        check("short press still opens the area", await visible_screen(pg) == "home")
        # exercise card: Direkt starten
        card = await pg.evaluate("(() => { const c = [...document.querySelectorAll('#home .excard[data-exercise]')].find(c => !c.classList.contains('incompatible') && c.getClientRects().length); return c.dataset.exercise; })()")
        csel = f'#home .excard[data-exercise="{card}"]'
        await pg.evaluate(f"document.querySelector({json.dumps(csel)}).scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, csel)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        acts = await pg.evaluate("[...document.querySelectorAll('#tileActionList button')].map(b => b.textContent)")
        check("exercise card actions", acts == ["Direkt starten", "In den Wochenplan", "Zum Kombi-Programm", "Abbrechen"], acts)
        await pg.click('#tileActionList [data-tile-act="start"]'); await pg.wait_for_timeout(600)
        check("Direkt starten runs the exercise", await pg.is_visible("#player") and await visible_screen(pg) is None)
        check("bottom bar hidden while it runs", not await pg.is_visible("#bottomNav"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(400)
        # In den Wochenplan
        if await visible_screen(pg) != "home":
            await pg.goto(HOST + "/index.html?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.evaluate(f"document.querySelector({json.dumps(csel)}).scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, csel)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        await pg.click('#tileActionList [data-tile-act="plan"]'); await pg.wait_for_timeout(300)
        check("plan sheet opens", await pg.is_visible("#planEntrySheet"))
        check("plan sheet prefilled with the exercise", await pg.input_value("#planEntryArea") == "visual" and await pg.input_value("#planEntryWhat") == "ex:" + card)
        # Trainingsplanung kp1 (07.10.): the weekday select became the
        # multi-day picker #planEntryDays (today preselected) - pick only Wednesday.
        check("weekday picker shown", await pg.is_visible("#planEntryDays"))
        for i in await pg.evaluate("[...document.querySelectorAll('#planEntryDays .plan-daypick.active[data-pick]')].map(b => b.dataset.pick)"):
            if i != "2": await pg.click(f'#planEntryDays [data-pick="{i}"]')
        if not await pg.locator('#planEntryDays [data-pick="2"].active').count():
            await pg.click('#planEntryDays [data-pick="2"]')
        check("only Wednesday picked", await pg.evaluate("[...document.querySelectorAll('#planEntryDays .plan-daypick.active')].map(b => b.dataset.pick)") == ["2"])
        await pg.click("#planEntrySaveBtn"); await pg.wait_for_timeout(300)
        planv = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        ok = planv and planv["phases"] and any(e["what"] == "ex:" + card for e in planv["phases"][0]["days"][2])
        check("entry saved on Wednesday of the Wochenplan (new phase created)", ok)
        await pg.reload(); await pg.wait_for_timeout(500)
        planv = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-plan-v1'))")
        check("plan entry persists after reload", any(e["what"] == "ex:" + card for e in planv["phases"][0]["days"][2]))
        await pg.evaluate("document.querySelector('#planEntrySheet').hidden")
        # the plain plan sheet (from Heute) has no weekday picker
        await pg.click(tab("today")); await pg.wait_for_timeout(250)
        await pg.click("#dayAddBtn"); await pg.wait_for_timeout(250)
        check("normal one-day entry sheet has no weekday picker", not await pg.is_visible("#planEntryDay") and not await pg.is_visible("#planEntryDays"))
        await pg.click("#planEntryCancelBtn"); await pg.wait_for_timeout(150)
        # Zum Kombi-Programm from an exercise card
        await pg.click(tab("training")); await pg.wait_for_timeout(200)
        await pg.click('#hubAreaGrid .area-tile[data-area="visual"]'); await pg.wait_for_timeout(250)
        await pg.evaluate(f"document.querySelector({json.dumps(csel)}).scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, csel)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        await pg.click('#tileActionList [data-tile-act="kombi"]'); await pg.wait_for_timeout(300)
        check("Kombi capture opens for this exercise", await visible_screen(pg) == "ready" and (await pg.inner_text("#startBtn")).strip() == "Baustein übernehmen")
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("Baustein lands in the Kombi-Programm", await visible_screen(pg) == "comboScreen" and await pg.locator("#comboBlockList .chapter-row").count() == 1)
        # NAT tile
        await pg.goto(HOST + "/index.html?bereich=nat"); await pg.wait_for_timeout(500)
        nsel = '#natExercises .nat-tile[data-nat-ex="blitz"]'
        await pg.evaluate(f"document.querySelector({json.dumps(nsel)}).scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, nsel)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        acts = await pg.evaluate("[...document.querySelectorAll('#tileActionList button')].map(b => b.textContent)")
        check("NAT tile actions", acts == ["Direkt starten", "In den Wochenplan", "Zum Kombi-Programm", "Abbrechen"], acts)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
        check("Escape closes the action sheet", not await pg.is_visible("#tileActionSheet"))
        check("page stays where it was after closing", await center(pg, nsel) == [x, y], (await center(pg, nsel), [x, y]))
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        await pg.click('#tileActionList [data-tile-act="start"]'); await pg.wait_for_timeout(600)
        check("NAT Direkt starten runs Blitz-Raster", await visible_screen(pg) is None)

        # ---------- 3a) drag reorder: Kombi-Bausteine ----------
        await pg.goto(HOST + "/index.html?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.click('[data-nav="training"]'); await pg.wait_for_timeout(250); await pg.click('#trainingHub .combo-entry-link'); await pg.wait_for_timeout(200)
        for dur in ("15", "30", "45"):
            await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
            await pg.fill("#rememberComboDurationSlider", dur)
            await pg.dispatch_event("#rememberComboDurationSlider", "input")
            await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        rows = pg.locator("#comboBlockList .chapter-row")
        check("3 Bausteine in the draft", await rows.count() == 3)
        check("each Baustein has a drag handle and ↑/↓ stay", await pg.locator("#comboBlockList .chapter-row .drag-handle").count() == 3 and await pg.locator("#comboBlockList .combo-block-move").count() == 4)
        check("drag handle is >= 44 px", await pg.evaluate("(() => { const r = document.querySelector('#comboBlockList .drag-handle').getBoundingClientRect(); return r.width >= 44 && r.height >= 44; })()"))
        await pg.evaluate("""(() => { const s = document.querySelectorAll('#comboBlockList .combo-pause-slider');
            s[0].value = 5; s[0].dispatchEvent(new Event('input')); s[1].value = 60; s[1].dispatchEvent(new Event('input')); })()""")
        metas = lambda: pg.evaluate("[...document.querySelectorAll('#comboBlockList .chapter-row .info span')].map(s => s.textContent)")
        pauses = lambda: pg.evaluate("[...document.querySelectorAll('#comboBlockList .combo-pause-slider')].map(s => s.value)")
        m_before = await metas()
        check("three distinct Bausteine", len(set(m_before)) == 3, m_before)
        await pg.evaluate("document.querySelector('#comboBlockList').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(150)
        hx, hy = await handle_at(pg, "#comboBlockList .chapter-row", 0)
        r2 = await pg.evaluate("(() => { const r = document.querySelectorAll('#comboBlockList .chapter-row')[1].getBoundingClientRect(); return [r.top, r.bottom]; })()")
        await pg.mouse.move(hx, hy); await pg.mouse.down()
        for i in range(1, 9):
            await pg.mouse.move(hx, hy + (r2[1] + 4 - hy) * i / 8); await pg.wait_for_timeout(20)
        check("live placeholder while dragging", await pg.locator("#comboBlockList .drag-placeholder").count() == 1)
        check("pause strips hidden while dragging", not await pg.locator("#comboBlockList .combo-pause-row").first.is_visible())
        await pg.screenshot(path="gestures_drag.png")
        await pg.mouse.up(); await pg.wait_for_timeout(250)
        m_after = await metas()
        check("drag moved Baustein 1 to position 2", m_after == [m_before[1], m_before[0], m_before[2]], m_after)
        check("'Pause danach' moved with its Baustein", await pauses() == ["60", "5"], await pauses())
        check("no placeholder left", await pg.locator("#comboBlockList .drag-placeholder").count() == 0)
        # the arrows use the same path: ↑ on block 2 restores the order and the pauses
        await pg.evaluate("document.querySelectorAll('#comboBlockList .chapter-row')[1].querySelector('[data-move=up]').click()"); await pg.wait_for_timeout(200)
        check("↑ still works the same way", await metas() == m_before and await pauses() == ["5", "60"])
        # dropping in place changes nothing
        hx, hy = await handle_at(pg, "#comboBlockList .chapter-row", 1)
        await pg.mouse.move(hx, hy); await pg.mouse.down(); await pg.mouse.move(hx, hy + 6); await pg.mouse.up(); await pg.wait_for_timeout(200)
        check("drop in place keeps the order", await metas() == m_before)
        # touch drag: last block to the top
        hx, hy = await handle_at(pg, "#comboBlockList .chapter-row", 2)
        r1 = await pg.evaluate("document.querySelectorAll('#comboBlockList .chapter-row')[0].getBoundingClientRect().top")
        await touch_drag(cdp, hx, hy, hx, r1 + 4, steps=10, pause=0.02); await pg.wait_for_timeout(250)
        check("touch drag moves the last Baustein to the top", await metas() == [m_before[2], m_before[0], m_before[1]], await metas())

        # ---------- 3b) drag reorder: Eigenes Training checklist ----------
        await pg.goto(HOST + "/index.html?bereich=free"); await pg.wait_for_timeout(500)
        await pg.click("#freeNewBtn"); await pg.wait_for_timeout(250)
        await pg.fill("#freeTitleInput", "Sortiertest")
        await pg.click('#freeKindRow [data-free-kind="list"]'); await pg.wait_for_timeout(150)
        for i, t in enumerate(["Alpha", "Beta", "Gamma"]):
            if i:
                await pg.click("#freeItemAddBtn"); await pg.wait_for_timeout(100)
            await pg.locator("#freeItemList .free-item-text").nth(i).fill(t)
        texts = lambda: pg.evaluate("[...document.querySelectorAll('#freeItemList .free-item-text')].map(i => i.value)")
        check("checklist has 3 points with handles", await texts() == ["Alpha", "Beta", "Gamma"] and await pg.locator("#freeItemList .drag-handle").count() == 3)
        check("↑/↓ buttons stay", await pg.locator('#freeItemList .free-item-btn[data-move]').count() == 4)
        await pg.evaluate("document.querySelector('#freeItemList').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(150)
        hx, hy = await handle_at(pg, "#freeItemList .free-item-row", 0)
        r3 = await pg.evaluate("document.querySelectorAll('#freeItemList .free-item-row')[2].getBoundingClientRect().bottom")
        await touch_drag(cdp, hx, hy, hx, r3 - 4, steps=12, pause=0.02); await pg.wait_for_timeout(250)
        check("touch drag moves Alpha to the end", await texts() == ["Beta", "Gamma", "Alpha"], await texts())
        await pg.screenshot(path="gestures_free.png")
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(300)
        await pg.reload(); await pg.wait_for_timeout(500)
        saved = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-free-blocks-v1'))")
        blk = [x for x in saved if x["title"] == "Sortiertest"]
        check("new order saved and persists after reload", blk and [i["text"] for i in blk[0]["items"]] == ["Beta", "Gamma", "Alpha"])
        # long press on an own Eigenes-Training card
        fsel = '#freeOwnGrid [data-free-id]'
        await pg.evaluate(f"document.querySelector({json.dumps(fsel)}).scrollIntoView({{block:'center'}})"); await pg.wait_for_timeout(150)
        x, y = await center(pg, fsel)
        await press(cdp, x, y, 700); await pg.wait_for_timeout(300)
        acts = await pg.evaluate("[...document.querySelectorAll('#tileActionList button')].map(b => b.textContent)")
        check("Eigenes Training card actions", acts == ["Direkt starten", "In den Wochenplan", "Zum Kombi-Programm", "Abbrechen"], acts)
        await pg.click('#tileActionList [data-tile-act="cancel"]'); await pg.wait_for_timeout(150)

        # wide screen: right click = same sheet, nothing breaks
        await pg.set_viewport_size({"width": 1024, "height": 768}); await pg.wait_for_timeout(200)
        await pg.click(fsel, button="right"); await pg.wait_for_timeout(200)
        check("right click opens the sheet on desktop", await pg.is_visible("#tileActionSheet"))
        await pg.keyboard.press("Escape")
        await ctx.close(); await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
