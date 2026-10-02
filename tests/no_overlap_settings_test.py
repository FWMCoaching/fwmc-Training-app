import asyncio
from playwright.async_api import async_playwright

# Client rule (2026-10-02, after "Intensität" was covered by its slider in
# Master-Einstellungen): nowhere in the app may text and a control overlap -
# settings screens included, not only exercise stages.
# 1) Every .slider-row in the DOM is cloned into a narrow 280px box and its
#    children must not overlap each other.
# 2) The Master sheet and several ready screens (all <details> opened) are
#    checked live: no two visible siblings may overlap.

URL = "http://localhost:8845/index.html"

SIBLING_CHECK = """(rootSel) => {
  const root = document.querySelector(rootSel);
  if (!root) return ['missing ' + rootSel];
  root.querySelectorAll('details').forEach(d => d.open = true);
  const bad = [];
  const ext = el => { const r = el.getBoundingClientRect(); if (!el.textContent.trim() || el.children.length) return r;
    const g = document.createRange(); g.selectNodeContents(el); const t = g.getBoundingClientRect();
    return { left: Math.min(r.left, t.left), right: Math.max(r.right, t.right), top: Math.min(r.top, t.top), bottom: Math.max(r.bottom, t.bottom), width: r.width, height: r.height }; };
  const vis = el => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.position === 'absolute' || cs.position === 'fixed') return null;
    return ext(el);
  };
  root.querySelectorAll('*').forEach(parent => {
    if (parent instanceof SVGElement) return;
    const kids = [...parent.children].map(k => [k, vis(k)]).filter(x => x[1]);
    for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
      const a = kids[i][1], b = kids[j][1];
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 1 && oy > 1) bad.push((kids[i][0].id || kids[i][0].className || kids[i][0].tagName) + ' x ' +
        (kids[j][0].id || kids[j][0].className || kids[j][0].tagName) + ' in ' + (parent.id || parent.className));
    }
  });
  return bad;
}"""

SLIDER_CLONE_CHECK = """() => {
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;left:0;top:0;width:280px;background:#fff;z-index:99999';
  document.body.appendChild(box);
  const bad = []; let n = 0;
  const ext = el => { const r = el.getBoundingClientRect(); if (!el.textContent.trim() || el.children.length) return r;
    const g = document.createRange(); g.selectNodeContents(el); const t = g.getBoundingClientRect();
    return { left: Math.min(r.left, t.left), right: Math.max(r.right, t.right), top: Math.min(r.top, t.top), bottom: Math.max(r.bottom, t.bottom), width: r.width, height: r.height }; };
  
  document.querySelectorAll('.slider-row').forEach(row => {
    const c = row.cloneNode(true); c.hidden = false; c.removeAttribute('id');
    box.innerHTML = ''; box.appendChild(c); n++;
    const kids = [...c.children].filter(k => { const r = k.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
      const a = ext(kids[i]), b = ext(kids[j]);
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 1 && oy > 1) bad.push((row.id || row.parentElement.id || '?') + ': "' + kids[i].textContent.trim() + '" x ' + kids[j].tagName);
    }
  });
  box.remove();
  return { n, bad };
}"""

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true'); localStorage.setItem('fwmc-tips-seen', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(500)

        res = await pg.evaluate(SLIDER_CLONE_CHECK)
        print("slider rows checked:", res["n"] > 40, res["n"])
        print("no slider-row overlaps at 280px:", res["bad"] == [], res["bad"][:5])

        # Master sheet, with a background default so the intensity row shows
        await pg.click(".master-settings-btn"); await pg.wait_for_timeout(200)
        await pg.click('#masterBgColorPicker [data-key="rot"]'); await pg.wait_for_timeout(150)
        lab = await pg.evaluate("""() => {
          const row = document.querySelector('#masterBgIntensityRow');
          const l = row.querySelector('.slider-label').getBoundingClientRect();
          const s = row.querySelector('input[type=range]').getBoundingClientRect();
          return l.right <= s.left + 0.5;
        }""")
        print("Master 'Intensität' label left of its slider:", lab)
        bad = await pg.evaluate(SIBLING_CHECK, "#masterSettingsSheet")
        print("Master sheet: no overlapping siblings:", bad == [], bad[:5])
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)

        # A few ready screens with sliders in their Feineinstellungen
        screens = [
            ("#gngOpenBtn", "#gngReady"),
        ]
        await pg.evaluate("() => document.querySelector('[data-section=test]').click()"); await pg.wait_for_timeout(200)
        for btn, scr in screens:
            if await pg.query_selector(btn):
                await pg.click(btn); await pg.wait_for_timeout(200)
                bad = await pg.evaluate(SIBLING_CHECK, scr)
                print(scr + ": no overlapping siblings:", bad == [], bad[:5])

        for sec, card, scr in [("workout", "#workoutRepsStartCard", "#workoutRepsReady"), ("cardio", "#cardioStartCard", "#cardioReady")]:
            await pg.evaluate("(s) => document.querySelector('.section-tab[data-section=' + s + ']').click()", sec); await pg.wait_for_timeout(200)
            await pg.click(card); await pg.wait_for_timeout(250)
            bad = await pg.evaluate(SIBLING_CHECK, scr)
            print(scr + ": no overlapping siblings:", bad == [], bad[:5])

        print("no page errors:", errors == [], errors[:3])
        await b.close()

asyncio.run(main())
