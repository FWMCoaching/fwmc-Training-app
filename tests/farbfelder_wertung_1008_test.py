"""Farbfelder · Antippen: Wertung im Kombi-Programm + Stufen-Vorschlag (Fabian 08.10.2026).
- A tap block in a Kombi reports its score: "Eben: …" in the pause before the
  next block, a list on the closing panel, and the combo history note.
- Coach programme pause screen + done panel use the same helper (checked
  through the DOM elements existing; no live coach code needed).
- Stufen-Vorschlag: 3 very good tap runs in a row on Mittel suggest Schwer;
  accepting sets the VT tempo; a weak run resets the streak; mute works.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "if (!localStorage.getItem('fwmc-master-v1')) localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false, defaultPauseS:20}));")
SHOTS = "screenshots/farbfelder_wertung"

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

async def wait_for(pg, js, timeout=20000, arg=None):
    t = 0
    while t < timeout:
        v = await pg.evaluate(js, arg)
        if v: return v
        await pg.wait_for_timeout(50); t += 50
    return None

NEW_STIM = """(skip) => { const s = window.__ffTap(); if (!s || !s.cur || s.cur.done) return null;
  if (skip !== null && Math.abs(s.cur.t0 - skip) < 1e-6) return null; return s.cur; }"""

async def tap_n(pg, n, right=True):
    last = None
    for _ in range(n):
        s = await wait_for(pg, NEW_STIM, arg=last)
        if not s: return False
        f = s["target"] if right else (s["target"] + 1) % 4
        await pg.mouse.click(*(await field_xy(pg, f))); await pg.wait_for_timeout(60)
        last = s["t0"]
    return True

def hist(pg):
    return pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")

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

        # ---- Kombi with two Farbfelder tap blocks ----
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        for mode in ("leuchten", "leuchten"):
            await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbfelder")'); await pg.wait_for_timeout(250)
            await pg.click('[data-ff-answer="tippen"]'); await pg.click(f'[data-ff-mode="{mode}"]'); await pg.click('[data-tempo="mittel"]'); await pg.wait_for_timeout(60)
            await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("two blocks in the Kombi", await pg.locator("#comboBlockList .chapter-main").count() == 2)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(600)
        check("block 1 is a tap run", await pg.evaluate("() => !!window.__ffTap()"))
        check("block 1: two right taps", await tap_n(pg, 2))
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        check("pause between blocks visible", await pg.is_visible("#comboTransition"))
        res = await pg.inner_text("#comboTransitionResult") if await pg.is_visible("#comboTransitionResult") else ""
        check("pause shows the block's score", res.startswith("Eben: Farbfelder · Leuchten") and "2 von 2 richtig" in res and "Ø" in res, res)
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/kombi_pause_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(500)
        check("block 2: one right, one wrong", await tap_n(pg, 1) and await tap_n(pg, 1, right=False))
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(400)
        check("Kombi done panel visible", await pg.is_visible("#comboDonePanel"))
        items = await pg.locator("#comboDoneResults li").all_inner_texts()
        check("done panel lists both blocks", len(items) == 2 and "2 von 2 richtig" in items[0] and "1 von 2 richtig" in items[1], items)
        h = await hist(pg)
        combo = [e for e in h if e.get("kind") == "combo"]
        check("combo history note carries the scores", combo and "Farbfelder · Leuchten: 2 von 2 richtig" in (combo[-1].get("note") or "") and "1 von 2 richtig" in combo[-1]["note"], combo[-1].get("note") if combo else None)
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/kombi_done_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        # "Nochmal von vorne" starts with an empty result list
        await pg.click("#comboAgainBtn"); await pg.wait_for_timeout(500)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        res = await pg.inner_text("#comboTransitionResult")
        check("again: fresh score, 0 taps", "0 von" in res, res)
        await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        check("again: list has only this run's 2 blocks", await pg.locator("#comboDoneResults li").count() == 2)
        await pg.click("#comboDoneBackBtn"); await pg.wait_for_timeout(200)

        # A Kombi without scored blocks shows no list.
        check("coach programme elements exist", await pg.locator("#pauseResult").count() == 1 and await pg.locator("#programDoneResults").count() == 1)

        # ---- Stufen-Vorschlag ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks: {'farbfelder:leuchten:mittel': 2}, muted: {}}))")
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}'); Object.assign(s, {stimulusS:1.5, intervalMin:3, intervalMax:6, duration:60}); localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="tippen"]'); await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
        # weak run first: resets the streak, no suggestion
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        await tap_n(pg, 2, right=False)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        check("weak run: no suggestion", await pg.locator("#donePanel .level-suggest").count() == 0)
        st = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-level-suggest-v1')).streaks['farbfelder:leuchten:mittel']")
        check("weak run resets the streak", st == 0, st)
        # three good runs (≥ 5 fields, ≥ 90 %) -> suggestion
        await pg.evaluate("() => localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks: {'farbfelder:leuchten:mittel': 2}, muted: {}}))")
        await pg.click("#againBtn"); await pg.wait_for_timeout(200)
        check("good run: five right taps", await tap_n(pg, 5))
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        box = pg.locator("#donePanel .level-suggest")
        check("suggestion after the 3rd good run", await box.count() == 1 and "Schwer" in await box.inner_text(), await box.inner_text() if await box.count() else "")
        await pg.screenshot(path=f"{SHOTS}/vorschlag.png")
        await pg.click("#donePanel .level-suggest-yes"); await pg.wait_for_timeout(100)
        check("accept text names Tempo", "„Tempo“" in await box.inner_text(), await box.inner_text())
        tempo = await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); return [s.stimulusS, s.intervalMin, s.intervalMax]; }")
        check("accept sets VT tempo Schwer", tempo == [0.8, 2, 4], tempo)
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("tempo persists after reload (Schwer active)", "active" in (await pg.get_attribute('[data-tempo="schwer"]', "class")))
        # Schwer is the top: never a suggestion; another exercise's panel has none
        await pg.evaluate("() => localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks: {'farbfelder:leuchten:schwer': 5}, muted: {}}))")
        await pg.click('[data-ff-answer="tippen"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        check("Schwer: no suggestion", await pg.locator("#donePanel .level-suggest").count() == 0)
        # mute
        await pg.click("#doneBackBtn"); await pg.wait_for_timeout(200)
        if not await pg.is_visible("#startBtn"): await open_ff(pg)
        await pg.evaluate("() => localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks: {}, muted: {farbfelder: true}}))")
        await pg.click('[data-tempo="mittel"]'); await pg.wait_for_timeout(60)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-level-suggest-v1')); s.streaks['farbfelder:leuchten:mittel'] = 5; localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify(s)); }")
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        await tap_n(pg, 5)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        check("muted: no suggestion", await pg.locator("#donePanel .level-suggest").count() == 0)
        # Treten runs never count
        await pg.click("#doneBackBtn"); await pg.wait_for_timeout(200)
        if not await pg.is_visible("#startBtn"): await open_ff(pg)
        await pg.evaluate("() => localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks: {'farbfelder:leuchten:mittel': 5}, muted: {}}))")
        await pg.click('[data-ff-answer="treten"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(1500)
        await pg.click("#liveEndBtn") if await pg.is_visible("#liveEndBtn") else await pg.evaluate("() => document.getElementById('liveEndBtn').click()")
        await pg.wait_for_timeout(300)
        check("treten: no suggestion", await pg.locator("#donePanel .level-suggest").count() == 0)

        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
