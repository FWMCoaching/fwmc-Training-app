"""Farbfelder Reize (Fabian 07.10.2026 21:53): new modes A Ansage, B Farbwort,
C Fuß und Hand, D Sehen und Hören ("Bei beidem gilt", Mischung) and the
option E Rhythmus-Umkehr (jedes 2./3. Mal andersherum) for Leuchten, Regeln
and Sehen und Hören. Rule functions, drawing, persistence, Kombi, Cardio.
Run from tests/ with a dev server on :8845."""
import asyncio, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
# Records every spoken text; speechSynthesis itself is silent in headless Chromium.
SPEECH_SPY = """
window.__said = [];
if (window.speechSynthesis) {
  const orig = window.speechSynthesis.speak.bind(window.speechSynthesis);
  window.speechSynthesis.speak = (u) => { window.__said.push(u.text); try { orig(u); } catch (e) {} };
}
"""
SHOTS = "screenshots/farbfelder_reize"
NEW_MODES = ("ansage", "farbwort", "fusshand", "sehenhoeren")
LAYOUT_HEX = {"rot": (0xd3, 0x2f, 0x2f), "blau": (0x15, 0x65, 0xc0), "gelb": (0xf2, 0xa9, 0x00), "gruen": (0x2e, 0x7d, 0x32)}

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

# Colours at the four field corners and centres (CSS px -> canvas px).
PIXELS_JS = """() => {
  const g = window.__ffLastGeom; if (!g) return null;
  const c = document.getElementById('stage'); const r = c.getBoundingClientRect();
  const k = c.width / r.width; const ctx = c.getContext('2d');
  const w = (g.right - g.left) / 2, h = (g.bottom - g.top) / 2;
  const at = (x, y) => Array.from(ctx.getImageData(Math.round((x - r.left) * k), Math.round((y - r.top) * k), 1, 1).data.slice(0, 3));
  const corner = [], centre = [], plate = [];
  for (let i = 0; i < 4; i++) {
    const x0 = g.left + (i % 2) * w, y0 = g.top + (i >> 1) * h;
    corner.push(at(x0 + w * 0.2, y0 + h * 0.2));
    centre.push(at(x0 + w * 0.5, y0 + h * 0.5));
    plate.push(at(x0 + w * 0.5, y0 + h * 0.34)); // inside a word plate, above the letters
  }
  return { corner, centre, plate, geom: g };
}"""

def close(a, b, tol=6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))

async def open_ff(pg):
    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        await ctx.add_init_script(SPEECH_SPY)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- pure rule functions ----
        r = await pg.evaluate("() => [1,2,3,4,5,6,7,8,9].map(n => [window.__ff.isFlipped(n, 0), window.__ff.isFlipped(n, 2), window.__ff.isFlipped(n, 3)])")
        check("Umkehr aus: never flipped", all(not x[0] for x in r))
        check("Umkehr jedes 2.: 2, 4, 6, 8", [i + 1 for i, x in enumerate(r) if x[1]] == [2, 4, 6, 8])
        check("Umkehr jedes 3.: 3, 6, 9", [i + 1 for i, x in enumerate(r) if x[2]] == [3, 6, 9])
        r = await pg.evaluate("() => [0,1,2,3].map(f => [window.__ff.leuchtenTarget(f, false), window.__ff.leuchtenTarget(f, true)])")
        check("Leuchten: normal = lit field, flipped = diagonal", r == [[0, 3], [1, 2], [2, 1], [3, 0]], r)
        r = await pg.evaluate("() => ['viereck','dreieck','strich','herz'].map(s => [0,1,2,3].map(f => window.__ff.regelnTarget(s, f, true) === 3 - window.__ff.target(s, f) && window.__ff.regelnTarget(s, f, false) === window.__ff.target(s, f)))")
        check("Regeln: flipped = diagonal of the normal target", all(all(x) for x in r))
        r = await pg.evaluate("() => { const l = ['rot','blau','gelb','gruen']; return [window.__ff.ansageTarget('gelb', l), window.__ff.farbwortTarget('blau', l)]; }")
        check("Ansage / Farbwort: target = field of that colour", r == [2, 1], r)
        r = await pg.evaluate("""() => { const t = window.__ff.sehenHoerenTarget;
            return [t('bild', 1, null, 'gesagt', false), t('ton', null, 2, 'gezeigt', false),
                    t('beides', 1, 2, 'gesagt', false), t('beides', 1, 2, 'gezeigt', false),
                    t('beides', 1, 2, 'gesagt', true), t('beides', 1, 2, 'gezeigt', true)]; }""")
        check("Sehen und Hören: rule incl. gilt + flip", r == [1, 2, 2, 1, 1, 2], r)
        r = await pg.evaluate("() => { const l = ['rot','blau','gelb','gruen']; return Array.from({length: 400}, () => window.__ff.pickFarbwort(l)).every(w => w.wordKey !== w.inkKey && l.includes(w.wordKey) && l[w.target] === w.inkKey); }")
        check("Farbwort pick: word never equals ink (400 draws)", r)

        # ---- schedules ----
        r = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'farbwort', duration:600}).filter(f => f.kind === 'farbfelder');
            return { n: fr.length, ok: fr.every(f => f.payload.wordKey !== f.payload.inkKey && f.payload.target === ['rot','blau','gelb','gruen'].indexOf(f.payload.inkKey)) }; }""")
        check("Farbwort schedule: word != ink, target = ink field", r["ok"] and r["n"] > 20, r)
        r = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'ansage', duration:300}).filter(f => f.kind === 'farbfelder');
            return { n: fr.length, ok: fr.every(f => f.payload.say && f.payload.lit === undefined && ['Rot','Blau','Gelb','Grün'][f.payload.target] === f.payload.say) }; }""")
        check("Ansage schedule: says the colour of the target, nothing lit", r["ok"] and r["n"] > 10, r)
        r = await pg.evaluate("""() => { const fr = window.__ff.build({ffMode:'fusshand', duration:300}).filter(f => f.kind === 'farbfelder');
            return { n: fr.length, ok: fr.every(f => f.payload.footAt !== f.payload.handAt && f.payload.target === f.payload.footAt) }; }""")
        check("Fuß und Hand: two different fields, target = foot field", r["ok"] and r["n"] > 10, r)
        for gilt in ("gesagt", "gezeigt"):
            r = await pg.evaluate("""(g) => { const fr = window.__ff.build({ffMode:'sehenhoeren', ffGilt:g, ffMix:'ausgewogen', ffFlip:0, duration:900}).filter(f => f.kind === 'farbfelder');
                const kinds = {}; fr.forEach(f => kinds[f.payload.kind] = (kinds[f.payload.kind] || 0) + 1);
                const both = fr.filter(f => f.payload.kind === 'beides');
                return { kinds, ok: both.every(f => f.payload.saidField !== f.payload.shown && f.payload.target === (g === 'gesagt' ? f.payload.saidField : f.payload.shown)),
                  single: fr.filter(f => f.payload.kind === 'bild').every(f => f.payload.target === f.payload.lit && !f.payload.say) && fr.filter(f => f.payload.kind === 'ton').every(f => f.payload.lit === undefined && f.payload.say) }; }""", gilt)
            check(f"Sehen und Hören gilt={gilt}: conflicts follow the setting", r["ok"] and r["single"], r)
            check(f"Sehen und Hören gilt={gilt}: all three kinds occur", len(r["kinds"]) == 3 and min(r["kinds"].values()) > 5, r["kinds"])
        r = await pg.evaluate("""() => window.__ff.build({ffMode:'sehenhoeren', ffMix:'nurbeides', duration:300}).filter(f => f.kind === 'farbfelder').every(f => f.payload.kind === 'beides')""")
        check("Mischung 'Nur beides': only both", r)
        for every in (2, 3):
            r = await pg.evaluate("""(e) => { const fr = window.__ff.build({ffMode:'leuchten', ffFlip:e, duration:300}).filter(f => f.kind === 'farbfelder');
                return { ok: fr.every((f, i) => f.payload.flipped === ((i + 1) % e === 0) && f.payload.target === (f.payload.flipped ? 3 - f.payload.lit : f.payload.lit)), n: fr.length }; }""", every)
            check(f"Leuchten jedes {every}.: every {every}th flipped to the diagonal", r["ok"] and r["n"] > 10, r)
            r = await pg.evaluate("""(e) => { const fr = window.__ff.build({ffMode:'regeln', ffLevel:4, ffFlip:e, duration:300}).filter(f => f.kind === 'farbfelder');
                return fr.every((f, i) => f.payload.flipped === ((i + 1) % e === 0) && f.payload.target === window.__ff.regelnTarget(f.payload.symbol, f.payload.at, f.payload.flipped)); }""", every)
            check(f"Regeln jedes {every}.: flip follows the count", r)
            r = await pg.evaluate("""(e) => { const fr = window.__ff.build({ffMode:'sehenhoeren', ffGilt:'gesagt', ffMix:'ausgewogen', ffFlip:e, duration:600}).filter(f => f.kind === 'farbfelder');
                const both = fr.filter(f => f.payload.kind === 'beides');
                return { ok: both.length > 5 && both.every((f, i) => f.payload.flipped === ((i + 1) % e === 0) && f.payload.target === (f.payload.flipped ? f.payload.shown : f.payload.saidField)),
                  singleNever: fr.filter(f => f.payload.kind !== 'beides').every(f => !f.payload.flipped) }; }""", every)
            check(f"Sehen und Hören jedes {every}.: counts only 'beides', flips the source", r["ok"] and r["singleNever"], r)
        r = await pg.evaluate("() => window.__ff.build({ffMode:'leer', ffFlip:2, duration:200}).filter(f => f.kind === 'farbfelder').every(f => !f.payload.flipped)")
        check("Umkehr does not touch Das leere Feld", r)

        # ---- ready screen: groups per mode ----
        await open_ff(pg)
        check("9 modes in the Modus row (+ Einblenden 08.10.)", await pg.locator("#ffModeRow [data-ff-mode]").count() == 9)
        await pg.click('[data-ff-mode="sehenhoeren"]'); await pg.wait_for_timeout(80)
        check("Sehen und Hören: gilt + Mischung + Umkehr visible", await pg.is_visible("#ffGiltGroup") and await pg.is_visible("#ffFlipGroup"))
        await pg.click('[data-ff-mode="farbwort"]'); await pg.wait_for_timeout(80)
        check("Farbwort: no gilt/Umkehr group", not await pg.is_visible("#ffGiltGroup") and not await pg.is_visible("#ffFlipGroup"))
        await pg.click('[data-ff-mode="fusshand"]'); await pg.wait_for_timeout(80)
        check("Fuß und Hand: Hände group hidden", not await pg.is_visible("#ffHandsGroup"))
        await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(80)
        check("Leuchten: Umkehr offered, default Aus", await pg.is_visible("#ffFlipGroup") and "active" in (await pg.get_attribute('[data-ff-flip="0"]', "class")))

        # ---- persistence ----
        await pg.click('[data-ff-mode="sehenhoeren"]'); await pg.click('[data-ff-gilt="gezeigt"]')
        await pg.click('[data-ff-mix="mehrbeides"]'); await pg.click('[data-ff-flip="3"]'); await pg.wait_for_timeout(80)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        act = lambda sel: pg.get_attribute(sel, "class")
        check("persists: mode, gilt, Mischung, Umkehr",
              all(["active" in (await act(s)) for s in ['[data-ff-mode="sehenhoeren"]', '[data-ff-gilt="gezeigt"]', '[data-ff-mix="mehrbeides"]', '[data-ff-flip="3"]']]))
        st = await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); return [s.ffMode, s.ffGilt, s.ffMix, s.ffFlip]; }")
        check("stored in fwmc-webapp-v3", st == ["sehenhoeren", "gezeigt", "mehrbeides", 3], st)
        # broken values get normalised
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.ffGilt = 'x'; s.ffMix = 'y'; s.ffFlip = 7; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("invalid stored values fall back to defaults",
              all(["active" in (await act(s)) for s in ['[data-ff-gilt="gesagt"]', '[data-ff-mix="ausgewogen"]', '[data-ff-flip="0"]']]))
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)

        # ---- every new mode starts and draws (light + dark) ----
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme)
            await pg.goto(URL); await pg.wait_for_timeout(400)
            await open_ff(pg)
            for mode in NEW_MODES + ("leuchten",):
                await pg.click(f'[data-ff-mode="{mode}"]')
                if mode in ("leuchten", "sehenhoeren"): await pg.click('[data-ff-flip="2"]')
                await pg.wait_for_timeout(80)
                await pg.screenshot(path=f"{SHOTS}/ready_{mode}_{scheme}.png", full_page=True)
                await pg.evaluate("() => { window.__said = []; }")
                await pg.click("#startBtn"); await pg.wait_for_timeout(500)
                info = await pg.evaluate(PIXELS_JS)
                if info is None:
                    check(f"{scheme} {mode}: drawn", False); continue
                g = info["geom"]
                check(f"{scheme} {mode}: grid below the bar, above the caption", g["top"] >= g["barBottom"] and g["bottom"] <= g["capTop"] + 0.5, g)
                if mode == "ansage":
                    full = all(close(info["corner"][i], LAYOUT_HEX[k]) for i, k in enumerate(["rot", "blau", "gelb", "gruen"]))
                    nomark = all(close(info["centre"][i], info["corner"][i]) for i in range(4))
                    check(f"{scheme} ansage: no highlighted field (4 full colours, nothing on a field)", full and nomark, info)
                    said = await pg.evaluate("() => window.__said.slice()")
                    check(f"{scheme} ansage: a colour was spoken", any(w in ("Rot", "Blau", "Gelb", "Grün") for w in said), said)
                if mode == "farbwort":
                    white = sum(1 for c in info["plate"] if c[0] > 240 and c[1] > 240 and c[2] > 240)
                    check(f"{scheme} farbwort: one white word plate", white == 1, info["plate"])
                if mode == "fusshand":
                    white = sum(1 for c in info["centre"] if c[0] > 240 and c[1] > 240 and c[2] > 240)
                    check(f"{scheme} fusshand: foot + hand drawn on two fields", white == 2, info["centre"])
                await pg.screenshot(path=f"{SHOTS}/{mode}_{scheme}.png")
                await pg.click("#backBtn"); await pg.wait_for_timeout(300)
            await pg.click('[data-ff-flip="0"]'); await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
            await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.emulate_media(color_scheme="light")

        # ---- sound off: nothing spoken, caption says so ----
        await pg.evaluate("() => { localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false})); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        muted = await pg.evaluate("() => { try { return JSON.parse(localStorage.getItem('fwmc-workout-sound-v1')).enabled === false; } catch (e) { return false; } }")
        await open_ff(pg)
        await pg.click('[data-ff-mode="ansage"]'); await pg.wait_for_timeout(60)
        await pg.evaluate("() => { window.__said = []; }")
        await pg.click("#startBtn"); await pg.wait_for_timeout(2500)
        said = await pg.evaluate("() => window.__said.slice()")
        check("🔊 off: Ansage speaks nothing", muted and not said, said)
        await pg.screenshot(path=f"{SHOTS}/ansage_ton_aus_light.png")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => localStorage.removeItem('fwmc-workout-sound-v1')")
        await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)

        # ---- Kombi capture: own mode + gilt, standalone untouched ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbfelder")'); await pg.wait_for_timeout(250)
        await pg.click('[data-ff-mode="sehenhoeren"]'); await pg.click('[data-ff-gilt="gezeigt"]'); await pg.click('[data-ff-flip="2"]'); await pg.wait_for_timeout(80)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("Kombi: block added", await pg.is_visible("#comboScreen") and "Farbfelder" in await pg.inner_text("#comboBlockList"))
        st = await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); return [s.ffMode, s.ffGilt, s.ffFlip]; }")
        check("Kombi: standalone settings unchanged", st == ["leuchten", "gesagt", 0], st)
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-editable with its own mode/gilt/Umkehr",
              all(["active" in (await act(s)) for s in ['[data-ff-mode="sehenhoeren"]', '[data-ff-gilt="gezeigt"]', '[data-ff-flip="2"]']]))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.evaluate("() => { window.__ffLastGeom = null; }")
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(900)
        check("Kombi: block plays on the canvas", await pg.is_visible("#player") and await pg.evaluate("() => !!window.__ffLastGeom"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        st = await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); return [s.ffMode, s.ffGilt, s.ffFlip]; }")
        check("Kombi: standalone settings restored after the run", st == ["leuchten", "gesagt", 0], st)

        # ---- history label ----
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.duration = 4; s.ffMode = 'farbwort'; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click("#startBtn")
        await pg.wait_for_selector("#donePanel:not([hidden])", timeout=20000)
        hist = await pg.evaluate("() => { const h = JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]'); return h.length ? h[0] : null; }")
        check("history: Farbfelder entry names the mode", hist and hist.get("exId") == "farbfelder" and hist.get("note") == "Farbwort", hist)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.duration = 60; s.ffMode = 'leuchten'; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")

        # ---- Cardio guest ----
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid [data-pool="farbfelder"]'); await pg.wait_for_timeout(150)
        panel = pg.locator("#cardioAddonPerType")
        check("Cardio settings: 9 Farbfelder modes", await panel.locator('[data-mode-row="farbfelder"] [data-mode]').count() == 9)
        await panel.locator('[data-mode-row="farbfelder"] [data-mode="sehenhoeren"]').click(); await pg.wait_for_timeout(120)
        check("Cardio settings: gilt + Mischung + Umkehr for Sehen und Hören",
              await panel.locator('[data-balf="gilt"]').count() == 2 and await panel.locator('[data-balf="mix"]').count() == 3 and await panel.locator('[data-balf="flip"]').count() == 3)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Farbfelder")'); await pg.wait_for_timeout(120)
        detail = pg.locator("#cardioAddonPickerDetail")
        check("Cardio picker lists the new modes", all([await detail.locator(f'[data-mode="{m}"]').count() == 1 for m in NEW_MODES]))
        await detail.locator('[data-mode="farbwort"]').click(); await pg.wait_for_timeout(120)
        await pg.evaluate("() => { window.__ffLastGeom = null; }")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(700)
        check("Cardio: guest runs Farbwort on the canvas", await pg.is_visible("#player") and await pg.evaluate("() => !!window.__ffLastGeom"))
        await pg.screenshot(path=f"{SHOTS}/cardio_guest_farbwort_light.png")
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
