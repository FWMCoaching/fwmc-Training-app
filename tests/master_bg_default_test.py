import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- seed one exercise (Simon-Test) with its OWN explicit bg
        # choice BEFORE the Master default is ever touched, to prove it's
        # never overridden ----
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => {
            localStorage.setItem('fwmc-simon-prefs-v1', JSON.stringify({ bgColorKey: 'lila', bgIntensity: 0.7 }));
        }""")
        await pg.reload(); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- open Master-Einstellungen, set a default background colour ----
        await pg.click(".master-settings-btn"); await pg.wait_for_timeout(200)
        print("master sheet open:", await pg.is_visible("#masterSettingsSheet"))
        print("no default set yet - 'Keinen Standard' hidden:", await pg.is_hidden("#masterBgNoneBtn"))
        await pg.click('#masterBgColorPicker [data-key="rot"]'); await pg.wait_for_timeout(150)
        print("intensity row now visible:", await pg.is_visible("#masterBgIntensityRow"))
        print("intensity jumped to 50% on first pick:", "50%" in await pg.inner_text("#masterBgIntensityValue"))
        print("'Keinen Standard' now visible:", await pg.is_visible("#masterBgNoneBtn"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- a never-touched exercise (Go/No-Go) must now start at the
        # Master default ----
        raw_gng = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gng-prefs-v1') || '{}')")
        print("Go/No-Go seeded with Master default colour (rot):", raw_gng.get("bgColorKey") == "rot")
        print("Go/No-Go seeded with Master default intensity (50%):", raw_gng.get("bgIntensity") == 0.5)

        # ---- the pre-seeded Simon-Test exercise must be UNTOUCHED ----
        raw_simon = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-simon-prefs-v1') || '{}')")
        print("Simon-Test (pre-existing own choice) still lila, not overridden:", raw_simon.get("bgColorKey") == "lila")
        print("Simon-Test intensity still 0.7, not overridden:", raw_simon.get("bgIntensity") == 0.7)

        # ---- Go/No-Go's own settings screen shows the seeded colour. Test-
        # Bereich exercises deliberately have no "transfer" row at all (an
        # earlier, separate scope decision - see CLAUDE.md), so no "Wie in
        # den Master-Einstellungen" button is expected here; the automatic
        # seeding above is their whole story. ----
        await pg.click('.section-tab[data-section="test"]'); await pg.wait_for_timeout(200)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#gngAdvanced summary"); await pg.wait_for_timeout(150)
        print("Go/No-Go bg picker shows rot as active:", "active" in (await pg.get_attribute('#gngBgColorPicker [data-key="rot"]', "class") or ""))
        print("Go/No-Go has no transfer row (expected - Test-Bereich scope decision):", "Wie in den Grundeinstellungen" not in await pg.inner_text("#gngAdvanced"))
        await pg.click("#gngReadyBackToHome"); await pg.wait_for_timeout(200)

        # ---- Remember (one of the 4 richer NAT domains that already had a
        # transfer row before this feature) offers the one-click Master
        # button, and using it actually applies the Master colour ----
        await pg.click('#testHome .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(200)
        await pg.click("#rememberAdvanced summary"); await pg.wait_for_timeout(150)
        print("Remember offers the Master transfer button:", "Wie in den Grundeinstellungen" in await pg.inner_text("#rememberAdvanced"))
        await pg.click('#rememberAdvanced >> text="Wie in den Grundeinstellungen"'); await pg.wait_for_timeout(150)
        print("Remember switched to rot after tapping the Master button:", "active" in (await pg.get_attribute('#rememberBgColorPicker [data-key="rot"]', "class") or ""))

        # ---- clearing the Master default doesn't retroactively undo
        # anything already seeded ----
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(200)
        await pg.click('#natHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(200)
        await pg.click(".master-settings-btn"); await pg.wait_for_timeout(200)
        await pg.click("#masterBgNoneBtn"); await pg.wait_for_timeout(150)
        print("cleared: picker shows no active swatch:", await pg.locator("#masterBgColorPicker .color-swatch.active").count() == 0)
        print("cleared: 'Keinen Standard' hidden again:", await pg.is_hidden("#masterBgNoneBtn"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        raw_gng_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gng-prefs-v1') || '{}')")
        print("Go/No-Go still rot after clearing Master default (no retroactive undo):", raw_gng_after.get("bgColorKey") == "rot")

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
