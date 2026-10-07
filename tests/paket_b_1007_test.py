"""Paket B (Fabian 06./07.10.2026, Ideen 47/48/50/51): Weitermachen beim
Kraftplan and the Ausdauer-Einheit, "Kurz anhalten" on the "Weiter geht's"
panel (Atem-Programm, Workout-Plan), Eigenes Training says the next point.
Run from tests/ with a dev server on :8845."""
import asyncio, json, time
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-bottomnav','1');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
        "localStorage.setItem('fwmc-history-v1', JSON.stringify([{id:'1',ts:'2026-10-01T08:00:00Z',kind:'breath',title:'Box-Atmung'},{id:'2',ts:'2026-10-02T08:00:00Z',kind:'breath',title:'Box-Atmung'},{id:'3',ts:'2026-10-03T08:00:00Z',kind:'breath',title:'Box-Atmung'}]));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- 47 Kraftplan: note at each set, Heute offers it, resumes at that set ----
        plan = {"items": [{"exercise": "kniebeuge", "sets": 2, "restS": 0, "restAfterS": 0}, {"exercise": "liegestuetz", "sets": 2, "restS": 0}], "exerciseRestS": 0, "prepS": 0}
        await pg.goto(BASE + "?bereich=workout"); await pg.wait_for_timeout(300)
        await pg.evaluate("(pl) => { localStorage.setItem('fwmc-workout-reps-builder-v1', JSON.stringify(pl)); }", plan)
        await pg.goto(BASE + "?bereich=workout"); await pg.wait_for_timeout(400)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(300); await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(600)
        for _ in range(4):
            if await pg.is_visible("#workoutRestSkipBtn"):
                await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(300)
            elif await pg.is_visible("#workoutSetDoneBtn"):
                await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(400)
        rec = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-resume-single-v1') || 'null')")
        check("Kraftplan noted its set", rec and rec.get("kind") == "strength" and rec.get("pos", 0) >= 1, json.dumps(rec)[:160] if rec else "none")
        if not rec or rec.get("kind") != "strength":
            rec = {"type": "single", "kind": "strength", "title": "Kraftplan · 2 Übungen", "plan": {"kind": "strength", **plan}, "idx": 2, "pos": 2, "total": 4, "played": 90, "ts": int(time.time() * 1000)}
            await pg.evaluate("(r) => localStorage.setItem('fwmc-resume-single-v1', JSON.stringify(r))", rec)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        main = await pg.inner_text("#todayMain")
        check("Heute: Weitermachen Kraftplan with 'Satz x von y'", "weitermachen" in main.lower() and "Satz " in main, main[:120])
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(500)
        check("resumes in the Kraft player", await pg.is_visible("#workoutPlayer"))
        idx = await pg.evaluate("() => { const t = document.getElementById('workoutPlayer').innerText; return t; }")
        check("resumed at the noted set, not set 1 of exercise 1", rec["idx"] < 2 or "Liegest" in idx, idx[:120])
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(300)

        # ---- 48 Ausdauer: seeded note, Fortsetzen keeps index + rest ----
        items = [{"activity": "laufen", "durationS": 300}, {"activity": "radfahren", "durationS": 300}]
        crec = {"type": "single", "kind": "cardio", "title": "Ausdauertraining", "program": None, "items": items, "index": 1, "blockS": 100,
                "total": 600, "rest": 200, "played": 400, "ts": int(time.time() * 1000)}
        await pg.evaluate("(r) => localStorage.setItem('fwmc-resume-single-v1', JSON.stringify(r))", crec)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        main = await pg.inner_text("#todayMain")
        check("Heute: Weitermachen Ausdauer 'noch 4 Min.'", "Ausdauertraining" in main and "noch 4" in main, main[:120])
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(600)
        check("cardio player open", await pg.is_visible("#cardioPlayer"))
        cd = await pg.inner_text("#cardioCountdown")
        check("second activity with its rest (~3:20)", cd.startswith("3:"), cd)
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)
        if await pg.locator(".confirm-sheet .danger, .confirm-sheet button.primary").count():
            await pg.locator(".confirm-sheet button").last.click(); await pg.wait_for_timeout(300)
        rec2 = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-resume-single-v1') || 'null')")
        check("Beenden keeps a cardio note", rec2 and rec2.get("kind") == "cardio" and rec2.get("index") == 1, json.dumps(rec2)[:120] if rec2 else "none")

        # ---- 50 Kurz anhalten on the Atem-Programm transition (page clock) ----
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        await pg2.clock.install()
        await pg2.goto(BASE + "?bereich=breath"); await pg2.wait_for_timeout(300)
        await pg2.click('#breathFeaturedGrid .featured-card'); await pg2.wait_for_timeout(300)
        await pg2.click("#breathProgramStartBtn"); await pg2.wait_for_timeout(300)
        for _ in range(40):
            if await pg2.is_visible("#breathTransition"): break
            await pg2.clock.run_for(15000)
        vis = await pg2.is_visible("#breathTransition")
        check("transition panel shows 'Kurz anhalten'", vis and await pg2.is_visible("#breathTransitionHoldBtn"))
        if vis:
            await pg2.click("#breathTransitionHoldBtn")
            await pg2.clock.run_for(6000)
            check("held: still on the panel after 6 s", await pg2.is_visible("#breathTransition"))
            check("label 'Angehalten'", "angehalten" in (await pg2.inner_text("#breathTransition .next-label")).lower())
            check("hold button gone", not await pg2.is_visible("#breathTransitionHoldBtn"))
            await pg2.click("#breathTransitionBtn"); await pg2.wait_for_timeout(300)
            check("Weiter continues", await pg2.is_visible("#breathPlayer") and not await pg2.is_visible("#breathTransition"))
        await pg2.close()

        # ---- 51 Eigenes Training says the points ----
        blocks = [{"id": "t1", "kind": "list", "title": "Dehnen kurz", "note": "", "items": [{"text": "Wade", "s": 16}, {"text": "Hüfte", "s": 16}]}]
        await pg.evaluate("(bl) => localStorage.setItem('fwmc-free-blocks-v1', JSON.stringify(bl))", blocks)
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { window.__cueLog = []; }")
        started = await pg.evaluate("() => { const c = [...document.querySelectorAll('#freeHome [data-free-id], #freeHome .bundle-item, #freeHome .excard')].find(e => e.textContent.includes('Dehnen kurz')); if (c) c.click(); return !!c; }")
        await pg.wait_for_timeout(300)
        await pg.evaluate("() => { const s = [...document.querySelectorAll('.screen:not([hidden]) .start-btn')].find(b => b.offsetParent); if (s) s.click(); }")
        await pg.wait_for_timeout(11500)
        log = await pg.evaluate("() => window.__cueLog || []")
        check("says the first point and 'Als Nächstes' before the end", started and "Wade" in log and "Als Nächstes: Hüfte" in log, str(log))
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
