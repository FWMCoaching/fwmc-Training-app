import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# "Test" is a 6th top-level section, alongside Visual Training/Atemtraining/
# Movement/Workout/NAT - an explicit experimentation area the client asked
# for: a place where new, self-contained visual/cognitive exercises get
# researched and built autonomously (see CLAUDE.md's "Test-Bereich"
# section), reviewed by the client, and only later sorted into a permanent
# home. This suite only covers the section-switcher scaffold (nav entry on
# every home screen, routing, empty state) - individual exercises added
# under Test get their own dedicated test files, same convention as NAT's
# Remember/Blitz/Flash/MOT.

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

        print("Test tab present on visual home:", await pg.is_visible('#home .section-tab[data-section="test"]'))
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        print("testHome visible:", await pg.is_visible("#testHome"))
        print("Test tab marked active:", "active" in (await pg.get_attribute('#testHome .section-tab[data-section="test"]', "class") or ""))
        print("empty-state hint visible when no exercises added yet:", await pg.is_visible("#testEmptyHint"))

        # navigate to every other section from Test and back, to confirm the
        # tab bar + showScreen wiring didn't regress anything for the others
        for sec, home in [("nat", "#natHome"), ("workout", "#workoutHome"), ("movement", "#movementHome"), ("breath", "#breathHome"), ("visual", "#home")]:
            await pg.click(f'#testHome .section-tab[data-section="{sec}"]'); await pg.wait_for_timeout(120)
            print(f"navigated to {sec}:", await pg.is_visible(home))
            await pg.click(f'{home} .section-tab[data-section="test"]'); await pg.wait_for_timeout(120)
            print(f"back to testHome from {sec}:", await pg.is_visible("#testHome"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
