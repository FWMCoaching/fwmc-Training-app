"""Einheitliches Design (Fabian, 2026-10-03: "aus einer Feder"). New
windows reuse the existing look and texts. This test compares Heute and the
trainer dashboard against the existing windows: every code card is identical
(texts, colours, button), section headings look alike everywhere, the
client-facing text says "Trainer" (never "Coach"), sub screens use the same
back link, and the dashboard uses the app fonts without horizontal scroll."""
import asyncio, json, re
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
DASH = "http://localhost:8845/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra)


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        await pg.goto(BASE); await pg.wait_for_timeout(500)

        cards = await pg.evaluate("""() => [...document.querySelectorAll('.code-card')].map(c => {
          const cs = getComputedStyle(c), btn = c.querySelector('.program-entry-row button');
          return { h: c.querySelector('h2')?.textContent.trim(), p: c.querySelector('p')?.textContent.trim(),
                   bg: cs.backgroundImage + '|' + cs.backgroundColor, btn: btn?.textContent.trim(),
                   input: c.querySelector('.program-entry-row input')?.placeholder }; })""")
        check("at least 7 code cards", len(cards) >= 7, len(cards))
        # The heading names the area ("Dein persönliches Atemtraining"), everything else is identical.
        check("code card headings follow one pattern", all(re.match(r"^Deine? persönliche", c["h"]) for c in cards))
        rest = [{k: v for k, v in c.items() if k != "h"} for c in cards]
        diff = [c for c in rest if c != rest[0]]
        check("all code cards identical (text, colour, button)", not diff, diff[:2])

        heads = await pg.evaluate("""() => [...document.querySelectorAll('.section-head h2')].map(h => {
          const cs = getComputedStyle(h); return cs.fontFamily + '|' + cs.fontSize + '|' + cs.fontWeight; })""")
        check("section headings look alike", len(set(heads)) == 1, set(heads))

        text = await pg.evaluate("""() => { const c = document.body.cloneNode(true);
          c.querySelectorAll('script,style').forEach(e => e.remove()); return c.textContent; }""")
        coach = [m.group(0) for m in re.finditer(r".{0,30}\\bCoach\\b.{0,30}", text)]
        check("no 'Coach' in client-facing text", not coach, coach[:3])
        src = open("../app.js", encoding="utf-8").read()
        coach_js = re.findall(r'"[^"\\n]*\\b(?:deinem|Dein|dein) Coach\\b[^"\\n]*"', src)
        check("no 'dein Coach' in app texts", not coach_js, coach_js[:2])

        backs = await pg.evaluate("""() => ['progressScreen','planScreen'].map(id =>
          !!document.querySelector('#' + id + ' > .brandbar > .back-link.bar-back-btn'))""")
        check("Heute sub screens use the shared back button in the logo bar", all(backs), backs)
        # Every sub page: its back link sits top left in the logo bar (2026-10-05)
        loose = await pg.evaluate("""() => [...document.querySelectorAll('.screen .back-link')]
          .filter(b => !b.matches('.screen > .brandbar > .back-link.bar-back-btn:first-child')).map(b => b.id)""")
        check("every back link is the round button in the logo bar", not loose, loose[:5])
        await b.close()

        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        d = await b.new_page(viewport={"width": 390, "height": 844})
        d.on("pageerror", lambda e: errors.append("dash: " + str(e)))
        prog = {"code": "ein-sehr-langer-code-abcdef", "active": True, "name": "Langer Name für ein Programm",
                "createdAt": "2026-10-01T10:00:00Z", "updatedAt": "2026-10-01T10:00:00Z", "seatsUsed": 3,
                "config": {"name": "X", "codeKind": "gruppe", "seats": 12, "validUntil": "2026-12-31",
                           "blocks": [{"exercise": "vt-color", "duration": 30}]}}

        async def api(r):
            if "/admin/programs" in r.request.url:
                await r.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": [prog]}))
            else:
                await r.fulfill(status=200, content_type="application/json", body='{"history":[]}')
        await d.route("https://online-training.fwmc.workers.dev/**", api)
        await d.add_init_script("localStorage.setItem('fwmc-admin-token','t')")
        await d.goto(DASH); await d.wait_for_timeout(600)
        sw = await d.evaluate("document.documentElement.scrollWidth")
        check("dashboard: no horizontal scroll at 390px", sw <= 390, sw)
        fonts = await d.evaluate("""() => [getComputedStyle(document.querySelector('#app h1')).fontFamily,
                                         getComputedStyle(document.body).fontFamily]""")
        check("dashboard: app fonts (Magra / Public Sans)", "Magra" in fonts[0] and "Public Sans" in fonts[1], fonts)
        check("dashboard: neutral title", "Trainer-Dashboard" in await d.inner_text("#app h1"))
        await b.close()
    check("no page errors", not errors, errors[:3])
    bad = [n for n, ok in results if not ok]
    print("FAILED:", bad if bad else "none")


asyncio.run(main())
