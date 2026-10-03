import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Regelwechsel-Test (Task-Switching): sixteenth exercise added under the
# autonomous "Test" section. Grounded in the task-switching paradigm
# (Jersild, 1927; Rogers & Monsell, 1995's "alternating runs" design;
# cued variant per Meiran, 1996) - a bare digit (1-4/6-9, excluding
# neutral 5) is classified by one of two rules ("Zahl": gerade/ungerade,
# or "Größe": kleiner/größer als 5), a cue names which rule applies this
# trial, and the rule sometimes repeats and sometimes switches versus the
# previous trial. Reports accuracy% plus average RT after a repeat vs.
# after a switch, and their difference as the "Wechselkosten" (switch
# cost, ms) - the actual outcome measure this paradigm exists to surface.
# Self-paced per trial (like Hick/Suchtest), only a short safety-net
# timeout advances an unanswered trial.
# Background colour/intensity (added later, sixth and final batch of the
# same Test-Bereich effort as Go/No-Go/N-Back/Trail/Flanker/UFOV/Posner/
# Rotation/Merkspanne/Simon/Suchtest/Doppelziel/Antizipationstest/Hick/
# Corsi/Reaktionsfeld - see CLAUDE.md's Established patterns for the scope
# decision, minus their transfer/preset-save machinery) tints the outer
# #tsStage. Both the ready screen and the pause overlay have their own
# live picker+slider sharing the same tsPrefs.

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
        print("Regelwechsel-Test card visible:", await pg.is_visible("#tsOpenBtn"))
        await pg.click("#tsOpenBtn"); await pg.wait_for_timeout(150)
        print("tsReady visible:", await pg.is_visible("#tsReady"))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#tsAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#tsBgColorPicker .color-swatch").count())
        await pg.click('#tsBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        await pg.fill("#tsBgIntensitySlider", "0.6"); await pg.dispatch_event("#tsBgIntensitySlider", "input")
        print("intensity value label updated:", "60%" in (await pg.inner_text("#tsBgIntensityValue")))

        # "schwer" = shortest CSI/ISI/timeout, fastest test run.
        await pg.click('#tsDifficultyRow [data-ts-diff="schwer"]'); await pg.wait_for_timeout(60)
        print("'schwer' selected:", "active" in (await pg.get_attribute('#tsDifficultyRow [data-ts-diff="schwer"]', "class") or ""))
        await pg.click("#tsReadyStartBtn"); await pg.wait_for_timeout(150)
        print("tsPlayer visible:", await pg.is_visible("#tsPlayer"))
        print("progress starts at 0/44:", "0/44" in (await pg.inner_text("#tsProgressEl")))
        bg_at_start = await pg.evaluate("() => document.getElementById('tsStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        VALID_LEFT_LABELS = {"Gerade", "Klein (<5)"}
        VALID_RIGHT_LABELS = {"Ungerade", "Groß (>5)"}
        # .ts-cue is CSS text-transform:uppercase, and Playwright's inner_text
        # reflects the RENDERED text (post-CSS-transform), not the raw
        # textContent the app actually sets - so compare against the
        # upper-cased form.
        VALID_CUES = {"AUFGABE: ZAHL", "AUFGABE: GRÖSSE"}

        async def wait_for_progress_change(prev, max_ms=6000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#tsProgressEl")
                if cur != prev:
                    return cur
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return prev

        async def wait_for_hint_contains(text, max_ms=5000, poll_ms=25):
            waited = 0
            while waited < max_ms:
                cur = await pg.inner_text("#tsHint")
                if text in cur:
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_stimulus(max_ms=3000, poll_ms=20):
            waited = 0
            while waited < max_ms:
                txt = (await pg.inner_text("#tsStimulus")).strip()
                if txt:
                    return txt
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return ""

        async def read_trial_context():
            digit_txt = await wait_for_stimulus()
            left_label = (await pg.inner_text("#tsLeftBtn")).strip()
            right_label = (await pg.inner_text("#tsRightBtn")).strip()
            cue = (await pg.inner_text("#tsCue")).strip()
            digit = int(digit_txt) if digit_txt else None
            correct_side = None
            if digit is not None:
                correct_side = "left" if (left_label == "Gerade" and digit % 2 == 0) or (left_label == "Klein (<5)" and digit < 5) else "right"
            return digit, left_label, right_label, cue, correct_side

        # Resolves whichever trial is CURRENTLY on screen (reading its
        # context first, since a trial's stimulus/labels are only stable
        # once shown) and returns a freshly re-baselined progress value
        # captured right before acting - re-baselining right at the point
        # of action (not reusing an older value from before this trial's
        # own stimulus-wait) is essential here, same trap the Hick test's
        # own comment on this exact pattern warns about: progress already
        # ticks over the instant a new trial's cue phase starts, well
        # before its stimulus/labels actually appear, so any "prev" value
        # captured earlier than that would make the very next
        # wait_for_progress_change return instantly instead of actually
        # waiting for the trial resolved here to end.
        async def resolve_trial(action):
            trial_ctx = await read_trial_context()
            digit, left_label, right_label, cue, correct_side = trial_ctx
            prev_progress = await pg.inner_text("#tsProgressEl")
            tapped_loc = correct_loc = None
            if action in ("correct", "wrong"):
                side = correct_side if action == "correct" else ("right" if correct_side == "left" else "left")
                tapped_loc = pg.locator("#tsLeftBtn" if side == "left" else "#tsRightBtn")
                correct_loc = pg.locator("#tsLeftBtn" if correct_side == "left" else "#tsRightBtn")
                await tapped_loc.click(); await pg.wait_for_timeout(60)
            return trial_ctx, tapped_loc, correct_loc, prev_progress

        # --- initial hint before the first cue ---
        initial_hint = await pg.inner_text("#tsHint")
        print("initial hint shown before first trial:", "los" in initial_hint)

        # --- trial 1 (baseline, unclassified - no switch/repeat cost yet): tap CORRECT ---
        (digit, left_label, right_label, cue, correct_side), tapped_loc, correct_loc, prev_progress = await resolve_trial("correct")
        print("digit is a bivalent digit (no 5):", digit is not None and digit != 5 and 1 <= digit <= 9)
        print("response buttons show a valid label pair:", left_label in VALID_LEFT_LABELS and right_label in VALID_RIGHT_LABELS)
        print("cue names a valid task:", cue in VALID_CUES)
        print("tapping the correct side marks it 'correct':", "correct" in (await tapped_loc.get_attribute("class") or ""))
        await wait_for_progress_change(prev_progress)

        # --- trial 2 (first classified trial): deliberately tap the WRONG side ---
        _, tapped_loc, correct_loc, prev_progress = await resolve_trial("wrong")
        print("tapping the wrong side marks it 'wrong':", "wrong" in (await tapped_loc.get_attribute("class") or ""))
        print("a wrong tap also reveals the correct side:", "correct" in (await correct_loc.get_attribute("class") or ""))
        print("a wrong tap shows the 'Daneben!' hint:", "Daneben" in (await pg.inner_text("#tsHint")))
        await wait_for_progress_change(prev_progress)

        # --- trial 3: let the safety-net timeout elapse without tapping ---
        _, _, _, prev_progress = await resolve_trial("timeout")
        timed_out_hint_shown = await wait_for_hint_contains("Verpasst")
        print("a timed-out trial shows the 'Verpasst!' hint:", timed_out_hint_shown)
        after_timeout_progress = await wait_for_progress_change(prev_progress)
        print("an unanswered trial times out and advances on its own:", after_timeout_progress != prev_progress)

        # --- pause/resume freezes the stage mid-trial ---
        await wait_for_stimulus()
        await pg.click("#tsPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#tsPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#tsPauseBtn"))
        stim_paused1 = await pg.inner_text("#tsStimulus")
        progress_paused1 = await pg.inner_text("#tsProgressEl")
        await pg.wait_for_timeout(700)
        stim_paused2 = await pg.inner_text("#tsStimulus")
        progress_paused2 = await pg.inner_text("#tsProgressEl")
        print("stage genuinely frozen while paused:", stim_paused1 == stim_paused2 and progress_paused1 == progress_paused2)
        await pg.click('#tsPauseBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('tsStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#tsResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#tsPauseOverlay"))

        # answer this (already-visible, now-resumed) trial correctly
        _, tapped_loc, _, prev_progress = await resolve_trial("correct")
        print("tap after resume still resolves the trial:", "correct" in (await tapped_loc.get_attribute("class") or ""))
        await wait_for_progress_change(prev_progress)

        # --- answer 8 more CONSECUTIVE classified trials correctly - the
        # max-3-in-a-row-same-type guard on buildTsTaskSeq guarantees both
        # "switch" and "repeat" trial types occur at least once within any
        # 8 consecutive classified trials, so this deterministically
        # populates BOTH rtByType buckets with at least one correct RT each
        # (needed for a non-null "Wechselkosten" in the done-panel below). ---
        for _ in range(8):
            _, tapped_loc, _, prev_progress = await resolve_trial("correct")
            await wait_for_progress_change(prev_progress)

        # --- Beenden mid-run with enough resolved trials -> done panel with
        # accuracy%, both RT averages and a real switch-cost number ---
        await pg.click("#tsBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with progress:", await pg.is_visible("#tsDonePanel"))
        summary = await pg.inner_text("#tsDoneSummary")
        print("done summary mentions Regelwechsel-Test and % richtig:", "Regelwechsel-Test" in summary and "% richtig" in summary)
        print("done summary reports both RT averages:", "gleiche Regel" in summary and "nach Wechsel" in summary)
        print("done summary reports Wechselkosten:", "Wechselkosten" in summary)
        print("first-ever run records a new best:", "Neue Bestleistung!" in summary)
        await pg.click("#tsDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- best-hint now shows on the ready screen ---
        await pg.click("#tsOpenBtn"); await pg.wait_for_timeout(150)
        best_hint = await pg.inner_text("#tsReadyBestHint")
        print("ready screen shows a best-hint after a completed run:", "Wechselkosten" in best_hint and "ms" in best_hint)

        # --- a fresh run with no progress skips the done panel ---
        await pg.click("#tsReadyStartBtn"); await pg.wait_for_timeout(150)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#tsPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#tsPauseBtn"))
        await pg.click("#tsBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#tsDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- difficulty selection persists across reload ---
        await pg.click("#tsOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#tsDifficultyRow [data-ts-diff="leicht"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#tsOpenBtn"); await pg.wait_for_timeout(150)
        print("'leicht' selection survives reload:", "active" in (await pg.get_attribute('#tsDifficultyRow [data-ts-diff="leicht"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
