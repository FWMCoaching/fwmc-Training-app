"""Idee 71 (Fabian 08.10.2026): "Zusatz für oben" for every exercise done by
stepping. One row in the Feineinstellungen ("Zusatz für oben: keiner" +
"+ Zusatz"), a bottom sheet with cards (any number, hint from the 2nd on),
chips with ✕, instructions on the ready screen and in the Regeln sheet, the
signal Zusatz (tone + ↻ at random intervals, only running time), presets,
Kombi blocks. Run from tests/ with a dev server (FWMC_PORT, default 8845)."""
import asyncio, json, os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded','1');"
        "localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false})); }")
SHOTS = "screenshots/paket_d"
WARN = "Prüfe, ob sich deine Zusätze gegenseitig ausschließen oder aufheben."

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

NO_SIDEWAYS = "() => document.documentElement.scrollWidth <= window.innerWidth + 1"

async def open_ex(pg, ex):
    await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
    await pg.evaluate(f"() => document.querySelector('.excard[data-exercise=\"{ex}\"]').click()")
    await pg.wait_for_timeout(250)

async def open_fine(pg, sel="#advanced"):
    if await pg.get_attribute(sel, "open") is None:
        await pg.click(f"{sel} > summary"); await pg.wait_for_timeout(150)

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

        # which exercises get the row
        await open_ex(pg, "4-straight")
        await open_fine(pg)
        check("4 Pfeile: one row 'Zusatz für oben: keiner'", await pg.is_visible("#zusGroup") and "keiner" in await pg.inner_text("#zusGroup") and "Zusatz für oben" in await pg.inner_text("#zusGroup"))
        check("only one row before choosing (no instructions yet)", await pg.is_hidden("#zusNote") and await pg.is_hidden("#zusRowWarn"))
        for ex, want in (("stroop-classic", False), ("cone-number", False), ("farbfelder", True), ("richtungskreuz", True), ("8-vrw", True)):
            await open_ex(pg, ex)
            check(f"{ex}: row {'shown' if want else 'hidden'}", (not await pg.evaluate("() => document.getElementById('zusGroup').hidden")) == want)
        await open_ex(pg, "cone-path")
        await open_fine(pg, "#lwAdvanced")
        check("Laufweg: row in its own Feineinstellungen", await pg.is_visible("#lwAdvanced #zusGroup"))

        # ---- sheet ----
        await open_ex(pg, "4-straight")
        await open_fine(pg)
        await pg.click("#zusAddBtn"); await pg.wait_for_timeout(300)
        check("sheet opens with 4 cards", await pg.is_visible("#zusatzSheet") and await pg.locator("#zusCardList .zus-card").count() == 4)
        check("sheet has the grab bar", await pg.locator("#zusatzSheet .sheet-grab").count() == 1)
        check("no hint with none chosen", await pg.is_hidden("#zusSheetWarn"))
        await pg.click('[data-zus-card="ball-kreisen"]'); await pg.wait_for_timeout(100)
        check("one chosen: still no hint", await pg.is_hidden("#zusSheetWarn"))
        await pg.click('[data-zus-card="kreis-signal"]'); await pg.wait_for_timeout(100)
        check("2nd chosen: hint", await pg.is_visible("#zusSheetWarn") and WARN in await pg.inner_text("#zusSheetWarn"))
        check("signal: interval sliders", await pg.is_visible("#zusSigGroup"))
        # boundary: min above max pulls max along
        await pg.evaluate("() => { const s = document.getElementById('zusSigMinSlider'); s.value = 40; s.dispatchEvent(new Event('input')); }")
        await pg.evaluate("() => { const s = document.getElementById('zusSigMaxSlider'); s.value = 20; s.dispatchEvent(new Event('input')); }")
        z = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).zusOben['4-straight']")
        check("min/max stay ordered", z["sigMin"] <= z["sigMax"] and z["sigMax"] == 20, z)
        await pg.evaluate("() => { const a = document.getElementById('zusSigMinSlider'); a.value = 3; a.dispatchEvent(new Event('input')); const b = document.getElementById('zusSigMaxSlider'); b.value = 4; b.dispatchEvent(new Event('input')); }")
        await pg.screenshot(path=f"{SHOTS}/zusatz_sheet_390_light.png")
        await pg.click("#zusatzDoneBtn"); await pg.wait_for_timeout(200)
        chips = await pg.inner_text("#zusChips")
        check("chips in the row", "Ball um den Körper kreisen" in chips and "Kreisrichtung wechseln auf Signal" in chips, chips)
        check("row hint from the 2nd Zusatz", await pg.is_visible("#zusRowWarn"))
        note = await pg.inner_text("#zusNote")
        check("ready screen shows the instructions", "Vorne und hinten gibst du ihn" in note and "Doppelton" in note, note)
        chip_x = await pg.locator(".zus-chip-x").first.bounding_box()
        check("chip ✕ is 44 px", chip_x["width"] >= 44 and chip_x["height"] >= 44, chip_x)
        await pg.screenshot(path=f"{SHOTS}/zusatz_row_390_light.png", full_page=True)

        # persistence + per exercise
        await open_ex(pg, "4-straight")
        check("chosen Zusätze survive reload", (await pg.locator("#zusChips .zus-chip").count()) == 2)
        await open_ex(pg, "4-diag")
        check("other exercise: own (none)", "keiner" in await pg.text_content("#zusChips"))

        # Regeln sheet lists them
        await open_ex(pg, "4-straight")
        await pg.click('#ready .regeln-btn'); await pg.wait_for_timeout(200)
        check("Regeln sheet lists the Zusätze", "Ball um den Körper kreisen" in await pg.inner_text("#regelnZusList"))
        await pg.click("#regelnDoneBtn")

        # ---- signal during the run (3-4 s) ----
        await pg.click("#startBtn"); await pg.wait_for_timeout(500)
        st = await pg.evaluate("() => window.__zusSig.state()")
        check("signal timer runs", st["running"], st)
        await pg.wait_for_timeout(8500)
        st = await pg.evaluate("() => window.__zusSig.state()")
        check("signal fired after 3-4 s (after the 3-2-1)", st["count"] >= 1, st)
        await pg.evaluate("() => window.__zusSig.fire()"); await pg.wait_for_timeout(100)
        check("↻ mark visible", await pg.is_visible("#zusSigCue"))
        await pg.screenshot(path=f"{SHOTS}/zusatz_signal_run_390_light.png")
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(200)
        c1 = (await pg.evaluate("() => window.__zusSig.state()"))["count"]
        await pg.wait_for_timeout(5000)
        c2 = (await pg.evaluate("() => window.__zusSig.state()"))["count"]
        check("no signal while paused", c1 == c2, (c1, c2))
        await pg.click("#periphResumeBtn")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("signal stops when leaving", not (await pg.evaluate("() => window.__zusSig.state()"))["running"])
        # Without the signal Zusatz no timer
        await open_ex(pg, "4-diag")
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        check("no signal Zusatz: no timer", not (await pg.evaluate("() => window.__zusSig.state()"))["running"])
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # remove a chip
        await open_ex(pg, "4-straight")
        await open_fine(pg)
        await pg.click('[data-zus-remove="kreis-signal"]'); await pg.wait_for_timeout(150)
        check("✕ removes the chip, hint gone", (await pg.locator("#zusChips .zus-chip").count()) == 1 and await pg.is_hidden("#zusRowWarn"))

        # ---- presets carry them ----
        await pg.click("#vtSaveBtn"); await pg.fill("#vtSaveNameInput", "Mit Ball"); await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(200)
        saved = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1')).find(e => e.name === 'Mit Ball')")
        check("preset stores zus", saved and saved["zus"]["ids"] == ["ball-kreisen"], saved and saved.get("zus"))

        # ---- Kombi block: own Zusätze, standalone untouched ----
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("4 Pfeile · gerade")'); await pg.wait_for_timeout(250)
        await open_fine(pg)
        await pg.click("#zusAddBtn"); await pg.wait_for_timeout(200)
        await pg.click('[data-zus-card="prellen"]'); await pg.click("#zusatzDoneBtn")
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        own = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).zusOben['4-straight'].ids")
        check("Kombi: standalone Zusätze unchanged", own == ["ball-kreisen"], own)
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        chips = await pg.inner_text("#zusChips")
        check("Kombi: block re-edit shows its own Zusätze", "Prellen" in chips and "Ball um" in chips, chips)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(1200)
        await pg.click('[data-regeln-bar="@vt"]'); await pg.wait_for_timeout(200)
        zl = await pg.inner_text("#regelnZusList")
        check("Kombi run: the block's Zusätze in Regeln", "Prellen" in zl, zl)
        await pg.click("#regelnDoneBtn")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- layout ----
        for w, h in ((390, 844), (1024, 768)):
            for scheme in ("light", "dark"):
                await pg.emulate_media(color_scheme=scheme)
                await pg.set_viewport_size({"width": w, "height": h})
                await open_ex(pg, "4-straight")
                await open_fine(pg)
                await pg.locator("#zusGroup").scroll_into_view_if_needed()
                ok1 = await pg.evaluate(NO_SIDEWAYS)
                await pg.screenshot(path=f"{SHOTS}/zusatz_row_{w}_{scheme}.png")
                await pg.click("#zusAddBtn"); await pg.wait_for_timeout(300)
                ok2 = await pg.evaluate(NO_SIDEWAYS)
                await pg.screenshot(path=f"{SHOTS}/zusatz_sheet_{w}_{scheme}.png")
                await pg.click("#zusatzDoneBtn")
                check(f"no sideways scroll {w} {scheme}", ok1 and ok2)
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
