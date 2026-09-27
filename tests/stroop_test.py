import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Wortfarben-Test (Stroop-Aufgabe): eighteenth exercise added under the
# autonomous "Test" section. Classic Stroop colour-word task (Stroop, 1935)
# - a colour name ("ROT"/"BLAU"/"GRUEN"/"GELB") is printed in one of four ink
# colours; the client must tap the colour PATCH matching the actual ink
# colour, ignoring the word's meaning. When word and ink agree that's
# "kongruent" (fast); when they conflict that's "inkongruent" (slower, more
# error-prone) - the classic Stroop effect. Fixed 48-trial run, no "Bei
# Fehler"/level progression - reports accuracy % + average congruent/
# incongruent reaction time + the "Stroop-Effekt" instead, same shape as
# Simon's Simon-Effekt / Flanker's Interferenz-Kosten. No background-colour
# customization (explicitly optional, correctly skipped). The four response
# buttons are plain colour swatches with no text label (a deliberate design
# choice, see CLAUDE.md).

# Fixed hex ink colours (styles.css/app.js STROOP_COLORS), and their RGB
# equivalents as inline styles normalize to in a headless Chromium page.
COLOR_HEX_TO_KEY = {
    "rgb(214, 55, 60)": "rot",
    "rgb(47, 111, 237)": "blau",
    "rgb(31, 157, 85)": "gruen",
    "rgb(224, 163, 0)": "gelb",
}

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
        print("Stroop card visible:", await pg.is_visible("#stroopOpenBtn"))
        await pg.click("#stroopOpenBtn"); await pg.wait_for_timeout(150)
        print("stroopReady visible:", await pg.is_visible("#stroopReady"))

        # "schwer" = shortest response window/ISI, so a short test window
        # still reliably samples several trials, including a timeout.
        await pg.click('#stroopDifficultyRow [data-stroop-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#stroopReadyStartBtn"); await pg.wait_for_timeout(200)
        print("stroopPlayer visible:", await pg.is_visible("#stroopPlayer"))
        print("four colour-swatch response buttons present:", await pg.locator("#stroopResponseRow [data-stroop-color]").count() == 4)
        progress = await pg.inner_text("#stroopProgressEl")
        print("progress starts at 0/48:", "0/48" in progress)

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#stroopProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_word(max_ms=3000, poll_ms=15):
            waited = 0
            while waited < max_ms:
                text = (await pg.inner_text("#stroopWord")).strip()
                if text:
                    color = await pg.eval_on_selector("#stroopWord", "el => el.style.color")
                    ink_key = COLOR_HEX_TO_KEY.get(color)
                    return text, ink_key
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None, None

        # --- trial 1: word appears, tap the CORRECT ink-colour swatch ---
        progress = await wait_for_progress_change(progress)
        word1, ink1 = await wait_for_word()
        print("trial 1's word appeared with a readable ink colour:", word1 is not None and ink1 is not None)
        correct_sel1 = f'#stroopResponseRow [data-stroop-color="{ink1}"]'
        await pg.click(correct_sel1); await pg.wait_for_timeout(80)
        print("tapping the matching-ink swatch marks it 'correct':", "correct" in (await pg.get_attribute(correct_sel1, "class") or ""))

        # --- trial 2: deliberately tap a WRONG colour swatch ---
        progress = await wait_for_progress_change(progress)
        word2, ink2 = await wait_for_word()
        print("trial 2's word appeared:", word2 is not None)
        wrong_key2 = next(k for k in ["rot", "blau", "gruen", "gelb"] if k != ink2)
        wrong_sel2 = f'#stroopResponseRow [data-stroop-color="{wrong_key2}"]'
        await pg.click(wrong_sel2); await pg.wait_for_timeout(80)
        print("tapping a wrong swatch marks it 'wrong':", "wrong" in (await pg.get_attribute(wrong_sel2, "class") or ""))
        print("a wrong tap shows the 'Falsche Farbe!' hint:", "Falsche" in (await pg.inner_text("#stroopHint")))

        # --- trial 3: let its response window fully elapse without tapping (timeout) ---
        progress = await wait_for_progress_change(progress)
        word3, ink3 = await wait_for_word()
        print("trial 3's word appeared:", word3 is not None)
        progress4 = await wait_for_progress_change(progress)
        print("an unanswered trial times out and advances progress on its own:", progress4 != progress)
        print("a timed-out trial shows the 'Verpasst!' hint:", "Verpasst" in (await pg.inner_text("#stroopHint")))
        progress = progress4

        # --- pause/resume freezes the stage ---
        await wait_for_word()
        await pg.click("#stroopPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#stroopPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#stroopPauseBtn"))
        html_paused1 = await pg.inner_html("#stroopStage")
        progress_paused1 = await pg.inner_text("#stroopProgressEl")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#stroopStage")
        progress_paused2 = await pg.inner_text("#stroopProgressEl")
        print("stage genuinely frozen while paused:", html_paused1 == html_paused2 and progress_paused1 == progress_paused2)
        await pg.click("#stroopResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#stroopPauseOverlay"))

        # --- Beenden mid-run with progress -> done panel with accuracy% ---
        await pg.wait_for_timeout(2500)
        await pg.click("#stroopBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#stroopDonePanel"))
        summary = await pg.inner_text("#stroopDoneSummary")
        print("done summary mentions Wortfarben-Test and % richtig:", "Wortfarben-Test" in summary and "%" in summary)
        await pg.click("#stroopDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel (same convention as Simon/Flanker) ---
        await pg.click("#stroopOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#stroopReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#stroopPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#stroopPauseBtn"))
        await pg.click("#stroopBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#stroopDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#stroopOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#stroopDifficultyRow [data-stroop-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#stroopOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#stroopDifficultyRow [data-stroop-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
