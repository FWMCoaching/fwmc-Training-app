import asyncio, json
from playwright.async_api import async_playwright

# Design-Runde 06.10.2026 (Fabian: "Code Kasten dezenter, ja / Atemübung im
# Dunkel Modus, ja / Fortschritt anpassen, ja", "Alles deutsch", "Kombi sehe
# ich nur bei den beiden"): ruhiger Code-Kasten, dunkler Atem-Player,
# freundlicher leerer Fortschritt, deutsche Bereichsnamen ohne "Name noch
# offen", Kombi-Link nur auf Heute und Training.
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
        "localStorage.setItem('fwmc-test-bottomnav','true');localStorage.setItem('fwmc-test-codequiet','true');")
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

def lum(rgb):
    n = [int(x) for x in rgb[rgb.index("(") + 1:rgb.index(")")].split(",")[:3]]
    return sum(n) / 3

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for scheme in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
            await ctx.add_init_script(INIT)
            await ctx.route("**/*.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            t = f"[{scheme}] "

            # Fortschritt leer
            await pg.goto(BASE + "?bereich=fortschritt"); await pg.wait_for_timeout(300)
            check(t + "empty progress shows the welcome card", await pg.is_visible("#progressEmpty"))
            check(t + "empty progress hides the zero stats", not await pg.is_visible("#progressStats"))
            await pg.click("#progressEmptyBtn"); await pg.wait_for_timeout(250)
            check(t + "empty-state button leads to Training", await pg.is_visible("#trainingHub"))

            # Ruhiger Code-Kasten
            check(t + "code card starts collapsed", await pg.is_visible("#trainingHub .code-toggle") and not await pg.is_visible("#moreCodeInput"))
            h = await pg.evaluate("document.querySelector('#trainingHub .code-card').getBoundingClientRect().height")
            check(t + "collapsed card is small", h < 90, h)
            bg = await pg.evaluate("getComputedStyle(document.querySelector('#trainingHub .code-card')).backgroundImage")
            check(t + "no gradient on the quiet card", bg == "none", bg)
            await pg.click("#trainingHub .code-toggle"); await pg.wait_for_timeout(150)
            check(t + "toggle opens the input", await pg.is_visible("#moreCodeInput"))
            check(t + "aria-expanded follows", await pg.get_attribute("#trainingHub .code-toggle", "aria-expanded") == "true")
            await pg.fill("#moreCodeInput", "gibtsnicht123"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(500)
            check(t + "wrong code still shows the error", await pg.is_visible("#moreCodeError"))
            await pg.click("#trainingHub .code-toggle"); await pg.wait_for_timeout(150)
            check(t + "toggle closes again", not await pg.is_visible("#moreCodeInput"))

            # Deutsche Namen, kein Vermerk
            hub = await pg.inner_text("#hubAreaGrid")
            for old in ("Visual Training", "Workout", "Cardio", "Movement"):
                check(t + f"hub has no '{old}'", old not in hub)
            for new in ("Visuelles", "Krafttraining", "Ausdauertraining", "Reaktionstraining"):
                check(t + f"hub shows '{new}'", new in hub.replace("­", ""))
            tags = await pg.evaluate("[...document.querySelectorAll('.placeholder-tag')].filter(e => e.textContent.includes('Name')).length")
            check(t + "no 'Name noch offen' tag left", tags == 0, tags)
            for area, kicker in (("workout", "krafttraining"), ("cardio", "ausdauertraining"), ("movement", "reaktionstraining"), ("visual", "visuelles training"), ("nat", "nat – neuroathletik")):
                await pg.goto(BASE + "?bereich=" + area); await pg.wait_for_timeout(250)
                txt = await pg.evaluate("(() => { const s = [...document.querySelectorAll('.screen')].find(x => !x.hidden); const k = s && s.querySelector('.hero-kicker'); return k ? k.textContent.trim().toLowerCase() : ''; })()")
                check(t + f"{area} heading reads '{kicker}'", txt.startswith(kicker), txt)
                vis = await pg.evaluate("(() => { const s = [...document.querySelectorAll('.screen')].find(x => !x.hidden); const l = s && s.querySelector(':scope > .combo-entry-link'); return !!(l && l.offsetParent); })()")
                check(t + f"{area} home has no Kombi link", not vis)
            await pg.goto(BASE); await pg.wait_for_timeout(250)
            check(t + "Kombi link stays on Heute", await pg.is_visible("#todayHome .combo-entry-link") or await pg.locator("#todayHome .combo-entry-link").count() == 0)

            # Atem-Player
            await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(300)
            await pg.click("#patternGrid .featured-card >> nth=1"); await pg.wait_for_timeout(200)
            await pg.click("#breathStartBtn"); await pg.wait_for_timeout(1200)
            pbg = await pg.evaluate("getComputedStyle(document.getElementById('breathPlayer')).backgroundColor")
            if scheme == "dark":
                check(t + "breath player is dark", lum(pbg) < 40, pbg)
            else:
                check(t + "breath player stays light", lum(pbg) > 180, pbg)
            await pg.click("#breathBackBtn"); await pg.wait_for_timeout(300)
            await ctx.close()
        await b.close()
    check("No page errors", not errors, errors[:5])
    print("ALL OK" if ok_all else "SOME CHECKS FAILED")

asyncio.run(main())
