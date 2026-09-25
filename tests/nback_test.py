import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Positions-Gedächtnis (N-Back): the second exercise added under the
# autonomous "Test" section (built the same firing that also fixed the
# first exercise's missing git push - see CLAUDE.md's Test-Bereich
# section). Classic spatial N-back working-memory task: one cell in a 3x3
# grid lights up per trial; the client taps "Übereinstimmung!" whenever the
# current position matches the one shown N trials back. Each trial cycle is
# stimulus (NBACK_STIMULUS_MS) + ISI (NBACK_ISI_MS) - correctness for a
# trial can only be judged once its full response window closes, so the
# correct/wrong flash on the match button is DEFERRED to the end of that
# window (testNbackEndTrial), not shown immediately on tap. Level adapts
# per Jaeggi et al. 2008's rule: <=2 errors in a block -> N goes up, >5 ->
# N goes down, otherwise unchanged - so this reports "highest N reached"
# rather than a fixed level like Remember/Blitz/Flash/MOT use.

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

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("N-Back card visible:", await pg.is_visible("#testNbackOpenBtn"))
        print("Go/No-Go card still visible (no collision between the two Test exercises):", await pg.is_visible("#gngOpenBtn"))
        await pg.click("#testNbackOpenBtn"); await pg.wait_for_timeout(150)
        print("testNbackReady visible:", await pg.is_visible("#testNbackReady"))

        await pg.click('#testNbackStartRow [data-nback-start="1"]'); await pg.wait_for_timeout(60)
        await pg.click("#testNbackReadyStartBtn"); await pg.wait_for_timeout(200)
        print("testNbackPlayer visible:", await pg.is_visible("#testNbackPlayer"))
        print("3x3 grid rendered:", await pg.locator("#testNbackGrid .nback-cell").count() == 9)
        print("level label shows Stufe 1:", "Stufe 1" in (await pg.inner_text("#testNbackLevelEl")))

        # a cell actually lights up during the "show" phase
        lit_seen = False
        for _ in range(60):
            if await pg.locator("#testNbackGrid .nback-cell.lit").count() == 1:
                lit_seen = True
                break
            await pg.wait_for_timeout(50)
        print("exactly one cell lights up per trial:", lit_seen)

        # tap the match button, then poll for the deferred correct/wrong
        # flash - it only fires at end-of-trial (stimulus + ISI later), not
        # immediately on tap
        await pg.click("#testNbackMatchBtn")
        flashed = False
        for _ in range(80):
            cls = (await pg.get_attribute("#testNbackMatchBtn", "class") or "").split()
            if "correct" in cls or "wrong" in cls:
                flashed = True
                break
            await pg.wait_for_timeout(50)
        print("match button eventually gets deferred correct/wrong feedback:", flashed)

        # pause/resume
        await pg.click("#testNbackPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#testNbackPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#testNbackPauseBtn"))
        lit_before = await pg.locator("#testNbackGrid .nback-cell.lit").count()
        await pg.wait_for_timeout(600)
        lit_after = await pg.locator("#testNbackGrid .nback-cell.lit").count()
        print("grid state frozen while paused:", lit_before == lit_after)
        await pg.click("#testNbackResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#testNbackPauseOverlay"))

        # Beenden mid-run -> either done panel (progress made) or straight back to testHome
        await pg.wait_for_timeout(2000)
        await pg.click("#testNbackBackBtn"); await pg.wait_for_timeout(150)
        back_home = await pg.is_visible("#testHome")
        done_panel = await pg.is_visible("#testNbackDonePanel")
        print("Beenden lands on testHome or the done panel:", back_home or done_panel)
        if done_panel:
            print("done summary mentions N-Back / Stufe:", "N-Back" in (await pg.inner_text("#testNbackDoneSummary")) or "Stufe" in (await pg.inner_text("#testNbackDoneSummary")))
            await pg.click("#testNbackDoneBackBtn"); await pg.wait_for_timeout(150)
            print("back at testHome:", await pg.is_visible("#testHome"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
