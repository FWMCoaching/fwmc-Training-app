import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# The top-level section-switch (6 tabs since "Test" was added) and NAT's own
# sub-switch (5 tabs since Objektverfolgung (MOT) was added) are flex rows of
# flex:1 tabs. Without min-width:0, a flex item can't shrink below its
# content's natural min-content width, so once enough tabs share the row a
# German-length label (esp. one unbreakable compound word like
# "Atemtraining") pushes the whole bar wider than the viewport instead of
# actually sharing the space - the client caught this as the rightmost tab
# being clipped off the screen edge on an iPhone in portrait. Below
# ~480px both bars switch to a 3-per-row grid instead (roomier per label,
# no font shrinking needed); above that they stay the original single-row
# pill, just wider (580px/560px caps) so a 6th/5th tab still has enough
# room for its longest label to sit on one line without any mid-word break.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 375, "height": 812}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)

        async def no_overflow(width, height):
            await pg.set_viewport_size({"width": width, "height": height})
            await pg.wait_for_timeout(120)
            box = await pg.evaluate("""(w) => {
                const sub = document.querySelector('#natHome .sub-switch');
                const sec = document.querySelector('#natHome .section-switch');
                const noOverflow = el => !el || el.scrollWidth <= el.clientWidth + 1;
                return { sub: noOverflow(sub), sec: noOverflow(sec), body: document.body.scrollWidth <= w + 1 };
            }""", width)
            return box

        for w, h in [(360, 780), (375, 812), (390, 844), (414, 896), (430, 932)]:
            r = await no_overflow(w, h)
            print(f"{w}px portrait - no overflow (section={r['sec']}, sub={r['sub']}, body={r['body']}):", all(r.values()))

        # a comfortably wide viewport should use the original single-row
        # pill (not the narrow-phone grid), with no overlapping labels
        await pg.set_viewport_size({"width": 768, "height": 1024}); await pg.wait_for_timeout(150)
        display = await pg.evaluate("() => getComputedStyle(document.querySelector('#natHome .section-switch')).display")
        print("wide viewport keeps the single-row pill (flex, not grid):", display == "flex")
        r = await no_overflow(768, 1024)
        print("768px - no overflow:", all(r.values()))
        # :not([hidden]) - the "Test" tab is hidden-by-default (client
        # request, 2026-10-01, see CLAUDE.md), so this bar can legitimately
        # render fewer than 6 tabs; a hidden element's rect collapses to
        # (0,0,0,0), which would otherwise read as a false "overlap"
        # against the real last tab's right edge.
        rects = await pg.evaluate("""() => [...document.querySelectorAll('#natHome .section-switch .section-tab:not([hidden])')].map(el => el.getBoundingClientRect())""")
        overlaps = any(rects[i]["right"] > rects[i + 1]["left"] for i in range(len(rects) - 1))
        print("no tab overlaps its neighbour at 768px:", not overlaps)

        # a narrow phone should have switched to the 3-per-row grid
        await pg.set_viewport_size({"width": 375, "height": 812}); await pg.wait_for_timeout(150)
        display_narrow = await pg.evaluate("() => getComputedStyle(document.querySelector('#natHome .section-switch')).display")
        print("narrow viewport uses the 3-per-row grid:", display_narrow == "grid")

        # --- client-reported (iPad screenshot): with "Test" unlocked, the
        # TOP-LEVEL section-switch goes from 6 to 7 tabs, and the old 580px
        # cap (sized for 6, see styles.css's own comment) left too little
        # room per tab - "Atemtraining" (one unbreakable compound word, no
        # space to wrap at) got cut mid-word into "Atemtraini"/"ng" on a
        # tablet-width screen. body.nav-test-unlocked widens the cap to
        # 680px whenever applyTestTabVisibility() finds the unlock flag.
        # A container-level scrollWidth<=clientWidth check (like no_overflow()
        # above) can't catch this - the container itself never overflows,
        # only one tab's own text wraps inside it - so this compares
        # "Atemtraining"'s rendered height against "Movement"'s (same font/
        # padding, short enough to never wrap): equal height = one line = no
        # mid-word break; taller = it wrapped, and since it has no space to
        # break at, that always means the bad case.
        await pg.evaluate("() => localStorage.setItem('fwmc-test-unlocked', 'true')")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.set_viewport_size({"width": 768, "height": 1024}); await pg.wait_for_timeout(150)
        tab_count = await pg.locator('#home .section-switch .section-tab:not([hidden])').count()
        print("Test unlocked -> 8 tabs now shown (incl. Heute):", tab_count == 8)
        heights = await pg.evaluate("""() => ({
            atem: document.querySelector('#home .section-tab[data-section="breath"]').getBoundingClientRect().height,
            movement: document.querySelector('#home .section-tab[data-section="movement"]').getBoundingClientRect().height,
        })""")
        print("'Atemtraining' stays one line (no mid-word break) at 768px with Test unlocked:", abs(heights["atem"] - heights["movement"]) < 2)

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
