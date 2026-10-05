import asyncio, json, os
from playwright.async_api import async_playwright

# Erfolge spürbar machen + Erster Start (Fabian, 2026-10-05).
# 1) Every done panel: the check mark draws itself on a completed run (not
#    on an aborted one); a new personal best counts up and pulses (3x), the
#    summary text always holds the final value; reduced motion = final state.
# 2) Onboarding: 3 slides on the very first start (Weiter, swipe, dots,
#    Überspringen), then the tips sheet; closing the tips the first time
#    points at "Mehr" (ring + toast). Only once, never for existing users,
#    never in automated browsers without fwmc-test-onboarding.
PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots"
os.makedirs(SHOTS, exist_ok=True)
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


def watch(pg, errors):
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)


async def new_ctx(b, init, **kw):
    opts = dict(viewport={"width": 390, "height": 844}, service_workers="block")
    opts.update(kw)
    ctx = await b.new_context(**opts)
    await ctx.add_init_script(init)
    return ctx


ONB_INIT = """if(!sessionStorage.getItem('seeded')){localStorage.clear();sessionStorage.setItem('seeded','1')}
localStorage.setItem('fwmc-test-onboarding','true');localStorage.setItem('fwmc-test-bottomnav','true');
localStorage.setItem('fwmc-test-tipshint','true');"""
RUN_INIT = """localStorage.setItem('fwmc-tips-seen','true');
localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"""


async def swipe(pg, sel, dx):
    await pg.evaluate("""([sel, dx]) => {
      const el = document.querySelector(sel), r = el.getBoundingClientRect();
      const x = r.left + r.width / 2, y = r.top + r.height / 2;
      const mk = (cx) => new Touch({ identifier: 1, target: el, clientX: cx, clientY: y });
      el.dispatchEvent(new TouchEvent('touchstart', { touches: [mk(x)], changedTouches: [mk(x)], bubbles: true, cancelable: true }));
      for (let i = 1; i <= 6; i++) el.dispatchEvent(new TouchEvent('touchmove', { touches: [mk(x + dx * i / 6)], changedTouches: [mk(x + dx * i / 6)], bubbles: true, cancelable: true }));
      el.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [mk(x + dx)], bubbles: true, cancelable: true }));
    }""", [sel, dx])


async def current_slide(pg):
    return await pg.evaluate("[...document.querySelectorAll('#onbDots .onb-dot')].findIndex(d => d.getAttribute('aria-current') === 'true')")


async def play_blitz(pg, start):
    await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(120)
    await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)
    await pg.click("#blitzAdvanced summary"); await pg.wait_for_timeout(100)
    await pg.fill("#blitzStartSlider", str(start)); await pg.dispatch_event("#blitzStartSlider", "input")
    await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(200)
    lit = await pg.evaluate("() => Array.from(document.querySelectorAll('#blitzGrid .blitz-cell')).map((el,i)=>el.classList.contains('lit')?i:-1).filter(i=>i>=0)")
    await pg.wait_for_timeout(1100)
    cells = await pg.locator("#blitzGrid .blitz-cell").all()
    for i in lit:
        await cells[i].click(); await pg.wait_for_timeout(60)
    await pg.wait_for_timeout(300)
    await pg.click("#blitzBackBtn")
    return len(lit)


async def make_free_blocks(pg):
    for kind, title in (("check", "Eisbad"), ("timer", "Mobilisation")):
        await pg.click("#freeNewBtn"); await pg.wait_for_timeout(120)
        await pg.click(f'#freeKindRow [data-free-kind="{kind}"]'); await pg.wait_for_timeout(60)
        await pg.fill("#freeTitleInput", title)
        await pg.click("#freeSaveBtn"); await pg.wait_for_timeout(150)
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ================= Onboarding: happy path =================
        ctx = await new_ctx(b, ONB_INIT, has_touch=True)
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        check("first start: onboarding visible, tips sheet waits", await pg.is_visible("#onboarding") and not await pg.is_visible("#tipsSheet"))
        t1 = await pg.inner_text("#onboarding .onb-slide:nth-child(1) h2")
        check("slide 1: welcome, trainer-neutral", "Willkommen bei deinem FWMC" in t1 and "Fabian" not in await pg.inner_text("#onboarding .onb-slide:nth-child(1)"), t1)
        check("Überspringen visible, button reads Weiter, dot 1 active",
              await pg.is_visible("#onbSkipBtn") and await pg.inner_text("#onbNextBtn") == "Weiter" and await current_slide(pg) == 0)
        small = await pg.evaluate("""() => [...document.querySelectorAll('#onbSkipBtn, #onbNextBtn, .onb-dot')]
          .map(e => e.getBoundingClientRect()).filter(r => r.width < 44 || r.height < 44).length""")
        check("tap targets >= 44 px", small == 0, small)
        hscroll = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        check("no sideways scroll", not hscroll)
        await pg.screenshot(path=f"{SHOTS}/onb_390_light_1.png")
        await pg.click("#onbNextBtn"); await pg.wait_for_timeout(450)
        check("Weiter -> slide 2", await current_slide(pg) == 1 and "plane deine Woche" in await pg.inner_text("#onboarding .onb-slide:nth-child(2) h2"))
        await pg.screenshot(path=f"{SHOTS}/onb_390_light_2.png")
        await swipe(pg, "#onbViewport", -200); await pg.wait_for_timeout(450)
        check("swipe left -> slide 3", await current_slide(pg) == 2)
        check("slide 3: Startbildschirm hint, button Los geht's",
              "Startbildschirm" in await pg.inner_text("#onbInstallTitle") and "Startbildschirm" in await pg.inner_text("#onbInstallText")
              and await pg.inner_text("#onbNextBtn") == "Los geht’s")
        await pg.screenshot(path=f"{SHOTS}/onb_390_light_3.png")
        await swipe(pg, "#onbViewport", -200); await pg.wait_for_timeout(400)
        check("swipe past the last slide stays", await current_slide(pg) == 2)
        await swipe(pg, "#onbViewport", 200); await pg.wait_for_timeout(450)
        check("swipe right -> back to slide 2", await current_slide(pg) == 1)
        await pg.click("#onbDots .onb-dot:nth-child(3)"); await pg.wait_for_timeout(450)
        check("dot 3 jumps to slide 3", await current_slide(pg) == 2)
        check("inactive slides are inert", await pg.evaluate("[...document.querySelectorAll('.onb-slide')].map(s => s.inert).join()") == "true,true,false")
        await pg.click("#onbNextBtn"); await pg.wait_for_timeout(500)
        check("Los geht's: slides gone, tips sheet follows",
              not await pg.is_visible("#onboarding") and await pg.is_visible("#tipsSheet"))
        check("onboarding stored", await pg.evaluate("localStorage.getItem('fwmc-onboarding-v1')") == "true")
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(300)
        toast = pg.locator(".where-toast")
        check("closing tips the first time: toast names Mehr", await toast.count() == 1 and "Mehr" in await toast.inner_text())
        check("Mehr tab gets the ring", await pg.evaluate("document.querySelector('#bottomNav [data-nav=more]').classList.contains('nav-hint')"))
        pos = await pg.evaluate("""() => { const t = document.querySelector('.where-toast').getBoundingClientRect(), m = document.querySelector('#bottomNav [data-nav=more]').getBoundingClientRect();
          return { above: t.bottom <= m.top, inside: t.left >= 0 && t.right <= innerWidth }; }""")
        check("toast sits above the bar, on screen", pos["above"] and pos["inside"], pos)
        await pg.screenshot(path=f"{SHOTS}/tipshint_390_light.png")
        await pg.wait_for_timeout(2800)
        check("hint is gone after ~2.5 s", await toast.count() == 0 and not await pg.evaluate("document.querySelector('#bottomNav [data-nav=more]').classList.contains('nav-hint')"))
        await pg.click("#bottomNav [data-nav=more]"); await pg.wait_for_timeout(200)
        await pg.click("#moreTipsBtn"); await pg.wait_for_timeout(200)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(200)
        check("closing tips again: no hint", await pg.locator(".where-toast").count() == 0)
        await pg.reload(); await pg.wait_for_timeout(500)
        check("after reload: neither onboarding nor tips", not await pg.is_visible("#onboarding") and not await pg.is_visible("#tipsSheet"))
        await ctx.close()

        # screenshots: dark 390, light/dark 1024
        for scheme, w, h in (("dark", 390, 844), ("light", 1024, 768), ("dark", 1024, 768)):
            ctx = await new_ctx(b, ONB_INIT, color_scheme=scheme, viewport={"width": w, "height": h})
            pg = await ctx.new_page(); watch(pg, errors)
            await pg.goto(BASE); await pg.wait_for_timeout(500)
            for i in (1, 2, 3):
                await pg.screenshot(path=f"{SHOTS}/onb_{w}_{scheme}_{i}.png")
                if i < 3: await pg.click("#onbNextBtn"); await pg.wait_for_timeout(450)
            fits = await pg.evaluate("""() => { const s = document.querySelectorAll('.onb-slide')[2]; return s.scrollHeight <= s.clientHeight + 1; }""")
            check(f"{w} {scheme}: slide content fits without scrolling", fits)
            await ctx.close()

        # ================= Onboarding: skip =================
        ctx = await new_ctx(b, ONB_INIT)
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await pg.click("#onbSkipBtn"); await pg.wait_for_timeout(500)
        check("Überspringen: slides gone, tips sheet follows, stored",
              not await pg.is_visible("#onboarding") and await pg.is_visible("#tipsSheet")
              and await pg.evaluate("localStorage.getItem('fwmc-onboarding-v1')") == "true")
        await pg.reload(); await pg.wait_for_timeout(400)
        check("skip persists across reload", not await pg.is_visible("#onboarding"))
        await ctx.close()

        # ================= Splash -> onboarding -> tips =================
        ctx = await new_ctx(b, ONB_INIT + "localStorage.setItem('fwmc-test-splash','true');")
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(250)
        order = await pg.evaluate("""() => { const s = document.getElementById('appSplash');
          return { splash: !!s && !s.classList.contains('is-gone'), onb: !document.getElementById('onboarding').hidden,
                   tips: !document.getElementById('tipsSheet').hidden,
                   z: s ? +getComputedStyle(s).zIndex > +getComputedStyle(document.getElementById('onboarding')).zIndex : null }; }""")
        check("splash covers the slides first, tips not yet open", order["splash"] and order["onb"] and not order["tips"] and order["z"], order)
        await pg.wait_for_timeout(1800)
        check("splash gone, slides visible", await pg.locator("#appSplash").count() == 0 and await pg.is_visible("#onboarding"))
        await ctx.close()

        # ================= Existing users / automated default =================
        for label, seed in (("tips seen", "localStorage.setItem('fwmc-tips-seen','true');"),
                            ("history only", "localStorage.setItem('fwmc-history-v1', JSON.stringify([{id:'1',ts:new Date().toISOString(),kind:'exercise',title:'X',seconds:60}]));")):
            ctx = await new_ctx(b, ONB_INIT + seed)
            pg = await ctx.new_page(); watch(pg, errors)
            await pg.goto(BASE); await pg.wait_for_timeout(400)
            check(f"existing user ({label}): no onboarding", not await pg.is_visible("#onboarding"))
            await ctx.close()
        ctx = await new_ctx(b, "")
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        check("automated browser without flag: no onboarding, tips as before", not await pg.is_visible("#onboarding") and await pg.is_visible("#tipsSheet"))
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(250)
        check("automated browser without flag: no tips hint", await pg.locator(".where-toast").count() == 0)
        await ctx.close()

        # ================= Done panel: check mark draws itself =================
        ctx = await new_ctx(b, RUN_INIT)
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await make_free_blocks(pg)
        await pg.click('#freeOwnGrid [data-free-id]:has-text("Eisbad")'); await pg.wait_for_timeout(120)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(200)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(120)
        st = await pg.evaluate("""() => { const c = document.querySelector('#freeDonePanel .done-check'), path = c.querySelector('svg path');
          const cs = path ? getComputedStyle(path) : null;
          return { svg: !!path, drawing: c.classList.contains('is-drawing'), anim: cs && cs.animationName, dur: cs && cs.animationDuration,
                   bg: getComputedStyle(c).backgroundColor, text: c.textContent.trim() }; }""")
        check("completed run: SVG check mark draws itself (~0.5 s, brand colour)",
              st["svg"] and st["drawing"] and st["anim"] == "doneCheckDraw" and st["dur"] == "0.5s" and st["bg"] == "rgb(0, 112, 148)", st)
        await pg.screenshot(path=f"{SHOTS}/done_drawing_390_light.png")
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=f"{SHOTS}/done_390_light.png")
        all_svg = await pg.evaluate("[...document.querySelectorAll('.done-check')].every(c => c.querySelector('svg'))")
        check("every done panel's check mark is the shared SVG", all_svg)
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#freeBackToHome"); await pg.wait_for_timeout(120)
        await pg.click('#freeOwnGrid [data-free-id]:has-text("Mobilisation")'); await pg.wait_for_timeout(120)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#stepNav [data-slot='next'] button") if await pg.locator("#stepNav [data-slot='next'] button").count() else await pg.click("#freeSkipBtn")
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("""() => { const c = document.querySelector('#freeDonePanel .done-check');
          return { panel: !document.getElementById('freeDonePanel').hidden, hidden: c.hidden, drawing: c.classList.contains('is-drawing') }; }""")
        check("aborted run: no check mark, no animation", st["panel"] and st["hidden"] and not st["drawing"], st)
        await ctx.close()

        # ================= Neue Bestleistung: count up + pulse =================
        ctx = await new_ctx(b, RUN_INIT)
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        n = await play_blitz(pg, 4)
        await pg.wait_for_timeout(250)
        s = await pg.evaluate("""() => { const sum = document.getElementById('blitzDoneSummary'), num = sum.querySelector('.best-num');
          return { text: sum.textContent, num: num && num.dataset.best, counting: !!num && num.classList.contains('counting'),
                   count: num ? +num.dataset.count : null, tag: !!sum.querySelector('.best-tag') }; }""")
        check("record: summary text final at once", f"Stufe {n} erreicht · Neue Bestleistung!" in s["text"], s)
        check("record: number counts up", s["num"] == str(n) and s["counting"] and s["count"] is not None and s["count"] < n and s["tag"], s)
        await pg.screenshot(path=f"{SHOTS}/best_counting_390.png")
        await pg.wait_for_timeout(700)
        s = await pg.evaluate("""() => { const num = document.querySelector('#blitzDoneSummary .best-num'), cs = getComputedStyle(num);
          return { pulse: num.classList.contains('best-pulse'), counting: num.classList.contains('counting'), anim: cs.animationName,
                   iter: cs.animationIterationCount, dur: parseFloat(cs.animationDuration) }; }""")
        check("then pulses 3 times (~2 s in total)", s["pulse"] and not s["counting"] and s["anim"] == "bestPulse" and s["iter"] == "3"
              and 1.4 <= 0.75 + 3 * s["dur"] <= 2.2, s)
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"{SHOTS}/best_done_390.png")
        await pg.click("#blitzDoneBackBtn") if await pg.is_visible("#blitzDoneBackBtn") else None
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await play_blitz(pg, 3)
        await pg.wait_for_timeout(250)
        s = await pg.evaluate("""() => { const sum = document.getElementById('blitzDoneSummary');
          return { text: sum.textContent, num: !!sum.querySelector('.best-num, .best-tag') }; }""")
        check("no record: no count/pulse", "Bestleistung" not in s["text"] and not s["num"], s)
        await ctx.close()

        # ================= Reduced motion =================
        ctx = await new_ctx(b, RUN_INIT, reduced_motion="reduce")
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        n = await play_blitz(pg, 4)
        await pg.wait_for_timeout(150)
        s = await pg.evaluate("""() => { const sum = document.getElementById('blitzDoneSummary'), num = sum.querySelector('.best-num'),
          c = document.querySelector('#blitzDonePanel .done-check');
          return { num: num && num.textContent, cls: num && num.className, drawing: c.classList.contains('is-drawing'), checkVis: !c.hidden,
                   anim: getComputedStyle(c.querySelector('path')).animationName }; }""")
        check("reduced motion: final number at once, no counting/pulse", s["num"] == str(n) and s["cls"] == "best-num", s)
        check("reduced motion: check mark shown without drawing", s["checkVis"] and not s["drawing"] and s["anim"] == "none", s)
        await ctx.close()
        ctx = await new_ctx(b, ONB_INIT, reduced_motion="reduce")
        pg = await ctx.new_page(); watch(pg, errors)
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        await pg.click("#onbSkipBtn"); await pg.wait_for_timeout(50)
        check("reduced motion: slides close at once, tips follow", not await pg.is_visible("#onboarding") and await pg.is_visible("#tipsSheet"))
        await ctx.close()

        # done panel screenshots (dark / 1024)
        for scheme, w, h in (("dark", 390, 844), ("light", 1024, 768)):
            ctx = await new_ctx(b, RUN_INIT, color_scheme=scheme, viewport={"width": w, "height": h})
            pg = await ctx.new_page(); watch(pg, errors)
            await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
            await play_blitz(pg, 4)
            await pg.wait_for_timeout(2300)
            await pg.screenshot(path=f"{SHOTS}/best_done_{w}_{scheme}.png")
            await ctx.close()

        await b.close()
    print("ERRORS:", errors)
    failed = [n for n, ok in results if not ok]
    print("FAILED:", failed)
    print("ALL OK" if not failed and not errors else "SOME CHECKS FAILED")


asyncio.run(main())
