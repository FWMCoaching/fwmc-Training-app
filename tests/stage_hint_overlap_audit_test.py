import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Broader audit triggered by a user report (screenshot of Trail Making's
# instruction text running off both edges of an iPhone screen, with markers
# rendered right up against the top bar): every exercise whose stage fills
# the WHOLE player from y=0 (".remember-stage/.trail-stage/.search-stage/
# .corsi-stage/.reakt-stage/.mot-objects{inset:0}", all `flex:1;position:
# relative`) has the instruction hint (".remember-hint") and player-bar
# floating on top via z-index - a hardcoded pixel minY couldn't account for
# wrapped-hint height or device safe-area insets. Fixed via the shared
# stageTopClearanceY() helper (app.js), applied to: rememberStageBounds,
# trailStageBounds, searchStageBounds, corsiStageBounds, reaktStageBounds,
# and MOT's continuous bounce physics (motState.topMinY - objects there
# drift for the whole tracking phase, not just at initial placement).
# Merkspanne-Test is NOT in this list: its .merk-field is a smaller,
# normal-flow sub-box centred within .merk-stage, so it never starts at
# y=0 and was never at risk the same way.

def overlaps(a, b):
    return not (a["right"] < b["left"] or a["left"] > b["right"] or a["bottom"] < b["top"] or a["top"] > b["bottom"])

async def check_markers(pg, hint_id, bar_id, marker_sel, label):
    r = await pg.evaluate("""
        ([hintId, barId, markerSel]) => {
          const hint = document.getElementById(hintId).getBoundingClientRect();
          const bar = document.getElementById(barId).getBoundingClientRect();
          const markers = [...document.querySelectorAll(markerSel)].map((m) => m.getBoundingClientRect());
          return { hint, bar, markers, count: markers.length };
        }
    """, [hint_id, bar_id, marker_sel])
    hint = {"left": r["hint"]["left"], "right": r["hint"]["right"], "top": r["hint"]["top"], "bottom": r["hint"]["bottom"]}
    bar = {"left": r["bar"]["left"], "right": r["bar"]["right"], "top": r["bar"]["top"], "bottom": r["bar"]["bottom"]}
    bad = [m for m in r["markers"] if overlaps(m, hint) or overlaps(m, bar)]
    print(f"{label}: {r['count']} markers, {len(bad)} overlapping hint/bar")
    assert r["count"] > 0, f"{label}: no markers found - selector/navigation broke"
    assert not bad, f"{label}: {len(bad)} marker(s) overlap the hint or player-bar"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])

        # Remember (fixed, 9 markers is the largest static grid)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('.sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(150)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await check_markers(pg, "rememberHint", "rememberPlayerBar", ".remember-marker", "Remember")
        await ctx.close()

        # Search (Suchtest)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#searchOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#searchReadyStartBtn")
        for _ in range(60):
            if await pg.locator(".search-item").count() > 0:
                break
            await pg.wait_for_timeout(100)
        await check_markers(pg, "searchHint", "searchPlayerBar", ".search-item", "Search")
        await ctx.close()

        # Corsi (Blockspanne)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#corsiOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#corsiReadyStartBtn"); await pg.wait_for_timeout(300)
        await check_markers(pg, "corsiHint", "corsiPlayerBar", ".corsi-block", "Corsi")
        await ctx.close()

        # Reaktionsfeld (Dynavision-style)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#reaktOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click('#reaktModeRow [data-reakt-mode="proaktiv"]'); await pg.wait_for_timeout(60)
        await pg.click("#reaktReadyStartBtn"); await pg.wait_for_timeout(1100)
        await check_markers(pg, "reaktHint", "reaktPlayerBar", ".reakt-light", "Reaktionsfeld")
        await ctx.close()

        # MOT: objects keep moving for the whole tracking phase, so sample
        # positions repeatedly rather than checking just the initial layout.
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => { localStorage.removeItem('fwmc-mot-prefs-v1'); }")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="mot"]'); await pg.wait_for_timeout(150)
        await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(150)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(300)
        worst = 0.0
        for _ in range(25):
            r = await pg.evaluate("""
                () => {
                  const hint = document.getElementById('motHint').getBoundingClientRect();
                  const bar = document.getElementById('motPlayerBar').getBoundingClientRect();
                  const objs = [...document.querySelectorAll('.mot-object')].map((m) => m.getBoundingClientRect());
                  return { hint, bar, objs };
                }
            """)
            hint = {"left": r["hint"]["left"], "right": r["hint"]["right"], "top": r["hint"]["top"], "bottom": r["hint"]["bottom"]}
            bar = {"left": r["bar"]["left"], "right": r["bar"]["right"], "top": r["bar"]["top"], "bottom": r["bar"]["bottom"]}
            bad = [m for m in r["objs"] if overlaps(m, hint) or overlaps(m, bar)]
            if bad:
                worst = max(worst, len(bad))
            await pg.wait_for_timeout(200)
        print(f"MOT: sampled 25 frames during tracking, worst overlap count seen: {worst}")
        assert worst == 0, "an MOT object overlapped the hint/player-bar while tracking"
        await ctx.close()

        print("ERRORS: []")
        await b.close()

asyncio.run(main())
