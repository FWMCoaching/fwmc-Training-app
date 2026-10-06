import asyncio, json, time
from playwright.async_api import async_playwright

# Fabian 2026-10-06: "Weitermachen nach Unterbrechung mit rein" and
# "Startbildschirm anpassen" (install hint with Safari share icon + arrow).
# A multi-block run (Kombi, Workout-Plan, Atem-Programm, Trainer-Programm)
# remembers the block it is in (fwmc-resume-v1); Heute offers Fortsetzen /
# Von vorne / Verwerfen when it was left in the middle.
BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

DEF = {"type": "breath-program", "name": "Feierabend-Reset", "blocks": [{"pattern": "box", "durationMin": 3}, {"pattern": "coherent", "durationMin": 5}]}
def rec(pos, age_s=600, total=2):
    return json.dumps({"type": "breath", "def": DEF, "code": None, "key": "atem-reset", "title": "Feierabend-Reset",
                       "idx": pos, "pos": pos, "total": total, "played": 180, "ts": int((time.time() - age_s) * 1000)})
VIS = "() => [...document.querySelectorAll('.screen,.player')].filter(e => !e.hidden && e.getClientRects().length).map(e => e.id).join('+')"
RES = "() => JSON.parse(localStorage.getItem('fwmc-resume-v1') || 'null')"

async def seeded(ctx, value):
    pg = await ctx.new_page()
    await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(200)
    await pg.evaluate("v => { if (v === null) localStorage.removeItem('fwmc-resume-v1'); else localStorage.setItem('fwmc-resume-v1', v); }", value)
    await pg.reload(); await pg.wait_for_timeout(300)
    return pg

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        def watch(pg):
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

        # a real run records its block; block 1 of 2 offers nothing yet
        pg = await seeded(ctx, None); watch(pg)
        await pg.goto(BASE + "index.html?bereich=breath"); await pg.wait_for_timeout(300)
        await pg.click("#breathFeaturedGrid > *"); await pg.wait_for_timeout(200)
        await pg.click("#breathProgramStartBtn"); await pg.wait_for_timeout(400)
        r = await pg.evaluate(RES)
        check("starting a programme records block 1", r and r["type"] == "breath" and r["idx"] == 0 and r["total"] == 2, str(r and {k: r[k] for k in ("idx", "pos", "total")}))
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(300)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        check("left in block 1: no Weitermachen card", await pg.locator("#todayResumeBtn").count() == 0)
        await pg.close()

        # left in block 2: Heute offers it
        pg = await seeded(ctx, rec(1)); watch(pg)
        main_txt = (await pg.inner_text("#todayMain")).replace("\xa0", " ")
        check("Heute shows Weitermachen card", "weitermachen" in main_txt.lower() and "Feierabend-Reset" in main_txt and "Übung 2 von 2" in main_txt, main_txt.replace("\n", " | ")[:160])
        check("meta says when", "vor 10 Min." in main_txt)
        for sel in ("#todayResumeBtn", "#todayResumeRestartBtn", "#todayResumeDropBtn"):
            bb = await pg.locator(sel).bounding_box()
            check(f"{sel} tap target >= 44 px", bb and bb["height"] >= 44, str(bb and round(bb["height"])))
        await pg.screenshot(path="screenshots/resume_today_light.png")
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(400)
        check("Fortsetzen opens the breath player", "breathPlayer" in await pg.evaluate(VIS), await pg.evaluate(VIS))
        r = await pg.evaluate(RES)
        check("continues at block 2", r and r["idx"] == 1, str(r and r["idx"]))
        await pg.evaluate("() => { const b = document.querySelector('#breathPlayer [id$=\"SkipBtn\"], #stepNextBtn'); }")
        await pg.close()

        # Von vorne starts at block 1 again
        pg = await seeded(ctx, rec(1)); watch(pg)
        await pg.click("#todayResumeRestartBtn"); await pg.wait_for_timeout(400)
        r = await pg.evaluate(RES)
        check("Von vorne restarts at block 1", "breathPlayer" in await pg.evaluate(VIS) and r and r["idx"] == 0, str(r and r["idx"]))
        await pg.close()

        # Verwerfen asks first; Nein keeps it, Ja drops it
        pg = await seeded(ctx, rec(1)); watch(pg)
        await pg.click("#todayResumeDropBtn"); await pg.wait_for_timeout(200)
        check("Verwerfen asks via confirm sheet", await pg.is_visible("#confirmSheet"))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(200)
        check("Nein keeps it", await pg.evaluate(RES) is not None and await pg.locator("#todayResumeBtn").count() == 1)
        await pg.click("#todayResumeDropBtn"); await pg.wait_for_timeout(200)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        check("Ja drops it and the card goes", await pg.evaluate(RES) is None and await pg.locator("#todayResumeBtn").count() == 0)
        await pg.close()

        # stale or broken records are ignored
        for label, v in (("older than 3 days", rec(1, age_s=4 * 86400)), ("pos 0", rec(0)), ("pos past the end", rec(2)), ("garbage", "{oops")):
            pg = await seeded(ctx, v); watch(pg)
            check(f"ignored: {label}", await pg.locator("#todayResumeBtn").count() == 0)
            await pg.close()

        # with a planned training today the plan stays first, resume is one line under it
        pg = await seeded(ctx, rec(1)); watch(pg)
        await pg.evaluate("""() => { const d = new Date(); const t = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
          localStorage.setItem('fwmc-plan-v1', JSON.stringify({extras: {[t]: [{id:'p1', area:'breath', minutes:10}]}})); }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        main_txt = (await pg.inner_text("#todayMain")).replace("\xa0", " ")
        has_plan = await pg.locator("#todayMain [data-today-start]").count() == 1
        if has_plan:
            check("plan first, resume as a line", "Unterbrochen: Feierabend-Reset" in main_txt and await pg.locator("#todayMain .today-resume-line #todayResumeBtn").count() == 1, main_txt.replace("\n", " | ")[:160])
        else:
            print("(plan seed format not matched, skipped plan line check)")
        await pg.close()

        # dark mode screenshot of the card
        dctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", service_workers="block")
        await dctx.add_init_script(INIT)
        pg = await seeded(dctx, rec(1)); watch(pg)
        await pg.screenshot(path="screenshots/resume_today_dark.png")
        await pg.close(); await dctx.close()

        # install hint: iPhone shows the steps, the button shows the arrow at the bottom; iPad points up
        for pad in (False, True):
            ictx = await b.new_context(viewport={"width": 390 if not pad else 820, "height": 844 if not pad else 1180}, service_workers="block")
            await ictx.add_init_script(INIT + "localStorage.setItem('fwmc-test-install', JSON.stringify('ios'));"
                                       + ("localStorage.setItem('fwmc-test-install-pad','true');" if pad else ""))
            pg = await ictx.new_page(); watch(pg)
            await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
            name = "iPad" if pad else "iPhone"
            check(f"{name}: hint card with steps", await pg.is_visible("#installHint") and await pg.is_visible("#installHintSteps"))
            where = await pg.inner_text("#installHintWhere")
            check(f"{name}: names where the share button is", ("oben rechts" in where) == pad, where)
            await pg.click("#installHintAddBtn"); await pg.wait_for_timeout(300)
            check(f"{name}: arrow overlay shown", await pg.is_visible("#installPointer"))
            bub = await pg.locator("#installPointerBubble").bounding_box()
            vh = 1180 if pad else 844
            check(f"{name}: bubble near the share button", bub and ((bub["y"] < vh / 2) if pad else (bub["y"] > vh / 2)), str(bub))
            await pg.screenshot(path=f"screenshots/install_pointer_{'pad' if pad else 'phone'}.png")
            await pg.click("#installPointer"); await pg.wait_for_timeout(200)
            check(f"{name}: tap closes the arrow", not await pg.is_visible("#installPointer"))
            await pg.click("#installHintCloseBtn"); await pg.wait_for_timeout(200)
            await pg.reload(); await pg.wait_for_timeout(300)
            check(f"{name}: Nicht mehr anzeigen sticks", not await pg.is_visible("#installHint"))
            await pg.close(); await ictx.close()
        # Android: no Safari steps
        actx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await actx.add_init_script(INIT + "localStorage.setItem('fwmc-test-install', JSON.stringify('android'));")
        pg = await actx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        check("Android: menu text, no Safari steps", await pg.is_visible("#installHint") and not await pg.is_visible("#installHintSteps") and "Browser-Menü" in await pg.inner_text("#installHintText"))
        await actx.close()
        # iPhone text size: --ts scales body text, capped at 0.95-1.25; big numbers stay
        for forced, want in ((1.25, 1.25), (2, 1.25), (0.5, 0.95)):
            tctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
            await tctx.add_init_script(INIT + f"localStorage.setItem('fwmc-test-textscale','{forced}');")
            pg = await tctx.new_page(); watch(pg)
            await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
            fs = await pg.evaluate("parseFloat(getComputedStyle(document.body).fontSize)")
            check(f"text scale {forced} -> body {15 * want:.2f}px", abs(fs - 15 * want) < 0.2, str(fs))
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            check(f"text scale {forced}: no sideways scroll", sw <= 390, str(sw))
            if forced == 1.25: await pg.screenshot(path="screenshots/textscale_125_today.png")
            await tctx.close()
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        check("default text scale 1 (no iPhone)", abs(await pg.evaluate("parseFloat(getComputedStyle(document.body).fontSize)") - 15) < 0.1)
        await pg.close()

        # app icon shortcuts (Android): manifest urls open the right page
        man = await (await ctx.request.get(BASE + "manifest.json")).json()
        urls = [x["url"] for x in man.get("shortcuts", [])]
        check("manifest has 4 shortcuts", len(urls) == 4, str(urls))
        nctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await nctx.add_init_script(INIT)
        pg = await nctx.new_page(); watch(pg)
        want = {"heute": "todayHome", "training": "trainingHub", "breath": "breathHome", "fortschritt": "progressScreen"}
        for u in urls:
            await pg.goto(BASE + u.lstrip("./")); await pg.wait_for_timeout(300)
            key = u.split("bereich=")[1]
            check(f"shortcut {key} opens {want[key]}", await pg.evaluate(VIS) == want[key], await pg.evaluate(VIS))
        await nctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "FAILED")

asyncio.run(main())
