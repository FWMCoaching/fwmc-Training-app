import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Reported bug: "Beenden" (#backBtn) inside a Cardio guest exercise
# (Zusatzimpuls) ended the ENTIRE Cardio session instead of just the guest
# exercise - abortTraining()'s cardioGuestActive branch called
# abortCardio() instead of returnFromCardioGuest(). A client who starts a
# guest exercise, doesn't want it after all (or wants to switch to a
# different one via the picker), needs to be able to bail out of just
# that without losing their running Cardio progress.

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
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)

        # ---- start a guest exercise via the live picker, give it a long
        # duration (well beyond this test) so ending it early via
        # "Beenden" is unambiguously an early abort, not a natural finish ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        print("guest exercise took over full-screen:", await pg.is_visible("#player"))

        # ---- "Beenden" mid-guest-exercise: must return to the still-
        # running Cardio session, NOT end the whole training ----
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        print("back at cardioPlayer (Cardio still running), not cardioReady/cardioHome:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))
        print("did NOT land back on cardioReady (that would mean the whole training ended):",
              await pg.is_hidden("#cardioReady"))
        print("trigger button available again for another try:", await pg.is_visible("#cardioAddonTriggerBtn"))
        print("badge cleared:", await pg.is_hidden("#cardioGuestBadge"))
        print("still the same activity (Joggen), not restarted:", "Joggen" in await pg.inner_text("#cardioActivityTitle"))

        # ---- repeatable: doing it again works the same way ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        print("second early-abort also returns to cardioPlayer:",
              await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))

        # ---- regression: Cardio's OWN "Beenden" (not inside a guest
        # exercise) still correctly ends the whole session as before ----
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("Cardio's own Beenden still ends the whole session:", await pg.is_visible("#cardioReady"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
