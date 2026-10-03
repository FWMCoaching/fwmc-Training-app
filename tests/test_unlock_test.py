import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Client request (2026-10-01): the "Test" section tab should not be visible
# to anyone by default - only someone who's been given a specific word gets
# it, permanently, on that browser. Implemented as a local-only gate (no
# server involved): the "Test" tab is hidden via applyTestTabVisibility()
# unless localStorage['fwmc-test-unlocked'] is set, and typing
# TEST_UNLOCK_WORD ("testbereich-frei") into ANY section's existing code box
# (they all funnel through openProgramIntro()) sets that flag and jumps
# straight into testHome instead of doing a real program lookup. This is
# obscurity for a soft/staged rollout, not real access control - the word
# lives in this same public app.js as everything else - so this test only
# checks the UX mechanics (hidden by default, revealed + persists after the
# right word, a wrong code behaves exactly like any other unknown code).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

        # ---- fresh browser: Test tab hidden everywhere, nothing unlocked ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        print("Test tab hidden on fresh visit:", await pg.is_hidden('#home .section-tab[data-section="test"]'))
        unlocked = await pg.evaluate("() => localStorage.getItem('fwmc-test-unlocked')")
        print("no unlock flag stored yet:", unlocked is None)

        # ---- every public FAQ/welcome-text mention of Test is ALSO hidden
        # until unlocked (client, 2026-10-01: promoting a hidden feature in
        # public copy defeats "soll nirgendwo auftauchen") ----
        print("welcome-text Test mention hidden:", await pg.get_attribute("#tipsWelcome .test-teaser", "hidden") is not None)
        await pg.click("#home .faq-open-btn"); await pg.wait_for_timeout(150)
        teaser_count = await pg.locator("#faqSheet .test-teaser").count()
        hidden_count = sum(1 for h in await pg.eval_on_selector_all("#faqSheet .test-teaser", "els => els.map(e => e.hidden)") if h)
        print(f"all {teaser_count} FAQ Test-teaser spots hidden:", teaser_count == hidden_count and teaser_count > 0)
        await pg.click("#faqCloseBtn"); await pg.wait_for_timeout(150)

        # ---- a WRONG code behaves like any other unknown code, tab stays hidden ----
        # The sandbox has no route to the Worker; answer like the real one does
        # for an unknown code, so the check doesn't depend on network timing.
        await pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
        await pg.fill("#programCodeInput", "definitely-not-a-real-code")
        await pg.click("#programGoBtn")
        await pg.wait_for_selector("#programError", state="visible", timeout=5000)
        print("wrong code shows the normal not-found error:", await pg.is_visible("#programError"))
        print("Test tab still hidden after a wrong code:", await pg.is_hidden('#home .section-tab[data-section="test"]'))

        # ---- the real unlock word, typed into Visual Training's own code box ----
        await pg.fill("#programCodeInput", "Testbereich-ein")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(400)
        print("jumps straight into testHome:", await pg.is_visible("#testHome"))
        print("Test tab now visible + active:", "active" in (await pg.get_attribute('#testHome .section-tab[data-section="test"]', "class") or ""))
        unlocked = await pg.evaluate("() => localStorage.getItem('fwmc-test-unlocked')")
        print("unlock flag now stored:", unlocked == "true")

        # ---- persists across a reload, and from every section's tab bar ----
        await pg.reload(); await pg.wait_for_timeout(400)
        print("Test tab visible again after reload:", await pg.is_visible('#home .section-tab[data-section="test"]'))
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        print("also visible from another section's own tab bar:", await pg.is_visible('#natHome .section-tab[data-section="test"]'))

        # ---- once unlocked: the teaser copy comes back, and testHome itself
        # carries a "Mit Code freigeschaltet" badge + a visibly different
        # accent colour (not --brand) so it never reads as a regular,
        # permanent part of the app ----
        print("welcome-text Test mention now shown:", await pg.get_attribute("#tipsWelcome .test-teaser", "hidden") is None)
        await pg.click('#natHome .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("'Mit Code freigeschaltet' badge visible on testHome:", await pg.is_visible(".test-unlock-badge"))
        kicker_color = await pg.evaluate("() => getComputedStyle(document.querySelector('#testHome .hero-kicker')).color")
        print("testHome's accent colour is amber (#b45309), not the teal brand colour:", kicker_color == "rgb(180, 83, 9)")

        # ---- the lock word hides it all again (typed into NAT's own box) ----
        await pg.click('#testHome .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.fill("#natProgramCodeInput", "testbereich-aus")
        await pg.click("#natProgramGoBtn"); await pg.wait_for_timeout(400)
        print("lock word lands back on natHome:", await pg.is_visible("#natHome"))
        print("no not-found error for the lock word:", await pg.is_hidden("#natProgramError"))
        print("Test tab hidden again after lock word:", await pg.is_hidden('#natHome .section-tab[data-section="test"]'))
        print("unlock flag removed:", await pg.evaluate("() => localStorage.getItem('fwmc-test-unlocked')") is None)
        print("welcome-text Test mention hidden again:", await pg.get_attribute("#tipsWelcome .test-teaser", "hidden") is not None)
        await pg.reload(); await pg.wait_for_timeout(400)
        print("still hidden after reload:", await pg.is_hidden('#home .section-tab[data-section="test"]'))

        # ---- old unlock word still works ----
        await pg.fill("#programCodeInput", "testbereich-frei")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(400)
        print("legacy word testbereich-frei still unlocks:", await pg.is_visible("#testHome"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
