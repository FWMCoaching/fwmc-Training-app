"""Ton-Sequenz (Test-Bereich, Fabian 08.10.2026): a tool that plays tones on
the left/right/both ears as a sequence of steps. Fakes the AudioContext
(add_init_script) and checks the node graph per tone (Oscillator -> pulse ->
fade -> L/R gain -> ChannelMerger -> master -> destination), frequencies,
glide, pulse, ear routing incl. Wechsel, quiet start (fade-in), volume x
cueVolume (🔊 off = silence), pause with live volume, the step editor
(±1/±10, input clamping, log slider, add/duplicate/move/remove,
persistence), presets, Kanal-Test (+ first-use prompt), Frequenz-Suchlauf
with "Merken", saved sequences, the 10-minute cap, Vorher/Nachher in the
history and abort handling.
Run from tests/ with a dev server (FWMC_PORT, default 8845)."""
import asyncio, json, os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/ton_sequenz"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-unlocked','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
CHAN_DONE = "localStorage.setItem('fwmc-ton-chantest-v1','1');"

FAKE_AUDIO = r"""
(() => {
  const log = { nodes: [], ctxs: 0 };
  window.__fakeAudio = log;
  let nid = 0;
  function Param(v) { this.value = v; this.events = []; }
  ['setValueAtTime','linearRampToValueAtTime','exponentialRampToValueAtTime','setTargetAtTime','cancelScheduledValues'].forEach((m) => {
    Param.prototype[m] = function (...a) { this.events.push([m, ...a]); if (m === 'setValueAtTime') this.value = a[0]; return this; };
  });
  class Node {
    constructor(ctx, type) { this.id = ++nid; this.kind = type; this.ctx = ctx; this.out = []; log.nodes.push(this); }
    connect(dest, o = 0, i = 0) { this.out.push({ to: dest.id, o, i }); return dest; }
    disconnect() { this.disconnected = true; }
  }
  class FakeCtx {
    constructor() { log.ctxs++; this.state = 'running'; this.t0 = performance.now(); this.destination = new Node(this, 'destination'); this.sampleRate = 44100; }
    get currentTime() { return (performance.now() - this.t0) / 1000; }
    resume() { this.state = 'running'; return Promise.resolve(); }
    close() { return Promise.resolve(); }
    createOscillator() { const n = new Node(this, 'osc'); n.frequency = new Param(440); n.type = 'sine'; n.stops = []; n.start = (t) => { n.started = t; }; n.stop = (t) => { n.stops.push(t); }; return n; }
    createGain() { const n = new Node(this, 'gain'); n.gain = new Param(1); return n; }
    createChannelMerger(c) { const n = new Node(this, 'merger'); n.inputs = c; return n; }
    createBufferSource() { const n = new Node(this, 'buffersrc'); n.start = () => {}; n.stop = () => {}; return n; }
    createBuffer() { return {}; }
  }
  window.AudioContext = FakeCtx; window.webkitAudioContext = FakeCtx;
  window.__voices = () => {
    const byId = (id) => log.nodes.find((n) => n.id === id);
    return log.nodes.filter((n) => n.kind === 'osc').map((o) => {
      try {
        const pulse = byId(o.out[0].to), fade = byId(pulse.out[0].to);
        const gs = fade.out.map((c) => byId(c.to));
        const merger = byId(gs[0].out[0].to), master = byId(merger.out[0].to);
        const ear = {};
        gs.forEach((g) => { ear[g.out[0].i === 0 ? 'L' : 'R'] = g.gain.events; });
        return { type: o.type, freq: o.frequency.events, started: o.started, stops: o.stops,
          pulse: pulse.gain.events, fade: fade.gain.events, L: ear.L, R: ear.R,
          mergerType: merger.kind, mergerInputs: merger.inputs, master: master.gain.events,
          toDest: master.out.length > 0 && master.out[0].to === o.ctx.destination.id };
      } catch (e) { return { broken: String(e) }; }
    });
  };
})();
"""

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def new_page(b, init, dark=False, w=390, h=844):
    ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme="dark" if dark else "light")
    await ctx.add_init_script(FAKE_AUDIO)
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg, errs


async def open_ready(pg):
    await pg.goto(BASE); await pg.wait_for_timeout(350)
    await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(150)
    await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(200)


def seq_seed(seq):
    return f"localStorage.setItem('fwmc-ton-current-v1', JSON.stringify({json.dumps(seq)}));"


def first(events, kind):
    return next((e for e in events if e[0] == kind), None)


async def voices(pg):
    return await pg.evaluate("() => window.__voices()")


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    all_errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- 1. ready screen, defaults, safety note, editor ----
        ctx, pg, errs = await new_page(b, INIT + CHAN_DONE)
        await open_ready(pg)
        check("1a ready screen opens from the Test home", await pg.is_visible("#tonReady"))
        check("1b one default step, 500 Hz", await pg.locator("#tonStepList .ton-step-row").count() == 1
              and await pg.input_value("#tonFreqInput") == "500")
        safety = await pg.text_content("#tonSafety")
        check("1c safety note collapsed, 'Training, keine Therapie', Tinnitus/Epilepsie/Schwindel",
              not await pg.evaluate("() => document.getElementById('tonSafety').open")
              and "keine Therapie" in safety and "Tinnitus" in safety and "Epilepsie" in safety and "schwindlig" in safety)
        check("1d no effect claims (Sacculus/Utriculus) and no dB anywhere",
              await pg.evaluate("() => !/Sacculus|Utriculus|Bogeng|\\bdB\\b/.test(document.getElementById('tonReady').textContent)"))
        await pg.screenshot(path=f"{SHOTS}/ready_390_light.png")
        await pg.click('[data-ton-fstep="10"]'); await pg.click('[data-ton-fstep="-1"]')
        check("1e ±10/±1 change the frequency (509)", await pg.input_value("#tonFreqInput") == "509")
        await pg.fill("#tonFreqInput", "25"); await pg.press("#tonFreqInput", "Enter"); await pg.wait_for_timeout(100)
        check("1f typed 25 Hz is kept and shows the low-frequency hint",
              (await pg.evaluate("() => window.__ton.seq().steps[0].freq")) == 25 and await pg.is_visible("#tonLowHint"))
        await pg.click('[data-ton-fstep="-10"]')
        check("1g lower bound 20 Hz", (await pg.evaluate("() => window.__ton.seq().steps[0].freq")) == 20)
        await pg.fill("#tonFreqInput", "5000"); await pg.press("#tonFreqInput", "Enter"); await pg.wait_for_timeout(100)
        check("1h typed 5000 Hz is clamped to 2000", (await pg.evaluate("() => window.__ton.seq().steps[0].freq")) == 2000
              and await pg.input_value("#tonFreqInput") == "2000" and not await pg.is_visible("#tonLowHint"))
        await pg.evaluate("() => { const s = document.getElementById('tonFreqSlider'); s.value = 500; s.dispatchEvent(new Event('input')); }")
        check("1i log slider middle = 200 Hz", (await pg.evaluate("() => window.__ton.seq().steps[0].freq")) == 200)
        await pg.click('[data-ton-ear="alt"]')
        check("1j Wechsel shows its interval slider", await pg.is_visible("#tonAltSlider"))
        await pg.click('[data-ton-pattern="pulse"]')
        check("1k Puls shows An/Aus sliders", await pg.is_visible("#tonOnSlider") and await pg.is_visible("#tonOffSlider") and not await pg.is_visible("#tonBpmSlider"))
        await pg.click('[data-ton-pulseunit="bpm"]')
        check("1l Takt shows the BPM slider", await pg.is_visible("#tonBpmSlider") and not await pg.is_visible("#tonOnSlider"))
        await pg.click('[data-ton-pattern="glide"]')
        check("1m Gleiten shows the target slider", await pg.is_visible("#tonGlideSlider") and not await pg.is_visible("#tonPulseGroup"))
        await pg.evaluate("() => { const s = document.getElementById('tonPauseSlider'); s.value = 180; s.dispatchEvent(new Event('input')); }")
        check("1n pause slider 0-180 s in 5 s steps", await pg.get_attribute("#tonPauseSlider", "max") == "180"
              and await pg.get_attribute("#tonPauseSlider", "step") == "5"
              and (await pg.evaluate("() => window.__ton.seq().steps[0].pause")) == 180)
        # list: add, duplicate, move, remove
        await pg.click("#tonAddStepBtn"); await pg.click("#tonAddStepBtn")
        check("1o + Schritt adds steps, newest selected", await pg.locator(".ton-step-row").count() == 3
              and (await pg.evaluate("() => window.__ton.sel()")) == 2)
        await pg.click('.ton-step-main[data-ton-sel="0"]')
        await pg.click('[data-ton-ear="left"]')
        await pg.click('[data-ton-down="0"]')
        check("1p ↓ moves the step (left ear now step 2)", (await pg.evaluate("() => window.__ton.seq().steps.map(s => s.ear)"))[1] == "left")
        await pg.click('[data-ton-dup="1"]')
        check("1q ⧉ duplicates", await pg.locator(".ton-step-row").count() == 4
              and (await pg.evaluate("() => window.__ton.seq().steps.map(s => s.ear)"))[2] == "left")
        await pg.click('[data-ton-del="3"]')
        check("1r ✕ removes", await pg.locator(".ton-step-row").count() == 3)
        await pg.screenshot(path=f"{SHOTS}/editor_390_light.png", full_page=True)
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(150)
        check("1s sequence survives a reload", await pg.locator(".ton-step-row").count() == 3)
        # presets
        await pg.click('[data-ton-preset="lr"]'); await pg.wait_for_timeout(100)
        sq = await pg.evaluate("() => window.__ton.seq()")
        check("1t Seitenvergleich L/R: left then right, 500 Hz", [s["ear"] for s in sq["steps"]] == ["left", "right"]
              and all(s["freq"] == 500 for s in sq["steps"]) and sq["name"] == "Seitenvergleich L/R")
        await pg.click('[data-ton-preset="ref100"]'); await pg.wait_for_timeout(100)
        sq = await pg.evaluate("() => window.__ton.seq()")
        check("1u Referenz 100 Hz: one step, both ears, quiet default volume", len(sq["steps"]) == 1 and sq["steps"][0]["freq"] == 100
              and sq["steps"][0]["ear"] == "both" and sq["steps"][0]["vol"] == 20)
        # save + load a sequence
        await pg.click('[data-ton-preset="lr"]')
        await pg.click("#tonSaveBtn"); await pg.fill("#tonSaveNameInput", "Mein Test"); await pg.click("#tonSaveConfirmBtn"); await pg.wait_for_timeout(100)
        await pg.click('[data-ton-preset="ref500"]')
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(150)
        check("1v saved sequence listed after reload", await pg.is_visible("#tonSavedGroup") and "Mein Test" in await pg.text_content("#tonSavedList"))
        await pg.click("#tonSavedList .bundle-item"); await pg.wait_for_timeout(100)
        sq = await pg.evaluate("() => window.__ton.seq()")
        check("1w loading it restores its steps", [s["ear"] for s in sq["steps"]] == ["left", "right"] and sq["name"] == "Mein Test")
        check("1x saved under a fwmc- key", await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-ton-seq-v1')).length") == 1)
        all_errors += errs
        await ctx.close()

        # ---- 2. a run: graph, frequencies, ears, pulse, glide, pause, finish ----
        seq = {"name": "Probe", "repeat": 1, "steps": [
            {"freq": 300, "ear": "left", "pattern": "pulse", "onMs": 200, "offMs": 300, "dur": 5, "pause": 0, "vol": 20},
            {"freq": 200, "ear": "right", "pattern": "glide", "glideTo": 800, "dur": 5, "pause": 0, "vol": 40, "wave": "triangle"},
        ]}
        ctx, pg, errs = await new_page(b, INIT + CHAN_DONE + seq_seed(seq))
        await open_ready(pg)
        await pg.fill("#tonBeforeInput", "Einbeinstand 12 s")
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(300)
        check("2a player visible with .player, Beenden/Pause conventions", await pg.is_visible("#tonPlayer")
              and await pg.text_content("#tonBackBtn") == "✕ Beenden" and await pg.text_content("#tonPauseBtn") == "Pause"
              and await pg.evaluate("() => document.getElementById('tonPlayer').classList.contains('player')"))
        v = await voices(pg)
        v1 = v[-1] if v else {}
        check("2b one oscillator -> ChannelMerger(2) -> master -> destination", len(v) == 1 and v1.get("mergerType") == "merger"
              and v1.get("mergerInputs") == 2 and v1.get("toDest"))
        check("2c frequency 300 Hz, sine", v1.get("freq", [[0, 0]])[0][1] == 300 and v1.get("type") == "sine")
        check("2d left ear: L gain 1, R gain 0", first(v1["L"], "setValueAtTime")[1] == 1 and first(v1["R"], "setValueAtTime")[1] == 0)
        fz = v1["fade"]
        check("2e starts quiet: fade from 0.0001 up over 1.5 s",
              fz[0][0] == "setValueAtTime" and fz[0][1] <= 0.001 and fz[1][0] == "exponentialRampToValueAtTime" and abs((fz[1][2] - fz[0][2]) - 1.5) < 0.01)
        ramps = [e for e in v1["pulse"] if e[0] == "linearRampToValueAtTime"]
        check("2f pulse: on/off edges with short ramps (10 pulses in 5 s)", len(ramps) == 20, f"{len(ramps)} ramps")
        m1 = v1["master"][0][1]
        cue = await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); return m.volume != null ? m.volume : 1; }")
        check("2g master gain = 20 % x 0.5 x cueVolume", abs(m1 - 0.2 * 0.5 * cue) < 1e-6, f"{m1}")
        check("2h stage shows 300 Hz and Links", "300 Hz" in await pg.text_content("#tonNowHz") and "Links" in await pg.text_content("#tonNowEar"))
        hint_box = await pg.locator("#tonHint").bounding_box(); bar_box = await pg.locator("#tonPlayerBar").bounding_box()
        check("2i safety hint sits below the player bar", hint_box and bar_box and hint_box["y"] >= bar_box["y"] + bar_box["height"] - 1)
        await pg.screenshot(path=f"{SHOTS}/player_390_light.png")
        await pg.wait_for_timeout(5200)
        v = await voices(pg)
        v2 = v[-1]
        check("2j step 2 starts: right ear, triangle", len(v) == 2 and first(v2["L"], "setValueAtTime")[1] == 0
              and first(v2["R"], "setValueAtTime")[1] == 1 and v2["type"] == "triangle")
        check("2k step 1's oscillator was stopped", len(v[0]["stops"]) >= 1)
        gl = first(v2["freq"], "exponentialRampToValueAtTime")
        check("2l glide 200 -> 800 Hz over the step", v2["freq"][0][1] == 200 and gl and abs(gl[1] - 800) < 1)
        check("2m triangle volume 40 % x 0.5 x 0.85", abs(v2["master"][0][1] - 0.4 * 0.5 * 0.85 * cue) < 1e-6)
        # pause with live volume
        await pg.click("#tonPauseBtn"); await pg.wait_for_timeout(150)
        v = await voices(pg)
        check("2n pause stops the tone and opens the pause sheet", len(v[-1]["stops"]) >= 2 and await pg.is_visible("#tonPauseOverlay"))
        await pg.evaluate("() => { const s = document.getElementById('tonLiveVolSlider'); s.value = 80; s.dispatchEvent(new Event('input')); }")
        await pg.screenshot(path=f"{SHOTS}/pause_390_light.png")
        await pg.click("#tonResumeBtn"); await pg.wait_for_timeout(200)
        v = await voices(pg)
        v3 = v[-1]
        check("2o resume: new voice at the live volume, short fade-in, glide continues mid-way",
              len(v) == 3 and abs(v3["master"][0][1] - 0.8 * 0.5 * 0.85 * cue) < 1e-6
              and abs((v3["fade"][1][2] - v3["fade"][0][2]) - 0.3) < 0.01 and v3["freq"][0][1] > 200)
        await pg.wait_for_timeout(5200)
        check("2p done panel after the last step", await pg.is_visible("#tonDonePanel") and "Probe" in await pg.text_content("#tonDoneSummary"))
        h = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || localStorage.getItem('fwmc-history') || '[]')")
        if not h:
            h = await pg.evaluate("() => { for (const k of Object.keys(localStorage)) { if (/history/.test(k)) { try { const l = JSON.parse(localStorage.getItem(k)); if (Array.isArray(l)) return l; } catch (e) {} } } return []; }")
        e = h[0] if h else {}
        check("2q history entry kind tonseq with Vorher", e.get("kind") == "tonseq" and "Vorher: Einbeinstand 12 s" in e.get("note", "")
              and not e.get("aborted"))
        await pg.fill("#tonAfterInput", "15 s"); await pg.click("#tonAfterSaveBtn"); await pg.wait_for_timeout(100)
        h2 = await pg.evaluate("() => { for (const k of Object.keys(localStorage)) { if (/history/.test(k)) { try { const l = JSON.parse(localStorage.getItem(k)); if (Array.isArray(l) && l.length && l[0].kind) return l; } catch (e) {} } } return []; }")
        check("2r Nachher is added to the same entry", h2 and h2[0].get("after") == "15 s" and "Nachher: 15 s" in h2[0].get("note", "")
              and await pg.is_visible("#tonAfterSaved"))
        await pg.screenshot(path=f"{SHOTS}/done_390_light.png")
        check("2s all tones stopped after the end", all(len(x["stops"]) >= 1 for x in await voices(pg)))
        all_errors += errs
        await ctx.close()

        # ---- 3. Wechsel, 🔊 off, abort ----
        seq = {"name": "", "repeat": 2, "steps": [{"freq": 440, "ear": "alt", "altS": 1, "dur": 5, "pause": 5}]}
        ctx, pg, errs = await new_page(b, INIT + CHAN_DONE + seq_seed(seq))
        await open_ready(pg)
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(300)
        v = (await voices(pg))[-1]
        tg = [e for e in v["L"] if e[0] == "setTargetAtTime"]
        check("3a Wechsel: starts left, then switches every second with soft ramps",
              first(v["L"], "setValueAtTime")[1] == 1 and first(v["R"], "setValueAtTime")[1] == 0 and len(tg) == 4
              and [e[1] for e in tg] == [0, 1, 0, 1])
        segs = await pg.evaluate("() => window.__ton.run().segs.map(s => s.kind + ':' + s.dur)")
        check("3b repeat 2 with pause between, no trailing pause", segs == ["tone:5", "pause:5", "tone:5"], str(segs))
        await pg.wait_for_timeout(1500)
        await pg.click("#tonBackBtn"); await pg.wait_for_timeout(200)
        check("3c Beenden before 5 s: back to the Test home, no history entry", await pg.is_visible("#testHome")
              and not await pg.evaluate("() => Object.keys(localStorage).some(k => /history/.test(k) && (localStorage.getItem(k) || '').includes('tonseq'))"))
        check("3d tone stopped on Beenden", all(len(x["stops"]) >= 1 for x in await voices(pg)))
        await pg.click("#tonOpenBtn"); await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(5600)
        await pg.click("#tonBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("3e Beenden after 5 s: aborted done panel without check", await pg.is_visible("#tonDonePanel")
              and not await pg.is_visible("#tonDonePanel .done-check") and "Abgebrochen" in await pg.text_content("#tonDoneSummary"))
        await pg.click("#tonDoneBackBtn")
        # 🔊 off
        await pg.evaluate("() => localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="test"]'); await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(150)
        n0 = len(await voices(pg))
        await pg.click("#tonPreviewBtn"); await pg.wait_for_timeout(150)
        check("3f 🔊 off: Probehören plays nothing", len(await voices(pg)) == n0)
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(300)
        v = await voices(pg)
        check("3g 🔊 off: run is silent (master gain 0) and says so", v and v[-1]["master"][0][1] == 0 and await pg.is_visible("#tonNowMute"))
        await pg.click("#tonBackBtn")
        all_errors += errs
        await ctx.close()

        # ---- 4. Kanal-Test, first-use prompt, Suchlauf, 10-min cap ----
        seq = {"name": "", "repeat": 1, "steps": [{"freq": 500, "ear": "right", "dur": 5}]}
        ctx, pg, errs = await new_page(b, INIT + seq_seed(seq))
        await open_ready(pg)
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(250)
        check("4a first run with a one-sided step offers the Kanal-Test", await pg.is_visible("#confirmSheet")
              and "Kanal-Test" in await pg.text_content("#confirmTitle"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        v = (await voices(pg))[-1]
        check("4b Kanal-Test: 'Jetzt links', left channel only", "links" in await pg.text_content("#tonChannelStatus")
              and first(v["L"], "setValueAtTime")[1] == 1 and first(v["R"], "setValueAtTime")[1] == 0)
        await pg.screenshot(path=f"{SHOTS}/kanaltest_390_light.png")
        await pg.wait_for_timeout(2700)
        v = (await voices(pg))[-1]
        check("4c then 'Jetzt rechts', right channel only", "rechts" in await pg.text_content("#tonChannelStatus")
              and first(v["L"], "setValueAtTime")[1] == 0 and first(v["R"], "setValueAtTime")[1] == 1)
        await pg.wait_for_timeout(2400)
        check("4d Kanal-Test done text + remembered", "Mono-Audio" in await pg.text_content("#tonChannelStatus")
              and await pg.evaluate("() => localStorage.getItem('fwmc-ton-chantest-v1')") == "1")
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(250)
        check("4e no prompt any more", not await pg.is_visible("#confirmSheet") and await pg.is_visible("#tonPlayer"))
        await pg.click("#tonBackBtn"); await pg.wait_for_timeout(200)
        await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#tonSweepBtn"); await pg.wait_for_timeout(150)
        v = (await voices(pg))[-1]
        sw = first(v["freq"], "exponentialRampToValueAtTime")
        check("4f Suchlauf: 100 -> 1000 Hz over 60 s", v["freq"][0][1] == 100 and sw and abs(sw[1] - 1000) < 1
              and abs((sw[2] - v["freq"][0][2]) - 60) < 0.05 and await pg.is_visible("#tonSweepMarkBtn"))
        await pg.wait_for_timeout(1800)
        await pg.click("#tonSweepMarkBtn"); await pg.wait_for_timeout(100)
        f = await pg.evaluate("() => window.__ton.seq().steps[0].freq")
        check("4g Merken puts the current Hz into the step", 100 < f < 120 and "gemerkt" in await pg.text_content("#tonSweepHz"), f"{f} Hz")
        check("4h Merken stops the sweep", len((await voices(pg))[-1]["stops"]) >= 2 and not await pg.is_visible("#tonSweepMarkBtn"))
        await pg.click("#tonPreviewBtn"); await pg.wait_for_timeout(100)
        await pg.click("#tonReadyBackToHome"); await pg.wait_for_timeout(100)
        check("4i leaving the ready screen stops Probehören", len((await voices(pg))[-1]["stops"]) >= 2)
        all_errors += errs
        await ctx.close()
        ctx, pg, errs = await new_page(b, INIT + CHAN_DONE + seq_seed({"repeat": 10, "steps": [{"freq": 500, "dur": 300, "pause": 60}]}))
        await open_ready(pg)
        check("4j more than 10 min: the help says so", "10 Minuten" in await pg.text_content("#tonTotalHelp"))
        await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(200)
        tot = await pg.evaluate("() => window.__ton.run().segs.reduce((a, s) => a + s.dur, 0)")
        check("4k a run never lasts longer than 10 min", tot == 600, str(tot))
        await pg.click("#tonBackBtn")
        all_errors += errs
        await ctx.close()

        # ---- 5. screenshots dark / 1024 ----
        for dark, w, h in ((True, 390, 844), (False, 1024, 768), (True, 1024, 768)):
            seq = {"name": "Seitenvergleich L/R", "repeat": 1, "steps": [{"freq": 500, "ear": "left", "dur": 20, "pause": 10}, {"freq": 500, "ear": "right", "dur": 20}]}
            ctx, pg, errs = await new_page(b, INIT + CHAN_DONE + seq_seed(seq), dark=dark, w=w, h=h)
            await open_ready(pg)
            tag = f"{w}_{'dark' if dark else 'light'}"
            await pg.screenshot(path=f"{SHOTS}/ready_{tag}.png")
            await pg.screenshot(path=f"{SHOTS}/ready_full_{tag}.png", full_page=True)
            await pg.click("#tonReadyStartBtn"); await pg.wait_for_timeout(600)
            await pg.screenshot(path=f"{SHOTS}/player_{tag}.png")
            ov = await pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
            check(f"5 {tag}: no sideways scroll", ov)
            await pg.click("#tonBackBtn")
            all_errors += errs
            await ctx.close()

        await b.close()
    check("no pageerror / console error", not all_errors, "; ".join(all_errors[:3]))
    print(f"\n{sum(results)}/{len(results)} passed")


asyncio.run(main())
