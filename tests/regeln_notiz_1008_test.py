"""Idee 72 (Fabian 08.10.2026): "ⓘ Regeln" + "Meine Notiz" in every exercise
with rules - ready screen, player bar (pauses the run, "Weiter" continues),
pause sheet, Kombi overview; notes per exercise, in presets, in Kombi blocks;
"Notiz von deinem Trainer" from a code block. Run from tests/ with a dev
server (FWMC_PORT, default 8845)."""
import asyncio, json, os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded','1');"
        "localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false})); }")
SHOTS = "screenshots/paket_d"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

NO_SIDEWAYS = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"

async def open_ex(pg, ex, area="visual"):
    await pg.goto(f"{BASE}?bereich={area}"); await pg.wait_for_timeout(500)
    await pg.evaluate(f"() => document.querySelector('.excard[data-exercise=\"{ex}\"]').click()")
    await pg.wait_for_timeout(250)

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # ---- ready screen: rules generated from the settings ----
        await open_ex(pg, "8-vrw")
        check("ready: ⓘ Regeln visible", await pg.is_visible('#ready .regeln-btn'))
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(250)
        txt = await pg.inner_text("#regelnList")
        check("8 Pfeile Rot/Grün: green/red lines", "Grüner Pfeil: in Pfeilrichtung." in txt and "Roter Pfeil: Gegenrichtung." in txt, txt)
        check("ready: button reads Fertig", (await pg.inner_text("#regelnDoneBtn")).strip() == "Fertig")
        check("no trainer box standalone", not await pg.is_visible("#regelnTrainerBox"))
        await pg.fill("#regelnNoteInput", "Rot heißt: zurück")
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(200)
        check("sheet closes", await pg.is_hidden("#regelnSheet"))
        prev = await pg.inner_text('#ready [data-regeln-preview="@vt"]')
        check("note preview under the button", "Meine Notiz: Rot heißt: zurück" in prev, prev)
        # max length
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(150)
        await pg.fill("#regelnNoteInput", "x" * 400)
        check("note capped at 300", len(await pg.input_value("#regelnNoteInput")) == 300)
        await pg.fill("#regelnNoteInput", "Rot heißt: zurück")
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
        check("Escape closes", await pg.is_hidden("#regelnSheet"))

        # persistence across reload
        await open_ex(pg, "8-vrw")
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(150)
        check("note survives reload", await pg.input_value("#regelnNoteInput") == "Rot heißt: zurück")
        await pg.click("#regelnDoneBtn")
        # per exercise: another exercise has its own (empty) note
        await open_ex(pg, "stroop-classic")
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(150)
        check("Stroop: own rules", "Schriftfarbe" in await pg.inner_text("#regelnList"))
        check("Stroop: own empty note", await pg.input_value("#regelnNoteInput") == "")
        await pg.click("#regelnDoneBtn")

        # every VT catalog exercise has rules lines
        vt = await pg.evaluate("() => [...document.querySelectorAll('#home .excard')].map(c => [c.dataset.exercise, window.__regeln.vtLines(c.dataset.exercise).length])")
        check("every VT exercise has rule lines", all(n > 0 for _, n in vt), vt)

        # Farbfelder rules follow the settings (Regeln Stufe 2 -> two symbols)
        await open_ex(pg, "farbfelder")
        await pg.click('[data-ff-mode="regeln"]'); await pg.click('[data-ff-level="2"]'); await pg.wait_for_timeout(80)
        lines = await pg.evaluate("() => window.__regeln.lines('@vt')")
        check("Farbfelder Regeln: mode + 2 symbol lines", any("Regeln" in l for l in lines) and any(l.startswith("Viereck") for l in lines) and any(l.startswith("Dreieck") for l in lines) and not any(l.startswith("Strich") for l in lines), lines)
        await pg.click('[data-ff-mode="leuchten"]')

        # ---- during the run: ⓘ pauses, Weiter continues ----
        await open_ex(pg, "8-vrw")
        await pg.click("#startBtn"); await pg.wait_for_timeout(1500)
        bar_btn = '[data-regeln-bar="@vt"]'
        check("run: ⓘ in the player bar", await pg.is_visible(bar_btn))
        box = await pg.locator(bar_btn).bounding_box()
        check("run: ⓘ is at least 44 px", box and box["width"] >= 44 and box["height"] >= 44, box)
        await pg.click(bar_btn); await pg.wait_for_timeout(300)
        check("run: sheet open", await pg.is_visible("#regelnSheet"))
        check("run: exercise paused", await pg.is_visible("#periphPauseOverlay"))
        check("run: button reads Weiter", (await pg.inner_text("#regelnDoneBtn")).strip() == "Weiter")
        check("run: note of the exercise", await pg.input_value("#regelnNoteInput") == "Rot heißt: zurück")
        await pg.screenshot(path=f"{SHOTS}/regeln_run_390_light.png")
        t1 = await pg.inner_text("#timeEl")
        await pg.wait_for_timeout(1200)
        t2 = await pg.inner_text("#timeEl")
        check("run: clock stands while the sheet is open", t1 == t2, (t1, t2))
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(300)
        check("Weiter: sheet closed and run continues", await pg.is_hidden("#regelnSheet") and await pg.is_hidden("#periphPauseOverlay"))
        await pg.wait_for_timeout(1300)
        t3 = await pg.inner_text("#timeEl")
        check("Weiter: clock runs again", t3 != t2, (t2, t3))
        # pause sheet button
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(250)
        check("pause sheet: Regeln und Notiz", await pg.is_visible("#periphPauseOverlay .regeln-pause-btn"))
        await pg.click("#periphPauseOverlay .regeln-pause-btn"); await pg.wait_for_timeout(200)
        check("pause sheet: opens in pause mode", (await pg.evaluate("() => window.__regeln.ctx().mode")) == "pause")
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(200)
        check("pause sheet: still paused after closing", await pg.is_visible("#periphPauseOverlay"))
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(200)
        # hint/bar: the ⓘ must not wrap the bar at 360
        await pg.set_viewport_size({"width": 360, "height": 740}); await pg.wait_for_timeout(300)
        rows = await pg.evaluate("() => { const tops = [...document.querySelectorAll('#playerBar > *')].filter(e => e.offsetParent).map(e => Math.round(e.getBoundingClientRect().top)); return new Set(tops).size; }")
        check("player bar stays one row at 360 px", rows == 1, rows)
        await pg.set_viewport_size({"width": 390, "height": 844})
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- presets carry the note ----
        await open_ex(pg, "8-vrw")
        await pg.click("#vtSaveBtn"); await pg.fill("#vtSaveNameInput", "Mit Notiz"); await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(200)
        saved = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1')).find(e => e.name === 'Mit Notiz')")
        check("preset stores the note", saved and saved.get("note") == "Rot heißt: zurück", saved and saved.get("note"))
        await pg.click('#ready .regeln-btn'); await pg.fill("#regelnNoteInput", "anders"); await pg.click("#regelnDoneBtn")
        await pg.click('#vtSavedList button:has-text("Mit Notiz")'); await pg.wait_for_timeout(400)
        check("loading the preset brings its note back", await pg.evaluate("() => window.__regeln.note('@vt')") == "Rot heißt: zurück")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Kombi: block note, standalone untouched, ⓘ per block ----
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("8 Pfeile · Rot/Grün")'); await pg.wait_for_timeout(250)
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(150)
        check("Kombi capture: note help names the Baustein", "Baustein" in await pg.inner_text("#regelnNoteHelp"))
        await pg.fill("#regelnNoteInput", "Baustein-Notiz"); await pg.click("#regelnDoneBtn")
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        st = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).exNotes['8-vrw']")
        check("Kombi: standalone note unchanged", st == "anders" or st == "Rot heißt: zurück", st)
        check("Kombi overview: ⓘ per Baustein", await pg.locator("#comboBlockList .combo-block-info").count() == 1)
        await pg.click("#comboBlockList .combo-block-info"); await pg.wait_for_timeout(200)
        check("Kombi ⓘ: block rules + block note", "Grüner Pfeil" in await pg.inner_text("#regelnList") and await pg.input_value("#regelnNoteInput") == "Baustein-Notiz")
        await pg.screenshot(path=f"{SHOTS}/regeln_kombi_390_light.png")
        await pg.fill("#regelnNoteInput", "Baustein neu"); await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(150)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(1200)
        await pg.click('[data-regeln-bar="@vt"]'); await pg.wait_for_timeout(250)
        check("Kombi run: ⓘ shows the block note", await pg.input_value("#regelnNoteInput") == "Baustein neu")
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(200)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- trainer note from a code block ----
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => window.__regeln.startCombo({ name: 'Trainer', blocks: [{ domain: 'visual', exercise: '4-straight', duration: 30, stimulusS: 1.5, intervalMin: 2, intervalMax: 3, trainerNote: 'Knie leicht gebeugt', zus: { ids: ['prellen'] } }] }, 'abc123')""")
        await pg.wait_for_timeout(1500)
        await pg.click('[data-regeln-bar="@vt"]'); await pg.wait_for_timeout(250)
        check("code block: Notiz von deinem Trainer", await pg.is_visible("#regelnTrainerBox") and "Knie leicht gebeugt" in await pg.inner_text("#regelnTrainerText"))
        zl = await pg.inner_text("#regelnZusList")
        check("code block: Zusatz marked Von deinem Trainer", "Prellen" in zl and "Von deinem Trainer" in zl, zl)
        await pg.screenshot(path=f"{SHOTS}/regeln_trainer_390_light.png")
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(200)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- NAT: Blitz-Raster ready + store ----
        await pg.goto(f"{BASE}?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.evaluate("() => { const t = document.querySelector('.nat-tile[data-nat=\"blitz\"], [data-nat-tile=\"blitz\"]'); if (t) t.click(); }")
        await pg.wait_for_timeout(300)
        if not await pg.is_visible("#blitzReady"):
            await pg.evaluate("() => { document.querySelectorAll('.screen').forEach(s => s.hidden = true); document.getElementById('blitzReady').hidden = false; }")
            await pg.wait_for_timeout(200)
        check("NAT Blitz-Raster: ⓘ on the ready screen", await pg.is_visible('#blitzReady .regeln-btn'))
        await pg.click('#blitzReady .regeln-btn'); await pg.wait_for_timeout(200)
        check("NAT: rules from the description", "Felder" in await pg.inner_text("#regelnList"))
        await pg.fill("#regelnNoteInput", "Blitz merken"); await pg.click("#regelnDoneBtn")
        stored = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-notes-v1') || '{}')")
        check("NAT note in fwmc-notes-v1", stored.get("nat:blitz") == "Blitz merken", stored)
        check("NAT player bars have ⓘ", await pg.evaluate("() => ['rememberPlayerBar','blitzPlayerBar','flashPlayerBar','motPlayerBar','balancePlayerBar'].every(id => document.querySelector('#' + id + ' .regeln-bar-btn'))"))

        # ---- layout: 390 / 1024, light / dark, no sideways scroll ----
        for w, h in ((390, 844), (1024, 768)):
            for scheme in ("light", "dark"):
                await pg.emulate_media(color_scheme=scheme)
                await pg.set_viewport_size({"width": w, "height": h})
                await open_ex(pg, "8-vrw")
                ok1 = await pg.evaluate(NO_SIDEWAYS)
                await pg.screenshot(path=f"{SHOTS}/regeln_ready_{w}_{scheme}.png")
                await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(300)
                ok2 = await pg.evaluate(NO_SIDEWAYS)
                await pg.screenshot(path=f"{SHOTS}/regeln_sheet_{w}_{scheme}.png")
                await pg.click("#regelnDoneBtn")
                check(f"no sideways scroll {w} {scheme}", ok1 and ok2)
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
