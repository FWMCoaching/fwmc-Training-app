import asyncio, json
from playwright.async_api import async_playwright

# Layout audit (Fabian, 2026-10-04: "Sowas muss geprüft werden und darf
# nicht vorkommen"): every area's home screen, plus each NAT sub-tab, at
# phone, tablet and laptop widths. Fails on
#  - a word broken in the middle across two lines (e.g. "Atemtrainin|g"),
#  - text sticking out of its own button/tab,
#  - the page scrolling sideways.
# A break right after a hyphen ("Flash-|Speicher") is allowed.
# New screens get covered by adding them to AREAS / the NAT loop.

BASE = "http://localhost:8845/index.html?bereich="
AREAS = ["heute", "visual", "breath", "movement", "workout", "cardio", "nat", "test", "free"]
WIDTHS = [375, 390, 430, 600, 768, 820, 1024, 1180, 1366]
# iPhone text size (2026-10-06): the app follows the iOS setting up to 1.25x
# (--ts), so small phones are also checked with the biggest and smallest factor.
SCALED = [(375, 1.25), (390, 1.25), (430, 1.25), (390, 0.95)]

AUDIT_JS = r"""
() => {
  const scr = [...document.querySelectorAll('.screen')].find(s => !s.hidden && s.offsetParent !== null);
  const root = scr || document.body;
  const out = [];
  const visible = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || !visible(el)) continue;
    if (el.closest('[hidden], details:not([open]) > :not(summary), input, textarea, select, svg')) continue;
    const re = /[^\s\-–­/]+[\-–­/]?/g;
    let m;
    while ((m = re.exec(n.textContent))) {
      const tok = m[0].replace(/[\-–­/]$/, '');
      if (tok.length < 2) continue;
      // Compare the line of the word's first and last letter (per-letter
      // ranges: a range spanning a soft hyphen also reports the hyphen glyph
      // on the previous line, which is a legal break, not a split word).
      const lineOf = i => {
        const rg = document.createRange();
        rg.setStart(n, i); rg.setEnd(n, i + 1);
        const rs = [...rg.getClientRects()];
        return rs.length ? Math.round(rs[rs.length - 1].top) : null;
      };
      const a = lineOf(m.index), z = lineOf(m.index + tok.length - 1);
      if (a !== null && z !== null && Math.abs(z - a) > 4)
        out.push('Wort getrennt: "' + tok + '" in <' + el.tagName.toLowerCase() + '.' + el.className + '>');
    }
  }
  root.querySelectorAll('button, .section-tab, .sub-tab, .choice').forEach(b => {
    if (!visible(b) || b.closest('[hidden]')) return;
    if (b.scrollWidth > b.clientWidth + 2) out.push('Text ragt aus Knopf: "' + b.textContent.trim().slice(0, 30) + '"');
  });
  // Tabs keep their label on one line (Fabian, 2026-10-05: "keine Umbrüche in den Reitern").
  root.querySelectorAll('.section-tab, .sub-tab').forEach(t => {
    if (!visible(t)) return;
    const rg = document.createRange(); rg.selectNodeContents(t);
    const lines = new Set([...rg.getClientRects()].filter(r => r.width > 1).map(r => Math.round(r.top))).size;
    if (lines > 1) out.push('Reiter zweizeilig: "' + t.textContent.trim().slice(0, 30) + '"');
  });
  if (document.documentElement.scrollWidth > window.innerWidth + 1)
    out.push('Seite scrollt seitlich (' + document.documentElement.scrollWidth + ' > ' + window.innerWidth + ')');
  return [...new Set(out)];
}
"""

def ts_tag(ts):
    return "" if ts == 1 else f" Schrift x{ts}"

async def audit(pg, label, problems):
    found = await pg.evaluate(AUDIT_JS)
    for f in found:
        problems.append(label + ": " + f)

async def main():
    problems, errors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for w, ts in [(w, 1) for w in WIDTHS] + SCALED:
            ctx = await b.new_context(viewport={"width": w, "height": 900}, service_workers="block")
            await ctx.add_init_script("localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-tips-seen','true')"
                                      + (f";localStorage.setItem('fwmc-test-textscale','{ts}');localStorage.setItem('fwmc-test-bottomnav','true')" if ts != 1 else ""))
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            for area in AREAS:
                await pg.goto(BASE + area); await pg.wait_for_timeout(250)
                await audit(pg, f"{w}px{ts_tag(ts)} {area}", problems)
                if area == "nat":
                    subs = await pg.eval_on_selector_all("#natHome .sub-tab", "els => els.map(e => e.dataset.natSub)")
                    for s in subs[1:]:
                        await pg.click(f'#natHome .sub-tab[data-nat-sub="{s}"]'); await pg.wait_for_timeout(150)
                        await audit(pg, f"{w}px{ts_tag(ts)} nat/{s}", problems)
                if area == "visual":
                    # Farbfelder ready screen (2026-10-07): Modus, Stufe 1-4, hand rows
                    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => ['[data-ff-mode=regeln]','[data-ff-level=\"4\"]','[data-ff-hands=\"1\"]'].forEach(s => document.querySelector(s).click())")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/farbfelder", problems)
                    # Reize (2026-10-07 night): Sehen und Hören shows gilt, Mischung, Rhythmus-Umkehr
                    await pg.evaluate("() => ['[data-ff-mode=sehenhoeren]','[data-ff-flip=\"2\"]'].forEach(s => document.querySelector(s).click())")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/farbfelder-sehenhoeren", problems)
                    await pg.evaluate("() => ['[data-ff-hands=\"0\"]','[data-ff-flip=\"0\"]','[data-ff-mode=leuchten]'].forEach(s => document.querySelector(s).click())")
                if area == "free":
                    # Freie Bausteine: ready screen and editor (checklist) of the template
                    await pg.click('#freeTplGrid [data-free-id="tpl-dehnen"]'); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} free/ready", problems)
                    await pg.click("#freeCopyBtn"); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} free/edit", problems)
            await ctx.close()
        await b.close()
    for x in problems: print("  " + x)
    print("Layout-Audit ohne Befund:", not problems, f"({len(problems)} Befunde)")
    print("No page errors:", not errors, errors[:3])

asyncio.run(main())
