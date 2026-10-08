import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Kippbild-Test: twenty-ninth exercise added under the autonomous "Test"
# section. Grounded in the classic multistable-perception paradigm around
# the Necker cube (Necker, L.A., 1832) - a plain wireframe cube is shown
# continuously, the drawing itself never changes, but the client's own
# perceived 3D orientation of it spontaneously flips from time to time.
# The client taps once every time they notice such a flip. Deliberately no
# best-score tracking (a reversal rate is a perceptual trait, not a skill).

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
        print("Kippbild-Test card visible:", await pg.is_visible("#kippbildOpenBtn"))
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(150)
        print("kippbildReady visible:", await pg.is_visible("#kippbildReady"))
        print("card has no best-score meta (deliberate, no best concept):",
              await pg.eval_on_selector("#kippbildOpenBtn", "el => !el.querySelector('.fc-meta')"))

        # --- length + mode selection ---
        await pg.click('#kippbildLengthRow [data-kippbild-length="kurz"]'); await pg.wait_for_timeout(60)
        print("kurz marked active:", "active" in (await pg.get_attribute('#kippbildLengthRow [data-kippbild-length="kurz"]', "class") or ""))
        await pg.click('#kippbildModeRow [data-kippbild-mode="verlangsamen"]'); await pg.wait_for_timeout(60)
        print("verlangsamen marked active:", "active" in (await pg.get_attribute('#kippbildModeRow [data-kippbild-mode="verlangsamen"]', "class") or ""))

        # --- Feineinstellungen: background colour/intensity ---
        await pg.click("#kippbildAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg swatch count:", await pg.locator("#kippbildBgColorPicker .color-swatch").count())
        await pg.click('#kippbildBgColorPicker .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        await pg.fill("#kippbildBgIntensitySlider", "0.5"); await pg.dispatch_event("#kippbildBgIntensitySlider", "input")
        print("intensity value label updated:", "50 %" in (await pg.inner_text("#kippbildBgIntensityValue")))

        await pg.click("#kippbildReadyStartBtn"); await pg.wait_for_timeout(250)
        print("kippbildPlayer visible:", await pg.is_visible("#kippbildPlayer"))
        print("cube visible:", await pg.is_visible("#kippbildCubeSvg"))
        print("hint names the verlangsamen instruction:", "verlangsamen" in (await pg.inner_text("#kippbildHint")))
        print("status starts at 0 Wechsel · 45s:", "0 Wechsel · 45s" in (await pg.inner_text("#kippbildProgressEl")))
        bg_at_start = await pg.evaluate("() => document.getElementById('kippbildStage').style.background")
        print("stage carries the chosen background as soon as the game starts:", bg_at_start not in ("", "rgb(255, 255, 255)"))

        # --- the player-bar can wrap to two rows on a narrow phone; the
        # hint (which stays visible for the WHOLE run, unlike a transient
        # per-trial instruction) must be repositioned below it, not
        # overlapped - the real bug caught and fixed while building this
        # exercise. Assert no actual rect overlap. ---
        overlap = await pg.evaluate("""() => {
          const bar = document.getElementById('kippbildPlayerBar').getBoundingClientRect();
          const hint = document.getElementById('kippbildHint').getBoundingClientRect();
          return !(hint.top >= bar.bottom || hint.bottom <= bar.top || hint.left >= bar.right || hint.right <= bar.left);
        }""")
        print("hint does NOT overlap the (possibly wrapped) player-bar:", not overlap)

        # --- countdown ticks down live ---
        await pg.wait_for_timeout(1200)
        print("countdown ticked down:", "44s" in (await pg.inner_text("#kippbildProgressEl")))

        # --- tapping the cube area logs a reversal ---
        await pg.click("#kippbildArea"); await pg.wait_for_timeout(100)
        print("tap registers as a reversal:", "1 Wechsel" in (await pg.inner_text("#kippbildProgressEl")))
        await pg.click("#kippbildArea"); await pg.wait_for_timeout(100)
        await pg.click("#kippbildArea"); await pg.wait_for_timeout(100)
        print("3 taps -> 3 Wechsel:", "3 Wechsel" in (await pg.inner_text("#kippbildProgressEl")))

        # --- pause/resume freezes the live status, taps while paused don't count ---
        status_before_pause = await pg.inner_text("#kippbildProgressEl")
        await pg.click("#kippbildPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#kippbildPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#kippbildPauseBtn"))
        # read after pausing: a 1 s tick between the read and the Pause click
        # made this flaky under load
        status_before_pause = await pg.inner_text("#kippbildProgressEl")
        await pg.wait_for_timeout(1300)
        print("status genuinely frozen while paused:",
              (await pg.inner_text("#kippbildProgressEl")) == status_before_pause)
        await pg.click('#kippbildPauseBgColorPicker .color-swatch[data-key="orange"]'); await pg.wait_for_timeout(80)
        bg_paused = await pg.evaluate("() => document.getElementById('kippbildStage').style.background")
        print("pause overlay's own picker live-updates the same stage background:", bg_paused not in ("", "rgb(255, 255, 255)"))
        await pg.click("#kippbildResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#kippbildPauseOverlay"))

        # --- push played time past KIPPBILD_MIN_PLAYED_S (8s) ---
        await pg.wait_for_timeout(7500)

        # --- Beenden mid-run with enough played time -> done panel ---
        await pg.click("#kippbildBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible after Beenden with enough played time:", await pg.is_visible("#kippbildDonePanel"))
        summary = await pg.inner_text("#kippbildDoneSummary")
        print("summary:", summary)
        print("summary names the test, mode and a Wechsel/Min rate:",
              "Kippbild-Test" in summary and "Bewusst verlangsamen" in summary and "Wechsel/Min" in summary)
        print("summary reports 3 Wechsel:", "3 Wechsel" in summary)
        await pg.click("#kippbildDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- a fresh run ended almost immediately (below KIPPBILD_MIN_PLAYED_S) skips the done panel ---
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#kippbildReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#kippbildPauseOverlay"))
        await pg.click("#kippbildBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with too little played time skips done panel:", await pg.is_hidden("#kippbildDonePanel"))
        print("back at testHome:", await pg.is_visible("#testHome"))

        # --- the full duration run also auto-finishes on its own ---
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#kippbildReadyStartBtn"); await pg.wait_for_timeout(150)
        await pg.wait_for_timeout(45500)
        print("run auto-finishes once the full duration elapses:", await pg.is_visible("#kippbildDonePanel"))
        await pg.click("#kippbildDoneBackBtn"); await pg.wait_for_timeout(150)

        # --- length + mode selection persist across reload ---
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#kippbildLengthRow [data-kippbild-length="lang"]'); await pg.wait_for_timeout(60)
        await pg.click('#kippbildModeRow [data-kippbild-mode="verlangsamen"]'); await pg.wait_for_timeout(60)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(150)
        print("'lang' selection survives reload:", "active" in (await pg.get_attribute('#kippbildLengthRow [data-kippbild-length="lang"]', "class") or ""))
        print("'verlangsamen' selection survives reload:", "active" in (await pg.get_attribute('#kippbildModeRow [data-kippbild-mode="verlangsamen"]', "class") or ""))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
