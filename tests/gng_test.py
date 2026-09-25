import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Go/No-Go Reaktionstest: the first exercise added under the autonomous
# "Test" section. Classic inhibitory-control paradigm - a series of single
# stimuli, most demanding a fast tap ("Go", green), a minority (~20%,
# GNG_NOGO_RATIO) demanding the tap be withheld ("No-Go", red). Fixed
# 24-trial run (GNG_TRIAL_COUNT), no "Bei Fehler"/level progression like
# Remember/Blitz/Flash/MOT - this task reports accuracy % + average
# reaction time instead, which is the actual outcome measure for this
# paradigm. No background-colour customization (explicitly optional for a
# Test exercise, correctly skipped here - nothing to configure on a task
# whose whole point is a plain green/red circle).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("testHome visible:", await pg.is_visible("#testHome"))
        print("empty hint hidden now that a real exercise exists:", await pg.is_hidden("#testEmptyHint"))
        print("Go/No-Go card visible:", await pg.is_visible("#gngOpenBtn"))
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        print("gngReady visible:", await pg.is_visible("#gngReady"))

        # "schwer" = shortest ISI/stimulus duration, so a short test window
        # still reliably samples several trials (needed to actually observe
        # a No-Go trial, ~20% of 24 total).
        await pg.click('#gngDifficultyRow [data-gng-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#gngReadyStartBtn"); await pg.wait_for_timeout(200)
        print("gngPlayer visible:", await pg.is_visible("#gngPlayer"))
        print("progress starts at 0/24:", "0/24" in (await pg.inner_text("#gngProgressEl")))

        async def wait_for_class(token, max_ms=25000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cls = (await pg.get_attribute("#gngStimulus", "class") or "").split()
                if token in cls:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- correct Go response ---
        got_go = await wait_for_class("go")
        if got_go:
            await pg.click("#gngStage")
        print("a Go (green) stimulus appeared and was tapped:", got_go)
        await pg.wait_for_timeout(120)
        print("stimulus marked hit on a correct tap:", "hit" in (await pg.get_attribute("#gngStimulus", "class") or ""))

        # --- correct inhibition: a No-Go trial appears, deliberately not tapped ---
        got_nogo = await wait_for_class("nogo")
        print("a No-Go (red) stimulus appeared within the sampling window:", got_nogo)
        if got_nogo:
            cls_before = await pg.get_attribute("#gngStimulus", "class")
            await pg.wait_for_timeout(150)
            print("not tapping a No-Go stimulus leaves it unmarked (no 'wrong' class):", "wrong" not in (await pg.get_attribute("#gngStimulus", "class") or ""))

        # --- pause/resume freezes the stage ---
        await pg.click("#gngPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#gngPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#gngPauseBtn"))
        cls_paused1 = await pg.get_attribute("#gngStimulus", "class")
        await pg.wait_for_timeout(600)
        cls_paused2 = await pg.get_attribute("#gngStimulus", "class")
        print("stage genuinely frozen while paused:", cls_paused1 == cls_paused2)
        await pg.click("#gngResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#gngPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy/RT ---
        await pg.wait_for_timeout(2500)
        await pg.click("#gngBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#gngDonePanel"))
        summary = await pg.inner_text("#gngDoneSummary")
        print("done summary mentions Go/No-Go and % richtig:", "Go/No-Go" in summary and "%" in summary)
        await pg.click("#gngDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as Blitz/MOT) ---
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#gngPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#gngPauseBtn"))
        await pg.click("#gngBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#gngDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
