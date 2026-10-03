import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Task #20 (client: "Bei schlechten Kontrasten jeweils ein Hinweis Feld in
# den Einstellungen vorher und während der Übung, bei Anpassung einbauen -
# wer das Risiko eingehen will, ok"). The underlying contrast check
# (relLuma of the mixed background < 0.45) and its ready-screen hint
# element already existed for every exercise; the actual gap closed here
# is that the SAME hint text now also appears in the mid-session pause
# overlay (previously only the ready screen's hint element existed, so
# adjusting the colour live while paused showed no warning at all), and
# a brand-new hint on the Master-Einstellungen "Standard-Hintergrundfarbe"
# picker itself.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await (await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")).new_page()
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- Go/No-Go ready screen: never blocks, just warns ----
        await pg.click('.section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#gngOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngAdvanced summary"); await pg.wait_for_timeout(100)

        await pg.click('#gngBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
        print("light colour (gelb): ready hint hidden:", await pg.is_hidden("#gngBgContrastHint"))

        await pg.click('#gngBgColorPicker [data-key="schwarz"]'); await pg.wait_for_timeout(100)
        await pg.fill("#gngBgIntensitySlider", "1")
        await pg.dispatch_event("#gngBgIntensitySlider", "input")
        await pg.wait_for_timeout(100)
        print("dark colour (schwarz) at 100%: ready hint visible:", await pg.is_visible("#gngBgContrastHint"))
        print("ready hint text:", await pg.inner_text("#gngBgContrastHint"))
        print("start button NOT disabled/blocked by bad contrast (never-block requirement):", await pg.is_enabled("#gngReadyStartBtn"))

        # ---- start the exercise, pause it, confirm the SAME warning is
        # now visible in the pause overlay too (the actual gap this task
        # closes - previously nothing showed there) ----
        await pg.click("#gngReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#gngPauseBtn"); await pg.wait_for_timeout(200)
        print("pause overlay visible:", await pg.is_visible("#gngPauseOverlay"))
        print("pause hint ALREADY visible on entering pause (state carried over):", await pg.is_visible("#gngPauseBgContrastHint"))

        # switch to a light colour from inside the pause overlay - hint
        # must clear live, without leaving the pause overlay
        await pg.click('#gngPauseBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
        print("pause: switched to light colour, hint hides live:", await pg.is_hidden("#gngPauseBgContrastHint"))

        # switch back to a dark colour from inside the pause overlay
        await pg.click('#gngPauseBgColorPicker [data-key="schwarz"]'); await pg.wait_for_timeout(100)
        print("pause: switched back to dark colour, hint reappears live:", await pg.is_visible("#gngPauseBgContrastHint"))
        print("pause hint text:", await pg.inner_text("#gngPauseBgContrastHint"))

        await pg.click("#gngResumeBtn"); await pg.wait_for_timeout(150)
        await pg.click("#gngBackBtn"); await pg.wait_for_timeout(200)

        # ---- Master-Einstellungen: the "vorallem Main Einstellungen" part
        # of the client's ask - its own picker gets the identical hint ----
        await pg.click("#testHome .master-settings-btn"); await pg.wait_for_timeout(200)
        print("master bg hint hidden with no default set:", await pg.is_hidden("#masterBgContrastHint"))
        await pg.click('#masterBgColorPicker [data-key="schwarz"]'); await pg.wait_for_timeout(100)
        await pg.fill("#masterBgIntensitySlider", "1")
        await pg.dispatch_event("#masterBgIntensitySlider", "input")
        await pg.wait_for_timeout(100)
        print("master bg hint visible for dark colour at 100%:", await pg.is_visible("#masterBgContrastHint"))
        print("master bg hint text:", await pg.inner_text("#masterBgContrastHint"))
        await pg.click('#masterBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
        print("master bg hint hides again for light colour:", await pg.is_hidden("#masterBgContrastHint"))
        await pg.click("#masterBgNoneBtn"); await pg.wait_for_timeout(100)
        print("master bg hint hidden after clearing default:", await pg.is_hidden("#masterBgContrastHint"))
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
