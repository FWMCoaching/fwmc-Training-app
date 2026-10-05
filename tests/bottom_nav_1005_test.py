import asyncio
from playwright.async_api import async_playwright

# Untere Navigationsleiste (Fabian, 2026-10-05: "Probieren wir den Schritt
# aus"): Heute, Training, Fortschritt, Mehr; in Übungen ausgeblendet; die
# Bereiche hängen unter Training mit ‹ zurück; die 8 Reiter oben entfallen.
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

ACTIVE = "() => [...document.querySelectorAll('#bottomNav .bottom-nav-btn.active')].map(b => b.dataset.nav).join(',')"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for vw, vh in [(390, 844), (1024, 768)]:
            ctx = await b.new_context(viewport={"width": vw, "height": vh}, service_workers="block")
            await ctx.add_init_script(INIT + "localStorage.setItem('fwmc-test-bottomnav','true')")
            await ctx.route("**/workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            await pg.goto(BASE); await pg.wait_for_timeout(300)
            t = f"[{vw}] "
            check(t + "bottom bar visible on Heute", await pg.is_visible("#bottomNav"))
            labels = await pg.eval_on_selector_all("#bottomNav .bottom-nav-btn span", "els => els.map(e => e.textContent)")
            check(t + "four tabs in order", labels == ["Heute", "Training", "Fortschritt", "Mehr"], labels)
            check(t + "Heute active", await pg.evaluate(ACTIVE) == "today")
            boxes = await pg.eval_on_selector_all("#bottomNav .bottom-nav-btn", "els => els.map(e => { const r = e.getBoundingClientRect(); return [r.width, r.height, r.bottom]; })")
            check(t + "tabs are big enough to tap", all(w >= 44 and h >= 44 for w, h, _ in boxes), boxes)
            check(t + "bar sits at the bottom", all(abs(bt - vh) < 12 for _, _, bt in boxes), boxes)
            check(t + "old 8-tab grid hidden", not await pg.is_visible("#todayHome .section-switch"))
            check(t + "Bereiche tiles gone from Heute", not await pg.is_visible("#todayHome .today-areas"))
            await pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); await pg.wait_for_timeout(100)
            fb = await pg.evaluate("document.querySelector('#todayHome .site-footer').getBoundingClientRect().bottom")
            nt = await pg.evaluate("document.getElementById('bottomNav').getBoundingClientRect().top")
            check(t + "footer not hidden under the bar", fb <= nt + 1, (fb, nt))

            await pg.click('[data-nav="training"]'); await pg.wait_for_timeout(200)
            check(t + "Training shows all areas", await pg.is_visible("#trainingHub") and await pg.locator("#hubAreaGrid .area-tile").count() == 6)
            check(t + "Training active", await pg.evaluate(ACTIVE) == "training")
            check(t + "Kombi-Programm entry on Training", await pg.is_visible("#trainingHub .combo-entry-link"))
            await pg.click('#hubAreaGrid [data-area="nat"]'); await pg.wait_for_timeout(200)
            check(t + "tile opens the area", await pg.is_visible("#natHome"))
            check(t + "Training stays active inside an area", await pg.evaluate(ACTIVE) == "training")
            check(t + "area home has ‹ back", await pg.is_visible("#natHome > .brandbar .bar-back-btn"))
            await pg.click("#natHome > .brandbar .bar-back-btn"); await pg.wait_for_timeout(200)
            check(t + "‹ leads back to Training", await pg.is_visible("#trainingHub"))

            await pg.click('[data-nav="progress"]'); await pg.wait_for_timeout(200)
            check(t + "Fortschritt opens", await pg.is_visible("#progressScreen") and await pg.evaluate(ACTIVE) == "progress")
            check(t + "no back button on a main tab", not await pg.is_visible("#progressScreen .bar-back-btn"))

            await pg.click('[data-nav="more"]'); await pg.wait_for_timeout(200)
            check(t + "Mehr opens", await pg.is_visible("#moreScreen") and await pg.evaluate(ACTIVE) == "more")
            check(t + "Mehr has the code card", await pg.is_visible("#moreScreen .code-card"))
            await pg.fill("#moreCodeInput", "gibtsnicht123"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
            check(t + "wrong code shows the error on Mehr", await pg.is_visible("#moreCodeError") and await pg.is_visible("#moreScreen"))
            await pg.click("#moreSettingsBtn"); await pg.wait_for_timeout(200)
            check(t + "Grundeinstellungen open from Mehr", await pg.is_visible("#masterSettingsSheet") if await pg.locator("#masterSettingsSheet").count() else await pg.evaluate("!![...document.querySelectorAll('.sheet')].find(s => !s.hidden)"))
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
            await pg.evaluate("[...document.querySelectorAll('.sheet')].forEach(s => s.hidden = true)")
            await pg.click("#moreScreen .more-list .faq-open-btn"); await pg.wait_for_timeout(200)
            check(t + "Häufige Fragen open from Mehr", await pg.is_visible("#faqSheet"))
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)

            await pg.click('[data-nav="training"]'); await pg.click('#hubAreaGrid [data-area="movement"]'); await pg.wait_for_timeout(200)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
            check(t + "bar still there on a sub page", await pg.is_visible("#bottomNav"))
            await pg.click("#movementStartBtn"); await pg.wait_for_timeout(400)
            check(t + "bar hidden during the exercise", not await pg.is_visible("#bottomNav"))
            await pg.click("#movementBackBtn"); await pg.wait_for_timeout(400)
            if await pg.is_visible("#confirmSheet"): await pg.click("#confirmOkBtn")
            await pg.wait_for_timeout(300)
            vis_screen = await pg.evaluate("!!document.querySelector('.screen:not([hidden])')")
            check(t + "bar back once a page shows again", (await pg.is_visible("#bottomNav")) == vis_screen, vis_screen)
            await ctx.close()

        # Test unlocked: Test tile in Training
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT + "localStorage.setItem('fwmc-test-bottomnav','true');localStorage.setItem('fwmc-test-unlocked','true')")
        pg = await ctx.new_page()
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        await pg.click('[data-nav="training"]'); await pg.wait_for_timeout(200)
        check("Test tile when unlocked", await pg.locator('#hubAreaGrid [data-area="test"]').count() == 1)
        await pg.click('#hubAreaGrid [data-area="test"]'); await pg.wait_for_timeout(200)
        check("Test tile opens Test", await pg.is_visible("#testHome"))
        await ctx.close()

        # automated runs without opt-in keep the old layout
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        check("without opt-in: no bottom bar, old tabs", not await pg.is_visible("#bottomNav") and await pg.is_visible("#todayHome .section-switch"))
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
