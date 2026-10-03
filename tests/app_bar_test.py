"""Logo-Leiste: fixed at the top while scrolling, hidden while an exercise
runs, shown at the same place in the pause and end phases without covering
any control."""
import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
fails = []
def check(name, ok):
    print(f"{name}: {ok}")
    if not ok: fails.append(name)

COVER_JS = """(sel) => {
  const bar = document.getElementById('appBar').getBoundingClientRect();
  const bad = [];
  document.querySelectorAll(sel).forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (r.top < bar.bottom - 0.5) bad.push(el.id || el.textContent.trim().slice(0, 20));
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (hit && !el.contains(hit) && !hit.contains(el)) bad.push('hidden:' + (el.id || el.textContent.trim().slice(0, 20)));
  });
  return bad;
}"""
BAR_ON = "() => getComputedStyle(document.getElementById('appBar')).display !== 'none'"

async def run(scheme, shot):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-unlocked','true')")
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # Normal screen: the brandbar stays at the top while scrolling.
        await pg.evaluate("window.scrollTo(0, 700)"); await pg.wait_for_timeout(150)
        top = await pg.evaluate("document.querySelector('#home > .brandbar').getBoundingClientRect().top")
        check(f"[{scheme}] home bar stays at top after scroll", abs(top) < 1)
        hit = await pg.evaluate("""() => { const r = document.querySelector('#home > .brandbar .brand-logo').getBoundingClientRect();
          return !!document.elementFromPoint(r.left + 5, r.top + r.height / 2).closest('#home > .brandbar'); }""")
        check(f"[{scheme}] home bar is on top of the content", hit)
        gear = await pg.evaluate("document.querySelector('#home > .brandbar .master-settings-btn').getBoundingClientRect().top")
        check(f"[{scheme}] gear reachable after scroll", gear >= 0)
        if shot: await pg.screenshot(path=f"app_bar_home_{scheme}.png")
        await pg.evaluate("window.scrollTo(0, 0)")
        check(f"[{scheme}] global bar hidden on normal screens", not await pg.evaluate(BAR_ON))

        # Same position on another screen.
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(200)
        y1 = await pg.evaluate("document.querySelector('#testHome > .brandbar .brand-logo').getBoundingClientRect().top")
        await pg.click('#testHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(200)
        y0 = await pg.evaluate("document.querySelector('#home > .brandbar .brand-logo').getBoundingClientRect().top")
        check(f"[{scheme}] logo at the same place on every screen", abs(y1 - y0) < 1)

        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(200)
        await pg.click("#kippbildOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#kippbildReadyStartBtn"); await pg.wait_for_timeout(500)
        check(f"[{scheme}] bar hidden while the exercise runs", not await pg.evaluate(BAR_ON))

        await pg.click("#kippbildPauseBtn"); await pg.wait_for_timeout(300)
        check(f"[{scheme}] bar shown in the pause", await pg.evaluate(BAR_ON))
        logo = await pg.evaluate("document.querySelector('#appBar .brand-logo').getBoundingClientRect().top")
        check(f"[{scheme}] pause bar logo at the same place", abs(logo - y0) < 1)
        bad = await pg.evaluate(COVER_JS, "#kippbildPlayerBar button, #kippbildPauseOverlay button, #kippbildPauseOverlay input")
        check(f"[{scheme}] nothing covered in the pause {bad}", bad == [])
        if shot: await pg.screenshot(path=f"app_bar_pause_{scheme}.png")
        await pg.click("#kippbildResumeBtn"); await pg.wait_for_timeout(300)
        check(f"[{scheme}] bar hidden again after resume", not await pg.evaluate(BAR_ON))

        await pg.wait_for_timeout(8500)
        await pg.click("#kippbildBackBtn"); await pg.wait_for_timeout(400)
        check(f"[{scheme}] done panel shown", await pg.is_visible("#kippbildDonePanel"))
        check(f"[{scheme}] bar shown at the end", await pg.evaluate(BAR_ON))
        bad = await pg.evaluate(COVER_JS, "#kippbildDonePanel button, #kippbildDonePanel h2")
        check(f"[{scheme}] nothing covered at the end {bad}", bad == [])
        if shot: await pg.screenshot(path=f"app_bar_done_{scheme}.png")
        await pg.click("#kippbildDoneBackBtn"); await pg.wait_for_timeout(300)
        check(f"[{scheme}] global bar gone after leaving", not await pg.evaluate(BAR_ON))
        # Body-level panels (Kombi pause between Bausteine etc. - Fabian 03.10.)
        for pid in ["comboTransition", "comboDonePanel", "workoutTransition", "breathTransition", "cardioDonePanel"]:
            await pg.evaluate(f"document.getElementById('{pid}').hidden=false")
            await pg.wait_for_timeout(100)
            check(f"[{scheme}] bar shown on #{pid}", await pg.evaluate(BAR_ON))
            bad = await pg.evaluate(COVER_JS, f"#{pid} button, #{pid} h2")
            check(f"[{scheme}] nothing covered on #{pid} {bad}", bad == [])
            await pg.evaluate(f"document.getElementById('{pid}').hidden=true")
        check(f"[{scheme}] no page errors {errs}", errs == [])
        await b.close()

async def main():
    import sys
    shot = "--shots" in sys.argv
    await run("light", shot)
    await run("dark", shot)
    print("ALL OK" if not fails else f"FAILED: {fails}")
asyncio.run(main())
