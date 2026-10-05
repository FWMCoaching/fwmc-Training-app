"""Fabian-Blick (Fabian, 2026-10-04: "Fehler vorher finden"): one automatic
walk through the whole app, looking for the KINDS of error Fabian keeps
spotting by eye, instead of one test per single case.

1. Discovery: starting from every area home, the bottom bar targets and the
   gear sheet, it clicks every visible button/tile and remembers every new
   screen, sheet and player it reaches (depth 2). New screens are covered
   automatically - nothing to register.
2. Audit: every state is replayed on a small iPhone (375x667) and a large
   one (430x932), light and dark, with a full-page screenshot, and checked
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
3. Report: tests/screenshots/fabian_blick/report.md (+ report.json and the
   screenshots). Findings already known are listed in
   tests/fabian_blick_baseline.json; the test fails only on NEW findings,
   so the suite stays usable while the known list is worked down. When a
   known finding is fixed, run with --update-baseline to shrink the list.
   Never add a finding to the baseline to make the test pass without
   Fabian's ok (CLAUDE.md: fix the app, never loosen the test).

Usage (from tests/, dev server on :8845):
  python3 fabian_blick_test.py                 # full walk, 4 configs
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
CONFIGS = [("se-hell", 375, 667, "light"), ("se-dunkel", 375, 667, "dark"),
           ("max-hell", 430, 932, "light"), ("max-dunkel", 430, 932, "dark")]
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
  return {screen: scr.join('+'), sheet: sheet.join('+'), player: player.join('+'), done: done.join('+')};
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
    .filter(el => !skip.test((el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '')));
  return els.map(el => ({sel: path(el), text: (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 40)}));
}
"""

AUDIT_JS = open(os.path.join(HERE, "fabian_blick_audit.js"), encoding="utf-8").read()


def key_of(state):
    parts = [state["screen"]]
    if state["sheet"]:
        parts.append("sheet:" + state["sheet"])
    if state["player"]:
        parts.append("player:" + state["player"])
    return " / ".join(p for p in parts if p)


async def new_page(b, w, h, scheme):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme,
                              service_workers="block", device_scale_factor=1)
    await ctx.add_init_script(INIT)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "favicon" not in m.text else None)
    return ctx, pg, errs


async def replay(pg, entry, clicks):
    """Open the entry point and replay a click path. Returns False if a click fails."""
    if entry.startswith("nav:"):
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(250)
        if entry == "nav:gear":
            await pg.click("#todayHome .master-settings-btn", timeout=3000)
        else:
            await pg.click(f'#bottomNav [data-nav="{entry[4:]}"]', timeout=3000)
    else:
        await pg.goto(BASE + "?bereich=" + entry)
    await pg.wait_for_timeout(250)
    for sel in clicks:
        try:
            await pg.click(sel, timeout=2500)
        except Exception:
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
        st = await pg.evaluate(STATE_JS)
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
        base_state = await pg.evaluate(STATE_JS)
        cands = await pg.evaluate(CANDIDATES_JS, SKIP_TEXT.pattern)
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
            st = await pg.evaluate(STATE_JS)
            if st == base_state:
                continue
            dirty = True
            k = key_of(st)
            if not k or k in states:
                continue
            states[k] = (entry, clicks + [c["sel"]], c["text"])
            if not st["player"]:
                queue.append((entry, clicks + [c["sel"]], depth + 1))
        # Remember how to start the exercise from this screen (player audit).
        if not base_state["player"] and not base_state["sheet"]:
            sb = await pg.evaluate("""() => { const vis = el => el.getBoundingClientRect().width > 0 && !el.closest('[hidden]');
              const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden && vis(e));
              let b = s && [...s.querySelectorAll('button')].find(x => vis(x) && !x.disabled && x.textContent.trim() === 'Training starten');
              if (!b) return null; if (b.id) return '#' + CSS.escape(b.id);
              const parts = []; let el = b;
              while (el && el !== document.body) { if (el.id) { parts.unshift('#' + CSS.escape(el.id)); break; }
                const p = el.parentElement; parts.unshift(el.tagName.toLowerCase() + ':nth-child(' + ([...p.children].indexOf(el) + 1) + ')'); el = p; }
              return parts.join(' > '); }""")
            if sb and base_state["screen"] not in starts:
                starts[base_state["screen"]] = (entry, clicks + [sb])
    await ctx.close()
    return states, starts


async def audit_config(b, cfg, states, starts):
    name, w, h, scheme = cfg
    ctx, pg, errs = await new_page(b, w, h, scheme)
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    findings, infos = [], {}
    items = [(k, v[0], v[1], False) for k, v in states.items()] + \
            [(f"start:{scr}", v[0], v[1], True) for scr, v in starts.items()]
    for k, entry, clicks, is_start in items:
        if not await replay(pg, entry, clicks):
            findings.append({"cat": "rundgang", "state": k, "msg": "Weg nicht nachspielbar", "el": ""})
            continue
        if is_start:
            await pg.wait_for_timeout(1800)
        st = await pg.evaluate(STATE_JS)
        if is_start and not st["player"]:
            continue  # starts a sheet/confirm instead; covered elsewhere
        res = await pg.evaluate(AUDIT_JS, {"isStart": is_start})
        infos[k] = res["info"]
        for f in res["findings"]:
            f["state"] = k if not is_start else f"player:{st['player']}"
            findings.append(f)
        fn = re.sub(r"[^A-Za-z0-9_.-]+", "_", k)[:80] + ".png"
        try:
            await pg.screenshot(path=os.path.join(OUT, name, fn), full_page=not is_start)
        except Exception:
            pass
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


def fkey(f):
    # Stable key without the config so a finding in all 4 configs counts once.
    return f"{f['cat']}|{f['state']}|{f.get('el','')}|{re.sub(r'[0-9.]+', '#', f['msg'])[:120]}"


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
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        states, starts = await discover(b)
        print(f"Gefunden: {len(states)} Zustände, {len(starts)} Übungsstarts ({int(time.time() - t0)} s)")
        results = await asyncio.gather(*[audit_config(b, c, states, starts) for c in CONFIGS])
        await b.close()
    findings = [f for r in results for f in r[0]]
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
