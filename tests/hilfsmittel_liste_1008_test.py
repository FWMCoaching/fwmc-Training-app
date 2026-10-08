import asyncio, os
from playwright.async_api import async_playwright

# Hilfsmittel und Starterpaket (Fabian 08.10., "Starterpaket Stufe 1"):
# Mehr row "Hilfsmittel" opens #gearScreen; one card per GEAR_ITEMS entry
# (starter items first), exercise chips derived from HILFSMITTEL[..].gear that
# open the exercise's ready screen (back returns to the page), no shop button
# without a link, with a link "Ansehen" + "Werbung · Partner-Link" + the
# Provision sentence; Rot-Grün-Brille only with the Test-Bereich unlocked;
# "Alle Hilfsmittel" in the ready-screen notes; Datenschutz sentence; no
# sideways scroll at 390/1024 light/dark; no page/console errors.
# Screenshots: tests/screenshots/hilfsmittel_liste/.

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "hilfsmittel_liste")
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
        "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}));")

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

async def visible_screen(pg):
    return await pg.evaluate("() => { const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden); return s ? s.id : null; }")

CARDS_JS = """() => [...document.querySelectorAll('#gearScreen .gear-card')].map(c => ({
  id: c.dataset.gear, starter: !!c.closest('#gearStarterList'),
  chips: [...c.querySelectorAll('.gear-ex-chip')].map(b => ({ key: b.dataset.gearEx, text: b.textContent.trim(), h: b.getBoundingClientRect().height })),
  shop: c.querySelectorAll('.gear-shop-btn').length, ad: c.querySelectorAll('.gear-ad').length }))"""

EXPECTED = {
    "cups": {"cone-compass", "cone-tap", "cone-path", "cone-number", "farbfelder", "richtungskreuz"},
    "mat": {"farbfelder", "richtungskreuz"},  # Richtungskreuz (08.10.): optional
    "numbers": {"cone-number"},
    "tape": {"cone-compass"},
}

async def open_gear(pg):
    await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(150)
    await pg.click("#moreGearBtn"); await pg.wait_for_timeout(200)

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(300)
        await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(150)
        row = pg.locator("#moreGearBtn")
        check("Mehr list has the 'Hilfsmittel' row", await row.is_visible() and "Hilfsmittel" in await row.inner_text())
        same = await pg.evaluate("""() => { const a = document.getElementById('moreGearBtn'), s = document.getElementById('moreTipsBtn');
          const ca = getComputedStyle(a), cs = getComputedStyle(s), aa = getComputedStyle(a, '::after');
          return a.className === s.className && ca.borderLeftWidth === cs.borderLeftWidth && ca.paddingRight === cs.paddingRight && aa.content !== 'none' && aa.width === getComputedStyle(s, '::after').width; }""")
        check("row looks like its siblings (same class, SVG chevron)", same)
        await row.click(); await pg.wait_for_timeout(200)
        check("row opens #gearScreen", await visible_screen(pg) == "gearScreen")
        title = await pg.inner_text("#gearScreen .page-title")
        check("page title 'Hilfsmittel und Starterpaket'", title.strip() == "Hilfsmittel und Starterpaket", title)
        check("logo bar with round back button", await pg.evaluate("() => !!document.querySelector('#gearScreen > .brandbar #gearBackBtn.bar-back-btn')"))
        check("bottom tab 'Mehr' stays active", await pg.evaluate("() => document.querySelector('#bottomNav [data-nav=more]').classList.contains('active')"))
        check("intro names the Starterpaket", "Starterpaket für den Anfang" in await pg.inner_text("#gearScreen"))

        cards = await pg.evaluate(CARDS_JS)
        ids = [c["id"] for c in cards]
        check("cards in order, starter first, no Rot-Grün-Brille while locked", ids == ["cups", "mat", "numbers", "tape"], ids)
        check("cups + mat are the starter items", [c["id"] for c in cards if c["starter"]] == ["cups", "mat"])
        for c in cards:
            got = {x["key"] for x in c["chips"]}
            check(f"card {c['id']}: chips derived from HILFSMITTEL", got == EXPECTED[c["id"]], got)
            check(f"card {c['id']}: chips >= 44 px", all(x["h"] >= 44 for x in c["chips"]))
            check(f"card {c['id']}: no shop button / marker without link", c["shop"] == 0 and c["ad"] == 0)
        check("partner sentence hidden without links", await pg.evaluate("() => document.getElementById('gearPartnerNote').hidden"))
        check("no empty button on the page", await pg.evaluate("() => [...document.querySelectorAll('#gearScreen button, #gearScreen a')].every(b => b.textContent.trim() || b.getAttribute('aria-label'))"))

        # every chip opens the right ready screen, back returns to the page
        for c in cards:
            for x in c["chips"]:
                await pg.click(f'#gearScreen .gear-card[data-gear="{c["id"]}"] [data-gear-ex="{x["key"]}"]'); await pg.wait_for_timeout(200)
                scr = await visible_screen(pg)
                rt = (await pg.inner_text("#readyTitle")).strip() if scr == "ready" else ""
                check(f"chip {c['id']}/{x['key']} opens its ready screen", scr == "ready" and rt == x["text"].replace(" (optional)", ""), f"{scr} {rt!r}")
                await pg.click("#backToHome"); await pg.wait_for_timeout(200)
                check(f"chip {c['id']}/{x['key']}: back returns to the page", await visible_screen(pg) == "gearScreen")

        # "Alle Hilfsmittel" in the ready-screen note
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
        await pg.click('.excard[data-exercise="cone-number"]'); await pg.wait_for_timeout(200)
        link = pg.locator("#hilfsmittelNote .hilfsmittel-all")
        check("ready note has 'Alle Hilfsmittel'", await link.is_visible() and (await link.inner_text()).strip() == "Alle Hilfsmittel")
        bb = await link.bounding_box()
        check("'Alle Hilfsmittel' >= 44 px high", bb and bb["height"] >= 44, bb)
        await link.click(); await pg.wait_for_timeout(200)
        check("'Alle Hilfsmittel' opens #gearScreen", await visible_screen(pg) == "gearScreen")
        await pg.click("#gearBackBtn"); await pg.wait_for_timeout(200)
        check("back returns to the ready screen", await visible_screen(pg) == "ready" and (await pg.inner_text("#readyTitle")).strip() == "Hütchen · Farbe + Zahl")
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        check("ready back still goes to the VT home", await visible_screen(pg) == "home")

        # with a shop link (test hook)
        await open_gear(pg)
        await pg.evaluate("() => { window.__gear.items.find(g => g.id === 'mat').link = 'https://example.com/matte'; window.__gear.render(); }")
        cards = await pg.evaluate(CARDS_JS)
        by = {c["id"]: c for c in cards}
        check("link set: only that card gets the button + marker", by["mat"]["shop"] == 1 and by["mat"]["ad"] == 1 and all(by[k]["shop"] == 0 and by[k]["ad"] == 0 for k in by if k != "mat"))
        shop = await pg.evaluate("""() => { const a = document.querySelector('[data-gear=mat] .gear-shop-btn'), m = document.querySelector('[data-gear=mat] .gear-ad');
          return { t: a.textContent.trim(), href: a.href, target: a.target, rel: a.rel, h: a.getBoundingClientRect().height, m: m.textContent.trim() }; }""")
        check("'Ansehen' opens the shop in a new tab", shop["t"] == "Ansehen" and shop["href"] == "https://example.com/matte" and shop["target"] == "_blank" and "noopener" in shop["rel"] and "sponsored" in shop["rel"], shop)
        check("'Ansehen' >= 44 px", shop["h"] >= 44, shop["h"])
        check("marker reads 'Werbung · Partner-Link'", shop["m"] == "Werbung · Partner-Link", shop["m"])
        note = await pg.evaluate("() => { const n = document.getElementById('gearPartnerNote'); return n.hidden ? '' : n.textContent.trim(); }")
        check("partner sentence shown with a link", note.startswith("Wenn du über einen Link kaufst, bekommt dein Trainer eine kleine Provision.") and "Preis nicht" in note, note)
        await pg.screenshot(path=os.path.join(SHOTS, "gear_mit_link_390_light.png"), full_page=True)
        await pg.evaluate("() => { window.__gear.items.find(g => g.id === 'mat').link = ''; window.__gear.render(); }")
        check("link removed: button + sentence gone again", await pg.evaluate("() => !document.querySelector('#gearScreen .gear-shop-btn') && document.getElementById('gearPartnerNote').hidden"))

        # Datenschutz sentence
        priv = await pg.evaluate("() => document.getElementById('privacySheet').textContent")
        check("Datenschutz names external shops", "Kauf-Links führen zu externen Shops; dort gelten deren Datenschutzregeln." in priv)

        # Test-Bereich unlocked: Rot-Grün-Brille card + Jedes Auge zählt
        await pg.evaluate("() => localStorage.setItem('fwmc-test-unlocked', 'true')")
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(300)
        await open_gear(pg)
        cards = await pg.evaluate(CARDS_JS)
        g = [c for c in cards if c["id"] == "glasses"]
        check("unlocked: Rot-Grün-Brille card shown, not in the starter list", len(g) == 1 and not g[0]["starter"])
        check("unlocked: chip 'Jedes Auge zählt'", g and [x["text"] for x in g[0]["chips"]] == ["Jedes Auge zählt"])
        await pg.click('[data-gear=glasses] [data-gear-ex="farbbrille"]'); await pg.wait_for_timeout(200)
        check("chip opens #eyecountReady", await visible_screen(pg) == "eyecountReady")
        await pg.click("#eyecountReadyBackToHome"); await pg.wait_for_timeout(200)
        check("eyecount back returns to the page", await visible_screen(pg) == "gearScreen")
        await pg.goto(BASE + "?bereich=test"); await pg.wait_for_timeout(300)
        await pg.click("#eyecountOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#eyecountReadyBackToHome"); await pg.wait_for_timeout(200)
        check("eyecount from the Test home still returns there", await visible_screen(pg) == "testHome")
        await pg.click("#eyecountOpenBtn"); await pg.wait_for_timeout(200)
        al = pg.locator("#eyecountHilfsmittel .hilfsmittel-all")
        if await al.is_visible():
            await al.click(); await pg.wait_for_timeout(200)
            check("eyecount note 'Alle Hilfsmittel' opens the page", await visible_screen(pg) == "gearScreen")
            await pg.click("#gearBackBtn"); await pg.wait_for_timeout(200)
            check("back returns to Jedes Auge zählt", await visible_screen(pg) == "eyecountReady")
        else:
            check("eyecount note visible", False)
        await ctx.close()

        # layout + screenshots: 390 and 1024, light and dark, next to sibling Mehr pages
        for scheme in ["light", "dark"]:
            for w in [390, 1024]:
                c2 = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme, service_workers="block")
                await c2.add_init_script(INIT)
                p2 = await c2.new_page()
                p2.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
                p2.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
                await p2.goto(BASE + "?bereich=heute"); await p2.wait_for_timeout(300)
                await p2.click('#bottomNav [data-nav="more"]'); await p2.wait_for_timeout(200)
                await p2.screenshot(path=os.path.join(SHOTS, f"mehr_{w}_{scheme}.png"), full_page=True)
                await p2.click("#moreGearBtn"); await p2.wait_for_timeout(250)
                sw = await p2.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                check(f"{w}px {scheme}: no sideways scroll", sw <= 1, sw)
                await p2.screenshot(path=os.path.join(SHOTS, f"gear_{w}_{scheme}.png"), full_page=True)
                await p2.evaluate("() => { window.__gear.items.forEach(g => { g.link = 'https://example.com/' + g.id; }); window.__gear.render(); }")
                sw = await p2.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                check(f"{w}px {scheme} with links: no sideways scroll", sw <= 1, sw)
                await p2.screenshot(path=os.path.join(SHOTS, f"gear_links_{w}_{scheme}.png"), full_page=True)
                # sibling sub page under the bottom bar (logo bar with ‹): Mein Fortschritt
                await p2.click('#bottomNav [data-nav="progress"]'); await p2.wait_for_timeout(200)
                await p2.screenshot(path=os.path.join(SHOTS, f"sibling_fortschritt_{w}_{scheme}.png"), full_page=False)
                await c2.close()
        await b.close()
    check("no page/console errors", not errors, errors[:3])
    print("FAILS:", fails)
    print("ERRORS:", errors)

asyncio.run(main())
