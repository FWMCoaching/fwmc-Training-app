import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Sofortmengen-Test (Subitizing-Aufgabe): a Test-Bereich entry picked from
# the "Recherche-Backlog: 20 Kandidaten" list. Grounded in subitizing
# (Kaufman, Lord, Reese & Volkmann, 1949) and the FINST/preattentive-
# individuation account (Trick & Pylyshyn, 1994) - a scatter of 1-9
# identical dots flashes briefly, the client taps the matching count on a
# 1-9 keypad. No "Bei Fehler" fail state (trial-block scored like N-Back/
# Flanker/Stroop), reports accuracy%, average RT for the "instant" range
# (≤4 dots) vs. the "counting" range (≥5 dots), and their difference - the
# actual subitizing/counting break this paradigm exists to reveal. No
# background-colour customization (explicitly optional for a Test entry,
# correctly skipped - the dots' plain contrast against the stage IS the
# stimulus, tinting it would undermine the count judgment itself).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("testHome visible:", await pg.is_visible("#testHome"))
        print("Sofortmengen-Test card visible:", await pg.is_visible("#subitizeOpenBtn"))
        await pg.click("#subitizeOpenBtn"); await pg.wait_for_timeout(150)
        print("subitizeReady visible:", await pg.is_visible("#subitizeReady"))

        # "schwer" = shortest flash duration, so a short test window still
        # reliably samples several trials.
        await pg.click('#subitizeDifficultyRow [data-subitize-diff="schwer"]'); await pg.wait_for_timeout(60)
        print("schwer marked active:", "active" in (await pg.get_attribute('#subitizeDifficultyRow [data-subitize-diff="schwer"]', "class") or ""))
        await pg.click("#subitizeReadyStartBtn"); await pg.wait_for_timeout(200)
        print("subitizePlayer visible:", await pg.is_visible("#subitizePlayer"))
        print("progress starts at 0/27:", "0/27" in (await pg.inner_text("#subitizeProgressEl")))
        print("keypad has 9 keys:", await pg.locator(".subitize-key").count() == 9)

        async def wait_for_dot_count(max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                n = await pg.locator(".subitize-dot").count()
                if n > 0:
                    return n
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return 0

        async def wait_for_answer_phase(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                txt = await pg.inner_text("#subitizeHint")
                if txt == "Wie viele?":
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        # --- correct response ---
        count1 = await wait_for_dot_count()
        print("a dot flash (1-9 dots) appeared:", 1 <= count1 <= 9)
        got_answer_phase = await wait_for_answer_phase()
        print("answer phase started after the flash:", got_answer_phase)
        print("dots cleared once answer phase starts:", await pg.locator(".subitize-dot").count() == 0)
        await pg.click(f'.subitize-key:has-text("{count1}")'); await pg.wait_for_timeout(100)
        print("tapped correct key marked correct:", "correct" in (await pg.get_attribute(f'.subitize-key:has-text("{count1}")', "class") or ""))

        # --- wrong response: deliberately tap a different number ---
        # No fixed pre-wait here (there used to be one, wait_for_timeout(1500)):
        # after a correct tap the app waits 700ms, then a random 500-900ms
        # gap before the next flash, which on "schwer" only stays up for
        # 280ms - so the flash can start and end anywhere in a ~1200-1880ms
        # window after the tap. A 1500ms fixed wait landed AFTER that
        # window closed whenever the random gap came out short (~30% of
        # the time - matches the flakiness actually observed), missing the
        # flash entirely. wait_for_dot_count() already polls from right
        # after the tap up to 6s, which safely spans the whole window on
        # its own with no fixed wait needed in front of it.
        count2 = await wait_for_dot_count()
        print("a second dot flash appeared:", 1 <= count2 <= 9)
        await wait_for_answer_phase()
        wrong_n = 1 if count2 != 1 else 2
        await pg.click(f'.subitize-key:has-text("{wrong_n}")'); await pg.wait_for_timeout(100)
        print("deliberately wrong tap marked wrong:", "wrong" in (await pg.get_attribute(f'.subitize-key:has-text("{wrong_n}")', "class") or ""))
        print("hint reveals the true count on a wrong tap:", str(count2) in (await pg.inner_text("#subitizeHint")))

        # --- pause/resume freezes the stage ---
        await pg.click("#subitizePauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#subitizePauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#subitizePauseBtn"))
        progress_paused1 = await pg.inner_text("#subitizeProgressEl")
        await pg.wait_for_timeout(600)
        progress_paused2 = await pg.inner_text("#subitizeProgressEl")
        print("stage genuinely frozen while paused:", progress_paused1 == progress_paused2)
        await pg.click("#subitizeResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#subitizePauseOverlay"))

        # --- this task is self-paced (no answer timeout), so the run only
        # advances as fast as trials are actually tapped - answer two more
        # to clear the 4-resolved-trial threshold for a done-panel summary.
        for _ in range(2):
            c = await wait_for_dot_count()
            await wait_for_answer_phase()
            await pg.click(f'.subitize-key:has-text("{c}")'); await pg.wait_for_timeout(750)

        # --- Beenden mid-run with progress -> done panel with accuracy/RT ---
        await pg.click("#subitizeBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#subitizeDonePanel"))
        summary = await pg.inner_text("#subitizeDoneSummary")
        print("done summary mentions Sofortmengen-Test and % richtig:", "Sofortmengen-Test" in summary and "%" in summary)
        await pg.click("#subitizeDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#subitizeOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#subitizeReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#subitizePauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#subitizePauseBtn"))
        await pg.click("#subitizeBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#subitizeDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty persists across reload ---
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#subitizeOpenBtn"); await pg.wait_for_timeout(150)
        print("difficulty persisted across reload (schwer still active):", "active" in (await pg.get_attribute('#subitizeDifficultyRow [data-subitize-diff="schwer"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
