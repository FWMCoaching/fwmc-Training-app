import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Client-facing "Kraft-/Wiederholungstraining" self-service builder - the
# reps mode was previously coach-plan-only (see CLAUDE.md's note on why
# this was deferred as its own product decision). Covers: rep-range
# presets backed by real strength-training research (Kraft/Muskelaufbau/
# Kraftausdauer + a custom range), the live per-set stopwatch (display
# only, per the time-under-tension research), the "geschafft" reps input,
# and the double-progression suggestion that appears on the NEXT visit
# once every set hit the top of the range.

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

        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(150)
        print("reps start card visible on workoutHome:", await pg.is_visible("#workoutRepsStartCard"))
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("reps ready screen open:", await pg.is_visible("#workoutRepsReady"))
        print("start button disabled with no exercise chosen:", await pg.get_attribute("#workoutRepsStartBtn", "disabled") is not None)
        print("default range preset is Muskelaufbau:", "active" in (await pg.get_attribute('[data-reps-range="muskelaufbau"]', "class") or ""))
        print("hint mentions the %1RM range:", "65" in await pg.inner_text("#workoutRepsRangeHint"))

        # ---- pick Kraft preset, then a custom range ----
        await pg.click('[data-reps-range="kraft"]'); await pg.wait_for_timeout(80)
        print("Kraft hint mentions Maximalkraft:", "Maximalkraft" in await pg.inner_text("#workoutRepsRangeHint"))
        await pg.click('[data-reps-range="custom"]'); await pg.wait_for_timeout(80)
        print("custom range sliders visible:", await pg.is_visible("#workoutRepsCustomRangeRow"))
        await pg.fill("#workoutRepsCustomMinSlider", "5")
        await pg.dispatch_event("#workoutRepsCustomMinSlider", "input")
        await pg.fill("#workoutRepsCustomMaxSlider", "8")
        await pg.dispatch_event("#workoutRepsCustomMaxSlider", "input")
        await pg.wait_for_timeout(80)
        print("custom range value updates:", "5–8" in await pg.inner_text("#workoutRepsCustomRangeValue"))
        # back to a preset for the actual run below
        await pg.click('[data-reps-range="muskelaufbau"]'); await pg.wait_for_timeout(80)

        # ---- pick an exercise ----
        await pg.click('#workoutRepsExerciseGrid .combo-add-btn >> text="Kniebeugen"'); await pg.wait_for_timeout(80)
        print("Kniebeugen now marked active:", "active" in (await pg.get_attribute('#workoutRepsExerciseGrid .combo-add-btn', "class") or ""))
        print("start button enabled once an exercise is chosen:", await pg.get_attribute("#workoutRepsStartBtn", "disabled") is None)

        # ---- sets/rest ----
        await pg.click('[data-reps-sets="2"]'); await pg.wait_for_timeout(60)
        await pg.fill("#workoutRepsRestSlider", "15")
        await pg.dispatch_event("#workoutRepsRestSlider", "input")
        await pg.wait_for_timeout(60)
        print("rest value shows 15 s:", "15" in await pg.inner_text("#workoutRepsRestValue"))
        print("no progression hint yet (never trained this exercise):", await pg.is_hidden("#workoutRepsSuggestionHint"))

        # ---- run it: 2 sets, log top-of-range reps each time -> should
        # trigger the "increase" suggestion on the done screen ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        print("player visible, reps view shown:", await pg.is_visible("#workoutRepsView"))
        print("range shown (6–12 Wiederholungen):", "6–12" in await pg.inner_text("#workoutRepsBig"))
        print("live set timer visible:", await pg.is_visible("#workoutSetTimer"))
        print("reps-input row visible, defaults to top of range (12):", await pg.inner_text("#workoutRepsInputValue") == "12")
        await pg.wait_for_timeout(1200)
        timer_text_1 = await pg.inner_text("#workoutSetTimer")
        print("timer is actually advancing:", timer_text_1 not in ("0:00", ""))

        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        print("rest screen shown between sets:", await pg.is_visible("#workoutRestBox"))
        await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(200)
        print("set 2 of 2 shown:", "2 VON 2" in (await pg.inner_text("#workoutSetInfo")).upper())
        print("reps input reset to top of range again (12):", await pg.inner_text("#workoutRepsInputValue") == "12")
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(300)

        print("done panel shown:", await pg.is_visible("#workoutDonePanel"))
        print("progression suggestion shown (hit top of range both sets):", await pg.is_visible("#workoutDoneSuggestion"))
        print("suggestion mentions Kniebeugen-appropriate wording:", "schwerer" in await pg.inner_text("#workoutDoneSuggestion"))
        await pg.click("#workoutDoneBackBtn"); await pg.wait_for_timeout(200)
        print("back at workoutHome:", await pg.is_visible("#workoutHome"))

        # ---- revisit: the suggestion should now show up on the ready screen ----
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        print("progression hint now shown on ready screen:", await pg.is_visible("#workoutRepsSuggestionHint"))
        print("hint mentions Kniebeugen:", "Kniebeugen" in await pg.inner_text("#workoutRepsSuggestionHint"))

        # ---- "Beenden" mid-set returns to the reps ready screen, not Tabata's ----
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(200)
        print("Beenden mid-set returns to workoutRepsReady (not workoutTabataReady):", await pg.is_visible("#workoutRepsReady"))

        # ---- sanity: coach-authored fixed-reps blocks (no rangeMin) are
        # completely unaffected - reps input/timer stay hidden, blind
        # "Satz erledigt" still works exactly as before ----
        await pg.evaluate("""() => {
            window.__fwmcTestBlock = { kind: 'reps', exercise: 'liegestuetz', sets: 1, reps: 5, restS: 1 };
        }""")
        # (no direct hook to inject a plan block from outside; covered
        # already by workout_combo_test.py's existing fixed-reps assertions -
        # this file only re-checks that the NEW elements stay hidden for a
        # completely fresh page load before any reps-builder interaction)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        print("reps-input row hidden by default (no active session):", await pg.is_hidden("#workoutRepsInputRow"))
        print("set timer hidden by default (no active session):", await pg.is_hidden("#workoutSetTimer"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
