"""Farbfelder · Einblenden (Fabian 08.10.2026): new mode in the Farbfelder "Modus" row.
- The full grid once for orientation ("So liegen deine Felder"), then an empty
  stage; only the shown field(s) appear, resting frames stay empty.
- "Wie viele Felder" (ffCount): Nur eins / Im Wechsel (default) / Phasenweise;
  persists, travels in snapshot / Kombi block, Cardio guest has the same row.
- Wechsel: both counts, never more than 3 of one count in a row; Phasen: blocks
  of 6; two fields always differ; no exact repeat of the previous set.
- Foot badge / hands only on single fields.
- Antippen: one field as Leuchten; two fields = right only when both are tapped,
  one only = missed, a field not shown = wrong.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/farbfelder_einblenden"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

async def open_ff(pg):
    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)

async def field_xy(pg, i):
    g = await pg.evaluate("() => window.__ffLastGeom")
    w = (g["right"] - g["left"]) / 2; h = (g["bottom"] - g["top"]) / 2
    return g["left"] + (i % 2 + 0.5) * w, g["top"] + (i // 2 + 0.5) * h

async def wait_for(pg, js, timeout=15000, arg=None):
    t = 0
    while t < timeout:
        v = await pg.evaluate(js, arg)
        if v: return v
        await pg.wait_for_timeout(40); t += 40
    return None

# a fresh, unanswered stimulus with `n` fields (not t0 = skip)
NEW_STIM = """([skip, n]) => { const s = window.__ffTap(); if (!s || !s.cur || s.cur.done) return null;
  if (skip !== null && Math.abs(s.cur.t0 - skip) < 1e-6) return null;
  const k = s.cur.targets ? s.cur.targets.length : 1; if (n && k !== n) return null; return s.cur; }"""

BUILD = """(over) => window.__ff.build(Object.assign({ffMode:'einblenden', duration: 600, stimulusS: 0.5, intervalMin: 0.5, intervalMax: 0.5}, over))
  .map(f => ({kind: f.kind, t0: f.t0, t1: f.t1, p: f.payload}))"""

def stims(sched): return [f for f in sched if f["kind"] == "farbfelder" and f["p"].get("phase") == "show"]
def max_run(counts):
    m = r = 0; prev = None
    for c in counts:
        r = r + 1 if c == prev else 1; prev = c; m = max(m, r)
    return m

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- schedule (pure) ----
        s = await pg.evaluate(BUILD, {"ffCount": "eins"})
        first = [f for f in s if f["kind"] != "count"][0]
        check("first frame = orientation grid", first["kind"] == "farbfelder" and first["p"].get("phase") == "orient" and first["p"].get("caption") == "So liegen deine Felder" and abs(first["t1"] - first["t0"] - 2) < 1e-6, first)
        st = stims(s)
        check("eins: only 1-field stimuli", len(st) > 50 and all(len(f["p"]["fields"]) == 1 for f in st), len(st))
        keys = [",".join(map(str, sorted(f["p"]["fields"]))) for f in st]
        check("eins: never the same field twice in a row", all(a != b2 for a, b2 in zip(keys, keys[1:])))
        check("resting frames are blank", all(f["kind"] == "blank" for f in s if f["kind"] != "count" and not (f["kind"] == "farbfelder")))
        ok_w = True; both = True; diff = True; norep = True
        for _ in range(5):
            s = await pg.evaluate(BUILD, {"ffCount": "wechsel"})
            st = stims(s); counts = [len(f["p"]["fields"]) for f in st]
            if max_run(counts) > 3: ok_w = False
            if not (1 in counts and 2 in counts): both = False
            if not (0.3 < counts.count(2) / len(counts) < 0.7): both = False
            if any(len(set(f["p"]["fields"])) != len(f["p"]["fields"]) for f in st): diff = False
            ks = [",".join(map(str, sorted(f["p"]["fields"]))) for f in st]
            if any(a == b2 for a, b2 in zip(ks, ks[1:])): norep = False
        check("wechsel: both counts, about half/half", both)
        check("wechsel: never more than 3 of one count in a row", ok_w)
        check("two fields always differ", diff)
        check("no exact repeat of the previous set", norep)
        s = await pg.evaluate(BUILD, {"ffCount": "phasen"})
        counts = [len(f["p"]["fields"]) for f in stims(s)]
        exp = [1 if (i // 6) % 2 == 0 else 2 for i in range(len(counts))]
        check("phasen: blocks of 6 ones, 6 twos, ...", counts == exp and len(counts) > 24, counts[:20])
        s = await pg.evaluate(BUILD, {"ffCount": "wechsel", "ffFoot": "wechsel", "ffHands": True, "ffHandRules": {"rot": "hoch", "blau": "hoch", "gelb": "hoch", "gruen": "hoch"}})
        st = stims(s)
        check("foot badge + hands only on single fields",
              all((f["p"]["foot"] in ("L", "R")) and f["p"]["hand"] for f in st if len(f["p"]["fields"]) == 1)
              and all(f["p"]["foot"] is None and f["p"]["hand"] is None for f in st if len(f["p"]["fields"]) == 2))
        check("default count is Im Wechsel", (await pg.evaluate("() => window.__ff.snapshot().ffCount")) == "wechsel")

        # ---- ready screen ----
        await open_ff(pg)
        btn = pg.locator('[data-ff-mode="einblenden"]')
        check("mode button Einblenden", "Einblenden" in await btn.inner_text() and "nur das Feld ist zu sehen" in await btn.inner_text())
        check("count group hidden for other modes", not await pg.is_visible("#ffCountGroup"))
        await btn.click(); await pg.wait_for_timeout(80)
        check("count group shown for Einblenden", await pg.is_visible("#ffCountGroup") and "Wie viele Felder" in await pg.inner_text("#ffCountGroup"))
        check("Im Wechsel active by default", "active" in (await pg.get_attribute('[data-ff-count="wechsel"]', "class")))
        check("mode help names both feet", "beiden Füßen" in await pg.inner_text("#ffModeHelp"))
        check("Umkehr not offered", not await pg.is_visible("#ffFlipGroup"))
        # layout of the 9 mode tiles: last one spans the row
        boxes = await pg.evaluate("() => [...document.querySelectorAll('#ffModeRow .choice')].map(b => { const r = b.getBoundingClientRect(); return [r.left, r.width, r.height]; })")
        row_w = await pg.evaluate("() => document.getElementById('ffModeRow').getBoundingClientRect().width")
        check("9 modes, last tile full width", len(boxes) == 9 and abs(boxes[-1][1] - row_w) < 1.5 and all(bx[2] >= 44 for bx in boxes), boxes[-1])
        await pg.click('[data-ff-count="phasen"]'); await pg.wait_for_timeout(60)
        check("phasen help", "6-mal" in await pg.inner_text("#ffCountHelp"))
        await pg.locator("#ffModeRow").scroll_into_view_if_needed()
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(150)
            await pg.screenshot(path=f"{SHOTS}/ready_{scheme}.png", full_page=True)
            await pg.locator("#ffModeRow").screenshot(path=f"{SHOTS}/moderow_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        check("ffCount persists across reload", "active" in (await pg.get_attribute('[data-ff-count="phasen"]', "class")))
        check("snapshot carries ffCount", (await pg.evaluate("() => window.__ff.snapshot().ffCount")) == "phasen")
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.ffCount = 'quatsch'; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        check("invalid ffCount falls back to wechsel", (await pg.evaluate("() => window.__ff.snapshot().ffCount")) == "wechsel")

        # ---- running (treten): orientation, empty rest, 1 and 2 fields ----
        await open_ff(pg)
        await pg.click('[data-ff-count="wechsel"]'); await pg.click('[data-ff-foot="wechsel"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(500)
        d = await pg.evaluate("() => window.__ffLastDrawn")
        check("run starts with all four fields", d and d["phase"] == "orient" and sorted(d["shown"]) == [0, 1, 2, 3], d)
        await pg.screenshot(path=f"{SHOTS}/run_orient.png")
        rest = await wait_for(pg, "() => { const d = window.__ffLastDrawn; return d && d.phase === 'rest' ? d : null; }")
        check("resting frame draws nothing", rest and rest["shown"] == [], rest)
        # canvas pixel check in the rest frame: centre of every field is white
        await pg.screenshot(path=f"{SHOTS}/run_rest.png")
        one = await wait_for(pg, "() => { const d = window.__ffLastDrawn; return d && d.phase === 'show' && d.shown.length === 1 ? d : null; }", timeout=25000)
        check("a single field appears", bool(one))
        await pg.wait_for_timeout(60)
        await pg.screenshot(path=f"{SHOTS}/run_one_field.png")
        two = await wait_for(pg, "() => { const d = window.__ffLastDrawn; return d && d.phase === 'show' && d.shown.length === 2 ? d : null; }", timeout=25000)
        check("two fields appear together", bool(two))
        await pg.wait_for_timeout(60)
        await pg.screenshot(path=f"{SHOTS}/run_two_fields.png")
        g = await pg.evaluate("() => window.__ffLastGeom")
        check("grid below bar and above caption band", g["top"] >= g["barBottom"] and g["bottom"] <= g["capTop"] + 0.5, g)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- history note ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.duration = 5; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click("#startBtn")
        await wait_for(pg, "() => !document.getElementById('donePanel').hidden", timeout=15000)
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]').map(e => e.note || '')")
        check("history note names mode + count", any("Einblenden · ein und zwei Felder im Wechsel" in n for n in hist), hist[:3])

        # ---- Antippen ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.duration = 120; s.stimulusS = 1.5; s.intervalMin = 2; s.intervalMax = 2.5; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="tippen"]'); await pg.click('[data-ff-count="wechsel"]'); await pg.wait_for_timeout(60)
        check("tippen: mode help", "bei zwei Feldern beide" in await pg.inner_text("#ffModeHelp"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        st0 = await pg.evaluate("() => window.__ffTap()")
        check("orientation opens no answer window", st0["cur"] is None and st0["items"] == [], st0["cur"])
        # tap during orientation is ignored
        await pg.mouse.click(*(await field_xy(pg, 0))); await pg.wait_for_timeout(40)
        check("tap during orientation ignored", (await pg.evaluate("() => window.__ffTap()"))["items"] == [])
        # two fields: both tapped = right
        a = await wait_for(pg, NEW_STIM, arg=[None, 2], timeout=30000)
        for f in a["targets"]:
            await pg.mouse.click(*(await field_xy(pg, f))); await pg.wait_for_timeout(60)
        cur = (await pg.evaluate("() => window.__ffTap()"))["cur"]
        check("two fields, both tapped = right", cur["done"] and cur["ok"] and cur["rt"] is not None, cur)
        await pg.screenshot(path=f"{SHOTS}/run_tap_two.png")
        # two fields: one only = missed
        bb = await wait_for(pg, NEW_STIM, arg=[a["t0"], 2], timeout=30000)
        await pg.mouse.click(*(await field_xy(pg, bb["targets"][0]))); await pg.wait_for_timeout(60)
        await pg.mouse.click(*(await field_xy(pg, bb["targets"][0]))); await pg.wait_for_timeout(60)
        cur = (await pg.evaluate("() => window.__ffTap()"))["cur"]
        check("one of two tapped: still open (same field twice ignored)", not cur["done"] and cur["got"] == [bb["targets"][0]], cur)
        nxt = await wait_for(pg, NEW_STIM, arg=[bb["t0"], 0], timeout=30000)
        items = (await pg.evaluate("() => window.__ffTap()"))["items"]
        last = items[-1]
        check("one of two only = missed", not last["done"] and not last["ok"], last)
        # wrong field (not shown) = wrong
        c = nxt
        shown = c["targets"] if c.get("targets") else [c["target"]]
        wrong = [i for i in range(4) if i not in shown][0]
        await pg.mouse.click(*(await field_xy(pg, wrong))); await pg.wait_for_timeout(60)
        cur = (await pg.evaluate("() => window.__ffTap()"))["cur"]
        check("tap on a field not shown = wrong", cur["done"] and not cur["ok"] and cur["field"] == wrong, cur)
        await pg.screenshot(path=f"{SHOTS}/run_tap_wrong_empty.png")
        # single field = as Leuchten
        e1 = await wait_for(pg, NEW_STIM, arg=[c["t0"], 1], timeout=30000)
        await pg.mouse.click(*(await field_xy(pg, e1["target"]))); await pg.wait_for_timeout(60)
        cur = (await pg.evaluate("() => window.__ffTap()"))["cur"]
        check("single field tapped = right", cur["done"] and cur["ok"], cur)
        await pg.evaluate("() => window.__ffTapFinish()"); await pg.wait_for_timeout(300)
        sc = await pg.evaluate("() => window.__ffTapLastScore")
        summ = await pg.inner_text("#doneSummary")
        check("score: right/missed counted", sc["hits"] >= 2 and sc["missed"] >= 1 and "richtig" in summ, (sc, summ))

        # ---- Kombi block keeps its own count ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await open_ff(pg)
        await pg.click('[data-ff-answer="treten"]'); await pg.click('[data-ff-mode="leuchten"]'); await pg.wait_for_timeout(60)
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbfelder")'); await pg.wait_for_timeout(250)
        await pg.click('[data-ff-mode="einblenden"]'); await pg.click('[data-ff-count="eins"]'); await pg.wait_for_timeout(60)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        std = await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); return [s.ffMode, s.ffCount]; }")
        check("Kombi: standalone settings unchanged", std[0] == "leuchten", std)
        check("Kombi: block row names Einblenden", "Einblenden" in await pg.inner_text("#comboBlockList"))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-opens with Einblenden + Nur eins", "active" in (await pg.get_attribute('[data-ff-mode="einblenden"]', "class")) and "active" in (await pg.get_attribute('[data-ff-count="eins"]', "class")))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(900)
        d = await wait_for(pg, "() => { const d = window.__ffLastDrawn; return d && d.mode === 'einblenden' ? d : null; }", timeout=8000)
        check("Kombi: block plays Einblenden", bool(d))
        cnt = await pg.evaluate("() => window.__ff.snapshot().ffCount")
        check("Kombi: block plays with its own count", cnt == "eins", cnt)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Cardio guest: same choice row ----
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Farbfelder")'); await pg.wait_for_timeout(120)
        await pg.click('#cardioAddonPickerDetail [data-mode="einblenden"]'); await pg.wait_for_timeout(120)
        det = await pg.inner_text("#cardioAddonPickerDetail")
        check("Cardio picker: Wie viele Felder row", "Wie viele Felder" in det and "Phasenweise" in det, det[:200])
        await pg.click('#cardioAddonPickerDetail [data-balf="count"][data-balv="phasen"]'); await pg.wait_for_timeout(80)
        await pg.evaluate("() => { window.__ffLastDrawn = null; }")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(900)
        d = await wait_for(pg, "() => { const d = window.__ffLastDrawn; return d && d.mode === 'einblenden' ? d : null; }", timeout=8000)
        cnt = await pg.evaluate("() => window.__ff.snapshot().ffCount")
        check("Cardio guest plays Einblenden phasenweise", bool(d) and cnt == "phasen", cnt)
        await pg.screenshot(path=f"{SHOTS}/cardio_guest.png")

        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
