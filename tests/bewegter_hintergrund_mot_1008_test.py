"""Bewegter Hintergrund in Objektverfolgung (MOT) (Fabian 08.10.2026): the
Optodrum pattern behind the moving balls, like Gleichgewicht/Positionen
merken/Flash.
- One group in Feineinstellungen on both MOT ready screens (default Aus),
  one live box in the pause sheet.
- Run: canvas first in the stage, z -1, pointer-events none; pattern moves,
  frozen while paused; balls stay on top and tap selection still works.
- Pause sheet changes it live (saved for standalone runs only); a Kombi block
  carries its own copy and never changes the client's own setting.
- Default pattern colours keep the black balls clearly readable.
Run from tests/ with a dev server on :8845."""
import asyncio, os
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-natmodes','true');"
        "if (!localStorage.getItem('fwmc-master-v1')) localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/bewegter_hintergrund"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

async def set_range(pg, sel, v):
    await pg.evaluate("""([s, v]) => { const i = document.querySelector(s); i.value = v; i.dispatchEvent(new Event('input', {bubbles: true})); }""", [sel, v])

def ls(pg, key):
    return pg.evaluate("(k) => JSON.parse(localStorage.getItem(k) || 'null')", key)

async def end_run(pg):
    await pg.evaluate("() => document.getElementById('motBackBtn').click()"); await pg.wait_for_timeout(300)
    if await pg.is_visible("#confirmSheet"):
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

async def open_mot(pg):
    await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)
    await pg.click('#natHome .nat-tile[data-nat-ex="mot"]'); await pg.wait_for_timeout(250)
    if await pg.is_hidden("#motReady"):
        await pg.click('#motTrainingReady [data-nat-mode="speed"], #motTrainingReady .nat-mode-row button >> nth=0'); await pg.wait_for_timeout(200)

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
        # slow, short rounds so the identify phase comes quickly
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => localStorage.setItem('fwmc-mot-prefs-v1', JSON.stringify({speed:0.08, trackS:3, highlightS:2}))")
        await open_mot(pg)

        for scr in ("motReady", "motTrainingReady"):
            n = await pg.locator(f"#{scr} details.advanced .mbg-group").count()
            check(f"{scr}: one 'Bewegter Hintergrund' group in Feineinstellungen", n == 1, n)
        after_bg = await pg.evaluate("""() => { const g = document.querySelector('#motReady .mbg-group'); const prev = g.previousElementSibling;
            return !!(prev && prev.querySelector('#motBgIntensitySlider')); }""")
        check("group sits right after 'Hintergrund'", after_bg)
        check("pause sheet has the live box", await pg.locator("#motPauseOverlay details.mbg-pause").count() == 1)
        check("ready screen open", await pg.is_visible("#motReady"))

        # ---- default off ----
        g = "#motReady .mbg-group"
        if not await pg.evaluate("() => document.getElementById('motAdvanced').open"):
            await pg.click("#motAdvanced summary"); await pg.wait_for_timeout(100)
        check("default Aus, details hidden", "active" in (await pg.get_attribute(f'{g} [data-opto-v="aus"]', "class")) and not await pg.is_visible(f"{g} .mbg-more"))
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(500)
        off = await pg.evaluate("() => window.__mbg('mot')")
        check("default run: no layer", not off["running"] and off["st"]["pattern"] == "aus", off)
        await end_run(pg)

        # ---- switch on in Feineinstellungen ----
        await open_mot(pg)
        if not await pg.evaluate("() => document.getElementById('motAdvanced').open"):
            await pg.click("#motAdvanced summary"); await pg.wait_for_timeout(100)
        await pg.click(f'{g} [data-opto-v="streifen"]'); await pg.wait_for_timeout(80)
        check("Streifen: details shown", await pg.is_visible(f"{g} .mbg-more"))
        check("epilepsy / Schwindel sentence present", "Epilepsie" in await pg.inner_text(f"{g} .mbg-more") and "Schwindel" in await pg.inner_text(f"{g} .mbg-more"))
        mb = (await ls(pg, "fwmc-mot-prefs-v1"))["mbg"]
        check("saved in MOT prefs, default intensity like the siblings (35 %)", mb["pattern"] == "streifen" and mb["fgInt"] == 35 and mb["speed"] == 3, mb)
        check("training ready screen shows the same setting", "active" in (await pg.get_attribute('#motTrainingReady .mbg-group [data-opto-v="streifen"]', "class")))
        await pg.evaluate("(s) => { document.querySelector(s).scrollIntoView({block: 'start'}); window.scrollBy(0, -70); }", g)
        await pg.wait_for_timeout(150)
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(150)
            await pg.screenshot(path=f"{SHOTS}/mot_ready_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        await pg.reload(); await pg.wait_for_timeout(500)
        check("persists across reload", (await ls(pg, "fwmc-mot-prefs-v1"))["mbg"]["pattern"] == "streifen")
        await open_mot(pg)

        # ---- run with pattern ----
        await pg.click("#motReadyStartBtn")
        targets = []
        for _ in range(40):
            targets = await pg.evaluate("""() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map((el, i) => el.classList.contains('target') ? i : -1).filter(i => i >= 0)""")
            if targets: break
            await pg.wait_for_timeout(80)
        await pg.wait_for_timeout(300)
        m1 = await pg.evaluate("() => window.__mbg('mot')")
        check("run: layer running with its own copy", m1["running"] and m1["st"]["pattern"] == "streifen", m1)
        lay = await pg.evaluate("""() => { const st = document.getElementById('motStage'); const c = st.querySelector(':scope > canvas.mbg-canvas'); const s = getComputedStyle(c);
            const r = c.getBoundingClientRect(); const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return { first: c === st.firstElementChild, z: s.zIndex, pe: s.pointerEvents, vis: !c.hidden && r.width > 100, hitCanvas: hit === c, iso: getComputedStyle(st).isolation }; }""")
        check("canvas first in the stage, z -1, never hit", lay["first"] and lay["z"] == "-1" and lay["pe"] == "none" and lay["vis"] and not lay["hitCanvas"] and lay["iso"] == "isolate", lay)
        # balls stay readable: black ball vs both pattern colours
        con = await pg.evaluate("""(c) => { const lum = (h) => { const v = [1,3,5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(x => x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
            const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
            return [ratio('#16232a', c.fg), ratio('#16232a', c.bg), ratio('#000000', c.fg)]; }""", m1["colors"])
        check("default pattern keeps dark balls clearly readable (contrast >= 4.5)", min(con) >= 4.5, con)
        await pg.wait_for_timeout(400)
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(150)
            await pg.screenshot(path=f"{SHOTS}/mot_run_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        m2 = await pg.evaluate("() => window.__mbg('mot')")
        check("pattern moves", abs(m2["m"]["s"] - m1["m"]["s"]) > 5, (m1["m"]["s"], m2["m"]["s"]))

        # ---- tap selection still works with the pattern on ----
        check("targets highlighted", len(targets) > 0, targets)
        ok = False
        for _ in range(120):
            if await pg.locator("#motObjectsLayer .mot-object.tappable").count() > 0: ok = True; break
            await pg.wait_for_timeout(80)
        check("identify phase reached", ok)
        on_top = await pg.evaluate("""(ids) => ids.every((i) => { const el = document.querySelectorAll('#motObjectsLayer .mot-object')[i]; const r = el.getBoundingClientRect();
            const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return h === el || el.contains(h); })""", targets)
        check("every ball is the hit target at its centre (above the canvas)", on_top)
        for i in targets:
            box = await pg.locator("#motObjectsLayer .mot-object").nth(i).bounding_box()
            await pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await pg.wait_for_timeout(60)
        hint = await pg.inner_text("#motHint")
        check("tapping the targets through real pointer hits counts", hint.startswith("Richtig"), hint)

        # ---- pause: frozen + live change (standalone = saved) ----
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        a = (await pg.evaluate("() => window.__mbg('mot')"))["m"]["s"]
        await pg.wait_for_timeout(300)
        bb = (await pg.evaluate("() => window.__mbg('mot')"))["m"]["s"]
        check("paused: frozen", abs(a - bb) < 0.01, (a, bb))
        await pg.click("#motPauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(80)
        pz = "#motPauseOverlay .mbg-group"
        check("pause box shows the run's values", "active" in (await pg.get_attribute(f'{pz} [data-opto-v="streifen"]', "class")))
        check("pause box says it is saved", "bleibt gespeichert" in await pg.inner_text("#motPauseOverlay [data-mbg-live]"))
        await pg.click(f'{pz} [data-opto-v="punkte"]'); await pg.wait_for_timeout(60)
        await set_range(pg, f'{pz} [data-opto-r="speed"]', 6); await pg.wait_for_timeout(80)
        m3 = await pg.evaluate("() => window.__mbg('mot')")
        check("live: run state changed", m3["st"]["pattern"] == "punkte" and m3["st"]["speed"] == 6, m3["st"])
        check("live: standalone run saves", m3["prefs"]["pattern"] == "punkte" and m3["prefs"]["speed"] == 6, m3["prefs"])
        await pg.click(f'{pz} [data-opto-v="aus"]'); await pg.wait_for_timeout(120)
        check("live Aus stops the layer", not (await pg.evaluate("() => window.__mbg('mot')"))["running"])
        await pg.click(f'{pz} [data-opto-v="streifen"]'); await pg.wait_for_timeout(80)
        await pg.click("#motResumeBtn"); await pg.wait_for_timeout(250)
        check("running again after resume", (await pg.evaluate("() => window.__mbg('mot')"))["running"])
        wide = await pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
        check("no sideways scroll", wide)
        await end_run(pg)
        check("leaving stops the layer", not (await pg.evaluate("() => window.__mbg('mot')"))["running"])

        # ---- Sanfte Reize: tempo capped ----
        await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); m.softStimuli = true; localStorage.setItem('fwmc-master-v1', JSON.stringify(m)); const f = JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')); f.mbg = {pattern:'streifen', speed:9}; localStorage.setItem('fwmc-mot-prefs-v1', JSON.stringify(f)); }")
        await open_mot(pg)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(400)
        s1 = await pg.evaluate("() => window.__mbg('mot')")
        check("Sanfte Reize: tempo capped at 4", s1["running"] and s1["st"]["speed"] == 9 and s1["eff"] == 4, s1)
        await end_run(pg)
        await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); m.softStimuli = false; localStorage.setItem('fwmc-master-v1', JSON.stringify(m)); const f = JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')); f.mbg = {pattern:'aus'}; localStorage.setItem('fwmc-mot-prefs-v1', JSON.stringify(f)); }")

        # ---- Kombi: own copy, own setting untouched ----
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Objektverfolgung (MOT) · Tempo steigt"'); await pg.wait_for_timeout(300)
        if not await pg.evaluate("() => document.getElementById('motAdvanced').open"):
            await pg.click("#motAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.click('#motReady .mbg-group [data-opto-v="punkte"]'); await pg.wait_for_timeout(60)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        own = (await ls(pg, "fwmc-mot-prefs-v1"))["mbg"]["pattern"]
        check("Kombi capture: own setting stays Aus", own == "aus", own)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(800)
        k1 = await pg.evaluate("() => window.__mbg('mot')")
        check("Kombi block plays with its own dots", k1["running"] and k1["st"]["pattern"] == "punkte", k1)
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(150)
        check("Kombi pause: only this run", "nur für diesen Durchgang" in await pg.evaluate("() => document.querySelector('#motPauseOverlay [data-mbg-live]').textContent"))
        await pg.click("#motPauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(60)
        await pg.click('#motPauseOverlay .mbg-group [data-opto-v="streifen"]'); await pg.wait_for_timeout(80)
        own = (await ls(pg, "fwmc-mot-prefs-v1"))["mbg"]["pattern"]
        check("Kombi live change never saved", own == "aus" and (await pg.evaluate("() => window.__mbg('mot')"))["st"]["pattern"] == "streifen", own)
        await pg.click("#motResumeBtn")
        await end_run(pg)
        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
