import asyncio, json, os
from playwright.async_api import async_playwright

# Farbbrille (Rot-Grün-Brille, 2026-10-08): shared settings in the
# Grundeinstellungen (only with the Test-Bereich unlocked), the mandatory
# calibration #anaglyphCalib, the pre-start brightness hint, the lock on
# every Farbbrille start until calibrated, and the Test exercise
# "Jedes Auge zählt" (dots per eye, result per eye).

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "farbbrille")
os.makedirs(SHOTS, exist_ok=True)

results = []
def check(name, ok):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}")

def hex_to_rgb(h):
    h = h.lstrip("#")
    return f"rgb({int(h[0:2],16)}, {int(h[2:4],16)}, {int(h[4:6],16)})"

SEED = """
localStorage.setItem('fwmc-test-unlocked', 'true');
if (!localStorage.getItem('fwmc-master-v1')) localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));
"""

async def new_page(b, errors, scheme="light", width=390, height=844, seed=SEED):
    ctx = await b.new_context(viewport={"width": width, "height": height}, service_workers="block", color_scheme=scheme)
    pg = await ctx.new_page()
    if seed:
        await pg.add_init_script(seed)
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg

async def open_ready(pg):
    await pg.goto(URL); await pg.wait_for_timeout(300)
    if await pg.is_visible("#tipsCloseBtn"):
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
    await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
    await pg.click("#eyecountOpenBtn"); await pg.wait_for_timeout(200)

async def ls(pg, key):
    return await pg.evaluate(f"JSON.parse(localStorage.getItem('{key}') || 'null')")

async def dot_info(pg):
    return await pg.evaluate("""() => {
      const d = document.getElementById('eyecountDot');
      if (!d || d.hidden) return null;
      const r = d.getBoundingClientRect();
      const bar = document.getElementById('eyecountPlayerBar').getBoundingClientRect();
      const hint = document.getElementById('eyecountHint').getBoundingClientRect();
      return { eye: d.dataset.eye, bg: getComputedStyle(d).backgroundColor, x: r.left + r.width/2, y: r.top + r.height/2,
               top: r.top, bottom: r.bottom, w: r.width, barBottom: bar.bottom, hintBottom: hint.bottom, vh: innerHeight, vw: innerWidth, right: r.right, left: r.left };
    }""")

async def set_range(pg, sel, value):
    await pg.evaluate("([s, v]) => { const el = document.querySelector(s); el.value = String(v); el.dispatchEvent(new Event('input', {bubbles:true})); }", [sel, value])

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---------- A: Grundeinstellungen group only when Test-Bereich unlocked ----------
        ctx0, pg0 = await new_page(b, errors, seed="localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
        await pg0.goto(URL); await pg0.wait_for_timeout(300)
        check("A1 Farbbrille group hidden while Test-Bereich locked", await pg0.evaluate("document.getElementById('masterAnaglyphGroup').hidden === true"))
        await ctx0.close()

        ctx, pg = await new_page(b, errors)
        await open_ready(pg)

        # ---------- B: lock before calibration ----------
        check("B1 ready screen visible", await pg.is_visible("#eyecountReady"))
        check("B2 Hilfsmittel note from HILFSMITTEL map", (await pg.text_content("#eyecountHilfsmittel .hilfsmittel-text")) == "Du brauchst eine Rot-Grün-Brille.")
        check("B3 Hilfsmittel shop link hidden while link is empty", not await pg.is_visible("#eyecountHilfsmittel .hilfsmittel-link"))
        check("B4 lock box visible", await pg.is_visible("#eyecountLock"))
        check("B5 lock text", "Erst die Farbbrille abgleichen" in (await pg.text_content("#eyecountLock")))
        check("B6 start button looks locked", await pg.evaluate("document.getElementById('eyecountReadyStartBtn').classList.contains('is-locked') && document.getElementById('eyecountReadyStartBtn').getAttribute('aria-disabled') === 'true'"))
        check("B7 start label stays 'Training starten'", (await pg.text_content("#eyecountReadyStartBtn")).strip() == "Training starten")
        await pg.screenshot(path=f"{SHOTS}/ready_locked_390_light.png", full_page=True)
        await pg.click("#eyecountReadyStartBtn", force=True); await pg.wait_for_timeout(200)
        check("B8 locked start opens the calibration, no run", await pg.is_visible("#anaglyphCalib") and not await pg.is_visible("#eyecountPlayer"))
        await pg.click("#anaglyphCalibCloseBtn"); await pg.wait_for_timeout(150)
        check("B9 closing calibration without Fertig keeps the lock", await pg.is_visible("#eyecountLock") and (await ls(pg, "fwmc-anaglyph-v1")) is None)

        # ---------- C: calibration flow ----------
        await pg.click("#eyecountLock [data-anaglyph-calib]"); await pg.wait_for_timeout(200)
        check("C1 calibration step 1 (Brille)", (await pg.text_content("#anaglyphCalibStepEl")) == "Schritt 1 von 4" and (await pg.text_content("#anaglyphCalibTitle")) == "Brille aufsetzen")
        check("C2 calibration background is black", (await pg.evaluate("getComputedStyle(document.getElementById('anaglyphCalib')).backgroundColor")) == "rgb(0, 0, 0)")
        await pg.screenshot(path=f"{SHOTS}/calib_1_brille_390.png")
        await pg.click("#anaglyphCalibNextBtn"); await pg.wait_for_timeout(150)
        check("C3 step 2 Rot ausblenden", (await pg.text_content("#anaglyphCalibTitle")) == "Rot ausblenden")
        txt = await pg.text_content("#anaglyphCalibText")
        check("C4 red step: close the left eye (red lens left), look through green with the right", "linke Auge zu" in txt and "rechten Auge" in txt)
        thumb = await pg.evaluate("(() => { const s = document.getElementById('anaglyphCalibV'); return s.getBoundingClientRect().height; })()")
        check("C5 slider is at least 44 px high", thumb >= 44)
        await set_range(pg, "#anaglyphCalibV", 70)
        await pg.click('#anaglyphCalib [data-calib-nudge="h:-1"]'); await pg.wait_for_timeout(100)
        red_sq = await pg.evaluate("getComputedStyle(document.getElementById('anaglyphCalibSquare')).backgroundColor")
        check("C6 red square follows the sliders", red_sq != "rgb(255, 0, 0)")
        await pg.screenshot(path=f"{SHOTS}/calib_2_rot_390.png")
        await pg.click("#anaglyphCalibNextBtn"); await pg.wait_for_timeout(150)
        check("C7 step 3 Grün ausblenden", (await pg.text_content("#anaglyphCalibTitle")) == "Grün ausblenden")
        txt = await pg.text_content("#anaglyphCalibText")
        check("C8 green step: close the right eye, look with the left", "rechte Auge zu" in txt and "linken Auge" in txt)
        await set_range(pg, "#anaglyphCalibV", 80)
        green_sq = await pg.evaluate("getComputedStyle(document.getElementById('anaglyphCalibSquare')).backgroundColor")
        check("C9 green square follows the slider", green_sq == "rgb(0, 204, 0)")
        await pg.screenshot(path=f"{SHOTS}/calib_3_gruen_390.png")
        await pg.click("#anaglyphCalibNextBtn"); await pg.wait_for_timeout(150)
        check("C10 step 4 Probe with Neu abgleichen + Fertig", (await pg.text_content("#anaglyphCalibTitle")) == "Probe"
              and (await pg.text_content("#anaglyphCalibPrevBtn")) == "Neu abgleichen" and (await pg.text_content("#anaglyphCalibNextBtn")) == "Fertig")
        wl = await pg.evaluate("getComputedStyle(document.getElementById('anaglyphCalibWordL')).color")
        wr = await pg.evaluate("getComputedStyle(document.getElementById('anaglyphCalibWordR')).color")
        check("C11 'Links' in the calibrated red, 'Rechts' in the calibrated green", wl == red_sq and wr == green_sq)
        await pg.screenshot(path=f"{SHOTS}/calib_4_probe_390.png")
        await pg.click("#anaglyphCalibNextBtn"); await pg.wait_for_timeout(200)
        saved = await ls(pg, "fwmc-anaglyph-v1")
        check("C12 calibration saved (calibrated, left rot, colours)", saved and saved["calibrated"] is True and saved["left"] == "rot"
              and hex_to_rgb(saved["red"]) == red_sq and hex_to_rgb(saved["green"]) == green_sq and saved["redCal"] == {"v": 70, "h": -1})
        check("C13 calibration closed, back on the ready screen", not await pg.is_visible("#anaglyphCalib") and await pg.is_visible("#eyecountReady"))
        check("C14 lock gone, start button normal", not await pg.is_visible("#eyecountLock") and not await pg.evaluate("document.getElementById('eyecountReadyStartBtn').classList.contains('is-locked')"))
        await pg.screenshot(path=f"{SHOTS}/ready_390_light.png", full_page=True)
        RED, GREEN = red_sq, green_sq

        # ---------- D: hint sheet before start, run 1 (natural end, 1 Min, tap only left-eye dots) ----------
        await pg.click('#eyecountLengthRow [data-eyecount-length="1"]')
        await pg.click('#eyecountTempoRow [data-eyecount-tempo="leicht"]')
        await pg.click("#eyecountReadyStartBtn"); await pg.wait_for_timeout(200)
        check("D1 brightness / Night Shift / True Tone hint before start", await pg.is_visible("#anaglyphHintSheet")
              and "Night Shift" in (await pg.text_content("#anaglyphHintSheet")) and not await pg.is_visible("#eyecountPlayer"))
        await pg.screenshot(path=f"{SHOTS}/hint_sheet_390.png")
        await pg.click("#anaglyphHintOkBtn"); await pg.wait_for_timeout(300)
        check("D2 'Erledigt' starts the run", await pg.is_visible("#eyecountPlayer") and await pg.is_visible("#eyecountCross"))
        check("D3 stage is black", (await pg.evaluate("getComputedStyle(document.getElementById('eyecountStage')).backgroundColor")) == "rgb(0, 0, 0)")
        taps = 0; seen = {"left": 0, "right": 0}; colors_ok = True; under_bar = False; out_of_stage = False; shot = False
        last_eye_key = None
        t_end = asyncio.get_event_loop().time() + 66
        while asyncio.get_event_loop().time() < t_end:
            if await pg.is_visible("#eyecountDonePanel"):
                break
            d = await dot_info(pg)
            if d:
                key = (round(d["x"]), round(d["y"]), d["eye"])
                if key != last_eye_key:
                    last_eye_key = key
                    seen[d["eye"]] += 1
                    exp = RED if d["eye"] == "left" else GREEN
                    if d["bg"] != exp: colors_ok = False
                    if d["top"] < max(d["barBottom"], d["hintBottom"]): under_bar = True
                    if d["left"] < 0 or d["right"] > d["vw"] or d["bottom"] > d["vh"]: out_of_stage = True
                    if not shot:
                        await pg.screenshot(path=f"{SHOTS}/running_390.png"); shot = True
                    if d["eye"] == "left":
                        await pg.mouse.click(d["x"], d["y"]); taps += 1
                        await pg.wait_for_timeout(60)
            await pg.wait_for_timeout(90)
        await pg.wait_for_timeout(500)
        check("D4 dots of both eyes appeared", seen["left"] > 3 and seen["right"] > 3)
        check("D5 left-eye dots red, right-eye dots green (left lens = Rot)", colors_ok)
        check("D6 no dot under the player bar / hint", not under_bar)
        check("D7 no dot outside the stage", not out_of_stage)
        check("D8 natural end shows the done panel with check mark", await pg.is_visible("#eyecountDonePanel") and await pg.is_visible("#eyecountDonePanel .done-check"))
        lines = await pg.evaluate("[...document.querySelectorAll('#eyecountEyes .eyecount-eye-line')].map(p => p.textContent)")
        print("   result lines:", lines, "taps:", taps)
        check("D9 left eye line counts the taps", len(lines) == 2 and lines[0].startswith(f"Linkes Auge: {taps} von ") and "Ø " in lines[0] and " s" in lines[0])
        check("D10 right eye got 0 (not tapped)", lines[1].startswith("Rechtes Auge: 0 von ") and lines[1].endswith("Ø –"))
        note = await pg.evaluate("[...document.querySelectorAll('#eyecountEyes .eyecount-eye-note')].map(p => p.textContent).join(' | ')")
        check("D11 neutral sentence names the weaker eye, refers to the trainer", "Dein rechtes Auge hat weniger Punkte erwischt" in note and "deinem Trainer" in note)
        hist = await ls(pg, "fwmc-history-v1") or await pg.evaluate("(() => { for (const k of Object.keys(localStorage)) if (k.includes('history')) { try { const l = JSON.parse(localStorage.getItem(k)); if (Array.isArray(l) && l[0] && l[0].kind) return l; } catch(e){} } return null; })()")
        check("D12 history entry kind eyecount, not aborted", bool(hist) and hist[0]["kind"] == "eyecount" and not hist[0].get("aborted"))
        await pg.screenshot(path=f"{SHOTS}/result_390_light.png")

        # ---------- E: again -> hint again -> 'Nicht mehr anzeigen' -> Beenden after 12 s = aborted ----------
        await pg.click("#eyecountAgainBtn"); await pg.wait_for_timeout(200)
        check("E1 hint appears again before 'Nochmal'", await pg.is_visible("#anaglyphHintSheet"))
        await pg.click("#anaglyphHintOffBtn"); await pg.wait_for_timeout(300)
        check("E2 'Nicht mehr anzeigen' starts and stores hintOff", await pg.is_visible("#eyecountStage") and not await pg.is_visible("#eyecountDonePanel") and (await ls(pg, "fwmc-anaglyph-v1"))["hintOff"] is True)
        await pg.wait_for_timeout(12000)
        await pg.click("#eyecountBackBtn"); await pg.wait_for_timeout(300)
        check("E3 early Beenden = aborted result without check mark", await pg.is_visible("#eyecountDonePanel") and not await pg.is_visible("#eyecountDonePanel .done-check")
              and (await pg.text_content("#eyecountDoneSummary")).startswith("Abgebrochen · "))
        hist = await pg.evaluate("(() => { for (const k of Object.keys(localStorage)) if (k.includes('history')) { try { const l = JSON.parse(localStorage.getItem(k)); if (Array.isArray(l) && l[0] && l[0].kind) return l; } catch(e){} } return null; })()")
        check("E4 aborted history entry", hist[0]["kind"] == "eyecount" and hist[0].get("aborted") is True and hist[0].get("note") == "abgebrochen")
        await pg.click("#eyecountDoneBackBtn"); await pg.wait_for_timeout(200)

        # ---------- F: Grundeinstellungen: swap side, persistence ----------
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(250)
        check("F1 Farbbrille group visible with Test-Bereich unlocked", await pg.is_visible("#masterAnaglyphGroup"))
        check("F2 status says calibrated", (await pg.text_content("#masterAnaglyphStatus")).startswith("Abgeglichen am "))
        check("F3 hint checkbox off after 'Nicht mehr anzeigen'", not await pg.is_checked("#masterAnaglyphHintCheck"))
        check("F4 calibrate button reads 'Neu abgleichen'", (await pg.text_content("#masterAnaglyphCalibBtn")) == "Neu abgleichen")
        await pg.click('#masterAnaglyphSideRow [data-anaglyph-left="gruen"]'); await pg.wait_for_timeout(100)
        await pg.evaluate("document.getElementById('masterAnaglyphGroup').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=f"{SHOTS}/grundeinstellungen_390_light.png")
        await pg.reload(); await pg.wait_for_timeout(400)
        saved = await ls(pg, "fwmc-anaglyph-v1")
        check("F5 side swap persisted, colours kept", saved["left"] == "gruen" and hex_to_rgb(saved["red"]) == RED and saved["calibrated"] is True)

        # ---------- G: mapping flips with the swapped side, no hint any more ----------
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
        await pg.click("#eyecountOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#eyecountReadyStartBtn"); await pg.wait_for_timeout(300)
        check("G1 no hint sheet after 'Nicht mehr anzeigen'", not await pg.is_visible("#anaglyphHintSheet") and await pg.is_visible("#eyecountStage"))
        flips_ok = True; n = 0; left_hits = 0; last = None
        t_end = asyncio.get_event_loop().time() + 9
        while asyncio.get_event_loop().time() < t_end:
            d = await dot_info(pg)
            if d and (round(d["x"]), round(d["y"])) != last:
                last = (round(d["x"]), round(d["y"]))
                n += 1
                exp = GREEN if d["eye"] == "left" else RED
                if d["bg"] != exp: flips_ok = False
            await pg.wait_for_timeout(100)
        check("G2 with green lens left: left-eye dots green, right-eye dots red", n >= 2 and flips_ok)
        status = await pg.text_content("#eyecountProgressEl")
        check("G3 status shows hits and time", "Treffer" in status and ":" in status)
        await pg.click("#eyecountBackBtn"); await pg.wait_for_timeout(300)
        check("G4 Beenden before 10 s returns to the Test home", await pg.is_visible("#testHome") and not await pg.is_visible("#eyecountPlayer"))
        await ctx.close()

        # ---------- H: screenshots dark mode + iPad ----------
        cal = json.dumps({"left": "rot", "red": "#b30003", "green": "#00cc00", "calibrated": True, "hintOff": True,
                          "redCal": {"v": 70, "h": -1}, "greenCal": {"v": 80, "h": 0}, "calibratedAt": "2026-10-08T10:00:00Z"})
        seed_cal = SEED + f"if (!localStorage.getItem('fwmc-anaglyph-v1')) localStorage.setItem('fwmc-anaglyph-v1', {json.dumps(cal)});"
        ctxd, pgd = await new_page(b, errors, scheme="dark", seed=seed_cal)
        await open_ready(pgd)
        await pgd.screenshot(path=f"{SHOTS}/ready_390_dark.png", full_page=True)
        await pgd.evaluate("localStorage.setItem('fwmc-anaglyph-v1', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('fwmc-anaglyph-v1')), {calibrated:false})))")
        await open_ready(pgd)
        check("H0 lock comes back when not calibrated", await pgd.is_visible("#eyecountLock"))
        await pgd.screenshot(path=f"{SHOTS}/ready_locked_390_dark.png", full_page=True)
        await pgd.click("#eyecountReadyBackToHome"); await pgd.wait_for_timeout(150)
        await pgd.click("#testHome .master-settings-btn"); await pgd.wait_for_timeout(250)
        await pgd.evaluate("document.getElementById('masterAnaglyphGroup').scrollIntoView({block:'center'})"); await pgd.wait_for_timeout(150)
        await pgd.screenshot(path=f"{SHOTS}/grundeinstellungen_390_dark.png")
        await pgd.click("#masterAnaglyphCalibBtn"); await pgd.wait_for_timeout(200)
        check("H1 calibration opens above the Grundeinstellungen", await pgd.is_visible("#anaglyphCalib"))
        await pgd.click("#anaglyphCalibNextBtn"); await pgd.wait_for_timeout(150)
        await pgd.screenshot(path=f"{SHOTS}/calib_2_rot_390_dark.png")
        await pgd.click("#anaglyphCalibCloseBtn"); await pgd.wait_for_timeout(150)
        check("H2 closing returns to the open Grundeinstellungen", await pgd.is_visible("#masterSettingsSheet"))
        await ctxd.close()

        ctxi, pgi = await new_page(b, errors, width=1024, height=768, seed=seed_cal)
        await open_ready(pgi)
        await pgi.click("#eyecountReadyStartBtn"); await pgi.wait_for_timeout(300)
        under = False
        for _ in range(40):
            d = await dot_info(pgi)
            if d:
                if d["top"] < max(d["barBottom"], d["hintBottom"]): under = True
                break
            await pgi.wait_for_timeout(100)
        await pgi.screenshot(path=f"{SHOTS}/running_1024.png")
        check("H3 iPad 1024: dot below the bar", not under and d is not None)
        await ctxi.close()

        await b.close()

    errs = [e for e in errors if "favicon" not in e]
    check("Z no pageerror / console error", not errs)
    if errs: print("\n".join(errs[:10]))
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed: print("FAILED:", failed)

asyncio.run(main())
