import asyncio, json
from playwright.async_api import async_playwright

# Freie Bausteine (2026-10-05): the client's own activities outside the app
# (Dehnen, Eisbad, Journal ...) as "Abhaken", "Mit Zeit" or "Checkliste".
# Covers: Training hub tile, creating each kind, persistence after reload,
# the Dehnen template (countdown, « », Kopieren und anpassen), a timed run
# with Pause, a checklist with tick + countdown auto-advance, history,
# skipping past the end = aborted, delete via confirmDialog, Kombi capture
# (own copy) + edit + playback, plan entry pointing at one Baustein that
# auto-ticks, and no page/console errors.
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


async def visible_screen(pg):
    return await pg.evaluate("""() => { const s = [...document.querySelectorAll('.screen')].find((el) => !el.hidden);
      return s ? s.id : null; }""")


async def history(pg):
    return await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")


async def own_blocks(pg):
    return await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-free-blocks-v1') || '[]')")


async def new_block(pg, kind, title, note=""):
    await pg.click("#freeNewBtn"); await pg.wait_for_timeout(120)
    await pg.click(f'#freeKindRow [data-free-kind="{kind}"]'); await pg.wait_for_timeout(60)
    await pg.fill("#freeTitleInput", title)
    if note: await pg.fill("#freeNoteInput", note)


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script("""localStorage.setItem('fwmc-tips-seen','true');
          localStorage.setItem('fwmc-test-bottomnav','true');
          localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));""")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- reachable from the Training hub ----
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        await pg.click('#bottomNav [data-nav="training"]'); await pg.wait_for_timeout(200)
        tile = pg.locator('#hubAreaGrid .area-tile[data-area="free"]')
        check("Training hub has a 'Freie Bausteine' tile", await tile.count() == 1 and "Freie Bausteine" in await tile.inner_text())
        await tile.click(); await pg.wait_for_timeout(200)
        check("tile opens the area home", await visible_screen(pg) == "freeHome")
        frame = await pg.evaluate("""() => { const h = document.getElementById('freeHome');
          return [!!h.querySelector('.combo-entry-link'), !!h.querySelector('.code-card'), !!h.querySelector('#freeHistorySection'),
                  !!h.querySelector(':scope > .brandbar .bar-back-btn')]; }""")
        check("same frame as the other area homes (Kombi link, code card, Verlauf, ‹ back)", all(frame), frame)
        check("Dehnen template listed, no own Bausteine yet",
              await pg.locator('#freeTplGrid [data-free-id="tpl-dehnen"]').count() == 1 and await pg.is_visible("#freeOwnEmpty"))

        # ---- create one of each kind ----
        await new_block(pg, "check", "Eisbad", "Langsam rein, ruhig atmen.")
        check("editor: duration and checklist hidden for 'Abhaken'",
              not await pg.is_visible("#freeMinutesGroup") and not await pg.is_visible("#freeItemsGroup"))
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        check("saving opens the ready screen", await visible_screen(pg) == "freeReady" and await pg.inner_text("#freeReadyTitle") == "Eisbad")
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)

        await new_block(pg, "timer", "Mobilisation")
        check("editor: duration slider for 'Mit Zeit' (1-60 min)", await pg.is_visible("#freeMinutesSlider") and
              await pg.evaluate("[freeMinutesSlider.min, freeMinutesSlider.max, freeMinutesSlider.step].join()") == "1,60,1")
        await pg.evaluate("() => { const s = document.getElementById('freeMinutesSlider'); s.value = '12'; s.dispatchEvent(new Event('input')); }")
        check("slider shows the minutes", await pg.inner_text("#freeMinutesValue") == "12 Min.")
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)

        await new_block(pg, "list", "Journal")
        check("Checkliste starts with one empty point, save disabled until it has text",
              await pg.locator("#freeItemList .free-item-row").count() == 1 and await pg.is_disabled("#freeSaveBtn"))
        await pg.fill("#freeItemList .free-item-text >> nth=0", "Drei gute Dinge")
        for _ in range(6):  # 30 s -> 0 = ohne Zeit
            await pg.click('#freeItemList .free-item-row >> nth=0 >> [data-step="-1"]')
        await pg.click("#freeItemAddBtn"); await pg.wait_for_timeout(60)
        await pg.fill("#freeItemList .free-item-text >> nth=1", "Ziel für morgen")
        for _ in range(4):  # 0 -> 10 s (the new point copies the last time: 0)
            await pg.click('#freeItemList .free-item-row >> nth=1 >> [data-step="-1"]')
        await pg.click('#freeItemList .free-item-row >> nth=1 >> [data-step="1"]')
        await pg.click("#freeItemAddBtn"); await pg.wait_for_timeout(60)
        await pg.fill("#freeItemList .free-item-text >> nth=2", "Wegwerfen")
        await pg.click('#freeItemList .free-item-row >> nth=2 >> [data-move="-1"]')
        order = await pg.eval_on_selector_all("#freeItemList .free-item-text", "els => els.map(e => e.value)")
        check("↑ moves a point up", order == ["Drei gute Dinge", "Wegwerfen", "Ziel für morgen"], order)
        await pg.click('#freeItemList .free-item-row >> nth=1 >> [data-remove]')
        times = await pg.eval_on_selector_all("#freeItemList .free-item-time", "els => els.map(e => e.textContent)")
        check("✕ removes, times 'ohne Zeit' and 10 s", times == ["ohne Zeit", "10 s"], times)
        small = await pg.evaluate("() => [...document.querySelectorAll('#freeEdit button')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).map(b => b.textContent.trim())")
        check("editor tap targets at least 44 px", not small, small[:4])
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)

        await pg.reload(); await pg.wait_for_timeout(400)
        blocks = await own_blocks(pg)
        check("three Bausteine saved under fwmc-free-blocks-v1",
              [(x["kind"], x["title"]) for x in blocks] == [("check", "Eisbad"), ("timer", "Mobilisation"), ("list", "Journal")], blocks)
        check("Mit Zeit keeps 12 min, checklist keeps its points", blocks[1]["minutes"] == 12 and
              [(i["text"], i["s"]) for i in blocks[2]["items"]] == [("Drei gute Dinge", 0), ("Ziel für morgen", 10)])
        ids = {x["title"]: x["id"] for x in blocks}
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(300)
        check("?bereich=free opens the area, cards persist after reload",
              await visible_screen(pg) == "freeHome" and await pg.locator("#freeOwnGrid [data-free-id]").count() == 3)

        # ---- plan entry pointing at one Baustein, auto-tick ----
        opts = await pg.evaluate("""() => { const a = document.getElementById('planEntryArea'); a.value = 'free';
          a.dispatchEvent(new Event('change')); return [...document.getElementById('planEntryWhat').options].map(o => o.textContent); }""")
        check("Wochenplan: 'Freie Bausteine' area offers each Baustein", "Eisbad" in opts and "Dehnen" in opts, opts)
        await pg.evaluate("""(id) => { const d = new Date(); const ds = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
          localStorage.setItem('fwmc-plan-v1', JSON.stringify({startDate: ds, phases: [], extras: {[ds]: [{id: 'pe1', area: 'free', what: 'free:' + id, code: '', time: '', minutes: 10}]}, skips: {}, done: {}})); }""", ids["Eisbad"])
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        main_txt = await pg.inner_text("#todayMain")
        check("Heute shows the planned Baustein by its title", "HEUTIGES TRAINING" in main_txt.upper() and "Eisbad" in main_txt, main_txt[:80])
        await pg.click("#todayMain [data-today-start]"); await pg.wait_for_timeout(200)
        check("starting it opens that Baustein", await visible_screen(pg) == "freeReady" and await pg.inner_text("#freeReadyTitle") == "Eisbad")

        # ---- Abhaken run ----
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(200)
        check("player: title, note, Erledigt button, Beenden/Pause conventions",
              await pg.is_visible("#freePlayer") and await pg.inner_text("#freeRunTitle") == "Eisbad" and await pg.is_visible("#freeTickBtn")
              and "Beenden" in await pg.inner_text("#freeBackBtn") and await pg.inner_text("#freePauseBtn") == "Pause"
              and await pg.evaluate("document.getElementById('freePlayer').classList.contains('player')"))
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(200)
        h = (await history(pg))[0]
        check("Erledigt -> done panel + history entry", await pg.is_visible("#freeDonePanel") and h["kind"] == "free"
              and h["title"] == "Eisbad" and not h.get("aborted") and h.get("freeId") == ids["Eisbad"], h)
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        done = await pg.evaluate("() => { const el = [...document.querySelectorAll('[data-occ=\"pe1\"]')].find(e => e.offsetParent); return el ? el.className + ' ' + el.textContent : ''; }")
        check("planned entry auto-ticked from the history", "done" in done, done[:90])

        # ---- Mit Zeit: pause freezes the countdown, » at the end = aborted ----
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(300)
        await pg.click(f'#freeOwnGrid [data-free-id="{ids["Mobilisation"]}"]'); await pg.wait_for_timeout(120)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(1300)
        t1 = await pg.inner_text("#freeRunCountdown")
        check("timer runs and has no Erledigt button", t1 in ("11:59", "11:58") and not await pg.is_visible("#freeTickBtn"), t1)
        await pg.click("#freePauseBtn"); await pg.wait_for_timeout(200)
        check("Pause opens the shared 'Pausiert' sheet", await pg.is_visible("#trainPauseOverlay"))
        p1 = await pg.inner_text("#freeRunCountdown"); await pg.wait_for_timeout(1500)
        check("countdown frozen while paused", await pg.inner_text("#freeRunCountdown") == p1)
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(1300)
        t2 = await pg.inner_text("#freeRunCountdown")
        check("countdown continues after Weiter", t2 != p1 and t2 >= "11:56", (p1, t2))
        n_before = len(await history(pg))
        await pg.click("#freeBackBtn"); await pg.wait_for_timeout(200)
        check("✕ Beenden returns to the ready screen without a history entry",
              await visible_screen(pg) == "freeReady" and len(await history(pg)) == n_before)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#stepNav [data-slot='next'] button") if await pg.locator("#stepNav [data-slot='next'] button").count() else await pg.click("#freeSkipBtn")
        await pg.wait_for_timeout(250)
        h = (await history(pg))[0]
        check("» past the end counts as aborted", await pg.is_visible("#freeDonePanel") and h.get("aborted") is True
              and h.get("note") == "abgebrochen" and not await pg.is_visible("#freeDonePanel .done-check"), h)
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(150)

        # ---- Checkliste: tick, then a 10 s countdown advances on its own ----
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)
        await pg.click(f'#freeOwnGrid [data-free-id="{ids["Journal"]}"]'); await pg.wait_for_timeout(120)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(200)
        check("checklist point 1 (ohne Zeit): tick button, 'Als Nächstes'",
              await pg.inner_text("#freeRunItem") == "Drei gute Dinge" and await pg.is_visible("#freeTickBtn")
              and "Ziel für morgen" in await pg.inner_text("#freeRunNext"))
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(300)
        check("point 2 (10 s): countdown", "2 VON 2" in (await pg.inner_text("#freeRunProgress")).upper() and await pg.is_visible("#freeRunCountdown"))
        await pg.wait_for_selector("#freeDonePanel", state="visible", timeout=14000)
        h = (await history(pg))[0]
        check("countdown runs out -> finished, not aborted", h["title"] == "Journal" and not h.get("aborted") and h["seconds"] >= 9, h)
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(150)

        # ---- Dehnen template ----
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)
        await pg.click('#freeTplGrid [data-free-id="tpl-dehnen"]'); await pg.wait_for_timeout(150)
        items = await pg.locator("#freeReadyItems .chapter-row").count()
        check("Dehnen: 8 points of 30 s, no Bearbeiten (template), Kopieren offered",
              items == 8 and not await pg.is_visible("#freeEditBtn") and await pg.is_visible("#freeCopyBtn"))
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(1300)
        c = await pg.inner_text("#freeRunCountdown")
        check("Dehnen run: Waden with a running 30 s countdown", await pg.inner_text("#freeRunItem") == "Waden" and c in ("0:29", "0:28"), c)
        await pg.click("#freeSkipBtn"); await pg.wait_for_timeout(200)
        check("» goes to the next point", await pg.inner_text("#freeRunItem") == "Oberschenkel vorne"
              and "2 VON 8" in (await pg.inner_text("#freeRunProgress")).upper())
        await pg.click("#freePrevBtn"); await pg.wait_for_timeout(200)
        check("« goes back", await pg.inner_text("#freeRunItem") == "Waden")
        await pg.click("#freeBackBtn"); await pg.wait_for_timeout(200)
        await pg.click("#freeCopyBtn"); await pg.wait_for_timeout(150)
        await pg.fill("#freeTitleInput", "Mein Dehnen")
        await pg.click('#freeItemList .free-item-row >> nth=7 >> [data-remove]')
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        blocks = await own_blocks(pg)
        check("Kopieren und anpassen saves an own copy, template unchanged",
              blocks[-1]["title"] == "Mein Dehnen" and len(blocks[-1]["items"]) == 7 and await pg.locator("#freeReadyItems .chapter-row").count() == 7)

        # ---- delete only via confirmDialog ----
        await pg.click("#freeEditBtn"); await pg.wait_for_timeout(120)
        await pg.click("#freeDeleteBtn"); await pg.wait_for_timeout(150)
        check("Löschen asks first", await pg.is_visible("#confirmYesBtn"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("deleted, back on the area home", len(await own_blocks(pg)) == 3 and await visible_screen(pg) == "freeHome")

        # ---- Kombi: capture (own copy), edit, playback ----
        await pg.click('#freeHome [data-open-combo="1"]'); await pg.wait_for_timeout(200)
        grp = await pg.evaluate("""() => { const g = [...document.querySelectorAll('#comboAddGrid .combo-domain-group')]
          .find(x => x.querySelector('.combo-domain-title').textContent === 'Freier Baustein');
          return g ? [...g.querySelectorAll('.ca-title')].map(e => e.textContent) : null; }""")
        check("Kombi offers a 'Freier Baustein' group with own + template + new", grp and "Eisbad" in grp and "Dehnen" in grp and "Neuer freier Baustein" in grp, grp)
        await pg.click('#comboAddGrid .combo-add-btn:has(.ca-title:text-is("Eisbad"))'); await pg.wait_for_timeout(150)
        check("capture opens the editor with 'Baustein übernehmen'", await visible_screen(pg) == "freeEdit"
              and await pg.inner_text("#freeSaveBtn") == "Baustein übernehmen" and not await pg.is_visible("#freeDeleteBtn"))
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        check("committed back to the Kombi", await visible_screen(pg) == "comboScreen" and await pg.locator("#comboBlockList .chapter-row").count() == 1)
        await pg.click('#comboAddGrid .combo-add-btn:has(.ca-title:text-is("Neuer freier Baustein"))'); await pg.wait_for_timeout(150)
        await pg.fill("#freeTitleInput", "Ruhig atmen")
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        await pg.click("#comboBlockList .chapter-row >> nth=0 >> .chapter-main"); await pg.wait_for_timeout(150)
        check("a Baustein is editable again", await visible_screen(pg) == "freeEdit" and await pg.input_value("#freeTitleInput") == "Eisbad")
        await pg.fill("#freeTitleInput", "Eisbad kalt")
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        labels = await pg.eval_on_selector_all("#comboBlockList .chapter-row strong", "els => els.map(e => e.textContent)")
        check("edit replaced the block in place", labels == ["Eisbad kalt", "Ruhig atmen"], labels)
        check("the saved Baustein is untouched by the Kombi edit", (await own_blocks(pg))[0]["title"] == "Eisbad")
        await pg.evaluate("() => { const s = document.querySelector('#comboBlockList .combo-pause-slider'); s.value = '0'; s.dispatchEvent(new Event('input')); }")
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(250)
        check("Kombi plays the first free block", await pg.is_visible("#freePlayer") and await pg.inner_text("#freeRunTitle") == "Eisbad kalt")
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(300)
        check("hands over to the next Baustein", await pg.is_visible("#freePlayer") and await pg.inner_text("#freeRunTitle") == "Ruhig atmen")
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(300)
        h = (await history(pg))[0]
        check("Kombi finishes with one Kombi history entry", await pg.is_visible("#comboDonePanel") and h["kind"] == "combo"
              and not await pg.is_visible("#freeDonePanel"), h.get("kind"))
        await pg.click("#comboDoneBackBtn"); await pg.wait_for_timeout(200)
        check("back from the Kombi lands on the free area home", await visible_screen(pg) == "freeHome")
        await b.close()
    check("no page or console errors", not errors, errors[:3])
    bad = [n for n, ok in results if not ok]
    print("FAILED:", bad if bad else "none")


asyncio.run(main())
