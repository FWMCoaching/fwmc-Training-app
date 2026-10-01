import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Cardio's "Nächste Aktivität" button used to be one-directional (forward-
# only, dynamic text label). The client asked for the same bidirectional
# chapter-nav Tabata already has (« vorherige / restart / weiter »), plus
# the ability to restart the current activity and to swipe. Cardio's own
# engine is index-based (cardioState.index/blockStartTime), unlike
# Tabata's frame-schedule-offset one - cardioJumpToIndex() jumps the index
# directly and resets blockStartTime, skipping over the interleaved pause
# pseudo-items in whichever direction it's travelling (a pause is never
# adjacent to another pause).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Rad fahren"'); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Walking"'); await pg.wait_for_timeout(100)

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("all three chapter-nav buttons visible:",
              await pg.is_visible("#cardioPrevBtn") and await pg.is_visible("#cardioRestartBtn") and await pg.is_visible("#cardioSkipBtn"))
        print("first activity shown (Joggen):", "Joggen" in await pg.inner_text("#cardioActivityTitle"))

        # ---- skip forward past the pause onto activity 2 ----
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(150)
        print("skip » lands on activity 2 (Rad fahren), not the pause:",
              "Rad fahren" in await pg.inner_text("#cardioActivityTitle"))

        # ---- restart: stays on the same activity, just resets its clock ----
        await pg.wait_for_timeout(1200)
        countdown_before = await pg.inner_text("#cardioCountdown")
        await pg.click("#cardioRestartBtn"); await pg.wait_for_timeout(150)
        countdown_after = await pg.inner_text("#cardioCountdown")
        print("restart stays on the same activity (Rad fahren):", "Rad fahren" in await pg.inner_text("#cardioActivityTitle"))
        print("restart resets the countdown (not still counting down from before):", countdown_after != countdown_before)

        # ---- prev « goes back past the pause onto activity 1 ----
        await pg.click("#cardioPrevBtn"); await pg.wait_for_timeout(150)
        print("prev « lands back on activity 1 (Joggen), not the pause:",
              "Joggen" in await pg.inner_text("#cardioActivityTitle"))

        # ---- prev at the very first activity just restarts it (no crash,
        # no negative index) ----
        await pg.click("#cardioPrevBtn"); await pg.wait_for_timeout(150)
        print("prev at the first activity stays on it instead of erroring out:",
              "Joggen" in await pg.inner_text("#cardioActivityTitle") and await pg.is_visible("#cardioPlayer"))

        # ---- skip all the way to the end finishes the session, same as
        # running out the clock naturally would - back at Joggen (activity
        # 1), so it takes two more skips to reach Walking (activity 3) ----
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(150)
        print("skip forward back on activity 2 (Rad fahren):", "Rad fahren" in await pg.inner_text("#cardioActivityTitle"))
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(150)
        print("skip forward now on activity 3 (Walking):", "Walking" in await pg.inner_text("#cardioActivityTitle"))
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(300)
        print("skipping past the last activity finishes the session:", await pg.is_visible("#cardioDonePanel"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
