"""Bewegter Hintergrund (Fabian 08.10.2026): the Optodrum pattern as a moving
layer behind Gleichgewicht, Positionen merken and Flash-Speicher-Test.
- Feineinstellungen group on every ready screen (default Aus), Streifen/Punkte,
  Richtung, Tempo, Breite/Punktgröße (label follows), Abstand, Musterfarbe +
  Intensität, Hintergrundfarbe + Intensität; persists across reload.
- Run: canvas behind the content (z-index -1, pointer-events none), moving,
  frozen while paused; pause sheet changes it live (saved standalone).
- Sanfte Reize caps the tempo at 4; Kombi block carries its own copy and a
  Kombi run never changes the client's own setting; presets carry it.
- Optodrum (same renderer) still moves.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
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
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)

        # ---- groups on every ready screen ----
        for scr in ("balanceReady", "rememberReady", "rememberTrainingReady", "flashReady", "flashTrainingReady"):
            n = await pg.locator(f"#{scr} details.advanced .mbg-group").count()
            check(f"{scr}: one 'Bewegter Hintergrund' group in Feineinstellungen", n == 1, n)
        for ov in ("balancePauseOverlay", "rememberPauseOverlay", "flashPauseOverlay"):
            check(f"{ov}: live box", await pg.locator(f"#{ov} details.mbg-pause").count() == 1)

        # ---- Positionen merken: ready settings ----
        await pg.click('#natHome .nat-tile[data-nat-ex="remember"]'); await pg.wait_for_timeout(250)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(100)
        g = "#rememberReady .mbg-group"
        check("default Aus, details hidden", "active" in (await pg.get_attribute(f'{g} [data-opto-v="aus"]', "class")) and not await pg.is_visible(f"{g} .mbg-more"))
        await pg.click(f'{g} [data-opto-v="punkte"]'); await pg.wait_for_timeout(80)
        check("Punkte: details shown", await pg.is_visible(f"{g} .mbg-more"))
        check("size label follows the pattern (Punktgröße)", (await pg.inner_text(f'{g} [data-opto-lbl="size"]')) == "Punktgröße")
        await set_range(pg, f'{g} [data-opto-r="size"]', 60)
        await set_range(pg, f'{g} [data-opto-r="gap"]', 30)
        await set_range(pg, f'{g} [data-opto-r="speed"]', 7)
        await set_range(pg, f'{g} [data-opto-r="fgInt"]', 50)
        await set_range(pg, f'{g} [data-opto-r="bgInt"]', 30)
        await pg.click(f'{g} [data-opto-c="fg"] [data-key="blau"]')
        await pg.click(f'{g} [data-opto-c="bg"] [data-key="gelb"]')
        await set_range(pg, f'{g} [data-opto-r="size"]', 999)  # clamped
        await pg.wait_for_timeout(80)
        mb = (await ls(pg, "fwmc-remember-prefs-v1"))["mbg"]
        check("saved: pattern/speed/size/gap/colours/intensities", mb["pattern"] == "punkte" and mb["speed"] == 7 and mb["size"] == 160 and mb["gap"] == 30
              and mb["fg"] == "blau" and mb["bg"] == "gelb" and mb["fgInt"] == 50 and mb["bgInt"] == 30, mb)
        check("size value shows px", (await pg.inner_text(f'{g} [data-opto-out="size"]')) == "160 px")
        await set_range(pg, f'{g} [data-opto-r="size"]', 40)
        check("intensity value shows %", (await pg.inner_text(f'{g} [data-opto-out="fgInt"]')) == "50 %")
        await pg.click(f'{g} [data-opto-v="schraeg"]'); await pg.wait_for_timeout(60)
        check("Schräg shows the diagonal row", await pg.is_visible(f'{g} [data-opto-v="lu"]'))
        await pg.click(f'{g} [data-opto-v="lu"]')
        await pg.click(f'{g} [data-opto-v="streifen"]'); await pg.wait_for_timeout(60)
        check("Streifen: label Streifenbreite", (await pg.inner_text(f'{g} [data-opto-lbl="size"]')) == "Streifenbreite")
        await pg.click(f'{g} [data-opto-v="punkte"]'); await pg.wait_for_timeout(60)
        await pg.locator(g).scroll_into_view_if_needed()
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/ready_remember_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        await pg.reload(); await pg.wait_for_timeout(500)
        await pg.click('#natHome .nat-tile[data-nat-ex="remember"]'); await pg.wait_for_timeout(250)
        check("persists across reload", "active" in (await pg.get_attribute(f'{g} [data-opto-v="punkte"]', "class")) and "active" in (await pg.get_attribute(f'{g} [data-opto-v="lu"]', "class")))
        check("training ready screen shows the same setting", "active" in (await pg.get_attribute('#rememberTrainingReady .mbg-group [data-opto-v="punkte"]', "class")))

        # ---- run: behind the content, moving, paused, live ----
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(700)
        m1 = await pg.evaluate("() => window.__mbg('remember')")
        check("run: layer running with its own copy", m1["running"] and m1["st"]["pattern"] == "punkte" and m1["st"]["speed"] == 7, m1)
        lay = await pg.evaluate("""() => { const c = document.querySelector('#rememberStage > canvas.mbg-canvas'); const s = getComputedStyle(c);
            const r = c.getBoundingClientRect(); const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            const st = getComputedStyle(document.getElementById('rememberStage'));
            return { first: c === document.getElementById('rememberStage').firstElementChild, z: s.zIndex, pe: s.pointerEvents, vis: !c.hidden && r.width > 100, hitCanvas: hit === c, iso: st.isolation }; }""")
        check("canvas first in the stage, z -1, never hit", lay["first"] and lay["z"] == "-1" and lay["pe"] == "none" and lay["vis"] and not lay["hitCanvas"] and lay["iso"] == "isolate", lay)
        mk = await pg.evaluate("""() => { const m = document.querySelector('.remember-marker'); if (!m) return null; const r = m.getBoundingClientRect();
            return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) === m || m.contains(document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)); }""")
        check("a marker stays on top (tappable)", mk is True, mk)
        await pg.screenshot(path=f"{SHOTS}/run_remember.png")
        await pg.wait_for_timeout(300)
        m2 = await pg.evaluate("() => window.__mbg('remember')")
        check("pattern moves", abs(m2["m"]["s"] - m1["m"]["s"]) > 5, (m1["m"]["s"], m2["m"]["s"]))
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(200)
        a = (await pg.evaluate("() => window.__mbg('remember')"))["m"]["s"]
        await pg.wait_for_timeout(300)
        bb = (await pg.evaluate("() => window.__mbg('remember')"))["m"]["s"]
        check("paused: frozen", abs(a - bb) < 0.01, (a, bb))
        await pg.click("#rememberPauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(80)
        pz = "#rememberPauseOverlay .mbg-group"
        check("pause box shows the run's values", "active" in (await pg.get_attribute(f'{pz} [data-opto-v="punkte"]', "class")) and (await pg.inner_text(f'{pz} [data-opto-out="speed"]')) == "Stufe 7")
        check("pause box says it is saved", "bleibt gespeichert" in await pg.inner_text("#rememberPauseOverlay [data-mbg-live]"))
        await set_range(pg, f'{pz} [data-opto-r="size"]', 80)
        await set_range(pg, f'{pz} [data-opto-r="speed"]', 2)
        await pg.click(f'{pz} [data-opto-c="fg"] [data-key="rot"]'); await pg.wait_for_timeout(80)
        m3 = await pg.evaluate("() => window.__mbg('remember')")
        check("live: run state changed", m3["st"]["size"] == 80 and m3["st"]["speed"] == 2 and m3["st"]["fg"] == "rot", m3["st"])
        check("live: standalone run saves", m3["prefs"]["size"] == 80 and m3["prefs"]["speed"] == 2)
        await pg.locator("#rememberPauseOverlay .mbg-pause").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/pause_remember.png")
        await pg.click(f'{pz} [data-opto-v="aus"]'); await pg.wait_for_timeout(120)
        check("live Aus stops the layer", not (await pg.evaluate("() => window.__mbg('remember')"))["running"])
        await pg.click(f'{pz} [data-opto-v="punkte"]'); await pg.wait_for_timeout(80)
        await pg.click("#rememberResumeBtn"); await pg.wait_for_timeout(250)
        check("live on again after resume", (await pg.evaluate("() => window.__mbg('remember')"))["running"])
        await pg.evaluate("() => document.getElementById('rememberBackBtn').click()"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("leaving stops the layer", not (await pg.evaluate("() => window.__mbg('remember')"))["running"])

        # ---- Flash: stripes, keypad above, Sanfte Reize ----
        await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); m.softStimuli = true; localStorage.setItem('fwmc-master-v1', JSON.stringify(m)); const f = JSON.parse(localStorage.getItem('fwmc-flash-prefs-v1') || '{}'); f.mbg = {pattern:'streifen', speed:9, fg:'schwarz', fgInt:40, dir:'hoch'}; localStorage.setItem('fwmc-flash-prefs-v1', JSON.stringify(f)); }")
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.click('#natHome .nat-tile[data-nat-ex="flash"]'); await pg.wait_for_timeout(250)
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(500)
        f1 = await pg.evaluate("() => window.__mbg('flash')")
        check("Sanfte Reize: tempo capped at 4", f1["running"] and f1["st"]["speed"] == 9 and f1["eff"] == 4, f1)
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#flashPauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(80)
        check("Sanfte Reize note in the pause box", await pg.is_visible('#flashPauseOverlay [data-mbg-out="soft"]'))
        await pg.click("#flashResumeBtn"); await pg.wait_for_timeout(100)
        ok = False
        for _ in range(80):
            if await pg.is_visible("#flashInputPanel"): ok = True; break
            await pg.wait_for_timeout(100)
        if ok:
            key = await pg.evaluate("""() => { const k = document.querySelector('#flashKeypad button'); const r = k.getBoundingClientRect(); const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return h === k || k.contains(h); }""")
            check("Flash keypad stays on top (tappable)", key)
            for scheme in ("light", "dark"):
                await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
                await pg.screenshot(path=f"{SHOTS}/run_flash_keypad_{scheme}.png")
            await pg.emulate_media(color_scheme="light")
        else:
            check("Flash input panel reached", False)
        await pg.evaluate("() => document.getElementById('flashBackBtn').click()"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); m.softStimuli = false; localStorage.setItem('fwmc-master-v1', JSON.stringify(m)); const f = JSON.parse(localStorage.getItem('fwmc-flash-prefs-v1')); f.mbg = {pattern:'aus'}; localStorage.setItem('fwmc-flash-prefs-v1', JSON.stringify(f)); }")

        # ---- Kombi: Flash block with its own background, own setting untouched ----
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Konstant"'); await pg.wait_for_timeout(300)
        await pg.click("#flashAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.click('#flashReady .mbg-group [data-opto-v="streifen"]'); await pg.wait_for_timeout(60)
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        own = (await ls(pg, "fwmc-flash-prefs-v1"))["mbg"]["pattern"]
        check("Kombi capture: own setting stays Aus", own == "aus", own)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(800)
        k1 = await pg.evaluate("() => window.__mbg('flash')")
        check("Kombi block plays with its own stripes", k1["running"] and k1["st"]["pattern"] == "streifen", k1)
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(150)
        check("Kombi pause: only this run", "nur für diesen Durchgang" in await pg.evaluate("() => document.querySelector('#flashPauseOverlay [data-mbg-live]').textContent"))
        await pg.click("#flashPauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(60)
        await pg.click('#flashPauseOverlay .mbg-group [data-opto-v="punkte"]'); await pg.wait_for_timeout(80)
        own = (await ls(pg, "fwmc-flash-prefs-v1"))["mbg"]["pattern"]
        check("Kombi live change never saved", own == "aus" and (await pg.evaluate("() => window.__mbg('flash')"))["st"]["pattern"] == "punkte", own)
        await pg.click("#flashResumeBtn")
        await pg.evaluate("() => document.getElementById('flashBackBtn').click()"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Gleichgewicht: preset carries it, pause box, screenshots ----
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(250)
        await pg.click("#balanceAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.click('#balanceReady .mbg-group [data-opto-v="streifen"]'); await pg.wait_for_timeout(60)
        await pg.click("#balanceReadySaveBtn"); await pg.wait_for_timeout(80)
        await pg.fill("#balanceReadySaveNameInput", "Streifen"); await pg.click("#balanceReadySaveConfirmBtn"); await pg.wait_for_timeout(100)
        saved = await ls(pg, "fwmc-nat-saved-v1")
        check("preset carries the moving background", any((e.get("prefs") or {}).get("mbg", {}).get("pattern") == "streifen" for e in (saved or [])))
        await pg.click('#balanceReady .mbg-group [data-opto-v="aus"]'); await pg.wait_for_timeout(60)
        await pg.click('#balanceReadySavedList .bundle-card, #balanceReadySavedList button >> nth=0'); await pg.wait_for_timeout(700)
        bal = await pg.evaluate("() => window.__mbg('balance')")
        check("preset start runs with stripes", bal["running"] and bal["st"]["pattern"] == "streifen", bal)
        await pg.screenshot(path=f"{SHOTS}/run_balance.png")
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#balancePauseOverlay .mbg-pause summary"); await pg.wait_for_timeout(80)
        await pg.locator("#balancePauseOverlay .mbg-pause").scroll_into_view_if_needed()
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/pause_balance_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        wide = await pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
        check("no sideways scroll", wide)
        await pg.evaluate("() => document.getElementById('balanceBackBtn').click()"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Optodrum: same renderer still moves ----
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(500)
        await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#optoStartBtn"); await pg.wait_for_timeout(600)
        o1 = await pg.evaluate("() => window.__opto()")
        await pg.wait_for_timeout(300)
        o2 = await pg.evaluate("() => window.__opto()")
        check("Optodrum still moves (shared renderer)", o1 and o2 and abs(o2["s"] - o1["s"]) > 5, (o1 and o1["s"], o2 and o2["s"]))
        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
