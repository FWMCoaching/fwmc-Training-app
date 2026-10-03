import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Doppelziel-Test (Attentional Blink): eleventh exercise added under the
# autonomous "Test" section. Classic RSVP attentional-blink paradigm
# (Raymond, Shapiro & Arnell, 1992) - a fast stream of single letters
# flashes at fixation; one letter is coloured (T1, first target) and, at a
# variable lag afterwards, the fixed letter "X" may or may not appear (T2).
# Both questions ("which letter was blue?" then "was X there?") are asked
# untimed, after the whole stream ends. 24 fixed trials (3 lags x
# 6-present/2-absent), no Bei-Fehler/level, reports overall accuracy% plus
# T2-given-T1-correct accuracy per lag and the "Aufmerksamkeitslücke"
# (lag 8 minus lag 3) as the actual dip-and-recovery effect this paradigm
# exists to surface.
# Background colour/intensity (added later, fourth batch of the same
# Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/Rotation/
# Merkspanne/Simon - see CLAUDE.md's Established patterns for the scope
# decision, minus their transfer/preset-save machinery) tints the outer
# #abStage - the T1 accent colour (#007094 teal) sits directly on it too
# (audited and approved: the tint is always mixed toward white, never full
# saturation, keeping contrast usable). Both the ready screen and the pause
# overlay have their own live picker+slider sharing the same abPrefs.

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
        print("Doppelziel-Test card visible:", await pg.is_visible("#abOpenBtn"))
        await pg.click("#abOpenBtn"); await pg.wait_for_timeout(150)
        print("abReady visible:", await pg.is_visible("#abReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#abAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#abBgColorPicker .color-swatch").count())
        await pg.click('#abBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#abBgIntensitySlider", "0.6"); await pg.dispatch_event("#abBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#abBgIntensityValue")))

        async def wait_for_visible(sel, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible(sel):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_text_change(sel, prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text(sel)
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        # --- "leicht" (slowest stream) so we can actually observe the
        # coloured T1 letter mid-stream, plus the reveal-on-wrong-answer path ---
        await pg.click('#abDifficultyRow [data-ab-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.click("#abReadyStartBtn"); await pg.wait_for_timeout(200)
        print("abPlayer visible:", await pg.is_visible("#abPlayer"))
        progress = await pg.inner_text("#abProgressEl")
        print("progress starts at 0/24:", "0/24" in progress)
        bg_at_start = await pg.evaluate("() => document.getElementById('abStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        saw_t1_color = False
        saw_plain_color = False
        waited = 0
        while waited < 5000 and not await pg.is_visible("#abT1Panel"):
            cls = await pg.get_attribute("#abStreamChar", "class") or ""
            txt = (await pg.inner_text("#abStreamChar")).strip()
            if txt:
                if "is-t1" in cls:
                    saw_t1_color = True
                else:
                    saw_plain_color = True
            await pg.wait_for_timeout(15)
            waited += 15
        print("T1 panel appeared after the stream:", await pg.is_visible("#abT1Panel"))
        print("saw the coloured T1 letter during the stream:", saw_t1_color)
        print("saw plain (uncoloured) distractor letters too:", saw_plain_color)

        # Deliberately tap a wrong-looking option: click button 0, then check
        # feedback classes appear (correct/wrong on at least one button).
        await pg.click("#abT1Btn0"); await pg.wait_for_timeout(100)
        classes = []
        for i in range(4):
            classes.append(await pg.get_attribute(f"#abT1Btn{i}", "class") or "")
        has_feedback = any(("correct" in c or "wrong" in c) for c in classes)
        print("T1 tap shows correct/wrong feedback:", has_feedback)
        exactly_one_correct = sum(1 for c in classes if "correct" in c) == 1
        print("exactly one button marked correct (the real T1 letter):", exactly_one_correct)

        print("T2 panel appears after the T1 feedback delay:", await wait_for_visible("#abT2Panel", max_ms=2000))
        await pg.click("#abT2NeinBtn"); await pg.wait_for_timeout(150)
        t2_classes = (await pg.get_attribute("#abT2JaBtn", "class") or "") + " " + (await pg.get_attribute("#abT2NeinBtn", "class") or "")
        print("T2 tap shows correct/wrong feedback:", ("correct" in t2_classes or "wrong" in t2_classes))

        # --- pause/resume freezes the stage - progress text stays put ---
        # (progress already ticked to "1/24" the instant trial 1's own gap
        # started, well before this point - so the real check is that it
        # advances at least once more, into trial 2, not any specific value.)
        progress_before_trial2 = await pg.inner_text("#abProgressEl")
        await wait_for_visible("#abT1Panel", max_ms=5000)
        progress = await pg.inner_text("#abProgressEl")
        print("progress advanced into trial 2:", progress != progress_before_trial2 and "2/24" in progress)
        await pg.click("#abPauseBtn"); await pg.wait_for_timeout(120)
        print("pause overlay visible:", await pg.is_visible("#abPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#abPauseBtn"))
        frozen1 = await pg.inner_text("#abProgressEl")
        await pg.wait_for_timeout(600)
        frozen2 = await pg.inner_text("#abProgressEl")
        print("progress frozen while paused:", frozen1 == frozen2)
        await pg.click('#abPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('abStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#abResumeBtn"); await pg.wait_for_timeout(120)
        print("pause overlay hidden after resume:", await pg.is_hidden("#abPauseOverlay"))

        # --- Beenden with only 1-2 resolved trials skips the done panel (< 4 threshold) ---
        await pg.click("#abBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with too few resolved trials returns to testHome, no done panel:",
              await pg.is_visible("#testHome") and await pg.is_hidden("#abDonePanel"))

        # --- full run to the done panel, "schwer" (fastest) for speed ---
        await pg.click("#abOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#abDifficultyRow [data-ab-diff="schwer"]'); await pg.wait_for_timeout(60)
        await pg.click("#abReadyStartBtn"); await pg.wait_for_timeout(200)

        for i in range(24):
            ok = await wait_for_visible("#abT1Panel", max_ms=6000)
            if not ok:
                errors.append(f"trial {i}: T1 panel never appeared")
                break
            await pg.click(f"#abT1Btn{i % 4}")
            ok2 = await wait_for_visible("#abT2Panel", max_ms=2000)
            if not ok2:
                errors.append(f"trial {i}: T2 panel never appeared")
                break
            await pg.click("#abT2JaBtn" if i % 2 == 0 else "#abT2NeinBtn")

        async def wait_for_done_panel(max_ms=6000, poll_ms=30):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible("#abDonePanel"):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        print("done panel shown after all 24 trials:", await wait_for_done_panel())
        summary = await pg.inner_text("#abDoneSummary")
        print("done summary mentions Doppelziel-Test:", "Doppelziel-Test" in summary)
        print("done summary reports a percentage:", "%" in summary)
        await pg.click("#abDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome after done panel:", await pg.is_visible("#testHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
