"""Farbfelder · Antippen + Matten-Anordnung per Halten und Ziehen (Fabian 08.10.2026).
- "So antwortest du": Treten (default) / Antippen; persists, travels in presets
  and Kombi blocks, Cardio guest always treads.
- Antippen: first tap in a stimulus' window counts (right / wrong / missed),
  Abfolge merken scores rounds, done summary + history note show the score.
- Layout grid: drag a field onto another (mouse and long-press touch) swaps
  the two colours and persists.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/farbfelder_tippen"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

async def open_ff(pg):
    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)

async def field_xy(pg, i):
    g = await pg.evaluate("() => window.__ffLastGeom")
    w = (g["right"] - g["left"]) / 2; h = (g["bottom"] - g["top"]) / 2
    return g["left"] + (i % 2 + 0.5) * w, g["top"] + (i // 2 + 0.5) * h

async def wait_for(pg, js, timeout=15000, arg=None):
    t = 0
    while t < timeout:
        v = await pg.evaluate(js, arg)
        if v: return v
        await pg.wait_for_timeout(50); t += 50
    return None

# A fresh, still unanswered stimulus (not the one with t0 = skip_t0).
NEW_STIM = """(skip) => { const s = window.__ffTap(); if (!s || !s.cur || s.cur.done) return null;
  if (skip !== null && Math.abs(s.cur.t0 - skip) < 1e-6) return null; return s.cur; }"""

async def cell_center(pg, i):
    b = await pg.locator(f'#ffLayoutGrid [data-ff-cell="{i}"]').bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

def layout(raw): return json.loads(raw)["ffLayout"]

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- ready screen: answer group ----
        await open_ff(pg)
        check("answer group visible", await pg.is_visible("#ffAnswerGroup") and "So antwortest du" in await pg.inner_text("#ffAnswerGroup"))
        check("Treten is the default", "active" in (await pg.get_attribute('[data-ff-answer="treten"]', "class")))
        check("treten: Hilfsmittel, Fuß-Vorgabe, Hände shown", await pg.is_visible("#hilfsmittelNote") and await pg.is_visible("#ffFootGroup") and await pg.is_visible("#ffHandsGroup"))
        check("treten: no Haken & Kreuz row", not await pg.is_visible("#ffFbRow"))
        check("layout label + tag", "Anordnung deiner Matte" in await pg.inner_text("#ffLayoutGroup .group-label") and await pg.is_visible("#ffLayoutGroup .ff-tag"))
        help_t = await pg.inner_text("#ffLayoutHelp")
        check("layout help explains drag and colour pick", "Halte ein Feld gedrückt" in help_t and "tauschen den Platz" in help_t and "Leg deine Matte genauso hin" in help_t, help_t)
        check("every cell shows a grip icon", await pg.locator("#ffLayoutGrid .ff-cell .ff-grip").count() == 4)
        await pg.click('[data-ff-answer="tippen"]'); await pg.wait_for_timeout(80)
        check("Antippen active", "active" in (await pg.get_attribute('[data-ff-answer="tippen"]', "class")))
        check("tippen: Hilfsmittel, Fuß-Vorgabe, Hände hidden", not await pg.is_visible("#hilfsmittelNote") and not await pg.is_visible("#ffFootGroup") and not await pg.is_visible("#ffHandsGroup"))
        check("tippen: Haken & Kreuz row shown, off by default", await pg.is_visible("#ffFbRow") and "active" in (await pg.get_attribute('#ffFbRow [data-cvd-val="0"]', "class")))
        check("tippen: mode help says Tippe", "Tippe" in await pg.inner_text("#ffModeHelp"))
        check("tippen: rules box without treading", "tippst" in await pg.inner_text("#rulesBox") and "trittst" not in await pg.inner_text("#rulesBox"))
        check("tippen: small mode text", "nachtippen" in await pg.inner_text('[data-ff-mode="abfolge"]'))
        check("tippen: layout help without the mat sentence", "Matte genauso" not in await pg.inner_text("#ffLayoutHelp"))
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(150)
            await pg.screenshot(path=f"{SHOTS}/ready_tippen_{scheme}.png", full_page=True)
        await pg.emulate_media(color_scheme="light")
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("ffAnswer persists across reload", "active" in (await pg.get_attribute('[data-ff-answer="tippen"]', "class")))
        check("snapshot carries ffAnswer", (await pg.evaluate("() => window.__ff.snapshot().ffAnswer")) == "tippen")

        # ---- Leuchten: right / wrong / missed ----
        await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("tap run has a tap state", await pg.evaluate("() => !!window.__ffTap()"))
        nofoot = await pg.evaluate("() => window.__ff.build({ffAnswer:'tippen', ffFoot:'wechsel', ffHands:true}).filter(f => f.kind === 'farbfelder').every(f => !f.payload.foot && !f.payload.hand)")
        check("tippen: no foot badge, no hand task", nofoot)
        s1 = await wait_for(pg, NEW_STIM, arg=None)
        x, y = await field_xy(pg, s1["target"])
        await pg.mouse.click(x, y); await pg.wait_for_timeout(60)
        st = await pg.evaluate("() => window.__ffTap()")
        check("tap on the target counts as right", st["cur"]["done"] and st["cur"]["ok"] and st["cur"]["rt"] is not None, st["cur"])
        await pg.screenshot(path=f"{SHOTS}/run_tap_neutral.png")
        await pg.mouse.click(*(await field_xy(pg, (s1["target"] + 1) % 4))); await pg.wait_for_timeout(60)
        st = await pg.evaluate("() => window.__ffTap()")
        check("a second tap in the same window is ignored", st["cur"]["ok"] and st["cur"]["field"] == s1["target"])
        s2 = await wait_for(pg, NEW_STIM, arg=s1["t0"])
        await pg.mouse.click(*(await field_xy(pg, (s2["target"] + 1) % 4))); await pg.wait_for_timeout(60)
        st = await pg.evaluate("() => window.__ffTap()")
        check("tap on another field counts as wrong", st["cur"]["done"] and not st["cur"]["ok"], st["cur"])
        s3 = await wait_for(pg, NEW_STIM, arg=s2["t0"])
        s4 = await wait_for(pg, NEW_STIM, arg=s3["t0"])
        st = await pg.evaluate("() => window.__ffTap()")
        check("no tap = missed", len(st["items"]) == 3 and not st["items"][2]["done"] and [i["ok"] for i in st["items"]] == [True, False, False], [(i["done"], i["ok"]) for i in st["items"]])
        # tick/cross on: drawn on the canvas, screenshot
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        check("pause sheet offers Haken & Kreuz", await pg.is_visible("#vtPauseFfFbGroup"))
        await pg.click('#vtPauseFfFbGroup [data-cvd-val="1"]'); await pg.wait_for_timeout(60)
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(100)
        s5 = await wait_for(pg, NEW_STIM, arg=s4["t0"])
        await pg.mouse.click(*(await field_xy(pg, s5["target"]))); await pg.wait_for_timeout(80)
        await pg.screenshot(path=f"{SHOTS}/run_tap_haken.png")
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        summ = await pg.inner_text("#doneSummary")
        sc = await pg.evaluate("() => window.__ffTapLastScore")
        check("done summary shows the score", f"{sc['hits']} von {sc['total']} richtig" in summ and "Ø" in summ and "," in summ.split("Ø")[1], summ)
        check("score counts right taps", sc["hits"] == 2 and sc["total"] >= 5, sc)
        hist_note = await pg.evaluate("() => { const h = JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]'); return h.map(e => e.note || '').filter(n => n.includes('Antippen')); }")
        check("history note has the score", any("richtig" in n for n in hist_note), hist_note)
        await pg.screenshot(path=f"{SHOTS}/done_leuchten.png")
        await pg.evaluate("() => { const x = [...document.querySelectorAll('#cvdOverrideReset, [data-cvd-reset=\"farbfelder:fb\"]')][0]; if (x) x.click(); }")

        # ---- Abfolge merken: rounds ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-mode="abfolge"]'); await pg.click('[data-ff-seq="2"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        r1 = await wait_for(pg, "() => { const s = window.__ffTap(); return s && s.round && s.round.input && s.round.pos === 0 ? s.round : null; }")
        for f in r1["seq"]:
            await pg.mouse.click(*(await field_xy(pg, f))); await pg.wait_for_timeout(80)
        st = await pg.evaluate("() => window.__ffTap()")
        check("Abfolge: whole sequence tapped", st["round"]["pos"] == len(r1["seq"]) and not st["round"]["failed"], st["round"])
        await pg.screenshot(path=f"{SHOTS}/run_abfolge.png")
        r2 = await wait_for(pg, "() => { const s = window.__ffTap(); return s && s.round && s.round.input && s.round.pos === 0 && !s.round.failed && s.rounds.length === 1 ? s.round : null; }", timeout=20000)
        await pg.mouse.click(*(await field_xy(pg, (r2["seq"][0] + 1) % 4))); await pg.wait_for_timeout(60)
        await pg.mouse.click(*(await field_xy(pg, r2["seq"][1]))); await pg.wait_for_timeout(60)
        st = await pg.evaluate("() => window.__ffTap()")
        check("Abfolge: a wrong tap ends the round's input", st["round"]["failed"] and st["round"]["pos"] == 0, st["round"])
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        summ = await pg.inner_text("#doneSummary")
        check("Abfolge: summary rounds + longest", "1 von 2 Runden richtig" in summ and "längste Folge 2" in summ, summ)

        # ---- Kombi: block keeps its own answer mode ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="treten"]'); await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbfelder")'); await pg.wait_for_timeout(250)
        await pg.click('[data-ff-answer="tippen"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        std = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).ffAnswer")
        check("Kombi: standalone stays Treten", std == "treten", std)
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-opens with Antippen", "active" in (await pg.get_attribute('[data-ff-answer="tippen"]', "class")))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(900)
        check("Kombi: block plays as a tap run", await pg.evaluate("() => !!window.__ffTap()"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Cardio guest always treads ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="tippen"]'); await pg.wait_for_timeout(60)
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Farbfelder")'); await pg.wait_for_timeout(120)
        check("Cardio picker: no Antippen choice", "Antippen" not in await pg.inner_text("#cardioAddonPickerDetail"))
        await pg.evaluate("() => { window.__ffLastGeom = null; }")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(700)
        check("Cardio guest runs without tap scoring", await pg.evaluate("() => !!window.__ffLastGeom") and await pg.evaluate("() => window.__ffTap() === null"))

        # ---- Layout: drag-swap with the mouse ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.ffLayout = ['rot','blau','gelb','gruen']; s.ffHandRules = {rot:'hoch'}; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="treten"]'); await pg.wait_for_timeout(60)
        await pg.evaluate("() => document.getElementById('ffLayoutGrid').scrollIntoView({block: 'center'})"); await pg.wait_for_timeout(100)  # centre: the sticky start bar must not cover the bottom row
        x0, y0 = await cell_center(pg, 0); x3, y3 = await cell_center(pg, 3)
        await pg.mouse.move(x0, y0); await pg.mouse.down()
        await pg.mouse.move(x0 + 3, y0 + 3); await pg.wait_for_timeout(30)
        check("mouse: no drag below 6 px", await pg.locator(".ff-ghost").count() == 0)
        for k in range(1, 9):
            await pg.mouse.move(x0 + (x3 - x0) * k / 8, y0 + (y3 - y0) * k / 8); await pg.wait_for_timeout(20)
        check("mouse: lifted copy follows", await pg.locator(".ff-ghost").count() == 1)
        gb = await pg.evaluate("() => { const r = document.querySelector('.ff-ghost').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }")
        check("mouse: lifted copy sits under the pointer", gb[0] <= x3 <= gb[2] and gb[1] <= y3 <= gb[3], gb)
        check("mouse: target cell highlighted", "ff-drop-target" in (await pg.get_attribute('#ffLayoutGrid [data-ff-cell="3"]', "class")))
        await pg.screenshot(path=f"{SHOTS}/drag_mouse.png")
        await pg.mouse.up(); await pg.wait_for_timeout(120)
        lay = layout(await pg.evaluate("() => localStorage.getItem('fwmc-webapp-v3')"))
        check("mouse: drop swaps the two colours", lay == ["gruen", "blau", "gelb", "rot"], lay)
        check("mouse: ghost removed", await pg.locator(".ff-ghost").count() == 0)
        check("cells show the new colours", (await pg.inner_text('#ffLayoutGrid [data-ff-cell="0"]')).strip() == "Grün" and (await pg.inner_text('#ffLayoutGrid [data-ff-cell="3"]')).strip() == "Rot")
        rules = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).ffHandRules")
        check("hand rule stays with its colour", rules == {"rot": "hoch"}, rules)
        # drop outside = cancel
        x1, y1 = await cell_center(pg, 1)
        await pg.mouse.move(x1, y1); await pg.mouse.down()
        for k in range(1, 6): await pg.mouse.move(x1, y1 + 60 * k); await pg.wait_for_timeout(15)
        await pg.mouse.move(x1, 20); await pg.mouse.up(); await pg.wait_for_timeout(450)
        lay2 = layout(await pg.evaluate("() => localStorage.getItem('fwmc-webapp-v3')"))
        check("mouse: drop outside cancels", lay2 == lay, lay2)
        # plain click still selects a cell for the colour picker
        await pg.click('#ffLayoutGrid [data-ff-cell="2"]'); await pg.wait_for_timeout(60)
        check("tap selects the cell", "active" in (await pg.get_attribute('#ffLayoutGrid [data-ff-cell="2"]', "class")) and "Unten links" in await pg.inner_text("#ffLayoutHelp"))
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("swap persists across reload", (await pg.inner_text('#ffLayoutGrid [data-ff-cell="0"]')).strip() == "Grün")

        # ---- Layout: long-press touch drag (CDP touch events) ----
        tctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", has_touch=True, is_mobile=True)
        await tctx.add_init_script(INIT)
        tp = await tctx.new_page()
        tp.on("pageerror", lambda e: errors.append("pageerror(touch): " + str(e)))
        tp.on("console", lambda m: errors.append("console(touch): " + m.text) if m.type == "error" else None)
        await tp.goto(URL); await tp.wait_for_timeout(400)
        await tp.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}'); s.ffLayout = ['rot','blau','gelb','gruen']; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await tp.reload(); await tp.wait_for_timeout(400)
        await tp.click('.excard[data-exercise="farbfelder"]'); await tp.wait_for_timeout(300)
        await tp.locator("#ffLayoutGrid").scroll_into_view_if_needed(); await tp.wait_for_timeout(150)
        cdp = await tctx.new_cdp_session(tp)
        a = await cell_center(tp, 1); z = await cell_center(tp, 2)
        async def touch(kind, x, y):
            pts = [] if kind == "touchEnd" else [{"x": x, "y": y, "id": 1}]
            await cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": pts})
        # a quick swipe over the grid does not drag
        await touch("touchStart", *a)
        for k in range(1, 6): await touch("touchMove", a[0], a[1] - 12 * k); await tp.wait_for_timeout(15)
        await touch("touchEnd", 0, 0); await tp.wait_for_timeout(100)
        check("touch: a quick move is no drag", await tp.locator(".ff-ghost").count() == 0 and layout(await tp.evaluate("() => localStorage.getItem('fwmc-webapp-v3')")) == ["rot", "blau", "gelb", "gruen"])
        a = await cell_center(tp, 1); z = await cell_center(tp, 2)
        await touch("touchStart", *a); await tp.wait_for_timeout(380)
        check("touch: long press lifts the field", await tp.locator(".ff-ghost").count() == 1)
        sy0 = await tp.evaluate("() => scrollY")
        for k in range(1, 9):
            await touch("touchMove", a[0] + (z[0] - a[0]) * k / 8, a[1] + (z[1] - a[1]) * k / 8); await tp.wait_for_timeout(20)
        await tp.screenshot(path=f"{SHOTS}/drag_touch.png")
        check("touch: page does not scroll while dragging", await tp.evaluate("() => scrollY") == sy0)
        await touch("touchEnd", 0, 0); await tp.wait_for_timeout(150)
        lay = layout(await tp.evaluate("() => localStorage.getItem('fwmc-webapp-v3')"))
        check("touch: drop swaps the two colours", lay == ["rot", "gelb", "blau", "gruen"], lay)
        await tctx.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
