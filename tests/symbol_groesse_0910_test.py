"""Symbole mit fester Größe (Fabian 09.10.2026, altes iPad mini).

On an old iPad mini the gear in the top bar showed as a dot: older Safari
treats an SVG's width/height attributes inside a flex button as a hint and
shrinks the icon. Every icon inside a button/link/label must get its size
from CSS. Check: remove the width/height attributes of every such SVG and
compare the rendered size - it must not change, and must not be 0.

Chromium cannot show the Safari bug itself; this checks the cause (an icon
sized only by attributes), which is what makes it safe there.
"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = """
for (const [k, v] of Object.entries({
  'fwmc-test-unlocked': 'true', 'fwmc-tips-seen': 'true', 'fwmc-test-bottomnav': 'true',
  'fwmc-test-natmodes': 'true', 'fwmc-install-hint-dismissed': 'true', 'fwmc-test-trainer-tools': 'true',
  'fwmc-master-v1': JSON.stringify({startCountdown: false})})) {
  if (localStorage.getItem(k) === null) localStorage.setItem(k, v);
}
"""
CHECK_JS = r"""
() => {
  const bad = [];
  const svgs = [...document.querySelectorAll('button svg, a svg, label svg, [role=button] svg')]
    .filter((s) => s.getBoundingClientRect().width > 0 && !s.closest('svg svg'));
  const before = svgs.map((s) => { const r = s.getBoundingClientRect(); return [r.width, r.height]; });
  const saved = svgs.map((s) => [s.getAttribute('width'), s.getAttribute('height')]);
  svgs.forEach((s) => { s.removeAttribute('width'); s.removeAttribute('height'); });
  svgs.forEach((s, i) => {
    const r = s.getBoundingClientRect();
    if (Math.abs(r.width - before[i][0]) > 0.5 || Math.abs(r.height - before[i][1]) > 0.5) {
      const host = s.closest('button, a, label, [role=button]');
      bad.push(`${host.id || host.className || host.tagName} > ${s.getAttribute('class') || 'svg'}: ${before[i][0]}x${before[i][1]} -> ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
  });
  svgs.forEach((s, i) => {
    if (saved[i][0] != null) s.setAttribute('width', saved[i][0]);
    if (saved[i][1] != null) s.setAttribute('height', saved[i][1]);
  });
  return { n: svgs.length, bad: [...new Set(bad)] };
}
"""
PAGES = ["heute", "training", "visual", "nat", "breath", "workout", "cardio", "free", "fortschritt", "aktivierung"]
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  {extra}" if not ok else ""))


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for w, h in ((390, 844), (768, 1024)):
            ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block")
            await ctx.add_init_script(INIT)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            for name in PAGES:
                await pg.goto(f"{BASE}?bereich={name}"); await pg.wait_for_timeout(500)
                r = await pg.evaluate(CHECK_JS)
                check(f"[{w}] {name}: {r['n']} Symbole haben eine feste Größe", not r["bad"], r["bad"][:6])
            # trainer menu + more page + gear sheet
            await pg.goto(f"{BASE}?bereich=training"); await pg.wait_for_timeout(500)
            await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(300)
            r = await pg.evaluate(CHECK_JS)
            check(f"[{w}] Trainer-Menü: Symbole haben eine feste Größe", not r["bad"], r["bad"][:6])
            await pg.goto(f"{BASE}?bereich=heute"); await pg.wait_for_timeout(400)
            await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(400)
            r = await pg.evaluate(CHECK_JS)
            check(f"[{w}] Mehr: Symbole haben eine feste Größe", not r["bad"], r["bad"][:6])
            gear = await pg.evaluate("(() => { const s = [...document.querySelectorAll('.master-settings-btn .gear-icon')].find((e) => e.getBoundingClientRect().width); if (!s) return null; const c = getComputedStyle(s); return [c.width, c.height]; })()")
            check(f"[{w}] Zahnrad oben rechts 22 px groß", gear == ["22px", "22px"], gear)
            await ctx.close()
        await b.close()
    check("keine Seitenfehler", not errors, errors[:3])
    failed = [n for n, ok in results if not ok]
    print(f"{len(results) - len(failed)}/{len(results)} passed")
    print("FAILED: " + (", ".join(failed) if failed else "none"))


asyncio.run(main())
