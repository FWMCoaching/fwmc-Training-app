"""Knopf lesbar (Fabian 2026-10-08 abends: "Öffnen" neben dem Code-Feld war im
Dunkelmodus unsichtbar - dunkle Schrift auf dunklem Grund, weil eine
allgemeine Dunkel-Regel die Code-Karten-Regel überstimmte).

General check of that kind of error: on every main page and area home, with
every collapsible (code cards) opened, every visible button/link with text
has a text/background contrast of at least 3:1 (WCAG large-text minimum),
light and dark. The background is the first non-transparent one up the tree.
Also: no page errors."""
import asyncio
import os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
PAGES = ["heute", "training", "fortschritt", "visual", "breath", "nat", "movement", "workout", "cardio", "free", "aktivierung"]
errors = []

MEASURE = r"""() => {
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(Number); return {r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0.5) return c; } return parse(getComputedStyle(document.body).backgroundColor); };
  const bad = [];
  document.querySelectorAll('button, a.text-link, a.start-btn').forEach((el) => {
    if (!el.getClientRects().length || el.closest('[hidden]')) return;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || Number(cs.opacity) < 0.3) return;
    const txt = (el.innerText || '').trim();
    if (!txt) return;
    const fg = parse(cs.color), bg = bgOf(el);
    if (!fg || !bg) return;
    const l1 = lum(fg), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    if (ratio < 3) bad.push(`${el.id ? '#' + el.id : el.className.split(' ')[0]} "${txt.slice(0, 24)}" ${ratio.toFixed(2)}`);
  });
  return bad;
}"""


async def main():
    found = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for scheme in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
            await ctx.add_init_script("try{localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-codequiet','true');localStorage.setItem('fwmc-test-bottomnav','true');localStorage.setItem('fwmc-test-trainer-tools','true')}catch(e){}")
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            for name in PAGES:
                await pg.goto(ROOT + f"?bereich={name}"); await pg.wait_for_timeout(350)
                # open every collapsed code card on the visible screen
                await pg.evaluate("document.querySelectorAll('.screen:not([hidden]) .code-card.is-collapsed .code-toggle').forEach((b) => b.click())")
                await pg.wait_for_timeout(150)
                bad = await pg.evaluate(MEASURE)
                if bad:
                    found[f"{scheme}/{name}"] = bad
            await ctx.close()
        await b.close()
    for k, v in found.items():
        print(k, v[:6])
    print("every button readable (contrast >= 3:1), light and dark:", not found)
    print("no page errors:", not errors, errors[:3])


asyncio.run(main())
