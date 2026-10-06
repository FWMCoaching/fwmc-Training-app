import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=nat"

# "Größe während der Übung" (Fabian 2026-10-06): Positionen merken, Flash
# and MOT get the size slider in their "Pausiert" sheet plus pinch
# (ctrl+wheel here). Standalone runs save the value; it applies at once
# (Flash: the current/next character, MOT: the moving objects, Positionen
# merken: the markers, capped so they never overlap).

INIT = """
localStorage.setItem('fwmc-tips-seen','true');
localStorage.setItem('fwmc-test-natmodes','true');
localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));
"""

def ok(label, cond, fails):
    print(label + ":", bool(cond))
    if not cond: fails.append(label)

async def set_live(pg, overlay, v):
    await pg.evaluate("""([o, v]) => { const s = document.querySelector('#' + o + ' [data-live-look] input'); s.value = v; s.dispatchEvent(new Event('input')); }""", [overlay, v])

async def main():
    errors, fails = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- MOT ----
        await pg.click('#natHome .nat-tile[data-nat-ex="mot"]'); await pg.wait_for_timeout(200)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(900)
        w0 = await pg.evaluate("() => document.querySelector('.mot-object').getBoundingClientRect().width")
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(150)
        ok("MOT: size slider visible in the pause sheet", await pg.locator('#motPauseOverlay [data-live-look="mot"] input').is_visible(), fails)
        await set_live(pg, "motPauseOverlay", "1.5"); await pg.wait_for_timeout(80)
        w1 = await pg.evaluate("() => document.querySelector('.mot-object').getBoundingClientRect().width")
        saved = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')).objScale")
        ok("MOT: objects grow at once and the value is saved", w1 > w0 and abs(saved - 1.5) < 0.01, fails)
        await pg.click("#motResumeBtn") if await pg.locator("#motResumeBtn").count() else None
        await pg.evaluate("() => { const b = document.getElementById('motBackBtn'); b.click(); }"); await pg.wait_for_timeout(300)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- Flash ----
        await pg.click('#natHome .nat-tile[data-nat-ex="flash"]'); await pg.wait_for_timeout(200)
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        box = await pg.locator("#flashStage").bounding_box()
        await pg.mouse.move(box["x"] + 100, box["y"] + 400)
        await pg.keyboard.down("Control"); await pg.mouse.wheel(0, -100); await pg.keyboard.up("Control")
        await pg.wait_for_timeout(120)
        cs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-flash-prefs-v1')).charScale")
        ok("Flash: pinch (ctrl+wheel) enlarges the characters and saves", cs > 1.05, fails)
        ok("Flash: size toast shown", await pg.locator("#flashStage .look-toast").is_visible(), fails)
        await pg.evaluate("() => document.getElementById('flashBackBtn').click()"); await pg.wait_for_timeout(300)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- Positionen merken ----
        await pg.click('#natHome .nat-tile[data-nat-ex="remember"]'); await pg.wait_for_timeout(200)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(500)
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(150)
        await set_live(pg, "rememberPauseOverlay", "1.6"); await pg.wait_for_timeout(80)
        res = await pg.evaluate("""() => { const m = [...document.querySelectorAll('.remember-marker')].map((e) => e.getBoundingClientRect());
            let minGap = Infinity; for (let i = 0; i < m.length; i++) for (let j = i + 1; j < m.length; j++) {
              const a = m[i], c = m[j]; const d = Math.hypot((a.left + a.width / 2) - (c.left + c.width / 2), (a.top + a.height / 2) - (c.top + c.height / 2)); minGap = Math.min(minGap, d - a.width); }
            return { w: m[0] ? m[0].width : 0, minGap, saved: JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')).markerScale }; }""")
        ok("Positionen merken: value saved", abs(res["saved"] - 1.6) < 0.01, fails)
        ok("Positionen merken: markers never overlap after growing", res["minGap"] >= 0, fails)
        await ctx.close()
        await b.close()
    print("failures:", fails)
    print("FINAL ERRORS:", errors)

asyncio.run(main())
