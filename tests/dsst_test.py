import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Zeichen-Zuordnungs-Test: twenty-third exercise added under the autonomous
# "Test" section, picked from the Recherche-Backlog (candidate #9, Digit
# Symbol Substitution Test / DSST - the "Coding" subtest of the Wechsler
# Adult Intelligence Scale). A fresh, randomly-shuffled digit->symbol key
# (9 digits, 9 simple geometric symbols) is generated per run and stays
# visible the whole time; a random digit 1-9 is shown, the client taps the
# matching symbol from a keypad in the same left-to-right order as the key
# row. Runs continuously for a fixed duration (kurz/mittel/lang), self-
# paced per trial (no per-item timeout - the real test races the OVERALL
# clock, not each item). Reports total correct substitutions (the DSST's
# own standard score), accuracy%, and a wrong-tap count.

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
        print("DSST card visible:", await pg.is_visible("#dsstOpenBtn"))
        await pg.click("#dsstOpenBtn"); await pg.wait_for_timeout(150)
        print("dsstReady visible:", await pg.is_visible("#dsstReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#dsstAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#dsstBgColorPicker .color-swatch").count())
        await pg.click('#dsstBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        await pg.fill("#dsstBgIntensitySlider", "0.5"); await pg.dispatch_event("#dsstBgIntensitySlider", "input")
        print("intensity value label updated:", "50 %" in (await pg.inner_text("#dsstBgIntensityValue")))

        await pg.click('#dsstLengthRow [data-dsst-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#dsstLengthRow [data-dsst-length="kurz"]', "class") or ""))
        await pg.click("#dsstReadyStartBtn"); await pg.wait_for_timeout(200)
        print("dsstPlayer visible:", await pg.is_visible("#dsstPlayer"))
        print("progress starts at 0 richtig:", "0 richtig" in (await pg.inner_text("#dsstProgressEl")))
        print("key row has 9 cells:", await pg.locator(".dsst-key-cell").count() == 9)
        print("keypad has 9 keys:", await pg.locator(".dsst-key").count() == 9)
        bg_at_start = await pg.evaluate("() => document.getElementById('dsstStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        async def current_digit():
            return int(await pg.inner_text("#dsstDigit"))

        async def key_symbols():
            return await pg.locator(".dsst-key-symbol").all_inner_texts()

        async def keypad_symbols():
            return await pg.locator(".dsst-key").all_inner_texts()

        keys = await key_symbols()
        pad = await keypad_symbols()
        print("keypad order matches key row order:", keys == pad)

        # --- trial 1: correct tap ---
        d1 = await current_digit()
        print("a digit 1-9 is shown:", 1 <= d1 <= 9)
        await pg.click(f'.dsst-key >> nth={d1 - 1}'); await pg.wait_for_timeout(60)
        print("tapping the correct symbol marks it 'correct':", "correct" in (await pg.get_attribute(f'.dsst-key >> nth={d1 - 1}', "class") or ""))
        print("progress updates to 1 richtig:", "1 richtig" in (await pg.inner_text("#dsstProgressEl")))
        await pg.wait_for_timeout(350)  # let the feedback pause elapse before the next trial

        # --- trial 2: deliberately wrong tap ---
        d2 = await current_digit()
        wrong_idx = 0 if d2 - 1 != 0 else 1
        await pg.click(f'.dsst-key >> nth={wrong_idx}'); await pg.wait_for_timeout(60)
        print("tapping the wrong symbol marks it 'wrong':", "wrong" in (await pg.get_attribute(f'.dsst-key >> nth={wrong_idx}', "class") or ""))
        await pg.wait_for_timeout(350)
        print("feedback classes clear before the next digit:", "correct" not in (await pg.get_attribute(f'.dsst-key >> nth={wrong_idx}', "class") or "") and "wrong" not in (await pg.get_attribute(f'.dsst-key >> nth={wrong_idx}', "class") or ""))

        # --- two more correct taps to clear the resolved>=4 threshold ---
        for _ in range(2):
            d = await current_digit()
            await pg.click(f'.dsst-key >> nth={d - 1}'); await pg.wait_for_timeout(350)

        # --- pause/resume freezes the stage ---
        await pg.click("#dsstPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#dsstPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#dsstPauseBtn"))
        digit_paused1 = await pg.inner_text("#dsstDigit")
        progress_paused1 = await pg.inner_text("#dsstProgressEl")
        await pg.wait_for_timeout(700)
        digit_paused2 = await pg.inner_text("#dsstDigit")
        progress_paused2 = await pg.inner_text("#dsstProgressEl")
        print("stage genuinely frozen while paused:", digit_paused1 == digit_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#dsstPauseBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('dsstStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#dsstResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#dsstPauseOverlay"))
        # taps still work after resume
        d = await current_digit()
        await pg.click(f'.dsst-key >> nth={d - 1}'); await pg.wait_for_timeout(150)

        # --- Beenden mid-run with progress -> done panel with correct count/accuracy ---
        await pg.click("#dsstBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#dsstDonePanel"))
        summary = await pg.inner_text("#dsstDoneSummary")
        print("done summary mentions Zeichen-Zuordnungs-Test and richtige Zuordnungen:", "Zeichen-Zuordnungs-Test" in summary and "richtige Zuordnungen" in summary)
        await pg.click("#dsstDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#dsstOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#dsstReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#dsstPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#dsstPauseBtn"))
        await pg.click("#dsstBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#dsstDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- length selection persists across reload ---
        await pg.click("#dsstOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#dsstLengthRow [data-dsst-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#dsstOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#dsstLengthRow [data-dsst-length="lang"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
