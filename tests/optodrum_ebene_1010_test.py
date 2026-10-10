"""Ebenen-Umschalter "Übung | Hintergrund" (Fabian 10.10.2026) for every exercise with the
Optodrum as moving background (MOVING_BG: Gleichgewicht, Positionen merken, Flash-Speicher-Test,
Objektverfolgung (MOT), Schulte-Tabelle).
- The switch shows only while the pattern runs (not with "Aus"), hidden in the pause sheet,
  every start begins on "Übung".
- "Hintergrund": swipe = direction, two fingers = width (10-160 px), taps never count as
  answers, the exercise's own pinch (Größe) and stick drag do nothing; a toast names the value.
- "Übung": taps count again.
- "Speichern" (standalone only) writes direction/width to that exercise's prefs and survives a
  reload; the pause sheet shows the live values; a Kombi block has no "Speichern" and never
  changes the client's own settings.
- The first switches to "Hintergrund" show a hint (fwmc-mbg-ebene-hint-v1, test flag fwmc-test-mbghint).
Screenshots: screenshots/optodrum_ebene/. Run from tests/ with a dev server on :8845."""
import json, os
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html"
CH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/optodrum_ebene"
KINDS = ["balance", "remember", "flash", "mot", "schulte"]
STAGE = {"balance": "#balanceStage", "remember": "#rememberStage", "flash": "#flashStage", "mot": "#motStage", "schulte": "#schulteStage"}
ok = True

def check(name, cond, extra=""):
    global ok
    print(f"{name}: {bool(cond)}" + (f"  ({extra})" if extra and not cond else ""))
    ok = ok and bool(cond)

PINCH = """([sel, f]) => { const s = document.querySelector(sel); const r = s.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const ev = (type, id, x, prim) => s.dispatchEvent(new PointerEvent(type, {pointerId: id, pointerType: 'touch', isPrimary: prim, clientX: x, clientY: cy, bubbles: true}));
  ev('pointerdown', 21, cx - 50, true); ev('pointerdown', 22, cx + 50, false);
  for (let k = 1; k <= 5; k++) { const d = 50 * (1 + (f - 1) * k / 5); ev('pointermove', 21, cx - d, true); ev('pointermove', 22, cx + d, false); }
  ev('pointerup', 22, cx + 50 * f, false); ev('pointerup', 21, cx - 50 * f, true); }"""

def seed(on=True):
    js = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-natmodes','true');"
          "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));localStorage.setItem('fwmc-test-mbghint','1');")
    prefs = {"balance": {}, "remember": {}, "flash": {}, "mot": {"trackS": 2, "highlightS": 1}, "schulte": {}}
    for k, p in prefs.items():
        p = dict(p)
        p["mbg"] = {"pattern": "streifen" if on else "aus", "dir": "links", "size": 40}
        js += f"localStorage.setItem('fwmc-{k}-prefs-v1', {json.dumps(json.dumps(p))});"
    return f"if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded','1'); {js} }}"

def mbg(pg, k):
    return pg.evaluate(f"window.__mbg('{k}')")

def prefs_mbg(pg, k):
    return (pg.evaluate(f"JSON.parse(localStorage.getItem('fwmc-{k}-prefs-v1') || '{{}}')") or {}).get("mbg") or {}

def start(pg, k):
    pg.goto(URL + "?bereich=nat"); pg.wait_for_timeout(450)
    pg.click(f'#natHome .nat-tile[data-nat-ex="{k}"]'); pg.wait_for_timeout(250)
    pg.click(f"#{k}ReadyStartBtn"); pg.wait_for_timeout(500)

def stop(pg, k):
    pg.evaluate(f"() => {{ const b = document.getElementById('{k}BackBtn'); if (b && b.offsetParent) b.click(); }}"); pg.wait_for_timeout(300)
    if pg.is_visible("#confirmSheet"):
        pg.click("#confirmYesBtn"); pg.wait_for_timeout(250)

def bar_sel(k):
    return f"{STAGE[k]} .mbg-ebene-bar"

def swipe(pg, k, dx, dy):
    b = pg.locator(STAGE[k]).bounding_box()
    cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2 - 40
    pg.mouse.move(cx - dx, cy - dy); pg.mouse.down(); pg.mouse.move(cx + dx, cy + dy, steps=5); pg.mouse.up()
    pg.wait_for_timeout(120)

def tap_center(pg, sel):
    b = pg.locator(sel).first.bounding_box()
    pg.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.wait_for_timeout(150)

def wait_for(pg, sel, ms=12000):
    for _ in range(ms // 100):
        if pg.locator(sel).count() and pg.locator(sel).first.is_visible():
            return True
        pg.wait_for_timeout(100)
    return False

def answer_state(pg, k):
    return pg.evaluate("""(k) => {
      if (k === 'remember') return [document.querySelectorAll('.remember-marker.covered').length, document.querySelectorAll('.remember-marker.correct, .remember-marker.wrong').length, document.getElementById('rememberHint').textContent];
      if (k === 'flash') return [...document.querySelectorAll('#flashAnswerBoxes > *')].map(b => b.textContent).join('|');
      if (k === 'mot') return [...document.querySelectorAll('.mot-object')].map(o => o.className).join('|') + document.getElementById('motHint').textContent;
      if (k === 'schulte') return document.getElementById('schulteLevelEl').textContent.split('·')[0] + [...document.querySelectorAll('.schulte-cell')].map(c => c.className).join('|');
      return null; }""", k)

def answer_target(pg, k):
    return {"remember": '.remember-marker.covered[data-num="1"]', "flash": "#flashKeypad button",
            "mot": ".mot-object.tappable", "schulte": None}[k]

os.makedirs(SHOTS, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CH, args=["--no-sandbox"])

    # ---- 1. Pattern "Aus": no switch anywhere ----
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    ctx.add_init_script(seed(on=False))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL + "?bereich=nat"); pg.wait_for_timeout(400)
    check("one switch per MOVING_BG stage", all(pg.locator(bar_sel(k)).count() == 1 for k in KINDS))
    for k in KINDS:
        start(pg, k)
        check(f"{k}: Aus -> no switch, no inset", not pg.is_visible(bar_sel(k)) and not pg.evaluate(f"document.querySelector('{STAGE[k]}').classList.contains('has-mbg-switch')"))
        stop(pg, k)
    check("Aus: no page errors", not errs, errs[:3])
    ctx.close()

    # ---- 2. Pattern on, every exercise, light + dark ----
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
        ctx.add_init_script(seed(on=True))
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for k in KINDS:
            start(pg, k)
            S = STAGE[k]
            check(f"{scheme} {k}: switch visible with the pattern on", pg.is_visible(bar_sel(k)))
            st = mbg(pg, k)
            check(f"{scheme} {k}: starts on Übung", st["ebene"] == "uebung" and pg.get_attribute(f"{S} [data-ebene=uebung]", "aria-pressed") == "true", st["ebene"])
            hb = pg.evaluate(f"""() => {{ const r = [...document.querySelectorAll('{S} .mbg-ebene button')].map(b => b.getBoundingClientRect());
                const s = document.querySelector('{S}').getBoundingClientRect(); return {{ h: Math.min(...r.map(q => q.height)), w: Math.min(...r.map(q => q.width)), bottom: Math.max(...r.map(q => q.bottom)), sb: s.bottom, l: Math.min(...r.map(q => q.left)), rr: Math.max(...r.map(q => q.right)) }}; }}""")
            check(f"{scheme} {k}: segments >= 44 px, at the bottom of the stage, inside", hb["h"] >= 44 and hb["w"] >= 44 and 0 < hb["sb"] - hb["bottom"] <= 20 and hb["l"] >= 0 and hb["rr"] <= 390, hb)
            # Hintergrund
            before = mbg(pg, k)["st"]
            pg.click(f"{S} [data-ebene=bg]"); pg.wait_for_timeout(150)
            if k == "balance":
                check(f"{scheme}: first switch shows the hint", pg.locator(f"{S} .opto-toast:not([hidden])").count() >= 1 and "Wischen" in pg.inner_text(f"{S} .opto-toast:not([hidden])"))
            check(f"{scheme} {k}: Hintergrund active, gesture layer covers the stage", mbg(pg, k)["ebene"] == "bg" and pg.is_visible(f"{S} .mbg-gesture"))
            check(f"{scheme} {k}: no Speichern before a change", not pg.is_visible(f"#{k}MbgSaveBtn"))
            stick0 = pg.evaluate("(() => { const s = document.getElementById('balanceStick0'); return s ? [s.style.left, s.style.top] : null; })()")
            swipe(pg, k, 80, 0)
            st = mbg(pg, k)
            check(f"{scheme} {k}: swipe right -> rechts", st["st"]["dir"] == "rechts", st["st"]["dir"])
            check(f"{scheme} {k}: toast names the direction", "rechts" in pg.inner_text(f"{S} .opto-toast:not([hidden])"))
            swipe(pg, k, 60, -60)
            st = mbg(pg, k)
            check(f"{scheme} {k}: swipe up-right -> schräg ro", st["st"]["dir"] == "schraeg" and st["st"]["diag"] == "ro", st["st"])
            if k == "balance":
                check(f"{scheme}: stick not dragged by the swipe", pg.evaluate("(() => { const s = document.getElementById('balanceStick0'); return [s.style.left, s.style.top]; })()") == stick0)
                size0 = pg.evaluate("window.__balWord().size")
            mpx0 = pg.evaluate("getComputedStyle(document.getElementById('rememberStage')).getPropertyValue('--remember-marker-px')")
            pg.evaluate(PINCH, [f"{S} .mbg-gesture", 2.0]); pg.wait_for_timeout(120)
            st = mbg(pg, k)
            check(f"{scheme} {k}: pinch -> width ~80 px", 70 <= st["st"]["size"] <= 90, st["st"]["size"])
            check(f"{scheme} {k}: toast names the width", "px" in pg.inner_text(f"{S} .opto-toast:not([hidden])"))
            if k == "balance":
                check(f"{scheme}: Gleichgewicht stick size untouched by the pinch", pg.evaluate("window.__balWord().size") == size0)
            if k == "remember":
                check(f"{scheme}: marker size untouched by the pinch", pg.evaluate("getComputedStyle(document.getElementById('rememberStage')).getPropertyValue('--remember-marker-px')") == mpx0)
            pg.evaluate(PINCH, [f"{S} .mbg-gesture", 10.0]); pg.wait_for_timeout(80)
            check(f"{scheme} {k}: width capped at 160", mbg(pg, k)["st"]["size"] == 160)
            pg.evaluate(PINCH, [f"{S} .mbg-gesture", 0.05]); pg.wait_for_timeout(80)
            check(f"{scheme} {k}: width at least 10", mbg(pg, k)["st"]["size"] == 10)
            pg.evaluate(PINCH, [f"{S} .mbg-gesture", 6.0]); pg.wait_for_timeout(80)
            check(f"{scheme} {k}: Speichern next to the switch", pg.is_visible(f"#{k}MbgSaveBtn") and pg.locator(f"{bar_sel(k)} #{k}MbgSaveBtn").count() == 1)
            check(f"{scheme} {k}: not saved yet", prefs_mbg(pg, k).get("dir") == "links")
            pg.wait_for_timeout(1300)
            pg.screenshot(path=f"{SHOTS}/{k}_hintergrund_{scheme}.png")
            # taps never count while on Hintergrund
            if k != "balance":
                tgt = answer_target(pg, k)
                if k == "remember": ready = wait_for(pg, tgt)
                elif k == "flash": ready = wait_for(pg, "#flashInputPanel")
                elif k == "mot": ready = wait_for(pg, tgt)
                else: ready = True; tgt = None
                check(f"{scheme} {k}: answer phase reached", ready)
                if k == "schulte":
                    one = pg.evaluate("""() => { const c = [...document.querySelectorAll('.schulte-cell')].find(c => c.textContent.trim() === '1'); c.id = 'schulteOneCell'; return true; }""")
                    tgt = "#schulteOneCell"
                a0 = answer_state(pg, k)
                tap_center(pg, tgt)
                check(f"{scheme} {k}: tap on Hintergrund does not count", answer_state(pg, k) == a0, (a0, answer_state(pg, k)))
                hit = pg.evaluate(f"""() => {{ const t = document.querySelector('{tgt}'); const r = t.getBoundingClientRect(); const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return h ? h.className : ''; }}""")
                check(f"{scheme} {k}: the gesture layer is on top of the answer", "mbg-gesture" in hit, hit)
                # back to Übung: taps count again
                pg.click(f"{S} [data-ebene=uebung]"); pg.wait_for_timeout(120)
                check(f"{scheme} {k}: Übung hides the layer and Speichern", not pg.is_visible(f"{S} .mbg-gesture") and not pg.is_visible(f"#{k}MbgSaveBtn"))
                if pg.locator(tgt).count():
                    a1 = answer_state(pg, k)
                    tap_center(pg, tgt)
                    check(f"{scheme} {k}: tap on Übung counts again", answer_state(pg, k) != a1, a1)
                else:
                    check(f"{scheme} {k}: answer target still there", False)
                pg.click(f"{S} [data-ebene=bg]"); pg.wait_for_timeout(120)
            else:
                pg.click(f"{S} [data-ebene=uebung]"); pg.wait_for_timeout(120)
                pg.screenshot(path=f"{SHOTS}/{k}_uebung_{scheme}.png")
                stick = pg.locator("#balanceStick0").bounding_box()
                pg.mouse.move(stick["x"] + stick["width"] / 2, stick["y"] + 20); pg.mouse.down(); pg.mouse.move(stick["x"] + stick["width"] / 2 + 60, stick["y"] + 60, steps=5); pg.mouse.up()
                pg.wait_for_timeout(120)
                check(f"{scheme}: Übung: stick drag works again", pg.evaluate("(() => { const s = document.getElementById('balanceStick0'); return [s.style.left, s.style.top]; })()") != stick0)
                check(f"{scheme}: Übung: swipe on the stage leaves the background alone", mbg(pg, k)["st"]["dir"] == "schraeg")
                pg.evaluate(PINCH, [S, 1.5]); pg.wait_for_timeout(120)
                check(f"{scheme}: Übung: pinch resizes the sticks again", pg.evaluate("window.__balWord().size") != size0)
                pg.click(f"{S} [data-ebene=bg]"); pg.wait_for_timeout(120)
            # pause: hidden, live values in the sheet
            live = mbg(pg, k)["st"]
            if pg.is_visible(f"#{k}PauseBtn"):
                pg.click(f"#{k}PauseBtn"); pg.wait_for_timeout(200)
                check(f"{scheme} {k}: switch hidden in the pause", not pg.is_visible(bar_sel(k)) and not pg.is_visible(f"#{k}MbgSaveBtn"))
                pz = f"#{k}PauseOverlay .mbg-pause"
                v = pg.evaluate(f"Number(document.querySelector('{pz} [data-opto-r=size]').value)")
                act = pg.evaluate(f"document.querySelector('{pz} [data-opto-f=dir][data-opto-v=schraeg]').classList.contains('active')")
                check(f"{scheme} {k}: pause sheet shows the live values", act and abs(v - live["size"]) <= 2, (act, v, live["size"]))
                pg.click(f"#{k}ResumeBtn"); pg.wait_for_timeout(200)
                check(f"{scheme} {k}: switch back after Weiter", pg.is_visible(bar_sel(k)))
            # Speichern
            if not pg.is_visible(f"#{k}MbgSaveBtn"):
                swipe(pg, k, 60, -60)
            pg.click(f"#{k}MbgSaveBtn"); pg.wait_for_timeout(150)
            pm = prefs_mbg(pg, k)
            check(f"{scheme} {k}: Speichern writes direction + width", pm.get("dir") == live["dir"] and pm.get("diag") == live["diag"] and pm.get("size") == live["size"] and pm.get("pattern") == "streifen", (pm, live))
            check(f"{scheme} {k}: button says Gespeichert", "Gespeichert" in pg.inner_text(f"#{k}MbgSaveBtn"))
            stop(pg, k)
            check(f"{scheme} {k}: end hides the switch", not pg.is_visible(bar_sel(k)))
            # next start begins on Übung again
            start(pg, k)
            check(f"{scheme} {k}: new start = Übung, saved values used", mbg(pg, k)["ebene"] == "uebung" and mbg(pg, k)["st"]["dir"] == "schraeg" and not pg.is_visible(f"{S} .mbg-gesture"))
            pg.screenshot(path=f"{SHOTS}/{k}_start_{scheme}.png")
            stop(pg, k)
        pg.reload(); pg.wait_for_timeout(500)
        check(f"{scheme}: saved values survive a reload", all(prefs_mbg(pg, k).get("dir") == "schraeg" for k in KINDS), [prefs_mbg(pg, k) for k in KINDS])
        hint_n = pg.evaluate("JSON.parse(localStorage.getItem('fwmc-mbg-ebene-hint-v1') || '0')")
        check(f"{scheme}: hint counted (max 3)", 1 <= hint_n <= 3, hint_n)
        check(f"{scheme}: no page errors", not errs, errs[:3])
        ctx.close()

    # ---- 3. iPad width: switch below the Schulte board, MOT objects above it ----
    ctx = b.new_context(viewport={"width": 1024, "height": 768}, service_workers="block")
    ctx.add_init_script(seed(on=True))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for k in ("schulte", "flash", "balance"):
        start(pg, k)
        pg.wait_for_timeout(300)
        if k == "schulte":
            g = pg.locator("#schulteGrid").bounding_box(); s = pg.locator(bar_sel(k) + " .mbg-ebene").bounding_box()
            check("1024: Schulte board ends above the switch", g["y"] + g["height"] <= s["y"] - 4, (g, s))
        if k == "balance":
            lv = pg.locator("#balanceLive .balance-live-row").bounding_box(); s = pg.locator(bar_sel(k) + " .mbg-ebene").bounding_box()
            check("1024: Gleichgewicht controls above the switch", lv["y"] + lv["height"] <= s["y"] - 4, (lv, s))
        pg.screenshot(path=f"{SHOTS}/{k}_1024.png")
        stop(pg, k)
    check("1024: no page errors", not errs, errs[:3])
    ctx.close()

    # ---- 4. Kombi block: no Speichern, own settings untouched ----
    ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    ctx.add_init_script(seed(on=False))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL + "?bereich=nat"); pg.wait_for_timeout(500)
    pg.click('#natHome .combo-entry-link'); pg.wait_for_timeout(300)
    pg.click('#comboAddGrid >> text="Flash-Speicher-Test · Konstant"'); pg.wait_for_timeout(300)
    pg.click("#flashAdvanced summary"); pg.wait_for_timeout(80)
    pg.click('#flashReady .mbg-group [data-opto-v="streifen"]'); pg.wait_for_timeout(60)
    pg.click("#flashReadyStartBtn"); pg.wait_for_timeout(300)
    pg.click("#comboStartBtn"); pg.wait_for_timeout(900)
    check("Kombi: switch shown in the Flash block", pg.is_visible(bar_sel("flash")) and mbg(pg, "flash")["ebene"] == "uebung")
    pg.click("#flashStage [data-ebene=bg]"); pg.wait_for_timeout(120)
    swipe(pg, "flash", 0, 80)
    pg.evaluate(PINCH, ["#flashStage .mbg-gesture", 2.0]); pg.wait_for_timeout(120)
    st = mbg(pg, "flash")["st"]
    check("Kombi: gestures change this run", st["dir"] == "runter" and st["size"] > 60, st)
    check("Kombi: no Speichern", not pg.is_visible("#flashMbgSaveBtn"))
    pm = prefs_mbg(pg, "flash")
    check("Kombi: own settings untouched", pm.get("pattern") == "aus" and pm.get("dir") == "links" and pm.get("size") == 40, pm)
    pg.screenshot(path=f"{SHOTS}/kombi_flash.png")
    pg.evaluate("() => document.getElementById('flashBackBtn').click()"); pg.wait_for_timeout(300)
    if pg.is_visible("#confirmSheet"): pg.click("#confirmYesBtn"); pg.wait_for_timeout(200)
    check("Kombi: no page errors", not errs, errs[:3])
    ctx.close()
    b.close()

print("ALLE OK" if ok else "FAILED")
