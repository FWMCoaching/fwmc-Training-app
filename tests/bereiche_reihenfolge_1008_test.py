import asyncio, os
from playwright.async_api import async_playwright

# Gleiche Abschnitt-Reihenfolge in allen Bereichen (Idee 20, Fabian 08.10.):
# every area home reachable from the Training hub has its sections in one
# order. Krafttraining (workout) and Ausdauertraining (cardio) are different
# on purpose and excluded. Categories of the visible top-level sections:
#   hero < Code-Karte < Beispiel-Programme < Übungen < Kombi-Link < Gesamter Trainingsverlauf
# (Beispiel-Programme above the exercises = the app's own order in Visuelles
# Training and Atemtraining, the reference siblings). Code card, exercises and
# history are required (Test-Bereich has no code card on purpose), programmes
# and the Kombi link only where present. Checked in the real layout (bottom
# bar + NAT tiles) at 390 and 1024 px by DOM order AND on-screen position (a
# CSS `order` must not reshuffle it), and in the automated-browser fallback
# layout (no bottom bar) for the same order across areas.
# A new area appears here automatically (read from #hubAreaGrid). If this
# fails, move the section in the app, never loosen the test.
# Run from tests/ with a dev server (FWMC_PORT, default 8845).

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
EXCLUDED = {"workout", "cardio"}
NO_CODE_CARD = {"test"}
RANK = {"hero": 0, "code": 1, "programs": 2, "exercises": 3, "kombi": 4, "history": 5}
NAMES = {"hero": "Kopf", "code": "Code-Karte", "programs": "Beispiel-Programme", "exercises": "Übungen", "kombi": "Kombi-Programm", "history": "Gesamter Trainingsverlauf"}

SECTIONS_JS = r"""() => {
  const s = [...document.querySelectorAll('.screen')].find((x) => !x.hidden && x.getClientRects().length);
  if (!s) return null;
  const out = [];
  for (const c of s.children) {
    if (!c.getClientRects().length || getComputedStyle(c).display === 'none' || getComputedStyle(c).visibility === 'hidden') continue;
    const tag = c.tagName.toLowerCase();
    if (tag === 'header' || tag === 'footer' || tag === 'nav' || tag === 'script' || tag === 'template') continue;
    let cat = null;
    if (c.matches('.hero')) cat = 'hero';
    else if (c.matches('.code-card') || c.querySelector(':scope > .code-card')) cat = 'code';
    else if (c.matches('.combo-entry-link, .combo-entry-card')) cat = 'kombi';
    else if (c.matches('.history') || /Gesamter Trainingsverlauf/.test((c.querySelector('h2,h3') || {}).textContent || '')) cat = 'history';
    else if (c.matches('.featured-programs')) cat = 'programs';
    else if (tag === 'section' || c.matches('.patterns, .exercises, .nat-panel, .nat-tiles')) cat = 'exercises';
    if (!cat) continue; // small helper rows (labels, hints) between sections
    const r = c.getBoundingClientRect();
    out.push({ cat, top: Math.round(r.top + scrollY), label: ((c.querySelector('h1,h2,h3') || {}).textContent || c.className).trim().slice(0, 40) });
  }
  return { id: s.id, sections: out };
}"""

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

def order_problems(area, secs):
    probs = []
    cats = [x["cat"] for x in secs]
    for a, b in zip(cats, cats[1:]):
        if RANK[b] < RANK[a]:
            probs.append(f"{NAMES[b]} steht nach {NAMES[a]}")
    tops = [x["top"] for x in secs]
    if tops != sorted(tops):
        probs.append(f"Bildschirm-Reihenfolge weicht von der DOM-Reihenfolge ab: {tops}")
    if area not in NO_CODE_CARD and "code" not in cats: probs.append("keine Code-Karte")
    if "exercises" not in cats: probs.append("keine Übungen")
    if "history" not in cats: probs.append("kein Gesamter Trainingsverlauf")
    elif cats[-1] != "history": probs.append("Gesamter Trainingsverlauf ist nicht der letzte Abschnitt")
    return probs

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        flags = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-test-neuro','true');"
                 "localStorage.setItem('fwmc-test-codequiet','true');")
        real = flags + "localStorage.setItem('fwmc-test-bottomnav','true');localStorage.setItem('fwmc-test-natmodes','true');"
        for layout, init in (("echt", real), ("ohne Leiste", flags)):
            for w, h in ((390, 844), (1024, 768)):
                ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block")
                await ctx.add_init_script(init)
                pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
                pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(400)
                # the hub only exists with the bottom bar; the fallback layout uses the same area list
                if layout == "echt":
                    areas = await pg.evaluate("() => [...document.querySelectorAll('#hubAreaGrid .area-tile')].map((t) => t.dataset.area)")
                    hub_areas = areas
                else:
                    areas = hub_areas
                tag = f"[{layout} {w}]"
                check(f"{tag} hub lists the areas incl. activation, free, nat, visual, breath, movement, test, neuro",
                      all(a in areas for a in ["visual", "breath", "movement", "nat", "free", "activation", "test", "neuro"]), areas)
                seqs = {}
                for area in areas:
                    if layout == "echt":
                        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(250)
                        await pg.click(f'#hubAreaGrid .area-tile[data-area="{area}"]'); await pg.wait_for_timeout(300)
                    else:
                        await pg.goto(BASE + "?bereich=" + {"activation": "aktivierung"}.get(area, area)); await pg.wait_for_timeout(300)
                    res = await pg.evaluate(SECTIONS_JS)
                    if not res:
                        check(f"{tag} {area}: area home opens", False); continue
                    secs = res["sections"]
                    print(f"{tag} {area} ({res['id']}): " + " > ".join(f"{NAMES[x['cat']]}" for x in secs))
                    if area in EXCLUDED: continue
                    seqs[area] = [x["cat"] for x in secs]
                    probs = order_problems(area, secs)
                    if layout == "ohne Leiste":
                        # the fallback layout keeps the old Kombi link at the top of every area:
                        # only the order of the other sections counts there, the Kombi
                        # position is compared across areas below
                        probs = [x for x in probs if "Kombi" not in x]
                    check(f"{tag} {area}: section order", not probs, "; ".join(probs))
                # same relative order across all areas (incl. the Kombi link in the fallback layout)
                ref = {}
                bad = []
                for area, cats in seqs.items():
                    for i, a in enumerate(cats):
                        for c in cats[i + 1:]:
                            if a == c: continue
                            key = tuple(sorted((a, c)))
                            first = a
                            if key in ref and ref[key][0] != first: bad.append(f"{area}: {NAMES[a]} vor {NAMES[c]}, {ref[key][1]} umgekehrt")
                            ref.setdefault(key, (first, area))
                check(f"{tag} same relative order in every area", not bad, "; ".join(sorted(set(bad))[:5]))
                await ctx.close()
        check("no page/console errors", errors == [], errors[:5])
        await b.close()
    print("FAILS:", fails)
    print("ERRORS:", errors)

asyncio.run(main())
