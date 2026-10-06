import asyncio, json
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=nat"

# Gleichgewicht (NAT, Fabian 2026-10-06): letter sticks, modes, letters
# (zufällig / eigene / nur einer), metronome + live tempo/Takt/"Zeit
# anhalten", open-ended run with "Fertig", timed run to its natural end,
# drag + pinch (ctrl+wheel) saved, Kombi-Baustein, Cardio-Zusatzaufgabe,
# and the live "Größe" slider in the pause sheets of every LOOK exercise.

INIT = """
localStorage.setItem('fwmc-tips-seen','true');
localStorage.setItem('fwmc-test-natmodes','true');
localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));
"""

def ok(label, cond, fails):
    print(label + ":", bool(cond))
    if not cond: fails.append(label)

async def prefs(pg):
    return await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1') || '{}')")

async def main():
    errors, fails = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- tile + ready screen ----
        ok("NAT tile 'Gleichgewicht' present", await pg.locator('#natHome .nat-tile[data-nat-ex="balance"]').count() == 1, fails)
        await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(250)
        ok("ready screen open", await pg.is_visible("#balanceReady"), fails)
        ok("five modes", await pg.locator("#balanceModeRow .choice").count() == 5, fails)
        ok("start button reads 'Training starten'", (await pg.inner_text("#balanceReadyStartBtn")).strip() == "Training starten", fails)
        ok("safety note is collapsed (discreet)", await pg.evaluate("() => !document.getElementById('balanceSafety').open"), fails)
        ok("look control 'Größe der Stifte' on the ready screen", await pg.locator('#balanceReady [data-look-size="balance"]').count() == 1, fails)
        await pg.click('[data-bal-mode="sakk"]'); await pg.wait_for_timeout(80)
        ok("Sakkaden switches to 2 sticks", (await prefs(pg)).get("sticks") == 2, fails)
        v2 = await pg.evaluate("() => !!document.getElementById('balanceLetterColor2Picker').offsetParent"); lab = await pg.text_content("#balanceLetterColorLabel")
        print("  stick2:", v2, lab)
        ok("2 sticks: own letter colour for stick 2", v2 and "Stift 1" in lab, fails)
        await pg.evaluate("() => { const bs = [...document.querySelectorAll('#balanceLetterColor2Picker button')]; bs[bs.length - 1].click(); }")
        await pg.wait_for_timeout(60)
        pp = await prefs(pg)
        ok("letter colour stick 2 saved separately", pp.get("letterColor2") and pp.get("letterColor2") != pp.get("letterColor"), fails)
        await pg.click('[data-bal-mode="nein"]'); await pg.click('[data-bal-sticks="1"]'); await pg.wait_for_timeout(60)
        ok("1 stick: stick-2 letter colour hidden", await pg.evaluate("() => !document.getElementById('balanceLetterColor2Group').offsetParent"), fails)
        await pg.click('[data-bal-letters="eigen"]'); await pg.wait_for_timeout(80)
        ok("custom letters field shown", await pg.is_visible("#balanceCustomInput"), fails)
        await pg.fill("#balanceCustomInput", "hxa7")
        await pg.click('[data-bal-timing="open"]'); await pg.wait_for_timeout(80)
        ok("open mode hides set sliders", await pg.is_hidden("#balanceSetSlider"), fails)
        await pg.reload(); await pg.wait_for_timeout(400)
        p0 = await prefs(pg)
        ok("settings survive a reload", p0.get("letters") == "eigen" and p0.get("custom") == "hxa7" and p0.get("timing") == "open", fails)

        # ---- open-ended run: custom letters, beat, live controls ----
        await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(200)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(1800)
        letters = await pg.locator("#balanceStick0 .balance-letter").all_inner_texts()
        ok("own letters on the stick, upper case", letters == ["H", "X", "A", "7"], fails)
        ok("one stick only", await pg.is_hidden("#balanceStick1"), fails)
        clicks = await pg.evaluate("() => window.__balanceClicks || 0")
        ok("metronome ticks at 60/min", clicks >= 1, fails)
        ok("cue shows a direction", (await pg.inner_text("#balanceCue")).strip() in ("◀ links", "rechts ▶"), fails)
        ok("'Fertig' shown in open mode", await pg.is_visible("#balanceFinishBtn"), fails)
        # hint must not sit under the player bar, sticks not under the hint/live row
        geo = await pg.evaluate("""() => { const r = (id) => document.getElementById(id).getBoundingClientRect();
            return { bar: r('balancePlayerBar').bottom, hintTop: r('balanceHint').top, hintBottom: r('balanceHint').bottom, stickTop: r('balanceStick0').top, stickBottom: r('balanceStick0').bottom, live: r('balanceLive').top }; }""")
        ok("hint below the player bar, stick between hint and live row", geo["hintTop"] >= geo["bar"] - 1 and geo["stickTop"] >= geo["hintBottom"] and geo["stickBottom"] <= geo["live"], fails)
        await pg.click("#balanceBpmPlus"); await pg.click("#balanceBpmPlus"); await pg.wait_for_timeout(80)
        ok("live tempo + saves 70/min", (await prefs(pg)).get("bpm") == 70 and "70/min" in await pg.inner_text("#balanceBpmLive"), fails)
        # Zeit anhalten: clock stops, beat goes on
        await pg.click("#balanceClockBtn"); await pg.wait_for_timeout(100)
        t1 = await pg.inner_text("#balanceStatusEl"); c1 = await pg.evaluate("() => window.__balanceClicks")
        await pg.wait_for_timeout(2200)
        t2 = await pg.inner_text("#balanceStatusEl"); c2 = await pg.evaluate("() => window.__balanceClicks")
        ok("'Zeit halten' stops the clock, shown as ⏸ (no word, bar stays one line)", t1 == t2 and t2.startswith("⏸") and "angehalten" not in t2, fails)
        ok("... while the beat keeps going", c2 > c1, fails)
        await pg.click("#balanceClockBtn")
        # Takt stoppen: no more clicks, clock runs
        await pg.click("#balanceMetroBtn"); await pg.wait_for_timeout(100)
        c3 = await pg.evaluate("() => window.__balanceClicks"); t3 = await pg.inner_text("#balanceStatusEl")
        await pg.wait_for_timeout(1600)
        ok("'Takt stoppen' stops the beat, clock keeps running", await pg.evaluate("() => window.__balanceClicks") == c3 and await pg.inner_text("#balanceStatusEl") != t3, fails)
        ok("metro off saved", (await prefs(pg)).get("metro") is False, fails)
        await pg.click("#balanceMetroBtn")
        ok("no 'Regler' chip in the live row any more", await pg.is_hidden("#balanceKnobBtn"), fails)
        ok("live row is one line", await pg.evaluate("() => { const r = [...document.querySelectorAll('#balanceLive .balance-live-row > *')].filter(e => e.offsetParent).map(e => Math.round(e.getBoundingClientRect().top)); return new Set(r).size <= 1; }"), fails)
        # size live via the pause sheet (shared LIVE_LOOK slider)
        h_before = await pg.evaluate("() => document.getElementById('balanceStick0').getBoundingClientRect().width")
        f_before = await pg.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#balanceStick0 .balance-letter')).fontSize)")
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => { const s = document.querySelector('#balancePauseOverlay [data-live-look=\"balance\"] input'); s.value = '1.4'; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(120)
        h_after = await pg.evaluate("() => document.getElementById('balanceStick0').getBoundingClientRect().width")
        f_after = await pg.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#balanceStick0 .balance-letter')).fontSize)")
        ok("live size makes the stick bigger and saves it", h_after > h_before and abs((await prefs(pg)).get("size") - 1.4) < 0.01, fails)
        ok("letters grow with the stick", f_after > f_before, fails)
        # at a large size the stick shows fewer letters instead of tiny ones
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => { const s = document.querySelector('#balancePauseOverlay [data-live-look=\"balance\"] input'); s.value = s.max; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(120)
        big = await pg.evaluate("() => { const st = document.getElementById('balanceStick0'); const vis = [...st.querySelectorAll('.balance-letter')].filter(e => e.offsetParent); const r = st.getBoundingClientRect(); const L = vis.map(e => e.getBoundingClientRect()); return { n: vis.length, inside: L.every(l => l.top >= r.top - 1 && l.bottom <= r.bottom + 1), font: parseFloat(getComputedStyle(vis[0]).fontSize) }; }")
        print("  big:", big)
        ok("biggest size: bigger font, letters inside the stick", big["inside"] and big["font"] > f_after, fails)
        # live look in the pause sheet: stick + letter colour, length, saved
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        ok("pause sheet: stick colour, letter colour, length, width, font", all([await pg.is_visible(x) for x in ("#balancePauseColor1Picker", "#balancePauseLetterColorPicker", "#balancePauseLengthSlider", "#balancePauseWidthSlider", "#balancePauseFontSlider")]), fails)
        ok("stick 2 colours hidden with one stick", await pg.is_hidden("#balancePauseStick2Group"), fails)
        lc_before = await pg.evaluate("() => getComputedStyle(document.querySelector('#balanceStick0 .balance-letter')).color")
        await pg.evaluate("() => { const bs = [...document.querySelectorAll('#balancePauseLetterColorPicker button')]; const cur = bs.find(b => b.getAttribute('aria-pressed') === 'true' || b.classList.contains('active') || b.classList.contains('selected')); const nb = bs.filter(b => b !== cur && b.dataset.key !== 'auto' && b.offsetParent).pop(); nb.click(); }")
        await pg.wait_for_timeout(80)
        lc_after = await pg.evaluate("() => getComputedStyle(document.querySelector('#balanceStick0 .balance-letter')).color")
        ok("letter colour changes live", lc_after != lc_before, fails)
        await pg.evaluate("() => { const s = document.getElementById('balancePauseLengthSlider'); s.value = '50'; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.wait_for_timeout(80)
        ok("length slider saves", (await prefs(pg)).get("lengthPct") == 50, fails)
        await pg.evaluate("() => { for (const [id, v] of [['balancePauseLengthSlider','30'],['balancePauseFontSlider','1.8']]) { const s = document.getElementById(id); s.value = v; s.dispatchEvent(new Event('input', {bubbles:true})); } }")
        await pg.wait_for_timeout(80)
        short = await pg.evaluate("() => { const st = document.getElementById('balanceStick0'); const vis = [...st.querySelectorAll('.balance-letter')].filter(e => e.offsetParent); const r = st.getBoundingClientRect(); return { n: vis.length, inside: vis.every(e => { const l = e.getBoundingClientRect(); return l.top >= r.top - 1 && l.bottom <= r.bottom + 1; }), font: parseFloat(getComputedStyle(vis[0]).fontSize) }; }")
        print("  short:", short)
        ok("big + short stick: fewer letters, still big, all inside", short["n"] < 4 and short["inside"] and short["font"] >= big["font"] - 1, fails)
        await pg.evaluate("() => { for (const [id, v] of [['balancePauseLengthSlider','100'],['balancePauseFontSlider','1']]) { const s = document.getElementById(id); s.value = v; s.dispatchEvent(new Event('input', {bubbles:true})); } }")
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(80)
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(100)
        await pg.evaluate("() => { const s = document.querySelector('#balancePauseOverlay [data-live-look=\"balance\"] input'); s.value = '1.4'; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(100)
        # pinch (ctrl+wheel = trackpad pinch)
        box = await pg.locator("#balanceStage").bounding_box()
        await pg.mouse.move(box["x"] + 60, box["y"] + 400)
        await pg.keyboard.down("Control"); await pg.mouse.wheel(0, 100); await pg.keyboard.up("Control")
        await pg.wait_for_timeout(150)
        ok("pinch makes it smaller again and saves", (await prefs(pg)).get("size") < 1.4, fails)
        # drag the stick
        sb = await pg.locator("#balanceStick0").bounding_box()
        await pg.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
        await pg.mouse.down(); await pg.mouse.move(sb["x"] - 80, sb["y"] + sb["height"] / 2, steps=6); await pg.mouse.up()
        await pg.wait_for_timeout(100)
        sb2 = await pg.locator("#balanceStick0").bounding_box()
        pos = (await prefs(pg)).get("pos")
        ok("stick can be dragged, position saved", sb2["x"] < sb["x"] - 40 and pos and pos[0]["x"] < 0.45, fails)
        # pause sheet carries tempo, volume, size
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(150)
        ok("pause sheet: tempo, volume and size sliders", await pg.is_visible("#balancePauseBpmSlider") and await pg.is_visible("#balancePauseVolumeSlider") and await pg.locator('#balancePauseOverlay [data-live-look="balance"] input').is_visible(), fails)
        await pg.click("#balanceResumeBtn")
        await pg.click("#balanceFinishBtn"); await pg.wait_for_timeout(300)
        ok("'Fertig' opens the done panel with a check mark", await pg.is_visible("#balanceDonePanel") and await pg.is_visible("#balanceDonePanel .done-check"), fails)
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")
        ok("history entry kind balance, not aborted", bool(hist) and hist[0]["kind"] == "balance" and not hist[0].get("aborted") and hist[0]["title"] == "Gleichgewicht · Nein-Nein", fails)
        await pg.click("#balanceDoneBackBtn"); await pg.wait_for_timeout(200)

        # ---- timed run to its natural end, single letter ----
        await pg.evaluate("""() => { const p = JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1'));
            Object.assign(p, { timing: 'timed', setS: 10, sets: 1, letters: 'einzeln', stanceSpeak: true, stance: 'tandem', mode: 'ja' });
            localStorage.setItem('fwmc-balance-prefs-v1', JSON.stringify(p)); }""")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(200)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(600)
        vis = await pg.evaluate("() => [...document.querySelectorAll('#balanceStick0 .balance-letter')].filter((s) => getComputedStyle(s).visibility !== 'hidden').length")
        ok("'Nur einer': exactly one letter visible", vis == 1, fails)
        ok("stance announced", "Tandem" in json.dumps(await pg.evaluate("() => window.__cueLog || []"), ensure_ascii=False), fails)
        ok("stance shown in the hint", "Tandem" in await pg.inner_text("#balanceHint"), fails)
        await pg.wait_for_timeout(10500)
        ok("timed run ends on its own with the done panel", await pg.is_visible("#balanceDonePanel") and await pg.is_visible("#balanceDonePanel .done-check"), fails)
        await pg.click("#balanceDoneBackBtn"); await pg.wait_for_timeout(200)

        # ---- Beenden within 10 s of a timed run: no entry, back to ready ----
        n_hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]').length")
        await pg.click('#natHome .nat-tile[data-nat-ex="balance"]'); await pg.wait_for_timeout(200)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(800)
        await pg.click("#balanceBackBtn"); await pg.wait_for_timeout(300)
        ok("early Beenden: back on the ready screen, no history entry", await pg.is_visible("#balanceReady") and await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]').length") == n_hist, fails)

        # ---- Kombi-Baustein: add, label, editable, standalone prefs untouched ----
        before = await prefs(pg)
        await pg.evaluate("() => document.querySelector('[data-open-combo]').click()"); await pg.wait_for_timeout(200)
        await pg.locator('#comboAddGrid .combo-add-btn:has-text("Gleichgewicht")').click(); await pg.wait_for_timeout(200)
        ok("Kombi capture opens the ready screen", await pg.is_visible("#balanceReady") and (await pg.inner_text("#balanceReadyStartBtn")).strip() == "Baustein übernehmen", fails)
        await pg.click('[data-bal-mode="ohr"]'); await pg.click('[data-bal-timing="open"]')
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(200)
        row = await pg.locator("#comboBlockList .chapter-row").last.inner_text()
        ok("Baustein listed as 'Gleichgewicht · Ohr-Schulter'", "Gleichgewicht · Ohr-Schulter" in row and "ohne Zeitvorgabe" in row, fails)
        after = await prefs(pg)
        ok("capture did not change the standalone settings", after.get("mode") == before.get("mode") and after.get("timing") == before.get("timing"), fails)

        # ---- live size slider in the pause sheet of every LOOK exercise ----
        n_live = await pg.evaluate("() => ['rememberPauseOverlay','flashPauseOverlay','motPauseOverlay','balancePauseOverlay'].filter((id) => document.querySelector('#' + id + ' [data-live-look] input[type=range]')).length")
        ok("size slider in the pause sheets of Positionen merken, Flash, MOT, Gleichgewicht", n_live == 4, fails)

        await ctx.close()

        # ---- Cardio-Zusatzaufgabe: offered in the live picker, runs, returns ----
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        choice = pg.locator('#cardioAddonPickerTypeRow .choice:has-text("Gleichgewicht")')
        ok("Cardio picker offers Gleichgewicht", await choice.count() == 1, fails)
        await choice.click(); await pg.wait_for_timeout(100)
        ok("picker shows its mode row", await pg.locator('#cardioAddonPicker [data-balf="sticks"]').count() >= 1, fails)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(500)
        ok("guest runs in #balancePlayer", await pg.is_visible("#balancePlayer") and await pg.is_hidden("#cardioPlayer"), fails)
        ok("no 'Fertig' for a guest", await pg.is_hidden("#balanceFinishBtn"), fails)
        await pg.click("#balanceBackBtn"); await pg.wait_for_timeout(300)
        ok("Beenden returns to the running Cardio session", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#balancePlayer"), fails)
        ok("guest left no standalone prefs behind", await pg.evaluate("() => localStorage.getItem('fwmc-balance-prefs-v1')") is None, fails)
        await ctx.close()
        # ---- music keeps playing: no forced "playback" session, one-time silent-switch hint ----
        c2 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await c2.add_init_script(INIT + "localStorage.setItem('fwmc-test-silenthint','true'); navigator.audioSession = navigator.audioSession || { type: 'auto' };")
        p2 = await c2.new_page()
        p2.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        await p2.goto(URL); await p2.wait_for_timeout(400)
        await p2.click('#natHome .nat-tile[data-nat-ex="balance"]'); await p2.wait_for_timeout(200)
        await p2.click("#balanceReadyStartBtn"); await p2.wait_for_timeout(1500)
        ok("beat run keeps the audio session on 'auto' (Spotify keeps playing)", await p2.evaluate("() => navigator.audioSession.type") == "auto", fails)
        ok("first beat run shows the silent-switch hint", await p2.is_visible("#silentHint") and "Stummschalter" in await p2.inner_text("#silentHint"), fails)
        await p2.click("#silentHint"); await p2.wait_for_timeout(100)
        ok("tap closes the hint", await p2.locator("#silentHint").count() == 0, fails)
        await p2.click("#balanceBackBtn"); await p2.wait_for_timeout(300)
        if await p2.is_visible("#balanceDoneBackBtn"): await p2.click("#balanceDoneBackBtn")
        await p2.goto(URL); await p2.wait_for_timeout(400)
        await p2.click('#natHome .nat-tile[data-nat-ex="balance"]'); await p2.wait_for_timeout(200)
        await p2.click("#balanceReadyStartBtn"); await p2.wait_for_timeout(1200)
        ok("hint only once per device", await p2.locator("#silentHint").count() == 0, fails)
        await c2.close()
        await b.close()
    print("failures:", fails)
    print("FINAL ERRORS:", errors)

asyncio.run(main())
