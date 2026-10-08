import asyncio, json, os, urllib.parse
from playwright.async_api import async_playwright

# Neuro-Aktivierung (Idee 68, Fabian 08.10.): a hidden area, unlocked by a
# trainer code of type "neuro-unlock". Hidden = no hub tile, no ?bereich=,
# no Kombi group, no Wochenplan entries, no gear cards. Unlocked: hub row
# "Für dich freigeschaltet", 4 guided templates (side cue, timer, Takt,
# pause sheet, Beenden, history, presets), Kombi capture/edit/playback.
# A trainer Kombi code with neuro blocks plays for a NOT unlocked client as
# "Spezialübung von deinem Trainer" (tag in the run, the Kombi pause and the
# history note) while the area stays hidden and the blocks can't be copied.
# The dashboard builds both code types. The live Worker is never used
# (CODE_API routed). Screenshots: tests/screenshots/neuro/.
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
DASH = f"http://localhost:{PORT}/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "neuro")
os.makedirs(SHOTS, exist_ok=True)
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra if not ok else "")


SERVED = {
    "neuro-frei": {"type": "neuro-unlock", "name": "Neuro freischalten"},
    "neuro-aus": {"type": "neuro-unlock", "name": "aus", "lock": True},
    "spezial": {"type": "combo-program", "name": "Spezial vor dem Spiel", "blocks": [
        {"domain": "neuro", "ex": "vibration", "prefs": {"stepS": 10, "reps": 1}, "pauseAfterS": 5},
        {"domain": "neuro", "ex": "gelenke", "prefs": {"stepS": 10}},
    ]},
    "spezial-paket": {"type": "combo-bundle", "name": "Pakete", "programs": [
        {"label": "Mit Spezialübung", "blocks": [{"domain": "neuro", "ex": "ball-hand", "prefs": {"stepS": 10}}]},
    ]},
}
INIT = """localStorage.setItem('fwmc-tips-seen','true');
  localStorage.setItem('fwmc-test-bottomnav','true');
  localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"""


async def visible_screen(pg):
    return await pg.evaluate("(() => { const s = [...document.querySelectorAll('.screen')].find((el) => !el.hidden); return s ? s.id : null; })()")


async def hub_areas(pg):
    await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
    return await pg.evaluate("[...document.querySelectorAll('#hubAreaGrid .area-tile')].map((t) => t.dataset.area)")


async def kombi_domains(pg):
    await pg.evaluate("document.querySelector('[data-open-combo]').click()"); await pg.wait_for_timeout(200)
    return await pg.evaluate("[...document.querySelectorAll('#comboAddGrid .combo-domain-group')].map((g) => g.dataset.domain)")


async def tray_texts(pg, tab):
    await pg.goto(BASE + "?bereich=today"); await pg.wait_for_timeout(300)
    await pg.evaluate("document.getElementById('todayPlanBtn').click()"); await pg.wait_for_timeout(250)
    await pg.click(f'[data-tray-tab="{tab}"]'); await pg.wait_for_timeout(120)
    return await pg.evaluate("[...document.querySelectorAll('#planTrayItems .plan-chip')].map((c) => c.textContent.trim())")


async def no_side_scroll(pg):
    return await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


async def set_step(pg, v):
    # Dauer pro Schritt is one slider since 08.10. (no duplicate chips)
    await pg.evaluate("(v) => { const i = document.querySelector('#neuroReadyControls input[data-nr-r=stepS]'); i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); }", v)


async def skip_step(pg):
    await pg.evaluate("window.__neuroSkipTime(999)"); await pg.wait_for_timeout(160)


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        async def api(route):
            url = route.request.url
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            code = (q.get("code") or [""])[0].lower()
            if "/program" in url and code in SERVED:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(SERVED[code]))
            else:
                await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')

        async def new_ctx(w=390, h=844, scheme="light"):
            ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme=scheme)
            await ctx.add_init_script(INIT)
            await ctx.route("https://online-training.fwmc.workers.dev/**", api)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            return ctx, pg

        # ================= 1. hidden without the unlock =================
        ctx, pg = await new_ctx()
        areas = await hub_areas(pg)
        check("locked: no Neuro tile on the Training page", "neuro" not in areas and len(areas) >= 8, areas)
        check("locked: no 'Für dich freigeschaltet' row", "Für dich freigeschaltet" not in await pg.evaluate("document.getElementById('hubAreaGrid').textContent"))
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(300)
        check("locked: ?bereich=neuro falls back to Heute", await visible_screen(pg) == "todayHome", await visible_screen(pg))
        await pg.goto(BASE + "?bereich=neuro-aktivierung"); await pg.wait_for_timeout(300)
        check("locked: ?bereich=neuro-aktivierung falls back too", await visible_screen(pg) == "todayHome")
        await pg.evaluate("document.querySelector('[data-open-combo]').click()"); await pg.wait_for_timeout(200)
        doms = await pg.evaluate("[...document.querySelectorAll('#comboAddGrid .combo-domain-group')].map((g) => g.dataset.domain)")
        check("locked: no Neuro group in the Kombi", "neuro" not in doms and "activation" in doms, doms)
        chips = await tray_texts(pg, "area")
        check("locked: Wochenplan areas without Neuro", not any("Neuro-Aktivierung" in c for c in chips) and len(chips) >= 8, chips)
        chips = await tray_texts(pg, "ex")
        check("locked: Wochenplan exercises without Neuro", not any(c in ("Gelenke kreisen", "Vibration links / rechts") for c in chips))
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(250)
        await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(150)
        await pg.click("#moreGearBtn"); await pg.wait_for_timeout(200)
        gear = await pg.inner_text("#gearScreen")
        check("locked: no Neuro gear cards", "Vibrationsgerät" not in gear and "Knochenschall" not in gear)

        # ================= 2. a trainer Kombi code with a Spezialübung (still locked) =================
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.fill("#moreCodeInput", "spezial"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(600)
        st = await pg.evaluate("window.__neuro()")
        check("Spezialübung: neuro block plays for a locked client", st and st["ex"] == "vibration" and st["special"] and not st["own"], st)
        check("Spezialübung: tag in the run", await pg.is_visible("#neuroRunSpecial") and "Spezialübung von deinem Trainer" in await pg.inner_text("#neuroRunSpecial"))
        check("Spezialübung: block settings from the code (10 s)", st and st["p"]["stepS"] == 10)
        await pg.screenshot(path=os.path.join(SHOTS, "spezial_player_390_light.png"))
        for _ in range(60):
            if not await pg.evaluate("!!window.__neuro()"): break
            await skip_step(pg)
        check("Spezialübung: Kombi pause shows the tag for the next block",
              await pg.is_visible("#comboTransition") and await pg.is_visible("#comboTransitionSpecial") and "Gelenke kreisen" in await pg.inner_text("#comboTransitionTitle"))
        check("Spezialübung: Kombi pause names the result", "Spezialübung von deinem Trainer" in await pg.inner_text("#comboTransition"))
        await pg.screenshot(path=os.path.join(SHOTS, "spezial_kombipause_390_light.png"))
        await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(200)
        check("Spezialübung: second block (Gelenke) runs", (await pg.evaluate("window.__neuro()") or {}).get("ex") == "gelenke")
        for _ in range(60):
            if not await pg.evaluate("!!window.__neuro()"): break
            await skip_step(pg)
        check("Spezialübung: Kombi finishes", await pg.is_visible("#comboDonePanel"))
        hist = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-history-v1') || localStorage.getItem('fwmc-history') || '[]')")
        hist_any = await pg.evaluate("Object.keys(localStorage).filter((k) => k.includes('history')).map((k) => localStorage.getItem(k)).join(' ')")
        check("Spezialübung: history note names it", "Spezialübung von deinem Trainer" in hist_any, hist_any[:300])
        check("Spezialübung: no own neuro history entry", '"kind":"neuro"' not in hist_any)
        check("Spezialübung: area still locked", await pg.evaluate("localStorage.getItem('fwmc-neuro-unlocked-v1')") is None)
        areas = await hub_areas(pg)
        check("Spezialübung: still no Neuro tile", "neuro" not in areas)
        # can't be copied into an own Kombi
        await pg.evaluate("document.querySelector('[data-open-combo]').click()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.getElementById('comboInsertGroup').open = true"); await pg.wait_for_timeout(200)
        ins = await pg.inner_text("#comboInsertList")
        check("Spezialübung: trainer Kombi not offered for 'einfügen'", "Spezial vor dem Spiel" not in ins, ins[:200])
        # combo-bundle overview tags the programme
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.fill("#moreCodeInput", "spezial-paket"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
        check("Spezialübung: tag in the programme list", await pg.is_visible("#comboBundleList .special-tag"))
        await pg.screenshot(path=os.path.join(SHOTS, "spezial_liste_390_light.png"))
        await ctx.close()

        # ================= 3. unlock by code =================
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.fill("#moreCodeInput", "neuro-frei"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
        check("unlock: code opens Neuro-Aktivierung", await visible_screen(pg) == "neuroHome", await visible_screen(pg))
        check("unlock: notice shown", await pg.is_visible("#neuroUnlockNotice"))
        check("unlock: stored on the device", await pg.evaluate("localStorage.getItem('fwmc-neuro-unlocked-v1')") == "true")
        check("unlock: 4 templates", await pg.locator("#neuroGrid [data-neuro-ex]").count() == 4)
        await pg.screenshot(path=os.path.join(SHOTS, "home_390_light.png"), full_page=True)
        areas = await hub_areas(pg)
        check("unlock: Neuro tile on the Training page", "neuro" in areas, areas)
        check("unlock: core tiles keep their places", areas[:4] == ["visual", "breath", "nat", "movement"], areas)
        check("unlock: own row 'Für dich freigeschaltet'", "Für dich freigeschaltet" in await pg.evaluate("document.getElementById('hubAreaGrid').textContent")
              and await pg.locator(".hub-unlocked [data-area=neuro]").count() == 1)
        await pg.screenshot(path=os.path.join(SHOTS, "hub_390_light.png"), full_page=True)
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(300)
        check("unlock: ?bereich=neuro opens the area after reload", await visible_screen(pg) == "neuroHome")
        doms = await kombi_domains(pg)
        n_k = await pg.locator("#comboAddGrid .combo-domain-group[data-domain=neuro] .combo-add-btn").count()
        check("unlock: Kombi group with every template", "neuro" in doms and n_k == 4, (doms, n_k))
        chips = await tray_texts(pg, "area")
        check("unlock: Wochenplan area", any("Neuro-Aktivierung" in c for c in chips), chips)
        chips = await tray_texts(pg, "ex")
        check("unlock: Wochenplan exercises", "Gelenke kreisen" in chips and "Massageball: Hände" in chips)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(250)
        await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(150)
        await pg.click("#moreGearBtn"); await pg.wait_for_timeout(200)
        gear = await pg.inner_text("#gearScreen")
        check("unlock: gear cards Vibrationsgerät, Massageball, Knochenschall", all(x in gear for x in ["Vibrationsgerät", "Massageball oder Massagepilz", "Knochenschall-Kopfhörer"]))
        check("unlock: gear chips open the exercises", await pg.locator('[data-gear="massageball"] .gear-ex-chip').count() == 2)
        await pg.locator('[data-gear="vibration"] .gear-ex-chip').first.click(); await pg.wait_for_timeout(200)
        check("unlock: gear chip opens the ready screen", await visible_screen(pg) == "neuroReady" and "Vibration" in await pg.inner_text("#neuroReadyTitle"))

        # ================= 4. every template runs =================
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(300)
        # Vibration: links -> Umsetzen -> rechts, spoken
        await pg.click('[data-neuro-ex="vibration"]'); await pg.wait_for_timeout(200)
        check("ready: Hilfsmittel note", await pg.is_visible("#neuroHilfsmittel") and "Z\u2011Vibe" in await pg.inner_text("#neuroHilfsmittel"))
        check("ready: start button 'Training starten'", (await pg.inner_text("#neuroStartBtn")).strip() == "Training starten")
        check("ready: step list (5 places x 2 sides)", await pg.locator("#neuroReadySteps .chapter-row").count() == 10)
        await pg.screenshot(path=os.path.join(SHOTS, "ready_390_light.png"), full_page=True)
        await pg.evaluate("window.__cueLog = []")
        await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(250)
        st = await pg.evaluate("window.__neuro()")
        check("vibration: starts with Links", st and st["side"] == "Links", st)
        check("vibration: side spoken", any("links" in x for x in await pg.evaluate("window.__cueLog")), await pg.evaluate("window.__cueLog"))
        check("vibration: countdown shows 0:20", (await pg.inner_text("#neuroRunCountdown")).strip() in ("0:20", "0:19"))
        await pg.screenshot(path=os.path.join(SHOTS, "player_390_light.png"))
        await skip_step(pg)
        st = await pg.evaluate("window.__neuro()")
        check("vibration: Umsetzen before the right side", st and st["phase"] == "move" and "Rechts" in st["side"], st)
        await skip_step(pg)
        st = await pg.evaluate("window.__neuro()")
        check("vibration: then Rechts", st and st["phase"] == "work" and st["side"] == "Rechts" and st["index"] == 1, st)
        # pause sheet: frozen time, live Takt
        await pg.click("#neuroPauseBtn"); await pg.wait_for_timeout(150)
        t1 = await pg.inner_text("#neuroRunCountdown"); await pg.wait_for_timeout(1300); t2 = await pg.inner_text("#neuroRunCountdown")
        check("pause: sheet open, time frozen", await pg.is_visible("#neuroPauseOverlay") and t1 == t2 and (await pg.evaluate("window.__neuro()"))["paused"])
        await pg.click('#neuroPauseControls [data-nr-f="takt"][data-nr-v="1"]'); await pg.wait_for_timeout(80)
        check("pause: Takt on saves to the own settings", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-neuro-prefs-v1')).vibration.takt") is True)
        await pg.screenshot(path=os.path.join(SHOTS, "player_pause_390_light.png"))
        await pg.click("#neuroResumeBtn"); await pg.wait_for_timeout(150)
        ticks0 = await pg.evaluate("window.__neuroTicks || 0"); await pg.wait_for_timeout(2300)
        ticks1 = await pg.evaluate("window.__neuroTicks || 0")
        check("Takt: ticks at 60 per minute", ticks1 - ticks0 >= 2, (ticks0, ticks1))
        # Beenden: no history, back to the ready screen
        await pg.click("#neuroBackBtn"); await pg.wait_for_timeout(250)
        check("Beenden: back to the ready screen, no entry", await visible_screen(pg) == "neuroReady"
              and '"kind":"neuro"' not in await pg.evaluate("Object.keys(localStorage).filter((k) => k.includes('history')).map((k) => localStorage.getItem(k)).join(' ')"))
        await pg.evaluate("document.querySelector('#neuroReadyControls [data-nr-f=\"takt\"][data-nr-v=\"0\"]').click()")

        async def run_through(ex, expect_n, label_check=None):
            await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(250)
            await pg.click(f'[data-neuro-ex="{ex}"]'); await pg.wait_for_timeout(150)
            await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(200)
            st = await pg.evaluate("window.__neuro()")
            check(f"{ex}: runs with {expect_n} steps", st and st["n"] == expect_n, st)
            if label_check: await label_check()
            for _ in range(80):
                if not await pg.evaluate("!!window.__neuro()"): break
                await skip_step(pg)
            check(f"{ex}: done panel", await pg.is_visible("#neuroDonePanel") and not await pg.is_visible("#neuroDonePanel .done-panel-aborted"))
            h = await pg.evaluate("Object.keys(localStorage).filter((k) => k.includes('history')).map((k) => localStorage.getItem(k)).join(' ')")
            check(f"{ex}: history entry kind neuro", f'"neuroEx":"{ex}"' in h and '"kind":"neuro"' in h)
            await pg.click("#neuroDoneBackBtn"); await pg.wait_for_timeout(150)

        async def hand_check():
            # last step "Ball von Hand zu Hand geben" alternates
            for _ in range(7):
                await pg.click("#neuroSkipBtn"); await pg.wait_for_timeout(60)
            st = await pg.evaluate("window.__neuro()")
            check("ball-hand: alternating step shows 'Abwechselnd · Links'", st and st["side"] == "Abwechselnd · Links", st)
            await pg.evaluate("window.__cueLog = []")
            await pg.evaluate("window.__neuroSkipTime(4.2)"); await pg.wait_for_timeout(200)
            st = await pg.evaluate("window.__neuro()")
            check("ball-hand: side flips after 4 s and is spoken", st and st["side"] == "Abwechselnd · Rechts" and "Rechts" in await pg.evaluate("window.__cueLog"), st)
            await pg.screenshot(path=os.path.join(SHOTS, "player_wechsel_390_light.png"))

        async def gelenke_check():
            await pg.click("#neuroSkipBtn"); await pg.wait_for_timeout(80)
            st = await pg.evaluate("window.__neuro()")
            check("gelenke: direction cue 'Nach hinten' + stick figure", st and st["side"] == "Nach hinten" and await pg.is_visible("#neuroRunIcon"), st)
            await pg.screenshot(path=os.path.join(SHOTS, "player_gelenke_390_light.png"))

        await run_through("vibration", 10)
        await run_through("ball-fuss", 7)
        await run_through("ball-hand", 8, hand_check)
        await run_through("gelenke", 13, gelenke_check)

        # ================= 5. presets + persistence =================
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(250)
        await pg.click('[data-neuro-ex="gelenke"]'); await pg.wait_for_timeout(150)
        await set_step(pg, 45)
        await pg.click('#neuroReadyControls [data-nr-f="reps"][data-nr-v="2"]')
        check("settings: total updates", "26 Schritte" in await pg.inner_text('#neuroReadyControls [data-nr-out="total"]'))
        await pg.click("#neuroSaveBtn"); await pg.fill("#neuroSaveNameInput", "Lang"); await pg.click("#neuroSaveConfirmBtn"); await pg.wait_for_timeout(100)
        await set_step(pg, 20)
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('[data-neuro-ex="gelenke"]'); await pg.wait_for_timeout(150)
        check("settings persist across reload", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-neuro-prefs-v1')).gelenke.reps") == 2)
        check("preset listed for its exercise", "Lang" in await pg.inner_text("#neuroSavedList"))
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(250)
        await pg.click('[data-neuro-ex="vibration"]'); await pg.wait_for_timeout(150)
        check("preset not listed for another exercise", await pg.is_hidden("#neuroSavedGroup"))
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(250)
        await pg.click('[data-neuro-ex="gelenke"]'); await pg.wait_for_timeout(150)
        await pg.locator("#neuroSavedList .bundle-item").first.click(); await pg.wait_for_timeout(200)
        st = await pg.evaluate("window.__neuro()")
        check("preset tap applies and starts", st and st["p"]["stepS"] == 45 and st["n"] == 26, st)
        await pg.click("#neuroBackBtn"); await pg.wait_for_timeout(150)
        # boundary clamping
        val = await pg.evaluate("""(() => { localStorage.setItem('fwmc-neuro-prefs-v1', JSON.stringify({gelenke:{stepS:999, reps:-4, bpm:5, moveS:77, order:'x'}})); return true; })()""")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('[data-neuro-ex="gelenke"]'); await pg.wait_for_timeout(150)
        await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(150)
        st = await pg.evaluate("window.__neuro()")
        check("clamping: 120 s, 1 Durchgang, 30 bpm, 30 s, lr", st and st["p"]["stepS"] == 120 and st["p"]["reps"] == 1 and st["p"]["bpm"] == 30 and st["p"]["moveS"] == 30 and st["p"]["order"] == "lr", st)
        await pg.click("#neuroBackBtn"); await pg.wait_for_timeout(150)

        # ================= 6. Kombi round trip (unlocked) =================
        await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(250)
        own_before = await pg.evaluate("localStorage.getItem('fwmc-neuro-prefs-v1')")
        await pg.evaluate("document.querySelector('#neuroHome [data-open-combo]').click()"); await pg.wait_for_timeout(200)
        await pg.locator("#comboAddGrid .combo-domain-group[data-domain=neuro] .combo-add-btn", has_text="Massageball: Fußsohlen").click(); await pg.wait_for_timeout(200)
        check("Kombi: capture opens the ready screen", await visible_screen(pg) == "neuroReady" and "Baustein:" in await pg.inner_text("#neuroReadyTitle")
              and (await pg.inner_text("#neuroStartBtn")).strip() == "Baustein übernehmen")
        await set_step(pg, 20)
        await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(200)
        rows = await pg.locator("#comboBlockList .chapter-row").count()
        check("Kombi: Baustein added", await visible_screen(pg) == "comboScreen" and rows == 1 and "Massageball: Fußsohlen" in await pg.inner_text("#comboBlockList"))
        check("Kombi: own settings untouched", await pg.evaluate("localStorage.getItem('fwmc-neuro-prefs-v1')") == own_before)
        await pg.locator("#comboBlockList .chapter-main").first.click(); await pg.wait_for_timeout(200)
        check("Kombi: Baustein re-editable with its values", await visible_screen(pg) == "neuroReady"
              and "20 s" in await pg.inner_text('#neuroReadyControls [data-nr-out="stepS"]'))
        await pg.click('#neuroReadyControls [data-nr-f="reps"][data-nr-v="2"]')
        await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(200)
        check("Kombi: edit replaced the block", await pg.locator("#comboBlockList .chapter-row").count() == 1 and "2 Durchgänge" in await pg.inner_text("#comboBlockList"))
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("window.__neuro()")
        check("Kombi: block plays with its own copy, not special", st and st["ex"] == "ball-fuss" and not st["own"] and not st["special"] and st["p"]["stepS"] == 20 and st["n"] == 14, st)
        check("Kombi: no Spezialübung tag when unlocked", await pg.is_hidden("#neuroRunSpecial"))
        for _ in range(40):
            if not await pg.evaluate("!!window.__neuro()"): break
            await skip_step(pg)
        check("Kombi: finishes", await pg.is_visible("#comboDonePanel"))
        await pg.click("#comboDoneBackBtn"); await pg.wait_for_timeout(200)

        # lock code hides it again
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.fill("#moreCodeInput", "neuro-aus"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
        areas = await pg.evaluate("[...document.querySelectorAll('#hubAreaGrid .area-tile')].map((t) => t.dataset.area)")
        check("lock code hides the area again", "neuro" not in areas and await pg.evaluate("localStorage.getItem('fwmc-neuro-unlocked-v1')") is None, areas)
        await ctx.close()

        # ================= 7. layout 390/1024 light/dark =================
        for w, h in [(390, 844), (1024, 1366)]:
            for scheme in ["light", "dark"]:
                ctx, pg = await new_ctx(w, h, scheme)
                await ctx.add_init_script("localStorage.setItem('fwmc-test-neuro','true')")
                tag = f"{w}_{scheme}"
                await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
                ok_hub = await no_side_scroll(pg)
                if w == 390 and scheme == "dark": await pg.screenshot(path=os.path.join(SHOTS, f"hub_{tag}.png"), full_page=True)
                await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(300)
                ok_home = await no_side_scroll(pg)
                await pg.screenshot(path=os.path.join(SHOTS, f"home_{tag}.png"), full_page=True)
                await pg.click('[data-neuro-ex="ball-hand"]'); await pg.wait_for_timeout(200)
                await pg.evaluate("document.getElementById('neuroAdvanced').open = true; document.getElementById('neuroSafety').open = true")
                ok_ready = await no_side_scroll(pg)
                await pg.screenshot(path=os.path.join(SHOTS, f"ready_{tag}.png"), full_page=True)
                await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(250)
                ok_player = await no_side_scroll(pg)
                await pg.screenshot(path=os.path.join(SHOTS, f"player_{tag}.png"))
                # side pill and step text never overflow the stage
                fits = await pg.evaluate("""(() => { const s = document.getElementById('neuroRunSide').getBoundingClientRect(); return s.left >= 0 && s.right <= window.innerWidth; })()""")
                check(f"layout {tag}: no sideways scroll (hub, home, ready, player)", ok_hub and ok_home and ok_ready and ok_player and fits, (ok_hub, ok_home, ok_ready, ok_player, fits))
                await ctx.close()

        # ================= 8. dashboard builds both code types =================
        ctx, _ = await new_ctx(1024, 1000)
        dash = await ctx.new_page()
        dash.on("pageerror", lambda e: errors.append("dash pageerror: " + str(e)))
        saved = []

        async def dash_api(route):
            req = route.request
            if "/admin/programs" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": [
                    {"code": "spezial", "name": "Spezial vor dem Spiel", "active": True, "updatedAt": "2026-10-08T10:00:00Z", "config": SERVED["spezial"]},
                    {"code": "neuro-frei", "name": "Neuro freischalten", "active": True, "updatedAt": "2026-10-08T10:00:00Z", "config": SERVED["neuro-frei"]}]}))
            elif "/admin/program" in req.url and req.method == "POST":
                saved.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": True}))
            else:
                await route.fulfill(status=200, content_type="application/json", body="{}")
        await dash.route("https://online-training.fwmc.workers.dev/**", dash_api)
        await dash.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await dash.goto(DASH); await dash.wait_for_timeout(600)
        check("dashboard: codes table marks Spezialübung / Freischalten",
              "Spezialübung" in await dash.inner_text("#progTable") and "Neuro freischalten" in await dash.inner_text("#progTable"))
        await dash.fill("#pCode", "spezial-neu"); await dash.fill("#pName", "Vor dem Training")
        await dash.click('#kindRow [data-kind="neuro"]')
        check("dashboard: neuro builder shown", await dash.is_visible("#neuroBuilder") and await dash.is_hidden("#visualBuilder"))
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(100)
        check("dashboard: Kombi needs an exercise", "Mindestens eine Übung" in await dash.inner_text("#pMsg"))
        await dash.locator("#neuroGrid .ex-btn", has_text="Gelenke kreisen").click()
        await dash.locator("#neuroGrid .ex-btn", has_text="Vibration links / rechts").click()
        await dash.locator('#neuroList .neuro-card').nth(0).locator('[data-n="stepS"]').fill("25")
        await dash.locator('#neuroList .neuro-card').nth(1).locator('[data-n="takt"]').check()
        check("dashboard: blocks marked Spezialübung", await dash.locator("#neuroList .pill.sp").count() == 2)
        await dash.screenshot(path=os.path.join(SHOTS, "dashboard_1024_light.png"), full_page=True)
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(250)
        cfg = saved[-1]["config"] if saved else {}
        check("dashboard: saved combo-program with neuro blocks", cfg.get("type") == "combo-program" and [x["ex"] for x in cfg.get("blocks", [])] == ["gelenke", "vibration"]
              and cfg["blocks"][0]["prefs"]["stepS"] == 25 and cfg["blocks"][1]["prefs"]["takt"] is True and cfg["blocks"][0].get("pauseAfterS") == 15, cfg)
        await dash.click('#neuroModeRow [data-neuro-mode="unlock"]')
        await dash.fill("#pCode", "frei-neu"); await dash.fill("#pName", "Freischalten Anna")
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(250)
        cfg2 = saved[-1]["config"] if saved else {}
        check("dashboard: saved neuro-unlock code", cfg2.get("type") == "neuro-unlock" and saved[-1]["code"] == "frei-neu", cfg2)
        await dash.click("text=Spezial vor dem Spiel"); await dash.wait_for_timeout(250)
        check("dashboard: existing Spezialübung code opens in the builder", await dash.is_visible("#neuroBuilder") and await dash.locator("#neuroList .neuro-card").count() == 2)
        await dash.set_viewport_size({"width": 390, "height": 844}); await dash.wait_for_timeout(150)
        check("dashboard: no sideways scroll at 390", await no_side_scroll(dash))
        await dash.screenshot(path=os.path.join(SHOTS, "dashboard_390_light.png"), full_page=True)
        await dash.close()
        # the saved Spezialübung code plays in the app
        SERVED["spezial-neu"] = cfg
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.fill("#moreCodeInput", "spezial-neu"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
        st = await pg.evaluate("window.__neuro()")
        check("dashboard code plays in the app as Spezialübung", st and st["ex"] == "gelenke" and st["special"] and st["p"]["stepS"] == 25, st)
        await ctx.close()

        check("no page/console errors", not errors, errors)
        await b.close()
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed: print("FAILED:", failed)
    print("ERRORS:", errors)

asyncio.run(main())
