"""App-Gefühl wie iOS (Fabian, 2026-10-05: Seitenübergänge "viel zu schnell",
wirkten wie Einblenden statt Hereinschieben; "Das musst du selbst
bemerken"). Part of the Fabian-Blick: measures the real animations and
gestures in Chromium against the iOS reference values and lists every
deviation.

iOS reference (UIKit defaults):
  - push: new page slides in fully from the right (translateX 100% -> 0),
    no fade, about 0.35 s, spring-like ease-out; the old page moves ~30 %
    to the left; the top bar stays.
  - pop / back: reverse, same duration.
  - sheet: slides up from the bottom (translateY 100% -> 0), ~0.35-0.5 s,
    grab handle (about 36x5 px) at the top, closes by pulling down.
  - swipe from the left edge goes back; tab bar targets >= 44 px.

Checks that fail today and are already on the finding list (Fabian-Blick
report) are in KNOWN and print as BEKANNT; everything else must pass.
When one gets fixed, remove it from KNOWN.
"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = """
for (const [k, v] of Object.entries({'fwmc-test-unlocked': 'true', 'fwmc-tips-seen': 'true',
  'fwmc-test-bottomnav': 'true', 'fwmc-test-natmodes': 'true', 'fwmc-test-transitions': 'true',
  'fwmc-install-hint-dismissed': 'true'})) if (localStorage.getItem(k) === null) localStorage.setItem(k, v);
"""
KNOWN = {  # Fundliste 2026-10-05, App-Thread behebt sie; nach dem Beheben hier streichen
    "Push: Dauer wie iOS (0,30-0,50 s)",
    "Push: kommt ganz von rechts (translateX 100 %), nicht nur ein Stück",
    "Push: kein Einblenden (Deckkraft bleibt), wie iOS",
    "Zurück: Dauer wie iOS (0,30-0,50 s)",
    "Fenster (Sheet): fährt animiert von unten herein",
    "Fenster (Sheet): Dauer wie iOS (0,30-0,50 s)",
    "Fenster (Sheet): Griff-Strich oben wie iOS",
    "Fenster (Sheet): schließt durch Herunterziehen",
}
results = []
CUR = "(() => { const s = [...document.querySelectorAll('.screen')].find(s => !s.hidden); return s ? s.id : ''; })()"


def check(name, ok, info=""):
    tag = "OK" if ok else ("BEKANNT" if name in KNOWN else "FEHLT")
    results.append((name, bool(ok)))
    print(f"[{tag}] {name}:", bool(ok), info)


ANIMS_JS = r"""
(sel) => {
  const root = document.querySelector(sel); if (!root) return [];
  return root.getAnimations({subtree: true}).map(a => {
    const t = a.effect.getTiming(), kf = a.effect.getKeyframes();
    return {target: (a.effect.target.id || a.effect.target.className || a.effect.target.tagName) + '',
            name: a.animationName || '', duration: +t.duration || 0, easing: t.easing,
            fromTransform: (kf[0] && kf[0].transform) || '', fromOpacity: kf[0] && kf[0].opacity};
  });
}
"""


async def touch_swipe(pg, x0, y0, x1, y1, steps=8):
    cdp = await pg.context.new_cdp_session(pg)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        x = x0 + (x1 - x0) * i / steps; y = y0 + (y1 - y0) * i / steps
        await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
        await pg.wait_for_timeout(16)
    await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--overscroll-history-navigation=0"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
                                  service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))

        # ---- push: area home -> exercise page ----
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(600)
        await pg.click(".nat-tile >> nth=0")
        await pg.wait_for_timeout(30)
        sid = await pg.evaluate(CUR)
        anims = await pg.evaluate(ANIMS_JS, "#" + sid)
        dur = max([a["duration"] for a in anims] or [0])
        check("Push: Seite schiebt sich überhaupt animiert herein", bool(anims), anims[:1])
        check("Push: Dauer wie iOS (0,30-0,50 s)", 300 <= dur <= 500, f"{dur:.0f} ms")
        full = any("translateX(100%)" in a["fromTransform"] or "translateX(9" in a["fromTransform"] for a in anims)
        check("Push: kommt ganz von rechts (translateX 100 %), nicht nur ein Stück", full,
              sorted({a["fromTransform"] for a in anims})[:2])
        fade = any(a["fromOpacity"] not in (None, "", "1") and float(a["fromOpacity"] or 1) < 0.5 for a in anims)
        check("Push: kein Einblenden (Deckkraft bleibt), wie iOS", not fade,
              sorted({str(a["fromOpacity"]) for a in anims}))
        bar_anim = await pg.evaluate(ANIMS_JS, f"#{sid} > .brandbar")
        check("Push: obere Leiste bleibt stehen", not bar_anim)
        await pg.wait_for_timeout(700)

        # ---- pop: back button ----
        await pg.click(f"#{sid} .bar-back-btn")
        await pg.wait_for_timeout(30)
        sid2 = await pg.evaluate(CUR)
        anims = await pg.evaluate(ANIMS_JS, "#" + sid2)
        dur = max([a["duration"] for a in anims] or [0])
        check("Zurück: Dauer wie iOS (0,30-0,50 s)", 300 <= dur <= 500, f"{dur:.0f} ms")
        await pg.wait_for_timeout(700)

        # ---- swipe from the left edge goes back ----
        # Chromium's own edge-swipe would leave the page (history back), so give
        # it a harmless in-page history entry; only the app's handler can change the screen.
        await pg.evaluate("history.pushState({}, '', location.href)")
        await pg.click(".nat-tile >> nth=0"); await pg.wait_for_timeout(800)
        before = await pg.evaluate(CUR)
        await touch_swipe(pg, 8, 420, 300, 425)
        await pg.wait_for_timeout(800)
        after = await pg.evaluate(CUR)
        check("Wischen vom linken Rand geht zurück", before != after, f"{before} -> {after}")

        # ---- sheet: Grundeinstellungen ----
        if not after:
            print("  nach dem Wischen ist keine Seite sichtbar, URL:", pg.url, await pg.evaluate("[...document.querySelectorAll('.screen')].filter(s => !s.hidden).map(s => s.id)"))
            await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(600); after = "natHome"
        await pg.click(f"#{after} .master-settings-btn")
        await pg.wait_for_timeout(30)
        anims = await pg.evaluate(ANIMS_JS, "#masterSettingsSheet")
        dur = max([a["duration"] for a in anims] or [0])
        check("Fenster (Sheet): fährt animiert von unten herein", any("translateY" in a["fromTransform"] for a in anims),
              sorted({a["fromTransform"] for a in anims})[:2])
        check("Fenster (Sheet): Dauer wie iOS (0,30-0,50 s)", 300 <= dur <= 500, f"{dur:.0f} ms")
        await pg.wait_for_timeout(700)
        handle = await pg.evaluate("""() => {
          const s = document.querySelector('#masterSettingsSheet .sheet-inner'); if (!s) return null;
          const r = s.getBoundingClientRect();
          const cands = [...s.querySelectorAll('*')].map(e => [e, e.getBoundingClientRect()]);
          for (const pe of ['::before', '::after']) { const c = getComputedStyle(s, pe);
            if (c.content && c.content !== 'none' && parseFloat(c.width) >= 25 && parseFloat(c.width) <= 60 && parseFloat(c.height) <= 8) return 'pseudo'; }
          const h = cands.find(([e, q]) => q.width >= 25 && q.width <= 60 && q.height >= 3 && q.height <= 8 && q.top - r.top < 24);
          return h ? 'element' : null; }""")
        check("Fenster (Sheet): Griff-Strich oben wie iOS", bool(handle), handle)
        box = await pg.evaluate("(() => { const r = document.querySelector('#masterSettingsSheet .sheet-inner').getBoundingClientRect(); return [r.left + r.width / 2, r.top + 12]; })()")
        await touch_swipe(pg, box[0], box[1], box[0], box[1] + 400, steps=12)
        await pg.wait_for_timeout(800)
        closed = await pg.evaluate("document.getElementById('masterSettingsSheet').hidden")
        check("Fenster (Sheet): schließt durch Herunterziehen", closed)
        if not closed:
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)

        # ---- bottom bar ----
        sizes = await pg.evaluate("[...document.querySelectorAll('#bottomNav .bottom-nav-btn')].map(b => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })")
        check("Untere Leiste: jede Taste mind. 44 px", sizes and all(min(s) >= 44 for s in sizes), sizes)
        await b.close()
    check("keine Seitenfehler", not errors, errors[:2])
    bad = [n for n, ok in results if not ok and n not in KNOWN]
    print("NEUE ABWEICHUNGEN:", bad if bad else "keine")

asyncio.run(main())
