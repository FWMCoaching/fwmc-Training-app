import asyncio, json, os, urllib.parse
from playwright.async_api import async_playwright

# Trainer-Vorlagen per Code (Fabian, 2026-10-05: "also so wie die eigenen
# Übungen die sie gestalten können? Dann ja"): a code of type
# "free-template" carries trainings in the Eigenes-Training shape. Entering
# it (Training hub, area code card, Heute) adds them as read-only templates
# "Von deinem Trainer" in #freeHome; re-entering updates instead of
# duplicating; broken defs show the one code error; templates start, go into
# the Kombi and the Wochenplan, can be copied and edited, can be removed via
# confirmDialog; everything survives a reload. The dashboard builder writes
# such a code and the saved config opens in the real app. The live Worker is
# never used (CODE_API routed).
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
DASH = f"http://localhost:{PORT}/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


V1 = {"type": "free-template", "name": "Vorlagen Anna", "message": "",
      "trainings": [
          {"kind": "list", "title": "Mobilisation", "note": "Ruhig atmen.",
           "items": [{"text": "Schultern kreisen", "s": 2}, {"text": "Hüfte kreisen", "s": 0}, {"text": "", "s": 10}]},
          {"kind": "timer", "title": "Eisbad", "minutes": 3},
      ]}
V2 = {"type": "free-template", "name": "Vorlagen Anna",
      "trainings": [
          {"kind": "list", "title": "Mobilisation neu", "items": [{"text": "Schultern kreisen", "s": 20}]},
          {"kind": "timer", "title": "Eisbad", "minutes": 4},
          {"kind": "check", "title": "Journal"},
      ]}
OTHER = {"type": "free-template", "name": "Andere", "trainings": [{"kind": "check", "title": "Atemnotiz"}]}
BROKEN = {
    "kaputt-leer": {"type": "free-template", "trainings": []},
    "kaputt-liste": {"type": "free-template", "trainings": [{"kind": "list", "title": "Leer", "items": [{"text": "  ", "s": 10}]}]},
    "kaputt-form": {"type": "free-template", "trainings": "nein"},
    "kaputt-punkte": {"type": "free-template", "trainings": [{"kind": "check", "title": "X", "items": "nein"}]},
}


async def visible_screen(pg):
    return await pg.evaluate("(() => { const s = [...document.querySelectorAll('.screen')].find((el) => !el.hidden); return s ? s.id : null; })()")


async def trainer_store(pg):
    return await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-free-trainer-v1') || '[]')")


async def card_titles(pg, grid):
    return await pg.evaluate(f"[...document.querySelectorAll('#{grid} .fc-title')].map((e) => e.textContent)")


async def main():
    errors = []
    served = {"anna-vorlage": V1, "andere-vorlage": OTHER, **BROKEN}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script("""localStorage.setItem('fwmc-tips-seen','true');
          localStorage.setItem('fwmc-test-bottomnav','true');
          localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));""")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

        async def api(route):
            url = route.request.url
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            code = (q.get("code") or [""])[0].lower()
            if "/program" in url and code in served:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(served[code]))
            else:
                await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
        await ctx.route("https://online-training.fwmc.workers.dev/**", api)

        # ---- empty state: no trainer section ----
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        check("no trainer section without a code", await pg.is_hidden("#freeTrainerSection"))

        # ---- enter the code on the Training hub ----
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        await pg.click('#bottomNav [data-nav="training"]'); await pg.wait_for_timeout(200)
        await pg.fill("#moreCodeInput", "Anna-Vorlage"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
        check("hub code opens Eigenes Training", await visible_screen(pg) == "freeHome", await visible_screen(pg))
        check("trainer section visible", await pg.is_visible("#freeTrainerSection"))
        check("section heading 'Von deinem Trainer'", "Von deinem Trainer" in await pg.inner_text("#freeTrainerSection h2"))
        check("both trainings listed", await card_titles(pg, "freeTrainerGrid") == ["Mobilisation", "Eisbad"], await card_titles(pg, "freeTrainerGrid"))
        notice = await pg.inner_text("#freeTrainerNotice")
        check("notice names the new trainings", await pg.is_visible("#freeTrainerNotice") and "Neu von deinem Trainer" in notice and "Eisbad" in notice, notice)
        store = await trainer_store(pg)
        check("stored per code with stable ids", [x["id"] for x in store] == ["tr-anna-vorlage-1", "tr-anna-vorlage-2"] and all(x["code"] == "anna-vorlage" for x in store), store)
        check("empty checklist point dropped", [i["text"] for i in store[0]["items"]] == ["Schultern kreisen", "Hüfte kreisen"])
        check("own list untouched", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-free-blocks-v1') || '[]').length") == 0)
        check("code history recorded", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-code-history-v1') || '[]').some((h) => h.code === 'Anna-Vorlage' || h.code === 'anna-vorlage')"))

        # ---- ready screen: read-only, labelled ----
        await pg.click('#freeTrainerGrid [data-free-id="tr-anna-vorlage-1"]'); await pg.wait_for_timeout(200)
        check("ready screen opens", await visible_screen(pg) == "freeReady")
        meta = await pg.inner_text("#freeReadyMeta")
        check("meta says 'von deinem Trainer'", "von deinem Trainer" in meta, meta)
        check("no Bearbeiten, but Kopieren and Entfernen", await pg.is_hidden("#freeEditBtn") and await pg.is_visible("#freeCopyBtn") and await pg.is_visible("#freeTrainerRemoveBtn"))
        check("note shown", "Ruhig atmen" in await pg.inner_text("#freeReadyNote"))

        # ---- it runs ----
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(300)
        check("player runs the template", await pg.is_visible("#freePlayer") and "Schultern kreisen" in await pg.inner_text("#freeRunItem"))
        await pg.wait_for_timeout(2600)
        check("timed point moves on by itself", "Hüfte kreisen" in await pg.inner_text("#freeRunItem"))
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(400)
        check("done panel after the last point", await pg.is_visible("#freeDonePanel"))
        h = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0]")
        check("history entry with freeId", h and h.get("kind") == "free" and h.get("freeId") == "tr-anna-vorlage-1", h)
        await pg.evaluate("[...document.querySelectorAll('#freeDonePanel button')].find((b) => /Übersicht/.test(b.textContent)).click()"); await pg.wait_for_timeout(200)

        # ---- copy and adapt -> becomes an own training ----
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.click('#freeTrainerGrid [data-free-id="tr-anna-vorlage-2"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeCopyBtn"); await pg.wait_for_timeout(150)
        check("copy opens the editor", await visible_screen(pg) == "freeEdit" and await pg.input_value("#freeTitleInput") == "Eisbad")
        await pg.fill("#freeTitleInput", "Eisbad lang"); await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(200)
        own = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-free-blocks-v1') || '[]')")
        check("copy saved as own training", len(own) == 1 and own[0]["title"] == "Eisbad lang" and own[0]["kind"] == "timer" and own[0]["minutes"] == 3, own)
        check("template itself unchanged", [x["title"] for x in await trainer_store(pg)] == ["Mobilisation", "Eisbad"])

        # ---- Kombi + Wochenplan see the templates ----
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.click('[data-nav="training"]'); await pg.wait_for_timeout(250); await pg.click('#trainingHub .combo-entry-link'); await pg.wait_for_timeout(200)
        labels = await pg.evaluate("[...document.querySelectorAll('#comboAddGrid button')].map((b) => b.textContent)")
        check("Kombi offers the trainer templates", any("Mobilisation" in l for l in labels) and any("Eisbad" in l and "lang" not in l for l in labels), labels)
        opts = await pg.evaluate("""(() => { const s = document.getElementById('planEntryArea'); s.value = 'free'; s.dispatchEvent(new Event('change'));
          return [...document.getElementById('planEntryWhat').options].map((o) => o.value); })()""")
        check("Wochenplan lists the templates", "free:tr-anna-vorlage-1" in opts and "free:tr-anna-vorlage-2" in opts, opts)

        # ---- re-enter the same code after the trainer changed it ----
        served["anna-vorlage"] = V2
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.fill("#freeProgramCodeInput", "anna-vorlage"); await pg.click("#freeProgramGoBtn"); await pg.wait_for_timeout(500)
        check("re-entering updates instead of duplicating", await card_titles(pg, "freeTrainerGrid") == ["Mobilisation neu", "Eisbad", "Journal"], await card_titles(pg, "freeTrainerGrid"))
        check("notice says 'Aktualisiert'", "Aktualisiert" in await pg.inner_text("#freeTrainerNotice"))
        st = await trainer_store(pg)
        check("same ids kept, Eisbad now 4 min", [x["id"] for x in st] == ["tr-anna-vorlage-1", "tr-anna-vorlage-2", "tr-anna-vorlage-3"] and st[1]["minutes"] == 4, st)

        # ---- a second code from the Visual Training code card adds, does not replace ----
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.fill("#programCodeInput", "andere-vorlage"); await pg.click("#programGoBtn"); await pg.wait_for_timeout(500)
        check("area code card works too", await visible_screen(pg) == "freeHome")
        check("second code adds its template", await card_titles(pg, "freeTrainerGrid") == ["Mobilisation neu", "Eisbad", "Journal", "Atemnotiz"], await card_titles(pg, "freeTrainerGrid"))

        # ---- broken defs -> the one error message, nothing stored ----
        for code in BROKEN:
            await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(350)
            await pg.fill("#freeProgramCodeInput", code); await pg.click("#freeProgramGoBtn"); await pg.wait_for_timeout(400)
            err = await pg.inner_text("#freeProgramError")
            check(f"broken def '{code}' shows the code error", await pg.is_visible("#freeProgramError") and "Trainer" in err and await visible_screen(pg) == "freeHome", err)
        check("broken defs stored nothing", len(await trainer_store(pg)) == 4)
        await pg.fill("#freeProgramCodeInput", "gibtsnicht"); await pg.click("#freeProgramGoBtn"); await pg.wait_for_timeout(400)
        check("unknown code: not-found text", "kein Training gefunden" in await pg.inner_text("#freeProgramError"))

        # ---- persistence across reload ----
        await pg.reload(); await pg.wait_for_timeout(400)
        check("templates survive a reload", await card_titles(pg, "freeTrainerGrid") == ["Mobilisation neu", "Eisbad", "Journal", "Atemnotiz"])
        check("notice gone after reload", await pg.is_hidden("#freeTrainerNotice"))

        # ---- remove one via the ready screen (confirmDialog) ----
        await pg.click('#freeTrainerGrid [data-free-id="tr-andere-vorlage-1"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeTrainerRemoveBtn"); await pg.wait_for_timeout(150)
        check("remove asks first", await pg.is_visible("#confirmSheet") and "Atemnotiz" in await pg.inner_text("#confirmText"))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(100)
        check("Nein keeps it", len(await trainer_store(pg)) == 4)
        await pg.click("#freeTrainerRemoveBtn"); await pg.wait_for_timeout(100)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(250)
        check("Ja removes it and returns to the list", await visible_screen(pg) == "freeHome" and await card_titles(pg, "freeTrainerGrid") == ["Mobilisation neu", "Eisbad", "Journal"])

        # ---- dashboard builder writes a code the app opens ----
        saved = []
        dash = await ctx.new_page()
        dash.on("pageerror", lambda e: errors.append("dash pageerror: " + str(e)))

        async def dash_api(route):
            req = route.request
            if "/admin/programs" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": [
                    {"code": "alt-vorlage", "name": "Alt", "active": True, "updatedAt": "2026-10-01T10:00:00Z", "config": V2}]}))
            elif "/admin/program" in req.url and req.method == "POST":
                saved.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": True}))
            elif "/admin/client-history" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"entries": []}))
            else:
                await api(route)
        await dash.route("https://online-training.fwmc.workers.dev/**", dash_api)
        await dash.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await dash.goto(DASH); await dash.wait_for_timeout(500)
        await dash.fill("#pCode", "neu-vorlage"); await dash.fill("#pName", "Vorlagen Ben")
        await dash.click('#kindRow [data-kind="free"]')
        check("dashboard: free builder shown", await dash.is_visible("#freeBuilder") and await dash.is_hidden("#visualBuilder"))
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(100)
        check("dashboard: needs a training", "Mindestens ein Training" in await dash.inner_text("#pMsg"))
        await dash.click("#freeAddBtn"); await dash.wait_for_timeout(80)
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(100)
        check("dashboard: needs a title", "Titel" in await dash.inner_text("#pMsg"))
        card = dash.locator("#freeList .free-card").nth(0)
        await card.locator('[data-f="title"]').fill("Morgenroutine")
        await card.locator('[data-f="note"]').fill("Langsam")
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(100)
        check("dashboard: checklist needs a point", "Punkt" in await dash.inner_text("#pMsg"))
        await card.locator('[data-p="text"]').nth(0).fill("Strecken")
        await card.locator('[data-p="s"]').nth(0).fill("45")
        await card.locator('[data-f="addPoint"]').click(); await dash.wait_for_timeout(60)
        card = dash.locator("#freeList .free-card").nth(0)
        await card.locator('[data-p="text"]').nth(1).fill("Wasser trinken")
        await card.locator('[data-p="s"]').nth(1).fill("0")
        await dash.click("#freeAddBtn"); await dash.wait_for_timeout(60)
        card2 = dash.locator("#freeList .free-card").nth(1)
        await card2.locator('[data-f-kind="timer"]').click(); await dash.wait_for_timeout(60)
        card2 = dash.locator("#freeList .free-card").nth(1)
        await card2.locator('[data-f="title"]').fill("Meditation")
        await card2.locator('[data-f="minutes"]').fill("10")
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(250)
        cfg = saved[-1]["config"] if saved else {}
        want = {"type": "free-template", "name": "Vorlagen Ben", "trainings": [
            {"kind": "list", "title": "Morgenroutine", "note": "Langsam", "items": [{"text": "Strecken", "s": 45}, {"text": "Wasser trinken", "s": 0}]},
            {"kind": "timer", "title": "Meditation", "minutes": 10}]}
        check("dashboard: saved free-template config", saved and saved[-1]["code"] == "neu-vorlage" and all(cfg.get(k) == v for k, v in want.items()), cfg)
        # editing an existing free-template code opens it in the builder
        await dash.click("text=alt-vorlage"); await dash.wait_for_timeout(250)
        check("dashboard: existing code opens in the builder", await dash.is_visible("#freeBuilder") and await dash.locator("#freeList .free-card").count() == 3
              and await dash.locator("#freeList .free-card").nth(2).locator('[data-f="title"]').input_value() == "Journal")
        await dash.close()
        # the saved config opens in the real app
        served["neu-vorlage"] = cfg
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.fill("#freeProgramCodeInput", "neu-vorlage"); await pg.click("#freeProgramGoBtn"); await pg.wait_for_timeout(500)
        titles = await card_titles(pg, "freeTrainerGrid")
        check("dashboard code opens in the app", titles[-2:] == ["Morgenroutine", "Meditation"], titles)

        check("no page/console errors", not errors, errors)
        await b.close()
    failed = [n for n, ok in results if not ok]
    print("\nALL PASSED" if not failed else f"\nFAILED: {failed}")


asyncio.run(main())
