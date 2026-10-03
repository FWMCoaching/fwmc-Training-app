import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Pause between Cardio activities - same client ask as the Kombi-Baukasten
# pause markers: per-activity adjustable (Material wechseln, Position
# einnehmen), Master default as starting value, always skippable.
#
# Cardio's tick loop compares requestAnimationFrame timestamps against a
# performance.now() blockStartTime (not setTimeout), and durationS has an
# enforced 60s floor (loadCardioPrefs), so this speeds up perceived time
# by warping BOTH performance.now() and the rAF callback's own timestamp
# onto the same accelerated clock (rAF keeps firing at the real rate;
# each frame just sees more virtual time having passed) - a plain
# performance.now() patch alone isn't enough, since rAF's timestamp
# argument comes from the browser's native scheduler, not from calling
# performance.now() itself.
SPEEDUP = """
  const realNow = performance.now.bind(performance);
  const realRAF = window.requestAnimationFrame.bind(window);
  const start = realNow();
  const factor = 15;
  const warp = (real) => start + (real - start) * factor;
  performance.now = () => warp(realNow());
  window.requestAnimationFrame = (cb) => realRAF((realTs) => cb(warp(realTs)));
"""

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        pg = await ctx.new_page()
        await ctx.add_init_script(SPEEDUP)
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # seed 3 activities at the shortest allowed duration (60s, floored
        # by loadCardioPrefs) - the performance.now() speedup above makes
        # this finish in a few real seconds instead of 3 real minutes
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => {
            localStorage.setItem('fwmc-cardio-v1', JSON.stringify({
                items: [
                    { activity: 'joggen', durationS: 60, label: '', interval: null },
                    { activity: 'rad', durationS: 60, label: '', interval: null },
                    { activity: 'cross', durationS: 60, label: '', interval: null },
                ],
                defaultDurationS: 600,
            }));
        }""")
        await pg.reload(); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- Master default pause at 30s (virtual) = 2s real with the
        # 15x speedup above - long enough to reliably observe/interact
        # with the pause screen before it would auto-continue ----
        await pg.click(".master-settings-btn"); await pg.wait_for_timeout(200)
        await pg.fill("#masterPauseSlider", "30")
        await pg.dispatch_event("#masterPauseSlider", "input")
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        print("3 activities loaded:", await pg.locator("#cardioList .circuit-item-row").count() == 3)

        pause_rows = pg.locator("#cardioList .combo-pause-row")
        print("exactly 2 pause rows (between 3 activities, none after the last):", await pause_rows.count() == 2)
        print("pause row defaults to the Master value (30s):", "30" in await pause_rows.first.inner_text())

        # ---- set the SECOND pause to 0s (skipped entirely), leave the
        # first at the 30s Master default ----
        await pg.fill("#cardioList .combo-pause-slider >> nth=1", "0")
        await pg.dispatch_event("#cardioList .combo-pause-slider >> nth=1", "input")
        await pg.wait_for_timeout(100)
        print("second pause value label updates to 0s:", "0" in await pause_rows.nth(1).inner_text())

        # ---- run: activity 1 (60s virtual / 15x = 4s real) -> pause
        # (visible, skippable) -> activity 2 -> NO pause screen at all
        # (set to 0s) -> activity 3 ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)
        print("cardio player visible:", await pg.is_visible("#cardioPlayer"))
        print("activity 1 title shown:", await pg.inner_text("#cardioActivityTitle") == "Joggen")
        print("progress shows activity 1 of 3:", "1 VON 3" in (await pg.inner_text("#cardioBlockProgress")).upper())

        await pg.wait_for_timeout(4000)  # activity 1's 60s (virtual) elapses
        print("pause phase shown after activity 1:", await pg.inner_text("#cardioActivityTitle") == "Pause")
        print("pause shows what's next:", "Rad fahren" in await pg.inner_text("#cardioActivityLabel"))
        # icon-only chapter-nav button now (cardioTick() swaps its
        # title/aria-label instead of textContent, see
        # cardio_chapter_nav_test.py) - the icon itself never changes
        print("skip button relabelled during pause:", (await pg.get_attribute("#cardioSkipBtn", "title")) == "Pause überspringen")

        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(300)
        print("skip jumps straight into activity 2:", await pg.inner_text("#cardioActivityTitle") == "Rad fahren")
        print("skip button label back to normal:", (await pg.get_attribute("#cardioSkipBtn", "title")) == "Weiter zur nächsten Aktivität")

        await pg.wait_for_timeout(4000)  # activity 2's 60s (virtual) elapses
        print("no pause screen shown (0s pause) - goes straight to activity 3:", await pg.inner_text("#cardioActivityTitle") == "Crosstrainer")

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
