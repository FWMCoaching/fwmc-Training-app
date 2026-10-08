"""Trainer-Menü (Fabian 2026-10-08 abends, docs/notes/36).

Round button in the free ‹ slot of the main pages, only with the
"trainer-tools" unlock (or while a mode runs). Modes: Mein Training,
Mit Kunde (Kunden-Training), Ausprobieren (nothing counts, Test-Ablage 14 Tage).
Ausprobieren during a Kunden-Training pauses it; the gap is not handed over.
Also: each Kunden-Training sends only its own runs, Test runs (and own
runs of the last 14 days, "eigenes") show up unticked with a tag, the
overview "Gespeicherte Trainings" (filter, swipe delete, delete by kind;
own runs are only hidden there, sending removes them from progress), the 3 h limit,
"weiter oder beenden?" after 30 min in the background, thin mode line in a
player, 390/1024 light/dark screenshots, no page errors."""
import asyncio
import json
import os
import time
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "trainer_menu")
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:200]}]" if not ok and extra != "" else ""))


FREE = [{"id": "f1", "kind": "check", "title": "Eisbad", "note": "", "minutes": 5, "items": []},
        {"id": "f2", "kind": "check", "title": "Journal", "note": "", "minutes": 5, "items": []}]


async def new_page(b, scheme="light", w=390, h=844, tools=True, extra=""):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, locale="de-DE",
                              service_workers="block", has_touch=True)
    init = ("try{if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
            "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');"
            f"localStorage.setItem('fwmc-free-blocks-v1', {json.dumps(json.dumps(FREE))});"
            + ("localStorage.setItem('fwmc-test-trainer-tools','true');" if tools else "") + extra + "}}catch(e){}")
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg


async def ls(pg, key, fallback=None):
    v = await pg.evaluate(f"localStorage.getItem({json.dumps(key)})")
    return json.loads(v) if v else fallback


async def menu_btn(pg):
    return pg.locator(".trainer-mode-btn:visible").first


async def set_mode(pg, m):
    if not await pg.is_visible("#trainerMenuSheet"):
        await (await menu_btn(pg)).click(); await pg.wait_for_timeout(150)
    await pg.click(f'#tmModes [data-tm="{m}"]'); await pg.wait_for_timeout(300)


async def do_free(pg, fid, check_slim=False):
    await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(350)
    await pg.click(f'#freeOwnGrid [data-free-id="{fid}"]'); await pg.wait_for_timeout(150)
    await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
    slim = None
    if check_slim:
        slim = await pg.evaluate("(() => { const s = document.getElementById('clientRunStrip'); return !s.hidden && s.classList.contains('slim') && s.getBoundingClientRect().height <= 10 ? getComputedStyle(s).backgroundColor : null; })()")
    await pg.click("#freeTickBtn"); await pg.wait_for_timeout(250)
    await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(200)
    await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(350)
    return slim


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- without unlock: no button ----
        ctx, pg = await new_page(b, tools=False)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        check("no unlock: no trainer button, empty ‹ slot keeps the logo in place",
              await pg.locator(".trainer-mode-btn:visible").count() == 0)
        x0 = await pg.evaluate("document.querySelector('#trainingHub .brand-logo').getBoundingClientRect().left")
        await ctx.close()

        # ---- with unlock ----
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        btn = await menu_btn(pg)
        box = await btn.bounding_box()
        x1 = await pg.evaluate("document.querySelector('#trainingHub .brand-logo').getBoundingClientRect().left")
        check("unlock: round 44 px button top left, logo does not move", box and box["width"] == 44 and box["height"] == 44
              and box["x"] < 70 and abs(x1 - x0) < 1, (box, x0, x1))
        for scr in ("heute", "fortschritt"):
            await pg.goto(ROOT + f"?bereich={scr}"); await pg.wait_for_timeout(300)
            check(f"button also on {scr}", await pg.locator(".trainer-mode-btn:visible").count() == 1)
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(300)
        check("not on an area page (‹ back sits there)", await pg.locator(".trainer-mode-btn:visible").count() == 0)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(300)
        await (await menu_btn(pg)).click(); await pg.wait_for_timeout(200)
        act = await pg.evaluate("[...document.querySelectorAll('#tmModes .tm-mode.active')].map(b => b.dataset.tm)")
        check("menu opens with 3 modes, 'Mein Training' active, trainer buttons inside",
              await pg.is_visible("#trainerMenuSheet") and act == ["own"] and await pg.is_visible("#handoverOpenBtn"), act)
        taps = await pg.evaluate("[...document.querySelectorAll('#tmModes .tm-mode, #tmCloseBtn')].map(b => b.getBoundingClientRect().height)")
        check("menu targets >= 44 px", min(taps) >= 44, taps)
        await pg.screenshot(path=os.path.join(SHOTS, "menu_390_light.png"))
        await pg.click("#tmCloseBtn"); await pg.wait_for_timeout(150)

        # ---- own run, then client, probe pause, back to client ----
        await do_free(pg, "f1")
        check("Mein Training: run in own history", [e["title"] for e in await ls(pg, "fwmc-history-v1", [])] == ["Eisbad"])
        await set_mode(pg, "client")
        word = await (await menu_btn(pg)).inner_text()
        col = await pg.evaluate("getComputedStyle(document.getElementById('clientRunStrip')).backgroundColor")
        check("Mit Kunde: button says 'Kunde', strip orange", word.strip() == "Kunde" and col == "rgb(168, 90, 18)", (word, col))
        await do_free(pg, "f1")
        await set_mode(pg, "try")
        word = await (await menu_btn(pg)).inner_text()
        strip = await pg.inner_text("#clientRunStrip")
        col = await pg.evaluate("getComputedStyle(document.getElementById('clientRunStrip')).backgroundColor")
        check("Ausprobieren in a Kunden-Training: 'Test', violet strip says the client run is paused",
              word.strip() == "Test" and col == "rgb(93, 74, 143)" and "pausiert" in strip, (word, col, strip))
        await pg.screenshot(path=os.path.join(SHOTS, "probe_strip_390_light.png"))
        slim = await do_free(pg, "f2", check_slim=True)
        check("in the player only a thin violet line", slim == "rgb(93, 74, 143)", slim)
        tr = await ls(pg, "fwmc-try-runs-v1", [])
        check("probe run lands in fwmc-try-runs-v1, not in history or client runs",
              [e["title"] for e in tr] == ["Journal"] and tr[0].get("tryRun")
              and len(await ls(pg, "fwmc-history-v1", [])) == 1 and len(await ls(pg, "fwmc-client-runs-v1", [])) == 1)
        await set_mode(pg, "client")
        check("back to Mit Kunde resumes the same session", (await (await menu_btn(pg)).inner_text()).strip() == "Kunde"
              and (await ls(pg, "fwmc-client-session-v1") or {}).get("start"))
        await do_free(pg, "f1")
        await set_mode(pg, "own")
        rows = await pg.evaluate("[...document.querySelectorAll('#handoverList li')].map(li => ({t: li.querySelector('.h-title').textContent, c: li.querySelector('input').checked}))")
        check("Mein Training ends the client run: selection, the 2 client runs ticked, test and own runs listed unticked",
              await pg.is_visible("#handoverScreen") and [r["c"] for r in rows if not r["t"].endswith(("Test", "eigenes"))] == [True, True]
              and [r["c"] for r in rows if r["t"].endswith("Test")] == [False]
              and [r["c"] for r in rows if r["t"].endswith("eigenes")] == [False], rows)
        await pg.screenshot(path=os.path.join(SHOTS, "auswahl_kunde_390_light.png"), full_page=True)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
        meta = await pg.inner_text("#handoverQrMeta") if await pg.is_visible("#handoverQrScreen") else ""
        check("QR with the 2 client runs only (gap left out)", meta.startswith("2 Trainings"), meta)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        check("after Fertig: client store empty, own history untouched, button back to icon",
              await ls(pg, "fwmc-client-runs-v1", []) == [] and len(await ls(pg, "fwmc-history-v1", [])) == 1
              and (await (await menu_btn(pg)).inner_text()).strip() == "")

        # ---- leftovers never mix with the next client ----
        await set_mode(pg, "client")
        await do_free(pg, "f1")
        await set_mode(pg, "own")
        await pg.click("#handoverBackBtn"); await pg.wait_for_timeout(200)
        await set_mode(pg, "client")
        await do_free(pg, "f2")
        await set_mode(pg, "own")
        rows = await pg.evaluate("[...document.querySelectorAll('#handoverList li')].map(li => ({t: li.querySelector('.h-title').textContent, c: li.querySelector('input').checked}))")
        check("second client: only his run ticked, the first client's leftover listed as 'früher' unticked",
              [r["c"] for r in rows if "früher" in r["t"]] == [False] and sum(r["c"] for r in rows) == 1, rows)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
        meta = await pg.inner_text("#handoverQrMeta")
        check("second client gets only his 1 run, not the leftover of the first", meta.startswith("1 Training"), meta)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        left = await ls(pg, "fwmc-client-runs-v1", [])
        check("the first client's leftover still waits", [e["title"] for e in left] == ["Eisbad"], left)
        await (await menu_btn(pg)).click(); await pg.wait_for_timeout(150)
        check("Trainer-Menü shows the leftover", await pg.is_visible("#clientRunPending"))
        await pg.click("#clientRunPendingBtn"); await pg.wait_for_timeout(300)
        await pg.click("#handoverDeleteBtn"); await pg.wait_for_timeout(200)
        check("'Angehakte löschen' asks first", await pg.is_visible("#confirmSheet") and await pg.inner_text("#confirmYesBtn") == "Löschen")
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        check("deleting removes the leftover from the client store, probe run stays",
              await ls(pg, "fwmc-client-runs-v1", []) == [] and len(await ls(pg, "fwmc-try-runs-v1", [])) == 1)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(300)

        # ---- time-window handover: probe runs listed, unticked, tagged ----
        await (await menu_btn(pg)).click(); await pg.wait_for_timeout(150)
        await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(300)
        rows = await pg.evaluate("[...document.querySelectorAll('#handoverList li')].map(li => ({t: li.querySelector('.h-title') && li.querySelector('.h-title').textContent, c: li.querySelector('input') && li.querySelector('input').checked}))")
        probe = [r for r in rows if r["t"] and r["t"].endswith("Test")]
        own = [r for r in rows if r["t"] and not r["t"].endswith("Test")]
        check("handover window lists the test run unticked with 'Test' tag, own runs ticked",
              len(probe) == 1 and not probe[0]["c"] and own and all(r["c"] for r in own), rows)
        await pg.screenshot(path=os.path.join(SHOTS, "zeitraum_probe_390_light.png"), full_page=True)
        await pg.locator("#handoverList li", has=pg.locator(".tm-tag-try")).locator("input").check()
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        check("a ticked probe run is handed over and leaves the probe store", await ls(pg, "fwmc-try-runs-v1", []) == [])
        await ctx.close()

        # ---- overview "Gespeicherte Trainings" ----
        now = int(time.time() * 1000)
        iso = lambda ms: time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ms / 1000))
        hist = [{"id": "o1", "ts": iso(now - 3600e3), "title": "Eisbad", "kind": "free", "seconds": 60},
                {"id": "o2", "ts": iso(now - 2 * 86400e3), "title": "Journal", "kind": "free", "seconds": 60},
                {"id": "o3", "ts": iso(now - 20 * 86400e3), "title": "Alt", "kind": "free", "seconds": 60}]
        tries = [{"id": "t1", "ts": iso(now - 3 * 86400e3), "title": "Test-Lauf", "kind": "free", "tryRun": True},
                 {"id": "t2", "ts": iso(now - 13 * 86400e3), "title": "Test-Lauf 2", "kind": "free", "tryRun": True}]
        cl = [{"id": "c1", "ts": iso(now - 5 * 86400e3), "title": "Kunde A", "kind": "free", "client": now - 5 * 86400e3}]
        seed = (f"localStorage.setItem('fwmc-history-v1', {json.dumps(json.dumps(hist))});"
                f"localStorage.setItem('fwmc-try-runs-v1', {json.dumps(json.dumps(tries))});"
                f"localStorage.setItem('fwmc-client-runs-v1', {json.dumps(json.dumps(cl))});")
        ctx, pg = await new_page(b, extra=seed)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        prog0 = await ls(pg, "fwmc-progress-v1")
        await (await menu_btn(pg)).click(); await pg.wait_for_timeout(150)
        check("Trainer-Menü has 'Gespeicherte Trainings'", await pg.is_visible("#tmStoreBtn"))
        await pg.click("#tmStoreBtn"); await pg.wait_for_timeout(350)
        rows = await pg.evaluate("[...document.querySelectorAll('#handoverList li')].map(li => ({t: li.querySelector('.h-title').textContent, c: li.querySelector('input').checked}))")
        check("overview: all kinds of the last 14 days (test kept 13 days), nothing ticked, 20-day-old own run left out",
              await pg.inner_text("#handoverPickTitle") == "Gespeicherte Trainings" and len(rows) == 5
              and not any(r["c"] for r in rows) and not any(r["t"].startswith("Alt") for r in rows)
              and await pg.is_visible("#handoverKindRow") and not await pg.is_visible("#handoverRangeGroup"), rows)
        await pg.screenshot(path=os.path.join(SHOTS, "uebersicht_390_light.png"), full_page=True)
        await pg.click('#handoverKindRow [data-ho-kind="try"]'); await pg.wait_for_timeout(200)
        n = await pg.locator("#handoverList li").count()
        check("filter 'Test' shows the 2 test runs, button 'Alle Test-Trainings löschen'",
              n == 2 and await pg.inner_text("#handoverClearBtn") == "Alle Test-Trainings löschen", n)
        await pg.click("#handoverClearBtn"); await pg.wait_for_timeout(200)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        check("delete by kind empties the test store", await ls(pg, "fwmc-try-runs-v1", []) == [])
        await pg.click('#handoverKindRow [data-ho-kind="all"]'); await pg.wait_for_timeout(200)
        cdp = await ctx.new_cdp_session(pg)
        sel = "#handoverList li"
        idx = await pg.evaluate("[...document.querySelectorAll('#handoverList li')].findIndex(li => li.textContent.includes('Kunde A'))")
        await pg.evaluate(f"document.querySelectorAll('{sel}')[{idx}].scrollIntoView({{block: 'center'}})"); await pg.wait_for_timeout(80)
        r = await pg.evaluate(f"(() => {{ const r = document.querySelectorAll('{sel}')[{idx}].getBoundingClientRect(); return {{x: r.left, y: r.top, w: r.width, h: r.height}}; }})()")
        y = r["y"] + r["h"] / 2; x0 = min(r["x"] + r["w"] - 20, 370)
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
        for i in range(1, 11):
            await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 - 20 * i, "y": y}]})
            await asyncio.sleep(0.016)
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); await pg.wait_for_timeout(400)
        acts = await pg.evaluate("[...document.querySelectorAll('.swipe-actions button')].map(b => b.textContent)")
        check("swipe left on a row shows 'Löschen'", acts == ["Löschen"], acts)
        if acts:
            await pg.click(".swipe-actions button"); await pg.wait_for_timeout(200)
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        check("swipe delete removes the client run", await ls(pg, "fwmc-client-runs-v1", []) == [])
        await pg.click('#handoverKindRow [data-ho-kind="own"]'); await pg.wait_for_timeout(200)
        await pg.click("#handoverClearBtn"); await pg.wait_for_timeout(200)
        txt = await pg.inner_text("#confirmText")
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        check("deleting own runs only hides them: history and progress stay",
              "bleiben" in txt and len(await ls(pg, "fwmc-history-v1", [])) == 3 and await ls(pg, "fwmc-progress-v1") == prog0
              and await pg.locator("#handoverList li input").count() == 0, txt)
        await ctx.close()

        # ---- probe alone, bests restored ----
        ctx, pg = await new_page(b, extra="localStorage.setItem('fwmc-remember-best-v1','{\"leicht\":4}');")
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(300)
        await set_mode(pg, "try")
        await pg.evaluate("localStorage.setItem('fwmc-remember-best-v1', JSON.stringify({leicht: 9}))")
        await pg.click("#clientRunEndBtn"); await pg.wait_for_timeout(300)
        check("strip 'Beenden' ends Ausprobieren, own best restored",
              await ls(pg, "fwmc-trainer-mode-v1") is None and await ls(pg, "fwmc-remember-best-v1") == {"leicht": 4}
              and not await pg.is_visible("#clientRunStrip"))
        await ctx.close()

        # ---- 30 min in the background asks, 3 h ends ----
        now = int(time.time() * 1000)
        ctx, pg = await new_page(b, extra=f"localStorage.setItem('fwmc-trainer-mode-v1', JSON.stringify({{mode:'try', since:{now - 3600000}, snap:{{}}}}));"
                                          f"localStorage.setItem('fwmc-trainer-seen-v1', '{now - 40 * 60000}');")
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(500)
        check("after 30+ min away: 'Ausprobieren fortsetzen?' Weiter / Beenden", await pg.is_visible("#confirmSheet")
              and "fortsetzen" in await pg.inner_text("#confirmTitle") and await pg.inner_text("#confirmNoBtn") == "Beenden")
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(300)
        check("Beenden ends the mode", await ls(pg, "fwmc-trainer-mode-v1") is None)
        await ctx.close()
        ctx, pg = await new_page(b, extra=f"localStorage.setItem('fwmc-client-session-v1', JSON.stringify({{start:{now - 4 * 3600000}, snap:{{}}}}));")
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(500)
        check("Kunden-Training older than 3 h ends by itself", await ls(pg, "fwmc-client-session-v1") is None
              and not await pg.is_visible("#clientRunStrip"))
        await ctx.close()

        # ---- looks: 390/1024 light/dark ----
        for w, h in ((390, 844), (1024, 1366)):
            for scheme in ("light", "dark"):
                ctx, pg = await new_page(b, scheme, w, h)
                await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(350)
                await pg.screenshot(path=os.path.join(SHOTS, f"bar_{w}_{scheme}.png"))
                await set_mode(pg, "client")
                await pg.screenshot(path=os.path.join(SHOTS, f"kunde_{w}_{scheme}.png"))
                await (await menu_btn(pg)).click(); await pg.wait_for_timeout(200)
                await pg.screenshot(path=os.path.join(SHOTS, f"menu_{w}_{scheme}.png"))
                wide = await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                check(f"[{w} {scheme}] no sideways scroll with the menu open", wide)
                await ctx.close()

        await b.close()
    check("no page errors", not errors, errors[:5])
    bad = [n for n, ok in results if not ok]
    print(f"{len(results) - len(bad)}/{len(results)} passed")
    if bad:
        print("FAILED:", bad)


asyncio.run(main())
