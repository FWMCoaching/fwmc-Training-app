import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Per-exercise "Auf Standard zurücksetzen" + "Master-Einstellungen aktiv"
# hint, and the global "Alle eigenen Hintergrundfarben zurücksetzen" in
# Master-Einstellungen. Client's ask: simple version (no separate opt-out
# toggle, no full factory reset) plus the "Master aktiv" indicator with a
# link back to Master-Einstellungen.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        pg.on("dialog", lambda d: asyncio.ensure_future(d.accept()))

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- Go/No-Go, never touched, no Master default yet: nothing shown ----
        await pg.click('.section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.querySelector('#gngAdvanced').open = true"); await pg.wait_for_timeout(100)
        print("no reset button, no master hint (nothing set yet):", (await pg.inner_text("#gngBgMasterStatus")).strip() == "")

        # ---- set a Master default - never-touched Go/No-Go should now
        # show 'Master-Einstellungen aktiv' ----
        await pg.click("#gngReadyBackToHome"); await pg.wait_for_timeout(200)
        await pg.click("#testHome .master-settings-btn"); await pg.wait_for_timeout(200)
        await pg.click('#masterBgColorPicker [data-key="rot"]'); await pg.wait_for_timeout(100)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.querySelector('#gngAdvanced').open = true"); await pg.wait_for_timeout(100)
        print("master hint now visible:", "Master-Einstellungen aktiv" in await pg.inner_text("#gngBgMasterStatus"))
        print("gng picker shows rot as active (following master):", "active" in (await pg.get_attribute('#gngBgColorPicker [data-key="rot"]', "class") or ""))

        # ---- click the master-hint's link -> jumps to Master-Einstellungen ----
        await pg.click('#gngBgMasterStatus button:has-text("zu den Einstellungen")'); await pg.wait_for_timeout(200)
        print("link opens Master-Einstellungen:", await pg.is_visible("#masterSettingsSheet"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- customize Go/No-Go's own colour -> master hint replaced by
        # a reset button ----
        await pg.click('#gngBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
        print("reset button shown after customizing:", "Auf Standard zurücksetzen" in await pg.inner_text("#gngBgMasterStatus"))
        print("master hint gone after customizing:", "Master-Einstellungen aktiv" not in await pg.inner_text("#gngBgMasterStatus"))
        raw_gng = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gng-prefs-v1') || '{}')")
        print("customization persisted (gelb):", raw_gng.get("bgColorKey") == "gelb")

        # ---- reset it: back to following Master (rot) ----
        await pg.click('#gngBgMasterStatus button:has-text("Auf Standard zurücksetzen")'); await pg.wait_for_timeout(150)
        print("picker shows rot again after reset:", "active" in (await pg.get_attribute('#gngBgColorPicker [data-key="rot"]', "class") or ""))
        print("master hint shown again after reset:", "Master-Einstellungen aktiv" in await pg.inner_text("#gngBgMasterStatus"))
        raw_gng2 = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gng-prefs-v1') || '{}')")
        print("reset persisted (rot, following master again):", raw_gng2.get("bgColorKey") == "rot")

        await pg.click("#gngReadyBackToHome"); await pg.wait_for_timeout(200)

        # ---- Simon-Test: pre-seed its OWN explicit colour before touching
        # anything else, to prove the global reset actually reaches it too ----
        await pg.evaluate("""() => {
            localStorage.setItem('fwmc-simon-prefs-v1', JSON.stringify({ bgColorKey: 'lila', bgIntensity: 0.7 }));
        }""")
        await pg.reload(); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.querySelector('#simonAdvanced').open = true"); await pg.wait_for_timeout(100)
        print("Simon-Test shows its own reset button (pre-existing custom colour):", "Auf Standard zurücksetzen" in await pg.inner_text("#simonBgMasterStatus"))
        await pg.click("#simonReadyBackToHome"); await pg.wait_for_timeout(200)

        # ---- global reset in Master-Einstellungen ----
        await pg.click("#testHome .master-settings-btn"); await pg.wait_for_timeout(200)
        await pg.click("#masterBgResetAllBtn"); await pg.wait_for_timeout(200)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        raw_simon_after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-simon-prefs-v1') || '{}')")
        print("Simon-Test reset by the global button (now rot, following master):", raw_simon_after.get("bgColorKey") == "rot")
        print("Simon-Test bgCustom cleared:", raw_simon_after.get("bgCustom") == False)

        await pg.click("#simonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("document.querySelector('#simonAdvanced').open = true"); await pg.wait_for_timeout(100)
        print("Simon-Test shows master hint after global reset:", "Master-Einstellungen aktiv" in await pg.inner_text("#simonBgMasterStatus"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
