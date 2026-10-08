"""Gleichgewicht · Wörter (VOR, Fabian 08.10.2026).
- "Inhalt": Buchstaben-Stifte (default) / Wörter; Tiere, Alltag, Farbwörter
  (Lies: das Wort / die Farbe); "Wort wechselt" jeden Schlag / 2. / 4.
- The word changes on the beat (every 1st/2nd/4th), silently without Takt,
  never twice the same; Farbwörter never in their own colour.
- Size follows LOOK size and always fits; hint never covered; works with
  the Bewegter Hintergrund; Kombi block carries it, own settings untouched;
  history note; persists; Sakkaden keeps the sticks.
Run from tests/ with a dev server on :8845."""
import asyncio, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-natmodes','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/gleichgewicht_woerter"
INKS = {"ROT": "#d32f2f", "BLAU": "#1f5fbf", "GRÜN": "#2e7d32", "GELB": "#f2c200", "LILA": "#7b3fa0", "SCHWARZ": "#16232a"}

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

def prefs(pg):
    return pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1') || '{}')")

async def open_bal(pg):
    await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(250)

async def stop(pg):
    await pg.evaluate("() => document.getElementById('balanceBackBtn').click()"); await pg.wait_for_timeout(300)
    if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

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
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await open_bal(pg)

        # ---- ready screen ----
        check("Inhalt group, Buchstaben-Stifte default", await pg.is_visible("#balanceContentGroup") and "active" in (await pg.get_attribute('[data-bal-content="stifte"]', "class")))
        check("word box hidden by default", not await pg.is_visible("#balanceWordBox"))
        await pg.click('[data-bal-content="woerter"]'); await pg.wait_for_timeout(80)
        check("Wörter: word box shown, stick groups hidden", await pg.is_visible("#balanceWordBox") and not await pg.is_visible("#balanceSticksGroup") and not await pg.is_visible("#balanceLettersGroup"))
        check("Wörter: Tiere + jeden Schlag default", "active" in (await pg.get_attribute('[data-bal-wordlist="tiere"]', "class")) and "active" in (await pg.get_attribute('[data-bal-wordevery="1"]', "class")))
        check("Lies row only for Farbwörter", not await pg.is_visible("#balanceWordReadBox"))
        check("look label says Wörter", "Größe der Wörter" in await pg.inner_text('#balanceReady [data-look-size="balance"]'))
        await pg.click("#balanceAdvanced summary"); await pg.wait_for_timeout(80)
        check("Feineinstellungen: stick colours/length hidden, Schriftgröße stays",
              not await pg.is_visible("#balanceColor1Picker") and not await pg.is_visible("#balanceLengthSlider") and await pg.is_visible("#balanceFontSlider"))
        await pg.click('[data-bal-wordlist="farben"]'); await pg.click('[data-bal-wordread="farbe"]'); await pg.click('[data-bal-wordevery="2"]'); await pg.wait_for_timeout(80)
        check("Farbwörter: Lies row + help", await pg.is_visible("#balanceWordReadBox") and "Sag laut die Farbe" in await pg.inner_text("#balanceWordHelp"))
        await pg.locator("#balanceContentGroup").scroll_into_view_if_needed()
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/ready_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        await pg.reload(); await pg.wait_for_timeout(500)
        pr = await prefs(pg)
        check("persists across reload", pr.get("content") == "woerter" and pr.get("wordList") == "farben" and pr.get("wordRead") == "farbe" and pr.get("wordEvery") == 2, pr)
        await open_bal(pg)
        check("reload: ready shows Wörter", "active" in (await pg.get_attribute('[data-bal-content="woerter"]', "class")))
        # Sakkaden keeps the sticks
        await pg.click('[data-bal-mode="sakk"]'); await pg.wait_for_timeout(80)
        check("Sakkaden: Inhalt hidden, sticks shown", not await pg.is_visible("#balanceContentGroup") and await pg.is_visible("#balanceSticksGroup"))
        await pg.click('[data-bal-mode="nein"]'); await pg.wait_for_timeout(80)

        # ---- run: changes every 2nd beat, Farbwort ink ----
        await pg.evaluate("() => { const s = document.getElementById('balanceBpmSlider'); s.value = 200; s.dispatchEvent(new Event('input')); }")
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(300)
        seen = []
        prev = None
        for _ in range(40):
            w = await pg.evaluate("() => window.__balWord()")
            if w["word"] and (not prev or w["count"] != prev["count"]): seen.append(w)
            prev = w
            await pg.wait_for_timeout(60)
        w = await pg.evaluate("() => window.__balWord()")
        check("run: word shown, sticks hidden", w["content"] == "woerter" and not w["hidden"] and not await pg.is_visible("#balanceStick0"), w)
        expect = 1 + max(0, (w["beats"] - 1) // 2)
        check("word changes every 2nd beat", abs(w["count"] - expect) <= 1 and w["beats"] >= 4, (w["count"], w["beats"]))
        check("Farbwort never in its own colour", all(INKS[s["word"]["text"]] != s["word"]["ink"] for s in seen), [(s["word"]["text"], s["word"]["ink"]) for s in seen])
        check("never the same word+ink twice in a row", all((a["word"]["text"], a["word"]["ink"]) != (c["word"]["text"], c["word"]["ink"]) for a, c in zip(seen, seen[1:])))
        cap = await pg.get_attribute("#balanceWord", "data-cap")
        check("caption says Sag die Farbe", cap == "Sag die Farbe", cap)
        geo = await pg.evaluate("""() => { const w = document.getElementById('balanceWord').getBoundingClientRect(), s = document.getElementById('balanceStage').getBoundingClientRect(), h = document.getElementById('balanceHint').getBoundingClientRect();
            return { inside: w.left >= s.left && w.right <= s.right, belowHint: w.top >= h.bottom, fs: parseFloat(getComputedStyle(document.getElementById('balanceWord')).fontSize) }; }""")
        check("word inside the stage, below the hint", geo["inside"] and geo["belowHint"], geo)
        for scheme in ("light", "dark"):
            await pg.emulate_media(color_scheme=scheme); await pg.wait_for_timeout(120)
            await pg.screenshot(path=f"{SHOTS}/run_farbwort_{scheme}.png")
        await pg.emulate_media(color_scheme="light")
        # live size: bigger, still fits
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => { const s = document.querySelector('#balancePauseOverlay [data-live-look] input'); s.value = 2; s.dispatchEvent(new Event('input')); }")
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(200)
        geo2 = await pg.evaluate("""() => { const w = document.getElementById('balanceWord').getBoundingClientRect(), s = document.getElementById('balanceStage').getBoundingClientRect();
            return { inside: w.left >= s.left - 0.5 && w.right <= s.right + 0.5, fs: parseFloat(getComputedStyle(document.getElementById('balanceWord')).fontSize) }; }""")
        check("size 2×: bigger and still inside", geo2["fs"] > geo["fs"] and geo2["inside"], (geo["fs"], geo2))
        await stop(pg)

        # ---- without Takt: silent rhythm; Tiere; with moving background; history ----
        await pg.evaluate("() => { const p = JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1')); Object.assign(p, { metro: false, bpm: 200, wordList: 'tiere', wordEvery: 1, timing: 'timed', sets: 1, setS: 10, size: 1, mbg: { pattern: 'punkte' } }); localStorage.setItem('fwmc-balance-prefs-v1', JSON.stringify(p)); }")
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await open_bal(pg)
        check("help explains the silent rhythm", "Ohne Takt" in await pg.inner_text("#balanceWordHelp"))
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(1500)
        w = await pg.evaluate("() => window.__balWord()")
        check("no Takt: words still change, no beats", w["count"] >= 3 and w["beats"] == 0, w)
        check("Tiere: plain dark ink", w["word"]["ink"] == "#16232a" and (await pg.get_attribute("#balanceWord", "data-cap")) == "Lies laut")
        mb = await pg.evaluate("() => window.__mbg('balance')")
        check("moving background runs behind the word", mb["running"] and mb["st"]["pattern"] == "punkte", mb["running"])
        top = await pg.evaluate("""() => { const w = document.getElementById('balanceWord'), c = document.querySelector('#balanceStage > canvas.mbg-canvas'); const r = w.getBoundingClientRect();
            w.style.pointerEvents = 'auto'; const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); w.style.pointerEvents = ''; return h === w && h !== c; }""")
        check("word paints above the background", top)
        await pg.screenshot(path=f"{SHOTS}/run_tiere_punkte.png")
        for _ in range(120):
            if await pg.is_visible("#balanceDonePanel"): break
            await pg.wait_for_timeout(100)
        h = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]').filter(e => e.kind === 'balance')")
        check("history note names the words", h and "Wörter (Tiere)" in (h[0].get("note") or "") or (h and "Wörter (Tiere)" in (h[-1].get("note") or "")), [e.get("note") for e in h])

        # ---- Kombi: block with words, own settings stay ----
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.evaluate("() => { const p = JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1')); p.content = 'stifte'; p.metro = true; p.mbg = { pattern: 'aus' }; localStorage.setItem('fwmc-balance-prefs-v1', JSON.stringify(p)); }")
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.evaluate("() => document.querySelector('[data-open-combo]').click()"); await pg.wait_for_timeout(200)
        await pg.locator('#comboAddGrid .combo-add-btn:has-text("Gleichgewicht")').click(); await pg.wait_for_timeout(200)
        await pg.click('[data-bal-content="woerter"]'); await pg.click('[data-bal-wordlist="alltag"]'); await pg.wait_for_timeout(60)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(200)
        check("Kombi capture: own content stays Stifte", (await prefs(pg)).get("content") == "stifte")
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(900)
        w = await pg.evaluate("() => window.__balWord()")
        check("Kombi block plays words (Alltag)", w and w["content"] == "woerter" and w["word"] and w["word"]["text"] in ["Tisch", "Stuhl", "Tasse", "Brot", "Schuh", "Jacke", "Uhr", "Lampe", "Buch", "Stift", "Glas", "Teller", "Löffel", "Gabel", "Bett", "Tür", "Fenster", "Auto", "Rad", "Ball", "Brief", "Handy", "Kissen", "Schal"], w)
        await stop(pg)
        check("after the Kombi: own content still Stifte", (await prefs(pg)).get("content") == "stifte")
        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print(f"\n{sum(results)}/{len(results)} passed")
    if not all(results): raise SystemExit(1)

asyncio.run(main())
