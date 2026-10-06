import asyncio, json, time, datetime
from playwright.async_api import async_playwright

# Fabian 2026-10-06 (second round): the 3-day limit is visible on the
# Weitermachen card, single longer exercises (Atem-Muster, Movement) can be
# continued with the time that was left ("atmen nach einem Anruf"), and the
# Sunday Wochenabschluss shows a check per planned unit, one sentence and an
# optional Vorsatz that sits on Heute the next week.
BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

VIS = "() => [...document.querySelectorAll('.screen,.player')].filter(e => !e.hidden && e.getClientRects().length).map(e => e.id).join('+')"
SINGLE = "() => JSON.parse(localStorage.getItem('fwmc-resume-single-v1') || 'null')"
PROG_DEF = {"type": "breath-program", "name": "Feierabend-Reset", "blocks": [{"pattern": "box", "durationMin": 3}, {"pattern": "coherent", "durationMin": 5}]}
def prog_rec(age_s):
    return json.dumps({"type": "breath", "def": PROG_DEF, "key": "atem-reset", "title": "Feierabend-Reset", "idx": 1, "pos": 1, "total": 2, "played": 180, "ts": int((time.time() - age_s) * 1000)})
def single_rec(kind, age_s, rest=240, total=300):
    r = {"type": "single", "kind": kind, "total": total, "played": total - rest, "rest": rest, "ts": int((time.time() - age_s) * 1000)}
    if kind == "breath":
        r.update(title="Box-Atmung", breath={"key": "box", "phases": {"in": 4, "hold1": 4, "out": 4, "hold2": 4}, "sound": False, "listen": False})
    else:
        r.update(title="Ganzkörper-Reaktion", movement={"movements": ["armL-heben", "armR-heben", "legL-strecken", "legR-strecken"], "bpm": 60, "preview": 2, "mirror": False, "showLabel": True})
    return json.dumps(r)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        def watch(pg):
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        async def fresh(seed=""):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            await ctx.add_init_script(INIT + seed)
            pg = await ctx.new_page(); watch(pg)
            return ctx, pg

        # 1) the 3-day limit is written on the card
        ctx, pg = await fresh(f"if(!sessionStorage.getItem('s')){{sessionStorage.setItem('s',1);localStorage.setItem('fwmc-resume-v1', {json.dumps(prog_rec(600))});}}")
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        until = (await pg.inner_text("#todayMain")).replace("\xa0", " ")
        end = datetime.datetime.now() + datetime.timedelta(days=3, seconds=-600)
        day = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][end.weekday()]
        check("card says until when", f"Fortsetzen ist noch bis {day}, {end:%H:%M} Uhr möglich." in until, until.replace("\n", " | ")[-90:])
        await ctx.close()

        # 2) a single Atem run remembers the rest when paused, Heute offers it, finishing clears it
        ctx, pg = await fresh()
        await ctx.clock.install()
        await pg.goto(BASE + "index.html?bereich=breath"); await pg.wait_for_timeout(300)
        await pg.click("#patternGrid .featured-card >> nth=1")  # Box-Atmung
        await pg.click('[data-breath-dur="5"]')
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(200)
        await pg.clock.run_for(70000)
        await pg.click("#breathPauseBtn"); await pg.wait_for_timeout(200)
        r = await pg.evaluate(SINGLE)
        check("pause remembers the single run", r and r["kind"] == "breath" and 60 <= r["played"] <= 80 and r["total"] >= 290, str(r and {k: r[k] for k in ("kind", "title", "played", "rest", "total")}))
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(200)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        txt = (await pg.inner_text("#todayMain")).replace("\xa0", " ")
        title = r["title"] if r else "?"
        check("Heute offers the single run with the time left", title in txt and "noch 4 Min." in txt and "Fortsetzen" in txt, txt.replace("\n", " | ")[:140])
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(300)
        clock_txt = await pg.inner_text("#breathTimeEl")
        check("continues with the rest only", "breathPlayer" in await pg.evaluate(VIS) and clock_txt.startswith(("3:", "4:")) and clock_txt != "5:00", clock_txt)
        prefs = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-breath-prefs-v1') || localStorage.getItem('fwmc-breath-v1') || 'null')")
        # pause again after the continuation: total stays the original length
        await pg.clock.run_for(40000)
        await pg.click("#breathPauseBtn"); await pg.wait_for_timeout(200)
        r2 = await pg.evaluate(SINGLE)
        check("second break keeps the original length", r2 and r2["total"] == r["total"] and r2["played"] > r["played"], str(r2 and {k: r2[k] for k in ("played", "rest", "total")}))
        await pg.click("#breathResumeBtn")
        await pg.clock.run_for(400000); await pg.wait_for_timeout(300)
        check("finishing clears it", await pg.evaluate(SINGLE) is None and await pg.is_visible("#breathDonePanel"))
        await ctx.close()

        # 3) short runs and programmes are not remembered as single runs
        ctx, pg = await fresh()
        await ctx.clock.install()
        await pg.goto(BASE + "index.html?bereich=breath"); await pg.wait_for_timeout(300)
        await pg.click("#patternGrid .featured-card >> nth=1")
        await pg.click('[data-breath-dur="5"]')
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(200)
        await pg.clock.run_for(10000)
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(200)
        check("under 30 s done: nothing remembered", await pg.evaluate(SINGLE) is None)
        await ctx.close()

        # 4) Movement continues with its own settings; the client's settings stay
        ctx, pg = await fresh(f"if(!sessionStorage.getItem('s')){{sessionStorage.setItem('s',1);localStorage.setItem('fwmc-resume-single-v1', {json.dumps(single_rec('movement', 300))});}}")
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        before = await pg.evaluate("localStorage.getItem('fwmc-movement-prefs-v1') || localStorage.getItem('fwmc-movement-v1')")
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(300)
        mt = await pg.inner_text("#movementTimeEl")
        check("Movement continues with 4 min left", "movementPlayer" in await pg.evaluate(VIS) and mt.startswith(("4:", "3:")), mt)
        after = await pg.evaluate("localStorage.getItem('fwmc-movement-prefs-v1') || localStorage.getItem('fwmc-movement-v1')")
        check("client's Movement settings unchanged", before == after)
        await ctx.close()

        # 5) programme and single run: the more recent one is offered; Verwerfen drops only that one
        seed = (f"if(!sessionStorage.getItem('s')){{sessionStorage.setItem('s',1);localStorage.setItem('fwmc-resume-v1', {json.dumps(prog_rec(3600))});"
                f"localStorage.setItem('fwmc-resume-single-v1', {json.dumps(single_rec('breath', 600))});}}")
        ctx, pg = await fresh(seed)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        txt = await pg.inner_text("#todayMain")
        check("more recent one is offered", "Box-Atmung" in txt and "Feierabend-Reset" not in txt)
        await pg.click("#todayResumeDropBtn"); await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        txt = await pg.inner_text("#todayMain")
        check("after Verwerfen the programme shows", "Feierabend-Reset" in txt and await pg.evaluate(SINGLE) is None)
        await ctx.close()

        # 6) Wochenabschluss on Sunday, Vorsatz on Monday
        plan_seed = """if(!sessionStorage.getItem('s')){sessionStorage.setItem('s',1);
          localStorage.setItem('fwmc-plan-v1', JSON.stringify({extras: {'2026-10-07': [{id:'w1', area:'breath', minutes:10}], '2026-10-09': [{id:'w2', area:'movement', minutes:15}]}}));
          localStorage.setItem('fwmc-history-v1', JSON.stringify([{id:'h1', ts:'2026-10-07T17:00:00.000Z', kind:'breath', title:'Box-Atmung', seconds:300}]));}"""
        for sc in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=sc, service_workers="block")
            await ctx.add_init_script(INIT + plan_seed)
            await ctx.clock.set_fixed_time(datetime.datetime(2026, 10, 11, 18, 0))
            pg = await ctx.new_page(); watch(pg)
            await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
            vis = await pg.is_visible("#todayWeekReview")
            rows = await pg.locator("#todayWeekReview .week-review-row").count()
            done = await pg.locator("#todayWeekReview .week-review-row.is-done").count()
            sent = await pg.inner_text("#todayWeekReview .week-review-sentence") if vis else ""
            if sc == "light":
                hist_ok = done == 1
                check("Sunday: Wochenabschluss with one row per planned unit", vis and rows == 2, f"rows {rows}")
                check("planned unit with a training that day is checked", hist_ok, f"done {done}")
                check("one sentence", "1 von 2 geplanten Einheiten geschafft" in sent, sent)
                bb = await pg.locator("#weekIntentInput").bounding_box()
                check("Vorsatz field >= 44 px", bb and bb["height"] >= 44, str(bb and bb["height"]))
                await pg.fill("#weekIntentInput", "Zweimal Atemtraining am Abend")
                await pg.press("#weekIntentInput", "Enter"); await pg.wait_for_timeout(200)
                st = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-week-intent-v1')||'{}')")
                check("Vorsatz saved for next Monday", st.get("2026-10-12", {}).get("text") == "Zweimal Atemtraining am Abend", str(st))
                check("saved note shown", await pg.is_visible("#weekIntentSaved"))
            await pg.locator("#todayWeekReview").screenshot(path=f"screenshots/week_review_{sc}.png")
            if sc == "light":
                await pg.close()
                await ctx.clock.set_fixed_time(datetime.datetime(2026, 10, 12, 8, 0))
                pg = await ctx.new_page(); watch(pg)
                await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
                t = await pg.inner_text("#todayWeekReview") if await pg.is_visible("#todayWeekReview") else ""
                check("Monday: Vorsatz on Heute", "Zweimal Atemtraining am Abend" in t, t.replace("\n", " | "))
                await pg.screenshot(path="screenshots/week_intent_monday.png")
                await pg.click("#weekIntentHideBtn"); await pg.wait_for_timeout(200)
                await pg.reload(); await pg.wait_for_timeout(300)
                check("Ausblenden sticks", not await pg.is_visible("#todayWeekReview"))
                await ctx.clock.set_fixed_time(datetime.datetime(2026, 10, 14, 8, 0))
                await pg.reload(); await pg.wait_for_timeout(300)
                check("other weekdays without Vorsatz: no card", not await pg.is_visible("#todayWeekReview"))
            await ctx.close()
        # Sunday with nothing planned and nothing done
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        await ctx.clock.set_fixed_time(datetime.datetime(2026, 10, 11, 18, 0))
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        sent = await pg.inner_text("#todayWeekReview .week-review-sentence")
        check("empty week: friendly sentence, no rows", "ruhig" in sent and await pg.locator(".week-review-row").count() == 0, sent)
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "FAILED")

asyncio.run(main())
