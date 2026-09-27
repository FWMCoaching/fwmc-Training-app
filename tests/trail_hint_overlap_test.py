import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Regression test for a real bug report (screenshot on an iPhone-width
# viewport): Trail Making Test's instruction line ("Tippe abwechselnd Zahl
# und Buchstabe in aufsteigender Reihenfolge an: 1, A, 2, B …") is much
# longer than the other exercises' short status blips that share the same
# .remember-hint pill - with the old forced white-space:nowrap it ran off
# both edges of a narrow phone screen, unreadable. Two fixes:
# 1. .remember-hint now wraps and is width-constrained (styles.css) so long
#    instructions stay fully on-screen instead of clipping.
# 2. trailStageBounds() now measures the hint's and player-bar's actual
#    rendered bottom edge (instead of a hardcoded pixel constant that didn't
#    account for the now-taller wrapped hint or device safe-area insets) and
#    keeps every marker clear of them.

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click('#testHome :text("Verbindungstest")'); await pg.wait_for_timeout(200)
        await pg.click('[data-trail-teil="b"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-trail-diff="schwer"]'); await pg.wait_for_timeout(100)
        await pg.click('#trailReadyStartBtn'); await pg.wait_for_timeout(400)

        r = await pg.evaluate("""
            () => {
              const vw = window.innerWidth;
              const hint = document.getElementById('trailHint').getBoundingClientRect();
              const bar = document.getElementById('trailPlayerBar').getBoundingClientRect();
              const markers = [...document.querySelectorAll('.trail-marker')].map(m => m.getBoundingClientRect());
              const overlaps = (a, b) => !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
              return {
                vw, hint,
                hintClipped: hint.left < 0 || hint.right > vw,
                hintWrapped: hint.height > 40,
                markerCount: markers.length,
                markerVsHintCount: markers.filter((m) => overlaps(m, hint)).length,
                markerVsBarCount: markers.filter((m) => overlaps(m, bar)).length,
              };
            }
        """)
        print("Teil B, 25 Felder, 390px viewport:", r)
        assert not r["hintClipped"], "instruction text runs off-screen"
        assert r["hintWrapped"], "expected the long Teil-B instruction to wrap onto multiple lines"
        assert r["markerCount"] == 25
        assert r["markerVsHintCount"] == 0, "a marker overlaps the instruction hint"
        assert r["markerVsBarCount"] == 0, "a marker overlaps the player bar"
        print("ERRORS: []")
        await b.close()

asyncio.run(main())
