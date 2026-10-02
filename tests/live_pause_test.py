import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Audit point 20 (Fabian, 2026-10-02): pause with live adjustment for every
# Visual-Training exercise (tempo, background, fixation point), Atemtraining
# (tempo, remaining duration, spoken cues) and Movement (BPM, preview).


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---------- Visual Training: 4 Pfeile gerade ----------
        await pg.evaluate("""() => {
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}');
            raw.stimulusS = 1; raw.intervalMin = 1; raw.intervalMax = 1; raw.duration = 60;
            localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(4200)
        print("VT: pause button visible for an arrow exercise:", await pg.is_visible("#periphPauseBtn"))
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        print("VT: pause overlay open:", await pg.is_visible("#periphPauseOverlay"))
        print("VT: tempo group shown:", await pg.is_visible("#vtPauseTempoGroup"))
        print("VT: background group shown (bg not the stimulus):", await pg.is_visible("#vtPauseBgColorGroup"))
        print("VT: stimulus colour group hidden (not Periph):", await pg.is_hidden("#vtPauseStimColorGroup"))
        t_before = await pg.inner_text("#timeEl")
        await pg.fill("#vtPauseStimulusSlider", "2.5"); await pg.dispatch_event("#vtPauseStimulusSlider", "input")
        await pg.fill("#vtPauseIntervalMinSlider", "5"); await pg.dispatch_event("#vtPauseIntervalMinSlider", "input")
        await pg.fill("#vtPauseIntervalMaxSlider", "6"); await pg.dispatch_event("#vtPauseIntervalMaxSlider", "input")
        print("VT: tempo values shown:", await pg.inner_text("#vtPauseStimulusValue"), await pg.inner_text("#vtPauseIntervalValue"))
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(200)
        t_after = await pg.inner_text("#timeEl")
        print("VT: resume continues near the paused time:", t_before, t_after)
        # New tempo in effect: sample whether an arrow is drawn (a dark pixel
        # anywhere on a scan across the canvas) and count how many separate
        # cues appear in 8 s. Old tempo (1 s + 1 s) would give ~4, the new one
        # (2.5 s + 5-6 s) at most 2.
        onsets, prev = 0, False
        for _ in range(80):
            drawn = await pg.evaluate("""() => {
                const c = document.getElementById('stage'), x = c.getContext('2d');
                const d = x.getImageData(0, Math.floor(c.height / 2) - 2, c.width, 4).data;
                let n = 0;
                for (let i = 0; i < d.length; i += 4) if (d[i] + d[i+1] + d[i+2] < 600) n++;
                return n > c.width * 4 * 0.12; // an arrow, not just the small fixation point
            }""")
            if drawn and not prev:
                onsets += 1
            prev = drawn
            await pg.wait_for_timeout(100)
        print("VT: new slower tempo in effect (at most 2 cues in 8 s):", onsets, 1 <= onsets <= 2)
        print("VT: exercise still running after tempo change:", await pg.is_visible("#player"))
        stored = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3')).stimulusS")
        print("VT: standalone tempo change saved to the client's settings:", stored == 2.5)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)

        # VT colour exercise whose background IS the stimulus: no bg group
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(600)
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(150)
        print("VT-Farbe: background groups hidden:", await pg.is_hidden("#vtPauseBgColorGroup") and await pg.is_hidden("#vtPauseBgIntensityGroup"))
        print("VT-Farbe: tempo group shown:", await pg.is_visible("#vtPauseTempoGroup"))
        # change tempo during the countdown -> whole schedule rebuilt, no error
        await pg.fill("#vtPauseStimulusSlider", "0.5"); await pg.dispatch_event("#vtPauseStimulusSlider", "input")
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(4000)
        print("VT-Farbe: runs on after a change during the countdown:", await pg.is_visible("#player"))

        # Hütchen sortieren: no pause button
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="cone-tap"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(400)
        print("Hütchen sortieren: no pause button:", await pg.is_hidden("#periphPauseBtn"))

        # ---------- Atemtraining ----------
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .featured-card").nth(1).click(); await pg.wait_for_timeout(200)  # Box
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(1500)
        await pg.click("#breathPauseBtn"); await pg.wait_for_timeout(200)
        print("Atem: pause sheet open:", await pg.is_visible("#breathPauseOverlay"))
        print("Atem: label says Pausiert:", await pg.inner_text("#breathPhaseLabel") == "Pausiert")
        t1 = await pg.inner_text("#breathTimeEl"); await pg.wait_for_timeout(1200)
        print("Atem: timer frozen while paused:", t1 == await pg.inner_text("#breathTimeEl"))
        phases_before = await pg.inner_text("#breathPausePhases")
        await pg.fill("#breathPauseTempoSlider", "1.5"); await pg.dispatch_event("#breathPauseTempoSlider", "input")
        phases_after = await pg.inner_text("#breathPausePhases")
        print("Atem: phase preview follows the tempo:", phases_before, "->", phases_after, phases_before != phases_after and "6 s" in phases_after)
        await pg.fill("#breathPauseRestSlider", "2"); await pg.dispatch_event("#breathPauseRestSlider", "input")
        await pg.click('[data-breath-pause-sound="off"]')
        await pg.click("#breathResumeBtn"); await pg.wait_for_timeout(500)
        print("Atem: sheet closed after Weiter:", await pg.is_hidden("#breathPauseOverlay"))
        rest = await pg.inner_text("#breathTimeEl")
        print("Atem: remaining time follows the new duration (~2 min):", rest, rest.startswith("1:") or rest.startswith("2:"))
        print("Atem: count shows a fresh 6 s inhale:", await pg.inner_text("#breathPhaseCount") in ("6", "5"))
        bprefs = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-breath-v1') || 'null')")
        print("Atem: client's own sound setting untouched:", bprefs is None or bprefs.get("sound") is not False)
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)

        # ---------- Movement ----------
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="movement"]'); await pg.wait_for_timeout(150)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(150)
        saved_bpm = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}').bpm")
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(800)
        print("Movement: pause button visible:", await pg.is_visible("#movementPauseBtn"))
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(150)
        print("Movement: pause sheet open:", await pg.is_visible("#movementPauseOverlay"))
        tm = await pg.inner_text("#movementTimeEl"); await pg.wait_for_timeout(1200)
        print("Movement: timer frozen while paused:", tm == await pg.inner_text("#movementTimeEl"))
        await pg.fill("#movementPauseBpmSlider", "120"); await pg.dispatch_event("#movementPauseBpmSlider", "input")
        print("Movement: BPM shown:", await pg.inner_text("#movementPauseBpmValue") == "120 BPM")
        await pg.click('[data-mv-pause-preview="4"]')
        await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(300)
        print("Movement: sheet closed after Weiter:", await pg.is_hidden("#movementPauseOverlay"))
        tiles = await pg.locator("#movementLane .movement-tile.next").count()
        print("Movement: preview now shows 3 upcoming tiles:", tiles == 3)
        await pg.wait_for_timeout(1100)
        print("Movement: still running:", await pg.is_visible("#movementPlayer") and await pg.is_hidden("#movementDonePanel"))
        # switch to the whole-programme grid live
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click('[data-mv-pause-preview="all"]')
        await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(300)
        print("Movement: grid layout after switching to Ganz:", "grid" in (await pg.get_attribute("#movementLane", "class") or ""))
        print("Movement: exactly one active tile:", await pg.locator("#movementLane .movement-tile.active").count() == 1)
        bpm_after = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}').bpm")
        print("Movement: client's saved BPM untouched:", bpm_after == saved_bpm)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
