"""Idee 70 (Fabian 08.10.2026): Richtungskreuz - four directions around the
client (vorne/hinten/links/rechts) with colours, numbers or both; Farbregel
(normal / Gegenrichtung / stehen bleiben / Kreisrichtung wechseln, default
Blau = Gegenrichtung); cross overview at the start; Abfolge merken; ready
screen, presets, Kombi, Cardio guest, Hilfsmittel (optional), history.
Run from tests/ with a dev server (FWMC_PORT, default 8845)."""
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
PREFS = "() => JSON.parse(localStorage.getItem('fwmc-webapp-v3'))"

async def open_rk(pg):
    await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
    await pg.evaluate("() => document.querySelector('.excard[data-exercise=\"richtungskreuz\"]').click()")
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

        # ---- pure rule ----
        r = await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(400)
        t = await pg.evaluate("""() => [
          window.__rk.target('vorne', 'rot', {blau:'gegen'}, true),
          window.__rk.target('hinten', 'blau', {blau:'gegen'}, true),
          window.__rk.target('links', 'blau', {blau:'gegen'}, true),
          window.__rk.target('rechts', 'gelb', {gelb:'stehen'}, true),
          window.__rk.target('rechts', 'gruen', {gruen:'kreis'}, true),
          window.__rk.target('hinten', 'blau', {blau:'gegen'}, false)]""")
        check("rule: normal colour = shown direction", t[0]["target"] == "vorne" and t[0]["action"] == "schritt")
        check("rule: Blau Gegenrichtung (hinten -> vorne, links -> rechts)", t[1]["target"] == "vorne" and t[2]["target"] == "rechts")
        check("rule: stehen bleiben / Kreisrichtung = no step", t[3]["action"] == "stehen" and t[4]["action"] == "kreis" and t[3]["target"] is None)
        check("rule off: always the shown direction", t[5]["target"] == "hinten")

        # ---- ready screen, defaults ----
        await open_rk(pg)
        check("card opens the ready screen", "Richtungskreuz" in await pg.inner_text("#readyTitle") and await pg.is_visible("#rkSettings"))
        check("start button reads Training starten", (await pg.inner_text("#startBtn")).strip() == "Training starten")
        st = await pg.evaluate(PREFS)
        check("default numbers vorne 4, hinten 1, links 2, rechts 3", st["rkNums"] == {"vorne": 4, "hinten": 1, "links": 2, "rechts": 3}, st["rkNums"])
        check("default colours: four classic colours", sorted(st["rkColors"].values()) == ["blau", "gelb", "gruen", "rot"], st["rkColors"])
        check("Hilfsmittel marked optional", "(optional)" in await pg.text_content("#hilfsmittelKicker") and "Es geht auch ohne" in await pg.inner_text("#hilfsmittelText"))
        check("no background picker, no fixpoint (sign is the stimulus)", await pg.is_hidden("#bgGroup") and await pg.is_hidden("#periphFixGroup"))
        check("Zusatzaufgabe offered (VT canvas)", await pg.is_visible("#addonGroup"))
        await pg.screenshot(path=f"{SHOTS}/rk_ready_390_light.png", full_page=True)
        # colour swap: give vorne Blau -> hinten gets Rot
        await pg.click('[data-rk-dir="vorne"]'); await pg.click('#rkColorPicker [data-color="blau"]'); await pg.wait_for_timeout(100)
        st = await pg.evaluate(PREFS)
        check("colour already used swaps places", st["rkColors"]["vorne"] == "blau" and st["rkColors"]["hinten"] == "rot", st["rkColors"])
        # number swap: Zahlen on, links = 4 -> vorne gets 2
        await pg.click('[data-rk-signs="beide"]'); await pg.click('[data-rk-dir="links"]'); await pg.click('#rkNumRow [data-rk-num="4"]'); await pg.wait_for_timeout(100)
        st = await pg.evaluate(PREFS)
        check("number already used swaps places", st["rkNums"]["links"] == 4 and st["rkNums"]["vorne"] == 2, st["rkNums"])
        await pg.click('#rkNumRow [data-rk-num="9"]')
        st = await pg.evaluate(PREFS)
        check("numbers up to 9", st["rkNums"]["links"] == 9)
        # Farbregel: hidden with Zahlen, default Blau = Gegenrichtung when switched on
        await pg.click('[data-rk-signs="zahlen"]'); await pg.wait_for_timeout(80)
        check("Zahlen: no Farbregel, no colour picker", await pg.is_hidden("#rkRuleGroup") and await pg.is_hidden("#rkColorPicker"))
        await pg.click('[data-rk-signs="farben"]'); await pg.wait_for_timeout(80)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); }")
        await pg.click('[data-rk-rule="1"]'); await pg.wait_for_timeout(80)
        st = await pg.evaluate(PREFS)
        check("Farbregel on: Blau = Gegenrichtung by default", st["rkRuleOn"] and st["rkRules"].get("blau") == "gegen", st["rkRules"])
        check("Farbregel rows per colour", await pg.locator("#rkRuleRows select").count() == 4)
        await pg.select_option('#rkRuleRows [data-rk-rulecol="gelb"]', "stehen"); await pg.wait_for_timeout(80)
        st = await pg.evaluate(PREFS)
        check("meaning per colour is editable", st["rkRules"].get("gelb") == "stehen")
        await pg.screenshot(path=f"{SHOTS}/rk_ready_farbregel_390_light.png", full_page=True)
        # Gear changes help, Abfolge shows start length and hides the Farbregel
        await pg.click('[data-rk-gear="keine"]'); await pg.wait_for_timeout(60)
        check("Ohne Hilfsmittel: Richtungen merken", "Merk dir" in await pg.inner_text("#rkGearHelp"))
        await pg.click('[data-rk-mode="abfolge"]'); await pg.wait_for_timeout(60)
        check("Abfolge: start length shown, Farbregel hidden", await pg.is_visible("#rkSeqGroup") and await pg.is_hidden("#rkRuleGroup"))
        await pg.click('[data-rk-mode="zeigen"]')
        # persistence
        await open_rk(pg)
        st = await pg.evaluate(PREFS)
        check("settings survive reload", st["rkColors"]["vorne"] == "blau" and st["rkRuleOn"] and st["rkGear"] == "keine" and "active" in (await pg.get_attribute('[data-rk-gear="keine"]', "class")))

        # ---- schedule ----
        sch = await pg.evaluate("() => window.__rk.build({ duration: 30, rkMode: 'zeigen', rkSigns: 'beide', rkRuleOn: true, rkRules: { blau: 'gegen' } })")
        rk = [f for f in sch if f["kind"] == "rk"]
        check("starts with the cross overview", rk[0]["payload"]["phase"] == "orient")
        shows = [f["payload"] for f in rk if f["payload"]["phase"] == "show"]
        check("several signs", len(shows) >= 4, len(shows))
        check("never the same direction twice in a row", all(a["dir"] != b2["dir"] for a, b2 in zip(shows, shows[1:])))
        check("Farbe + Zahl + Regel: number names the direction", all(s["num"] == st["rkNums"][s["dir"]] for s in shows))
        check("rule applied: blue sign = opposite", all((s["target"] == {"vorne": "hinten", "hinten": "vorne", "links": "rechts", "rechts": "links"}[s["dir"]]) for s in shows if s["colorKey"] == "blau") )
        seq = await pg.evaluate("() => window.__rk.build({ duration: 60, rkMode: 'abfolge', rkSeqStart: 3 })")
        phases = [f["payload"].get("phase") for f in seq if f["kind"] == "rk"]
        check("Abfolge: intro/show/recall", "intro" in phases and "recall" in phases)
        lens = [f["payload"]["seqLen"] for f in seq if f["kind"] == "rk" and f["payload"].get("phase") == "intro"]
        check("Abfolge: starts at 3 and grows", lens[0] == 3 and (len(lens) < 2 or lens[1] == 4), lens)

        # ---- run ----
        await pg.click('[data-dur="60"]')
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("timer starts at the chosen 1:00", (await pg.inner_text("#timeEl")).strip() == "1:00")
        await pg.wait_for_timeout(1200)
        d = await pg.evaluate("() => window.__rkLastDrawn")
        check("overview drawn first", d and d["phase"] == "orient", d)
        await pg.screenshot(path=f"{SHOTS}/rk_run_overview_390_light.png")
        geom = await pg.evaluate("() => window.__ffLastGeom")
        check("cross below the player bar", geom and geom["top"] >= geom["barBottom"], geom)
        for _ in range(40):
            d = await pg.evaluate("() => window.__rkLastDrawn")
            if d and d["phase"] == "show": break
            await pg.wait_for_timeout(200)
        check("a sign is drawn", d and d["phase"] == "show", d)
        await pg.screenshot(path=f"{SHOTS}/rk_run_sign_390_light.png")
        await pg.click('[data-regeln-bar="@vt"]'); await pg.wait_for_timeout(250)
        lines = await pg.inner_text("#regelnList")
        check("Regeln: mapping + Farbregel lines", "Blau: vorne." in lines and "Blau: Schritt in die Gegenrichtung." in lines and "Gelb: stehen bleiben" in lines, lines)
        await pg.screenshot(path=f"{SHOTS}/rk_regeln_390_light.png")
        await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(200)
        # tempo change in the pause sheet: no second overview
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => { const s = document.getElementById('vtPauseStimulusSlider'); s.value = 2; s.dispatchEvent(new Event('input')); s.dispatchEvent(new Event('change')); }")
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(1500)
        d = await pg.evaluate("() => window.__rkLastDrawn")
        check("after a live tempo change no second overview", d and d["phase"] != "orient", d)
        await pg.evaluate("() => { const s = window.__fwmcTestSession; }")
        # finish via Übung beenden is not here: end via the clock (short duration)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # history note
        await open_rk(pg)
        await pg.evaluate("() => { document.getElementById('durationSlider').value = 15; document.getElementById('durationSlider').dispatchEvent(new Event('input')); }")
        await pg.click("#startBtn"); await pg.wait_for_timeout(16500)
        hist = await pg.evaluate("() => { for (const k of Object.keys(localStorage)) { if (/hist/i.test(k)) { try { const v = JSON.parse(localStorage.getItem(k)); if (Array.isArray(v) && v.length) return v; } catch (e) {} } } return []; }")
        last = hist[-1] if hist else {}
        check("history entry with mode + signs", "Richtungskreuz" in json.dumps(last, ensure_ascii=False) and "Zeichen zeigen" in json.dumps(last, ensure_ascii=False), json.dumps(last, ensure_ascii=False)[:200])
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(400)

        # ---- preset ----
        await open_rk(pg)
        await pg.click("#vtSaveBtn"); await pg.fill("#vtSaveNameInput", "Kreuz blau"); await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(200)
        saved = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1')).find(e => e.name === 'Kreuz blau')")
        check("preset carries rk", saved and saved["rk"]["rkColors"]["vorne"] == "blau" and saved["rk"]["rkRuleOn"])
        check("preset meta names mode + signs", "Zeichen zeigen" in await pg.inner_text("#vtSavedList"))

        # ---- Kombi: own settings, standalone untouched, playback ----
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(500)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Richtungskreuz")'); await pg.wait_for_timeout(250)
        check("Kombi: capture opens the ready screen", "Baustein: Richtungskreuz" in await pg.inner_text("#readyTitle") and (await pg.inner_text("#startBtn")).strip() == "Baustein übernehmen")
        await pg.click('[data-rk-mode="abfolge"]'); await pg.click('[data-rk-signs="zahlen"]'); await pg.wait_for_timeout(80)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("Kombi: block row names the mode", "Richtungskreuz · Abfolge merken" in await pg.inner_text("#comboBlockList"))
        st = await pg.evaluate(PREFS)
        check("Kombi: standalone settings unchanged", st["rkMode"] == "zeigen" and st["rkSigns"] == "farben", (st["rkMode"], st["rkSigns"]))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: re-edit shows the block's settings", "active" in await pg.get_attribute('[data-rk-signs="zahlen"]', "class") and "active" in await pg.get_attribute('[data-rk-mode="abfolge"]', "class"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(5000)
        d = await pg.evaluate("() => window.__rkLastDrawn")
        check("Kombi: block plays", await pg.is_visible("#player") and d is not None)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Wochenplan + Hilfsmittel page ----
        await pg.goto(f"{BASE}?bereich=visual"); await pg.wait_for_timeout(400)
        chips = await pg.evaluate("() => window.__gear.exercises('mat').map(x => x.title)")
        check("Hilfsmittel page: Richtungskreuz (optional)", "Richtungskreuz (optional)" in chips, chips)

        # ---- Cardio guest ----
        await pg.goto(f"{BASE}?bereich=cardio"); await pg.wait_for_timeout(500)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        check("Cardio: Richtungskreuz in the pool", await pg.locator('#cardioAddonPoolGrid [data-pool="richtungskreuz"]').count() == 1)
        await pg.check('#cardioAddonPoolGrid [data-pool="richtungskreuz"]'); await pg.wait_for_timeout(150)
        panel = await pg.inner_text("#cardioAddonPerType")
        check("Cardio: own panel (Modus, Zeichen, Farbregel)", "Richtungskreuz" in panel and "Abfolge merken" in panel and "Farbregel" in panel)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(500)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        check("picker offers 22 types", await pg.locator("#cardioAddonPickerTypeRow .choice").count() == 22)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Richtungskreuz")'); await pg.wait_for_timeout(120)
        await pg.evaluate("() => { window.__rkLastDrawn = null; }")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(4500)
        check("Cardio: guest runs Richtungskreuz", await pg.is_visible("#player") and await pg.evaluate("() => !!window.__rkLastDrawn"))
        check("Cardio guest: no ⓘ in the bar", await pg.evaluate("() => document.querySelector('[data-regeln-bar=\"@vt\"]').hidden"))
        await pg.screenshot(path=f"{SHOTS}/rk_cardio_guest_390_light.png")

        # ---- layout ----
        for w, h in ((390, 844), (1024, 768)):
            for scheme in ("light", "dark"):
                await pg.emulate_media(color_scheme=scheme)
                await pg.set_viewport_size({"width": w, "height": h})
                await open_rk(pg)
                ok = await pg.evaluate(NO_SIDEWAYS)
                await pg.screenshot(path=f"{SHOTS}/rk_ready_{w}_{scheme}.png", full_page=True)
                check(f"no sideways scroll {w} {scheme}", ok)
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
