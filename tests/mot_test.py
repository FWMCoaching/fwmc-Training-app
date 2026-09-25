import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# MOT-Fähigkeit (Multiple Object Tracking): several identical-looking objects
# drift around the stage; one or more are briefly highlighted as "targets",
# then everything looks the same again and keeps moving for a while - the
# client tracks the target(s) with their eyes, then taps them back once
# movement stops (same unordered tap-set mechanic as Blitz-Raster). First
# engine in the app driven by a continuous requestAnimationFrame physics loop
# (bouncing off the stage edges) rather than a precomputed schedule or
# discrete setTimeout phases.
#
# Difficulty progression mirrors the researched MOT literature (classic
# paradigm + NeuroTracker's 3D-MOT: 8 objects / 4 targets, speed on a
# ±0.05-log staircase) but - per explicit user request - is now FOUR modes,
# mirroring Flash Speicher Test's own multi-mode shape: "speed" (fixed
# object/target count, only speedStep rises - the literature-accurate mode
# and the one whose defaults must match 8/4), "count" (fixed speed, object/
# target count rises from a configurable start), "both" (both rise together),
# "training" (direct start at chosen object/target/speed-step values, with a
# weiter-steigern/bei-dieser-Einstellung-bleiben toggle). A single unified
# `motState.level` counter drives whichever axis/axes the mode says should
# grow; motCountsForRound() is the one place that derives {n, k, speedStep}
# from it. Objects also get a configurable colour (one per ROUND, not per
# object - all objects must look identical within a round for MOT to make
# sense), reusing the generic buildStimColorPicker()/pickPeriphColor() stim-
# colour infrastructure built earlier for Zusatzaufgabe/Periph.

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
        await pg.evaluate("() => { localStorage.removeItem('fwmc-mot-prefs-v1'); localStorage.removeItem('fwmc-mot-best-v1'); }")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        print("MOT panel visible:", await pg.is_visible("#natMotPanel"))
        cards_visible = True
        for sel in ["#motOpenSpeed", "#motOpenCount", "#motOpenBoth", "#motOpenTraining"]:
            if not await pg.is_visible(sel):
                cards_visible = False
        print("four featured cards present:", cards_visible)

        async def wait_tappable(limit=100):
            for _ in range(limit):
                if await pg.locator("#motObjectsLayer .mot-object.tappable").count() > 0:
                    return True
                await pg.wait_for_timeout(80)
            return False

        async def find_target_id():
            return await pg.evaluate("""() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].findIndex(el => el.classList.contains('target'))""")

        async def tap_correct(track_wait_ms):
            target_id = await find_target_id()
            await pg.wait_for_timeout(track_wait_ms)
            await wait_tappable()
            cells = await pg.locator("#motObjectsLayer .mot-object").all()
            await cells[target_id].click()
            # the level label only updates once the next round's
            # motStartRound() actually runs, 900ms after a correct tap
            await pg.wait_for_timeout(1100)

        async def open_advanced(details_id):
            is_open = await pg.evaluate(f"() => document.getElementById('{details_id}').open")
            if not is_open:
                await pg.click(f"#{details_id} summary"); await pg.wait_for_timeout(100)

        # ---------------------------------------------------------------
        # Mode: "speed" - fixed object/target count (8/4 default, matching
        # the researched NeuroTracker standard), only Tempo-Stufe rises.
        # ---------------------------------------------------------------
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        print("motReady visible:", await pg.is_visible("#motReady"))
        print("title: Tempo steigt:", await pg.inner_text("#motReadyTitle") == "Tempo steigt")
        print("speed mode: fixedCountGroup visible, growStartGroup hidden:",
              await pg.is_visible("#motFixedCountGroup") and await pg.is_hidden("#motGrowStartGroup"))
        print("default is 8 objects / 4 targets (matches researched standard):",
              await pg.inner_text("#motObjectsValue") == "8" and await pg.inner_text("#motTargetsValue") == "4")

        print("Darstellung defaults to Flach:", "active" in (await pg.get_attribute('#motStyleRow [data-mot-style="flach"]', "class") or ""))
        await pg.click('#motStyleRow [data-mot-style="3d"]'); await pg.wait_for_timeout(60)
        style_pref = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')||'{}').style")
        print("3D-Optik selectable and persisted:", style_pref == "3d")
        await pg.click('#motStyleRow [data-mot-style="flach"]'); await pg.wait_for_timeout(60)

        # Farbe der Objekte: default schwarz-only, can select more, persists.
        print("colour picker default schwarz-only:", "active" in (await pg.get_attribute('#motColorPicker [data-color="schwarz"]', "class") or ""))
        await pg.click('#motColorPicker [data-color="rot"]'); await pg.wait_for_timeout(60)
        colors_pref = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')||'{}').colors")
        print("second colour persisted:", set(colors_pref) == {"schwarz", "rot"})
        print("gemischt hint once 2+ colours selected:", "Gemischt" in (await pg.inner_text("#motColorHint")))

        # Shrink counts + timings for a fast, deterministic round.
        await open_advanced("motAdvanced")
        await pg.fill("#motObjectsSlider", "4"); await pg.dispatch_event("#motObjectsSlider", "input")
        await pg.fill("#motTargetsSlider", "1"); await pg.dispatch_event("#motTargetsSlider", "input")
        await pg.fill("#motSpeedSlider", "0.06"); await pg.dispatch_event("#motSpeedSlider", "input")
        await pg.fill("#motTrackSlider", "3"); await pg.dispatch_event("#motTrackSlider", "input")
        await pg.fill("#motHighlightSlider", "1"); await pg.dispatch_event("#motHighlightSlider", "input")
        print("custom sliders switch difficulty bucket to 'individuell':", await pg.is_visible("#motDiffCustom"))
        objs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')||'{}').objectCount")
        tgts = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-mot-prefs-v1')||'{}').targetCount")
        print("4 objects / 1 target persisted to prefs:", objs == 4 and tgts == 1)

        # background swatches present (shared pattern with every other domain)
        print("bg swatch count:", await pg.locator("#motBgColorPicker .color-swatch").count())
        print("bg source row lists the other domains:", len(await pg.locator("#motBgSourceRow button").all_inner_texts()) > 0)

        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)
        print("motPlayer visible:", await pg.is_visible("#motPlayer"))
        print("4 objects rendered:", await pg.locator("#motObjectsLayer .mot-object").count() == 4)
        print("exactly 1 target highlighted:", await pg.locator("#motObjectsLayer .mot-object.target").count() == 1)
        print("level indicator shows fixed counts + Tempo-Stufe 1:", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 1")

        target_id = await find_target_id()
        await pg.wait_for_timeout(1200)
        print("highlight cleared once tracking begins:", await pg.locator("#motObjectsLayer .mot-object.target").count() == 0)
        pos_before = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left + ',' + el.style.top)")
        await pg.wait_for_timeout(800)
        pos_after = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left + ',' + el.style.top)")
        print("objects actually moved during tracking:", pos_before != pos_after)

        # non-target/non-special object uses the chosen colour, not the CSS default
        bg_style = await pg.evaluate("""() => { const el = [...document.querySelectorAll('#motObjectsLayer .mot-object')].find(e => !e.classList.contains('target')); return el ? el.style.background : null; }""")
        print("normal object background is set inline from chosen colour:", bool(bg_style))

        await wait_tappable()
        print("objects become tappable once tracking ends:", await pg.locator("#motObjectsLayer .mot-object.tappable").count() == 4)
        pos_stopped1 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        await pg.wait_for_timeout(300)
        pos_stopped2 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        print("objects are frozen in place during identify phase:", pos_stopped1 == pos_stopped2)

        cells = await pg.locator("#motObjectsLayer .mot-object").all()
        await cells[target_id].click(); await pg.wait_for_timeout(150)
        print("hint after correct tap:", await pg.inner_text("#motHint"))
        await pg.wait_for_timeout(1100)
        print("still 4 objects (speed mode never grows count):", await pg.locator("#motObjectsLayer .mot-object").count() == 4)
        print("level indicator now shows Tempo-Stufe 2:", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 2")

        # a second correct round, so `cleared` > 0 for the done-panel check later
        await tap_correct(1200)
        print("level indicator now shows Tempo-Stufe 3:", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 3")

        # wrong tap: reveals the real target, applies default reset2 (back to Tempo-Stufe 1)
        target_id3 = await find_target_id()
        await pg.wait_for_timeout(1200)
        await wait_tappable()
        cells3 = await pg.locator("#motObjectsLayer .mot-object").all()
        wrong_id = next(i for i in range(4) if i != target_id3)
        await cells3[wrong_id].click(); await pg.wait_for_timeout(150)
        print("hint after wrong tap (default reset2):", await pg.inner_text("#motHint"))
        print("actual target revealed as correct:", await pg.locator("#motObjectsLayer .mot-object.correct").count() == 1)
        print("wrong-tapped object marked:", await pg.locator("#motObjectsLayer .mot-object.wrong").count() == 1)
        await pg.wait_for_timeout(1600)
        print("Tempo-Stufe reset to 1 after wrong answer (still 4 objects):", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 1")

        # --- pause / live-adjust / resume, mid-tracking ---
        await pg.wait_for_timeout(1200)
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#motPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#motPauseBtn"))
        pos_paused1 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        await pg.wait_for_timeout(700)
        pos_paused2 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        print("physics genuinely frozen while paused:", pos_paused1 == pos_paused2)
        await pg.click('#motPauseBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        bg = await pg.evaluate("() => document.getElementById('motStage').style.background")
        print("bg updated live while paused:", bg not in ("", "rgb(255, 255, 255)"))
        await pg.click("#motResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#motPauseOverlay"))
        pos_resumed1 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        await pg.wait_for_timeout(600)
        pos_resumed2 = await pg.evaluate("() => [...document.querySelectorAll('#motObjectsLayer .mot-object')].map(el => el.style.left)")
        print("physics resumes moving after Weiter:", pos_resumed1 != pos_resumed2)

        # Beenden while paused: progress was made (cleared=2) -> done panel,
        # and "Zur Übersicht" returns to motReady (motReturnScreen), not
        # hardcoded natHome - MOT deliberately differs from Flash here so a
        # quick "adjust and go again" loop doesn't require re-opening the tab.
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible (progress was made earlier):", await pg.is_visible("#motDonePanel"))
        print("done summary mentions Tempo steigt + Tempo-Stufe:",
              "Tempo steigt" in (await pg.inner_text("#motDoneSummary")) and "Tempo-Stufe" in (await pg.inner_text("#motDoneSummary")))
        await pg.click("#motDoneBackBtn"); await pg.wait_for_timeout(150)
        print("Zur Übersicht returns to motReady (motReturnScreen), not natHome:", await pg.is_visible("#motReady"))
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        # a fresh run has no stuck overlay / pause button hidden state
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#motPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#motPauseBtn"))
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel, returns to motReady:",
              await pg.is_hidden("#motDonePanel") and await pg.is_visible("#motReady"))
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(150)

        # ---------------------------------------------------------------
        # Mode: "count" - fixed speed, object/target count rises with
        # level per motCountsForRound()'s formula: n grows every 2 levels,
        # k every 4, both capped. No Tempo-Stufe shown (speed never moves).
        # ---------------------------------------------------------------
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenCount"); await pg.wait_for_timeout(150)
        print("title: Anzahl steigt:", await pg.inner_text("#motReadyTitle") == "Anzahl steigt")
        print("count mode: growStartGroup visible, fixedCountGroup hidden:",
              await pg.is_visible("#motGrowStartGroup") and await pg.is_hidden("#motFixedCountGroup"))
        print("default start: 4 objects / 1 target:",
              await pg.inner_text("#motGrowObjectsValue") == "4" and await pg.inner_text("#motGrowTargetsValue") == "1")

        await open_advanced("motAdvanced")
        await pg.fill("#motSpeedSlider", "0.06"); await pg.dispatch_event("#motSpeedSlider", "input")
        await pg.fill("#motTrackSlider", "3"); await pg.dispatch_event("#motTrackSlider", "input")
        await pg.fill("#motHighlightSlider", "1"); await pg.dispatch_event("#motHighlightSlider", "input")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)
        print("round1: 4 objects, 1 target, no Tempo-Stufe in label:", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel")

        await tap_correct(1200)  # level 1 -> 2: n=4+floor(1/2)=4, k unchanged
        print("level 2: still 4 objects (floor(1/2)=0 growth):", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel")
        await tap_correct(1200)  # level 2 -> 3: n=4+floor(2/2)=5
        print("level 3: object count grew to 5 (floor(2/2)=1):", await pg.inner_text("#motLevelEl") == "5 Objekte · 1 Ziel")
        await tap_correct(1200)  # level 3 -> 4: n=4+floor(3/2)=5
        await tap_correct(1200)  # level 4 -> 5: n=4+floor(4/2)=6, k=1+floor(4/4)=2
        print("level 5: object count 6, target count grew to 2 (floor(4/4)=1):", await pg.inner_text("#motLevelEl") == "6 Objekte · 2 Ziele")
        print("no Tempo-Stufe ever shown in count mode:", "Tempo-Stufe" not in (await pg.inner_text("#motLevelEl")))
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        print("done panel after count-mode progress, mentions Stufe (not Tempo-Stufe):",
              "Stufe" in (await pg.inner_text("#motDoneSummary")))
        await pg.click("#motDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(150)

        # ---------------------------------------------------------------
        # Mode: "both" - object/target count AND speed grow together from
        # the same level counter.
        # ---------------------------------------------------------------
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenBoth"); await pg.wait_for_timeout(150)
        print("title: Beides steigt:", await pg.inner_text("#motReadyTitle") == "Beides steigt")
        print("both mode: growStartGroup visible, fixedCountGroup hidden:",
              await pg.is_visible("#motGrowStartGroup") and await pg.is_hidden("#motFixedCountGroup"))
        await open_advanced("motAdvanced")
        await pg.fill("#motSpeedSlider", "0.06"); await pg.dispatch_event("#motSpeedSlider", "input")
        await pg.fill("#motTrackSlider", "3"); await pg.dispatch_event("#motTrackSlider", "input")
        await pg.fill("#motHighlightSlider", "1"); await pg.dispatch_event("#motHighlightSlider", "input")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)
        print("round1: 4 objects, 1 target, Tempo-Stufe 1 (both shown together):", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 1")
        await tap_correct(1200)  # level 1 -> 2: n unchanged, speedStep = level-1 = 1 -> Tempo-Stufe 2
        print("level 2: count unchanged but Tempo-Stufe rose to 2 (grows together):", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 2")
        await tap_correct(1200)  # level 2 -> 3: n=5, Tempo-Stufe 3
        print("level 3: object count AND Tempo-Stufe both grew:", await pg.inner_text("#motLevelEl") == "5 Objekte · 1 Ziel · Tempo-Stufe 3")
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(150)

        # ---------------------------------------------------------------
        # Mode: "training" - direct start at chosen object/target/speed-
        # step values, own colour+bg picker instance, progress toggle.
        # ---------------------------------------------------------------
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenTraining"); await pg.wait_for_timeout(150)
        print("motTrainingReady visible:", await pg.is_visible("#motTrainingReady"))
        print("default training start: 6 objects / 2 targets:",
              await pg.inner_text("#motTrainingObjectsValue") == "6" and await pg.inner_text("#motTrainingTargetsValue") == "2")

        await pg.fill("#motTrainingObjectsSlider", "5"); await pg.dispatch_event("#motTrainingObjectsSlider", "input")
        await pg.fill("#motTrainingTargetsSlider", "1"); await pg.dispatch_event("#motTrainingTargetsSlider", "input")
        await pg.click('#motTrainingProgressRow [data-mot-progress="0"]'); await pg.wait_for_timeout(80)
        await open_advanced("motTrainingAdvanced")
        await pg.fill("#motTrainingSpeedSlider", "0.06"); await pg.dispatch_event("#motTrainingSpeedSlider", "input")
        await pg.fill("#motTrainingTrackSlider", "3"); await pg.dispatch_event("#motTrainingTrackSlider", "input")
        await pg.fill("#motTrainingHighlightSlider", "1"); await pg.dispatch_event("#motTrainingHighlightSlider", "input")
        await pg.click("#motTrainingStartBtn"); await pg.wait_for_timeout(150)
        print("training run starts at direct 5 objects / 1 target:", await pg.inner_text("#motLevelEl") == "5 Objekte · 1 Ziel · Tempo-Stufe 1")

        await tap_correct(1200)
        print("'bei dieser Einstellung bleiben': counts+speed stay fixed after success:",
              await pg.inner_text("#motLevelEl") == "5 Objekte · 1 Ziel · Tempo-Stufe 1")
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible (training mode, progress was made):", await pg.is_visible("#motDonePanel"))
        print("done summary mentions Trainingsmodus:", "Trainingsmodus" in (await pg.inner_text("#motDoneSummary")))
        await pg.click("#motDoneBackBtn"); await pg.wait_for_timeout(150)
        print("Zur Übersicht returns to motTrainingReady (motReturnScreen), not motReady:",
              await pg.is_visible("#motTrainingReady"))
        await pg.click("#motTrainingBackToHome"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        # "weiter steigern" toggle actually grows, same formula as "both"
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenTraining"); await pg.wait_for_timeout(150)
        await pg.click('#motTrainingProgressRow [data-mot-progress="1"]'); await pg.wait_for_timeout(80)
        await pg.click("#motTrainingStartBtn"); await pg.wait_for_timeout(150)
        await tap_correct(1200)
        print("'weiter steigern': Tempo-Stufe rose to 2 after success:", await pg.inner_text("#motLevelEl") == "5 Objekte · 1 Ziel · Tempo-Stufe 2")
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motTrainingBackToHome"); await pg.wait_for_timeout(150)

        # ---------------------------------------------------------------
        # "Nochmal" restarts the same last-played mode.
        # ---------------------------------------------------------------
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        await open_advanced("motAdvanced")
        await pg.fill("#motObjectsSlider", "4"); await pg.dispatch_event("#motObjectsSlider", "input")
        await pg.fill("#motTargetsSlider", "1"); await pg.dispatch_event("#motTargetsSlider", "input")
        await pg.fill("#motTrackSlider", "3"); await pg.dispatch_event("#motTrackSlider", "input")
        await pg.fill("#motHighlightSlider", "1"); await pg.dispatch_event("#motHighlightSlider", "input")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(150)
        await tap_correct(1200)
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#motAgainBtn"); await pg.wait_for_timeout(200)
        print("Nochmal restarts speed mode fresh at Tempo-Stufe 1:", await pg.inner_text("#motLevelEl") == "4 Objekte · 1 Ziel · Tempo-Stufe 1")
        await pg.click("#motBackBtn"); await pg.wait_for_timeout(150)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
