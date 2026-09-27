import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Blockspanne-Test (Corsi Block-Tapping Task): fourteenth exercise added
# under the autonomous "Test" section. Grounded in the Corsi block-tapping
# task (Corsi, 1972; standardised in Kessels et al., 2000) - nine scattered
# blocks, a subset lights up ONE AT A TIME in a specific order, the client
# then taps the same blocks back in the SAME ORDER. Correct recall -> the
# sequence grows by one block; a wrong tap ends the run and reports the
# longest sequence recalled ("Blockspanne"). Single-trial-per-length
# adaptive climb (no client-set level), same "no Bei-Fehler, the climb IS
# the difficulty" shape as N-Back/Hick.
# Background colour/intensity (added later, fifth batch of the same
# Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/Rotation/
# Merkspanne/Simon/Suchtest/Doppelziel/Antizip - see CLAUDE.md's Established
# patterns for the scope decision, minus their transfer/preset-save
# machinery) tints the outer #corsiStage. Both the ready screen and the
# pause overlay have their own live picker+slider sharing the same
# corsiPrefs.

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
        print("Blockspanne-Test card visible:", await pg.is_visible("#corsiOpenBtn"))
        await pg.click("#corsiOpenBtn"); await pg.wait_for_timeout(150)
        print("corsiReady visible:", await pg.is_visible("#corsiReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#corsiAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#corsiBgColorPicker .color-swatch").count())
        await pg.click('#corsiBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#corsiBgIntensitySlider", "0.6"); await pg.dispatch_event("#corsiBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#corsiBgIntensityValue")))

        # "schwer" = fastest flashes (500ms lit / 250ms gap), so the run
        # advances through several sequence lengths quickly in a test.
        await pg.click('#corsiDifficultyRow [data-corsi-difficulty="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#corsiReadyStartBtn"); await pg.wait_for_timeout(200)
        print("corsiPlayer visible:", await pg.is_visible("#corsiPlayer"))
        print("board renders exactly 9 blocks:", await pg.locator("#corsiBoard .corsi-block").count() == 9)
        progress = await pg.inner_text("#corsiProgressEl")
        print("progress starts at Länge 2:", "2" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('corsiStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def wait_for_hint_contains(text, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#corsiHint")
                if text in cur:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_lit_index(max_ms=3000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                idx = await pg.eval_on_selector_all("#corsiBoard .corsi-block", "(els) => els.findIndex(e => e.classList.contains('lit'))")
                if idx >= 0:
                    return idx
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return -1

        async def wait_for_responding(max_ms=6000, poll_ms=25):
            return await wait_for_hint_contains("Jetzt in der gleichen Reihenfolge", max_ms, poll_ms)

        # --- observe the first (length-2) sequence flash, in order ---
        merken_shown = await wait_for_hint_contains("Merken")
        print("'Merken' hint shown before the sequence flashes:", merken_shown)
        seq = []
        for _ in range(2):
            idx = await wait_for_lit_index()
            seq.append(idx)
            # wait for it to go dark again before the next one lights up
            waited = 0
            while waited < 2000:
                still_lit = await pg.eval_on_selector_all("#corsiBoard .corsi-block", "(els) => els.some(e => e.classList.contains('lit'))")
                if not still_lit:
                    break
                await pg.wait_for_timeout(20); waited += 20
        print("two distinct blocks flashed for the length-2 sequence:", len(set(seq)) == 2 and -1 not in seq)

        responding = await wait_for_responding()
        print("'Jetzt antippen' hint shown once the sequence finished flashing:", responding)

        # --- tap the sequence back correctly -> span advances to 3 ---
        for i in seq:
            await pg.locator("#corsiBoard .corsi-block").nth(i).click()
            await pg.wait_for_timeout(80)
        print("last correct tap marks its block 'correct':",
              "correct" in (await pg.locator("#corsiBoard .corsi-block").nth(seq[-1]).get_attribute("class") or ""))
        progress = await wait_for_hint_contains("Merken", 3000)
        progress_text = await pg.inner_text("#corsiProgressEl")
        print("progress advances to Länge 3 after a correct recall:", "3" in progress_text)

        # --- observe and correctly recall the length-3 sequence too, so the best-score / done-panel checks below have real progress (span >= 3) ---
        seq3 = []
        for _ in range(3):
            idx = await wait_for_lit_index()
            seq3.append(idx)
            waited = 0
            while waited < 2000:
                still_lit = await pg.eval_on_selector_all("#corsiBoard .corsi-block", "(els) => els.some(e => e.classList.contains('lit'))")
                if not still_lit:
                    break
                await pg.wait_for_timeout(20); waited += 20
        await wait_for_responding()
        for i in seq3:
            await pg.locator("#corsiBoard .corsi-block").nth(i).click()
            await pg.wait_for_timeout(80)
        await wait_for_hint_contains("Merken", 3000)
        progress_text2 = await pg.inner_text("#corsiProgressEl")
        print("progress advances to Länge 4 after a second correct recall:", "4" in progress_text2)

        # --- pause/resume freezes the board mid-flash ---
        await wait_for_lit_index()
        await pg.click("#corsiPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#corsiPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#corsiPauseBtn"))
        html_paused1 = await pg.inner_html("#corsiBoard")
        await pg.wait_for_timeout(700)
        html_paused2 = await pg.inner_html("#corsiBoard")
        print("board genuinely frozen while paused:", html_paused1 == html_paused2)
        await pg.click('#corsiPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('corsiStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#corsiResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#corsiPauseOverlay"))

        # --- fail the length-4 sequence on purpose (tap a block that's
        # definitely NOT first in the sequence) to reach the done panel ---
        await wait_for_responding(max_ms=8000)
        seq4_first = await pg.eval_on_selector_all("#corsiBoard .corsi-block", "() => null") or None
        # tap block 0 or 1, whichever isn't the actual first-expected one is
        # unknown to us here, so just tap ALL blocks in a fixed order until
        # one registers wrong (a correct one just advances tapIndex, which is
        # harmless) - simplest: tap every block 0..8 in order, guaranteeing a
        # mismatch appears well before block 8 for a length-4 sequence.
        wrong_seen = False
        for i in range(9):
            await pg.locator("#corsiBoard .corsi-block").nth(i).click()
            await pg.wait_for_timeout(100)
            cls = await pg.locator("#corsiBoard .corsi-block").nth(i).get_attribute("class") or ""
            if "wrong" in cls:
                wrong_seen = True
                break
            if await pg.is_visible("#corsiDonePanel"):
                break
        print("a wrong tap eventually ends the run:", wrong_seen or await pg.is_visible("#corsiDonePanel"))

        done_shown = await wait_for_hint_contains("Leider daneben", 2000) or await pg.is_visible("#corsiDonePanel")
        await pg.wait_for_timeout(1600)
        print("done panel visible after failing a sequence:", await pg.is_visible("#corsiDonePanel"))
        summary = await pg.inner_text("#corsiDoneSummary")
        print("done summary mentions Blockspanne-Test and erreichte Länge:", "Blockspanne-Test" in summary and "Blockspanne erreicht" in summary)
        print("done summary reports a span of at least 3:", any(f"erreicht: {n}" in summary for n in (3, 4, 5, 6, 7, 8, 9)))
        await pg.click("#corsiDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run quit immediately (Beenden with zero progress) skips the done panel ---
        await pg.click("#corsiOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#corsiReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#corsiPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#corsiPauseBtn"))
        await pg.click("#corsiBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#corsiDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#corsiOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#corsiDifficultyRow [data-corsi-difficulty="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#corsiOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#corsiDifficultyRow [data-corsi-difficulty="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
