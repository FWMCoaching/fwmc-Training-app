import asyncio, json
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=training"

# Training-Übersicht (Fabian 2026-10-06: "warum sind das untere jetzt
# Querdinger?"): the lower "Dazu" tiles sit 2 per row like the core tiles
# (4 per row from 700 px), and every area name stays on one line inside its
# tile - from a small Android phone to a laptop, also with large iPhone text.

INIT = """localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');
localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-onboarding-v1','done');"""

MEASURE = """() => { const vis = (t) => t.offsetParent;
  const core = [...document.querySelectorAll('#trainingHub .hub-core .area-tile')].filter(vis);
  const extra = [...document.querySelectorAll('#trainingHub .hub-extra .area-tile')].filter(vis);
  const perRow = (tiles) => tiles.filter((t) => Math.abs(t.getBoundingClientRect().top - tiles[0].getBoundingClientRect().top) < 2).length;
  const bad = [...core, ...extra].map((t) => { const n = t.querySelector('.area-name'); const r = t.getBoundingClientRect(), nr = n.getBoundingClientRect();
    const lh = parseFloat(getComputedStyle(n).fontSize) * 1.6;
    return (nr.height > lh || nr.right > r.right - 6) ? n.textContent.trim() : null; }).filter(Boolean);
  return { core: perRow(core), extra: perRow(extra), n: extra.length, bad }; }"""

def ok(label, cond, fails):
    print(label + ":", bool(cond))
    if not cond: fails.append(label)

async def main():
    errors, fails = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for ts in [None, 1.25]:
            for w in [360, 375, 390, 430, 768, 1024, 1440]:
                ctx = await b.new_context(viewport={"width": w, "height": 900}, service_workers="block")
                await ctx.add_init_script(INIT + (f"localStorage.setItem('fwmc-test-textscale','{ts}');" if ts else ""))
                pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
                pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
                await pg.goto(URL); await pg.wait_for_timeout(400)
                r = await pg.evaluate(MEASURE)
                want = 4 if w >= 700 else 2
                tag = f"{w}px" + (f" x{ts}" if ts else "")
                ok(f"{tag}: lower tiles {want} per row like the core tiles {json.dumps(r)}", r["n"] >= 2 and r["core"] == want and r["extra"] == min(want, r["n"]), fails)
                ok(f"{tag}: every area name on one line inside its tile", not r["bad"], fails)
                await ctx.close()
        await b.close()
    print("FAILED:", fails or "none")
    print("FINAL ERRORS:", errors)

asyncio.run(main())
