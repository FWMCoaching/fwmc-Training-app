import asyncio, json
from playwright.async_api import async_playwright

# Paket 06.10.2026 abends, Ideen 41-44 (Fabian "Ja" 20:00/20:03):
# 41. Takt-Ton im Reaktionstraining: an/aus + Lautstärke (Ready-Seite und
#     Pausenfenster), gespeichert, keine Ansage der Bewegung.
# 42. Tempo live im Pausenfenster: MOT Geschwindigkeit, Flash Einblenddauer +
#     Pause zwischen den Zeichen (nur dieser Lauf, Einstellungen bleiben).
# 43. Kraftvolle Atmung: Ton + kurze Ansage bei jedem Phasenwechsel, auch
#     während der Übung abschaltbar (🔊 / Pausenfenster).
# 44. Kraftvolle Atmung: 3-2-1 vor dem Start und Pause-Knopf.
BASE = "http://localhost:8845/index.html"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

AUDIO_SPY = """
(() => {
  window.__tones = []; window.__spoken = [];
  class FakeParam { setValueAtTime(){} exponentialRampToValueAtTime(v){ if (v > 0.001) window.__tones.push(v); } linearRampToValueAtTime(){} }
  class FakeNode { connect(n){ return n; } disconnect(){} }
  class FakeOsc extends FakeNode { constructor(){ super(); this.frequency = { value: 0 }; } start(){} stop(){} }
  class FakeGain extends FakeNode { constructor(){ super(); this.gain = new FakeParam(); } }
  class FakeAC { constructor(){ this.state = 'running'; this.currentTime = 0; this.destination = new FakeNode(); }
    resume(){ return Promise.resolve(); } createOscillator(){ return new FakeOsc(); } createGain(){ return new FakeGain(); }
    createBuffer(){ return {}; } createBufferSource(){ const n = new FakeNode(); n.start = () => {}; return n; } }
  window.AudioContext = FakeAC; window.webkitAudioContext = FakeAC;
  const ss = { speak(u){ if (u.text && u.text.trim()) window.__spoken.push(u.text); }, cancel(){}, getVoices(){ return []; }, onvoiceschanged: null };
  Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true });
  window.SpeechSynthesisUtterance = function(t){ this.text = t; this.volume = 1; };
})();
"""

async def new_page(b, extra="", scheme="light"):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
    await ctx.add_init_script("if (!localStorage.getItem('fwmc-tips-seen')) localStorage.setItem('fwmc-tips-seen','true');" + extra)
    await ctx.add_init_script(AUDIO_SPY)
    pg = await ctx.new_page()
    return ctx, pg

async def open_wimhof(pg):
    await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
    await pg.click("#breathHome .featured-card:has-text('Kraftvolle Atmung')"); await pg.wait_for_timeout(200)
    await pg.click("#wimhofAckCheck"); await pg.wait_for_timeout(100)

BAR_CLEAR_JS = """(id) => { const ov = document.getElementById(id); const bar = ov.closest('.player').querySelector('.player-bar');
  const panel = ov.querySelector('.pause-panel'); ov.scrollTop = 0;
  // the overlay itself clips scrolled content, so its top must be below the bar
  return [Math.round(bar.getBoundingClientRect().bottom), Math.round(ov.getBoundingClientRect().top), Math.round(panel.getBoundingClientRect().top)]; }"""

async def main():
    errors = []
    def watch(pg):
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])

        # ---- 43 + 44: Kraftvolle Atmung ----
        fast = "localStorage.setItem('fwmc-wimhof-v1', JSON.stringify({breaths:2, rounds:2, breathPaceS:0.5, recoveryHoldS:4}));"
        ctx, pg = await new_page(b, fast)
        watch(pg)
        await open_wimhof(pg)
        await pg.click("#wimhofStartBtn"); await pg.wait_for_timeout(300)
        check("44 pause button visible in the running exercise", await pg.is_visible("#wimhofPauseBtn"))
        check("43 start cue spoken", "Kräftig ein- und ausatmen" in await pg.evaluate("window.__spoken"))
        await pg.wait_for_timeout(1100)
        spoken = await pg.evaluate("window.__spoken")
        check("43 'Ausatmen und anhalten' at the breath hold", "Ausatmen und anhalten" in spoken, spoken)
        check("43 tones played at the changes", await pg.evaluate("window.__tones.length") >= 2)
        check("step bar with 🔊 is there during the exercise", await pg.is_visible("#stepSoundBtn"))
        # pause freezes the breath hold
        await pg.click("#wimhofPauseBtn"); await pg.wait_for_timeout(200)
        check("44 pause sheet opens", await pg.is_visible("#wimhofPauseOverlay"))
        check("44 label reads Pausiert", (await pg.inner_text("#wimhofPhaseLabel")).strip() == "Pausiert")
        held1 = await pg.inner_text("#wimhofPhaseCount")
        await pg.wait_for_timeout(1500)
        held2 = await pg.inner_text("#wimhofPhaseCount")
        check("44 hold clock stands still while paused", held1 == held2, (held1, held2))
        check("43 pause sheet shows sound on", "active" in (await pg.get_attribute("[data-wh-pause-sound='on']", "class") or ""))
        await pg.click("[data-wh-pause-sound='off']"); await pg.wait_for_timeout(100)
        check("43 switching off in the pause sheet = global 🔊 off", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-workout-sound-v1')||'{}').enabled") is False)
        await pg.click("#wimhofResumeBtn"); await pg.wait_for_timeout(200)
        check("44 resume closes the sheet, pause button back", (not await pg.is_visible("#wimhofPauseOverlay")) and await pg.is_visible("#wimhofPauseBtn"))
        n_spoken = len(await pg.evaluate("window.__spoken")); n_tones = await pg.evaluate("window.__tones.length")
        await pg.click("#wimhofHoldDoneBtn"); await pg.wait_for_timeout(300)
        check("43 muted: no cue at 'Einatmen und halten'", len(await pg.evaluate("window.__spoken")) == n_spoken and await pg.evaluate("window.__tones.length") == n_tones)
        # 🔊 in the step bar switches it back on mid-exercise
        await pg.click("#stepSoundBtn"); await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(4500)
        spoken = await pg.evaluate("window.__spoken")
        check("43 🔊 back on mid-exercise: 'Neue Runde' spoken", any("Neue Runde" in t for t in spoken), spoken[-3:])
        await pg.wait_for_timeout(1300)
        await pg.click("#wimhofHoldDoneBtn"); await pg.wait_for_timeout(4800)
        check("finishes normally with done panel", await pg.is_visible("#wimhofDonePanel"))
        check("43 'Geschafft' at the end", any("Geschafft" in t for t in await pg.evaluate("window.__spoken")))
        check("pause button hidden on the result", not await pg.is_visible("#wimhofPauseBtn"))
        await ctx.close()

        # 44: 3-2-1 before the start (calm overlay like Atem)
        ctx, pg = await new_page(b, fast + "localStorage.setItem('fwmc-test-leadin','true');")
        watch(pg)
        await open_wimhof(pg)
        await pg.click("#wimhofStartBtn"); await pg.wait_for_timeout(300)
        check("44 3-2-1 overlay before Kraftvolle Atmung", await pg.is_visible("#leadIn") and not await pg.is_visible("#wimhofPlayer"))
        check("44 lead-in is the calm variant", "calm" in (await pg.get_attribute("#leadIn", "class") or ""))
        await pg.wait_for_timeout(3300)
        check("44 exercise starts after the 3-2-1", await pg.is_visible("#wimhofPlayer") and not await pg.is_visible("#leadIn"))
        await ctx.close()

        # ---- 41: Takt-Ton im Reaktionstraining ----
        ctx, pg = await new_page(b, "if (!localStorage.getItem('fwmc-movement-v1')) localStorage.setItem('fwmc-movement-v1', JSON.stringify({bpm: 120, durationMin: 1}));")
        watch(pg)
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        check("41 Takt group on the ready screen, default on", "active" in (await pg.get_attribute("[data-mv-tick='1']", "class") or ""))
        check("41 volume slider visible when on", await pg.is_visible("#movementTickVolumeSlider"))
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(2300)
        ticks = await pg.evaluate("window.__mvTicks || 0")
        check("41 one tone per movement (120/min, ~2.3 s)", 4 <= ticks <= 6, ticks)
        check("41 no spoken movement names", await pg.evaluate("window.__spoken.length") == 0, await pg.evaluate("window.__spoken"))
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(200)
        check("41 pause sheet has Takt-Ton on/off", await pg.is_visible("[data-mv-pause-tick='0']"))
        widths = await pg.evaluate("[document.getElementById('movementPauseTickVolumeSlider').offsetWidth, document.getElementById('movementPauseBpmSlider').offsetWidth]")
        check("41 Takt-Ton volume slider as wide as the Tempo slider", abs(widths[0] - widths[1]) <= 2, widths)
        check("41 same name on ready screen and pause sheet", await pg.evaluate("[...document.querySelectorAll('#movementReady .group-label')].some(e => e.textContent.trim() === 'Takt-Ton')"))
        await pg.click("[data-mv-pause-tick='0']"); await pg.wait_for_timeout(100)
        check("41 pause volume hidden when off", not await pg.is_visible("#movementPauseTickVolumeSlider"))
        await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(100)
        t0 = await pg.evaluate("window.__mvTicks || 0")
        await pg.wait_for_timeout(1500)
        check("41 off in the pause sheet: no more ticks", await pg.evaluate("window.__mvTicks || 0") == t0)
        check("41 run-only change leaves the saved setting on", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-v1')).tick") is not False)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        # off on the ready screen is saved and survives a reload
        if not await pg.is_visible("#movementReady"):
            await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(300)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("[data-mv-tick='0']"); await pg.wait_for_timeout(100)
        check("41 volume row hidden when off", not await pg.is_visible("#movementTickVolumeSlider"))
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        check("41 'Ohne Takt-Ton' persists across reload", "active" in (await pg.get_attribute("[data-mv-tick='0']", "class") or ""))
        await pg.evaluate("window.__mvTicks = 0")
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(1500)
        check("41 no ticks when off", await pg.evaluate("window.__mvTicks || 0") == 0)
        await ctx.close()

        # 41: volume scales the tone, 🔊 off mutes it
        for vol, sound, label in [(0.5, True, "half volume"), (1.0, False, "🔊 off")]:
            seed = f"localStorage.setItem('fwmc-movement-v1', JSON.stringify({{bpm: 120, durationMin: 1, tick: true, tickVolume: {vol}}}));"
            if not sound:
                seed += "localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false}));"
            ctx, pg = await new_page(b, seed)
            watch(pg)
            await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
            await pg.click("#movementStartBtn"); await pg.wait_for_timeout(1200)
            tones = await pg.evaluate("window.__tones")
            if sound:
                check(f"41 {label}: tone peak scaled to 0.45*0.5", tones and abs(max(tones) - 0.225) < 0.01, tones[:3])
            else:
                check(f"41 {label}: silent", len(tones) == 0, tones[:3])
            await ctx.close()

        # ---- 42: Tempo live MOT + Flash ----
        nat = "localStorage.setItem('fwmc-test-natmodes','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
        ctx, pg = await new_page(b, nat)
        watch(pg)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(400)
        await pg.click('#natHome .nat-tile[data-nat-ex="mot"]'); await pg.wait_for_timeout(200)
        saved_before = await pg.evaluate("localStorage.getItem('fwmc-mot-prefs-v1')")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(900)
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        check("42 MOT pause sheet has Geschwindigkeit", await pg.is_visible("#motPauseSpeedSlider"))
        r = await pg.evaluate(BAR_CLEAR_JS, "motPauseOverlay")
        check("42 MOT pause sheet starts below the (wrapping) player bar, also scrolled", r[1] >= r[0] and r[2] >= r[0], r)
        await pg.fill("#motPauseSpeedSlider", "0.33"); await pg.wait_for_timeout(100)
        check("42 MOT value label follows", (await pg.inner_text("#motPauseSpeedValue")).strip() == "33%")
        await pg.click("#motResumeBtn"); await pg.wait_for_timeout(500)
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        check("42 MOT new speed kept for this run", (await pg.input_value("#motPauseSpeedSlider")) == "0.33")
        check("42 MOT saved settings unchanged", await pg.evaluate("localStorage.getItem('fwmc-mot-prefs-v1')") == saved_before)
        await pg.click("#motResumeBtn"); await pg.wait_for_timeout(200)
        await ctx.close()

        ctx, pg = await new_page(b, nat)
        watch(pg)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(400)
        await pg.click('#natHome .nat-tile[data-nat-ex="flash"]'); await pg.wait_for_timeout(200)
        saved_before = await pg.evaluate("localStorage.getItem('fwmc-flash-prefs-v1')")
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(200)
        check("42 Flash pause sheet has Einblenddauer + Pause", await pg.is_visible("#flashPauseStimulusSlider") and await pg.is_visible("#flashPauseIntervalSlider"))
        await pg.fill("#flashPauseIntervalSlider", "1.5"); await pg.fill("#flashPauseStimulusSlider", "0.4"); await pg.wait_for_timeout(100)
        check("42 Flash labels follow", "1,5" in await pg.inner_text("#flashPauseIntervalValue") and "0,4" in await pg.inner_text("#flashPauseStimulusValue"),
              (await pg.inner_text("#flashPauseIntervalValue"), await pg.inner_text("#flashPauseStimulusValue")))
        await pg.click("#flashResumeBtn"); await pg.wait_for_timeout(300)
        await pg.click("#flashPauseBtn"); await pg.wait_for_timeout(200)
        check("42 Flash values kept for this run", (await pg.input_value("#flashPauseIntervalSlider")) == "1.5" and (await pg.input_value("#flashPauseStimulusSlider")) == "0.4")
        check("42 Flash saved settings unchanged", await pg.evaluate("localStorage.getItem('fwmc-flash-prefs-v1')") == saved_before)
        # pause sheet must still fit: Weiter reachable on a small phone
        await pg.set_viewport_size({"width": 375, "height": 667}); await pg.wait_for_timeout(200)
        box = await pg.evaluate("(() => { const r = document.getElementById('flashResumeBtn').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
        check("42 Weiter visible on a 375x667 phone", box[1] <= box[2] + 1 and box[0] >= 0, box)
        r = await pg.evaluate(BAR_CLEAR_JS, "flashPauseOverlay")
        check("42 Flash pause sheet below the player bar at 375 px, also scrolled", r[1] >= r[0] and r[2] >= r[0], r)
        await ctx.close()

        await b.close()
    check("no page errors", not errors, errors[:5])
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
