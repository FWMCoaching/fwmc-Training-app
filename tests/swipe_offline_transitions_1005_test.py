import asyncio
from playwright.async_api import async_playwright

# Paket 2026-10-05 (Fabian: "Alle 4 Punkte"): Zurück per Wischen vom linken
# Rand, offline nutzbar (Service Worker), Dashboard folgt Hell/Dunkel,
# Seitenübergänge (tiefer = von rechts, zurück = von links, Bereiche =
# einblenden, Ergebnis = von unten, "Bewegung reduzieren" = nur einblenden).
BASE = "http://localhost:8845/"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

TR = "(id) => [...document.getElementById(id).classList].filter(c => c.startsWith('tr-')).join(',')"
SWIPE = """([x0, x1]) => {
  const el = document.elementFromPoint(x0, 400) || document.body;
  const mk = (x) => new Touch({ identifier: 1, target: el, clientX: x, clientY: 400 });
  el.dispatchEvent(new TouchEvent('touchstart', { touches: [mk(x0)], changedTouches: [mk(x0)], bubbles: true }));
  for (let i = 1; i <= 8; i++) { const x = x0 + (x1 - x0) * i / 8; el.dispatchEvent(new TouchEvent('touchmove', { touches: [mk(x)], changedTouches: [mk(x)], bubbles: true })); }
  el.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [mk(x1)], bubbles: true }));
}"""

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        def watch(pg):
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

        # ---- Übergänge ----
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", has_touch=True)
        await ctx.add_init_script(INIT + "localStorage.setItem('fwmc-test-transitions','true')")
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        check("no animation on the first page at start", await pg.evaluate(TR, "todayHome") == "")
        await pg.click('#todayHome .section-tab[data-section="movement"]')
        check("switching areas fades", await pg.evaluate(TR, "movementHome") == "tr-fade")
        await pg.wait_for_timeout(400)
        check("animation class removed afterwards", await pg.evaluate(TR, "movementHome") == "")
        await pg.click("#movementStartCard")
        check("going deeper slides in from the right", await pg.evaluate(TR, "movementReady") == "tr-push")
        check("old page stays visible underneath (iOS push)", await pg.evaluate("document.querySelectorAll('.tr-ghost.push').length") == 1)
        check("snapshot is never found as a screen", await pg.evaluate("document.querySelectorAll('.screen:not([hidden])').length") == 1)
        await pg.wait_for_timeout(400)
        await pg.click("#movementReady .bar-back-btn")
        check("going back slides in from the left", await pg.evaluate(TR, "movementHome") == "tr-pop")
        await pg.wait_for_timeout(400)

        # ---- Wischen ----
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(400)
        await pg.evaluate(SWIPE, [150, 360]); await pg.wait_for_timeout(400)
        check("swipe starting mid-screen does nothing", await pg.is_visible("#movementReady"))
        await pg.evaluate(SWIPE, [8, 40]); await pg.wait_for_timeout(500)
        check("short swipe from the edge snaps back", await pg.is_visible("#movementReady"))
        await pg.evaluate(SWIPE, [8, 250]); await pg.wait_for_timeout(600)
        check("swipe from the left edge goes back", await pg.is_visible("#movementHome") and not await pg.is_visible("#movementReady"))
        check("page transform cleaned up", await pg.evaluate("document.getElementById('movementReady').style.transform") == "")
        await pg.evaluate(SWIPE, [8, 250]); await pg.wait_for_timeout(500)
        check("swipe on an area home does nothing", await pg.is_visible("#movementHome"))
        await ctx.close()

        # reduced motion: only fade
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", reduced_motion="reduce")
        await ctx.add_init_script(INIT + "localStorage.setItem('fwmc-test-transitions','true')")
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html?bereich=movement"); await pg.wait_for_timeout(300)
        await pg.click("#movementStartCard")
        anim = await pg.evaluate("getComputedStyle(document.querySelector('#movementReady > :not(.brandbar)')).animationName")
        bar_anim = await pg.evaluate("getComputedStyle(document.querySelector('#movementReady > .brandbar')).animationName")
        check("logo bar itself never moves", bar_anim == "none", bar_anim)
        check("reduced motion: only a fade", anim == "trFade", anim)
        await ctx.close()

        # without the opt-in (every other test): no animation at all
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html?bereich=movement"); await pg.wait_for_timeout(300)
        await pg.click("#movementStartCard")
        check("automated runs without opt-in: no animation", await pg.evaluate(TR, "movementReady") == "")
        await ctx.close()

        # ---- Offline ----
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "index.html"); await pg.wait_for_timeout(300)
        await pg.evaluate("navigator.serviceWorker.ready.then(() => true)")
        await pg.reload(); await pg.wait_for_timeout(500)
        check("service worker controls the page", await pg.evaluate("!!navigator.serviceWorker.controller"))
        await pg.goto(BASE + "index.html?bereich=nat"); await pg.wait_for_timeout(500)
        await ctx.set_offline(True)
        await pg.goto(BASE + "index.html?bereich=today"); await pg.wait_for_timeout(500)
        check("offline: app opens", await pg.is_visible("#todayHome"))
        check("offline: styles and logo there", await pg.evaluate("getComputedStyle(document.querySelector('#todayHome .brandbar')).display !== 'block' && document.querySelector('#todayHome .brand-logo').naturalWidth > 0"))
        await pg.click('#todayHome .section-tab[data-section="movement"]'); await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(500)
        check("offline: an exercise runs", await pg.is_visible("#movementPlayer"))
        faq = await pg.evaluate("[...document.querySelectorAll('#faqSheet .faq-item summary')].map(s => s.textContent)")
        check("FAQ explains offline use", any("ohne Internet" in t for t in faq))
        await ctx.set_offline(False)
        await ctx.close()

        # ---- Dashboard Hell/Dunkel ----
        lum = "(() => { const m = getComputedStyle(document.body).backgroundColor.match(/\\d+/g).map(Number); return (0.299*m[0] + 0.587*m[1] + 0.114*m[2]) / 255; })()"
        for scheme, test in [("dark", lambda l: l < 0.3), ("light", lambda l: l > 0.8)]:
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
            pg = await ctx.new_page(); watch(pg)
            await pg.goto(BASE + "dashboard.html"); await pg.wait_for_timeout(300)
            l = await pg.evaluate(lum)
            check(f"dashboard follows {scheme} mode", test(l), round(l, 2))
            await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
