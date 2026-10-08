"""Farbfelder (Fabian 07.10.2026): 2x2 colour grid like the client's floor mat,
modes Leuchten / Regeln (Stufe 1-4) / Das leere Feld / Abfolge merken, plus
Fuß-Vorgabe, Hände, Hilfsmittel note, Kombi and Cardio guest.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/farbfelder"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

# Field colours the canvas shows at the four field centres (CSS px -> canvas px).
PIXELS_JS = """() => {
  const g = window.__ffLastGeom; if (!g) return null;
  const c = document.getElementById('stage'); const r = c.getBoundingClientRect();
  const k = c.width / r.width; const ctx = c.getContext('2d');
  const w = (g.right - g.left) / 2, h = (g.bottom - g.top) / 2;
  const out = [];
  for (let i = 0; i < 4; i++) {
    // sample near the field's corner, away from the centre mark/symbol
    const x = g.left + (i % 2) * w + w * 0.2, y = g.top + (i >> 1) * h + h * 0.2;
    const d = ctx.getImageData(Math.round((x - r.left) * k), Math.round((y - r.top) * k), 1, 1).data;
    out.push([d[0], d[1], d[2]]);
  }
  return { px: out, geom: g };
}"""

async def open_ff(pg):
    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- ready screen ----
        check("card on the VT home", await pg.is_visible('.excard[data-exercise="farbfelder"]'))
        await open_ff(pg)
        check("ready screen opens", await pg.is_visible("#ready") and (await pg.inner_text("#readyTitle")).strip() == "Farbfelder")
        check("Hilfsmittel note visible", await pg.is_visible("#hilfsmittelNote") and "Farbmatte mit 4 Feldern" in await pg.inner_text("#hilfsmittelNote"))
        check("Hilfsmittel link hidden while empty", not await pg.is_visible("#hilfsmittelLink"))
        check("Farbfelder settings visible", await pg.is_visible("#ffSettings"))
        check("no centre-dot settings", not await pg.is_visible("#periphFixGroup"))
        check("no background picker (colours are the stimulus)", not await pg.is_visible("#bgGroup"))
        check("start button reads Training starten", (await pg.inner_text("#startBtn")).strip() == "Training starten")
        check("Zusatzaufgabe offered", await pg.is_visible("#addonGroup"))
        # other exercises don't show the Farbfelder block or the note
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        check("sibling has no Farbfelder block/note", not await pg.is_visible("#ffSettings") and not await pg.is_visible("#hilfsmittelNote"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)

        # ---- rule logic (pure function) ----
        table = await pg.evaluate("() => ['viereck','dreieck','strich','herz'].map(s => [0,1,2,3].map(f => window.__ff.target(s, f)))")
        check("Viereck = same field", table[0] == [0, 1, 2, 3], table[0])
        check("Dreieck = diagonal", table[1] == [3, 2, 1, 0], table[1])
        check("Strich = neighbour in the row", table[2] == [1, 0, 3, 2], table[2])
        check("Herz = same column", table[3] == [2, 3, 0, 1], table[3])
        for lvl in (1, 2, 3, 4):
            res = await pg.evaluate("""(lvl) => { const allowed = ['viereck','dreieck','strich','herz'].slice(0, lvl);
                const fr = window.__ff.build({ffMode:'regeln', ffLevel:lvl, duration:300}).filter(f => f.kind === 'farbfelder');
                return { n: fr.length, syms: [...new Set(fr.map(f => f.payload.symbol))].sort(),
                  ok: fr.every(f => allowed.includes(f.payload.symbol) && f.payload.target === window.__ff.target(f.payload.symbol, f.payload.at)) }; }""", lvl)
            check(f"Stufe {lvl}: only its symbols, target follows the rule", res["ok"] and res["n"] > 5 and len(res["syms"]) == lvl, res)

        # ---- empty field: exactly one ----
        res = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'leer', duration:300}).filter(f => f.kind === 'farbfelder');
            return { n: fr.length, ok: fr.every(f => f.payload.marks.length === 3 && new Set(f.payload.marks).size === 3 && !f.payload.marks.includes(f.payload.target)) }; }""")
        check("Das leere Feld: always exactly one empty field", res["ok"] and res["n"] > 5, res)

        # ---- Leuchten: no field twice in a row; foot L/R alternates ----
        res = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'leuchten', ffFoot:'wechsel', duration:300}).filter(f => f.kind === 'farbfelder');
            return { norep: fr.every((f, i) => !i || f.payload.lit !== fr[i-1].payload.lit), feet: fr.slice(0, 4).map(f => f.payload.foot) }; }""")
        check("Leuchten: never the same field twice in a row", res["norep"])
        check("Fuß im Wechsel: L R L R", res["feet"] == ["L", "R", "L", "R"], res["feet"])
        res = await pg.evaluate("""() => window.__ff.build({ffMode:'leuchten', ffHands:true, ffLayout:['rot','blau','gelb','gruen'], ffHandRules:{rot:'hoch'}, duration:300})
            .filter(f => f.kind === 'farbfelder').every(f => (f.payload.lit === 0) === (f.payload.hand === 'Hände hoch'))""")
        check("Hände: only the red field carries 'Hände hoch'", res)

        # ---- Abfolge: sequence grows by one per round ----
        for start in (2, 3):
            lens = await pg.evaluate("""(s) => { const fr = window.__ff.build({ffMode:'abfolge', ffSeqStart:s, duration:240, stimulusS:1});
                const rec = fr.filter(f => f.payload && f.payload.phase === 'recall').map(f => f.payload.seqLen);
                const shows = fr.filter(f => f.payload && f.payload.phase === 'show').length;
                return { rec, shows }; }""", start)
            rec = lens["rec"]
            check(f"Abfolge from {start}: grows by one each round", rec[:3] == [start, start + 1, start + 2] and all(b2 - a == 1 or a == b2 == 12 for a, b2 in zip(rec, rec[1:])), rec)
            check(f"Abfolge from {start}: one lit step per sequence element", lens["shows"] == sum(rec), lens["shows"])
        res = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'abfolge', ffSeqStart:2, duration:200});
            const rounds = []; let cur = null;
            fr.forEach(f => { if (f.payload && f.payload.phase === 'intro') { cur = []; rounds.push(cur); } if (f.payload && f.payload.phase === 'show') cur.push(f.payload.lit); });
            return rounds.slice(0, 4); }""")
        check("Abfolge: each round repeats the previous one plus one step (Simon)", all(r2[:len(r1)] == r1 for r1, r2 in zip(res, res[1:])), res)

        # ---- arrangement + persistence ----
        await open_ff(pg)
        await pg.click('#ffLayoutGrid [data-ff-cell="0"]')
        await pg.click('#ffColorPicker .color-swatch[data-color="lila"]'); await pg.wait_for_timeout(100)
        check("field top-left now Lila", (await pg.inner_text('#ffLayoutGrid [data-ff-cell="0"]')).strip() == "Lila")
        await pg.click('#ffLayoutGrid [data-ff-cell="1"]')
        await pg.click('#ffColorPicker .color-swatch[data-color="lila"]'); await pg.wait_for_timeout(100)
        lay = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).ffLayout")
        check("picking a used colour swaps the two fields", lay == ["blau", "lila", "gelb", "gruen"], lay)
        await pg.click('[data-ff-mode="regeln"]'); await pg.click('[data-ff-level="3"]'); await pg.wait_for_timeout(80)
        check("Stufe 3 lists three rules", await pg.locator("#ffRuleList li").count() == 3)
        await pg.click('[data-ff-hands="1"]'); await pg.wait_for_timeout(80)
        check("hand rows for the 4 layout colours (chips)", await pg.locator("#ffHandRows .color-choice-line").count() == 4)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("arrangement persists across reload", [ (await pg.inner_text(f'#ffLayoutGrid [data-ff-cell="{i}"]')).strip() for i in range(4)] == ["Blau", "Lila", "Gelb", "Grün"])
        check("mode + Stufe persist across reload", "active" in (await pg.get_attribute('[data-ff-mode="regeln"]', "class")) and "active" in (await pg.get_attribute('[data-ff-level="3"]', "class")))
        # back to the default layout for the drawing checks
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.ffLayout = ['rot','blau','gelb','gruen']; s.ffHands = false; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")

        # ---- every mode starts and draws 4 colours, below the bar ----
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme)
            await pg.goto(URL); await pg.wait_for_timeout(400)
            await open_ff(pg)
            await pg.screenshot(path=f"{SHOTS}/ready_{scheme}.png", full_page=True)
            for mode in ("leuchten", "regeln", "leer", "abfolge"):
                await pg.click(f'[data-ff-mode="{mode}"]')
                if mode == "regeln": await pg.click('[data-ff-level="4"]')
                await pg.click('[data-ff-foot="wechsel"]')
                await pg.wait_for_timeout(80)
                await pg.click("#startBtn"); await pg.wait_for_timeout(1700 if mode == "abfolge" else 500)
                info = await pg.evaluate(PIXELS_JS)
                ok = info is not None
                if ok:
                    px = info["px"]; g = info["geom"]
                    distinct = len({tuple(c) for c in px}) == 4 and all(not (c[0] > 245 and c[1] > 245 and c[2] > 245) for c in px)
                    check(f"{scheme} {mode}: 4 coloured fields drawn", distinct, px)
                    check(f"{scheme} {mode}: grid below the player bar and above the caption", g["top"] >= g["barBottom"] and g["bottom"] <= g["capTop"] + 0.5, g)
                else:
                    check(f"{scheme} {mode}: drawn", False)
                await pg.screenshot(path=f"{SHOTS}/{mode}_{scheme}.png")
                await pg.click("#backBtn"); await pg.wait_for_timeout(300)
            await pg.click('[data-ff-mode="leuchten"]')
            await pg.click('[data-ff-hands="1"]'); await pg.wait_for_timeout(80)
            await pg.screenshot(path=f"{SHOTS}/ready_hands_{scheme}.png", full_page=True)
            await pg.click('[data-ff-hands="0"]'); await pg.click('[data-ff-foot="aus"]'); await pg.wait_for_timeout(80)
            await pg.click("#backToHome"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=f"{SHOTS}/home_{scheme}.png", full_page=True)
        await pg.emulate_media(color_scheme="light")

        # ---- pause sheet: tempo yes, centre dot/background no ----
        await open_ff(pg)
        await pg.click('[data-ff-mode="leuchten"]')
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        check("pause sheet: tempo shown, dot + background hidden",
              await pg.is_visible("#vtPauseTempoGroup") and not await pg.is_visible("#vtPauseFixColorGroup") and not await pg.is_visible("#vtPauseBgColorGroup"))
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(100)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # ---- Prüfer 07.10. Nr. 4: "1 Min" starts at 1:00 like Kompass-Aufbau
        # (the schedule ends at the chosen time, Abfolge merken included) ----
        for mode in ["abfolge", "regeln", "sehenhoeren", "leuchten"]:
            await pg.goto(URL); await pg.wait_for_timeout(400)
            await open_ff(pg)
            await pg.click(f'[data-ff-mode="{mode}"]'); await pg.click('[data-dur="60"]'); await pg.wait_for_timeout(80)
            await pg.click("#startBtn"); await pg.wait_for_timeout(150)
            t = await pg.inner_text("#timeEl")
            check(f"timer starts at the chosen 1:00 ({mode})", t.strip() == "1:00", t)
            await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # ---- Kombi capture: own settings, standalone untouched ----
        before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).ffMode")
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbfelder")'); await pg.wait_for_timeout(250)
        check("Kombi: capture opens the ready screen", "Baustein: Farbfelder" in await pg.inner_text("#readyTitle") and (await pg.inner_text("#startBtn")).strip() == "Baustein übernehmen")
        await pg.click('[data-ff-mode="leer"]'); await pg.wait_for_timeout(80)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("Kombi: block added", await pg.is_visible("#comboScreen") and "Farbfelder" in await pg.inner_text("#comboBlockList"))
        after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).ffMode")
        check("Kombi: standalone mode unchanged", before == after == "leuchten", (before, after))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-editable with its own mode", "active" in (await pg.get_attribute('[data-ff-mode="leer"]', "class")))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(900)
        played = await pg.evaluate("() => window.__ffLastGeom ? true : false")
        check("Kombi: block plays on the canvas", await pg.is_visible("#player") and played)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Cardio guest ----
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        check("Cardio: Farbfelder in the Zusatzaufgaben pool", await pg.locator('#cardioAddonPoolGrid [data-pool="farbfelder"]').count() == 1)
        await pg.check('#cardioAddonPoolGrid [data-pool="farbfelder"]'); await pg.wait_for_timeout(150)
        panel = await pg.inner_text("#cardioAddonPerType")
        check("Cardio: own settings panel (Modus, Fuß, Hände)", "Farbfelder" in panel and "Abfolge merken" in panel and "Fuß-Vorgabe" in panel)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Farbfelder")'); await pg.wait_for_timeout(120)
        await pg.click('#cardioAddonPickerDetail [data-mode="regeln"]'); await pg.wait_for_timeout(120)
        check("Cardio picker: Stufe row appears for Regeln", await pg.locator('#cardioAddonPickerDetail [data-balf="level"]').count() == 4)
        await pg.evaluate("() => { window.__ffLastGeom = null; }")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(700)
        check("Cardio: guest runs Farbfelder on the canvas", await pg.is_visible("#player") and await pg.evaluate("() => !!window.__ffLastGeom"))
        await pg.screenshot(path=f"{SHOTS}/cardio_guest_light.png")
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
