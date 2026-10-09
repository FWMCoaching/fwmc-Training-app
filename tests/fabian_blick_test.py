"""Fabian-Blick (Fabian, 2026-10-04: "Fehler vorher finden"): one automatic
walk through the whole app, looking for the KINDS of error Fabian keeps
spotting by eye, instead of one test per single case.

1. Discovery: starting from every area home, the bottom bar targets and the
   gear sheet, it clicks every visible button/tile and remembers every new
   screen, sheet and player it reaches (depth 2). New screens are covered
   automatically - nothing to register.
2. Audit: every state is replayed on a small iPhone (375x667), a large
   one (430x932), a small Android phone (360x780), an iPad portrait
   (768x1024) and landscape (1024x768) and a laptop (1440x900), light and dark, with a full-page screenshot, and checked
   for these error kinds:
     umbruch     word split mid-word, text sticking out of its box,
                 page scrolling sideways, clipped text
     ueberlappt  two pieces of text/controls on top of each other, content
                 that can never scroll out from under the bottom bar
     taste       tap target smaller than 44 px
     kopf        top bar differs from the common one (height, logo, title,
                 gear, back button on sub pages), bottom bar missing
     farbe       a colour outside the design tokens (light/dark set)
     kontrast    text contrast below 4.5:1 (3:1 for large text)
     stil        the same kind of element (page title, start button, ...)
                 looks different on different screens
     name        old/forbidden names (Remember, Coach, Komplett-Programm ...)
     player      exercise player: buttons, naming (…BackBtn "Beenden",
                 …PauseBtn "Pause"), hint/bar overlap
     lange       long press on a tile three times: sheet opens every time,
                 the page never changes (first config only)
     zurueck     a ‹ is visible but swiping back / the back button does not
                 go back (first config only)
     verdeckt    an inline form (name + Abbrechen/Speichern) opened on a
                 tap lands in view, not under the sticky start bar or the
                 bottom bar, with one filled main button (first config)
     sprung      page jumps after a slide-in (Fabian 2026-10-06, Box-Atmung):
                 on a phone (mobile viewport, transitions on) the page must
                 keep the device width during every slide in, ‹ back and
                 edge swipe, and must not move/resize once it has arrived
3. Report: tests/screenshots/fabian_blick/report.md (+ report.json and the
   screenshots). Findings already known are listed in
   tests/fabian_blick_baseline.json; the test fails only on NEW findings,
   so the suite stays usable while the known list is worked down. When a
   known finding is fixed, run with --update-baseline to shrink the list.
   Never add a finding to the baseline to make the test pass without
   Fabian's ok (CLAUDE.md: fix the app, never loosen the test).

Usage (from tests/, dev server on :8845):
  python3 fabian_blick_test.py                 # full walk, 12 configs
  python3 fabian_blick_test.py --quick         # 1 config (375 light)
  python3 fabian_blick_test.py --update-baseline
"""
import asyncio, json, os, re, sys, time
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "screenshots", "fabian_blick")
BASELINE = os.path.join(HERE, "fabian_blick_baseline.json")
QUICK = "--quick" in sys.argv
UPDATE = "--update-baseline" in sys.argv
# Every device class Fabian's clients use (Fabian 2026-10-06: "iPad, Laptop,
# aber auch Android und Co"), each light and dark.
CONFIGS = [("se-hell", 375, 667, "light"), ("se-dunkel", 375, 667, "dark"),
           ("max-hell", 430, 932, "light"), ("max-dunkel", 430, 932, "dark"),
           ("android-hell", 360, 780, "light"), ("android-dunkel", 360, 780, "dark"),
           ("ipad-hell", 768, 1024, "light"), ("ipad-dunkel", 768, 1024, "dark"),
           ("ipad-quer-hell", 1024, 768, "light"), ("ipad-quer-dunkel", 1024, 768, "dark"),
           ("laptop-hell", 1440, 900, "light"), ("laptop-dunkel", 1440, 900, "dark")]
if QUICK:
    CONFIGS = CONFIGS[:1]
ENTRIES = ["heute", "visual", "breath", "movement", "workout", "cardio", "nat", "test", "free"]
MAX_DEPTH = 2

# Real user experience: bottom bar, NAT modes on; no countdown, no tips.
INIT = """
for (const [k, v] of Object.entries({
  'fwmc-test-unlocked': 'true', 'fwmc-tips-seen': 'true', 'fwmc-test-bottomnav': 'true',
  'fwmc-test-natmodes': 'true', 'fwmc-install-hint-dismissed': 'true',
  'fwmc-master-v1': JSON.stringify({startCountdown: false})})) {
  if (localStorage.getItem(k) === null) localStorage.setItem(k, v);
}
"""

# Clicks that would leave the app, delete data or end a run are not explored.
SKIP_TEXT = re.compile(r"L(ö|oe)schen|Zur(ü|ue)cksetzen|Entfernen|Beenden|Sicherung|Datei|Website|Impressum|"
                       r"Abbrechen|Teilen|Herunterladen|Exportieren|Importieren|Training starten|Baustein übernehmen|"
                       r"Bereit machen|Los geht|Starten", re.I)

STATE_JS = r"""
() => {
  const vis = el => { if (!el || el.hidden) return false; const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden' && getComputedStyle(el).display !== 'none'; };
  const scr = [...document.querySelectorAll('.screen')].filter(vis).map(e => e.id);
  const sheet = [...document.querySelectorAll('.sheet')].filter(vis).map(e => e.id);
  const player = [...document.querySelectorAll('.player')].filter(vis).map(e => e.id);
  const done = [...document.querySelectorAll('.done-panel')].filter(vis).map(e => e.id || e.className);
  const sc = document.getElementById(scr[0] || '');
  const h = sc && [...sc.querySelectorAll('h1, h2')].find(vis);
  return {screen: scr.join('+'), title: h ? h.textContent.trim().replace(/\s+/g, ' ').slice(0, 40) : '', sheet: sheet.join('+'), player: player.join('+'), done: done.join('+')};
}
"""

# Candidate clicks inside the current top layer (sheet > player > screen).
CANDIDATES_JS = r"""
(skipSrc) => {
  const skip = new RegExp(skipSrc, 'i');
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !el.closest('[hidden]'); };
  const sheets = [...document.querySelectorAll('.sheet')].filter(vis);
  const root = sheets[sheets.length - 1] || [...document.querySelectorAll('.screen')].find(vis);
  if (!root) return [];
  const path = el => {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    while (el && el !== document.body) {
      if (el.id) { parts.unshift('#' + CSS.escape(el.id)); break; }
      const p = el.parentElement; const i = [...p.children].indexOf(el) + 1;
      parts.unshift(el.tagName.toLowerCase() + ':nth-child(' + i + ')'); el = p;
    }
    return parts.join(' > ');
  };
  const els = [...root.querySelectorAll('button, a[href], [role=button], [data-open-combo], summary')]
    .filter(el => vis(el) && !el.disabled && !el.closest('.bottom-nav, .brandbar .bar-back-btn, .bar-back-btn'))
    .filter(el => !(el.tagName === 'A' && /^https?:|^mailto:|^tel:/.test(el.getAttribute('href') || '')))
    .filter(el => !skip.test((el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '')))
    // Settings toggles (choices, chips, steppers, tabs) never open a new screen: skip for speed.
    .filter(el => !el.matches('[aria-pressed], [aria-checked], [role=tab], [role=radio], [role=switch], .choice, .chip, [class*=stepper], [class*=-opt], [class*=seg]'))
    .filter(el => (el.textContent || '').trim().length > 2 || el.matches('.master-settings-btn, [aria-label]'));
  return els.map(el => ({sel: path(el), text: (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 40)}));
}
"""

BACK_VISIBLE_JS = """() => [...document.querySelectorAll('.bar-back-btn')].some(b => !b.hidden && !b.closest('[hidden]') && b.getClientRects().length > 0)"""

# lange (Fabian 2026-10-06): long press a tile three times in a row, the
# way iOS does it (touch held 600 ms, then the late click on the tile and a
# tap that lands on the sheet that opened under the finger). Every time the
# action sheet must open and the page must stay where it was.
LONGPRESS_JS = r"""
async () => {
  const SEL = '#hubAreaGrid .area-tile, #todayAreaGrid .area-tile, #home .excard[data-exercise], #natExercises .nat-tile, #freeOwnGrid [data-free-id], #freeTrainerGrid [data-free-id], #freeTplGrid [data-free-id]';
  const vis = el => el && !el.closest('[hidden]') && el.getClientRects().length > 0;
  const tile = [...document.querySelectorAll(SEL)].find(vis);
  if (!tile) return null;
  const scr = () => [...document.querySelectorAll('.screen')].filter(vis).map(e => e.id).join('+');
  const before = scr(), sheet = document.getElementById('tileActionSheet'), out = [];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 1; i <= 3; i++) {
    const r = tile.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    const mk = () => new Touch({identifier: i, target: tile, clientX: x, clientY: y});
    tile.dispatchEvent(new TouchEvent('touchstart', {touches: [mk()], changedTouches: [mk()], bubbles: true, cancelable: true}));
    await wait(650);
    tile.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [mk()], bubbles: true, cancelable: true}));
    tile.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
    const under = document.elementFromPoint(x, y);
    if (under) under.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
    await wait(150);
    if (sheet.hidden) out.push('Menü beim ' + i + '. langen Drücken nicht offen');
    if (scr() !== before) { out.push('Seite gewechselt beim ' + i + '. langen Drücken (' + scr() + ')'); break; }
    await wait(400);
    const cancel = sheet.querySelector('[data-tile-act=cancel]');
    if (cancel && !sheet.hidden) cancel.click();
    await wait(150);
  }
  return out;
}
"""

AUDIT_JS = open(os.path.join(HERE, "fabian_blick_audit.js"), encoding="utf-8").read()
# verdeckt (Prüfer 07.10. Nr. 1): an inline form that opens on a tap (name
# field + Abbrechen/Speichern, e.g. "Aktuelle Einstellung speichern") must
# land fully in view, never under a sticky/fixed bar (start bar, bottom bar),
# and leave one filled main button on screen. Opens each such form on the
# current screen, checks it, closes it again.
FORM_OPENERS_JS = r"""() => [...document.querySelectorAll('.screen:not([hidden]) button[id$="SaveBtn"]')]
  .filter(b => b.offsetParent && /speichern/i.test(b.textContent) && b.nextElementSibling && b.nextElementSibling.matches('.custom-exercise-form[hidden]'))
  .map(b => b.id)"""
FORM_CHECK_JS = r"""(id) => {
  const opener = document.getElementById(id), form = opener.nextElementSibling;
  // only links a person can actually see and tap (not inside a collapsed box)
  const o = opener.getBoundingClientRect(), top = document.elementFromPoint(o.left + o.width / 2, o.top + o.height / 2);
  if (!top || !(top === opener || opener.contains(top))) return [];
  opener.click();
  return new Promise(res => setTimeout(() => {
    const out = [];
    if (form.hidden) { res(['Formular öffnet nicht']); return; }
    const vh = window.innerHeight;
    const covers = [...document.querySelectorAll('body *')].filter(e => {
      const p = getComputedStyle(e).position;
      return (p === 'sticky' || p === 'fixed') && !form.contains(e) && !e.contains(form) && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden' && !e.closest('[hidden]');
    }).map(e => [e, e.getBoundingClientRect()]).filter(([e, r]) => r.width > 0 && r.height > 0 && r.top < vh && r.bottom > 0);
    [...form.querySelectorAll('input, button')].filter(el => el.getClientRects().length && !el.hidden).forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.top < 0 || r.bottom > vh) { out.push('Formular-Teil nicht im Bild nach dem Öffnen: ' + (el.textContent.trim() || el.placeholder || el.id).slice(0, 24)); return; }
      const hit = covers.find(([e, q]) => q.top < r.bottom - 2 && q.bottom > r.top + 2 && q.left < r.right && q.right > r.left);
      if (hit) out.push('Formular-Teil unter ' + (hit[0].id ? '#' + hit[0].id : '.' + String(hit[0].className).split(' ')[0]) + ': ' + (el.textContent.trim() || el.placeholder || el.id).slice(0, 24));
    });
    const prim = [...document.querySelectorAll('.screen:not([hidden]) .start-btn:not(.secondary)')].filter(b => {
      if (!b.getClientRects().length || b.closest('[hidden]') || getComputedStyle(b).visibility === 'hidden') return false;
      const r = b.getBoundingClientRect(); return r.bottom > 0 && r.top < vh;
    });
    if (prim.length > 1) out.push(prim.length + ' gefüllte Hauptknöpfe bei offenem Formular: ' + prim.map(b => b.textContent.trim().slice(0, 18)).join(' / '));
    const cancel = [...form.querySelectorAll('button')].find(b => /Abbrechen/.test(b.textContent));
    if (cancel) cancel.click();
    res(out);
  }, 450));
}"""


def key_of(state):
    if state["sheet"]:
        return "sheet:" + state["sheet"]  # the same sheet over any screen is one state
    parts = [state["screen"]]
    # Screens shared by several exercises/programmes are told apart by their title.
    if re.fullmatch(r"ready|programIntro|\w*ProgramIntro|\w*BundleOverview|bundleOverview", state["screen"] or ""):
        parts = [f'{state["screen"]}[{state["title"]}]']
    if state["player"]:
        parts.append("player:" + state["player"])
    return " / ".join(p for p in parts if p)


# (history.back() and SWIPE_JS keep the plain pg.evaluate: they act, and a retry would act twice.)
async def ev(pg, js, arg=None):
    """pg.evaluate that survives a page navigation in flight (08.10.: under
    full-suite load a click's navigation could land between click and
    evaluate - "Execution context was destroyed" - and crash the whole walk).
    Waits for the new document and evaluates again, at most twice."""
    for attempt in range(3):
        try:
            return await (pg.evaluate(js) if arg is None else pg.evaluate(js, arg))
        except Exception as e:
            if attempt == 2 or "Execution context was destroyed" not in str(e):
                raise
            try:
                await pg.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass
            await pg.wait_for_timeout(300)


async def new_page(b, w, h, scheme):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme,
                              service_workers="block", device_scale_factor=1)
    await ctx.add_init_script(INIT)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "favicon" not in m.text else None)
    return ctx, pg, errs


async def replay(pg, entry, clicks, slow=False):
    """Open the entry point and replay a click path. Returns False (and
    remembers the failing selector in pg.last_fail) if a click fails."""
    if entry.startswith("nav:"):
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(250)
        try:  # under suite load a click can miss its window: retry once, then skip
            for attempt in (0, 1):
                try:
                    if entry == "nav:gear":
                        await pg.click("#todayHome .master-settings-btn", timeout=3000 + attempt * 5000)
                    else:
                        await pg.click(f'#bottomNav [data-nav="{entry[4:]}"]', timeout=3000 + attempt * 5000)
                    break
                except Exception:
                    if attempt:
                        raise
        except Exception:
            pg.last_fail = entry
            return False
    else:
        await pg.goto(BASE + "?bereich=" + entry)
    await pg.wait_for_timeout(250)
    for sel in clicks:
        try:
            await pg.click(sel, timeout=8000 if slow else 2500)
        except Exception:
            pg.last_fail = sel
            return False
        await pg.wait_for_timeout(180)
    return True


async def discover(b):
    """Breadth-first walk; returns {state key: (entry, clicks, label)} for screens and players."""
    ctx, pg, _ = await new_page(b, 390, 844, "light")
    states, starts = {}, {}
    queue = []
    for e in ENTRIES + ["nav:training", "nav:progress", "nav:more", "nav:gear"]:
        if not await replay(pg, e, []):
            continue
        st = await ev(pg, STATE_JS)
        k = key_of(st)
        if k and k not in states:
            states[k] = (e, [], e)
            queue.append((e, [], 0))
    while queue:
        entry, clicks, depth = queue.pop(0)
        if depth >= MAX_DEPTH:
            continue
        if not await replay(pg, entry, clicks):
            continue
        base_state = await ev(pg, STATE_JS)
        # Remember how to start the exercise from this screen (player audit).
        if not base_state["player"] and not base_state["sheet"]:
            sb = await ev(pg, """() => { const vis = el => el.getBoundingClientRect().width > 0 && !el.closest('[hidden]');
              const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden && vis(e));
              let b = s && [...s.querySelectorAll('button')].find(x => vis(x) && !x.disabled && x.textContent.trim() === 'Training starten');
              if (!b) return null; if (b.id) return '#' + CSS.escape(b.id);
              const parts = []; let el = b;
              while (el && el !== document.body) { if (el.id) { parts.unshift('#' + CSS.escape(el.id)); break; }
                const p = el.parentElement; parts.unshift(el.tagName.toLowerCase() + ':nth-child(' + ([...p.children].indexOf(el) + 1) + ')'); el = p; }
              return parts.join(' > '); }""")
            if sb and key_of(base_state) not in starts:
                starts[key_of(base_state)] = (entry, clicks + [sb])
        cands = await ev(pg, CANDIDATES_JS, SKIP_TEXT.pattern)
        dirty = False
        for c in cands:
            if dirty:
                if not await replay(pg, entry, clicks):
                    break
                dirty = False
            try:
                await pg.click(c["sel"], timeout=1500)
            except Exception:
                continue
            await pg.wait_for_timeout(160)
            st = await ev(pg, STATE_JS)
            if st == base_state:
                continue
            dirty = True
            k = key_of(st)
            if not k or k in states:
                continue
            states[k] = (entry, clicks + [c["sel"]], c["text"])
            print(f"  + {k}  ({entry} › {c['text']})", flush=True)
            if not st["player"]:
                queue.append((entry, clicks + [c["sel"]], depth + 1))
    await ctx.close()
    return states, starts


SCROLL_JS = r"""
async () => {
  const out = [];
  const vis = el => el && !el.closest('[hidden]') && el.getBoundingClientRect().width > 0;
  const sheets = [...document.querySelectorAll('.sheet')].filter(vis);
  // the sheet on top: highest z-index, then the later one in the page
  // (Datenschutz opens over Grundeinstellungen with z-index 61)
  const z = el => parseInt(getComputedStyle(el).zIndex, 10) || 0;
  sheets.sort((a, b2) => z(a) - z(b2));
  const layer = sheets[sheets.length - 1] || [...document.querySelectorAll('.screen')].find(vis);
  if (!layer) return out;
  const scrollers = [document.scrollingElement, ...layer.querySelectorAll('*')].filter(e => {
    if (e === document.scrollingElement) return !sheets.length;
    const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 4; });
  const frame = () => new Promise(r => requestAnimationFrame(() => r(true)));
  for (const sc of scrollers.slice(0, 3)) {
    sc.scrollTop = sc.scrollHeight; await frame(); await new Promise(r => setTimeout(r, 120));
    sc.scrollTop = 0; sc.scrollTop = -50; await frame(); await new Promise(r => setTimeout(r, 120));
  }
  // Still alive? A frame must come within a second, and the first visible
  // control must be the element hit at its centre (no invisible layer on top).
  const alive = await Promise.race([frame(), new Promise(r => setTimeout(() => r(false), 1000))]);
  if (!alive) out.push({cat: 'eingefroren', msg: 'Seite reagiert nach Scrollen an Anfang/Ende nicht mehr', el: ''});
  const ctrls = [...layer.querySelectorAll('button, a[href], input, select')].filter(e => {
    const r = e.getBoundingClientRect(); return vis(e) && r.top >= 0 && r.bottom <= innerHeight && getComputedStyle(e).visibility !== 'hidden'; });
  for (const c of ctrls.slice(0, 12)) {
    const r = c.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    // a visible control on top (sticky start bar) is layout, not a frozen page
    if (hit && !c.contains(hit) && !hit.contains(c) && !hit.closest('.bottom-nav, .brandbar, .start-sticky-bar, button, a, input, label, select')) {
      const d = hit.tagName.toLowerCase() + (hit.id ? '#' + hit.id : '') + (typeof hit.className === 'string' && hit.className ? '.' + hit.className.split(' ')[0] : '');
      out.push({cat: 'eingefroren', msg: 'Knopf nach Scrollen nicht antippbar, verdeckt von ' + d,
                el: c.tagName.toLowerCase() + (c.id ? '#' + c.id : '') + ' "' + (c.textContent || '').trim().slice(0, 24) + '"'});
    }
  }
  return out;
}
"""


async def scroll_check(pg):
    """Scroll every scroll area to its end and back to the top (also past it),
    then check the page still reacts (Fabian 2026-10-05: Grundeinstellungen
    froze after scrolling to the top)."""
    try:
        return await asyncio.wait_for(ev(pg, SCROLL_JS), timeout=8)
    except Exception as e:
        return [{"cat": "eingefroren", "msg": "Seite hängt nach Scrollen (" + type(e).__name__ + ")", "el": ""}]


JUMP_INIT = """
(() => { window.__fbW = innerWidth; const w0 = () => window.__fbW0 || innerWidth;
  const f = () => { const w = Math.max(innerWidth, document.documentElement.scrollWidth);
    if (window.__fbW0 && w > window.__fbW0 + 1) window.__fbBad = Math.max(window.__fbBad || 0, w);
    requestAnimationFrame(f); };
  addEventListener('DOMContentLoaded', () => { window.__fbW0 = innerWidth; requestAnimationFrame(f); });
  localStorage.setItem('fwmc-test-transitions', 'true'); })();
"""
JUMP_RECT_JS = """() => { const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden && e.getClientRects().length);
  const h = s && (s.querySelector('h1, .page-title, h2') || s); if (!h) return null;
  const r = h.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.width), innerWidth]; }"""
SWIPE_JS = """async () => { const el = document.elementFromPoint(8, innerHeight / 2) || document.body;
  const mk = x => new Touch({identifier: 1, target: el, clientX: x, clientY: innerHeight / 2});
  el.dispatchEvent(new TouchEvent('touchstart', {touches: [mk(8)], changedTouches: [mk(8)], bubbles: true}));
  for (let i = 1; i <= 8; i++) { el.dispatchEvent(new TouchEvent('touchmove', {touches: [mk(8 + i * 30)], changedTouches: [mk(8 + i * 30)], bubbles: true}));
    await new Promise(r => requestAnimationFrame(r)); }
  el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [mk(248)], bubbles: true})); }"""


async def jump_pass(b, states):
    """sprung: replay every page on a phone with the iOS transitions on and
    watch the layout width (a wider page = the phone zooms out, then snaps
    back) and the title position after the page has arrived."""
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                              service_workers="block")
    await ctx.add_init_script(INIT); await ctx.add_init_script(JUMP_INIT)
    pg = await ctx.new_page()
    out = []
    async def bad():
        return await ev(pg, "window.__fbBad || 0")
    for k, (entry, clicks, _) in states.items():
        if k.startswith("sheet:") or "player:" in k:
            continue
        if not await replay(pg, entry, clicks):
            continue
        await pg.wait_for_timeout(450)
        r1 = await ev(pg, JUMP_RECT_JS)
        await pg.wait_for_timeout(400)
        r2 = await ev(pg, JUMP_RECT_JS)
        w = await bad()
        if w:
            out.append({"cat": "sprung", "state": k, "el": "", "msg": f"Seite beim Hereinschieben breiter als das Handy ({w} px), springt danach zurück"})
        elif r1 and r2 and (abs(r1[0] - r2[0]) > 3 or abs(r1[1] - r2[1]) > 3):
            out.append({"cat": "sprung", "state": k, "el": "", "msg": "Seite verschiebt/vergrößert sich nach dem Hereinschieben"})
        if not await ev(pg, BACK_VISIBLE_JS):
            continue
        await ev(pg, "window.__fbBad = 0")
        await pg.evaluate(SWIPE_JS); await pg.wait_for_timeout(600)
        w = await bad()
        if w:
            out.append({"cat": "sprung", "state": k, "el": "", "msg": f"Zurückwischen macht die Seite breiter als das Handy ({w} px)"})
    await ctx.close()
    for f in out:
        f["cfg"] = "handy-uebergang"
    return out


async def audit_config(b, cfg, states, starts):
    name, w, h, scheme = cfg
    ctx, pg, errs = await new_page(b, w, h, scheme)
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    findings, infos = [], {}
    items = [(k, v[0], v[1], False) for k, v in states.items()] + \
            [(f"start:{scr}", v[0], v[1], True) for scr, v in starts.items()]
    for k, entry, clicks, is_start in items:
        # 12 configs run in parallel; se-hell does extra checks and gets the
        # least CPU. A missed click under that load is retried once slowly
        # before it counts (09.10.: 55 false "nicht nachspielbar" in se-hell,
        # 0 when se-hell ran alone).
        if not await replay(pg, entry, clicks) and not await replay(pg, entry, clicks, slow=True):
            findings.append({"cat": "rundgang", "state": k, "msg": "Weg nicht nachspielbar", "el": getattr(pg, "last_fail", "")})
            continue
        if is_start:
            await pg.wait_for_timeout(1800)
        await pg.mouse.move(0, 0)  # no :hover left on the last clicked button
        st = await ev(pg, STATE_JS)
        if is_start and not st["player"]:
            continue  # starts a sheet/confirm instead; covered elsewhere
        res = await ev(pg, AUDIT_JS, {"isStart": is_start})
        if not is_start:
            res["findings"] += await scroll_check(pg)
        infos[k] = res["info"]
        for f in res["findings"]:
            f["state"] = k if not is_start else f"player:{st['player']}"
            findings.append(f)
        fn = re.sub(r"[^A-Za-z0-9_.-]+", "_", k)[:80] + ".png"
        try:
            await pg.screenshot(path=os.path.join(OUT, name, fn), full_page=not is_start)
        except Exception:
            pass
        if cfg == CONFIGS[0] and not is_start and not st["sheet"] and not st["player"]:
            lp = await ev(pg, LONGPRESS_JS)
            for m in lp or []:
                findings.append({"cat": "lange", "state": k, "el": "", "msg": m})
            if lp is not None and not await replay(pg, entry, clicks):
                continue
        if cfg == CONFIGS[0] and not is_start and not st["sheet"] and not st["player"]:
            for fid in await ev(pg, FORM_OPENERS_JS):
                await ev(pg, f"() => document.getElementById('{fid}').scrollIntoView({{block: 'end'}})")
                await pg.wait_for_timeout(120)
                for m in await ev(pg, FORM_CHECK_JS, fid):
                    findings.append({"cat": "verdeckt", "state": k, "el": "#" + fid, "msg": m})
        # zurueck (Fabian 2026-10-06): wherever a ‹ is visible, swiping back
        # (Safari edge swipe = browser back, Android back) must go back too.
        if cfg == CONFIGS[0] and not is_start and not st["sheet"] and not st["player"] and await ev(pg, BACK_VISIBLE_JS):
            await pg.evaluate("history.back()"); await pg.wait_for_timeout(350)
            after = await ev(pg, STATE_JS)
            if "localhost" not in pg.url or after["screen"] == st["screen"] or not after["screen"]:
                findings.append({"cat": "zurueck", "state": k, "el": "",
                                 "msg": "‹ sichtbar, aber Zurückwischen/Zurück-Taste bleibt auf der Seite oder verlässt die App"})
    await ctx.close()
    for e in errs:
        findings.append({"cat": "fehler", "state": "-", "msg": e[:160], "el": ""})
    for f in findings:
        f["cfg"] = name
    return findings, infos


def cross_screen(infos_by_cfg):
    """stil + kopf across screens: the same kind of element must look the same."""
    out = []
    for cfg, infos in infos_by_cfg.items():
        groups = {}
        for state, info in infos.items():
            for kind, sig in info.get("styles", []):
                groups.setdefault(kind, {}).setdefault(sig, []).append(state)
        for kind, sigs in groups.items():
            if len(sigs) < 2:
                continue
            main = max(sigs, key=lambda s: len(sigs[s]))
            for sig, where in sigs.items():
                if sig == main:
                    continue
                for st in sorted(set(where)):
                    out.append({"cat": "stil", "state": st, "cfg": cfg, "el": kind,
                                "msg": f"{kind} sieht anders aus als sonst: {sig} (üblich: {main})"})
    return out


NUM = re.compile(r"\d+(\.\d+)?")


def fkey(f):
    # Stable key without the config so a finding in all configs counts once.
    msg = NUM.sub("#", f["msg"])[:120]
    el = f.get("el", "")
    if f["cat"] in ("taste", "druck", "dunkel"):
        el = re.sub(r' ".*', "", el)  # same kind of control = one finding, whatever its label
        # randomised shape classes (Test-Bereich "Suchen" draws circles or squares at random)
        el = re.sub(r"\.shape-[\w-]+", ".shape-*", el)
        if f["cat"] == "dunkel":
            msg = re.sub(r"\(#.*", "", msg)
            # an element with an id is the same element whatever transient state
            # class it has at that moment (e.g. #vorlaufDot .armed while waiting)
            el = re.sub(r"^([\w-]+#[\w-]+\.[\w-]+)(\.[\w-]+)+", r"\1", el)
    return f"{f['cat']}|{f['state']}|{el}|{msg}"


def write_report(findings, states, starts, new_keys, secs):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(findings, fh, ensure_ascii=False, indent=1)
    by = {}
    for f in findings:
        by.setdefault(fkey(f), []).append(f)
    lines = [f"# Fabian-Blick Bericht", "",
             f"{len(states)} Zustände (Seiten, Fenster), {len(starts)} Übungsstarts, "
             f"{len(CONFIGS)} Ansichten ({', '.join(c[0] for c in CONFIGS)}), {int(secs)} s.", "",
             f"{len(by)} verschiedene Befunde, davon {len(new_keys)} neu (nicht in der Baseline).", ""]
    cats = {}
    for k, fs in by.items():
        cats.setdefault(fs[0]["cat"], []).append((k, fs))
    for cat in sorted(cats):
        lines += [f"## {cat} ({len(cats[cat])})", ""]
        for k, fs in sorted(cats[cat], key=lambda x: x[0]):
            f = fs[0]
            cfgs = ",".join(sorted({x["cfg"] for x in fs}))
            mark = "**NEU** " if k in new_keys else ""
            lines.append(f"- {mark}`{f['state']}` {f['msg']} {('· ' + f['el']) if f.get('el') else ''} [{cfgs}]")
        lines.append("")
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


async def main():
    t0 = time.time()
    import shutil
    shutil.rmtree(OUT, ignore_errors=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        states, starts = await discover(b)
        print(f"Gefunden: {len(states)} Zustände, {len(starts)} Übungsstarts ({int(time.time() - t0)} s)")
        results, jumps = await asyncio.gather(asyncio.gather(*[audit_config(b, c, states, starts) for c in CONFIGS]),
                                              jump_pass(b, states))
        await b.close()
    findings = [f for r in results for f in r[0]] + jumps
    findings += cross_screen({c[0]: r[1] for c, r in zip(CONFIGS, results)})
    keys = sorted({fkey(f) for f in findings})
    base = []
    if os.path.exists(BASELINE):
        base = json.load(open(BASELINE, encoding="utf-8"))
    new_keys = [k for k in keys if k not in set(base)]
    if QUICK:
        new_keys = [k for k in new_keys if not k.startswith("stil|")]
    write_report(findings, states, starts, set(new_keys), time.time() - t0)
    if UPDATE:
        with open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump(keys, fh, ensure_ascii=False, indent=0)
        print("Baseline neu geschrieben:", len(keys))
        new_keys = []
    fixed = [k for k in base if k not in set(keys)]
    print(f"Befunde gesamt: {len(keys)}, neu: {len(new_keys)}, behoben (aus Baseline verschwunden): {len(fixed)}")
    for k in new_keys[:60]:
        print("  NEU", k)
    print("Bericht:", os.path.join(OUT, "report.md"))
    print("Keine neuen Befunde:", not new_keys)

asyncio.run(main())
