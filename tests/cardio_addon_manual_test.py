import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Manual "+ Zusatzimpuls" trigger for Cardio's existing dual-task add-on
# system (cardio_test.py already covers the AUTOMATIC randomized-interval
# trigger). Client's ask: rather than only ever waiting for the random
# interval, actively switch a guest exercise on right now, mid-activity,
# whenever they feel like it - reuses the exact same triggerCardioGuest()
# random-pick-from-pool mechanism, just fired on demand instead of on a
# timer.

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

        # ---- sanity: button stays hidden the whole run when the add-on
        # system is off (the default) ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("cardioPlayer visible:", await pg.is_visible("#cardioPlayer"))
        print("trigger button hidden when add-on disabled:", await pg.is_hidden("#cardioAddonTriggerBtn"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("back at cardioReady (still has Joggen from before):", await pg.is_visible("#cardioReady"))

        # ---- configure the add-on: enable, pick a pool, long interval (so
        # the AUTOMATIC timer never fires during this test - only the
        # manual button should) ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check('#cardioAddonPoolGrid input[data-pool="vt-color"]'); await pg.wait_for_timeout(150)
        await pg.fill("#cardioAddonIntervalMinSlider", "600")
        await pg.dispatch_event("#cardioAddonIntervalMinSlider", "input")
        await pg.fill("#cardioAddonIntervalMaxSlider", "600")
        await pg.dispatch_event("#cardioAddonIntervalMaxSlider", "input")
        await pg.wait_for_timeout(150)
        # short guest-window duration so it finishes fast once triggered
        await pg.fill('.cardio-guest-panel input[data-f="duration"]', "5")
        await pg.dispatch_event('.cardio-guest-panel input[data-f="duration"]', "input")
        await pg.wait_for_timeout(150)

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("cardioPlayer visible:", await pg.is_visible("#cardioPlayer"))
        print("trigger button visible once add-on is configured:", await pg.is_visible("#cardioAddonTriggerBtn"))

        # ---- tap it: should switch to the guest exercise IMMEDIATELY, long
        # before the 600s auto-interval could ever fire ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(400)
        print("guest window (VT-Farbe) took over immediately on manual tap:",
              await pg.is_visible("#player") and not await pg.is_visible("#cardioPlayer"))

        # ---- let the 5s guest window finish on its own -> back to cardio,
        # button visible again, activity/timer picked up right where it
        # left off (not reset) ----
        await pg.wait_for_timeout(9000)
        print("returned to cardioPlayer after guest window finished:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))
        print("trigger button visible again after returning:", await pg.is_visible("#cardioAddonTriggerBtn"))
        print("still on the same activity (Joggen), not restarted:", "Joggen" in await pg.inner_text("#cardioActivityTitle"))

        # ---- repeatable: triggering it a second time (a legitimate,
        # ordinary second use - the button is visible and enabled again by
        # now) works just as well as the first ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(400)
        print("second manual trigger also takes over the screen:",
              await pg.is_visible("#player") and not await pg.is_visible("#cardioPlayer"))
        await pg.wait_for_timeout(9000)
        print("returns again after the second guest window finishes:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))

        # ---- guard: while a guest window is genuinely active, the button
        # is unreachable (its own screen - cardioPlayer - is hidden then),
        # but the click handler itself should still no-op safely if ever
        # invoked directly rather than firing a second, overlapping guest ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        print("third trigger takes over the screen:", await pg.is_visible("#player"))
        await pg.evaluate("document.getElementById('cardioAddonTriggerBtn').click()")
        await pg.wait_for_timeout(200)
        print("clicking again mid-guest-window does not start a second overlapping one:", await pg.is_visible("#player"))
        await pg.wait_for_timeout(9000)
        print("still returns cleanly to cardio after that:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))

        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("abort back at cardioReady:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
