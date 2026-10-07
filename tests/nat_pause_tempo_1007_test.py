"""Positionen merken: Reizdauer & Co. live in the pause sheet, taps count on
touch-down (Fabian 2026-10-07: "Die Kreise reagieren manchmal, loggen aber
nicht ein"), plus the sibling rows in Blitz-Raster, Flash and MOT.

Run from tests/ with a dev server on :8845."""
import asyncio, json, time
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(ok)
    print(f"{name}: {ok}" + (f"  ({extra})" if extra else ""))


async def open_sub(pg, sub, opener):
    await pg.goto(URL); await pg.wait_for_timeout(400)
    await pg.click(f'#natHome .sub-tab[data-nat-sub="{sub}"]'); await pg.wait_for_timeout(150)
    if opener:
        await pg.click(opener); await pg.wait_for_timeout(200)


async def touch_down(pg, sel, primary=False):
    await pg.evaluate("""([sel, primary]) => {
        const el = document.querySelector(sel);
        const r = el.getBoundingClientRect();
        el.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, pointerType:'touch', pointerId: Math.floor(Math.random()*1e6)+2,
          isPrimary: primary, clientX: r.x + r.width/2, clientY: r.y + r.height/2}));
    }""", [sel, primary])


async def wait_hint(pg, text, timeout=8000):
    t0 = time.time()
    while (time.time() - t0) * 1000 < timeout:
        if text in (await pg.inner_text("#rememberHint")):
            return time.time() - t0
        await pg.wait_for_timeout(50)
    return None


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", has_touch=True)
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---------- Positionen merken, Feste Positionen ----------
        await open_sub(pg, "remember", "#rememberOpenFixed")
        await pg.click('[data-remember-diff="mittel"]'); await pg.wait_for_timeout(80)
        await pg.click('#rememberErrorRow [data-remember-error="reset2"]'); await pg.wait_for_timeout(80)
        await pg.click("#rememberReadyStartBtn")
        await wait_hint(pg, "Jetzt in der richtigen")

        # A touch that never becomes a click (finger slid, second finger on
        # the glass) still counts: pointerdown alone, non-primary pointer.
        await touch_down(pg, '#rememberStage .remember-marker[data-num="1"]')
        await pg.wait_for_timeout(80)
        cls = await pg.get_attribute('#rememberStage .remember-marker[data-num="1"]', "class")
        check("pointerdown alone counts (marker 1 correct)", "correct" in cls, cls)
        scale_before = await pg.evaluate("() => getComputedStyle(document.getElementById('rememberStage')).getPropertyValue('--remember-marker-px')")
        await touch_down(pg, '#rememberStage .remember-marker[data-num="2"]')
        await pg.wait_for_timeout(80)
        check("second finger on a marker counts too (round solved)", "Richtig" in await pg.inner_text("#rememberHint"))
        scale_after = await pg.evaluate("() => getComputedStyle(document.getElementById('rememberStage')).getPropertyValue('--remember-marker-px')")
        check("two fingers on markers never start a pinch", await pg.evaluate("() => !document.getElementById('rememberStage').dataset.pinching") and scale_before == scale_after)
        # release those synthetic pointers so later checks start clean
        await pg.evaluate("() => document.getElementById('rememberStage').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch',pointerId:1,isPrimary:true}))")
        await pg.evaluate("() => document.getElementById('rememberStage').dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerType:'touch',pointerId:1,isPrimary:true}))")

        # A normal mouse/tap click still works and is not counted twice.
        await wait_hint(pg, "Jetzt in der richtigen")
        await pg.click('#rememberStage .remember-marker[data-num="1"]'); await pg.wait_for_timeout(80)
        hint = await pg.inner_text("#rememberHint")
        check("normal click counts once (no false 'falsch')", "falsch" not in hint and "correct" in (await pg.get_attribute('#rememberStage .remember-marker[data-num="1"]', "class")), hint)
        await pg.click('#rememberStage .remember-marker[data-num="2"]')
        await pg.click('#rememberStage .remember-marker[data-num="3"]')
        await wait_hint(pg, "Richtig")

        # Pause: tempo + Bei Fehler
        await wait_hint(pg, "Merken")
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(200)
        check("pause shows Einblenddauer slider", await pg.is_visible("#rememberPauseRevealSlider"))
        check("slider starts at the run's value (1.1)", await pg.input_value("#rememberPauseRevealSlider") == "1.1")
        check("value label shown", (await pg.inner_text("#rememberPauseRevealValue")).strip() != "")
        err_row = '#rememberPauseOverlay [data-pause-choice="remember-error"]'
        prog_row = '#rememberPauseOverlay [data-pause-choice="remember-progress"]'
        check("Bei Fehler row visible (normal mode)", await pg.is_visible(err_row))
        check("Nach Erfolg row hidden (normal mode)", not await pg.is_visible(prog_row))
        check("current error mode marked", "active" in (await pg.get_attribute(err_row + ' [data-pause-val="reset2"]', "class")))
        await pg.fill("#rememberPauseRevealSlider", "3"); await pg.dispatch_event("#rememberPauseRevealSlider", "input")
        await pg.fill("#rememberPauseStepSlider", "0.6"); await pg.dispatch_event("#rememberPauseStepSlider", "input")
        await pg.click(err_row + ' [data-pause-val="stay"]'); await pg.wait_for_timeout(80)
        check("pick marked active", "active" in (await pg.get_attribute(err_row + ' [data-pause-val="stay"]', "class")))
        state = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1') || '{}')")
        check("saved settings untouched", state.get("revealBaseS", 1.1) == 1.1 and state.get("errorMode", "reset2") == "reset2", json.dumps(state))
        await pg.click("#rememberResumeBtn"); await pg.wait_for_timeout(100)
        # finish the current (level 4) round, then time the next reveal (5 numbers: 3 + 3*0.6 = 4.8 s)
        await wait_hint(pg, "Jetzt in der richtigen", 9000)
        for n in range(1, 5):
            await pg.click(f'#rememberStage .remember-marker[data-num="{n}"]')
        await wait_hint(pg, "Merken")
        t = await wait_hint(pg, "Jetzt in der richtigen", 9000)
        check("new Einblenddauer applies from the next round (~4.8 s)", t is not None and t > 4.0, f"{t}")
        # wrong tap -> 'stay'
        await pg.click('#rememberStage .remember-marker[data-num="3"]'); await pg.wait_for_timeout(100)
        check("Bei Fehler from pause applies (nochmal versuchen)", "nochmal versuchen" in await pg.inner_text("#rememberHint"))
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(200)
        if await pg.is_visible(".confirm-sheet button"):
            pass

        # Trainingsmodus: Nach Erfolg instead of Bei Fehler
        await open_sub(pg, "remember", "#rememberOpenTraining")
        await pg.click("#rememberTrainingStartBtn" if await pg.locator("#rememberTrainingStartBtn").count() else "#rememberTrainingReady .start-btn[id$=StartBtn]")
        await pg.wait_for_timeout(300)
        await pg.click("#rememberPauseBtn"); await pg.wait_for_timeout(200)
        check("training: Nach Erfolg visible", await pg.is_visible(prog_row))
        check("training: Bei Fehler hidden", not await pg.is_visible(err_row))
        await pg.screenshot(path="screenshots/nat_pause_remember_training.png")
        await pg.click(prog_row + ' [data-pause-val="0"]')
        check("training: stay-at-number marked", "active" in (await pg.get_attribute(prog_row + ' [data-pause-val="0"]', "class")))

        # ---------- Blitz-Raster ----------
        await open_sub(pg, "blitz", "#blitzOpenBtn")
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#blitzPauseBtn"); await pg.wait_for_timeout(200)
        check("Blitz: Blitzdauer slider in pause", await pg.is_visible("#blitzPauseFlashSlider"))
        check("Blitz: Bei Fehler row in pause", await pg.is_visible('#blitzPauseOverlay [data-pause-choice="blitz-error"]'))
        await pg.screenshot(path="screenshots/nat_pause_blitz.png")
        await pg.fill("#blitzPauseFlashSlider", "2"); await pg.dispatch_event("#blitzPauseFlashSlider", "input")
        check("Blitz: value label follows", "2" in await pg.inner_text("#blitzPauseFlashValue"))

        # ---------- Flash ----------
        await open_sub(pg, "flash", "#flashOpenClimb")
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(200)
        check("Flash: Bei Fehler row in pause", await pg.is_visible('#flashPauseOverlay [data-pause-choice="flash-error"]'))
        # error row sits after the tempo group
        order = await pg.evaluate("() => { const p = document.querySelector('#flashPauseOverlay .pause-panel'); const g=[...p.children]; return g.indexOf(document.getElementById('flashPauseTempoGroup')) < g.indexOf(p.querySelector('[data-pause-choice]')); }")
        check("Flash: error row below the tempo sliders", order)
        await pg.screenshot(path="screenshots/nat_pause_flash.png")

        # ---------- MOT ----------
        await open_sub(pg, "mot", "#motOpenSpeed")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        check("MOT: Bei Fehler row in pause", await pg.is_visible('#motPauseOverlay [data-pause-choice="mot-error"]'))

        # no horizontal overflow in a pause sheet at 375
        await pg.set_viewport_size({"width": 375, "height": 700}); await pg.wait_for_timeout(150)
        over = await pg.evaluate("() => [...document.querySelectorAll('#motPauseOverlay .choice')].some(c => c.scrollWidth > c.clientWidth + 1)")
        check("MOT pause choices fit at 375 px", not over)
        await pg.screenshot(path="screenshots/nat_pause_mot.png")

        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
