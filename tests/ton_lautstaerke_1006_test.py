import asyncio, json
from playwright.async_api import async_playwright

# Paket 06.10.2026 abends (Fabian "Ok" 17:20/17:22):
# 1. Training-Seite: "Unser Schwerpunkttraining" über den Kernkacheln, untere
#    Zeile "Frei kombinierbar, auch mit den Bereichen oben.", Kombi-Knopf unter
#    den unteren Kacheln, Kacheltexte beginnen oben und unten gleich weit links.
# 2. 🔊 aus = alles stumm (auch VT-Sprachwörter/Pieptöne und Atem-Ansage).
# 3. Eine Lautstärke für alle Töne und Ansagen (Grundeinstellungen).
# 4. 3-2-1 auch bei Hütchen sortieren und vor dem ersten Kombi-Baustein.
BASE = "http://localhost:8845/index.html"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

# Records every tone (peak gain) and every spoken text (with volume).
AUDIO_SPY = """
(() => {
  window.__tones = []; window.__spoken = [];
  class FakeParam { setValueAtTime(){} exponentialRampToValueAtTime(v){ window.__tones.push(v); } linearRampToValueAtTime(){} }
  class FakeNode { connect(n){ return n; } disconnect(){} }
  class FakeOsc extends FakeNode { constructor(){ super(); this.frequency = { value: 0 }; } start(){} stop(){} }
  class FakeGain extends FakeNode { constructor(){ super(); this.gain = new FakeParam(); } }
  class FakeAC { constructor(){ this.state = 'running'; this.currentTime = 0; this.destination = new FakeNode(); }
    resume(){ return Promise.resolve(); } createOscillator(){ return new FakeOsc(); } createGain(){ return new FakeGain(); }
    createBuffer(){ return {}; } createBufferSource(){ const n = new FakeNode(); n.start = () => {}; return n; } }
  window.AudioContext = FakeAC; window.webkitAudioContext = FakeAC;
  const ss = { speak(u){ if (u.text && u.text.trim()) window.__spoken.push([u.text, u.volume]); }, cancel(){}, getVoices(){ return []; }, onvoiceschanged: null };
  Object.defineProperty(window, 'speechSynthesis', { value: ss, configurable: true });
  window.SpeechSynthesisUtterance = function(t){ this.text = t; this.volume = 1; };
})();
"""

async def new_page(b, extra="", w=390, h=844, scheme="light"):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');" + extra)
    await ctx.add_init_script(AUDIO_SPY)
    pg = await ctx.new_page()
    return ctx, pg

async def main():
    errors = []
    def watch(pg):
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])

        # ---- 1. Training-Seite ----
        for w, scheme in [(390, "light"), (360, "dark"), (1024, "light")]:
            ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-bottomnav','true');localStorage.setItem('fwmc-test-unlocked','true');", w=w, scheme=scheme)
            watch(pg)
            await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(500)
            info = await pg.evaluate("""() => {
              const g = document.getElementById('hubAreaGrid');
              const titles = [...g.querySelectorAll('.hub-group-title')].map(e => e.textContent.trim());
              const subs = [...g.querySelectorAll('.hub-sub')].map(e => e.textContent.trim());
              const first = g.firstElementChild;
              const pads = [...g.querySelectorAll('.area-tile')].map(t => Math.round(t.querySelector('.area-name').getBoundingClientRect().left - t.getBoundingClientRect().left));
              const link = document.querySelector('#trainingHub > .combo-entry-link');
              const extra = g.querySelector('.hub-extra').getBoundingClientRect();
              const lr = link.getBoundingClientRect();
              const badge = g.querySelector('.test-unlock-badge');
              return { titles, subs, firstIsTitle: first.classList.contains('hub-group-title'), pads,
                       linkVisible: lr.height > 0, linkBelow: lr.top >= extra.bottom - 1 && lr.top - extra.bottom < 110,
                       verbHead: (() => { const h = link.previousElementSibling && link.previousElementSibling.previousElementSibling; return !!h && h.classList.contains('hub-group-title') && h.textContent.trim() === 'Alles verbinden' && h.getBoundingClientRect().top >= extra.bottom; })(),
                       squares: [...link.querySelectorAll('.combo-card-icon i')].map(i => getComputedStyle(i).backgroundColor),
                       coreCols: [...g.querySelectorAll('.hub-core .area-icon')].map(i => getComputedStyle(i).backgroundColor),
                       noDash: getComputedStyle(link).borderTopStyle === 'solid',
                       titleAbove: g.querySelector('.hub-group-title').getBoundingClientRect().bottom <= g.querySelector('.hub-core').getBoundingClientRect().top,
                       badgeOneLine: badge ? badge.getBoundingClientRect().height < 26 : true,
                       testMark: (() => { const m = g.querySelectorAll('.hub-test-mark'); if (m.length !== 1) return false; const t = m[0].closest('.area-tile'), mr = m[0].getBoundingClientRect(), nr = t.querySelector('.area-name').getBoundingClientRect(), tr = t.getBoundingClientRect(); return t.dataset.area === 'movement' && t.closest('.hub-core') && m[0].textContent.trim() === 'Test' && mr.right <= tr.right && mr.top >= tr.top && mr.bottom <= nr.top; })(),
                       noSideScroll: document.documentElement.scrollWidth <= innerWidth };
            }""")
            tag = f"{w} {scheme}"
            check(f"[{tag}] heading 'Unser Schwerpunkttraining' first, above the core tiles",
                  info["firstIsTitle"] and info["titles"][0] == "Unser Schwerpunkttraining" and info["titleAbove"], info["titles"])
            check(f"[{tag}] sub lines", info["subs"] == ["Neurozentrierte Grundlagen gezielt trainieren.", "Frei kombinierbar, auch mit den Bereichen oben."], info["subs"])
            check(f"[{tag}] lower group title stays", info["titles"][1] == "Dazu: dein klassisches Training")
            check(f"[{tag}] tile texts start equally far left", len(set(info["pads"])) == 1, info["pads"])
            check(f"[{tag}] Kombi tile below the lower tiles under the heading 'Alles verbinden'", info["linkVisible"] and info["linkBelow"] and info["verbHead"])
            check(f"[{tag}] Kombi icon = four squares in the core area colours, solid frame (Variante H, 07.10.)", info["squares"] == info["coreCols"][:4] and len(info["squares"]) == 4 and info["noDash"], info["squares"])
            check(f"[{tag}] unlock badge on one line", info["badgeOneLine"])
            check(f"[{tag}] Reaktionstraining keeps its core place with a 'Test' mark that covers nothing (07.10.)", info["testMark"])
            check(f"[{tag}] no sideways scroll", info["noSideScroll"])
            await ctx.close()
        # Heute shows no Kombi link any more (Fabian 06.10. abends: "Wer trainieren will, geht unten auf Training")
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-bottomnav','true');")
        watch(pg)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(500)
        check("Heute: no Kombi link", await pg.evaluate("(() => { const l = document.querySelector('#todayHome > .combo-entry-link'); return !l || l.getBoundingClientRect().height === 0; })()"))
        await ctx.close()

        # ---- 2 + 3. Ton aus = alles stumm, eine Lautstärke ----
        # seeded once only, so the reload below keeps what the slider saved
        ctx, pg = await new_page(b, "if (!localStorage.getItem('fwmc-master-v1')) localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click(".master-settings-btn >> visible=true"); await pg.wait_for_timeout(200)
        check("volume slider in Grundeinstellungen, 100 % by default",
              await pg.is_visible("#masterVolumeSlider") and (await pg.inner_text("#masterVolumeValue")).strip() == "100 %")
        await pg.evaluate("() => { const s = document.getElementById('masterVolumeSlider'); s.value = 40; s.dispatchEvent(new Event('input', {bubbles:true})); s.dispatchEvent(new Event('change', {bubbles:true})); }")
        check("value shows 40 %", (await pg.inner_text("#masterVolumeValue")).strip() == "40 %")
        tones = await pg.evaluate("window.__tones")
        check("sample tone on release, scaled to 40 %", len(tones) > 0 and abs(max(tones) - 0.3 * 0.4) < 1e-6, tones[-3:])
        check("volume saved", await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-master-v1')).volume") == 0.4)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(200)
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.click(".master-settings-btn >> visible=true"); await pg.wait_for_timeout(200)
        check("volume persists across reload", (await pg.inner_text("#masterVolumeValue")).strip() == "40 %")
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(200)

        # VT "Sehen & Hören" speaks words + beeps through speakWord/playBeep
        await pg.evaluate("window.__tones = []; window.__spoken = [];")
        await pg.click(".excard[data-exercise='cross-modal']"); await pg.wait_for_timeout(200)
        await pg.click("#startBtn")
        # Sehen & Hören picks image or word at random: wait until a word came
        for _ in range(50):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("window.__spoken.length > 0"): break
        spoken = await pg.evaluate("window.__spoken")
        tones = await pg.evaluate("window.__tones")
        check("VT words spoken at 40 % volume", len(spoken) > 0 and all(abs(v - 0.4) < 1e-6 for _, v in spoken), spoken[:3])
        check("VT beeps (if any) scaled to 40 %", all(t <= 0.35 * 0.4 + 1e-6 for t in tones), tones[:3])
        await pg.click("#stepSoundBtn"); await pg.wait_for_timeout(100)
        await pg.evaluate("window.__tones = []; window.__spoken = [];")
        await pg.wait_for_timeout(15000)
        spoken = await pg.evaluate("window.__spoken")
        tones = [t for t in await pg.evaluate("window.__tones") if t > 0.001]
        check("🔊 off: VT says and beeps nothing", not spoken and not tones, (spoken[:3], tones[:3]))
        await ctx.close()

        # Atem: spoken phase words muted by 🔊, volume scaled when on
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false, volume:0.5}));")
        watch(pg)
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(200)
        await pg.click('[data-breath-sound="on"]'); await pg.wait_for_timeout(100)
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(5000)
        spoken = await pg.evaluate("window.__spoken")
        check("Atem: spoken cues at 50 %", len(spoken) > 0 and all(abs(v - 0.5) < 1e-6 for _, v in spoken), spoken[:3])
        await pg.click("#stepSoundBtn"); await pg.wait_for_timeout(100)
        await pg.evaluate("window.__spoken = [];")
        await pg.wait_for_timeout(6000)
        check("Atem: 🔊 off mutes the spoken cues", not await pg.evaluate("window.__spoken"), await pg.evaluate("window.__spoken"))
        await ctx.close()

        # Volume 0 = silent even with the switch on
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:true, volume:0}));localStorage.setItem('fwmc-test-leadin','true');")
        watch(pg)
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(1500)
        check("volume 0: 3-2-1 beeps silent", not [t for t in await pg.evaluate("window.__tones") if t > 0.001])
        await pg.click("#leadInCancelBtn")
        await ctx.close()

        # ---- 4. 3-2-1 bei Hütchen sortieren und vor dem ersten Kombi-Baustein ----
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-leadin','true');")
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click(".excard[data-exercise='cone-tap']"); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("Hütchen: lead-in shows", await pg.is_visible("#leadIn") and not await pg.is_visible("#coneOrderStage"))
        await pg.wait_for_timeout(3300)
        check("Hütchen: starts after 3-2-1", await pg.is_visible("#coneOrderStage") and not await pg.is_visible("#leadIn"))
        await ctx.close()

        # Other VT exercises keep their own on-stage countdown (no overlay)
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-leadin','true');")
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click(".excard[data-exercise='cone-compass']"); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("other VT exercise: no extra overlay", not await pg.is_visible("#leadIn") and await pg.is_visible("#player"))
        await ctx.close()

        combos = [
            {"id": "1", "name": "Atem zuerst", "blocks": [{"domain": "breath", "pattern": "box", "durationMin": 1}], "createdAt": "2026-10-06T00:00:00Z"},
            {"id": "2", "name": "VT zuerst", "blocks": [{"domain": "visual", "exercise": "cone-compass", "duration": 20}], "createdAt": "2026-10-06T00:00:00Z"},
        ]
        seed = "localStorage.setItem('fwmc-test-leadin','true');localStorage.setItem('fwmc-combo-saved-v1', %s);" % json.dumps(json.dumps(combos))
        ctx, pg = await new_page(b, seed)
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.locator("[data-open-combo] >> visible=true").first.click(); await pg.wait_for_timeout(300)
        await pg.locator("#comboSavedList .bundle-item", has_text="Atem zuerst").click(); await pg.wait_for_timeout(300)
        check("Kombi: 3-2-1 before the first Baustein", await pg.is_visible("#leadIn") and not await pg.is_visible("#breathPlayer"))
        check("Kombi (Atem first): calm lead-in", "calm" in (await pg.get_attribute("#leadIn", "class") or ""))
        await pg.click("#leadInCancelBtn"); await pg.wait_for_timeout(1500)
        check("Kombi: Abbrechen stays on the Kombi page", await pg.is_visible("#comboScreen") and not await pg.is_visible("#breathPlayer"))
        await pg.locator("#comboSavedList .bundle-item", has_text="Atem zuerst").click(); await pg.wait_for_timeout(3600)
        check("Kombi: first Baustein starts after 3-2-1", await pg.is_visible("#breathPlayer") and not await pg.is_visible("#leadIn"))
        await ctx.close()

        ctx, pg = await new_page(b, seed)
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.locator("[data-open-combo] >> visible=true").first.click(); await pg.wait_for_timeout(300)
        await pg.locator("#comboSavedList .bundle-item", has_text="VT zuerst").click(); await pg.wait_for_timeout(300)
        check("Kombi (VT first): VT's own countdown, no overlay", not await pg.is_visible("#leadIn") and await pg.is_visible("#player"))
        await ctx.close()

        ctx, pg = await new_page(b, seed.replace("'fwmc-test-leadin','true'", "'fwmc-test-leadin','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false})"))
        watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.locator("[data-open-combo] >> visible=true").first.click(); await pg.wait_for_timeout(300)
        await pg.locator("#comboSavedList .bundle-item", has_text="Atem zuerst").click(); await pg.wait_for_timeout(300)
        check("Kombi: countdown switched off starts directly", await pg.is_visible("#breathPlayer") and not await pg.is_visible("#leadIn"))
        await ctx.close()
        await b.close()
    check("No page errors", not errors)
    if errors: print(errors[:5])
    print("ALL OK" if ok_all else "SOME CHECKS FAILED")
    print("ERRORS:", errors)

asyncio.run(main())
