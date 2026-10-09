"""Schulte-Tabelle (NAT, 2026-10-09): Raster 3x3-6x6, Modi Fest / Wechselnd /
Aus der Erinnerung, Fixpunkt (shared module, key "schulte:<mode>", standard
on; odd grid = free middle cell, even grid = point on the crossing), wrong
tap = red + counted, best time per mode/grid in fwmc-schulte-best-v1 (kept
across reload), pause covers the numbers + live Fixpunkt, Kombi block that
repeats tables until its time is up, screenshots 390/1024 light/dark, no
page or console errors."""
import asyncio
import json
import os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "schulte")
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:300]}]" if not ok and extra != "" else ""))


async def new_page(b, extra="", scheme="light", width=390, height=844):
    ctx = await b.new_context(viewport={"width": width, "height": height}, locale="de-DE", service_workers="block", color_scheme=scheme)
    await ctx.add_init_script("try{if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
                              "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');" + extra + "}}catch(e){}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    return ctx, pg


async def open_ready(pg, card, grid=None, nav=True):
    if nav:
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(350)
    await pg.evaluate(f"document.getElementById('{card}').click()"); await pg.wait_for_timeout(250)
    if grid:
        await pg.click(f'#schulteGridRow [data-schulte-grid="{grid}"]'); await pg.wait_for_timeout(80)


async def cells(pg):
    """[(text, classes)] of every cell, in grid order."""
    return await pg.evaluate("[...document.querySelectorAll('#schulteGrid .schulte-cell')].map((c) => [c.textContent, c.className])")


async def tap(pg, i):
    await pg.evaluate(f"document.querySelectorAll('#schulteGrid .schulte-cell')[{i}].click()")


async def tap_number(pg, n, memo=None):
    cs = await cells(pg)
    if memo is not None:
        i = memo[n]
    else:
        i = next(k for k, (t, _) in enumerate(cs) if t == str(n))
    await tap(pg, i)


async def play_table(pg, total, memo_first=False):
    memo = None
    if memo_first:
        cs = await cells(pg)
        memo = {int(t): k for k, (t, _) in enumerate(cs) if t}
    for n in range(1, total + 1):
        await tap_number(pg, n, memo)


async def fix_store(pg):
    v = await pg.evaluate("localStorage.getItem('fwmc-fix-v1')")
    return json.loads(v) if v else {}


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ================= home: tile, sub tab, cards =================
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(350)
        check("NAT home: Schulte sub tab and tile exist", await pg.locator('[data-nat-sub="schulte"]').count() == 1
              and await pg.locator('.nat-tile[data-nat-ex="schulte"]').count() == 1)
        await pg.evaluate("document.querySelector('[data-nat-sub=\"schulte\"]').click()"); await pg.wait_for_timeout(150)
        check("sub tab shows the three mode cards", await pg.is_visible("#schulteOpenFest") and await pg.is_visible("#schulteOpenWechselnd") and await pg.is_visible("#schulteOpenErinnerung"))

        # ================= ready screen =================
        await open_ready(pg, "schulteOpenFest", nav=False)
        check("ready: title and 'Training starten'", await pg.inner_text("#schulteReadyTitle") == "Schulte-Tabelle"
              and (await pg.inner_text("#schulteReadyStartBtn")).strip() == "Training starten")
        check("ready: default grid 5x5", await pg.evaluate("document.querySelector('#schulteGridRow .choice.active').dataset.schulteGrid") == "5")
        check("ready: Fixpunkt on by default", await pg.evaluate("document.querySelector('#schulteFixToggleRow .choice.active').dataset.fixOn") == "1")
        check("ready: count help names the free middle cell", "24" in await pg.inner_text("#schulteGridCount"), await pg.inner_text("#schulteGridCount"))
        await pg.click('#schulteGridRow [data-schulte-grid="4"]'); await pg.wait_for_timeout(80)
        check("ready: 4x4 = 16 numbers", "16" in await pg.inner_text("#schulteGridCount"), await pg.inner_text("#schulteGridCount"))
        await pg.evaluate("document.getElementById('schulteAdvanced').open = true"); await pg.wait_for_timeout(80)
        check("ready: Größe/Farbe der Zahlen + Hintergrund in Feineinstellungen",
              "Größe der Zahlen" in await pg.inner_text("#schulteAdvanced") and "Farbe der Zahlen" in await pg.inner_text("#schulteAdvanced")
              and await pg.is_visible("#schulteBgColorPicker"))
        check("ready: ⓘ Regeln button", await pg.locator("#schulteReady .regeln-btn, #schulteReady [data-regeln]").count() >= 1)

        # ================= Fest 3x3 with Fixpunkt: middle free, wrong tap =================
        await pg.click('#schulteGridRow [data-schulte-grid="3"]'); await pg.wait_for_timeout(80)
        await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(500)
        cs = await cells(pg)
        check("fest 3x3 + Fixpunkt: 9 cells, middle free, 8 numbers", len(cs) == 9 and "free" in cs[4][1] and cs[4][0] == ""
              and sorted(int(t) for t, _ in cs if t) == list(range(1, 9)), cs)
        check("fest: fixation point visible", await pg.is_visible("#schulteFixpointEl"))
        fp = await pg.evaluate("(() => { const a = document.getElementById('schulteFixpointEl').getBoundingClientRect(), c = document.querySelectorAll('#schulteGrid .schulte-cell')[4].getBoundingClientRect(); return [a.left + a.width / 2, a.top + a.height / 2, c.left, c.right, c.top, c.bottom]; })()")
        check("fest: point sits inside the free middle cell", fp[2] <= fp[0] <= fp[3] and fp[4] <= fp[1] <= fp[5], fp)
        status = await pg.inner_text("#schulteLevelEl")
        check("fest: status shows 0/8", status.startswith("0/8"), status)
        await pg.screenshot(path=os.path.join(SHOTS, "fest_3x3_390_light.png"))
        # wrong tap: tap the 5 first
        i5 = next(k for k, (t, _) in enumerate(cs) if t == "5")
        await tap(pg, i5); await pg.wait_for_timeout(60)
        check("wrong tap: cell turns red", "wrong" in (await cells(pg))[i5][1])
        await pg.wait_for_timeout(500)
        check("wrong tap: red goes away again", "wrong" not in (await cells(pg))[i5][1])
        await play_table(pg, 8)
        await pg.wait_for_timeout(1100)
        check("fest: done panel with check mark", await pg.is_visible("#schulteDonePanel") and await pg.is_visible("#schulteDonePanel .done-check"))
        summ = await pg.evaluate("document.getElementById('schulteDoneSummary').textContent")
        check("fest: summary names mode, grid, 1 Fehler, Neue Bestzeit", "Fest" in summ and "3×3" in summ and "1 Fehler" in summ and "Neue Bestzeit" in summ, summ)
        best = json.loads(await pg.evaluate("localStorage.getItem('fwmc-schulte-best-v1')") or "{}")
        check("best stored under fest:3f (free middle)", list(best) == ["fest:3f"] and best["fest:3f"] > 0, best)
        hist = json.loads(await pg.evaluate("localStorage.getItem('fwmc-history-v1') || '[]'") or "[]")
        h = [e for e in hist if e.get("kind") == "schulte"]
        check("history entry kind schulte", len(h) == 1 and "Schulte-Tabelle" in h[0].get("title", ""), hist[-1:] if hist else hist)
        await pg.screenshot(path=os.path.join(SHOTS, "fest_done_390_light.png"))

        # ================= best survives a reload =================
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(350)
        best2 = json.loads(await pg.evaluate("localStorage.getItem('fwmc-schulte-best-v1')") or "{}")
        meta = await pg.evaluate("document.getElementById('schulteBestFest').textContent")
        check("reload: best still stored and on the Fest card", best2 == best and meta.strip() != "", (best2, meta))
        await open_ready(pg, "schulteOpenFest", nav=False)
        check("reload: ready screen names the best time for 3x3", (await pg.inner_text("#schulteReadyBestHint")).strip() != "", await pg.inner_text("#schulteReadyBestHint"))

        # ================= Wechselnd 4x4: point on the crossing, numbers swap =================
        await open_ready(pg, "schulteOpenWechselnd", grid=4)
        await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(500)
        cs = await cells(pg)
        check("wechselnd 4x4: 16 numbers, no free cell", len(cs) == 16 and not any("free" in c for _, c in cs)
              and sorted(int(t) for t, _ in cs) == list(range(1, 17)), cs)
        fp = await pg.evaluate("(() => { const a = document.getElementById('schulteFixpointEl').getBoundingClientRect(), g = document.getElementById('schulteGrid').getBoundingClientRect(); return [a.left + a.width / 2 - (g.left + g.width / 2), a.top + a.height / 2 - (g.top + g.height / 2), a.width, g.width]; })()")
        check("wechselnd 4x4: point on the crossing (grid centre), small", abs(fp[0]) < 2 and abs(fp[1]) < 2 and fp[2] < fp[3] / 4, fp)
        before = [t for t, _ in cs]
        changed = False
        for n in (1, 2, 3):
            await tap_number(pg, n); await pg.wait_for_timeout(30)
            now = [t for t, _ in await cells(pg)]
            open_before = [t for t, k in zip(before, now) if t and int(t) > n]
            if any(a != b2 for a, b2 in zip(before, now) if a and int(a) > n): changed = True
            before = now
        check("wechselnd: remaining numbers change places", changed)
        cs = await cells(pg)
        check("wechselnd: tapped numbers stay done", sum("done" in c for _, c in cs) == 3)
        await pg.screenshot(path=os.path.join(SHOTS, "wechselnd_4x4_390_light.png"))
        for n in range(4, 17):
            await tap_number(pg, n)
        await pg.wait_for_timeout(1100)
        summ = await pg.inner_text("#schulteDoneSummary")
        check("wechselnd: done, fehlerfrei", await pg.is_visible("#schulteDonePanel") and "Wechselnd" in summ and "fehlerfrei" in summ, summ)
        best = json.loads(await pg.evaluate("localStorage.getItem('fwmc-schulte-best-v1')") or "{}")
        check("wechselnd best key 'wechselnd:4' (even grid, no f)", "wechselnd:4" in best, best)

        # ================= Erinnerung 3x3 without Fixpunkt =================
        await open_ready(pg, "schulteOpenErinnerung", grid=3)
        await pg.click('#schulteFixToggleRow [data-fix-on="0"]'); await pg.wait_for_timeout(80)
        st = await fix_store(pg)
        check("Fixpunkt off stored for schulte:erinnerung only", st.get("schulte:erinnerung", {}).get("on") is False and "schulte:fest" not in st, st)
        check("count help: 9 numbers without point", "9" in await pg.inner_text("#schulteGridCount"))
        await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(500)
        cs = await cells(pg)
        check("erinnerung 3x3 ohne Fixpunkt: 9 numbers, middle used", len(cs) == 9 and all(t for t, _ in cs) and not await pg.is_visible("#schulteFixpointEl"), cs)
        memo = {int(t): k for k, (t, _) in enumerate(cs)}
        await tap(pg, memo[1]); await pg.wait_for_timeout(60)
        cs = await cells(pg)
        shown = [t for t, _ in cs if t]
        check("erinnerung: after the 1 only the 1 stays visible", shown == ["1"] and sum("covered" in c for _, c in cs) == 8, cs)
        await pg.screenshot(path=os.path.join(SHOTS, "erinnerung_390_light.png"))
        k7 = memo[7]
        await tap(pg, k7); await pg.wait_for_timeout(40)
        check("erinnerung: wrong covered tap counts red", "wrong" in (await cells(pg))[k7][1])
        for n in range(2, 10):
            await tap(pg, memo[n])
        await pg.wait_for_timeout(1100)
        summ = await pg.inner_text("#schulteDoneSummary")
        check("erinnerung: done, 1 Fehler", await pg.is_visible("#schulteDonePanel") and "Aus der Erinnerung" in summ and "1 Fehler" in summ, summ)
        best = json.loads(await pg.evaluate("localStorage.getItem('fwmc-schulte-best-v1')") or "{}")
        check("erinnerung best key 'erinnerung:3' (no point = no f)", "erinnerung:3" in best, best)

        # ================= pause: numbers covered, live Fixpunkt =================
        await open_ready(pg, "schulteOpenFest", grid=5)
        await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(500)
        check("fest 5x5 + Fixpunkt: 24 numbers", len([t for t, _ in await cells(pg) if t]) == 24)
        await tap_number(pg, 1); await pg.wait_for_timeout(50)
        await pg.click("#schultePauseBtn"); await pg.wait_for_timeout(200)
        col = await pg.evaluate("getComputedStyle(document.querySelectorAll('#schulteGrid .schulte-cell.tappable')[0]).color")
        check("pause: numbers covered (transparent)", await pg.is_visible("#schultePauseOverlay") and col in ("rgba(0, 0, 0, 0)", "transparent"), col)
        s1 = await pg.inner_text("#schulteLevelEl"); await pg.wait_for_timeout(600)
        check("pause: clock stands still", s1 == await pg.inner_text("#schulteLevelEl"), s1)
        check("pause: Fixpunkt group with kind row", await pg.is_visible("#schultePauseFixToggleRow") and await pg.is_visible("#schultePauseFixKindRow"))
        await pg.screenshot(path=os.path.join(SHOTS, "pause_390_light.png"))
        await pg.click('#schultePauseFixToggleRow [data-fix-on="0"]'); await pg.wait_for_timeout(150)
        cs = await cells(pg)
        check("pause: Fixpunkt off on 5x5 = new table with 25 numbers", len([t for t, _ in cs if t]) == 25 and not any("free" in c for _, c in cs)
              and not any("done" in c for _, c in cs), cs[:3])
        check("pause: point hidden at once", not await pg.is_visible("#schulteFixpointEl"))
        check("pause: change stored for schulte:fest", (await fix_store(pg)).get("schulte:fest", {}).get("on") is False, await fix_store(pg))
        await pg.click('#schultePauseFixToggleRow [data-fix-on="1"]'); await pg.wait_for_timeout(150)
        await pg.click('#schultePauseFixKindRow [data-fix-kind="kreuz"]'); await pg.wait_for_timeout(100)
        check("pause: back on = free middle + point again", "free" in (await cells(pg))[12][1] and await pg.is_visible("#schulteFixpointEl"))
        await pg.click("#schulteResumeBtn"); await pg.wait_for_timeout(200)
        col = await pg.evaluate("getComputedStyle(document.querySelectorAll('#schulteGrid .schulte-cell.tappable')[0]).color")
        check("resume: numbers visible again", col not in ("rgba(0, 0, 0, 0)", "transparent"), col)
        await pg.click("#schulteBackBtn"); await pg.wait_for_timeout(300)
        check("Beenden without a finished table: back on the ready screen, no history entry",
              await pg.is_visible("#schulteReady") and len([e for e in json.loads(await pg.evaluate("localStorage.getItem('fwmc-history-v1') || '[]'")) if e.get("kind") == "schulte"]) == 3)
        await ctx.close()

        # ================= Kombi: capture, edit, playback, repeat =================
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false,\"defaultPauseS\":0}');")
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(350)
        await pg.evaluate("document.querySelector('[data-open-combo=\"1\"]').click()"); await pg.wait_for_timeout(200)
        await pg.click('#comboAddGrid >> text="Schulte-Tabelle · Fest"'); await pg.wait_for_timeout(300)
        check("Kombi capture: ready screen with Baustein duration + 'Baustein übernehmen'", await pg.is_visible("#schulteComboDurationGroup")
              and "Baustein übernehmen" in await pg.inner_text("#schulteReadyStartBtn"))
        await pg.click('#schulteGridRow [data-schulte-grid="3"]')
        await pg.fill("#schulteComboDurationSlider", "15")
        await pg.dispatch_event("#schulteComboDurationSlider", "input")
        await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(300)
        lst = await pg.inner_text("#comboBlockList")
        check("Kombi: block listed with mode, 3x3", "Schulte-Tabelle · Fest" in lst and "3×3" in lst, lst)
        own = json.loads(await pg.evaluate("localStorage.getItem('fwmc-schulte-prefs-v1') || '{}'") or "{}")
        check("Kombi capture leaves the client's own grid alone", own.get("gridSize", 5) == 5, own)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        check("Kombi: Schulte block plays", await pg.is_visible("#schultePlayer") and len(await cells(pg)) == 9)
        await play_table(pg, 8)
        await pg.wait_for_timeout(400)
        check("Kombi: between tables the hint says the next one comes", "nächste Tabelle" in await pg.inner_text("#schulteHint"), await pg.inner_text("#schulteHint"))
        await pg.wait_for_timeout(1500)
        cs = await cells(pg)
        check("Kombi: a fresh table follows", not any("done" in c for _, c in cs) and len(cs) == 9, cs)
        await pg.wait_for_function("() => !document.getElementById('comboDonePanel').hidden || !document.getElementById('comboTransition').hidden", timeout=20000)
        txt = await pg.evaluate("document.getElementById('comboDonePanel').textContent + document.getElementById('comboTransition').textContent")
        check("Kombi: block result '1 Tabelle · beste …'", "1 Tabelle" in txt and "beste" in txt, txt[:300])
        await pg.screenshot(path=os.path.join(SHOTS, "kombi_done_390_light.png"))
        await ctx.close()

        # ================= Cardio-Zusatzaufgabe: picker, runs, returns =================
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        choice = pg.locator('#cardioAddonPickerTypeRow .choice:has-text("Schulte-Tabelle")')
        check("Cardio picker offers Schulte-Tabelle", await choice.count() == 1)
        await choice.click(); await pg.wait_for_timeout(100)
        check("Cardio picker: 3 modes", await pg.locator("#cardioAddonPicker [data-mode]").count() >= 3)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(500)
        check("Cardio guest runs in #schultePlayer (4x4 default)", await pg.is_visible("#schultePlayer") and await pg.is_hidden("#cardioPlayer") and len(await cells(pg)) == 16)
        await pg.click("#schulteBackBtn"); await pg.wait_for_timeout(300)
        check("Cardio guest: Beenden returns to the Cardio session", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#schultePlayer"))
        check("Cardio guest: no own prefs or history written", await pg.evaluate("localStorage.getItem('fwmc-schulte-prefs-v1')") is None
              and not [e for e in json.loads(await pg.evaluate("localStorage.getItem('fwmc-history-v1') || '[]'")) if e.get("kind") == "schulte"])
        await ctx.close()

        # ================= screenshots: 390 / 1024, light / dark =================
        for w, h in ((390, 844), (1024, 1366)):
            for scheme in ("light", "dark"):
                ctx, pg = await new_page(b, scheme=scheme, width=w, height=h)
                await open_ready(pg, "schulteOpenWechselnd")
                await pg.evaluate("document.getElementById('schulteAdvanced').open = true")
                await pg.screenshot(path=os.path.join(SHOTS, f"ready_{w}_{scheme}.png"), full_page=True)
                await pg.click("#schulteReadyStartBtn"); await pg.wait_for_timeout(500)
                await pg.screenshot(path=os.path.join(SHOTS, f"player_{w}_{scheme}.png"))
                ov = await pg.evaluate("""(() => {
                  const hint = document.getElementById('schulteHint').getBoundingClientRect();
                  const grid = document.getElementById('schulteGrid').getBoundingClientRect();
                  const bar = document.getElementById('schultePlayerBar').getBoundingClientRect();
                  const cell = document.querySelector('#schulteGrid .schulte-cell').getBoundingClientRect();
                  return { gapHint: grid.top - hint.bottom, gapBar: grid.top - bar.bottom, cell: cell.width, inside: grid.right <= innerWidth && grid.bottom <= innerHeight };
                })()""")
                check(f"{w} {scheme}: grid below hint and bar, cells >= 44 px, on screen",
                      ov["gapHint"] >= 0 and ov["gapBar"] >= 0 and ov["cell"] >= 44 and ov["inside"], ov)
                await pg.click("#schultePauseBtn"); await pg.wait_for_timeout(200)
                await pg.screenshot(path=os.path.join(SHOTS, f"pause_{w}_{scheme}.png"))
                await ctx.close()

        check("no page/console errors", errors == [], errors[:5])
        await b.close()
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)


asyncio.run(main())
