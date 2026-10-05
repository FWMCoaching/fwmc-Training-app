import asyncio
from playwright.async_api import async_playwright

# Einheitliche Steuerung (Fabian, 2026-10-05): generic 3-2-1 lead-in before
# exercises without their own countdown, its switch in the Grundeinstellungen,
# one sound switch in the step bar + Grundeinstellungen, and the back button
# top left in the logo bar (pages) and in the bar over pauses/results.
URL = "http://localhost:8845/index.html?bereich=movement"
ok_all = True
def check(label, ok):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok))

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-leadin','true')")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(300)

        check("no back button on an area home", not await pg.is_visible("#movementHome .bar-back-btn"))
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        check("back button in the logo bar of a sub page", await pg.is_visible("#movementReady .bar-back-btn"))
        box = await pg.locator("#movementReady .bar-back-btn").bounding_box()
        check("back button is 44 px and top left", box and box["width"] >= 44 and box["height"] >= 44 and box["x"] < 40)
        await pg.click("#movementReady .bar-back-btn"); await pg.wait_for_timeout(200)
        check("back button returns to the area home", await pg.is_visible("#movementHome"))

        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(200)
        check("lead-in shows 3", await pg.is_visible("#leadIn") and (await pg.inner_text("#leadInNum")).strip() == "3")
        check("player not started yet", not await pg.is_visible("#movementPlayer"))
        await pg.click("#leadInCancelBtn"); await pg.wait_for_timeout(1500)
        check("Abbrechen stops it", not await pg.is_visible("#leadIn") and not await pg.is_visible("#movementPlayer"))

        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(3500)
        check("player starts after 3-2-1", await pg.is_visible("#movementPlayer") and not await pg.is_visible("#leadIn"))
        check("sound switch in the step bar", await pg.is_visible("#stepNav #stepSoundBtn"))
        await pg.click("#stepSoundBtn"); await pg.wait_for_timeout(100)
        check("sound switch mutes", "is-off" in (await pg.get_attribute("#stepSoundBtn", "class") or "")
              and await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-workout-sound-v1')).enabled === false"))
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(300)
        check("no second exit over the pause (Beenden is right there)", not await pg.is_visible("#appBar .bar-back-btn"))
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(400)
        check("results: back button in the top bar", await pg.is_visible("#appBar .bar-back-btn") or not await pg.is_visible("#movementPlayer"))

        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click(".master-settings-btn >> visible=true"); await pg.wait_for_timeout(200)
        check("Grundeinstellungen show sound off", not await pg.is_checked("#masterSoundCheck"))
        check("countdown switch on by default", await pg.is_checked("#masterStartCountdownCheck"))
        await pg.click("#masterSoundCheck"); await pg.click("#masterStartCountdownCheck")
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        check("sound back on", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-workout-sound-v1')).enabled === true"))
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        check("countdown off: starts directly", await pg.is_visible("#movementPlayer") and not await pg.is_visible("#leadIn"))
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        await pg.reload(); await pg.wait_for_timeout(300)
        check("countdown setting persists", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-master-prefs-v1') || '{}').startCountdown") is False
              or await pg.evaluate("Object.keys(localStorage).some(k => k.includes('master') && (localStorage.getItem(k)||'').includes('\"startCountdown\":false'))"))

        # Visual Training without countdown still runs (no 3-2-1 frames)
        await pg.goto("http://localhost:8845/index.html?bereich=visual"); await pg.wait_for_timeout(300)
        await pg.locator(".excard[data-exercise]").first.click(); await pg.wait_for_timeout(200)
        await pg.locator("#startBtn").click(); await pg.wait_for_timeout(1500)
        check("VT runs with countdown off", await pg.is_visible("#player"))
        await b.close()
    check("No page errors", not errors)
    if errors: print(errors[:3])
    print("ALL OK:", ok_all)

asyncio.run(main())
