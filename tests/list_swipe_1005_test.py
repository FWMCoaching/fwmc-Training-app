import asyncio, json, os
from playwright.async_api import async_playwright

# Wischen in Listen (Fabian, 2026-10-05: "Einen Termin oder ein eigenes
# Training nach links wischen, dann erscheinen 'Bearbeiten' und 'Löschen',
# so wie beim Löschen einer Mail am iPhone."). Real touch input via CDP.
# Covers: Eigenes Training cards (Bearbeiten/Löschen, one row open at a
# time, swipe right / tap elsewhere closes and the tap does not open
# anything, vertical drag and edge start do not open a row, a plain tap and
# a long press still work), trainer templates (only Löschen), Heute Termine
# (event + one-off training + weekly training: edit sheets, delete confirm),
# Wochenplan rows, saved Kombi-Programme (only Löschen, confirm), 44 px
# buttons, persistence after reload, no page/console errors.
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
        "localStorage.setItem('fwmc-test-bottomnav','true');")
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


async def touch_drag(cdp, x0, y0, x1, y1, steps=10, pause=0.016):
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / steps, "y": y0 + (y1 - y0) * i / steps}]})
        await asyncio.sleep(pause)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


async def tap(cdp, x, y):
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    await asyncio.sleep(0.05)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


async def rect(pg, sel, i=0):
    return await pg.evaluate(f"(() => {{ const r = document.querySelectorAll({json.dumps(sel)})[{i}].getBoundingClientRect(); return {{x: r.left, y: r.top, w: r.width, h: r.height}}; }})()")


async def swipe_left(pg, cdp, sel, i=0, dist=200):
    await pg.evaluate(f"document.querySelectorAll({json.dumps(sel)})[{i}].scrollIntoView({{block: 'center'}})")
    await pg.wait_for_timeout(80)
    r = await rect(pg, sel, i)
    y = r["y"] + min(r["h"] / 2, 24)
    x0 = min(r["x"] + r["w"] - 20, 370)
    await touch_drag(cdp, x0, y, x0 - dist, y)
    await pg.wait_for_timeout(380)


async def panels(pg):
    return await pg.evaluate("[...document.querySelectorAll('.swipe-actions')].map((p) => [...p.querySelectorAll('button')].map((b) => b.textContent))")


async def visible_screen(pg):
    return await pg.evaluate("(() => { const s = [...document.querySelectorAll('.screen')].find((el) => !el.hidden); return s ? s.id : null; })()")


async def tx(pg, sel, i=0):
    return await pg.evaluate(f"(() => {{ const m = getComputedStyle(document.querySelectorAll({json.dumps(sel)})[{i}]).transform; return m === 'none' ? 0 : new DOMMatrix(m).m41; }})()")


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await ctx.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body='{"error":"not_found"}', content_type="application/json"))
        cdp = await ctx.new_cdp_session(pg)

        # ---------- seed ----------
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(300)
        await pg.evaluate("""(() => {
          const d = new Date(), pad = (n) => String(n).padStart(2, '0');
          const today = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
          localStorage.setItem('fwmc-free-blocks-v1', JSON.stringify([
            {id: 'fb-a', kind: 'check', title: 'Journal', note: 'Drei Sätze'},
            {id: 'fb-b', kind: 'timer', title: 'Eisbad', minutes: 3},
            {id: 'fb-c', kind: 'check', title: 'Lesen'}]));
          localStorage.setItem('fwmc-free-trainer-v1', JSON.stringify([{id: 'tr-x-1', code: 'x', kind: 'check', title: 'Vom Trainer'}]));
          localStorage.setItem('fwmc-events-v1', JSON.stringify([{id: 'ev1', date: today, time: '18:00', title: 'Spiel gegen Nord', kind: 'wettkampf', goal: false}]));
          const day = () => [{id: 'wk1', area: 'free', what: 'free:fb-a', time: '07:00', minutes: 10}];
          localStorage.setItem('fwmc-plan-v1', JSON.stringify({startDate: today, phases: [{id: 'ph1', name: 'Phase 1', weeks: 0, days: [day(), day(), day(), day(), day(), day(), day()]}],
            extras: {[today]: [{id: 'ex1', area: 'breath', what: '', time: '12:00', minutes: 15}]}, skips: {}, done: {}}));
          localStorage.setItem('fwmc-combo-saved-v1', JSON.stringify([{id: 'k1', name: 'Morgenkombi', blocks: [{domain: 'free', free: {kind: 'check', title: 'Journal', note: '', minutes: 5, items: []}}]}]));
          localStorage.setItem('fwmc-day-view-v1', JSON.stringify('list'));
        })()""")
        await pg.reload(); await pg.wait_for_timeout(400)
        OWN = "#freeOwnGrid [data-free-id]"

        # ---------- Eigenes Training ----------
        check("three own cards", await pg.locator(OWN).count() == 3)
        await swipe_left(pg, cdp, OWN, 0)
        check("swipe left reveals Bearbeiten + Löschen", await panels(pg) == [["Bearbeiten", "Löschen"]], await panels(pg))
        check("row moved left", await tx(pg, OWN, 0) < -150, await tx(pg, OWN, 0))
        sizes = await pg.evaluate("[...document.querySelectorAll('.swipe-actions button')].map((b) => { const r = b.getBoundingClientRect(); return [r.width, r.height]; })")
        check("action buttons >= 44 px", all(w >= 44 and h >= 44 for w, h in sizes), sizes)
        inside = await pg.evaluate("[...document.querySelectorAll('.swipe-actions button')].every((b) => { const r = b.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; })")
        check("buttons fully on screen", inside)
        colors = await pg.evaluate("""[...document.querySelectorAll('.swipe-actions button')].map((b) => getComputedStyle(b).backgroundColor)""")
        warn = await pg.evaluate("(() => { const s = document.createElement('span'); s.style.color = 'var(--warn)'; document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; })()")
        check("Löschen uses the destructive colour (--warn)", colors[1] == warn, (colors, warn))
        check("still on the area home", await visible_screen(pg) == "freeHome")

        await swipe_left(pg, cdp, OWN, 1)
        check("one row open at a time", len(await panels(pg)) == 1 and abs(await tx(pg, OWN, 0)) < 1 and await tx(pg, OWN, 1) < -150)

        # swipe right closes
        r = await rect(pg, OWN, 1)
        await touch_drag(cdp, 120, r["y"] + 20, 320, r["y"] + 20); await pg.wait_for_timeout(420)
        check("swipe right closes", await panels(pg) == [] and abs(await tx(pg, OWN, 1)) < 1)
        check("swipe right on the open row stays on the page", await visible_screen(pg) == "freeHome")
        # ... even when it starts at the left edge (no swipe-back while closing a row)
        await swipe_left(pg, cdp, OWN, 1)
        r = await rect(pg, OWN, 1)
        await touch_drag(cdp, 24, r["y"] + 20, 240, r["y"] + 20); await pg.wait_for_timeout(420)
        check("edge-start swipe right on an open row only closes it", await panels(pg) == [] and await visible_screen(pg) == "freeHome", await visible_screen(pg))

        # tap elsewhere closes, and does not open what was tapped
        await swipe_left(pg, cdp, OWN, 0)
        r2 = await rect(pg, OWN, 1)
        await tap(cdp, r2["x"] + 60, r2["y"] + 20); await pg.wait_for_timeout(420)
        check("tap elsewhere closes the row", await panels(pg) == [])
        check("that tap did not open the other card", await visible_screen(pg) == "freeHome", await visible_screen(pg))
        # tap on the open row itself closes it too
        await swipe_left(pg, cdp, OWN, 0)
        await tap(cdp, 100, (await rect(pg, OWN, 0))["y"] + 20); await pg.wait_for_timeout(420)
        check("tap on the open row closes it, no navigation", await panels(pg) == [] and await visible_screen(pg) == "freeHome")

        # a short swipe snaps back
        r0 = await rect(pg, OWN, 0)
        await touch_drag(cdp, r0["x"] + 300, r0["y"] + 20, r0["x"] + 260, r0["y"] + 20, steps=4); await pg.wait_for_timeout(420)
        check("short swipe snaps back closed", abs(await tx(pg, OWN, 0)) < 1)

        # vertical drag is not hijacked
        await pg.evaluate("window.scrollTo(0, 0)"); await pg.wait_for_timeout(60)
        await pg.evaluate(f"document.querySelector({json.dumps(OWN)}).scrollIntoView({{block: 'end'}})"); await pg.wait_for_timeout(80)
        y_before = await pg.evaluate("scrollY")
        r0 = await rect(pg, OWN, 0)
        await touch_drag(cdp, r0["x"] + 200, r0["y"] + 20, r0["x"] + 185, r0["y"] - 220, steps=12); await pg.wait_for_timeout(500)
        check("vertical drag opens no row", await panels(pg) == [] and abs(await tx(pg, OWN, 0)) < 1)
        y_after = await pg.evaluate("scrollY")
        check("vertical drag still scrolls the page", y_after > y_before + 50, (y_before, y_after))

        # edge start belongs to swipe-back
        r0 = await rect(pg, OWN, 0)
        await touch_drag(cdp, 12, r0["y"] + 20, 4, r0["y"] + 22, steps=3); await pg.wait_for_timeout(300)
        check("touch from the left edge opens no row", await panels(pg) == [])

        # a plain tap still opens the card, a long press still opens the sheet
        await pg.evaluate(f"document.querySelector({json.dumps(OWN)}).scrollIntoView({{block: 'center'}})"); await pg.wait_for_timeout(80)
        r0 = await rect(pg, OWN, 0)
        await tap(cdp, r0["x"] + 60, r0["y"] + 20); await pg.wait_for_timeout(300)
        check("plain tap still opens the training", await visible_screen(pg) == "freeReady" and "Journal" in await pg.inner_text("#freeReadyTitle"), (await visible_screen(pg), await pg.inner_text("#freeReadyTitle")))
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        r0 = await rect(pg, OWN, 0)
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": r0["x"] + 60, "y": r0["y"] + 20}]})
        await asyncio.sleep(0.7)
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); await pg.wait_for_timeout(250)
        check("long press still opens the action sheet", await pg.is_visible("#tileActionSheet") and await panels(pg) == [])
        await pg.click('#tileActionList [data-tile-act="cancel"]'); await pg.wait_for_timeout(150)

        # Bearbeiten
        await swipe_left(pg, cdp, OWN, 1)
        await pg.click(".swipe-actions [data-swipe-act='edit']"); await pg.wait_for_timeout(250)
        check("Bearbeiten opens the editor of that training", await visible_screen(pg) == "freeEdit" and await pg.input_value("#freeTitleInput") == "Eisbad"
              and "bearbeiten" in await pg.inner_text("#freeEditTitle"))
        check("panel gone after the action", await panels(pg) == [])
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)

        # Löschen -> confirmDialog
        await swipe_left(pg, cdp, OWN, 2)
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        check("Löschen asks first", await pg.is_visible("#confirmSheet") and "Lesen" in await pg.inner_text("#confirmText"))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(150)
        check("Nein keeps it", await pg.locator(OWN).count() == 3)
        await swipe_left(pg, cdp, OWN, 2)
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(150)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("Ja deletes it", await pg.locator(OWN).count() == 2)

        # trainer template: only Löschen
        await swipe_left(pg, cdp, "#freeTrainerGrid [data-free-id]", 0)
        check("trainer template offers only Löschen", await panels(pg) == [["Löschen"]], await panels(pg))
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(150)
        check("trainer remove asks first", await pg.is_visible("#confirmSheet") and "Vom Trainer" in await pg.inner_text("#confirmText"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("trainer template removed", await pg.is_hidden("#freeTrainerSection"))

        # ---------- Heute ----------
        await pg.goto(BASE); await pg.wait_for_timeout(450)
        EV = "#dayEvents .event-item"
        DI = "#dayPanelBody .day-item:not(.compact)"
        check("Heute shows event + 2 trainings", await pg.locator(EV).count() == 1 and await pg.locator(DI).count() == 2)
        await swipe_left(pg, cdp, EV, 0)
        check("event row: Bearbeiten + Löschen", await panels(pg) == [["Bearbeiten", "Löschen"]])
        await pg.click(".swipe-actions [data-swipe-act='edit']"); await pg.wait_for_timeout(200)
        check("event Bearbeiten opens the Termin sheet", await pg.is_visible("#eventSheet") and await pg.input_value("#eventTitleInput") == "Spiel gegen Nord")
        await pg.click("#eventCancelBtn"); await pg.wait_for_timeout(150)

        # one-off training (12:00, Atemtraining) is the 2nd row (07:00 weekly first)
        titles = await pg.evaluate(f"[...document.querySelectorAll({json.dumps(DI)})].map((e) => e.dataset.occ)")
        i_ex, i_wk = titles.index("ex1"), titles.index("wk1")
        await swipe_left(pg, cdp, DI, i_ex)
        check("training row: Bearbeiten + Löschen", await panels(pg) == [["Bearbeiten", "Löschen"]])
        await pg.click(".swipe-actions [data-swipe-act='edit']"); await pg.wait_for_timeout(200)
        check("one-off Bearbeiten opens 'Training ändern'", await pg.is_visible("#planEntrySheet") and "ändern" in await pg.inner_text("#planEntryTitle")
              and await pg.input_value("#planEntryArea") == "breath")
        await pg.select_option("#planEntryMinutes", "30"); await pg.click("#planEntrySaveBtn"); await pg.wait_for_timeout(250)
        ex = await pg.evaluate("Object.values(JSON.parse(localStorage.getItem('fwmc-plan-v1')).extras).flat()")
        check("one-off edited in place (no duplicate)", len(ex) == 1 and ex[0]["id"] == "ex1" and ex[0]["minutes"] == 30, ex)
        check("Heute re-rendered with the new length", "30 Min." in await pg.inner_text("#dayPanelBody"))

        await swipe_left(pg, cdp, DI, i_wk)
        await pg.click(".swipe-actions [data-swipe-act='edit']"); await pg.wait_for_timeout(200)
        check("weekly Bearbeiten opens the plan entry", await pg.is_visible("#planEntrySheet") and await pg.input_value("#planEntryWhat") == "free:fb-a")
        await pg.select_option("#planEntryMinutes", "20"); await pg.click("#planEntrySaveBtn"); await pg.wait_for_timeout(250)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-plan-v1')).phases[0].days.flat().filter((e) => e.id === 'wk1')")
        check("weekly entry edited (only today's weekday)", len(wk) == 7 and sum(1 for e in wk if e["minutes"] == 20) == 1, [e["minutes"] for e in wk])
        check("Heute shows the edited weekly entry", "20 Min." in await pg.inner_text("#dayPanelBody"))

        await swipe_left(pg, cdp, DI, i_wk)
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        txt = await pg.inner_text("#confirmText")
        check("weekly delete explains it leaves the Wochenplan", await pg.is_visible("#confirmSheet") and "Wochenplan" in txt, txt)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        wk = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-plan-v1')).phases[0].days.flat().filter((e) => e.id === 'wk1')")
        check("weekly entry removed from today's weekday only", len(wk) == 6)

        await swipe_left(pg, cdp, DI, 0)
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("one-off training deleted", await pg.evaluate("Object.values(JSON.parse(localStorage.getItem('fwmc-plan-v1')).extras).flat().length") == 0)

        await swipe_left(pg, cdp, EV, 0)
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        check("event delete asks first", await pg.is_visible("#confirmSheet") and "Spiel gegen Nord" in await pg.inner_text("#confirmText"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("event deleted", await pg.locator(EV).count() == 0)

        # ---------- Wochenplan screen ----------
        await pg.click("#todayPlanBtn"); await pg.wait_for_timeout(250)
        PI = "#planPhaseList .plan-item"
        n_before = await pg.locator(PI).count()
        await swipe_left(pg, cdp, PI, 0)
        check("plan row: Bearbeiten + Löschen", await panels(pg) == [["Bearbeiten", "Löschen"]])
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        check("plan delete asks first (the ✕ itself does not)", await pg.is_visible("#confirmSheet"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("plan row removed", await pg.locator(PI).count() == n_before - 1)
        await swipe_left(pg, cdp, PI, 0)
        await pg.click(".swipe-actions [data-swipe-act='edit']"); await pg.wait_for_timeout(200)
        check("plan Bearbeiten opens the entry sheet", await pg.is_visible("#planEntrySheet"))
        await pg.click("#planEntryCancelBtn"); await pg.wait_for_timeout(150)

        # ---------- saved Kombi-Programme ----------
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.click('[data-nav="training"]'); await pg.wait_for_timeout(250); await pg.click('#trainingHub .combo-entry-link'); await pg.wait_for_timeout(250)
        KS = "#comboSavedList .bundle-item-wrap"
        check("saved Kombi listed, ✎ and ✕ still there", await pg.locator(KS).count() == 1 and await pg.locator(KS + " .combo-block-remove").count() == 1 and await pg.locator(KS + " .combo-saved-edit").count() == 1)
        await swipe_left(pg, cdp, KS, 0)
        # since 07.10. a saved Kombi can be edited (Fabian "Erst Vorschau")
        check("saved Kombi: Bearbeiten + Löschen", await panels(pg) == [["Bearbeiten", "Löschen"]], await panels(pg))
        await pg.click(".swipe-actions [data-swipe-act='delete']"); await pg.wait_for_timeout(200)
        check("saved Kombi delete asks first", await pg.is_visible("#confirmSheet") and "Morgenkombi" in await pg.inner_text("#confirmText"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("saved Kombi deleted", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-combo-saved-v1')).length") == 0)

        # ---------- persistence ----------
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        check("deletions persist after reload", await pg.locator(OWN).count() == 2 and await pg.is_hidden("#freeTrainerSection"))

        check("no page/console errors", not errors, errors)
        await b.close()
    failed = [n for n, ok in results if not ok]
    print("\nALL PASSED" if not failed else f"\nFAILED: {failed}")


asyncio.run(main())
