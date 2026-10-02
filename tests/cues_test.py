import asyncio, json
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Töne & Ansagen + "Alle entfernen" (2026-10-02, Fabian): one Master setting
# for countdown beeps, Takt-Ton and spoken cues, each area (Tabata,
# Kraftplan, Cardio, Kombi) can deviate in its Feineinstellungen; every
# built list can be cleared in one go after a Ja/Nein question.

# Fake AudioContext records every tone's frequency (880 short beep, 1180
# long beep, 620 Takt-Ton); window.__cueLog records spoken texts.
AUDIO_STUB = """
  window.__tones = [];
  class FakeCtx {
    constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
    createOscillator() { const o = { frequency: { value: 0 }, connect() {}, start() { window.__tones.push(o.frequency.value); }, stop() {} }; return o; }
    createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; }
    resume() {}
  }
  window.AudioContext = FakeCtx; window.webkitAudioContext = FakeCtx;
"""
def speedup(factor):
    return """
  const realNow = performance.now.bind(performance);
  const realRAF = window.requestAnimationFrame.bind(window);
  const start = realNow();
  const warp = (real) => start + (real - start) * %d;
  performance.now = () => warp(realNow());
  window.requestAnimationFrame = (cb) => realRAF((realTs) => cb(warp(realTs)));
""" % factor

async def new_page(b, errors, factor=None, seed=None):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
    if seed:
        await ctx.add_init_script(seed)
    await ctx.add_init_script(AUDIO_STUB)
    if factor:
        await ctx.add_init_script(speedup(factor))
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await pg.goto(URL); await pg.wait_for_timeout(300)
    return pg

def master_seed(cues):
    return "localStorage.setItem('fwmc-master-v1', JSON.stringify(%s))" % json.dumps({"cues": cues})

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])

        # ---------- settings UI ----------
        pg = await new_page(b, errors)
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(150)
        m = pg.locator("#masterCuesGroup")
        print("master has Töne & Ansagen:", "Töne & Ansagen" in await m.inner_text())
        print("note option hidden until 'ansagen' ticked:", await m.locator('[data-cue-key="announceNote"]').count() == 0)
        await m.locator('[data-cue-count="5"]').click(); await pg.wait_for_timeout(60)
        await m.locator('[data-cue-key="announceNext"]').check(); await pg.wait_for_timeout(60)
        print("note option appears:", await m.locator('[data-cue-key="announceNote"]').count() == 1)
        await m.locator('[data-cue-tick="15"]').click(); await m.locator("[data-cue-silent]").check(); await pg.wait_for_timeout(60)
        st = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-master-v1'))")
        print("master persisted:", st["cues"]["countdownS"] == 5 and st["cues"]["announceNext"] and st["cues"]["tickS"] == 15 and st["cuesIgnoreSilent"])
        await m.locator('[data-cue-count="0"]').click(); await pg.wait_for_timeout(60)
        print("countdown Aus hides start/end checkboxes:", await m.locator('[data-cue-key="countStart"]').count() == 0)
        await m.locator('[data-cue-count="5"]').click()
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(100)

        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutCircuitAdvanced summary"); await pg.wait_for_timeout(80)
        d = pg.locator("#cueDomain_tabata")
        print("tabata follows master by default:", "Folgt den Grundeinstellungen" in await d.inner_text())
        await d.locator('[data-cue-mode="own"]').click(); await pg.wait_for_timeout(60)
        print("own setting seeded from master (5 s active):", "active" in (await d.locator('[data-cue-count="5"]').get_attribute("class")))
        await d.locator('[data-cue-count="3"]').click(); await pg.wait_for_timeout(60)
        ov = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-cue-overrides-v1'))")
        mst = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-master-v1')).cues.countdownS")
        print("override stored, master untouched:", ov["tabata"]["countdownS"] == 3 and mst == 5)
        await d.locator('[data-cue-mode="master"]').click(); await pg.wait_for_timeout(60)
        ov = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-cue-overrides-v1'))")
        print("back to master removes override:", "tabata" not in ov)
        print("kombi panel has no Takt-Ton:", await pg.evaluate("document.querySelector('#cueDomain_kombi').innerHTML.indexOf('Takt') === -1") and await pg.locator("#cueDomain_kombi").count() == 1)
        await pg.context.close()

        # ---------- clear-all ----------
        pg = await new_page(b, errors)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        print("clear hidden on empty list:", await pg.is_hidden("#workoutCircuitClearBtn"))
        for n in ["Kniebeugen", "Liegestütze"]:
            await pg.click(f'#workoutCircuitAddGrid .custom-exercise-add-row:has-text("{n}") .ca-plus-btn'); await pg.wait_for_timeout(60)
        await pg.click("#workoutCircuitClearBtn"); await pg.wait_for_timeout(80)
        print("asks first:", await pg.is_visible("#confirmSheet") and "Bist du sicher" in await pg.inner_text("#confirmTitle"))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(80)
        print("Nein keeps list:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 2 and await pg.is_hidden("#confirmSheet"))
        await pg.click("#workoutCircuitClearBtn"); await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(80)
        print("Ja clears tabata:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 0 and await pg.is_hidden("#workoutCircuitClearBtn") and await pg.is_disabled("#workoutTabataStartBtn"))
        await pg.click("#workoutTabataBackToHome"); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(60)
        await pg.click("#workoutRepsClearBtn"); await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(80)
        stored = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-workout-reps-builder-v1')).items.length")
        print("Ja clears Kraftplan (and storage):", await pg.locator("#workoutRepsList .strength-item-row").count() == 0 and stored == 0)
        await pg.click("#workoutRepsBackToHome"); await pg.wait_for_timeout(100)
        await pg.click('#workoutHome .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(60)
        await pg.click("#cardioClearBtn"); await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(80)
        print("Ja clears Cardio:", await pg.locator("#cardioList .circuit-item-row").count() == 0)
        await pg.click("#cardioBackToHome"); await pg.wait_for_timeout(100)
        await pg.click("#cardioHome .combo-entry-link"); await pg.wait_for_timeout(200)
        for act in ["Joggen", "Walking"]:
            await pg.click('#comboAddGrid >> text="Cardio-Einheit"'); await pg.wait_for_timeout(200)
            await pg.click(f'#cardioAddGrid >> text="{act}"'); await pg.wait_for_timeout(60)
            await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(200)
        print("two Kombi blocks:", await pg.locator("#comboBlockList .combo-block-remove:not(.combo-block-move)").count() == 2)
        await pg.click("#comboClearBtn"); await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(80)
        print("Ja clears Kombi:", await pg.locator("#comboBlockList .combo-block-remove:not(.combo-block-move)").count() == 0 and await pg.is_visible("#comboEmptyHint"))
        await pg.context.close()

        # ---------- Tabata runtime (time x6) ----------
        cues = {"countdownS": 3, "countStart": True, "countEnd": True, "tickS": 0, "announceNext": True, "announceNote": True, "announceHalf": True, "announceLastRound": True}
        pg = await new_page(b, errors, factor=6, seed=master_seed(cues) + ";localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify({items:[{exercise:'kniebeuge',workS:15},{exercise:'liegestuetz',workS:15,note:'Ellbogen eng'}],restS:10,sets:2,setRestS:10,defaultWorkS:15,prepS:3,cooldownS:0}))")
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        print("seeded circuit:", await pg.locator("#workoutCircuitList .circuit-item-row").count() == 2)
        await pg.click("#workoutTabataStartBtn")
        await pg.wait_for_timeout(17500)
        log = await pg.evaluate("window.__cueLog || []")
        tones = await pg.evaluate("window.__tones")
        print("tabata spoken:", log)
        print("start announced:", any("Los geht's mit Kniebeugen" in t for t in log))
        print("next with note:", any("Als Nächstes: Liegestütze. Ellbogen eng" in t for t in log))
        print("last round + half:", any("Letzte Runde" in t for t in log) and "Halbzeit" in log)
        print("countdown and long beeps:", tones.count(880) >= 12 and tones.count(1180) >= 8, tones.count(880), tones.count(1180))
        print("done panel:", await pg.is_visible("#workoutDonePanel"))
        await pg.context.close()

        # tabata own override: countdown Aus -> no beeps, still announces
        pg = await new_page(b, errors, factor=6, seed=master_seed(cues) + ";localStorage.setItem('fwmc-cue-overrides-v1', JSON.stringify({tabata:{countdownS:0,announceNext:false}}));localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify({items:[{exercise:'kniebeuge',workS:5}],restS:0,sets:1,setRestS:10,defaultWorkS:15,prepS:3,cooldownS:0}))")
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(2500)
        print("override wins (no beeps, no speech):", await pg.evaluate("window.__tones.length") == 0 and await pg.evaluate("(window.__cueLog||[]).length") == 0)
        await pg.context.close()

        # ---------- Kraftplan ----------
        cues2 = {"countdownS": 3, "countStart": True, "countEnd": True, "tickS": 0, "announceNext": True, "announceNote": False, "announceLastSet": True}
        pg = await new_page(b, errors, seed=master_seed(cues2))
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(60)
        await pg.click("#workoutRepsAdvanced summary"); await pg.wait_for_timeout(60)
        await pg.evaluate("const s=document.getElementById('workoutRepsPrepSlider'); s.value=4; s.dispatchEvent(new Event('input',{bubbles:true}))")
        sets = int((await pg.locator("#workoutRepsList .strength-item-row").nth(0).locator('[data-svalue="sets"]').inner_text()).strip())
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(200)
        print("start announced:", "Los geht's mit Kniebeugen." in await pg.evaluate("window.__cueLog || []"))
        await pg.wait_for_timeout(4600)
        tones = await pg.evaluate("window.__tones")
        print("start countdown 3 short + 1 long:", tones.count(880) == 3 and tones.count(1180) == 1, tones)
        for k in range(1, sets):
            await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(120)
            log = await pg.evaluate("window.__cueLog || []")
            if k < sets - 1:
                print(f"no 'Letzter Satz' before set {k+1}:", "Letzter Satz." not in log)
            else:
                print("'Letzter Satz' before last set:", "Letzter Satz." in log)
            await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(120)
        await pg.context.close()

        # ---------- Cardio Takt-Ton (time x15) ----------
        cues3 = {"countdownS": 3, "countStart": True, "countEnd": True, "tickS": 10, "announceNext": True}
        pg = await new_page(b, errors, factor=15, seed=master_seed(cues3))
        await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(60)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(2800)
        tones = await pg.evaluate("window.__tones")
        print("cardio Takt-Ton every 10 s:", tones.count(620) >= 3, tones.count(620))
        print("cardio start announced:", any("Los geht's mit Joggen" in t for t in await pg.evaluate("window.__cueLog || []")))
        await pg.context.close()

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
