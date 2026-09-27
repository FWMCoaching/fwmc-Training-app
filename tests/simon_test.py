import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Farbkonflikt-Test (Simon-Aufgabe): ninth exercise added under the autonomous
# "Test" section. Classic Simon task (Simon & Rudell, 1967) - a coloured dot
# (blue or orange) appears in a left or right slot; the client must tap the
# FIXED-position button matching the dot's COLOUR (Blau=links, Orange=rechts,
# never changes during a run), ignoring which slot the dot appeared in. When
# the dot's slot side happens to match its colour's button side that's
# "congruent" (fast); when it doesn't, that's "incongruent" (slower, more
# error-prone) - the classic Simon effect. Fixed 40-trial run
# (SIMON_TRIAL_COUNT), no "Bei Fehler"/level progression - reports accuracy %
# + average congruent/incongruent reaction time + the "Simon-Effekt" instead,
# same shape as Flanker's Interferenz-Kosten / Posner's Umlenkungs-Kosten. No
# background-colour customization (explicitly optional, correctly skipped).
#
# Timing note: like Flanker/Posner, the feedback ring on a tapped button
# stays up for the rest of diff.responseMs regardless of how fast the client
# answers, so "a new trial started" is only reliably detected via the
# progress counter advancing, not via the dot simply reappearing.

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
        print("Simon card visible:", await pg.is_visible("#simonOpenBtn"))
        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        print("simonReady visible:", await pg.is_visible("#simonReady"))

        # "schwer" = shortest response window/ISI, so a short test window
        # still reliably samples several trials, including a timeout.
        await pg.click('#simonDifficultyRow [data-simon-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#simonReadyStartBtn"); await pg.wait_for_timeout(200)
        print("simonPlayer visible:", await pg.is_visible("#simonPlayer"))
        print("fixed response buttons show Blau/Orange:", "Blau" in (await pg.inner_text("#simonLeftBtn")) and "Orange" in (await pg.inner_text("#simonRightBtn")))
        progress = await pg.inner_text("#simonProgressEl")
        print("progress starts at 0/40:", "0/40" in progress)

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#simonProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_dot(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                if await pg.locator(".simon-dot.show").count() == 1:
                    cls_left = await pg.get_attribute("#simonDotLeft", "class") or ""
                    cls_right = await pg.get_attribute("#simonDotRight", "class") or ""
                    side = "left" if "show" in cls_left else "right"
                    cls = cls_left if side == "left" else cls_right
                    color = "blue" if "simon-dot-blue" in cls else "orange"
                    return side, color
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None, None

        # --- trial 1: dot appears, tap the CORRECT colour button ---
        progress = await wait_for_progress_change(progress)
        side1, color1 = await wait_for_dot()
        print("trial 1's dot appeared with a side and a colour:", side1 is not None and color1 is not None)
        correct_btn1 = "#simonLeftBtn" if color1 == "blue" else "#simonRightBtn"
        await pg.click(correct_btn1); await pg.wait_for_timeout(80)
        print("tapping the matching-colour button marks it 'correct':", "correct" in (await pg.get_attribute(correct_btn1, "class") or ""))

        # --- trial 2: deliberately tap the WRONG colour button ---
        progress = await wait_for_progress_change(progress)
        side2, color2 = await wait_for_dot()
        print("trial 2's dot appeared:", side2 is not None)
        wrong_btn2 = "#simonRightBtn" if color2 == "blue" else "#simonLeftBtn"
        await pg.click(wrong_btn2); await pg.wait_for_timeout(80)
        print("tapping the wrong-colour button marks it 'wrong':", "wrong" in (await pg.get_attribute(wrong_btn2, "class") or ""))
        print("a wrong tap shows the 'Falsche Farbe!' hint:", "Falsche" in (await pg.inner_text("#simonHint")))

        # --- trial 3: let its response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        side3, color3 = await wait_for_dot()
        print("trial 3's dot appeared:", side3 is not None)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#simonHint")))
        progress = progress4

        # --- pause/resume freezes the stage ---
        await wait_for_dot()
        await pg.click("#simonPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#simonPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#simonPauseBtn"))
        html_paused1 = await pg.inner_html("#simonStage")
        progress_paused1 = await pg.inner_text("#simonProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#simonStage")
        progress_paused2 = await pg.inner_text("#simonProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click("#simonResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#simonPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy% ---
        await pg.wait_for_timeout(2500)
        await pg.click("#simonBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#simonDonePanel"))
        summary = await pg.inner_text("#simonDoneSummary")
        print("done summary mentions Farbkonflikt-Test and % richtig:", "Farbkonflikt-Test" in summary and "%" in summary)
        await pg.click("#simonDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as Flanker/Posner) ---
        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#simonReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#simonPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#simonPauseBtn"))
        await pg.click("#simonBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#simonDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#simonDifficultyRow [data-simon-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#simonDifficultyRow [data-simon-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
