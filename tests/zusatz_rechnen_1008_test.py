"""Zusatzaufgabe "Rechnen" (Fabian 08.10.2026): a statement like "2 + 3 > 6"
appears on top of a VT canvas exercise; answer by Doppelkreis (inside =
stimmt, ring = stimmt nicht), go/no-go or aloud. Checks the statement maker
(levels, ~50 % true, truth correct), the ready-screen controls + persistence,
placement (below the bar, clear of the arrow), scoring (richtig/falsch/
verpasst) in the done summary, that its taps never reach Farbfelder ·
Antippen, and the Cardio "+ Zusatzaufgabe" picker entry.
Run from tests/ with a dev server (FWMC_PORT, default 8845)."""
import asyncio, json, os, re
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/zusatz_rechnen"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


def py_truth(text):
    a, op, b, rel, c = text.split(" ")
    a, b, c = int(a), int(b), int(c)
    res = a + b if op == "+" else a - b if op == "−" else a * b
    return {"=": res == c, ">": res > c, "<": res < c}[rel], res, (a, b, c)


def seed(vt, addon):
    return INIT + (f"localStorage.setItem('fwmc-webapp-v3', JSON.stringify({json.dumps(vt)}));"
                   f"localStorage.setItem('fwmc-addon-v1', JSON.stringify({json.dumps(addon)}));")


async def new_page(b, init, dark=False, w=390, h=844):
    ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme="dark" if dark else "light")
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg, errs


async def wait_cur(pg, timeout=12000, unanswered=True):
    for _ in range(timeout // 100):
        s = await pg.evaluate("() => window.__math && window.__math.state()")
        if s and s["cur"] and (not unanswered or not s["cur"]["answered"]):
            return s
        await pg.wait_for_timeout(100)
    return None


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    all_errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- 1. statement maker ----
        ctx, pg, errs = await new_page(b, INIT)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        for level, mx in (("plus10", 10), ("plus20", 20), ("mal", 100)):
            sts = await pg.evaluate(f"() => window.__math.make('{level}', 400, 7)")
            trues = sum(1 for s in sts if s["truth"])
            ok_truth = all(py_truth(s["text"])[0] == s["truth"] for s in sts)
            nonneg = all(min(py_truth(s["text"])[2]) >= 0 and py_truth(s["text"])[1] >= 0 for s in sts)
            in_range = all(py_truth(s["text"])[1] <= mx for s in sts)
            check(f"{level}: about half are true", 0.4 <= trues / len(sts) <= 0.6, f"{trues}/{len(sts)}")
            check(f"{level}: truth flag matches the maths", ok_truth)
            check(f"{level}: no negative numbers, results within range", nonneg and in_range)
            rels = {s["rel"] for s in sts}
            check(f"{level}: '=', '>' and '<' all occur", rels == {"=", ">", "<"}, str(rels))
            if level == "mal":
                check("mal: has multiplications", any(s["op"] == "·" for s in sts))
            else:
                check(f"{level}: only plus/minus", all(s["op"] in "+−" for s in sts))
        # ---- 2. ready screen ----
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(300)
        check("Zusatzaufgabe group visible, heading neutral", await pg.is_visible("#addonGroup") and (await pg.inner_text("#addonGroup .group-label")).strip() == "Zusatzaufgabe")
        check("task row hidden while the add-on is off", not await pg.is_visible("#addonTaskRow"))
        await pg.click('[data-addon-phase="pause"]'); await pg.wait_for_timeout(120)
        check("task row appears, Zeichen am Rand is the default", await pg.is_visible("#addonTaskRow") and "active" in await pg.get_attribute('[data-addon-task="periph"]', "class"))
        await pg.click('[data-addon-task="rechnen"]'); await pg.wait_for_timeout(120)
        check("Rechnen shows its own body, hides the periph one", await pg.is_visible("#addonMathBody") and not await pg.is_visible("#addonPeriphBody"))
        check("defaults: Plus/Minus bis 10 + Doppelkreis", "active" in await pg.get_attribute('[data-addon-mathlevel="plus10"]', "class") and "active" in await pg.get_attribute('[data-addon-mathanswer="doppelkreis"]', "class"))
        check("Anzeigedauer 3 s default", (await pg.input_value("#addonMathShowSlider")) == "3")
        await pg.click('[data-addon-mathlevel="mal"]'); await pg.click('[data-addon-mathanswer="gonogo"]'); await pg.wait_for_timeout(100)
        await pg.fill("#addonMathShowSlider", "4.5"); await pg.dispatch_event("#addonMathShowSlider", "input")
        await pg.locator("#addonGroup").screenshot(path=f"{SHOTS}/ready_390_light.png")
        await pg.reload(); await pg.wait_for_timeout(400)
        store = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-addon-v1'))['4-straight']")
        check("persisted per exercise", store["task"] == "rechnen" and store["math"]["level"] == "mal" and store["math"]["answer"] == "gonogo" and store["math"]["stimulusS"] == 4.5, json.dumps(store))
        other = await pg.evaluate("() => (JSON.parse(localStorage.getItem('fwmc-addon-v1'))['4-diag'] || {}).task || 'none'")
        check("another exercise keeps its own add-on", other in ("none", "periph"), other)
        all_errors += errs; await ctx.close()

        # ---- 3. Doppelkreis run on 4 Pfeile gerade, pause phase ----
        vt = {"exercise": "4-straight", "duration": 60, "stimulusS": 1, "intervalMin": 7, "intervalMax": 8}
        addon = {"4-straight": {"phases": ["pause"], "task": "rechnen", "math": {"level": "plus10", "answer": "doppelkreis", "stimulusS": 2.5, "intervalMin": 1, "intervalMax": 1}}}
        ctx, pg, errs = await new_page(b, seed(vt, addon))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(250)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg)
        check("a statement appears", s is not None)
        bar = await pg.evaluate("() => document.getElementById('playerBar').getBoundingClientRect().bottom")
        stage = await pg.evaluate("() => { const r = document.getElementById('stage').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }")
        check("ring and inner disc are both >= 44 px", s["rIn"] * 2 >= 44 and s["R"] - s["rIn"] >= 44, f"R={s['R']:.0f} rIn={s['rIn']:.0f}")
        c = s["cur"]
        check("circle below the player bar and inside the stage", c["cy"] - s["R"] >= bar and c["cx"] - s["R"] >= stage[0] and c["cx"] + s["R"] <= stage[2] and c["cy"] + s["R"] <= stage[3],
              f"cy={c['cy']:.0f} R={s['R']:.0f} bar={bar:.0f}")
        check("pause-phase statements keep the fixation point free", all(i["overlap"] == 0 for i in s["items"]))
        await pg.screenshot(path=f"{SHOTS}/run_doppelkreis_390_light.png")
        # tap inside -> "stimmt"
        truth1 = c["truth"]
        await pg.mouse.click(c["cx"], c["cy"]); await pg.wait_for_timeout(120)
        s2 = await pg.evaluate("() => window.__math.state()")
        check("inside tap counts as 'stimmt'", (s2["ok"], s2["bad"]) == ((1, 0) if truth1 else (0, 1)), f"truth={truth1} ok={s2['ok']} bad={s2['bad']}")
        check("statement disappears after the answer", s2["cur"] is None or s2["cur"]["answered"])
        # next one: tap the ring -> "stimmt nicht"
        s = await wait_cur(pg)
        c = s["cur"]; truth2 = c["truth"]
        ring = (s["R"] + s["rIn"]) / 2
        await pg.mouse.click(c["cx"], c["cy"] + ring); await pg.wait_for_timeout(120)
        s3 = await pg.evaluate("() => window.__math.state()")
        exp_ok = (1 if truth1 else 0) + (0 if truth2 else 1)
        check("ring tap counts as 'stimmt nicht'", s3["ok"] == exp_ok and s3["ok"] + s3["bad"] == 2, f"truth2={truth2} ok={s3['ok']} bad={s3['bad']}")
        # a tap outside the circle is not an answer
        s = await wait_cur(pg)
        c = s["cur"]
        far_x = stage[0] + 10 if c["cx"] > (stage[0] + stage[2]) / 2 else stage[2] - 10
        await pg.mouse.click(far_x, stage[3] - 10 if c["cy"] < (stage[1] + stage[3]) / 2 else bar + 10); await pg.wait_for_timeout(100)
        s4 = await pg.evaluate("() => window.__math.state()")
        check("tap beside the circle is ignored", s4["ok"] + s4["bad"] == 2)
        # let it run out -> verpasst
        cur_id = c["id"]
        for _ in range(60):
            s5 = await pg.evaluate("() => window.__math.state()")
            if not s5["cur"] or s5["cur"]["id"] != cur_id: break
            await pg.wait_for_timeout(100)
        # the engine closes it on its next frame (state() reads the wall clock)
        for _ in range(20):
            if s5["miss"] >= 1: break
            await pg.wait_for_timeout(100)
            s5 = await pg.evaluate("() => window.__math.state()")
        check("unanswered statement counts as verpasst", s5["miss"] >= 1, f"miss={s5['miss']}")
        # pause: taps on the sheet do nothing
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        check("pause sheet opens", await pg.is_visible("#periphPauseOverlay"))
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => window.__mathFinishRun()"); await pg.wait_for_timeout(300)
        summ = await pg.inner_text("#doneSummary")
        check("done summary names the Rechnen score", re.search(r"Rechnen: \d+ richtig, \d+ falsch, \d+ verpasst", summ) is not None, summ)
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")
        last = hist[0] if hist and isinstance(hist, list) else {}
        if isinstance(hist, list) and hist and hist[-1].get("ts", 0) > last.get("ts", 0): last = hist[-1]
        check("history note carries the score", "Rechnen:" in (last.get("note") or ""), str(last.get("note")))
        await pg.screenshot(path=f"{SHOTS}/done_390_light.png")
        all_errors += errs; await ctx.close()

        # ---- 4. Reiz phase: statements keep clear of the arrow ----
        vt = {"exercise": "4-straight", "duration": 60, "stimulusS": 3, "intervalMin": 1, "intervalMax": 1}
        addon = {"4-straight": {"phases": ["reiz"], "task": "rechnen", "math": {"level": "plus20", "answer": "doppelkreis", "stimulusS": 2, "intervalMin": 1, "intervalMax": 1}}}
        ctx, pg, errs = await new_page(b, seed(vt, addon))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(250)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg)
        clear = sum(1 for i in s["items"] if i["overlap"] == 0)
        check("Reiz phase: statements placed clear of the arrow", clear >= len(s["items"]) * 0.9 and len(s["items"]) > 5, f"{clear}/{len(s['items'])}")
        await pg.screenshot(path=f"{SHOTS}/run_reiz_arrow_390_light.png")
        all_errors += errs; await ctx.close()

        # ---- 5. go/no-go and aloud ----
        vt = {"exercise": "8-solo", "duration": 60, "stimulusS": 1, "intervalMin": 7, "intervalMax": 8}
        addon = {"8-solo": {"phases": ["pause"], "task": "rechnen", "math": {"level": "plus10", "answer": "gonogo", "stimulusS": 1.5, "intervalMin": 1, "intervalMax": 1}}}
        ctx, pg, errs = await new_page(b, seed(vt, addon), dark=True)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(250)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg)
        check("go/no-go: single disc (R == rIn)", abs(s["R"] - s["rIn"]) < 0.5 and s["R"] * 2 >= 44)
        await pg.screenshot(path=f"{SHOTS}/run_gonogo_390_dark.png")
        tapped_true = None
        for _ in range(8):
            s = await wait_cur(pg)
            c = s["cur"]
            if c["truth"]:
                await pg.mouse.click(c["cx"], c["cy"]); tapped_true = True; break
            # leave a false one alone
            cid = c["id"]
            for _ in range(40):
                s = await pg.evaluate("() => window.__math.state()")
                if not s["cur"] or s["cur"]["id"] != cid: break
                await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(100)
        await pg.evaluate("() => window.__mathFinishRun()"); await pg.wait_for_timeout(250)
        sc = await pg.evaluate("() => window.__mathLastScore")
        wrong = [l for l in sc["log"] if l["result"] != "richtig"]
        check("go/no-go: tapping a true one and leaving false ones = all richtig", tapped_true and sc["ok"] >= 1 and not wrong, json.dumps(sc["log"])[:300])
        all_errors += errs; await ctx.close()

        addon = {"8-solo": {"phases": ["pause"], "task": "rechnen", "math": {"level": "plus10", "answer": "laut", "stimulusS": 1.5, "intervalMin": 1, "intervalMax": 1}}}
        ctx, pg, errs = await new_page(b, seed(vt, addon))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="8-solo"]'); await pg.wait_for_timeout(250)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg)
        await pg.mouse.click(s["cur"]["cx"], s["cur"]["cy"]); await pg.wait_for_timeout(100)
        s = await pg.evaluate("() => window.__math.state()")
        check("Laut sagen: taps are not scored", s["ok"] + s["bad"] == 0)
        await pg.evaluate("() => window.__mathFinishRun()"); await pg.wait_for_timeout(250)
        check("Laut sagen: no score in the summary", "Rechnen" not in await pg.inner_text("#doneSummary"))
        all_errors += errs; await ctx.close()

        # ---- 6. Farbfelder · Antippen: a tap on the statement never reaches the grid ----
        vt = {"exercise": "farbfelder", "duration": 60, "stimulusS": 1, "intervalMin": 7, "intervalMax": 8, "ffAnswer": "tippen", "ffMode": "leuchten"}
        addon = {"farbfelder": {"phases": ["pause", "reiz"], "task": "rechnen", "math": {"level": "plus10", "answer": "doppelkreis", "stimulusS": 2.5, "intervalMin": 1, "intervalMax": 1}}}
        ctx, pg, errs = await new_page(b, seed(vt, addon))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg)
        before = await pg.evaluate("() => window.__ffTap && window.__ffTap()")
        check("Farbfelder tapping run is on", before is not None)
        await pg.mouse.click(s["cur"]["cx"], s["cur"]["cy"]); await pg.wait_for_timeout(120)
        after = await pg.evaluate("() => window.__ffTap()")
        s2 = await pg.evaluate("() => window.__math.state()")
        n_items = lambda t: sum(1 for i in t["items"] if i.get("got") is not None or i.get("tap") is not None or i.get("field") is not None)
        check("statement tap scored for Rechnen", s2["ok"] + s2["bad"] == 1)
        check("statement tap did not reach Farbfelder", json.dumps(before["items"]) == json.dumps(after["items"]) and (before["cur"] or {}).get("got") == (after["cur"] or {}).get("got"),
              json.dumps(after["cur"])[:200])
        await pg.screenshot(path=f"{SHOTS}/run_farbfelder_390_light.png")
        all_errors += errs; await ctx.close()

        # ---- 7. Cardio "+ Zusatzaufgabe" picker ----
        ctx, pg, errs = await new_page(b, INIT)
        await pg.goto(BASE + "?bereich=cardio"); await pg.wait_for_timeout(500)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(1500)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        heads = await pg.locator("#cardioAddonPickerTypeRow .cardio-addon-picker-group-label").all_inner_texts()
        check("picker: own group 'Weitere Zusatzaufgaben' at the end", heads[-1] == "Weitere Zusatzaufgaben", str(heads))
        last = pg.locator("#cardioAddonPickerTypeRow .choice").last
        check("picker: last choice is Rechnen", "Rechnen" in await last.inner_text())
        await last.click(); await pg.wait_for_timeout(100)
        det = pg.locator("#cardioAddonPickerDetail")
        check("picker: Rechenart + So antwortest du offered", await det.locator('[data-balf="level"]').count() == 3 and await det.locator('[data-balf="answer"]').count() == 3)
        await det.locator('[data-balf="answer"][data-balv="gonogo"]').click(); await pg.wait_for_timeout(80)
        await pg.locator("#cardioAddonPicker").screenshot(path=f"{SHOTS}/cardio_picker_390_light.png")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        s = await wait_cur(pg, unanswered=False)
        check("Cardio guest runs Rechnen with the live choice", s is not None and s["answer"] == "gonogo")
        await pg.screenshot(path=f"{SHOTS}/cardio_run_390_light.png")
        saved = await pg.evaluate("() => (JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1') || '{}').perType || {})['addon-math']")
        check("live picker choice not written back", not saved or saved.get("answer") == "doppelkreis", json.dumps(saved))
        all_errors += errs; await ctx.close()

        await b.close()
    print("ERRORS:", all_errors)
    print(f"{sum(results)}/{len(results)} checks passed")
    if all_errors or not all(results):
        raise SystemExit(1)

asyncio.run(main())
