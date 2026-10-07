"""Nacht 07.10.2026 - three features Fabian approved on 06.10.:
  Idee 52  Vollbild in Eigenes Training + Kombi bleibt durchgehend im Vollbild
           (iPhone Safari: no Fullscreen API -> no button)
  Idee 53  Atemtraining "Ohne Zeitlimit" + "Weiter atmen" after the time is up
           (Kombi goes on afterwards, presets, Kombi capture, Weitermachen)
  Idee 55  Reaktionstraining: Hintergrund + Signalfarbe (presets, Kombi block,
           Weitermachen, pause sheet, light/dark)
Run from tests/ with a dev server on :8845. The Fullscreen API is stubbed
(headless Chromium): requests/exits are counted in window.__fs."""
import asyncio, json, os, time
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = "screenshots/nacht_1007"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
FS_STUB = """
window.__fs = { req: [], exits: 0, el: null };
Object.defineProperty(Document.prototype, 'fullscreenElement', { configurable: true, get() { return window.__fs.el; } });
Object.defineProperty(Document.prototype, 'fullscreenEnabled', { configurable: true, get() { return true; } });
Element.prototype.requestFullscreen = function () { window.__fs.req.push(this.id || this.tagName); window.__fs.el = this; document.dispatchEvent(new Event('fullscreenchange')); return Promise.resolve(); };
Document.prototype.exitFullscreen = function () { window.__fs.exits++; window.__fs.el = null; document.dispatchEvent(new Event('fullscreenchange')); return Promise.resolve(); };
"""
NO_FS_API = "delete Element.prototype.requestFullscreen; delete Element.prototype.webkitRequestFullscreen;"

FREE_OWN = [{"id": "j1", "kind": "check", "title": "Journal", "note": "", "minutes": 5, "items": []}]
FAST_PHASES = {"in": 1, "hold1": 0, "out": 1, "hold2": 0}
MV_FAST = {"domain": "movement", "movements": ["armL-heben", "armR-heben", "legL-strecken", "legR-strecken"],
           "bpm": 160, "durationMin": 0.02, "preview": 2, "mirror": True, "showLabel": False,
           "layout": "zeilen", "rowLen": 4, "figureStyle": "felder"}

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

VIS = "() => [...document.querySelectorAll('.screen,.player,.done-panel')].filter(e => !e.hidden && e.getClientRects().length).map(e => e.id).join('+')"
LAST_HIST = "() => (JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')).slice(-1)[0] || (JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]'))[0]"
HIST = "() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')"


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return tuple(x + (y - x) * t for x, y in zip(pa, pb))


def near(css, want):
    """css 'rgb(r, g, b)' within 1 of the mixed colour (JS rounds half up)."""
    try:
        got = [int(v) for v in css[css.index("(") + 1:css.index(")")].split(",")[:3]]
    except ValueError:
        return False
    return all(abs(g - w) <= 1 for g, w in zip(got, want))


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        async def fresh(seed="", scheme="light", fs=True):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme=scheme)
            await ctx.add_init_script(INIT + (FS_STUB if fs else "") + seed)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            return ctx, pg

        def once(js):
            # seed only on the first load of a context, so reloads keep what the app wrote
            return "if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');" + js + "}"

        async def latest_history(pg):
            h = await pg.evaluate(HIST)
            return max(h, key=lambda e: e.get("ts") or e.get("date") or 0) if h else None

        async def open_combo(pg, name):
            await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
            await pg.locator("[data-open-combo] >> visible=true").first.click(); await pg.wait_for_timeout(300)
            await pg.locator("#comboSavedList .bundle-item", has_text=name).click(); await pg.wait_for_timeout(400)

        # ================= Idee 52: Vollbild =================
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-free-blocks-v1', {json.dumps(json.dumps(FREE_OWN))});"))
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.locator("#freeOwnGrid .featured-card", has_text="Journal").click(); await pg.wait_for_timeout(300)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(400)
        check("Eigenes Training: Vollbild button in the player bar", await pg.is_visible("#freePlayer #freePlayerBar #freeFsBtn"))
        await pg.click("#freeFsBtn"); await pg.wait_for_timeout(150)
        fs = await pg.evaluate("() => window.__fs")
        check("Eigenes Training: fullscreen requested on the player", fs["req"][-1:] == ["freePlayer"], fs)
        check("Eigenes Training: label 'Vollbild aus'", (await pg.inner_text("#freeFsBtn")).strip() == "Vollbild aus")
        for scheme in ("light",):
            await pg.screenshot(path=f"{SHOTS}/free_player_vollbild_{scheme}.png")
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(400)
        fs = await pg.evaluate("() => window.__fs")
        check("Eigenes Training: done leaves fullscreen", fs["el"] is None and fs["exits"] >= 1 and await pg.is_visible("#freeDonePanel"), fs)
        await ctx.close()

        # Kombi keeps fullscreen across the Baustein change
        combos = [
            {"id": "k1", "name": "Vollbild-Kombi", "createdAt": "2026-10-07T00:00:00Z", "blocks": [
                {"domain": "free", "free": FREE_OWN[0], "pauseAfterS": 0},
                dict(MV_FAST, pauseAfterS=0)]},
        ]
        ctx, pg = await fresh(f"localStorage.setItem('fwmc-combo-saved-v1', {json.dumps(json.dumps(combos))});")
        await open_combo(pg, "Vollbild-Kombi")
        check("Kombi: first Baustein (Eigenes Training) runs", await pg.is_visible("#freePlayer"))
        await pg.click("#freeFsBtn"); await pg.wait_for_timeout(150)
        fs = await pg.evaluate("() => window.__fs")
        check("Kombi: fullscreen requested on the whole page", fs["req"][-1:] == ["HTML"], fs)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(300)
        fs = await pg.evaluate("() => window.__fs")
        check("Kombi: next Baustein plays", await pg.is_visible("#movementPlayer"), await pg.evaluate(VIS))
        check("Kombi: still fullscreen after the Baustein change (no exit)", fs["el"] is not None and fs["exits"] == 0, fs)
        check("Kombi: next player's button reads 'Vollbild aus'", (await pg.inner_text("#movementFsBtn")).strip() == "Vollbild aus")
        await pg.wait_for_timeout(3500)
        fs = await pg.evaluate("() => window.__fs")
        check("Kombi end: done panel + fullscreen left", await pg.is_visible("#comboDonePanel") and fs["el"] is None and fs["exits"] == 1, fs)
        await ctx.close()

        # Kombi abort leaves fullscreen too
        ctx, pg = await fresh(f"localStorage.setItem('fwmc-combo-saved-v1', {json.dumps(json.dumps(combos))});")
        await open_combo(pg, "Vollbild-Kombi")
        await pg.click("#freeFsBtn"); await pg.wait_for_timeout(150)
        await pg.click("#freeBackBtn"); await pg.wait_for_timeout(300)
        fs = await pg.evaluate("() => window.__fs")
        check("Kombi abort: fullscreen left", fs["el"] is None and fs["exits"] >= 1, fs)
        await ctx.close()

        # Standalone players keep fullscreen on themselves (no regression)
        ctx, pg = await fresh()
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(300)
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#breathFsBtn"); await pg.wait_for_timeout(150)
        fs = await pg.evaluate("() => window.__fs")
        check("single run: fullscreen on the player itself", fs["req"][-1:] == ["breathPlayer"], fs)
        await ctx.close()

        # dark screenshot of the Eigenes-Training player with its button
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-free-blocks-v1', {json.dumps(json.dumps(FREE_OWN))});"), scheme="dark")
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.locator("#freeOwnGrid .featured-card", has_text="Journal").click(); await pg.wait_for_timeout(300)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{SHOTS}/free_player_vollbild_dark.png")
        await ctx.close()

        # iPhone Safari (no Fullscreen API): no Vollbild buttons
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-free-blocks-v1', {json.dumps(json.dumps(FREE_OWN))});") + NO_FS_API, fs=False)
        await pg.goto(BASE + "?bereich=free"); await pg.wait_for_timeout(400)
        await pg.locator("#freeOwnGrid .featured-card", has_text="Journal").click(); await pg.wait_for_timeout(300)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(300)
        check("no Fullscreen API: Vollbild button hidden", await pg.is_visible("#freePlayer") and not await pg.is_visible("#freeFsBtn"))
        hidden_all = await pg.evaluate("() => [...document.querySelectorAll('[id$=FsBtn]')].every(b => getComputedStyle(b).display === 'none')")
        check("no Fullscreen API: every player's button hidden", hidden_all)
        await ctx.close()

        # ================= Idee 53: Atem ohne Zeitlimit =================
        ctx, pg = await fresh(scheme="light")
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(300)
        slider = await pg.locator("#breathDurationSlider").bounding_box()
        box = await pg.locator("#breathNoLimitCheck").bounding_box()
        same_group = await pg.evaluate("() => document.getElementById('breathNoLimitCheck').closest('.group') === document.getElementById('breathDurationSlider').closest('.group')")
        check("checkbox 'Ohne Zeitlimit' directly under the duration", same_group and box["y"] > slider["y"], (box, slider))
        check("off by default", not await pg.is_checked("#breathNoLimitCheck"))
        await pg.click("#breathNoLimitCheck"); await pg.wait_for_timeout(100)
        check("on: help text + duration dimmed", await pg.is_visible("#breathNoLimitHelp") and await pg.evaluate("() => document.getElementById('breathDurationSlider').closest('.group').classList.contains('breath-dur-off')"))
        await pg.locator("#breathNoLimitCheck").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/atem_ready_ohne_zeitlimit_light.png")
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(300)
        check("persists across reload", await pg.is_checked("#breathNoLimitCheck"))
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(1300)
        t1 = await pg.inner_text("#breathTimeEl")
        check("open run: clock counts up, Fertig shown", t1.startswith("0:0") and t1 != "0:00" and await pg.is_visible("#breathFinishBtn"), t1)
        check("Prüfer 10: open run shows one way to end (bar ✕ Beenden waits for the pause sheet)", await pg.evaluate("() => getComputedStyle(document.getElementById('breathBackBtn')).visibility === 'hidden'"))
        await pg.screenshot(path=f"{SHOTS}/atem_offen_light.png")
        n_before = len(await pg.evaluate(HIST))
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(600)
        check("↻ restarts an open run without a history entry", len(await pg.evaluate(HIST)) == n_before and await pg.is_visible("#breathFinishBtn"))
        await pg.wait_for_timeout(1200)
        await pg.click("#breathPauseBtn"); await pg.wait_for_timeout(200)
        check("pause sheet: no Restdauer, a Fertig button", not await pg.is_visible("#breathPauseRestGroup") and await pg.is_visible("#breathPauseFinishBtn"))
        check("Prüfer 10: in the pause sheet the bar's Beenden is back", await pg.is_visible("#breathBackBtn"))
        await pg.click("#breathResumeBtn"); await pg.wait_for_timeout(1200)
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(400)
        h = await latest_history(pg)
        check("Fertig: done panel, history = real time, note", await pg.is_visible("#breathDonePanel") and h and h.get("kind") == "breath" and 1 <= h.get("seconds", 0) <= 5 and h.get("note") == "ohne Zeitlimit", h)
        # tapping a duration switches the time limit back on
        await pg.click("#breathDoneBackBtn"); await pg.wait_for_timeout(300)
        await pg.locator("#patternGrid .fc-title", has_text="Box-Atmung").click(); await pg.wait_for_timeout(300)
        await pg.click('[data-breath-dur="5"]'); await pg.wait_for_timeout(100)
        check("picking a duration unticks 'Ohne Zeitlimit'", not await pg.is_checked("#breathNoLimitCheck"))
        # preset carries it
        await pg.click("#breathNoLimitCheck"); await pg.wait_for_timeout(100)
        await pg.click("#breathSaveBtn"); await pg.fill("#breathSaveNameInput", "Offen atmen"); await pg.click("#breathSaveConfirmBtn"); await pg.wait_for_timeout(200)
        check("preset label says 'ohne Zeitlimit'", "ohne Zeitlimit" in await pg.inner_text("#breathSavedList"))
        await pg.click('[data-breath-dur="3"]'); await pg.wait_for_timeout(100)
        await pg.locator("#breathSavedList .bundle-item", has_text="Offen atmen").click(); await pg.wait_for_timeout(500)
        check("preset starts an open run", await pg.is_visible("#breathFinishBtn") and await pg.is_visible("#breathPlayer"))
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(300)
        await ctx.close()

        # timed run: hold at the end with "Beenden" / "Weiter atmen"
        short = {"durationMin": 0.05, "sound": False, "listen": False, "noLimit": False, "custom": FAST_PHASES}
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-breath-v1', {json.dumps(json.dumps(short))});"))
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Eigenes Muster").click(); await pg.wait_for_timeout(300)
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(4600)
        hold = await pg.is_visible("#breathMoreBtn") and await pg.is_visible("#breathEndNowBtn")
        check("time up: 'Weiter atmen' next to 'Beenden'", hold, await pg.evaluate(VIS))
        mb, eb = await pg.locator("#breathMoreBtn").bounding_box(), await pg.locator("#breathEndNowBtn").bounding_box()
        check("both in one row, >= 44 px", abs(mb["y"] - eb["y"]) < 4 and mb["height"] >= 44 and eb["height"] >= 44, (mb, eb))
        check("bar's ✕ Beenden waits (one Beenden on screen)", await pg.evaluate("() => getComputedStyle(document.getElementById('breathBackBtn')).visibility === 'hidden'"))
        check("note names the auto-end", "endet die Übung" in await pg.inner_text("#breathEndNote"))
        check("Prüfer 9: one counter at the end (time pill hidden, check mark in the circle)",
              await pg.evaluate("() => getComputedStyle(document.getElementById('breathTimeEl')).visibility === 'hidden'") and (await pg.inner_text("#breathPhaseCount")).strip() == "✓")
        await pg.screenshot(path=f"{SHOTS}/atem_weiter_atmen_light.png")
        await pg.click("#breathMoreBtn"); await pg.wait_for_timeout(2200)
        t = await pg.inner_text("#breathTimeEl")
        check("Prüfer 9: time pill back after 'Weiter atmen'", await pg.is_visible("#breathTimeEl"))
        check("Weiter atmen: open run goes on, clock past the planned time", await pg.is_visible("#breathFinishBtn") and t >= "0:05", t)
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(400)
        h = await latest_history(pg)
        check("history: planned + extra time", h and 5 <= h.get("seconds", 0) <= 9 and h.get("note") == "ohne Zeitlimit", h)
        # without a tap the run ends by itself
        await pg.click("#breathAgainBtn"); await pg.wait_for_timeout(4500 + 10800)
        check("no tap: ends by itself after the hold", await pg.is_visible("#breathDonePanel") and not await pg.is_visible("#breathMoreBtn"))
        h = await latest_history(pg)
        check("timed run keeps its planned time", h and h.get("seconds") == 4 and not h.get("note"), h)
        await ctx.close()

        # Kombi: "Weiter atmen" then the next Baustein; a noLimit block plays until Fertig
        combos = [
            {"id": "a1", "name": "Atem dann Journal", "createdAt": "2026-10-07T00:00:00Z", "blocks": [
                {"domain": "breath", "pattern": "custom", "phases": FAST_PHASES, "durationMin": 0.05, "sound": False, "pauseAfterS": 0},
                {"domain": "free", "free": FREE_OWN[0]}]},
            {"id": "a2", "name": "Offen dann Journal", "createdAt": "2026-10-07T00:00:00Z", "blocks": [
                {"domain": "breath", "pattern": "box", "durationMin": 5, "noLimit": True, "sound": False, "pauseAfterS": 0},
                {"domain": "free", "free": FREE_OWN[0]}]},
        ]
        seed = f"localStorage.setItem('fwmc-combo-saved-v1', {json.dumps(json.dumps(combos))});"
        ctx, pg = await fresh(seed)
        await open_combo(pg, "Atem dann Journal")
        await pg.wait_for_timeout(4300)
        check("Kombi: hold with 'Weiter atmen'", await pg.is_visible("#breathMoreBtn") and "geht es" in await pg.inner_text("#breathEndNote"))
        await pg.click("#breathMoreBtn"); await pg.wait_for_timeout(1500)
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(400)
        check("Kombi: after Weiter atmen + Fertig the next Baustein plays", await pg.is_visible("#freePlayer"), await pg.evaluate(VIS))
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(400)
        h = await latest_history(pg)
        check("Kombi history counts the real time", await pg.is_visible("#comboDonePanel") and h and h.get("kind") == "combo" and h.get("seconds", 0) >= 5, h)
        await ctx.close()

        ctx, pg = await fresh(seed)
        await open_combo(pg, "Offen dann Journal")
        await pg.wait_for_timeout(1500)
        check("Kombi block 'ohne Zeitlimit': open run with Fertig", await pg.is_visible("#breathFinishBtn") and (await pg.inner_text("#breathTimeEl")).startswith("0:0"))
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(400)
        check("Kombi: Fertig goes on to the next Baustein", await pg.is_visible("#freePlayer"))
        await pg.click("#freeBackBtn"); await pg.wait_for_timeout(300)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-breath-v1') || '{}')")
        check("Kombi never changes the client's own setting", not prefs.get("noLimit"), prefs)
        # Kombi capture + edit
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.click('#breathHome .combo-entry-link'); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Box-Atmung"'); await pg.wait_for_timeout(300)
        await pg.click("#breathNoLimitCheck"); await pg.click("#breathStartBtn"); await pg.wait_for_timeout(300)
        check("Kombi capture: block meta 'ohne Zeitlimit'", "ohne Zeitlimit" in await pg.inner_text("#comboBlockList"))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        check("Kombi edit: checkbox ticked again", await pg.is_checked("#breathNoLimitCheck"))
        await pg.click("#breathBackToHome"); await pg.wait_for_timeout(200)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-breath-v1') || '{}')")
        check("capture leaves the own setting off", not prefs.get("noLimit"), prefs)
        await ctx.close()

        # Weitermachen: an open run that was interrupted continues open-ended
        rec = {"type": "single", "kind": "breath", "title": "Box-Atmung", "open": True, "total": 95, "played": 95, "rest": 0,
               "ts": int(time.time() * 1000) - 60000,
               "breath": {"key": "box", "phases": {"in": 4, "hold1": 4, "out": 4, "hold2": 4}, "sound": False, "listen": False, "open": True}}
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-resume-single-v1', {json.dumps(json.dumps(rec))});localStorage.setItem('fwmc-test-bottomnav','true');"))
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        card = await pg.inner_text("#todayHome")
        check("Heute: Weitermachen names 'ohne Zeitlimit'", "ohne Zeitlimit" in card)
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(1300)
        check("Fortsetzen: open run again", await pg.is_visible("#breathFinishBtn"))
        await pg.click("#breathPauseBtn"); await pg.wait_for_timeout(200)
        r2 = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-resume-single-v1') || 'null')")
        check("pause notes the open run with the time so far", r2 and r2.get("open") and r2.get("played", 0) >= 96, r2)
        await pg.click("#breathPauseFinishBtn"); await pg.wait_for_timeout(300)
        check("Fertig from the pause sheet ends it", await pg.is_visible("#breathDonePanel"))
        await ctx.close()

        # dark mode screenshots of the breath screens
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-breath-v1', {json.dumps(json.dumps(short))});"), scheme="dark")
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.locator("#patternGrid .fc-title", has_text="Eigenes Muster").click(); await pg.wait_for_timeout(300)
        await pg.locator("#breathNoLimitCheck").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/atem_ready_ohne_zeitlimit_dark.png")
        await pg.click("#breathStartBtn"); await pg.wait_for_timeout(4600)
        await pg.screenshot(path=f"{SHOTS}/atem_weiter_atmen_dark.png")
        await pg.click("#breathMoreBtn"); await pg.wait_for_timeout(600)
        await pg.screenshot(path=f"{SHOTS}/atem_offen_dark.png")
        await pg.click("#breathFinishBtn"); await pg.wait_for_timeout(300)
        await ctx.close()

        # ================= Idee 55: Reaktionstraining Farben =================
        for scheme in ("light", "dark"):
            ctx, pg = await fresh(scheme=scheme)
            await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
            await pg.click("#movementAdvanced summary"); await pg.wait_for_timeout(150)
            if scheme == "light":
                check("Signalfarbe: 'Standard: Orange.'", "Standard: Orange" in await pg.inner_text("#movementSigStatus"))
            await pg.click('#movementSigPicker [data-key="blau"]'); await pg.wait_for_timeout(100)
            await pg.click('#movementBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
            if scheme == "light":
                check("own signal colour + Standard link", "Eigene Farbe: Blau" in await pg.inner_text("#movementSigStatus") and await pg.is_visible("[data-mv-sig-reset]"))
                check("bg pick jumps to 50 %", (await pg.inner_text("#movementBgIntensityValue")).strip() == "50%")
                chip = await pg.inner_html("#movementPicker")
                check("movement chips draw the signal colour", "#1565c0" in chip)
            await pg.locator("#movementSigGroup").scroll_into_view_if_needed()
            await pg.screenshot(path=f"{SHOTS}/reaktion_farben_ready_{scheme}.png")
            await pg.reload(); await pg.wait_for_timeout(400)
            prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}')")
            check(f"[{scheme}] colours persist", prefs.get("sigColor") == "blau" and prefs.get("bgColorKey") == "gelb" and prefs.get("bgIntensity") == 0.5, prefs)
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
            await pg.click("#movementStartBtn"); await pg.wait_for_timeout(700)
            bg = await pg.evaluate("() => getComputedStyle(document.getElementById('movementPlayer')).backgroundColor")
            want = mix("#ffffff" if scheme == "light" else "#0b1619", "#f2a900", 0.5)
            check(f"[{scheme}] player background follows the setting", near(bg, want), (bg, want))
            act = await pg.evaluate("() => { const a = document.querySelector('#movementLane .active'); return a ? getComputedStyle(a).borderTopColor : ''; }")
            check(f"[{scheme}] active field in the signal colour", act == "rgb(21, 101, 192)", act)
            check(f"[{scheme}] symbols in the signal colour", "#1565c0" in await pg.inner_html("#movementLane"))
            await pg.screenshot(path=f"{SHOTS}/reaktion_farben_player_{scheme}.png")
            await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(200)
            check(f"[{scheme}] pause sheet has the background", await pg.is_visible("#movementPauseBgSlider") and await pg.is_visible("#movementPauseBgColorPicker"))
            await pg.click('#movementPauseBgColorPicker [data-key="rot"]'); await pg.wait_for_timeout(100)
            bg = await pg.evaluate("() => getComputedStyle(document.getElementById('movementPlayer')).backgroundColor")
            check(f"[{scheme}] live change in the pause sheet", near(bg, mix("#ffffff" if scheme == "light" else "#0b1619", "#d32f2f", 0.5)), bg)
            await pg.screenshot(path=f"{SHOTS}/reaktion_pause_{scheme}.png")
            await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(100)
            await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
            await ctx.close()

        # presets carry the colours
        ctx, pg = await fresh()
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
        await pg.click("#movementAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.click('#movementSigPicker [data-key="lila"]'); await pg.click('#movementBgColorPicker [data-key="blau"]'); await pg.wait_for_timeout(100)
        await pg.click("#movementSaveBtn"); await pg.fill("#movementSaveNameInput", "Lila auf Blau"); await pg.click("#movementSaveConfirmBtn"); await pg.wait_for_timeout(200)
        await pg.click("[data-mv-sig-reset]"); await pg.wait_for_timeout(100)
        await pg.click('#movementBgColorPicker [data-key="gruen"]'); await pg.wait_for_timeout(100)
        check("Standard link resets the signal colour", "Standard: Orange" in await pg.inner_text("#movementSigStatus"))
        await pg.locator("#movementSavedList .bundle-item", has_text="Lila auf Blau").click(); await pg.wait_for_timeout(600)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}')")
        check("preset restores signal + background", prefs.get("sigColor") == "lila" and prefs.get("bgColorKey") == "blau", prefs)
        check("preset run shows the colours", "#7b3fa0" in (await pg.inner_html("#movementLane")).lower() or "#7e4fbe" in (await pg.inner_html("#movementLane")).lower())
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        await ctx.close()

        # Kombi block keeps its own colours; the client's stay untouched
        own = {"sigColor": None, "bgColorKey": "gruen", "bgIntensity": 0, "layout": "zeilen", "rowLen": 4, "figureStyle": "felder"}
        combos = [{"id": "m1", "name": "Reaktion bunt", "createdAt": "2026-10-07T00:00:00Z", "blocks": [
            dict(MV_FAST, durationMin=0.2, sigColor="pink", bgColorKey="lila", bgIntensity=0.3, pauseAfterS=0)]}]
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-combo-saved-v1', {json.dumps(json.dumps(combos))});localStorage.setItem('fwmc-movement-v1', {json.dumps(json.dumps(own))});"))
        await open_combo(pg, "Reaktion bunt")
        bg = await pg.evaluate("() => getComputedStyle(document.getElementById('movementPlayer')).backgroundColor")
        check("Kombi block plays its own background", near(bg, mix("#ffffff", "#7e4fbe", 0.3)), bg)
        check("Kombi block plays its own signal colour", "#e6399b" in await pg.inner_html("#movementLane"))
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#movementPauseBgColorPicker [data-key="gelb"]'); await pg.wait_for_timeout(100)
        await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(100)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}')")
        check("Kombi (incl. pause-sheet change) leaves the own colours", prefs.get("sigColor") is None and prefs.get("bgColorKey") == "gruen" and prefs.get("bgIntensity") == 0, prefs)
        # capture: a new block takes the colours along
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click('#movementHome .combo-entry-link'); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Ganzkörper-Reaktion"'); await pg.wait_for_timeout(300)
        await pg.click("#movementAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.click('#movementSigPicker [data-key="gruen"]'); await pg.wait_for_timeout(100)
        await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(300)
        check("Kombi capture/edit keeps the signal colour", "Eigene Farbe: Grün" in await pg.inner_text("#movementSigStatus"))
        await pg.click("#movementBackToHome"); await pg.wait_for_timeout(200)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-movement-v1') || '{}')")
        check("capture leaves the own signal colour", prefs.get("sigColor") is None, prefs)
        await ctx.close()

        # Weitermachen: the record's colours play
        rec = {"type": "single", "kind": "movement", "title": "Ganzkörper-Reaktion", "total": 300, "played": 60, "rest": 240,
               "ts": int(time.time() * 1000) - 60000,
               "movement": {"movements": ["armL-heben", "armR-heben", "legL-strecken", "legR-strecken"], "bpm": 60, "preview": 2,
                            "mirror": False, "showLabel": False, "layout": "zeilen", "rowLen": 4, "figureStyle": "felder",
                            "sigColor": "rot", "bgColorKey": "blau", "bgIntensity": 0.2}}
        ctx, pg = await fresh(once(f"localStorage.setItem('fwmc-resume-single-v1', {json.dumps(json.dumps(rec))});localStorage.setItem('fwmc-test-bottomnav','true');"))
        await pg.goto(BASE); await pg.wait_for_timeout(400)
        await pg.click("#todayResumeBtn"); await pg.wait_for_timeout(500)
        bg = await pg.evaluate("() => getComputedStyle(document.getElementById('movementPlayer')).backgroundColor")
        check("Weitermachen plays the record's colours", near(bg, mix("#ffffff", "#1565c0", 0.2)) and "#d32f2f" in await pg.inner_html("#movementLane"), bg)
        await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(150)
        await ctx.close()

        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:4]))
    print("ALL PASS" if all(results) else "SOME FAILED")


asyncio.run(main())
