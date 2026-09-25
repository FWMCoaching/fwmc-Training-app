import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

# Flash Speicher Test: a THIRD distinct NAT memory mechanic (explicitly not
# Remember, not Blitz-Raster). Numbers appear one at a time at scattered
# (Periph-style) positions, then an input box opens to type them back IN
# ORDER. Four modes: constant (speeds up), climb (count grows), climbRepeat
# (count grows after N repeats), training (direct start).

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
        await pg.evaluate("() => localStorage.removeItem('fwmc-flash-prefs-v1')")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        print("flash panel visible:", await pg.is_visible("#natFlashPanel"))

        # --- mode-specific field visibility on the shared ready screen ---
        await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(150)
        print("constant: constantGroup visible, start/reps hidden:",
              await pg.is_visible("#flashConstantGroup") and await pg.is_hidden("#flashStartGroup") and await pg.is_hidden("#flashRepsGroup"))
        await pg.click("#flashReadyBackToHome"); await pg.wait_for_timeout(150)

        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimbRepeat"); await pg.wait_for_timeout(150)
        print("climbRepeat: reps+start visible, constant hidden:",
              await pg.is_visible("#flashRepsGroup") and await pg.is_visible("#flashStartGroup") and await pg.is_hidden("#flashConstantGroup"))
        await pg.click("#flashReadyBackToHome"); await pg.wait_for_timeout(150)

        # --- Bereich zero-selection guard ---
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)
        await pg.click("#flashAllBtn"); await pg.wait_for_timeout(80)
        print("start disabled at zero Bereich:", await pg.get_attribute("#flashReadyStartBtn", "disabled") is not None)
        await pg.click("#flashAllBtn"); await pg.wait_for_timeout(80)
        print("start re-enabled:", await pg.get_attribute("#flashReadyStartBtn", "disabled") is None)

        # --- background: swatches + cross-domain transfer sources ---
        await pg.click("#flashAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#flashBgColorPicker .color-swatch").count())
        print("bg source row lists the other three domains:", await pg.locator("#flashBgSourceRow button").all_inner_texts())

        # --- run climb mode: capture the shown sequence, answer correctly ---
        await pg.fill("#flashStimulusSlider", "1.1"); await pg.dispatch_event("#flashStimulusSlider", "input")
        await pg.fill("#flashIntervalSlider", "0.5"); await pg.dispatch_event("#flashIntervalSlider", "input")
        await pg.fill("#flashStartSlider", "3"); await pg.dispatch_event("#flashStartSlider", "input")
        await pg.click("#flashReadyStartBtn")
        print("flashPlayer visible:", await pg.is_visible("#flashPlayer"))
        print("level text:", await pg.inner_text("#flashLevelEl"))

        # Single JS round-trip per poll (rather than 2-3 separate Playwright
        # calls) so a fast digit transition can't slip between polls.
        async def capture_sequence(max_polls=100, poll_ms=40):
            seq, last_txt, was_visible = [], None, False
            for _ in range(max_polls):
                await pg.wait_for_timeout(poll_ms)
                snap = await pg.evaluate("""() => {
                    const panel = document.getElementById('flashInputPanel');
                    const digit = document.getElementById('flashDigitEl');
                    return { inputVisible: !panel.hidden, digitVisible: !digit.hidden, text: digit.textContent };
                }""")
                if snap["inputVisible"]:
                    return seq
                if snap["digitVisible"]:
                    if not was_visible or snap["text"] != last_txt:
                        seq.append(snap["text"]); last_txt = snap["text"]
                    was_visible = True
                else:
                    was_visible = False
            return seq

        seq1 = await capture_sequence()
        print("round1 sequence length matches Startanzahl (3):", len(seq1) == 3)
        await pg.screenshot(path=OUT + "flash_digit.png")
        await pg.type("#flashTypedInput", "".join(seq1))
        await pg.wait_for_timeout(150)
        print("hint after correct entry:", await pg.inner_text("#flashHint"))
        await pg.wait_for_timeout(950)
        print("level advanced to 4 Zahlen:", await pg.inner_text("#flashLevelEl"))

        # Wrong-answer path: rather than re-capturing the flashed sequence
        # (racy under load - the app itself already slices typed input to
        # exactly this many digits before comparing), read the expected
        # length off the level indicator (plain static text, no timing
        # race) and submit a fixed digit repeated that many times. A
        # genuinely random sequence being all-9s is a ~1-in-10000 fluke.
        level_txt = await pg.inner_text("#flashLevelEl")
        expected_len = int(level_txt.split()[0])
        print("round2 expects 4 digits:", expected_len == 4)
        for _ in range(100):  # poll until round2's own flash/gap sequence finishes
            if await pg.is_visible("#flashInputPanel"):
                break
            await pg.wait_for_timeout(80)
        await pg.type("#flashTypedInput", "9" * expected_len)
        await pg.wait_for_timeout(150)
        print("hint right after wrong entry:", await pg.inner_text("#flashHint"))
        await pg.wait_for_timeout(1600)
        print("level reset to Startanzahl (3) after wrong answer, default reset2:", await pg.inner_text("#flashLevelEl"))

        # --- pause / live-adjust / resume ---
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#flashPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#flashPauseBtn"))
        hint_before = await pg.inner_text("#flashHint")
        await pg.wait_for_timeout(1300)
        print("frozen while paused:", hint_before == await pg.inner_text("#flashHint"))
        await pg.click('#flashPauseBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        bg = await pg.evaluate("() => document.getElementById('flashStage').style.background")
        print("bg updated live while paused:", bg not in ("", "rgb(255, 255, 255)"))
        await pg.click("#flashResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#flashPauseOverlay"))

        # --- Beenden while paused shouldn't leave the overlay stuck ---
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible (progress was made):", await pg.is_visible("#flashDonePanel"))
        print("done summary mentions the mode:", "Steigend" in (await pg.inner_text("#flashDoneSummary")))
        await pg.click("#flashDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        # --- Trainingsmodus: direct start count, "bei dieser Zahl bleiben" ---
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenTraining"); await pg.wait_for_timeout(150)
        await pg.fill("#flashTrainingStartSlider", "6"); await pg.dispatch_event("#flashTrainingStartSlider", "input")
        await pg.click('#flashTrainingProgressRow [data-flash-progress="0"]'); await pg.wait_for_timeout(80)
        await pg.click("#flashTrainingStartBtn"); await pg.wait_for_timeout(200)
        print("training run: level starts at 6 Zahlen:", await pg.inner_text("#flashLevelEl"))
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress returns to flashTrainingReady:", await pg.is_visible("#flashTrainingReady"))
        await pg.click("#flashTrainingBackToHome"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
