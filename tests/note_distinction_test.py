import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/note_shot.png"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        # add one built-in exercise (has a general note)
        await pg.locator("#workoutCircuitAddGrid .combo-add-btn").nth(0).click(); await pg.wait_for_timeout(150)
        # set a custom personal note on it
        await pg.fill(".circuit-item-note", "Heute langsamer wegen Knie")
        await pg.locator(".circuit-item-note").dispatch_event("change")
        await pg.wait_for_timeout(150)

        # jump straight to the "work" phase by shrinking prep time via direct JS start
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)
        print("tabata player visible:", await pg.is_visible("#workoutTabataView"))
        # fast-forward past the 5s prep phase by rewinding workoutState.startTime
        await pg.evaluate("() => { window.__wsHack = true; }")
        await pg.wait_for_timeout(5300)  # let prep phase pass naturally

        general_note_text = await pg.inner_text("#tabataExerciseNote")
        general_note_hidden = await pg.is_hidden("#tabataExerciseNote")
        custom_note_visible = await pg.is_visible("#tabataExerciseCustomNote")
        custom_note_html = await pg.inner_html("#tabataExerciseCustomNote") if custom_note_visible else ""
        print("general note text:", repr(general_note_text), "hidden:", general_note_hidden)
        print("custom note visible:", custom_note_visible)
        print("custom note html:", repr(custom_note_html))
        assert "Heute langsamer wegen Knie" in custom_note_html
        assert "Deine Notiz" in custom_note_html
        assert general_note_text != "" and "Heute langsamer" not in general_note_text
        await pg.screenshot(path=OUT)
        print("screenshot saved")

        if await pg.is_visible("#workoutBackBtn"):
            await pg.click("#workoutBackBtn")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
