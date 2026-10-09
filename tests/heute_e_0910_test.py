"""Heute Entwurf E (Fabian 09.10.): flat "Zuletzt" row, two half tiles
(Nichtraucher-Pause + Tagesform, 09.10. instead of "Neu für dich"), trainer question as a
slim line until answered, "Für dein Ziel" row under the week, code types
(unlock codes never count as "Mit Trainer"). Run from tests/."""
import asyncio, json, datetime
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT = "screenshots/heute_e/"
errors = []

def iso(days_ago):
    return (datetime.datetime.now() - datetime.timedelta(days=days_ago)).isoformat()

def hist(*items):
    return [dict(id=str(i), ts=iso(d), rating=None, seconds=120, **e) for i, (d, e) in enumerate(items)]

async def page_with(browser, store, scheme="light", w=390):
    ctx = await browser.new_context(viewport={"width": w, "height": 844}, color_scheme=scheme)
    base = {"fwmc-tips-seen": True, "fwmc-master-v1": {"startCountdown": False}, "fwmc-test-bottomnav": True}
    base.update(store)
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(json.dumps(v))});" for k, v in base.items())
    await ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ {js} sessionStorage.setItem('seeded','1'); }}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    await pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    await pg.goto(URL); await pg.wait_for_timeout(500)
    return ctx, pg

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        H = hist((2, {"kind": "exercise", "exId": "periph-flash", "title": "Periphere Wahrnehmung"}),
                 (3, {"kind": "breath", "title": "Box-Atmung"}), (4, {"kind": "breath", "title": "Box-Atmung"}))

        # 1. regular client with history, no answer yet
        ctx, pg = await page_with(b, {"fwmc-history-v1": H})
        print("Zuletzt row is flat:", await pg.is_visible("#todayMain.is-flat .today-last"))
        print("kicker names the weekday:", "ZULETZT ·" in (await pg.inner_text("#todayMain .today-main-kicker")).upper())
        print("Nochmal button:", (await pg.inner_text("#todayContinueBtn")).strip() == "Nochmal")
        print("pause tile visible:", await pg.is_visible("#todayBreak"))
        print("pause tile title in quotes:", "„Nichtraucher-Pause“" in await pg.inner_text("#todayBreakTitle"))
        print("minutes moved off Heute:", await pg.locator("#todayHome [data-break-min]").count() == 0)
        print("mood tile visible:", await pg.is_visible("#todayNewTile"))
        print("mood tile asks, no exercise:", "Wie fühlst du dich heute?" in await pg.inner_text("#todayNewTile") and await pg.locator("#todayNewTile [data-starter]").count() == 0)
        btns = pg.locator("#todayNewTile [data-mood]")
        hs = [(await btns.nth(i).bounding_box())["height"] for i in range(await btns.count())]
        print("three mood buttons >= 44 px, one line:", len(hs) == 3 and all(44 <= h < 60 for h in hs), hs)
        b1 = await pg.locator("#todayBreak").bounding_box(); b2 = await pg.locator("#todayNewTile").bounding_box()
        print("tiles side by side, same height:", abs(b1["y"] - b2["y"]) < 2 and abs(b1["height"] - b2["height"]) < 2)
        print("trainer question shown:", await pg.is_visible("#todayAsk"))
        wk = await pg.locator(".today-week .section-head").bounding_box()
        print("week heading visible on first iPhone screen:", wk["y"] < 844)
        await pg.screenshot(path=OUT + "e_light.png", full_page=True)
        # minutes in the info sheet
        await pg.click("#todayBreakInfoBtn"); await pg.wait_for_timeout(150)
        await pg.click('#breakInfoSheet [data-break-min="3"]'); await pg.wait_for_timeout(80)
        await pg.click("#breakInfoCloseBtn"); await pg.wait_for_timeout(80)
        print("minutes chosen in sheet show on tile:", (await pg.inner_text("#todayBreakStartBtn")).startswith("3 Min."))
        # Allein -> goal row appears, ask disappears
        await pg.click('#todayAsk [data-starter-who="allein"]'); await pg.wait_for_timeout(150)
        print("ask gone after answer:", await pg.is_hidden("#todayAsk"))
        print("goal row shown (Zum Ausprobieren):", await pg.is_visible("#todayGoal") and "ZIEL WÄHLEN" in (await pg.inner_text("#todayGoalHead")).upper())
        await pg.click("#todayGoalHead"); await pg.wait_for_timeout(100)
        await pg.click('#todayGoal [data-starter-goal="fokus"]'); await pg.wait_for_timeout(150)
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-start-v1')"))
        print("goal saved with date:", st.get("goal") == "fokus" and bool(st.get("goalAt")))
        # Tagesform: tap fit -> stored for today, tile switches to the week
        await pg.click('#todayNewTile [data-mood="3"]'); await pg.wait_for_timeout(150)
        md = json.loads(await pg.evaluate("localStorage.getItem('fwmc-mood-v1')"))
        print("mood saved for today:", md.get(datetime.date.today().isoformat(), {}).get("v") == 3)
        print("tile shows the week after answer:", "HEUTE FIT" in (await pg.inner_text("#todayNewTile .today-main-kicker")).upper() and " von " in await pg.inner_text("#todayNewTile .today-mood-week") and "diese Woche" in await pg.inner_text("#todayNewTile"))
        await pg.locator("#todayPair").screenshot(path=OUT + "mood_answered_light.png")
        print("no exercise shown twice on Heute:", await pg.locator("#todayNewTile .starter-card").count() == 0)
        await pg.click("#todayMoodChangeBtn"); await pg.wait_for_timeout(120)
        print("ändern reopens with fit active:", "active" in (await pg.get_attribute('#todayNewTile [data-mood="3"]', "class")))
        await pg.click('#todayNewTile [data-mood="1"]'); await pg.wait_for_timeout(120)
        md = json.loads(await pg.evaluate("localStorage.getItem('fwmc-mood-v1')"))
        print("changed to müde:", md.get(datetime.date.today().isoformat(), {}).get("v") == 1)
        await pg.reload(); await pg.wait_for_timeout(400)
        print("answer survives reload:", "HEUTE MÜDE" in (await pg.inner_text("#todayNewTile .today-main-kicker")).upper())
        await pg.click("#todayMoodProgressBtn"); await pg.wait_for_timeout(200)
        print("Fortschritt shows Tagesform:", await pg.is_visible("#progressMoodGroup") and await pg.locator("#progressMood .mood-cell.m1.today").count() == 1)
        await pg.screenshot(path=OUT + "mood_progress_light.png", full_page=True)
        print("hint line without trainer links to request:", await pg.locator("#todayGoal .today-goal-hint a").count() == 1)
        await pg.screenshot(path=OUT + "e_goal_light.png", full_page=True)
        await ctx.close()

        # 2. unlock code only -> still counts as "no trainer"
        ctx, pg = await page_with(b, {"fwmc-history-v1": H, "fwmc-code-history-v1": [{"code": "x1", "firstUsed": "2026-10-01", "lastUsed": "2026-10-01", "type": "feature-unlock"}]})
        print("unlock code: trainer question still shown:", await pg.is_visible("#todayAsk"))
        await ctx.close()
        # 3. training code (old entry without type) -> no question, compact goal row
        ctx, pg = await page_with(b, {"fwmc-history-v1": H, "fwmc-start-v1": {"who": "allein", "goal": "ruhe", "goalAt": "2026-08-01"},
                                      "fwmc-code-history-v1": [{"code": "abc", "firstUsed": "2026-10-01", "lastUsed": "2026-10-01"}]})
        print("training code: no question:", await pg.is_hidden("#todayAsk"))
        print("goal row compact with trainer:", "is-compact" in (await pg.get_attribute("#todayGoal", "class")))
        print("trainer hint line:", "sprich mit deinem Trainer" in await pg.inner_text("#todayGoal .today-goal-hint"))
        print("6-week check shown:", await pg.is_visible("#todayGoalOkBtn"))
        await pg.click("#todayGoalOkBtn"); await pg.wait_for_timeout(100)
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-start-v1')"))
        print("Ja renews the date:", st.get("goalAt") == datetime.date.today().isoformat() and await pg.is_hidden("#todayGoalOkBtn"))
        await pg.screenshot(path=OUT + "e_trainer_dark.png", full_page=True) if False else None
        await ctx.close()
        # 4. everything tried -> best value tile; dark mode screenshot
        allk = [(1, {"kind": k}) for k in ("remember", "blitz", "balance", "flash", "mot")] + [
            (1, {"kind": "breath", "title": "Box-Atmung"}), (1, {"kind": "breath", "title": "Ruhige Atmung (Kohärenz)"}),
            (1, {"kind": "breath-program", "progKey": "atem-reset", "title": "x"}), (1, {"kind": "exercise", "exId": "vt-color", "title": "VT"}),
            (1, {"kind": "exercise", "exId": "periph-flash", "title": "P"}), (1, {"kind": "workout-plan", "progKey": "workout-start", "title": "K"})]
        for _, e in allk: e.setdefault("title", e["kind"])
        # Tagesform statistics: 12 days, 6 fit (5 trained), 6 müde (1 trained)
        moods, H2 = {}, []
        for d in range(1, 13):
            day = (datetime.date.today() - datetime.timedelta(days=d)).isoformat()
            fit = d % 2 == 0
            moods[day] = {"v": 3 if fit else 1, "at": 0}
            if (fit and d != 2) or d == 1: H2.append((d, {"kind": "breath", "title": "Box-Atmung"}))
        ctx, pg = await page_with(b, {"fwmc-history-v1": hist(*allk, *H2), "fwmc-mood-v1": moods, "fwmc-start-v1": {"who": "allein"}}, "dark")
        await pg.screenshot(path=OUT + "mood_ask_dark.png")
        await pg.evaluate("document.getElementById('todayProgressOpenBtn').click()"); await pg.wait_for_timeout(200)
        sent = await pg.inner_text("#progressMood .mood-sentence")
        print("comparison sentence:", "„müde“-Tagen hast du in 17 %" in sent and "„fit“-Tagen hast du in 83 %" in sent, sent)
        await pg.screenshot(path=OUT + "mood_progress_dark.png", full_page=True)
        await ctx.close()
        # 5. newcomer: unchanged ask in main card, no new tile, pause tile full width
        ctx, pg = await page_with(b, {})
        print("newcomer: no mood tile, pause single:", await pg.is_hidden("#todayNewTile") and "single" in await pg.get_attribute("#todayPair", "class"))
        print("newcomer: ask in main card:", await pg.locator('#todayMain [data-starter-who]').count() == 2)
        await pg.screenshot(path=OUT + "e_new_light.png")
        await ctx.close()
        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
