import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"

# Hörmodus (Fabian, 2026-10-03, "Hör-Modus ohne Bildschirm"): Atemtraining
# with spoken phases + counted seconds + remaining minutes, a dark screen and
# a hold-to-pause button so a phone in a pocket can't pause by accident.
# Speech is faked so the spoken words can be checked.
FAKE_SPEECH = """
window.__said = [];
class FakeUtt { constructor(t) { this.text = t; } }
window.SpeechSynthesisUtterance = FakeUtt;
Object.defineProperty(window, 'speechSynthesis', { value: {
  speak(u) { window.__said.push(u.text); }, cancel() {}, getVoices() { return []; }, onvoiceschanged: null
}, configurable: true });
localStorage.setItem('fwmc-tips-seen', 'true');
"""


async def main():
    errors, fails = [], []
    def check(label, ok):
        print(label + ":", ok)
        if not ok: fails.append(label)

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(FAKE_SPEECH)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(200)

        check("three Ansage modes offered", await pg.locator("[data-breath-sound]").count() == 3)
        check("help hidden before Hörmodus", await pg.is_hidden("#breathListenHelp"))
        await pg.click('[data-breath-sound="hoer"]'); await pg.wait_for_timeout(100)
        check("Hörmodus active", "active" in (await pg.get_attribute('[data-breath-sound="hoer"]', "class") or ""))
        check("help shown in Hörmodus", await pg.is_visible("#breathListenHelp"))
        prefs = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-breath-v1'))")
        check("saved as sound+listen", prefs.get("sound") is True and prefs.get("listen") is True)

        # Persists across reload
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(200)
        check("Hörmodus still selected after reload", "active" in (await pg.get_attribute('[data-breath-sound="hoer"]', "class") or ""))

        await pg.click('[data-breath-dur="3"]')
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(3300)
        check("dark listen layer shown", await pg.is_visible("#breathListenLayer"))
        bg = await pg.evaluate("getComputedStyle(document.getElementById('breathListenLayer')).backgroundColor")
        check("layer is dark", bg == "rgb(5, 9, 11)")
        # Layer covers the player-bar: a tap on Beenden's spot hits the layer.
        hit = await pg.evaluate("""() => { const r = document.getElementById('breathBackBtn').getBoundingClientRect();
            const el = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
            return !!el.closest('#breathListenLayer'); }""")
        check("player-bar covered (no pocket taps on Beenden)", hit)
        said = [w for w in await pg.evaluate("window.__said") if w.strip()]  # " " = speech priming
        print("  said:", said)
        check("first phase announced", said and said[0].startswith("Einatmen"))
        check("seconds counted", "2" in said and "3" in said)
        check("phase shown on dark screen", (await pg.inner_text("#breathListenPhase")) in ("Einatmen", "Halten", "Ausatmen"))

        # A short tap does not pause.
        await pg.click("#breathListenHoldBtn"); await pg.wait_for_timeout(300)
        check("short tap does not pause", await pg.is_hidden("#breathPauseOverlay"))
        # Holding pauses.
        box = await pg.locator("#breathListenHoldBtn").bounding_box()
        await pg.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
        await pg.mouse.down(); await pg.wait_for_timeout(1100); await pg.mouse.up()
        await pg.wait_for_timeout(150)
        check("hold pauses", await pg.is_visible("#breathPauseOverlay"))
        check("layer hidden while paused", await pg.is_hidden("#breathListenLayer"))
        await pg.click("#breathResumeBtn"); await pg.wait_for_timeout(200)
        check("layer back after resume", await pg.is_visible("#breathListenLayer"))

        # Turning the voice off in the pause sheet returns to the normal view.
        await pg.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
        await pg.mouse.down(); await pg.wait_for_timeout(1100); await pg.mouse.up()
        await pg.wait_for_timeout(150)
        await pg.click('[data-breath-pause-sound="off"]')
        await pg.click("#breathResumeBtn"); await pg.wait_for_timeout(200)
        check("voice off -> normal view", await pg.is_hidden("#breathListenLayer") and await pg.is_visible("#breathBig"))
        await pg.click("#breathBackBtn"); await pg.wait_for_timeout(300)

        # Minute announcement with a short session: 1 min, fast time.
        await pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('fwmc-breath-v1'));
            s.durationMin = 2; localStorage.setItem('fwmc-breath-v1', JSON.stringify(s)); }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('.section-tab[data-section="breath"]'); await pg.wait_for_timeout(200)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(200)
        # Speed time up 40x so a minute passes in a few seconds.
        await pg.evaluate("""() => { const real = performance.now.bind(performance); const t0 = real();
            performance.now = () => t0 + (real() - t0) * 40;
            const raf = window.requestAnimationFrame.bind(window);
            window.requestAnimationFrame = (cb) => raf(() => cb(performance.now())); }""")
        await pg.evaluate("window.__said = []")
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(2500)
        said = await pg.evaluate("window.__said")
        check("remaining minute announced", any("Noch eine Minute" in s for s in said))
        await pg.wait_for_timeout(1500)
        said = await pg.evaluate("window.__said")
        check("end announced", "Geschafft. Gut gemacht." in said)
        check("done panel after Hörmodus run", await pg.is_visible("#breathDonePanel"))
        check("layer gone at the end", await pg.is_hidden("#breathListenLayer"))

        # Kombi block carries Hörmodus.
        await pg.click("#breathDoneBackBtn"); await pg.wait_for_timeout(200)
        await pg.click('#breathHome .combo-entry-link'); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Box-Atmung"'); await pg.wait_for_timeout(300)
        await pg.click('[data-breath-sound="hoer"]')
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(300)
        meta = await pg.inner_text("#comboBlockList")
        check("Kombi block shows Hörmodus", "Hörmodus" in meta)

        check("no page errors", not errors)
        if errors: print(errors)
        await b.close()
    if fails: print("FAILED:", fails)

asyncio.run(main())
